"""
Unit and Synthetic Tests for Engine 1 (Photo Quality Assessment).
Verifies detection of blur, darkness, glare, obstruction, and acceptable phone images,
plus execution timing (<100ms per image).
"""

import time
import numpy as np
import cv2
import pytest
from engines.quality import assess_image_quality


def create_synthetic_skin_image(
    h: int = 400,
    w: int = 400,
    blur: bool = False,
    dark: bool = False,
    bright: bool = False,
    glare: bool = False,
    obstructed: bool = False,
    far_away: bool = False
) -> np.ndarray:
    """
    Synthesizes test images with deterministic characteristics:
    - Base skin tone in YCrCb: Cr~150, Cb~100 (RGB ~ (200, 160, 140))
    """
    img = np.zeros((h, w, 3), dtype=np.uint8)

    if obstructed:
        # Solid non-skin background (e.g. blue cloth/object)
        img[:, :] = [200, 50, 30]  # BGR
        return img

    if far_away:
        # Small 30x30 skin patch in a 400x400 non-skin background
        img[:, :] = [50, 50, 50]  # Dark non-skin background
        img[185:215, 185:215] = [140, 160, 200]  # BGR skin
        return img

    # Standard skin tone base (BGR: ~140, 160, 200)
    img[:, :] = [140, 160, 200]

    # Add high-frequency textures for sharpness (sharp rash dots/edges)
    rng = np.random.RandomState(42)
    noise = rng.randint(0, 40, (h, w), dtype=np.int16) - 20
    for c in range(3):
        channel = img[:, :, c].astype(np.int16) + noise
        img[:, :, c] = np.clip(channel, 0, 255).astype(np.uint8)

    # Draw clear sharp border/grid
    cv2.circle(img, (w // 2, h // 2), 60, (90, 110, 160), 4)
    cv2.rectangle(img, (80, 80), (120, 120), (80, 100, 150), 3)

    if blur:
        img = cv2.GaussianBlur(img, (25, 25), 10.0)

    if dark:
        img = (img.astype(np.float32) * 0.1).astype(np.uint8)

    if bright:
        img = np.clip(img.astype(np.float32) * 1.8 + 80, 0, 255).astype(np.uint8)

    if glare:
        # White specular reflection hotspot (V > 245, S < 40)
        cv2.circle(img, (w // 2, h // 2), 70, (255, 255, 255), -1)

    return img


def test_sharp_well_lit_image_is_acceptable():
    good_img = create_synthetic_skin_image()
    res = assess_image_quality(good_img)
    assert res["acceptable"] is True
    assert len(res["reasons"]) == 0
    assert res["measurements"]["blur"] > 80.0
    assert res["measurements"]["skin_fraction"] > 0.15


def test_blur_detected():
    blurry_img = create_synthetic_skin_image(blur=True)
    res = assess_image_quality(blurry_img)
    assert res["acceptable"] is False
    assert "BLUR" in res["reasons"]
    assert any("steady" in tip.lower() for tip in res["tips"])


def test_darkness_detected():
    dark_img = create_synthetic_skin_image(dark=True)
    res = assess_image_quality(dark_img)
    assert res["acceptable"] is False
    assert "DARK" in res["reasons"]
    assert any("brighter" in tip.lower() for tip in res["tips"])


def test_glare_detected():
    glare_img = create_synthetic_skin_image(glare=True)
    res = assess_image_quality(glare_img)
    assert res["acceptable"] is False
    assert "GLARE" in res["reasons"]
    assert any("reflecting" in tip.lower() for tip in res["tips"])


def test_obstructed_detected():
    obstructed_img = create_synthetic_skin_image(obstructed=True)
    res = assess_image_quality(obstructed_img)
    assert res["acceptable"] is False
    assert "OBSTRUCTED" in res["reasons"]
    assert any("covered" in tip.lower() for tip in res["tips"])


def test_too_far_detected():
    far_img = create_synthetic_skin_image(far_away=True)
    res = assess_image_quality(far_img)
    assert res["acceptable"] is False
    assert ("TOO_FAR" in res["reasons"] or "OBSTRUCTED" in res["reasons"])


def test_quality_execution_speed_under_100ms():
    test_img = create_synthetic_skin_image(h=600, w=800)
    # Warmup
    _ = assess_image_quality(test_img)

    t0 = time.perf_counter()
    _ = assess_image_quality(test_img)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert elapsed_ms < 100.0, f"Quality engine took {elapsed_ms:.2f} ms (expected < 100 ms)"
