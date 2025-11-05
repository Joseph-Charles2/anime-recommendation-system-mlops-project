from tensorflow.keras.models import Model 
from tensorflow.keras.layers import Input,Embedding, Dot,Flatten,Dense,Activation,BatchNormalization,Dropout
from utils.common_function import read_yaml
from src.logger import get_logger
from src.custom_exception import CustomException
import os 
import sys

# Initialize Logger 
logger = get_logger(__name__)

class BaseModel:

    def __init__(self,config_path):
        try:
            self.config = read_yaml(config_path)
            logger.info("Configuration file loaded successfully.")
        except Exception as e:
            logger.error("Error loading configuration file.")
            raise CustomException(f"Error loading Configuration:{e}", sys)
        
    
    def recommenderNet(self,n_user,n_anime):
        try:
            ### Model Architecture:

            embedding_size = self.config['model']['embedding_size']

            # User Input Layer
            user = Input(name="user",shape=[1])

            # User Embedding Layer
            user_embedding = Embedding(input_dim=n_user,output_dim=embedding_size,name='user_embedding')(user)

            # Anime Input Layer 
            anime = Input(name="anime",shape=[1])

            # Anime Embedding Layer 
            anime_embedding = Embedding(input_dim=n_anime,output_dim=embedding_size,name="anime_embedding")(anime)

            # Dot Product of User and Anime Embedding Layer
            x = Dot(name="dot_product",normalize=True,axes=2)([user_embedding,anime_embedding])

            # Flatten Layer
            x = Flatten()(x)

            # Dense Layer 
            x = Dense(1,kernel_initializer="he_normal",name="dense_layer")(x)

            # Batch Normalization Layer
            x = BatchNormalization()(x)

            # Activation Layer
            x = Activation("sigmoid")(x)

            # Create Model 
            model = Model(inputs=[user,anime],outputs=x)

            # Compile the Model 
            model.compile(loss=self.config['model']['loss'],
                          optimizer=self.config['model']['optimizer'],
                          metrics=self.config['model']['metrics'])
            logger.info("Model created and compiled successfully.")
    
            return model
        except Exception as e:
            logger.error(f"Error in creating the model.")
            raise CustomException(f"Error in Model Creation:{e}", sys)
        