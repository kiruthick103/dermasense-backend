"""
ONNX Export, INT8 Dynamic Quantization, and Parity Verification.
Exports PyTorch MobileNetV3-Small to ONNX, quantizes weights to INT8 to achieve <5MB size,
and verifies numerical parity between PyTorch and ONNX Runtime on a fixed test batch.
"""

import os
import sys
import json
from typing import Any, Dict, Optional
import numpy as np
import torch
import onnx
import onnxruntime as ort
from onnxruntime.quantization import quantize_dynamic, QuantType

# Force UTF-8 on Windows stdout/stderr to handle PyTorch ONNX logger emojis
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from model.train import build_mobilenet_v3_small_binary, set_seed


def export_and_quantize(
    checkpoint_path: Optional[str] = None,
    output_onnx_path: str = "model/model.onnx",
    tolerance_fp32: float = 1e-4,
) -> Dict[str, Any]:
    """
    Exports MobileNetV3-Small to ONNX and quantizes to INT8.
    Verifies PyTorch vs ONNX numerical parity and records model size.
    """
    set_seed(42)
    os.makedirs(os.path.dirname(output_onnx_path), exist_ok=True)
    fp32_onnx_path = os.path.join(os.path.dirname(output_onnx_path), "model_fp32.onnx")

    # 1. Instantiate PyTorch model
    model = build_mobilenet_v3_small_binary(pretrained=False)
    if checkpoint_path and os.path.exists(checkpoint_path):
        ckpt = torch.load(checkpoint_path, map_location="cpu")
        state_dict = ckpt.get("model_state_dict", ckpt)
        model.load_state_dict(state_dict)
    model.eval()

    # Save exact reference weights for parity testing
    weights_path = os.path.join(os.path.dirname(output_onnx_path), "model_weights.pt")
    torch.save(model.state_dict(), weights_path)

    # 2. Export to FP32 ONNX
    dummy_input = torch.randn(1, 3, 224, 224, dtype=torch.float32)
    input_names = ["input"]
    output_names = ["output"]
    dynamic_axes = {"input": {0: "batch_size"}, "output": {0: "batch_size"}}

    torch.onnx.export(
        model,
        dummy_input,
        fp32_onnx_path,
        export_params=True,
        opset_version=18,
        do_constant_folding=True,
        input_names=input_names,
        output_names=output_names,
        dynamic_axes=dynamic_axes,
        dynamo=False,
    )

    # Verify FP32 ONNX graph
    onnx_model = onnx.load(fp32_onnx_path)
    onnx.checker.check_model(onnx_model)
    fp32_size_mb = os.path.getsize(fp32_onnx_path) / (1024 * 1024)

    # 3. Dynamic INT8 Quantization
    quantize_dynamic(
        model_input=fp32_onnx_path,
        model_output=output_onnx_path,
        weight_type=QuantType.QUInt8
    )
    int8_size_mb = os.path.getsize(output_onnx_path) / (1024 * 1024)

    # 4. Numerical Parity Check on Fixed Batch
    torch.manual_seed(999)
    test_batch = torch.randn(4, 3, 224, 224, dtype=torch.float32)

    with torch.no_grad():
        pytorch_logits = model(test_batch).numpy()

    # Run FP32 ONNX
    session_fp32 = ort.InferenceSession(fp32_onnx_path, providers=["CPUExecutionProvider"])
    onnx_fp32_logits = session_fp32.run(None, {"input": test_batch.numpy()})[0]
    max_diff_fp32 = float(np.max(np.abs(pytorch_logits - onnx_fp32_logits)))

    # Run INT8 ONNX
    session_int8 = ort.InferenceSession(output_onnx_path, providers=["CPUExecutionProvider"])
    onnx_int8_logits = session_int8.run(None, {"input": test_batch.numpy()})[0]
    max_diff_int8 = float(np.max(np.abs(pytorch_logits - onnx_int8_logits)))

    parity_fp32_passed = max_diff_fp32 < tolerance_fp32

    report = {
        "fp32_size_mb": round(fp32_size_mb, 2),
        "int8_size_mb": round(int8_size_mb, 2),
        "target_size_met": bool(int8_size_mb < 5.0),
        "max_diff_fp32": float(max_diff_fp32),
        "tolerance_fp32": tolerance_fp32,
        "parity_fp32_passed": parity_fp32_passed,
        "max_diff_int8_vs_pytorch": float(max_diff_int8),
        "quantization_type": "INT8 dynamic",
    }

    report_path = os.path.join(os.path.dirname(output_onnx_path), "parity_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    report = export_and_quantize()
    print("ONNX Export completed:", json.dumps(report, indent=2))
