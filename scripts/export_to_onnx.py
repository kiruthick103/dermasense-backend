import os
import sys
import torch
from torchvision import models
import torch.nn as nn

sys.path.insert(0, os.path.abspath("."))
from model.multi_model_engine import _load_pytorch_predictor

# 1. Export 10-class MobileNetV3
print("Exporting 10-class MobileNetV3...")
pred = _load_pytorch_predictor('mobilenetv3')
pred.model.eval()
dummy = torch.randn(1, 3, 224, 224)
onnx_10_path = os.path.abspath('model/mobilenetv3_10class.onnx')

torch.onnx.export(
    pred.model,
    dummy,
    onnx_10_path,
    input_names=['input'],
    output_names=['output'],
    opset_version=17
)
print("Saved 10-class ONNX to:", onnx_10_path, f"({os.path.getsize(onnx_10_path) / 1024 / 1024:.2f} MB)")

# 2. Export 22-class Dataset MobileNetV3
print("Exporting 22-class Dataset MobileNetV3...")
ckpt = torch.load('model/trained_dataset_model.pth', map_location='cpu')
m22 = models.mobilenet_v3_small(weights=None)
in_features = m22.classifier[0].in_features
m22.classifier = nn.Sequential(
    nn.Linear(in_features, 512),
    nn.Hardswish(),
    nn.Dropout(p=0.3),
    nn.Linear(512, 256),
    nn.ReLU(),
    nn.Dropout(p=0.2),
    nn.Linear(256, ckpt['num_classes'])
)
m22.load_state_dict(ckpt['state_dict'])
m22.eval()

onnx_22_path = os.path.abspath('model/dataset_22class.onnx')
torch.onnx.export(
    m22,
    dummy,
    onnx_22_path,
    input_names=['input'],
    output_names=['output'],
    opset_version=17
)
print("Saved 22-class ONNX to:", onnx_22_path, f"({os.path.getsize(onnx_22_path) / 1024 / 1024:.2f} MB)")
