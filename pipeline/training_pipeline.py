from utils.common_function import read_yaml
from config.paths_config import *
from src.data_preprocessing import DataPreprocessing
from src.model_training import ModelTraining




if __name__ == "__main__":
        
        # Instantiate and run the Data Preprocessing 
        data_preprocessor = DataPreprocessing(input_file=ANIMELIST_CSV,output_dir=PROCESSED_DIR)
        data_preprocessor.run()

        # Instantiate and run the Model Training
        model_trainer = ModelTraining(PROCESSED_DIR)
        model_trainer.train_model()