import sys
import os
import numpy as np
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.multi_model_engine import get_available_models_info, predict_ensemble

print("=== REGISTERED MULTI-MODELS IN PROJECT ===")
models = get_available_models_info()
for m in models:
    print(f"- [{m['id']}] {m['name']} ({m['framework']}) -> {m['status']}")

# Run test image through the ensemble
img = Image.fromarray(np.random.randint(100, 200, (224, 224, 3), dtype=np.uint8))
print("\n=== EXECUTING MULTI-MODEL ENSEMBLE CONSENSUS ===")
result = predict_ensemble(img)

print(f"Top Consensus: {result['top_display_name']} ({result['calibrated_prob']*100:.1f}%)")
print(f"Strength Rating: {result['strength']}")
print(f"Consensus Agreement: {result['consensus_agreement']}")
print(f"Total Latency: {result['total_latency_ms']} ms")
print(f"Models Evaluated: {result['models_evaluated']}")

print("\nIndividual Model Outputs:")
for ind in result['individual_breakdown']:
    print(f"  * {ind['model_name']}: {ind['predicted_class']} ({ind['confidence']*100:.1f}%) [{ind['latency_ms']} ms]")
