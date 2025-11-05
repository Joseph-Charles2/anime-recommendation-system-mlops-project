import os
import pandas as pd
from google.cloud import storage

from google.api_core.exceptions import NotFound as GcpNotFound, GoogleAPIError

from src.logger import get_logger
from src.custom_exception import CustomException,DataIngenstionError
from utils.common_function import read_yaml

from config.paths_config import *


logger = get_logger(__name__)

class IngestionConfig:

    def __init__(self,config):
        try:
            self.config = config['data_ingestion']
            self.bucket_name = self.config['bucket_name']
            self.bucket_filename_list = self.config['bucket_file_name']
            self.chunk_size = self.config['chunk_size']
            self.file_size_threshold_mb = self.config['file_size_threshold_mb'] * 1024 * 1024
            self.raw_dir = RAW_DIR

            if not self.bucket_name or not isinstance(self.bucket_name,str):
                raise ValueError(f"Configuration bucket_name : {self.bucket_name} is missing or invalid")
            if not self.bucket_filename_list or not isinstance(self.bucket_filename_list,list):
                raise ValueError(f"Configuration bucket_filename_list : {self.bucket_filename_list} is missing or invalid")
            if not self.chunk_size or not isinstance(self.chunk_size,int):
                raise ValueError(f"Configuration chunk_size : {self.chunk_size} is missing or invalid")
            if not self.file_size_threshold_mb or not isinstance(self.file_size_threshold_mb,int):
                raise ValueError(f"Configuration Threshold_Size : {self.file_size_threshold_mb} is missing or invalid")

        except (KeyError , ValueError) as e:
            raise CustomException(f"Configuration Error in Data Ingestion :{e}","Config Load")

