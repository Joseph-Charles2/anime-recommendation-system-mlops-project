import os 
import pandas as pd 
import numpy as np 
import joblib 
from sklearn.model_selection import train_test_split
from src.logger import get_logger
from src.custom_exception import CustomException, DataValidationError
from config.paths_config import *
import sys

# Initialize Logger 
logger = get_logger(__name__)

class DataPreprocessing:
    def __init__(self, input_file,output_dir):

        '''
         input_file : str : path to the input data file
         output_dir : str : directory to save processed data
        '''

        self.input_file = input_file
        self.output_dir = output_dir

        self.rating_df = None
        self.anime_df = None
        self.X_train_array = None
        self.X_test_array = None
        self.y_train = None
        self.y_test = None

        self.user2user_encoded = {}
        self.user_encoded2user = {}
        self.anime2anime_encoded = {}
        self.anime_encoded2anime = {}

        os.makedirs(self.output_dir,exist_ok=True)
        logger.info(f"Data Preprocessing initialized. Input file: {self.input_file}, Output dir: {self.output_dir}")

    
    def load_data(self):
        try:
            self.rating_df = pd.read_csv(self.input_file,low_memory=True,usecols=['user_id','anime_id','rating'])
            logger.info(f"Data loaded successfully from {self.input_file}. Shape: {self.rating_df.shape}")
        except Exception as e:
            logger.error(f"Error loading data from {self.input_file}: {e}")
            raise CustomException(f"Error loading data from {self.input_file}: {e}", "Data Loading")
        
    
    def filter_users(self,min_ratings=400):
        try:
            n_ratings = self.rating_df['user_id'].value_counts()
            self.rating_df = self.rating_df[self.rating_df['user_id'].isin(n_ratings[n_ratings >= 400].index)].copy()
            logger.info(f"Filtered users with at least {min_ratings} ratings. New shape: {self.rating_df.shape}")
        except Exception as e:
            logger.error(f"Error filtering users: {e}")
            raise CustomException(f"Error filtering users: {e}", "Data Filtering")
        
    def scale_ratings(self):
        try:
            min_rating = self.rating_df['rating'].min()
            max_rating = self.rating_df['rating'].max()
            self.rating_df['rating'] = self.rating_df['rating'].apply(lambda x: (x-min_rating)/(max_rating - min_rating)).values.astype(np.float64)
            logger.info(f"Scaled ratings to range [0, 1].")
        except Exception as e:
            logger.error(f"Error scaling ratings: {e}")
            raise CustomException(f"Error scaling ratings: {e}", "Data Scaling")
        
    def encode_data(self):
        try:
            # users and Anime ids encoding 

            user_ids = self.rating_df['user_id'].unique().tolist()
            anime_ids = self.rating_df['anime_id'].unique().tolist()

            # Encode user ids 
            self.user2user_encoded = { x:i for i,x in enumerate(user_ids)}

            # Encode anime ids
            self.anime2anime_encoded = {x:i for i,x in enumerate(anime_ids)}

            # Decode user ids 
            self.user_encoded2user = {i:x for i,x in enumerate(user_ids)}

            # Decode anime ids
            self.anime_encoded2anime = {i:x for i,x in enumerate(anime_ids)}


            # Map the encoded values in the self.rating_df with new columns name user and anime 
            self.rating_df['user'] = self.rating_df['user_id'].map(self.user2user_encoded)
            self.rating_df['anime'] = self.rating_df['anime_id'].map(self.anime2anime_encoded)

            logger.info(f"Encoded user and anime IDs.")
        except Exception as e:
            logger.error(f"Error encoding data: {e}")
            raise CustomException(f"Error encoding data: {e}", "Data Encoding")
        
    def split_data(self,test_size=1000,random_state=42):

        try:
            # Shuffle the data
            self.rating_df = self.rating_df.sample(frac=1,random_state=42).reset_index(drop=True)

            # Split the data into train and test sets 
            X = self.rating_df[['user','anime']].values
            y = self.rating_df['rating'].values
            # Split the data into train and test with test_size = 1000
            train_indices = self.rating_df.shape[0] - test_size

            X_train, X_test, y_train, y_test = (
                X[:train_indices], 
                X[train_indices:], 
                y[:train_indices], 
                y[train_indices:]
            )
            
            self.X_train_array = [X_train[:, 0], X_train[:, 1]]
            self.X_test_array = [X_test[:, 0], X_test[:, 1]]
            self.y_train = y_train
            self.y_test = y_test


            logger.info(f"Split data into train and test sets. Train size: {X_train.shape[0]}, Test size: {X_test.shape[0]}")
        
        except Exception as e:
            logger.error(f"Error splitting data: {e}")
            raise CustomException(f"Error splitting data: {e}", "Data Splitting")
        
    
    def save_artifacts(self):
        try:
            artifacts = {
                "user2user_encoded": self.user2user_encoded,
                "user_encoded2user": self.user_encoded2user,
                "anime2anime_encoded": self.anime2anime_encoded,
                "anime_encoded2anime": self.anime_encoded2anime
            }

            for name, artifact in artifacts.items():
                joblib.dump(artifact, os.path.join(self.output_dir, f"{name}.pkl"))
                logger.info(f"Saved artifact: {name} to {self.output_dir}")
                logger.info("Data Preprocessing artifacts saved successfully.")

            joblib.dump(self.X_train_array,X_TRAIN_ARRAY)
            joblib.dump(self.X_test_array,X_TEST_ARRAY)
            joblib.dump(self.y_train,Y_TRAIN)
            joblib.dump(self.y_test,Y_TEST)


            self.rating_df.to_csv(RATING_DF,index=False)
            logger.info(f"Saved processed data arrays and rating dataframe to {self.output_dir}")
        except Exception as e:
            logger.error(f"Error saving artifacts: {e}")
            raise CustomException(f"Error saving artifacts: {e}", "Artifact Saving")
        

    def getAnimeName(self,df,anime_id):
            try:
                name = df[df.MAL_ID == anime_id]["English name"].values[0]
                if name is np.nan:
                    name = df[df.MAL_ID == anime_id]["Name"].values[0]
            except:
                print("Anime name not found!")

            return name
    
    def process_anime_data(self):
        try:
            df = pd.read_csv(ANIME_CSV,low_memory=True)
            cols = ["MAL_ID","Name","Genres","sypnopsis"]
            synopsis_df = pd.read_csv(ANIMESYNOPSIS_CSV,low_memory=True,usecols=cols)

            # Replace "Unknown" with NaN
            df = df.replace("Unknown",np.nan)

            # create a new column 'eng_version' by applying getAnimeName function
            df["eng_version"] = df['MAL_ID'].apply(lambda x: self.getAnimeName(df,x))

            # Sort the df by 'Score' column in descending order 
            df.sort_values(by=["Score"], ascending=False,inplace=True,kind="quicksort",na_position="last")

            # Use selected columns only 
            df = df[["MAL_ID","eng_version","Score","Genres","Episodes","Type","Premiered","Studios","Members"]]

            # Save the processed anime dataframe 
            df.to_csv(DF,index=False)
            synopsis_df.to_csv(SYNOPSIS_DF_PATH,index=False)
            logger.info(f"Anime and Synopsis data processed and saved successfully.In paths: {DF} and {SYNOPSIS_DF_PATH}")
        
        except Exception as e:
            logger.error(f"Error in Processing anime and synopsis dataframe: {e}")
            raise CustomException(f"Error in Processing anime and synopsis dataframe: {e}", "Anime and Synopsis Data Processing") 

            
    def run(self):
        try:
            logger.info("Starting Data Preprocessing...")
            self.load_data()
            self.filter_users(min_ratings=400)
            self.scale_ratings()
            self.encode_data()
            self.split_data(test_size=1000,random_state=42)
            self.save_artifacts()
            self.process_anime_data()
            logger.info("Data Preprocessing pipeline completed successfully.")
        except Exception as e:
            logger.error(f"Error in Data Preprocessing pipeline run: {e}")
            raise CustomException(f"Error in Data Preprocessing pipeline run: {e}", "Data Preprocessing Run")

if __name__ == "__main__":

    data_preprocessor = DataPreprocessing(input_file=ANIMELIST_CSV,output_dir=PROCESSED_DIR)
    data_preprocessor.run()


       
