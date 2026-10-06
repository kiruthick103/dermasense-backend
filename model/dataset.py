"""
Model Dataset, Augmentation, and Splitting Pipeline.
Implements patient/source-level splitting, perceptual hashing (dHash) for duplicate removal,
and realistic phone-photography augmentations.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import numpy as np
import cv2
import torch
from torch.utils.data import Dataset
import torchvision.transforms as T


def compute_dhash(image: np.ndarray, hash_size: int = 8) -> int:
    """
    Computes difference hash (dHash) for near-duplicate image detection.
    Compares adjacent pixels along rows.
    """
    if image.ndim == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    return sum([2 ** i for i, v in enumerate(diff.flatten()) if v])


def filter_near_duplicates(
    image_paths: List[str],
    hamming_threshold: int = 3
) -> List[str]:
    """
    Filters near-duplicate images using dHash Hamming distance.
    Ensures no visual leakage across datasets or patients.
    """
    unique_paths: List[str] = []
    seen_hashes: List[int] = []

    for path in image_paths:
        img = cv2.imread(path)
        if img is None:
            continue
        h = compute_dhash(img)
        is_duplicate = False
        for sh in seen_hashes:
            # Hamming distance via XOR bit count
            xor_val = h ^ sh
            dist = bin(xor_val).count("1")
            if dist <= hamming_threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            seen_hashes.append(h)
            unique_paths.append(path)

    return unique_paths


def split_by_patient_or_source(
    records: List[Dict[str, Any]],
    patient_key: str = "patient_id",
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    seed: int = 42
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Splits samples strictly at the patient/source level to prevent data leakage.
    Never splits randomly by image when multiple images belong to the same patient.
    """
    rng = np.random.RandomState(seed)

    # Group records by patient ID
    patient_groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in records:
        pid = str(r.get(patient_key, r.get("image_id", "")))
        patient_groups.setdefault(pid, []).append(r)

    unique_patients = list(patient_groups.keys())
    rng.shuffle(unique_patients)

    n_total = len(unique_patients)
    n_train = int(round(train_ratio * n_total))
    n_val = int(round(val_ratio * n_total))

    train_patients = set(unique_patients[:n_train])
    val_patients = set(unique_patients[n_train : n_train + n_val])
    test_patients = set(unique_patients[n_train + n_val :])

    train_data = [r for pid in train_patients for r in patient_groups[pid]]
    val_data = [r for pid in val_patients for r in patient_groups[pid]]
    test_data = [r for pid in test_patients for r in patient_groups[pid]]

    return train_data, val_data, test_data


class RealisticPhoneAugmentations:
    """
    Realistic augmentations modeling real phone camera artifacts:
    - Mild blur
    - Color temperature / white balance shifts
    - Lighting / brightness adjustments
    - Mild rotation (-15 to +15 deg)
    """
    def __init__(self, target_size: int = 224):
        self.target_size = target_size
        self.transforms = T.Compose([
            T.ToPILImage(),
            T.Resize((target_size, target_size)),
            T.RandomRotation(degrees=15),
            T.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
            T.RandomApply([T.GaussianBlur(kernel_size=(3, 3), sigma=(0.1, 1.5))], p=0.3),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

    def __call__(self, img_bgr: np.ndarray) -> torch.Tensor:
        # Convert BGR to RGB for PyTorch vision transforms
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        return self.transforms(img_rgb)


class RashDataset(Dataset):
    """PyTorch Dataset for skin rash screening images."""
    def __init__(
        self,
        records: List[Dict[str, Any]],
        transform: Optional[Any] = None,
        is_training: bool = False
    ):
        self.records = records
        self.is_training = is_training
        self.transform = transform or (
            RealisticPhoneAugmentations(224) if is_training else T.Compose([
                T.ToPILImage(),
                T.Resize((224, 224)),
                T.ToTensor(),
                T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
        )

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        item = self.records[idx]
        image_path = item.get("image_path", "")
        img = cv2.imread(image_path)
        if img is None:
            # Fallback zero image if path unreadable
            img = np.zeros((224, 224, 3), dtype=np.uint8)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        tensor = self.transform(img)
        label = int(item.get("label", 0))
        return tensor, label