class DataIngestion:

    def __init__(self, config:IngestionConfig, gcs_client:storage.Client = None):

        self.config = config

        self.client = gcs_client if gcs_client else storage.Client()

        os.makedirs(self.config.raw_dir,exist_ok=True)
        logger.info(f"Data Ingestion initialized . Destination :{self.config.raw_dir}")

    def get_blob_size_bytes(self,file_name):

        try:
            blob = self.client.bucket(self.config.bucket_name).blob(file_name)

            blob.reload()

            logger.info(f"Blob metadata reloaded for {file_name}. Size: {blob.size} bytes.")

            return blob.size

        except GcpNotFound as e :
            raise DataIngenstionError(f"Blob {file_name} not found", f"gs://{self.config.bucket_name}/{file_name}")
        except GoogleAPIError as e:
            raise DataIngenstionError(f"GCS communication failed while getting blob size for {file_name}. Error :{e}", f"gs://{self.config.bucket_name}/{file_name}")
        except Exception as e :
            raise  DataIngenstionError(f"An unexpected Error occured getting size of {file_name} : {e}",f"gs://{self.config.bucket_name}/{file_name}")


    def stream_large_csv(self,file_name):
        

        # --- NEW CONSTANT FOR ROW LIMIT ---
        MAX_ROWS = 5000000 
        rows_processed = 0
        # ----------------------------------

        logger.info(f"Starting chunked streaming for large file :{file_name}........")
        try:
            with self.client.bucket(self.config.bucket_name).blob(file_name).open('rb') as f:

                for i ,chunk in enumerate(pd.read_csv(f,chunksize=self.config.chunk_size)):
                    
                    # --- NEW ROW LIMIT LOGIC ---
                    if rows_processed >= MAX_ROWS:
                        logger.info(f"Reached maximum row limit of {MAX_ROWS}. Stopping stream for {file_name}.")
                        break
                    
                    rows_to_yield = min(len(chunk), MAX_ROWS - rows_processed)
                    
                    if rows_to_yield < len(chunk):
                        # Truncate the chunk if it exceeds the remaining limit
                        chunk = chunk.iloc[:rows_to_yield]

                    logger.info(f"Processed chunk {i+1} with {len(chunk)} rows form {file_name}.")
                    yield chunk
                    
                    rows_processed += len(chunk)
                    # -----------------------------

            logger.info(f"Finished Streaming and processing all chunks (Total Rows Processed: {rows_processed}) for {file_name}.")

        except GcpNotFound as e :
            raise DataIngenstionError(f"Blob {file_name} not found", f"gs://{self.config.bucket_name}/{file_name}")
        except GoogleAPIError as e:
            raise DataIngenstionError(f"GCS communication failed while chunking filename for {file_name}. Error :{e}", f"gs://{self.config.bucket_name}/{file_name}")
        except Exception as e :
            raise  DataIngenstionError(f"An unexpected Error occured while chunking the largefile filename: {file_name} : {e}",f"gs://{self.config.bucket_name}/{file_name}")


    def  download_small_file(self,file_name):
        logger.info(f"Downloading small file:{file_name}.....")
        file_path = os.path.join(self.config.raw_dir,file_name)

        try:
            blob = self.client.bucket(self.config.bucket_name).blob(file_name)
            blob.download_to_filename(file_path)
            logger.info(f"Successfully Downloaded {file_name} to {file_path}.")

        except GcpNotFound as e:
            raise DataIngenstionError(f"Blob {file_name} not found", f"gs://{self.config.bucket_name}/{file_name}")
        except GoogleAPIError as e:
            raise DataIngenstionError(f"GCS communication failed while downloading small file  {file_name}. Error :{e}",f"gs://{self.config.bucket_name}/{file_name}")
        except Exception as e:
            raise DataIngenstionError(
                f"An unexpected Error occured while downloading small file : {file_name} : {e}", f"gs://{self.config.bucket_name}/{file_name}")


    def download_large_files_in_chunks(self,file_name):

        logger.info(f"Starting Chunked download for {file_name}..........")

        file_path = os.path.join(self.config.raw_dir,file_name)

        try:
            for i ,chunk_df in enumerate(self.stream_large_csv(file_name)):
                mode = 'w' if i ==0 else 'a'

                write_header = (i==0)

                chunk_df.to_csv(file_path,mode=mode,header=write_header,index=False)

                logger.info(f"Chunk {i+1} written to local file {file_name}.")

            logger.info(f"Successfully Downloaded all chunks and saved to {file_name}.")

        except Exception as e:
            raise DataIngenstionError(f"Failed to download and write file '{file_name}' in chunks. Error: {e}",f"gs://{self.config.bucket_name}/{file_name}")

    def run(self):
        logger.info(f"Starting Data Ingestion Process....")

        try:
            # Replaced print statements with logger.info/debug
            logger.info(f"Files to process: {self.config.bucket_filename_list}")

            for file_name in self.config.bucket_filename_list:
                logger.debug(f"Processing file: {file_name}")

                file_size_bytes = self.get_blob_size_bytes(file_name)
                if file_size_bytes is None:
                    # get_blob_size_bytes should raise an error, but as a safeguard:
                    logger.warning(f"Could not determine size for file '{file_name}'. Skipping.")
                    continue

                logger.info(f"File '{file_name}' detected with size: {file_size_bytes / (1024 * 1024):.2f} MB")

                if file_size_bytes > self.config.file_size_threshold_mb:
                    self.download_large_files_in_chunks(file_name)
                else:
                    self.download_small_file(file_name)

        except DataIngenstionError as ce:
            logger.error(f"FATAL ERROR: A critical data ingestion failure occurred. Reason: {ce}")
            logger.debug(f"Source of failure: {ce.source_uri}")
        except CustomException as e:
            logger.critical(f"FATAL CONFIGURATION ERROR: {e}")
        except Exception as e:
            logger.critical(f"An unhandled critical error occurred during run: {e}")

        finally:
            logger.info("Data Ingestion Process Done.")


if __name__ == "__main__":

    try:
        # Assuming CONFIG_PATH and read_yaml are correctly defined/imported
        config = IngestionConfig(read_yaml(CONFIG_PATH))

        # Instantiate and run the data Ingestion class.
        data_ingestion = DataIngestion(config)
        data_ingestion.run()
    except Exception as e:
        logger.error(f"Main execution failed: {e}")