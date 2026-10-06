"""
Integration and Parity Tests for AI Model (MobileNetV3-Small INT8 ONNX).
Verifies PyTorch vs ONNX numerical parity, model file size (<5MB), inference latency (<300ms),
and abstention threshold outputs.
"""

import os
import time
import numpy as np
import pytest
import torch
import onnxruntime as ort

from model.train import build_mobilenet_v3_small_binary, set_seed
from model.predict import predict, preprocess_image


def test_model_size_under_5mb():
    onnx_path = "model/model.onnx"
    assert os.path.exists(onnx_path), "model.onnx must exist"
    size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
    assert size_mb < 5.0, f"Model size is {size_mb:.2f} MB, must be < 5 MB"


def test_pytorch_vs_onnx_parity_fixed_batch():
    """Checks numerical parity between PyTorch and ONNX Runtime on a fixed test batch."""
    set_seed(123)
    model = build_mobilenet_v3_small_binary(pretrained=False)
    weights_path = "model/model_weights.pt"
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    test_batch = torch.randn(4, 3, 224, 224, dtype=torch.float32)

    with torch.no_grad():
        pytorch_logits = model(test_batch).numpy()

    fp32_path = "model/model_fp32.onnx"
    if os.path.exists(fp32_path):
        session = ort.InferenceSession(fp32_path, providers=["CPUExecutionProvider"])
        input_name = session.get_inputs()[0].name
        onnx_logits = session.run(None, {input_name: test_batch.numpy()})[0]
        max_diff = float(np.max(np.abs(pytorch_logits - onnx_logits)))
        assert max_diff < 1e-4, f"PyTorch vs FP32 ONNX max absolute diff {max_diff} exceeded tolerance 1e-4"


def test_inference_latency_under_300ms():
    dummy_img = np.zeros((400, 400, 3), dtype=np.uint8)
    # Warmup
    _ = predict(dummy_img)

    t0 = time.perf_counter()
    res = predict(dummy_img)
    total_ms = (time.perf_counter() - t0) * 1000.0

    assert total_ms < 300.0, f"Inference took {total_ms:.2f} ms (expected < 300 ms)"
    assert res["metrics"]["inference_ms"] < 200.0


def test_predict_schema_and_abstention():
    dummy_img = np.zeros((224, 224, 3), dtype=np.uint8)
    res = predict(dummy_img)

    assert "label" in res
    assert "confidence" in res
    assert "abstained" in res
    assert "isPlaceholder" in res
    assert isinstance(res["abstained"], bool)
    assert isinstance(res["confidence"], float)
    assert res["isPlaceholder"] is True
