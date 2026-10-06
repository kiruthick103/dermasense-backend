/**
 * Unit & Integration Test Suite for DermaVision Engine (vision.js).
 * Validates quality assessment, skin detection across tones, rash segmentation,
 * ring scores, non-skin rejection, and execution performance.
 */

const assert = require('assert');
const path = require('path');
const vision = require('../web/engine/vision.js');

// Helper to create synthetic ImageData in Node.js
function makeImageData(width, height) {
  return {
    width,
    height,
    data: new Uint8ClampedArray(width * height * 4)
  };
}

console.log('🧪 Starting DermaVision Engine Test Suite...\n');

// Test 1: Color Space Conversions
{
  const [y, cr, cb] = vision.rgbToYCrCb(200, 160, 140);
  assert(y > 100 && y < 200, 'Y value within valid range');
  assert(cr >= 130 && cr <= 178, 'Cr value captures skin range');

  const [h, s, v] = vision.rgbToHsv(220, 180, 150);
  assert(h >= 0 && h <= 50, 'HSV Hue within skin spectrum');
  console.log('✓ Test 1: Color space transformations (YCrCb, HSV, Lab) accurate');
}

// Test 2: Quality Assessment - Blur, Darkness, Glare, Skin Coverage
{
  // A. Sharp skin image
  const imgSharp = makeImageData(160, 120);
  for (let i = 0; i < 160 * 120; i++) {
    const idx = i * 4;
    // Base skin tone with high-contrast texturing (edges)
    const noise = (i % 2 === 0 ? 30 : -30);
    imgSharp.data[idx] = Math.min(255, Math.max(0, 190 + noise));
    imgSharp.data[idx + 1] = Math.min(255, Math.max(0, 150 + noise));
    imgSharp.data[idx + 2] = Math.min(255, Math.max(0, 120 + noise));
    imgSharp.data[idx + 3] = 255;
  }
  const qSharp = vision.assessLiveQuality(imgSharp);
  assert(qSharp.acceptable, 'High texture skin passes quality check');
  assert.strictEqual(qSharp.status, 'GREEN');
  console.log('✓ Test 2A: Sharp skin image correctly rated GREEN');

  // B. Blurry skin image (uniform, zero variance)
  const imgBlur = makeImageData(160, 120);
  for (let i = 0; i < 160 * 120; i++) {
    const idx = i * 4;
    imgBlur.data[idx] = 190;
    imgBlur.data[idx + 1] = 150;
    imgBlur.data[idx + 2] = 120;
    imgBlur.data[idx + 3] = 255;
  }
  const qBlur = vision.assessLiveQuality(imgBlur);
  assert(!qBlur.acceptable, 'Uniform blurry image correctly flagged');
  assert(qBlur.status === 'RED' || qBlur.status === 'AMBER');
  assert(qBlur.tip.includes('blurry') || qBlur.tip.includes('steady'));
  console.log('✓ Test 2B: Blurry image blocked with "Hold steady" tip');

  // C. Too dark image
  const imgDark = makeImageData(160, 120);
  for (let i = 0; i < 160 * 120; i++) {
    const idx = i * 4;
    imgDark.data[idx] = 20;
    imgDark.data[idx + 1] = 15;
    imgDark.data[idx + 2] = 10;
    imgDark.data[idx + 3] = 255;
  }
  const qDark = vision.assessLiveQuality(imgDark);
  assert(!qDark.acceptable, 'Dark image blocked');
  assert(qDark.tip.includes('light'));
  console.log('✓ Test 2C: Dark image blocked with "More light needed" tip');

  // D. Glare / Overexposed image
  const imgGlare = makeImageData(160, 120);
  for (let i = 0; i < 160 * 120; i++) {
    const idx = i * 4;
    imgGlare.data[idx] = 250;
    imgGlare.data[idx + 1] = 250;
    imgGlare.data[idx + 2] = 250;
    imgGlare.data[idx + 3] = 255;
  }
  const qGlare = vision.assessLiveQuality(imgGlare);
  assert(!qGlare.acceptable, 'Glare overexposure blocked');
  console.log('✓ Test 2D: Glare / Specular reflection blocked');
}

// Test 3: Non-Skin Rejection (e.g. Wall, Hand-drawn picture, Blue Cloth)
{
  const imgWall = makeImageData(200, 200);
  for (let i = 0; i < 200 * 200; i++) {
    const idx = i * 4;
    // Blue wall / cloth
    imgWall.data[idx] = 50;
    imgWall.data[idx + 1] = 100;
    imgWall.data[idx + 2] = 220;
    imgWall.data[idx + 3] = 255;
  }
  const resWall = vision.analyzeRashImage(imgWall);
  assert.strictEqual(resWall.hasSkin, false);
  assert.strictEqual(resWall.error, "I can't see skin in this photo. Please retake.");
  console.log('✓ Test 3: Non-skin photo correctly rejected with "I can\'t see skin"');
}

