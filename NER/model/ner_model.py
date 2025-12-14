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


class BertForNER(BertPreTrainedModel):
    def __init__(self, config, id2label):
        super().__init__(config)
        self.bert = BertModel(config, add_pooling_layer=False)  
        self.dropout = nn.Dropout(config.hidden_dropout_prob) 
        self.classifier = nn.Linear(config.hidden_size, len(id2label))  
        self.post_init()
        logger.info(f"ner model initialization completed classifier dimensions {config.hidden_size} -> {len(id2label)}")

    def forward(self, x):
        bert_output = self.bert(**x)  
        sequence_output = bert_output.last_hidden_state   
        sequence_output = self.dropout(sequence_output)  
        logits = self.classifier(sequence_output)  
        return logits
    


def load_model(model_path, id2label, device):

    config = AutoConfig.from_pretrained(model_path)
    model = BertForNER.from_pretrained(model_path, config=config, id2label=id2label).to(device)
    logger.info(f"model loading completed {model_path}, using the device: {device}")

    return model    