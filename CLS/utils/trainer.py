'''
author: whx
date: 2025/9/16
description: training module

'''



import torch
import logging
from tqdm.auto import tqdm
from torch import nn
from transformers import AdamW, get_scheduler

logger = logging.getLogger(__name__)






def train_loop(dataloader, model, loss_fn, optimizer, lr_scheduler, epoch, total_loss, config):
    progress_bar = tqdm(range(len(dataloader)))            
    progress_bar.set_description(f'loss: ----')        
    finish_batch_num = (epoch-1) * len(dataloader)      
    
    model.train()                      
    for batch, (X, y) in enumerate(dataloader, start=1):  
        X, y = X.to(config.DEVICE), y.to(config.DEVICE) 
        pred = model(X)
        loss = loss_fn(pred, y)   
        optimizer.zero_grad()  
        loss.backward()    
        optimizer.step()  
        lr_scheduler.step() 

        total_loss += loss.item()
        progress_bar.set_description(f'loss: {total_loss/(finish_batch_num + batch):>7f}')
        progress_bar.update(1)
    return total_loss



def test_loop(dataloader, model, config):
    model.eval()   
    correct = 0
    total   = 0
    with torch.no_grad():    
        for X, y in tqdm(dataloader):
            X, y = X.to(config.DEVICE), y.to(config.DEVICE)
            pred = model(X)
            predictions = pred.argmax(dim=-1)           
            correct += (predictions == y).sum().item()  
            total += y.size(0)              
    acc = correct / total           
    print(f"Valid Acc: {acc:.4f}")
    return {"accuracy": acc}


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
    best_acc = 0.
    for t in range(config.epoch_num):
        print(f"Epoch {t+1}/{config.epoch_num}\n-------------------------------")
        total_loss = train_loop(train_dataloader, model, loss_fn, optimizer, lr_scheduler, t+1, total_loss, config)
        metrics = test_loop(valid_dataloader, model, config)
        valid_acc = metrics["accuracy"]
        if valid_acc > best_acc:       
            best_acc = valid_acc
            torch.save(
                model.state_dict(),
                f"{config.model_save_path}/Epoch {t+1}-best_acc_{100*valid_acc:.2f}.bin")

        logger.info(f"Epoch {t+1}: acc={valid_acc:.4f}")
    logger.info("done!")
    return best_acc
