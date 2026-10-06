"""
Model Training Module for DermaSense.
Implements transfer learning using MobileNetV3-Small for superficial fungal pattern screening.
Uses class-weighted cross-entropy loss, reproducible seeds, and validation checkpoints.
"""

import os
import json
import random
from typing import Any, Dict, Optional, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torchvision.models as models

from model.dataset import RashDataset, split_by_patient_or_source


def set_seed(seed: int = 42) -> None:
    """Enforces deterministic reproducibility across Python, NumPy, and PyTorch."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False


def build_mobilenet_v3_small_binary(pretrained: bool = False) -> nn.Module:
    """
    Constructs a lightweight MobileNetV3-Small binary classification model.
    Class 0: Not clearly compatible
    Class 1: Compatible with superficial fungal pattern
    """
    try:
        if pretrained:
            weights = models.MobileNet_V3_Small_Weights.DEFAULT
            model = models.mobilenet_v3_small(weights=weights)
        else:
            model = models.mobilenet_v3_small(weights=None)
    except Exception:
        model = models.mobilenet_v3_small(weights=None)

    # Replace classifier head for 2-class binary output
    in_features = model.classifier[0].in_features
    model.classifier = nn.Sequential(
        nn.Linear(in_features, 256),
        nn.Hardswish(),
        nn.Dropout(p=0.2),
        nn.Linear(256, 2)
    )
    return model


def train_model(
    train_records: list,
    val_records: list,
    config: Optional[Dict[str, Any]] = None,
    checkpoint_dir: str = "model"
) -> Tuple[nn.Module, Dict[str, Any]]:
    """
    Trains MobileNetV3-Small on skin rash dataset using class-weighted loss.
    """
    cfg = config or {
        "seed": 42,
        "epochs": 10,
        "batch_size": 16,
        "learning_rate": 1e-4,
        "weight_decay": 1e-4,
        "pos_weight": 1.5,
    }

    set_seed(cfg["seed"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = build_mobilenet_v3_small_binary(pretrained=True)
    model.to(device)

    # Weighted Cross-Entropy Loss to handle class imbalance
    class_weights = torch.tensor([1.0, float(cfg["pos_weight"])], device=device)
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.AdamW(
        model.parameters(),
        lr=float(cfg["learning_rate"]),
        weight_decay=float(cfg["weight_decay"])
    )

    train_ds = RashDataset(train_records, is_training=True)
    val_ds = RashDataset(val_records, is_training=False)

    train_loader = DataLoader(train_ds, batch_size=cfg["batch_size"], shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=cfg["batch_size"], shuffle=False)

    history = {"train_loss": [], "val_loss": [], "val_acc": []}
    best_val_loss = float("inf")
    best_weights_path = os.path.join(checkpoint_dir, "best_pytorch_model.pt")

    for epoch in range(cfg["epochs"]):
        model.train()
        running_loss = 0.0
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)

        epoch_train_loss = running_loss / max(1, len(train_ds))

        # Validation step
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device)
                labels = labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                preds = torch.argmax(outputs, dim=1)
                correct += int((preds == labels).sum().item())
                total += labels.size(0)

        epoch_val_loss = val_loss / max(1, total)
        epoch_val_acc = correct / max(1, total)

        history["train_loss"].append(round(epoch_train_loss, 4))
        history["val_loss"].append(round(epoch_val_loss, 4))
        history["val_acc"].append(round(epoch_val_acc, 4))

        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            os.makedirs(checkpoint_dir, exist_ok=True)
            torch.save({
                "model_state_dict": model.state_dict(),
                "config": cfg,
                "epoch": epoch,
                "best_val_loss": best_val_loss,
            }, best_weights_path)

    # Save training metadata
    meta_path = os.path.join(checkpoint_dir, "training_meta.json")
    with open(meta_path, "w") as f:
        json.dump({"config": cfg, "history": history}, f, indent=2)

    return model, history


if __name__ == "__main__":
    print("DermaSense MobileNetV3-Small training module loaded.")