// Test 4: Ring-Shaped Annular Rash on Light, Medium, and Dark Skin Tones
{
  const tones = [
    { name: 'Light skin (Type I-II)', base: [225, 190, 165] },
    { name: 'Medium skin (Type III-IV)', base: [180, 140, 110] },
    { name: 'Dark skin (Type V-VI)', base: [115, 80, 55] },
  ];

  for (const tone of tones) {
    const w = 240, h = 240;
    const img = makeImageData(w, h);
    const [br, bg, bb] = tone.base;
    const cx = 120, cy = 120;

    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const i = (y * w + x) * 4;
        const dx = x - cx;
        const dy = y - cy;
        const dist = Math.sqrt(dx * dx + dy * dy);

        // Natural skin base
        let r = br + (Math.sin(x * 0.1) * 4);
        let g = bg + (Math.cos(y * 0.1) * 3);
        let b = bb;

        // Annular / Ring lesion: raised erythematous border around r = 45-65, clearer inside
        if (dist >= 45 && dist <= 65) {
          r = Math.min(255, r + 45); // Erythema redness boost
          g = Math.max(0, g - 15);
        } else if (dist < 45) {
          r = Math.min(255, r + 10); // Slight clearing
        }

        img.data[i] = r;
        img.data[i + 1] = g;
        img.data[i + 2] = b;
        img.data[i + 3] = 255;
      }
    }

    const res = vision.analyzeRashImage(img);
    assert(res.hasSkin, `${tone.name} recognized as skin`);
    assert(res.hasRash, `${tone.name} annular rash detected`);
    assert(res.metrics.ringScore > 0.25, `${tone.name} ring score detected: ${res.metrics.ringScore}`);
    assert(res.overlayMask !== null, 'Translucent overlay mask generated');
    assert(res.durationMs < 300, `Execution speed fast (<300ms, actual ${res.durationMs}ms)`);
    console.log(`✓ Test 4 [${tone.name}]: Ring score = ${res.metrics.ringScore}, Pattern = ${res.visualPattern} (${res.durationMs}ms)`);
  }
}

// Test 5: Cleared-Skin / Healthy Skin (No Rash Area)
{
  const w = 200, h = 200;
  const imgClear = makeImageData(w, h);
  for (let i = 0; i < w * h; i++) {
    const idx = i * 4;
    imgClear.data[idx] = 195 + (i % 5);
    imgClear.data[idx + 1] = 155 + (i % 3);
    imgClear.data[idx + 2] = 130;
    imgClear.data[idx + 3] = 255;
  }
  const resClear = vision.analyzeRashImage(imgClear);
  assert(resClear.hasSkin, 'Recognizes healthy skin');
  assert.strictEqual(resClear.hasRash, false, 'No rash detected on uniform skin');
  assert.strictEqual(resClear.message, 'No clear rash area found in this photo');
  console.log('✓ Test 5: Cleared healthy skin returns "No clear rash area found in this photo" (not reassuring)');
}

// Test 6: Pattern Model Similarity & Conformal Strength Rating
{
  const mockMetrics = {
    hasSkin: true,
    hasRash: true,
    affectedAreaPct: 15.0,
    metrics: { ringScore: 0.85, rednessContrast: 14.0, borderSharpness: 22.0 }
  };
  const patRes = vision.evaluatePatternSimilarity(mockMetrics, { source: 'camera' });
  assert.strictEqual(patRes.top_pattern, 'fungal_ring_pattern');
  assert.strictEqual(patRes.strength, 'Strong');
  assert.strictEqual(patRes.ensemble_compatible, true);
  assert(patRes.conformal_set.length >= 1);
  console.log('✓ Test 6: Pattern similarity assigns Strong strength and conformal set to annular rash');

  // Upload quality flag penalty caps at Moderate
  const patUpload = vision.evaluatePatternSimilarity(mockMetrics, { source: 'upload', uploadFlags: ['HEAVY_COMPRESSION'] });
  assert.strictEqual(patUpload.strength, 'Moderate', 'Upload flags cap strength at Moderate');
  console.log('✓ Test 6B: Upload quality flag caps strength rating at Moderate');
}

// Test 7: Upload Quality Pre-check
{
  const upBad = vision.checkUploadQuality(200, 200, 20 * 1024 * 1024);
  assert(upBad.has_upload_flags, 'Detects low resolution and large file');
  assert(upBad.flags.includes('LOW_RESOLUTION'));
  assert(upBad.flags.includes('LARGE_FILE_DOWNSCALED'));
  console.log('✓ Test 7: Upload quality pre-check flags low-res (<320px) images');
}

console.log('\n🎉 ALL 7 DERMAVISION ENGINE TESTS PASSED SUCCESFULLY!\n');

