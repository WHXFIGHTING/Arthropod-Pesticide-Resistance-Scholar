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

class NERDataset(Dataset):
    #类的初始化
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
                    'sentence': input_data.iloc[i, 1],
                    'labels': ast.literal_eval(input_data.iloc[i, 2])
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




def collote_fn(batch_samples, tokenizer, label2id):
    batch_sentence, batch_labels  = [], [] 

    for sample in batch_samples:
        batch_sentence.append(sample['sentence'])
        batch_labels.append(sample['labels'])
    batch_inputs = tokenizer(
        batch_sentence, 
        #max_length=512,
        padding=True,   
        truncation=True,
        return_tensors="pt" 
    )

    batch_label = np.zeros(batch_inputs['input_ids'].shape, dtype=int)

    for s_idx, sentence in enumerate(batch_sentence):
        encoding = tokenizer(sentence, truncation=True)
        batch_label[s_idx][0] = -100 
        batch_label[s_idx][len(encoding.tokens())-1:] = -100   
        for char_start, char_end, _, tag in batch_labels[s_idx]:    
            token_start = encoding.char_to_token(char_start) 
            token_end = encoding.char_to_token(char_end - 1)     
            batch_label[s_idx][token_start] = label2id[f"B-{tag}"]
            batch_label[s_idx][token_start+1:token_end+1] = label2id[f"I-{tag}"]
            
    return batch_inputs, torch.tensor(batch_label)






def create_data_loaders(dataset, batch_size, label2id, valid_ratio=0.2):
    trainset,validset = random_split(dataset,lengths=[(1-valid_ratio),valid_ratio])
    logger.info(f"dataset segmentation scale {1-valid_ratio}:{valid_ratio}")




    def train_collate_fn(batch):
        return collote_fn(batch, dataset.tokenizer, label2id)
    
    def valid_collate_fn(batch):
        return collote_fn(batch, dataset.tokenizer, label2id)


    train_dataloader = DataLoader(trainset, batch_size=batch_size, shuffle=True, collate_fn=train_collate_fn)
    valid_dataloader = DataLoader(validset, batch_size=batch_size, shuffle=False, collate_fn=valid_collate_fn)
    

    return train_dataloader, valid_dataloader










