'''
author: whx
date: 2025/9/9
description: loading model

'''


import torch
import torch.nn as nn
import logging
from transformers import BertPreTrainedModel, BertModel, AutoConfig

logger = logging.getLogger(__name__)


class BertForClassification(BertPreTrainedModel):
    def __init__(self, config):
        super().__init__(config)
        self.bert = BertModel(config, add_pooling_layer=True)  
        self.dropout = nn.Dropout(config.hidden_dropout_prob) 
        self.classifier = nn.Linear(config.hidden_size, 2)  
        self.post_init()
        logger.info(f"ner model initialization completed classifier dimensions {config.hidden_size} -> 2")

    def forward(self, x):
        bert_output = self.bert(**x)  
        sequence_output = bert_output.pooler_output  
        sequence_output = self.dropout(sequence_output)  
        logits = self.classifier(sequence_output)  
        return logits
    

def load_model(model_path, device):

    config = AutoConfig.from_pretrained(model_path)
    model = BertForClassification.from_pretrained(model_path, config=config).to(device)
    logger.info(f"model loading completed {model_path}, using the device: {device}")

    return model    