import logging
import sys
import os
from datetime import datetime

## Configure File Directory and File path

LOG_DIR = 'log'
LOG_FILE_PATH = os.path.join(LOG_DIR,f"log_{datetime.now().strftime('%Y-%m-%d')}.log")


def get_logger(name):

    # Create instance for logger
    logger = logging.getLogger(name)

    # Set Level for logger
    logger.setLevel(logging.DEBUG)

    # Check for existing handler to prevent duplicate logs.
    if not logger.handlers:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s -%(message)s'
        )

    ## Create Console_Handler and File_handler
    ## Create object for Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # check whether the directory is present or not .IF not create it
    os.makedirs(LOG_DIR,exist_ok=True)

    ## create object for File handler and set level and Formatter
    file_handler = logging.FileHandler(LOG_FILE_PATH,mode='a')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    ## Add both Handler
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger