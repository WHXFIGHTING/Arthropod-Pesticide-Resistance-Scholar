'''
author: whx
date: 2025/9/9
description: training module

'''



import torch
import logging
from tqdm.auto import tqdm
from seqeval.metrics import classification_report
from seqeval.scheme import IOB2
from torch import nn
from transformers import AdamW, get_scheduler

logger = logging.getLogger(__name__)





def train_loop(dataloader, model, loss_fn, optimizer, lr_scheduler, epoch, total_loss, config):
    progress_bar = tqdm(range(len(dataloader)))           
    progress_bar.set_description(f'loss: {0:>7f}')        
    finish_batch_num = (epoch-1) * len(dataloader)     
    
    model.train()                     
    for batch, (X, y) in enumerate(dataloader, start=1):  
        X, y = X.to(config.DEVICE), y.to(config.DEVICE) 
        pred = model(X)
        loss = loss_fn(pred.permute(0, 2, 1), y)   
        optimizer.zero_grad()   
        loss.backward()    
        optimizer.step()  
        lr_scheduler.step() 

        total_loss += loss.item()
        progress_bar.set_description(f'loss: {total_loss/(finish_batch_num + batch):>7f}')
        progress_bar.update(1)
    return total_loss



def test_loop(dataloader, model, config):
    true_labels, true_predictions = [], []

    model.eval()   
    with torch.no_grad():    
        for X, y in tqdm(dataloader):
            X, y = X.to(config.DEVICE), y.to(config.DEVICE)
            pred = model(X)
            predictions = pred.argmax(dim=-1).cpu().numpy().tolist()   
            labels = y.cpu().numpy().tolist()
            true_labels += [[config.ID2LABEL[int(l)] for l in label if l != -100] for label in labels]
            true_predictions += [
                [config.ID2LABEL[int(p)] for (p, l) in zip(prediction, label) if l != -100]
                for prediction, label in zip(predictions, labels)
            ]
    print(classification_report(true_labels, true_predictions, mode='strict', scheme=IOB2))
    return classification_report(   
      true_labels, 
      true_predictions, 
      mode='strict', 
      scheme=IOB2,        
      output_dict=True
    )



def setup_training(model, learning_rate, epoch_num, train_dataloader):
    loss_fn = nn.CrossEntropyLoss()   
    optimizer = AdamW(model.parameters(), lr=learning_rate)  
    lr_scheduler = get_scheduler(
        "linear",
        optimizer=optimizer,
        num_warmup_steps=0,
        num_training_steps=epoch_num*len(train_dataloader),
    )   
    
    logger.info(f"training component setup complete lr={learning_rate}, epochs={epoch_num}")
    
    return loss_fn, optimizer, lr_scheduler





def train_model(model, train_dataloader, valid_dataloader, config):

    loss_fn, optimizer, lr_scheduler = setup_training(
        model, 
        config.learning_rate, 
        config.epoch_num, 
        train_dataloader
    )


    total_loss = 0.
    best_f1 = 0.
    for t in range(config.epoch_num):
        print(f"Epoch {t+1}/{config.epoch_num}\n-------------------------------")
        total_loss = train_loop(train_dataloader, model, loss_fn, optimizer, lr_scheduler, t+1, total_loss, config)
        metrics = test_loop(valid_dataloader, model, config)
        valid_macro_f1, valid_micro_f1 = metrics['macro avg']['f1-score'], metrics['micro avg']['f1-score']
        valid_f1 = metrics['weighted avg']['f1-score']

        logger.info(f"Epoch {t+1}: Macro F1={valid_macro_f1:.4f}, Micro F1={valid_micro_f1:.4f}")
        if valid_f1 > best_f1:
            best_f1 = valid_f1
            logger.info(f'saving new weights... Best F1: {best_f1:.4f}')
            torch.save(
                model.state_dict(), 
                f'{config.model_save_path}/epoch_{t+1}_valid_macrof1_{(100*valid_macro_f1):0.3f}_microf1_{(100*valid_micro_f1):0.3f}_weights.bin'
            )

    logger.info("done!")
    return best_f1
