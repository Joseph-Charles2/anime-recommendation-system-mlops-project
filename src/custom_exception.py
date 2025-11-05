class CustomException(Exception):
    def __int__(self,message,*args):
        super().__init__(message,*args)

class DataIngenstionError(CustomException):
    def __int__(self,message,source_uri):
        super().__init__(message)
        self.source_uri =source_uri


class DataValidationError(CustomException):
    def __int__(self, message="Data Validation failed",invalid_data=None):
        super().__init__(message)
        self.invalid_data = invalid_data

class ModelTrainingError(CustomException):
    def __int__(self,message="Model Training Failed",model_name=None,epoch=None):
        super().__int__(message)
        self.model_name = model_name
        self.epoch =epoch
