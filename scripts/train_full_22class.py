"""
Production training pipeline for 22 Skin Disease Categories.
Trains on dataset/SkinDisease/SkinDisease with data augmentation,
exports PyTorch checkpoint and optimized ONNX weights.
"""

import os
import sys
import json
import time
import random
from PIL import Image
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from torchvision import models
from torch.utils.data import Dataset, DataLoader

torch.manual_seed(42)
random.seed(42)
np.random.seed(42)
device = torch.device("cpu")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TRAIN_DIR = os.path.join(BASE_DIR, "dataset", "SkinDisease", "SkinDisease", "train")
TEST_DIR = os.path.join(BASE_DIR, "dataset", "SkinDisease", "SkinDisease", "test")
PTH_OUTPUT = os.path.join(BASE_DIR, "model", "trained_dataset_model.pth")
ONNX_OUTPUT = os.path.join(BASE_DIR, "model", "dataset_22class.onnx")
CLASSES_OUTPUT = os.path.join(BASE_DIR, "model", "dataset_classes.json")


class BalancedSkinDiseaseDataset(Dataset):
    def __init__(self, root_dir, max_per_class=40, transform=None):
        self.transform = transform
        self.samples = []
        self.classes = sorted([d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))])
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}

        for cls_name in self.classes:
            folder = os.path.join(root_dir, cls_name)
            files = [
                os.path.join(folder, f)
                for f in os.listdir(folder)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ]
            random.shuffle(files)
            selected = files[:max_per_class]
            for fpath in selected:
                self.samples.append((fpath, self.class_to_idx[cls_name]))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        try:
            image = Image.open(path).convert("RGB")
        except Exception:
            image = Image.new("RGB", (224, 224), (128, 128, 128))
        if self.transform:
            image = self.transform(image)
        return image, label


def run_training():
    print(f"== Starting 22-Class Skin Disease Training ==")
    print(f"Source train directory: {TRAIN_DIR}")

    train_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_set = BalancedSkinDiseaseDataset(TRAIN_DIR, max_per_class=35, transform=train_tf)
    test_set = BalancedSkinDiseaseDataset(TEST_DIR, max_per_class=10, transform=val_tf)

    classes = train_set.classes
    num_classes = len(classes)
    print(f"Total classes: {num_classes}")
    print(f"Training samples: {len(train_set)} | Test samples: {len(test_set)}")

    train_loader = DataLoader(train_set, batch_size=16, shuffle=True)
    test_loader = DataLoader(test_set, batch_size=16, shuffle=False)

    # Initialize MobileNetV3 with pre-trained ImageNet weights
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)

    # Fine-tune classifier & top feature blocks
    for param in model.features.parameters():
        param.requires_grad = False
    for param in list(model.features.parameters())[-6:]:
        param.requires_grad = True

    in_features = model.classifier[0].in_features
    model.classifier = nn.Sequential(
        nn.Linear(in_features, 512),
        nn.Hardswish(),
        nn.Dropout(p=0.3),
        nn.Linear(512, 256),
        nn.ReLU(),
        nn.Dropout(p=0.2),
        nn.Linear(256, num_classes)
    )
    model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1.2e-3, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=5)

    epochs = 5
    print(f"Training for {epochs} epochs on CPU...")
    t0 = time.time()

    best_val_acc = 0.0
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss, train_correct, train_total = 0.0, 0, 0

        for imgs, lbls in train_loader:
            imgs, lbls = imgs.to(device), lbls.to(device)
            optimizer.zero_grad()
            outputs = model(imgs)
            loss = criterion(outputs, lbls)
            loss.backward()
            optimizer.step()

            train_loss += loss.item() * imgs.size(0)
            _, preds = torch.max(outputs, 1)
            train_correct += torch.sum(preds == lbls.data).item()
            train_total += lbls.size(0)

        scheduler.step()
        epoch_loss = train_loss / train_total
        epoch_acc = train_correct / train_total

        # Validation step
        model.eval()
        val_correct, val_total = 0, 0
        with torch.no_grad():
            for imgs, lbls in test_loader:
                imgs, lbls = imgs.to(device), lbls.to(device)
                outputs = model(imgs)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == lbls.data).item()
                val_total += lbls.size(0)

        val_acc = val_correct / max(1, val_total)
        print(f"Epoch {epoch}/{epochs}: Train Loss: {epoch_loss:.4f} | Train Acc: {epoch_acc:.1%} | Val Acc: {val_acc:.1%}")

    print(f"Training finished in {time.time() - t0:.1f}s.")

    # 1. Save PyTorch checkpoint
    os.makedirs(os.path.dirname(PTH_OUTPUT), exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(),
        "classes": classes,
        "num_classes": num_classes,
        "arch": "mobilenet_v3_small_22class"
    }, PTH_OUTPUT)
    print(f"Saved PyTorch model to: {PTH_OUTPUT}")

    # 2. Save classes metadata
    with open(CLASSES_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(classes, f, indent=2)
    print(f"Saved classes to: {CLASSES_OUTPUT}")

    # 3. Export to ONNX
    print("Exporting model to ONNX...")
    model.eval()
    dummy = torch.randn(1, 3, 224, 224)
    torch.onnx.export(
        model,
        dummy,
        ONNX_OUTPUT,
        input_names=["input"],
        output_names=["output"],
        opset_version=17
    )
    print(f"Saved ONNX model to: {ONNX_OUTPUT}")


if __name__ == "__main__":
    run_training()
