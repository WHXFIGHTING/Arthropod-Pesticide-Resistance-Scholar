'''
author: whx
date: 2025/9/8
description: Configure project configuration information

'''


import torch
import logging
import sys


logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(message)s',
    stream=sys.stdout,
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)




class Config:
    def __init__(self):
        self.DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.ID2LABEL  = {0: 'O',
                     1: 'B-Species', 2: 'I-Species', 
                     3: 'B-Pesticides', 4: 'I-Pesticides', 
                     5:'B-Resistance_factor_value', 6:'I-Resistance_factor_value',
                     7:'B-Location',8:'I-Location',
                     9:'B-Gene',10:'I-Gene',
                     11:'B-Year',12:'I-Year',
                     13:'B-Research_level',14:'I-Research_level',
                     15:'B-Resistance_mechanism',16:'I-Resistance_mechanism',
                     17:'B-LC/LD',18:'I-LC/LD',
                     }
        
        self.LABEL2ID = {v: k for k, v in self.ID2LABEL.items()}

        self._log_initial_config()

    def _log_initial_config(self):
        logger.info(f"Using device: {self.DEVICE}")
        logger.info(f"ID2LABEL: {self.ID2LABEL}")



    def set_path_params(self, model_path, data_path, model_save_path):
        if not all([model_path, data_path, model_save_path]):
            logger.error("All path parameters must be provided and non-empty.")
            raise ValueError("All path parameters must be provided and non-empty.")

        self.model_path = model_path
        self.data_path = data_path
        self.model_save_path = model_save_path


        self._log_path_params()

    def _log_path_params(self):
        logger.info(f"Current MODEL_PATH: {self.model_path}")
        logger.info(f"Current DATA_PATH: {self.data_path}")
        logger.info(f"Current MODEL_SAVE_PATH: {self.model_save_path}")
        


    def set_training_params(self, learning_rate=1e-5, batch_size=4, epoch_num=10, seed=42):
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epoch_num = epoch_num
        self.seed = seed

        self._log_training_params()

    def _log_training_params(self):
        logger.info(f"Current LEARNING_RATE: {self.learning_rate}")
        logger.info(f"Current BATCH_SIZE: {self.batch_size}")
        logger.info(f"Current EPOCH_NUM: {self.epoch_num}")
        logger.info(f"Current SEED: {self.seed}")




