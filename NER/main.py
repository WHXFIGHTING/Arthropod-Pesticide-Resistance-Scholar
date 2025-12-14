# test_dataset.py
"""

"""


import sys
import torch
import random
import numpy as np
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))



from config.settings import Config
from data.dataset import NERDataset, create_data_loaders
from model.ner_model import BertForNER, load_model
from utils.trainer import train_model


def main():
    print("1. ...")
    config = Config()
    config.set_path_params(
        model_path=r'',
        data_path=r'',
        model_save_path=r''
    )

    config.set_training_params(
        learning_rate=1e-5,
        batch_size=32,
        epoch_num=10,
        seed=42
    )
    
    config.hidden_size = 768  


    torch.manual_seed(config.seed)
    torch.cuda.manual_seed(config.seed)
    torch.cuda.manual_seed_all(config.seed)
    random.seed(config.seed)
    np.random.seed(config.seed)
    os.environ['PYTHONHASHSEED'] = str(config.seed)
    print(f"random seed has been set: {config.seed}")




    dataset = NERDataset(config.data_path, config.model_path)
    

    print("2. ...")
    train_loader, valid_loader = create_data_loaders(
        dataset, 
        batch_size=4,
        label2id=config.LABEL2ID,
        valid_ratio=0.2,
    )
    
    print("\n✅ dataset loading completed!")

    print("3. ...")
    model = load_model(config.model_path, config.ID2LABEL, config.DEVICE)

    print("\n✅ model loading completed!")


    print("4. ...")
    best_f1 = train_model(model, train_loader, valid_loader, config)
    print(f"best f1 score: {best_f1:.4f}")

    print("\n✅ model training completed!")

    print("=================== ner model training completed ===================")



if __name__ == "__main__":
    main()