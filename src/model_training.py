import joblib
from comet_ml import start
import numpy as np
import os 
# from tensorflow.keras.callbacks import EarlyStopping,ModelCheckpoint,LearningRateScheduler
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, LearningRateScheduler
from src.logger import get_logger
from src.custom_exception import CustomException
from src.base_model import BaseModel
import sys
from config.paths_config import *

# Initialize Logger
logger = get_logger(__name__)

class ModelTraining:

    def __init__(self,data_path):
        
        self.data_path = data_path
        self.experiment = start(
            api_key='agcsmeWkyOcninCzlPJOxIX7Z',
            project_name='mlops-project_2',
            workspace="joseph-charles2"
        )
        logger.info("ModelTraining instance & CometML Initialized successfully.") 

    def load_data(self):
        try:
            X_train_array = joblib.load(X_TRAIN_ARRAY)
            X_test_array = joblib.load(X_TEST_ARRAY)
            y_train = joblib.load(Y_TRAIN)
            y_test = joblib.load(Y_TEST)

            logger.info(f"Data Loaded Sucessfully for Model Training")

            return X_train_array,X_test_array,y_train,y_test

        except Exception as e :
            logger.error(f"Failed to load data:{e} ")
            raise CustomException(f"Failed to load data from the path",e)
    
    def lrfn(self,epoch):
        if epoch < self.ramup_epochs:
            lr = (self.max_lr - self.start_lr)/self.ramup_epochs * epoch + self.start_lr
        elif epoch < self.ramup_epochs + self.sustain_epochs:
            lr = self.max_lr
        else:
            lr = (self.max_lr - self.min_lr) * self.expo_decay**(epoch - self.ramup_epochs - self.sustain_epochs) + self.min_lr
        return lr
    
        
    def train_model(self):
        try:
            X_train_array,X_test_array,y_train,y_test = self.load_data()

            # calculate the number of user
            n_users = len(joblib.load(USER2USER_ENCODED))
            n_anime = len(joblib.load(ANIME2ANIME_ENCODED))

            base_model = BaseModel(config_path=CONFIG_PATH)

            model = base_model.recommenderNet(n_user=n_users,n_anime=n_anime)

            self.start_lr = 0.00001
            self.min_lr = 0.0001
            self.max_lr = 0.00005
            self.batch_size = 10000

            self.ramup_epochs = 5
            self.sustain_epochs = 0
            self.expo_decay = 0.8

            lr_callback = LearningRateScheduler(lambda epoch: self.lrfn(epoch),verbose=0)
            model_checkpoint = ModelCheckpoint(filepath=CHECKPOINT_FILE_PATH,save_weights_only=True,monitor="val_loss",mode="min",save_best_only=True)
            early_stopping = EarlyStopping(patience =3,monitor="val_loss",mode="min",restore_best_weights=True)


            my_callbacks = [model_checkpoint,lr_callback,early_stopping]

            os.makedirs(os.path.dirname(CHECKPOINT_FILE_PATH),exist_ok=True)
            os.makedirs(MODEL_DIR,exist_ok=True)
            os.makedirs(WEIGHTS_DIR,exist_ok=True)

            history = model.fit(x=X_train_array,y=y_train,batch_size=self.batch_size,epochs=20,verbose=1,validation_data=(X_test_array,y_test),callbacks=my_callbacks)


            model.load_weights(CHECKPOINT_FILE_PATH)
            logger.info(f"Model Training Completed........")

            for epoch in range(len(history.history['loss'])):
                train_loss = history.history["loss"][epoch]
                val_loss = history.history["val_loss"][epoch]
                self.experiment.log_metric("train_loss",train_loss,step =epoch)
                self.experiment.log_metric("val_loss",val_loss,step =epoch)
            self.save_model_weights(model)

        
        except Exception as e :
            logger.error(f"Failed in Model Training,{e}")
            raise CustomException(f"Failed in training the model",e)
        
    def extract_weights(self,layer_name,model):
        try:
            weight_layer = model.get_layer(layer_name)
            weights = weight_layer.get_weights()[0]
            weights = weights/np.linalg.norm(weights,axis=1).reshape((-1,1))
            logger.info(f"Extracting weights for {layer_name}")
            return weights

        except Exception as e:
            logger.error(f"Error during weight extraction {e}")
            raise CustomException (f"Error occured during weights extraction")
            
    
    def save_model_weights(self,model):
        try:
            model.save(MODEL_PATH)
            logger.info(f"Model Saved to {MODEL_PATH}")

            anime_weights = self.extract_weights("anime_embedding",model)
            user_weights = self.extract_weights("user_embedding",model)

            joblib.dump(user_weights,USER_WEIGHTS_PATH)
            joblib.dump(anime_weights,ANIME_WEIGHTS_PATH)

            self.experiment.log_asset(MODEL_PATH)
            self.experiment.log_asset(ANIME_WEIGHTS_PATH)
            self.experiment.log_asset(USER_WEIGHTS_PATH)


            logger.info(f"User and Anime weights saved successfully...")

        except Exception as e:
            logger.error(f"Error in saved the model weights,{e}")
            raise CustomException(f"Error in save the model anime and user weights",e)
        
        

if __name__ == "__main__":
    logger.info("Start the Model Training.")
    model_trainer = ModelTraining(PROCESSED_DIR)
    model_trainer.train_model()


