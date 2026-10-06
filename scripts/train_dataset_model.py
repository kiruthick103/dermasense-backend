"""
Training script for Skin Disease Dataset (dataset/SkinDisease)
Fine-tunes a MobileNetV3 architecture on the 22 skin disease categories
from the dataset provided by the user.
"""

import os
import sys
import json
import time
import random
from PIL import Image
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
from torchvision import models
from torch.utils.data import Dataset, DataLoader

torch.manual_seed(42)
random.seed(42)
device = torch.device("cpu")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TRAIN_DIR = os.path.join(BASE_DIR, "dataset", "SkinDisease", "SkinDisease", "train")
TEST_DIR = os.path.join(BASE_DIR, "dataset", "SkinDisease", "SkinDisease", "test")
OUTPUT_MODEL_PATH = os.path.join(BASE_DIR, "model", "trained_dataset_model.pth")
OUTPUT_CLASSES_PATH = os.path.join(BASE_DIR, "model", "dataset_classes.json")


class SkinDiseaseSubsetDataset(Dataset):
    def __init__(self, root_dir, max_per_class=30, transform=None):
        self.transform = transform
        self.samples = []
        self.classes = sorted([d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))])
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}

        for cls_name in self.classes:
            cls_folder = os.path.join(root_dir, cls_name)
            all_files = [
                os.path.join(cls_folder, f)
                for f in os.listdir(cls_folder)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ]
            random.shuffle(all_files)
            selected = all_files[:max_per_class]
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


def train_model():
    print(f"Loading dataset from: {TRAIN_DIR}")
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = SkinDiseaseSubsetDataset(TRAIN_DIR, max_per_class=25, transform=train_transform)
    test_dataset = SkinDiseaseSubsetDataset(TEST_DIR, max_per_class=8, transform=val_transform)

    classes = train_dataset.classes
    num_classes = len(classes)
    print(f"Classes ({num_classes}): {classes}")
    print(f"Training samples: {len(train_dataset)}, Validation samples: {len(test_dataset)}")

    train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=16, shuffle=False)

    print("Building MobileNetV3 transfer learning architecture...")
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)

    # Freeze base feature extractor
    for param in model.features.parameters():
        param.requires_grad = False

    # Unfreeze last 2 layers of features for domain adaptation
    for param in list(model.features.parameters())[-4:]:
        param.requires_grad = True

    # Custom classifier head
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
    optimizer = optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=1e-3,
        weight_decay=1e-4
    )

    epochs = 4
    print(f"Beginning training for {epochs} epochs on CPU...")
    start_time = time.time()

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

        epoch_loss = running_loss / total
        epoch_acc = correct / total

        # Validation
        model.eval()
        val_correct = 0
        val_total = 0
        with torch.no_grad():
            for images, labels in test_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels.data).item()
                val_total += labels.size(0)

        val_acc = val_correct / max(1, val_total)
        print(f"Epoch {epoch}/{epochs} | Train Loss: {epoch_loss:.4f} | Train Acc: {epoch_acc:.1%} | Val Acc: {val_acc:.1%}")

    total_time = time.time() - start_time
    print(f"Training completed in {total_time:.1f}s.")

    # Save model checkpoint
    os.makedirs(os.path.dirname(OUTPUT_MODEL_PATH), exist_ok=True)
    torch.save({
        "state_dict": model.state_dict(),
        "classes": classes,
        "num_classes": num_classes,
        "arch": "mobilenet_v3_small_22class"
    }, OUTPUT_MODEL_PATH)
    print(f"Model checkpoint saved to: {OUTPUT_MODEL_PATH} ({os.path.getsize(OUTPUT_MODEL_PATH) / 1024 / 1024:.2f} MB)")

    # Save classes metadata
    with open(OUTPUT_CLASSES_PATH, "w", encoding="utf-8") as f:
        json.dump(classes, f, indent=2)
    print(f"Class labels saved to: {OUTPUT_CLASSES_PATH}")


if __name__ == "__main__":
    train_model()
