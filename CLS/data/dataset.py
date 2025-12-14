'''
author: whx
date: 2025/9/8
description: load data set

'''


import pandas as pd
import numpy as np
import ast
import logging
import torch
from torch.utils.data import Dataset, DataLoader, random_split
from transformers import AutoTokenizer


logger = logging.getLogger(__name__)


class ClassificationDataset(Dataset):

    def __init__(self, data_path, tokenizer_checkpoint):
        self.data_file = data_path
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_checkpoint)
        self.data = self._load_data()

    def _load_data(self):
        try:
            input_data = pd.read_csv(self.data_file, encoding='utf-8')
            logger.info(f"Loaded {len(input_data)} lines from {self.data_file}")
            

            data = {
                i: {
                    'text': input_data.iloc[i, 1],
                    'labels': input_data.iloc[i, 0]
                }
                for i in range(len(input_data))
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Error: {e}")
            raise    

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]







def cls_collate_fn(batch_samples, tokenizer):

    texts = [s['text'] for s in batch_samples]

    labels = [int(s['labels']) for s in batch_samples]  


    batch_inputs = tokenizer(
        texts, 
        max_length=512,
        padding=True,   
        truncation=True,  
        return_tensors="pt" 
    )

    return batch_inputs, torch.tensor(labels, dtype=torch.long)










def create_data_loaders(dataset, batch_size, valid_ratio=0.2):
    trainset,validset = random_split(dataset,lengths=[(1-valid_ratio),valid_ratio])
    logger.info(f"dataset segmentation scale {1-valid_ratio}:{valid_ratio}")


    def train_collate_fn(batch):
        return cls_collate_fn(batch, dataset.tokenizer)
    
    def valid_collate_fn(batch):
        return cls_collate_fn(batch, dataset.tokenizer)


    train_dataloader = DataLoader(trainset, batch_size=batch_size, shuffle=True, collate_fn=train_collate_fn)
    valid_dataloader = DataLoader(validset, batch_size=batch_size, shuffle=False, collate_fn=valid_collate_fn)
    

    return train_dataloader, valid_dataloader










