import os
import sys
import torch
import torchvision.transforms as transforms
from PIL import Image

sys.path.insert(0, os.path.abspath("."))
from model.multi_model_engine import _load_pytorch_predictor

mob_pred = _load_pytorch_predictor('mobilenetv3')
eff_pred = _load_pytorch_predictor('efficientnet_b0')

classes_alphanumeric = [
    'Eczema',
    'Warts Molluscum and other Viral Infections',
    'Melanoma',
    'Atopic Dermatitis',
    'Basal Cell Carcinoma (BCC)',
    'Melanocytic Nevi (NV)',
    'Benign Keratosis-like Lesions (BKL)',
    'Psoriasis pictures Lichen Planus and related diseases',
    'Seborrheic Keratoses and other Benign Tumors',
    'Tinea Ringworm Candidiasis and other Fungal Infections'
]

classes_1_to_10 = [
    'Eczema',
    'Melanoma',
    'Atopic Dermatitis',
    'Basal Cell Carcinoma (BCC)',
    'Melanocytic Nevi (NV)',
    'Benign Keratosis-like Lesions (BKL)',
    'Psoriasis pictures, Lichen Planus and related diseases',
    'Seborrheic Keratoses and other Benign Tumors',
    'Tinea Ringworm Candidiasis and other Fungal Infections',
    'Warts Molluscum and other Viral Infections'
]

tinea_dir = 'dataset/SkinDisease/SkinDisease/test/Tinea'
eczema_dir = 'dataset/SkinDisease/SkinDisease/test/Eczema'
psoriasis_dir = 'dataset/SkinDisease/SkinDisease/test/Psoriasis'
warts_dir = 'dataset/SkinDisease/SkinDisease/test/Warts'

test_imgs = [
    ('Tinea', os.path.join(tinea_dir, os.listdir(tinea_dir)[0])),
    ('Tinea2', os.path.join(tinea_dir, os.listdir(tinea_dir)[1])),
    ('Eczema', os.path.join(eczema_dir, os.listdir(eczema_dir)[0])),
    ('Psoriasis', os.path.join(psoriasis_dir, os.listdir(psoriasis_dir)[0])),
    ('Warts', os.path.join(warts_dir, os.listdir(warts_dir)[0])),
]

print("Device:", torch.device('cuda' if torch.cuda.is_available() else 'cpu'))
for label, p in test_imgs:
    img = Image.open(p).convert('RGB')
    tensor = mob_pred.transform(img).unsqueeze(0)
    with torch.no_grad():
        out_mob = mob_pred.model(tensor)
        idx_mob = torch.argmax(out_mob, dim=1).item()
        prob_mob = torch.softmax(out_mob, dim=1)[0][idx_mob].item()
        
        out_eff = eff_pred.model(tensor)
        idx_eff = torch.argmax(out_eff, dim=1).item()
        prob_eff = torch.softmax(out_eff, dim=1)[0][idx_eff].item()
        
    print(f"=== Ground truth: {label} ({os.path.basename(p)}) ===")
    print(f"  MobileNet: idx={idx_mob} ({prob_mob:.1%}) -> AlphaSort: [{classes_alphanumeric[idx_mob]}] | 1-10: [{classes_1_to_10[idx_mob]}]")
    print(f"  EffNet:    idx={idx_eff} ({prob_eff:.1%}) -> AlphaSort: [{classes_alphanumeric[idx_eff]}] | 1-10: [{classes_1_to_10[idx_eff]}]")
