'''
author: whx
date: 2025/9/16
description: Configure project configuration information

'''


import torch
import logging
import sys


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    stream=sys.stdout,
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)



class Config:
    def __init__(self):
        self.DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._log_initial_config()

    def _log_initial_config(self):
        logger.info(f"Using device: {self.DEVICE}")



    # 配置路径
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




