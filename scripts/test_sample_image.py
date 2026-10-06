import sys
import os
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.multi_model_engine import predict_ensemble

img_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "samples", "sample_ring_rash.jpg")
print(f"Testing on sample ring rash image: {img_path}")
img = Image.open(img_path)

res = predict_ensemble(img)
prob_pct = res['calibrated_prob'] * 100
print(f"Top Pattern: {res['top_display_name']} ({prob_pct:.1f}%)")
print(f"Strength: {res['strength']}")
print(f"Agreement: {res['consensus_agreement']}")
print("\nIndividual models:")
for ind in res['individual_breakdown']:
    c_pct = ind['confidence'] * 100
    print(f"  {ind['model_name']}: {ind['predicted_class']} ({c_pct:.1f}%) -> group: {ind['canonical_group']}")
