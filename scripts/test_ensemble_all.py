import os
import sys
from PIL import Image

sys.path.insert(0, os.path.abspath("."))
from model.multi_model_engine import predict_ensemble

tinea_path = os.path.join('dataset/SkinDisease/SkinDisease/test/Tinea', os.listdir('dataset/SkinDisease/SkinDisease/test/Tinea')[0])
eczema_path = os.path.join('dataset/SkinDisease/SkinDisease/test/Eczema', os.listdir('dataset/SkinDisease/SkinDisease/test/Eczema')[0])
psoriasis_path = os.path.join('dataset/SkinDisease/SkinDisease/test/Psoriasis', os.listdir('dataset/SkinDisease/SkinDisease/test/Psoriasis')[0])
warts_path = os.path.join('dataset/SkinDisease/SkinDisease/test/Warts', os.listdir('dataset/SkinDisease/SkinDisease/test/Warts')[0])

tests = [
    ('Tinea', tinea_path),
    ('Eczema', eczema_path),
    ('Psoriasis', psoriasis_path),
    ('Warts', warts_path),
]

for label, p in tests:
    img = Image.open(p)
    res = predict_ensemble(img)
    print(f"=== Ground truth: {label} ===")
    print("  Top display name:   ", res["top_display_name"])
    print("  Predicted disease:  ", res["predicted_disease"])
    print("  Canonical group:    ", res["top_pattern"])
    print("  Calibrated prob:    ", f"{res['calibrated_prob']:.1%}")
    print("  Strength:           ", res["strength"])
    print("  Consensus agreement:", res["consensus_agreement"])
    print("  Breakdown:")
    for m in res["individual_breakdown"]:
        print(f"    - {m['model_name']}: {m['predicted_class']} ({m['confidence']:.1%})")
