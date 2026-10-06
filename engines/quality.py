"""
Engine 1: Photo Quality Assessment & Upload Verification
Deterministic, purely functional quality engine with no I/O, no network, and no global state.
Evaluates blur, brightness, glare, skin coverage, and upload-specific artifacts (compression, moire, cartoon, resolution).
Computes Individual Typology Angle (ITA) strictly for fairness auditing and contrast normalisation.
"""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import cv2


def calculate_ita(l_channel: np.ndarray, b_channel: np.ndarray, skin_mask: np.ndarray) -> Tuple[float, str]:
    """
    Computes Individual Typology Angle (ITA) on healthy skin pixels:
    ITA = arctan((L* - 50) / b*) * (180 / pi)
    Used ONLY for fairness reporting and contrast normalisation, NEVER to alter risk scores.
    """
    skin_pts = skin_mask > 0
    if not np.any(skin_pts):
        return 0.0, "UNKNOWN"

    l_vals = l_channel[skin_pts]
    b_vals = b_channel[skin_pts]

    # Convert uint8 OpenCV Lab (L: 0-255 -> 0-100, b: 0-255 -> -128-127)
    l_star = np.median(l_vals) * (100.0 / 255.0)
    b_star = (np.median(b_vals) - 128.0)

    denominator = max(abs(b_star), 1e-4) * (1 if b_star >= 0 else -1)
    ita_rad = np.arctan((l_star - 50.0) / denominator)
    ita_deg = float(ita_rad * (180.0 / np.pi))

    # Standard Fitzpatrick ITA Bands
    if ita_deg > 55:
        tone_group = "Type I-II (Very Light)"
    elif ita_deg > 41:
        tone_group = "Type III (Light)"
    elif ita_deg > 28:
        tone_group = "Type IV (Intermediate)"
    elif ita_deg > 10:
        tone_group = "Type V (Tan/Brown)"
    else:
        tone_group = "Type VI (Dark)"

    return round(ita_deg, 2), tone_group


