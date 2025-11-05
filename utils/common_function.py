import os
from src.logger import get_logger
from src.custom_exception import CustomException,DataIngenstionError

import yaml

logger = get_logger(__name__)

def read_yaml(file_path):

    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File is not in the given path {file_path}")

        with open (file_path,'r') as yaml_file:
            config = yaml.safe_load(yaml_file)
            logger.info("Successfully read the yaml file.")

            return config

    except Exception as e :
        logger.error("Error while reading Yaml File.")
        raise CustomException("Failed to read Yaml file",e)