def detect_upload_artifacts(image: np.ndarray, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Detects upload-specific quality defects:
    - Very low resolution (< 320px)
    - Heavy JPEG compression blocking
    - Moire / Screen grid artifact (FFT high-frequency peaks)
    - Drawing or cartoon (edge-to-color entropy ratio)
    """
    cfg = config or {}
    min_w = int(cfg.get("upload_min_width", 320))
    min_h = int(cfg.get("upload_min_height", 320))
    fft_thresh = float(cfg.get("upload_fft_moire_threshold", 0.45))
    cartoon_thresh = float(cfg.get("upload_cartoon_edge_ratio_max", 0.70))

    h, w = image.shape[:2]
    flags: List[str] = []
    tips: List[str] = []

    # 1. Resolution Check
    if w < min_w or h < min_h:
        flags.append("LOW_RESOLUTION")
        tips.append("Image resolution is very low. Please upload an original photo.")

    # 2. Convert to grayscale for frequency and compression checks
    if image.ndim == 2:
        gray = image
    else:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # 3. Moire / Screenshot Detection via 2D FFT
    # Screen grids create high-energy periodic peaks outside center DC
    if min(h, w) >= 128:
        small_gray = cv2.resize(gray, (128, 128))
        f_transform = np.fft.fft2(small_gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1e-5)

        # Mask out center DC component (radius 16)
        cy, cx = 64, 64
        y, x = np.ogrid[:128, :128]
        center_mask = ((x - cx)**2 + (y - cy)**2) <= 16**2
        magnitude_spectrum[center_mask] = 0

        max_peak = float(np.max(magnitude_spectrum))
        mean_energy = float(np.mean(magnitude_spectrum))
        moire_ratio = max_peak / max(mean_energy, 1e-4) if mean_energy > 0 else 0

        if moire_ratio > 3.8:
            flags.append("SCREENSHOT_OR_MOIRE")
            tips.append("This appears to be a photo of a screen or digital display. Please photograph skin directly.")

    # 4. Cartoon / Drawing Detection (Posterization & Color Count)
    # Natural skin photos have continuous gradients; drawings have flat blocks with stark edges
    edges = cv2.Canny(gray, 50, 150)
    edge_ratio = float(np.sum(edges > 0)) / float(edges.size)
    unique_colors = len(np.unique(cv2.resize(gray, (64, 64))))

    if unique_colors < 25 and edge_ratio > 0.08:
        flags.append("CARTOON_OR_DRAWING")
        tips.append("This appears to be a drawing or graphic, not a clinical skin photo.")

    # 5. JPEG Blockiness / Compression Estimation
    # Measure 8x8 grid boundary discontinuity relative to interior pixel differences
    if min(h, w) >= 64:
        diff_horizontal = np.abs(gray[:, 1:] - gray[:, :-1])
        block_boundary_diff = np.mean(diff_horizontal[:, 7::8])
        interior_diff = np.mean(diff_horizontal[:, [i for i in range(diff_horizontal.shape[1]) if i % 8 != 7]])
        blockiness = float(block_boundary_diff / max(interior_diff, 1e-4)) if interior_diff > 0 else 1.0

        if blockiness > 1.35:
            flags.append("HEAVY_COMPRESSION")
            tips.append("Image is heavily compressed (e.g. forwarded multiple times). Please upload the camera original.")

    return {
        "has_upload_flags": len(flags) > 0,
        "flags": flags,
        "tips": tips,
        "caps_model_strength": len(flags) > 0
    }


def assess_image_quality(
    image: np.ndarray,
    config: Optional[Dict[str, Any]] = None,
    source: str = "camera"
) -> Dict[str, Any]:
    """
    Evaluates rash photograph quality against deterministic thresholds.
    Handles both live camera captures and gallery file uploads.
    """
    if image is None or not isinstance(image, np.ndarray) or image.size == 0:
        return {
            "acceptable": False,
            "reasons": ["OBSTRUCTED"],
            "measurements": {
                "blur": 0.0,
                "brightness_mean": 0.0,
                "brightness_p05": 0.0,
                "brightness_p95": 0.0,
                "glare_fraction": 0.0,
                "skin_fraction": 0.0,
                "largest_skin_region_fraction": 0.0,
                "ita": 0.0,
                "skin_tone_group": "UNKNOWN"
            },
            "upload_quality": {"has_upload_flags": False, "flags": [], "tips": []},
            "tips": ["Make sure the affected skin is not covered."]
        }

    # Configuration thresholds
    cfg = config or {}
    max_dim = int(cfg.get("max_dimension", 768))
    blur_thresh = float(cfg.get("laplacian_blur_threshold", 80.0))
    crop_fraction = float(cfg.get("crop_fraction", 0.60))
    b_mean_min = float(cfg.get("brightness_mean_min", 40.0))
    b_mean_max = float(cfg.get("brightness_mean_max", 220.0))
    b_p05_min = float(cfg.get("brightness_p05_min", 15.0))
    b_p95_max = float(cfg.get("brightness_p95_max", 250.0))
    glare_max = float(cfg.get("glare_fraction_max", 0.08))
    skin_min = float(cfg.get("skin_fraction_min", 0.15))
    largest_skin_min = float(cfg.get("largest_skin_region_fraction_min", 0.08))

    # Resize image so maximum dimension is preserved under max_dim
    h, w = image.shape[:2]
    max_current = max(h, w)
    if max_current > max_dim:
        scale = max_dim / float(max_current)
        new_w = max(1, int(round(w * scale)))
        new_h = max(1, int(round(h * scale)))
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        resized = image.copy()

    rh, rw = resized.shape[:2]
    total_pixels = float(rh * rw)

    # Grayscale and Color spaces
    if resized.ndim == 2:
        gray = resized
        bgr = cv2.cvtColor(resized, cv2.COLOR_GRAY2BGR)
    elif resized.shape[2] == 4:
        bgr = cv2.cvtColor(resized, cv2.COLOR_BGRA2BGR)
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    else:
        bgr = resized
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    # Blur: Variance of Laplacian on full image and central crop
    laplacian_full = cv2.Laplacian(gray, cv2.CV_64F)
    blur_full = float(laplacian_full.var())

    crop_h = max(1, int(round(rh * crop_fraction)))
    crop_w = max(1, int(round(rw * crop_fraction)))
    start_y = max(0, (rh - crop_h) // 2)
    start_x = max(0, (rw - crop_w) // 2)
    crop_gray = gray[start_y : start_y + crop_h, start_x : start_x + crop_w]

    if crop_gray.size > 0:
        blur_crop = float(cv2.Laplacian(crop_gray, cv2.CV_64F).var())
        blur_score = min(blur_full, blur_crop)
    else:
        blur_score = blur_full

    # Brightness & Glare (HSV)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    v_channel = hsv[:, :, 2]
    s_channel = hsv[:, :, 1]

    brightness_mean = float(np.mean(v_channel))
    brightness_p05 = float(np.percentile(v_channel, 5))
    brightness_p95 = float(np.percentile(v_channel, 95))

    glare_mask = (v_channel > 245) & (s_channel < 40)
    glare_fraction = float(np.sum(glare_mask)) / total_pixels

    # Multi-tone Skin Coverage (YCrCb + HSV)
    ycrcb = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    cr = ycrcb[:, :, 1]
    cb = ycrcb[:, :, 2]

    # Skin segmentation covering diverse Indian skin tones (Fitzpatrick I-VI)
    skin_mask = (cr >= 133) & (cr <= 178) & (cb >= 75) & (cb <= 130)
    skin_fraction = float(np.sum(skin_mask)) / total_pixels

    skin_uint8 = skin_mask.astype(np.uint8)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(skin_uint8, connectivity=8)

    if num_labels > 1:
        largest_area = int(np.max(stats[1:, cv2.CC_STAT_AREA]))
        largest_skin_region_fraction = float(largest_area) / total_pixels
    else:
        largest_skin_region_fraction = 0.0

    # Calculate ITA on skin
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2Lab)
    ita_deg, skin_tone_group = calculate_ita(lab[:, :, 0], lab[:, :, 2], skin_mask)

    # Determine Quality Reasons and Tips
    reasons: List[str] = []
    tips: List[str] = []

    if blur_score < blur_thresh:
        reasons.append("BLUR")
        tips.append("Hold the phone steady and take the photo again.")

    if brightness_mean < b_mean_min or brightness_p05 < b_p05_min:
        reasons.append("DARK")
        tips.append("Move to a brighter area.")

    if brightness_mean > b_mean_max or brightness_p95 > b_p95_max:
        if "BRIGHT" not in reasons:
            reasons.append("BRIGHT")
            tips.append("Reduce lighting or move away from strong glare.")

    if glare_fraction > glare_max:
        if "GLARE" not in reasons:
            reasons.append("GLARE")
            tips.append("Avoid direct light reflecting from the skin.")

    if skin_fraction < 0.05:
        reasons.append("OBSTRUCTED")
        tips.append("Make sure the affected skin is not covered.")
    elif skin_fraction < skin_min or largest_skin_region_fraction < largest_skin_min:
        reasons.append("TOO_FAR")
        tips.append("Move closer so the affected skin is clearly visible.")

    # Upload-specific Artifact Checks
    upload_res = {"has_upload_flags": False, "flags": [], "tips": []}
    if source == "upload" or cfg.get("run_upload_checks", False):
        upload_res = detect_upload_artifacts(image, config=cfg)
        if upload_res["has_upload_flags"]:
            for u_flag in upload_res["flags"]:
                reasons.append(u_flag)
            for u_tip in upload_res["tips"]:
                tips.append(u_tip)

    acceptable = len(reasons) == 0

    return {
        "acceptable": acceptable,
        "reasons": reasons,
        "measurements": {
            "blur": round(blur_score, 2),
            "brightness_mean": round(brightness_mean, 2),
            "brightness_p05": round(brightness_p05, 2),
            "brightness_p95": round(brightness_p95, 2),
            "glare_fraction": round(glare_fraction, 4),
            "skin_fraction": round(skin_fraction, 4),
            "largest_skin_region_fraction": round(largest_skin_region_fraction, 4),
            "ita": ita_deg,
            "skin_tone_group": skin_tone_group
        },
        "upload_quality": upload_res,
        "tips": tips
    }
