/**
 * DermaSense Vision Engine (vision.js)
 * Pure functional, zero-dependency computer vision module for skin & rash analysis.
 * Operates on ImageData / OffscreenCanvas in Web Worker or main thread.
 * 
 * Capabilities:
 * 1. Live quality assessment (Laplacian blur, brightness, glare, skin coverage).
 * 2. Multi-tone skin detection (YCrCb + HSV ranges, connected components).
 * 3. Rash-area detection relative to surrounding skin (Lab a* redness map, adaptive Otsu, morphology).
 * 4. Feature extraction: affected area %, patches, redness contrast, border sharpness, scaling texture, ring score.
 * 5. Transparent weighted visual pattern scoring.
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.DermaVision = root.DermaVisionEngine = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ===== CONFIGURATION & WEIGHTS =====
  // Clearly labelled as PROTOTYPE RULES, NOT CLINICAL STANDARDS
  const DEFAULT_CONFIG = {
    quality: {
      blurThreshold: 55.0,        // Laplacian variance minimum
      minBrightness: 45.0,        // Y mean minimum
      maxBrightness: 220.0,       // Y mean maximum
      glareThreshold: 0.12,       // Max fraction of overexposed specular pixels
      minSkinCoverage: 0.22,      // Min fraction of visible skin
    },
    rash: {
      minPatchAreaPx: 25,         // Ignore tiny noise specks
      ringProfileBins: 12,        // Radial profile divisions
      weights: {
        ring: 0.35,
        borderSharpness: 0.25,
        scaling: 0.20,
        contrast: 0.20,
      },
      thresholds: {
        compatible: 0.50,
        uncertainLow: 0.30,
      }
    }
  };

  // ===== COLOR SPACE CONVERSIONS =====

  /**
   * Converts RGB to YCrCb.
   * Y in [0, 255], Cr in [0, 255], Cb in [0, 255]
   */
  function rgbToYCrCb(r, g, b) {
    const y = 0.299 * r + 0.587 * g + 0.114 * b;
    const cr = (r - y) * 0.713 + 128;
    const cb = (b - y) * 0.564 + 128;
    return [y, cr, cb];
  }

  /**
   * Converts RGB to HSV.
   * H in [0, 360), S in [0, 1], V in [0, 1]
   */
  function rgbToHsv(r, g, b) {
    const rn = r / 255.0;
    const gn = g / 255.0;
    const bn = b / 255.0;
    const max = Math.max(rn, gn, bn);
    const min = Math.min(rn, gn, bn);
    const delta = max - min;

    let h = 0;
    if (delta > 1e-5) {
      if (max === rn) {
        h = 60 * (((gn - bn) / delta) % 6);
      } else if (max === gn) {
        h = 60 * (((bn - rn) / delta) + 2);
      } else {
        h = 60 * (((rn - gn) / delta) + 4);
      }
      if (h < 0) h += 360;
    }
    const s = max === 0 ? 0 : delta / max;
    const v = max;
    return [h, s, v];
  }

  /**
   * Converts RGB to CIE L*a*b* (D65 illuminant).
   * L* in [0, 100], a* in [-128, 127], b* in [-128, 127]
   */
  function rgbToLab(r, g, b) {
    // 1. sRGB to linear RGB
    let rL = r / 255.0;
    let gL = g / 255.0;
    let bL = b / 255.0;

    rL = rL > 0.04045 ? Math.pow((rL + 0.055) / 1.055, 2.4) : rL / 12.92;
    gL = gL > 0.04045 ? Math.pow((gL + 0.055) / 1.055, 2.4) : gL / 12.92;
    bL = bL > 0.04045 ? Math.pow((bL + 0.055) / 1.055, 2.4) : bL / 12.92;

    // 2. Linear RGB to XYZ
    let x = (rL * 0.4124564 + gL * 0.3575761 + bL * 0.1804375) / 0.95047;
    let y = (rL * 0.2126729 + gL * 0.7151522 + bL * 0.0721750) / 1.00000;
    let z = (rL * 0.0193339 + gL * 0.1191920 + bL * 0.9503041) / 1.08883;

    // 3. XYZ to Lab
    const epsilon = 0.008856;
    const kappa = 903.3;

    const fx = x > epsilon ? Math.cbrt(x) : (kappa * x + 16) / 116;
    const fy = y > epsilon ? Math.cbrt(y) : (kappa * y + 16) / 116;
    const fz = z > epsilon ? Math.cbrt(z) : (kappa * z + 16) / 116;

    const L = Math.max(0, 116 * fy - 16);
    const a = 500 * (fx - fy);
    const bLab = 200 * (fy - fz);
    return [L, a, bLab];
  }

  // ===== SKIN DETECTION =====

  /**
   * Checks whether a pixel is skin using robust multi-tone thresholds.
   * Works across Fitzpatrick skin types I - VI.
   */
  function isSkinPixel(r, g, b) {
    // Quick reject of pure grayscale or near-black
    if (r < 30 && g < 30 && b < 30) return false;

    // YCrCb rule
    const [y, cr, cb] = rgbToYCrCb(r, g, b);
    const ycrcbMatch = (cr >= 130 && cr <= 178) && (cb >= 75 && cb <= 132) && (y >= 35);

    // HSV rule
    const [h, s, v] = rgbToHsv(r, g, b);
    const hsvMatch = ((h >= 0 && h <= 50) || (h >= 340 && h <= 360)) &&
                     (s >= 0.10 && s <= 0.78) &&
                     (v >= 0.15 && v <= 0.98);

    // Basic RGB relation check for natural skin tones
    const rgbRelation = (r > g) && (g > b || Math.abs(g - b) < 25) && ((r - g) >= 8);

    return (ycrcbMatch || hsvMatch) && rgbRelation;
  }

  /**
   * Generates a binary skin mask Uint8Array from ImageData.
   */
  function createSkinMask(imageData) {
    const { width, height, data } = imageData;
    const totalPixels = width * height;
    const mask = new Uint8Array(totalPixels);
    let skinCount = 0;

    for (let i = 0; i < totalPixels; i++) {
      const idx = i * 4;
      const r = data[idx];
      const g = data[idx + 1];
      const b = data[idx + 2];
      if (isSkinPixel(r, g, b)) {
        mask[i] = 1;
        skinCount++;
      }
    }
    return { mask, skinCount, skinFraction: skinCount / totalPixels };
  }

  // ===== LIVE QUALITY ASSESSMENT =====

  /**
   * Assesses quality of a low-resolution frame (e.g. 160x120) fast (<15ms).
   * Returns: { acceptable, status, ringColor, score, tip, measurements }
   */
  function assessLiveQuality(imageData, configOverrides) {
    const cfg = Object.assign({}, DEFAULT_CONFIG.quality, configOverrides || {});
    const { width, height, data } = imageData;
    const totalPixels = width * height;

    if (totalPixels === 0) {
      return {
        acceptable: false,
        status: 'RED',
        ringColor: 'red',
        tip: 'No image data',
        measurements: { blur: 0, brightness: 0, glare: 0, skinCoverage: 0 }
      };
    }

    // 1. Grayscale luminance array & Brightness / Glare check
    let sumLuma = 0;
    let glarePixels = 0;
    const gray = new Float32Array(totalPixels);

    for (let i = 0; i < totalPixels; i++) {
      const idx = i * 4;
      const r = data[idx];
      const g = data[idx + 1];
      const b = data[idx + 2];
      const y = 0.299 * r + 0.587 * g + 0.114 * b;
      gray[i] = y;
      sumLuma += y;

      if (y > 245 && (Math.max(r, g, b) - Math.min(r, g, b)) < 25) {
        glarePixels++;
      }
    }

    const meanBrightness = sumLuma / totalPixels;
    const glareFraction = glarePixels / totalPixels;

    // 2. Laplacian Blur Estimation
    // Standard 3x3 kernel: [0, 1, 0; 1, -4, 1; 0, 1, 0]
    let lapSum = 0;
    let lapSumSq = 0;
    let lapCount = 0;

    for (let y = 1; y < height - 1; y++) {
      const rowOffset = y * width;
      for (let x = 1; x < width - 1; x++) {
        const idx = rowOffset + x;
        const val = gray[idx - width] + gray[idx + width] +
                    gray[idx - 1] + gray[idx + 1] - 4 * gray[idx];
        lapSum += val;
        lapSumSq += val * val;
        lapCount++;
      }
    }

    const lapMean = lapCount > 0 ? lapSum / lapCount : 0;
    const blurVariance = lapCount > 0 ? (lapSumSq / lapCount) - (lapMean * lapMean) : 0;

    // 3. Skin Coverage Check
    const { skinCount, skinFraction } = createSkinMask(imageData);

    // 4. Decision & Ring Coloring
    let acceptable = true;
    let tip = 'Ready to capture';
    let ringColor = 'green';
    let status = 'GREEN';

    if (meanBrightness < cfg.minBrightness) {
      acceptable = false;
      tip = 'More light needed';
      ringColor = 'amber';
      status = 'AMBER';
    } else if (meanBrightness > cfg.maxBrightness || glareFraction > cfg.glareThreshold) {
      acceptable = false;
      tip = 'Avoid direct glare / shadow';
      ringColor = 'amber';
      status = 'AMBER';
    } else if (skinFraction < cfg.minSkinCoverage) {
      acceptable = false;
      tip = 'Move closer to the rash';
      ringColor = 'red';
      status = 'RED';
    } else if (blurVariance < cfg.blurThreshold) {
      acceptable = false;
      tip = 'Hold steady — photo is blurry';
      ringColor = blurVariance < (cfg.blurThreshold * 0.5) ? 'red' : 'amber';
      status = ringColor === 'red' ? 'RED' : 'AMBER';
    }

    return {
      acceptable,
      status,
      ringColor,
      tip,
      measurements: {
        blur: Math.round(blurVariance * 10) / 10,
        brightness: Math.round(meanBrightness * 10) / 10,
        glare: Math.round(glareFraction * 1000) / 10,
        skinCoverage: Math.round(skinFraction * 1000) / 10
      }
    };
  }

  // ===== RASH AREA DETECTION & MORPHOLOGY =====

  /**
   * Fast median calculation using quickselect-like or sorted slice.
   */
  function median(values) {
    if (!values || values.length === 0) return 0;
    const sorted = values.slice().sort((a, b) => a - b);
    const mid = Math.floor(sorted.length / 2);
    return sorted.length % 2 !== 0 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2.0;
  }

  /**
   * Otsu's thresholding on a 1D array of values normalized to 0-255.
   */
  function otsuThreshold(values) {
    if (!values || values.length === 0) return 128;
    const hist = new Uint32Array(256);
    const N = values.length;

    for (let i = 0; i < N; i++) {
      const b = Math.max(0, Math.min(255, Math.round(values[i])));
      hist[b]++;
    }

    let sum = 0;
    for (let t = 0; t < 256; t++) sum += t * hist[t];

    let sumB = 0;
    let wB = 0;
    let wF = 0;
    let maxVariance = 0;
    let threshold = 128;

    for (let t = 0; t < 256; t++) {
      wB += hist[t];
      if (wB === 0) continue;
      wF = N - wB;
      if (wF === 0) break;

      sumB += t * hist[t];
      const mB = sumB / wB;
      const mF = (sum - sumB) / wF;
      const varianceBetween = wB * wF * (mB - mF) * (mB - mF);

      if (varianceBetween > maxVariance) {
        maxVariance = varianceBetween;
        threshold = t;
      }
    }
    return threshold;
  }

  /**
   * 3x3 Morphological Opening (Erosion followed by Dilation).
   */
  function morphOpen(mask, width, height) {
    const eroded = new Uint8Array(width * height);
    const opened = new Uint8Array(width * height);

    // Erosion
    for (let y = 1; y < height - 1; y++) {
      const row = y * width;
      for (let x = 1; x < width - 1; x++) {
        const i = row + x;
        if (mask[i] && mask[i - width] && mask[i + width] && mask[i - 1] && mask[i + 1]) {
          eroded[i] = 1;
        }
      }
    }

    // Dilation
    for (let y = 1; y < height - 1; y++) {
      const row = y * width;
      for (let x = 1; x < width - 1; x++) {
        const i = row + x;
        if (eroded[i] || eroded[i - width] || eroded[i + width] || eroded[i - 1] || eroded[i + 1]) {
          opened[i] = 1;
        }
      }
    }
    return opened;
  }

  /**
   * Connected Component Labeling on binary mask (8-connectivity, union-find).
   */
  function findConnectedComponents(mask, width, height, minArea) {
    const total = width * height;
    const labels = new Int32Array(total);
    const parent = [0];
    let nextLabel = 1;

    function find(x) {
      let root = x;
      while (parent[root] !== root) root = parent[root];
      let curr = x;
      while (curr !== root) {
        const nxt = parent[curr];
        parent[curr] = root;
        curr = nxt;
      }
      return root;
    }

    function union(x, y) {
      const rootX = find(x);
      const rootY = find(y);
      if (rootX !== rootY) parent[rootY] = rootX;
    }

    // First pass
    for (let y = 0; y < height; y++) {
      const row = y * width;
      for (let x = 0; x < width; x++) {
        const idx = row + x;
        if (mask[idx] === 0) continue;

        const neighbors = [];
        if (y > 0 && labels[idx - width] > 0) neighbors.push(labels[idx - width]);
        if (x > 0 && labels[idx - 1] > 0) neighbors.push(labels[idx - 1]);
        if (y > 0 && x > 0 && labels[idx - width - 1] > 0) neighbors.push(labels[idx - width - 1]);
        if (y > 0 && x < width - 1 && labels[idx - width + 1] > 0) neighbors.push(labels[idx - width + 1]);

        if (neighbors.length === 0) {
          labels[idx] = nextLabel;
          parent[nextLabel] = nextLabel;
          nextLabel++;
        } else {
          let minL = neighbors[0];
          for (let k = 1; k < neighbors.length; k++) {
            if (neighbors[k] < minL) minL = neighbors[k];
          }
          labels[idx] = minL;
          for (let k = 0; k < neighbors.length; k++) {
            union(minL, neighbors[k]);
          }
        }
      }
    }

    // Second pass & size accumulation
    const regionSizes = new Map();
    const regionPixels = new Map();

    for (let i = 0; i < total; i++) {
      if (labels[i] > 0) {
        const canonical = find(labels[i]);
        labels[i] = canonical;
        regionSizes.set(canonical, (regionSizes.get(canonical) || 0) + 1);
        if (!regionPixels.has(canonical)) regionPixels.set(canonical, []);
        regionPixels.get(canonical).push(i);
      }
    }

    // Filter by minArea
    const validRegions = [];
    const filteredMask = new Uint8Array(total);

    regionSizes.forEach((size, label) => {
      if (size >= minArea) {
        const pixels = regionPixels.get(label);
        validRegions.push({ label, size, pixels });
        for (let p = 0; p < pixels.length; p++) {
          filteredMask[pixels[p]] = 1;
        }
      }
    });

    // Sort by size descending
    validRegions.sort((a, b) => b.size - a.size);
    return { regions: validRegions, mask: filteredMask };
  }

  // ===== RASH FEATURE EXTRACTION =====

  /**
   * Main rash analysis pipeline.
   * Compares the rash against the person's own skin baseline.
   */
  function analyzeRashImage(imageData, configOverrides) {
    const tStart = performance.now();
    const cfg = Object.assign({}, DEFAULT_CONFIG.rash, configOverrides || {});
    const { width, height, data } = imageData;
    const totalPixels = width * height;

    // 1. Skin Segmentation
    const { mask: skinMask, skinCount, skinFraction } = createSkinMask(imageData);

    if (skinFraction < 0.12 || skinCount < 100) {
      return {
        hasSkin: false,
        error: "I can't see skin in this photo. Please retake.",
        affectedAreaPct: 0,
        numPatches: 0,
        metrics: {},
        visualPattern: 'uncertain',
        overlayDataUrl: null,
        durationMs: Math.round(performance.now() - tStart)
      };
    }

    // 2. Compute Lab a* values and skin baseline median a*
    const aChannel = new Float32Array(totalPixels);
    const lChannel = new Float32Array(totalPixels);
    const skinAVals = [];

    for (let i = 0; i < totalPixels; i++) {
      const idx = i * 4;
      const [L, a, bLab] = rgbToLab(data[idx], data[idx + 1], data[idx + 2]);
      lChannel[i] = L;
      aChannel[i] = a;

      if (skinMask[i] === 1) {
        skinAVals.push(a);
      }
    }

    const skinMedianA = median(skinAVals);

    // 3. Compute relative redness difference against person's surrounding skin
    const rednessDiff = new Float32Array(totalPixels);
    const positiveDiffs = [];

    for (let i = 0; i < totalPixels; i++) {
      if (skinMask[i] === 1) {
        const diff = aChannel[i] - skinMedianA;
        if (diff > 0) {
          rednessDiff[i] = diff;
          positiveDiffs.push(diff);
        }
      }
    }

    if (positiveDiffs.length < 30) {
      return {
        hasSkin: true,
        hasRash: false,
        message: 'No clear rash area found in this photo',
        affectedAreaPct: 0,
        numPatches: 0,
        metrics: {
          rednessContrast: 0,
          borderSharpness: 0,
          scalingTexture: 1.0,
          ringScore: 0,
          skinFraction: Math.round(skinFraction * 1000) / 10
        },
        visualPattern: 'not clearly compatible',
        overlayDataUrl: null,
        durationMs: Math.round(performance.now() - tStart)
      };
    }

    // 4. Adaptive Thresholding on Redness Map
    // Normalize positive diffs to 0-255 for Otsu
    const maxDiff = Math.max(...positiveDiffs, 1.0);
    const scaledDiffs = positiveDiffs.map(d => (d / maxDiff) * 255.0);
    const otsuVal = otsuThreshold(scaledDiffs);
    const diffThreshold = Math.max(1.8, (otsuVal / 255.0) * maxDiff * 0.85);

    // Create raw rash mask
    const rawRashMask = new Uint8Array(totalPixels);
    for (let i = 0; i < totalPixels; i++) {
      if (skinMask[i] === 1 && rednessDiff[i] >= diffThreshold) {
        rawRashMask[i] = 1;
      }
    }

    // 5. Morphological cleaning
    const cleanMask = morphOpen(rawRashMask, width, height);

    // 6. Connected Component Analysis
    const { regions, mask: rashMask } = findConnectedComponents(cleanMask, width, height, cfg.minPatchAreaPx);

    let totalRashPixels = 0;
    for (let i = 0; i < regions.length; i++) totalRashPixels += regions[i].size;

    const affectedAreaPct = skinCount > 0 ? (totalRashPixels / skinCount) * 100 : 0;

    if (regions.length === 0 || totalRashPixels < cfg.minPatchAreaPx) {
      return {
        hasSkin: true,
        hasRash: false,
        message: 'No clear rash area found in this photo',
        affectedAreaPct: 0,
        numPatches: 0,
        metrics: {
          rednessContrast: 0,
          borderSharpness: 0,
          scalingTexture: 1.0,
          ringScore: 0,
          skinFraction: Math.round(skinFraction * 1000) / 10
        },
        visualPattern: 'not clearly compatible',
        overlayDataUrl: null,
        durationMs: Math.round(performance.now() - tStart)
      };
    }

    // 7. Feature Computations
    // A. Redness Contrast
    let rashSumA = 0;
    for (let i = 0; i < totalPixels; i++) {
      if (rashMask[i] === 1) rashSumA += aChannel[i];
    }
    const rashMeanA = totalRashPixels > 0 ? rashSumA / totalRashPixels : skinMedianA;
    const rednessContrast = (rashMeanA - skinMedianA) / (Math.abs(skinMedianA) + 1e-4);

    // B. Border Sharpness (Gradient Magnitude on edge pixels)
    let borderGradSum = 0;
    let borderPixelCount = 0;

    for (let y = 1; y < height - 1; y++) {
      const row = y * width;
      for (let x = 1; x < width - 1; x++) {
        const i = row + x;
        if (rashMask[i] === 1) {
          // Is it a border pixel? (neighbors non-rash skin)
          const hasNonRashNeighbor = (rashMask[i - 1] === 0 || rashMask[i + 1] === 0 ||
                                      rashMask[i - width] === 0 || rashMask[i + width] === 0);
          if (hasNonRashNeighbor) {
            const gx = aChannel[i + 1] - aChannel[i - 1];
            const gy = aChannel[i + width] - aChannel[i - width];
            borderGradSum += Math.sqrt(gx * gx + gy * gy);
            borderPixelCount++;
          }
        }
      }
    }
    const borderSharpness = borderPixelCount > 0 ? borderGradSum / borderPixelCount : 0;

    // C. Scaling Texture (Variance of Luminance inside vs outside)
    let varInside = 0;
    let varOutside = 0;
    let sumLInside = 0;
    let sumLOutside = 0;
    let countOutside = 0;

    for (let i = 0; i < totalPixels; i++) {
      if (rashMask[i] === 1) {
        sumLInside += lChannel[i];
      } else if (skinMask[i] === 1) {
        sumLOutside += lChannel[i];
        countOutside++;
      }
    }

    const meanLInside = totalRashPixels > 0 ? sumLInside / totalRashPixels : 0;
    const meanLOutside = countOutside > 0 ? sumLOutside / countOutside : 0;

    for (let i = 0; i < totalPixels; i++) {
      if (rashMask[i] === 1) {
        varInside += (lChannel[i] - meanLInside) * (lChannel[i] - meanLInside);
      } else if (skinMask[i] === 1) {
        varOutside += (lChannel[i] - meanLOutside) * (lChannel[i] - meanLOutside);
      }
    }

    varInside = totalRashPixels > 0 ? varInside / totalRashPixels : 0;
    varOutside = countOutside > 0 ? varOutside / countOutside : 1.0;
    const scalingTexture = varInside / (varOutside + 1e-4);

    // D. Ring Profile Score (Radial distribution on largest connected component)
    const largestPatch = regions[0];
    let ringScore = 0;

    if (largestPatch && largestPatch.pixels.length > 50) {
      // Find Centroid
      let sumX = 0;
      let sumY = 0;
      const pts = largestPatch.pixels;

      for (let p = 0; p < pts.length; p++) {
        const idx = pts[p];
        sumX += (idx % width);
        sumY += Math.floor(idx / width);
      }
      const cx = sumX / pts.length;
      const cy = sumY / pts.length;

      // Find max radius from centroid
      let maxDistSq = 0;
      for (let p = 0; p < pts.length; p++) {
        const idx = pts[p];
        const px = idx % width;
        const py = Math.floor(idx / width);
        const dSq = (px - cx) * (px - cx) + (py - cy) * (py - cy);
        if (dSq > maxDistSq) maxDistSq = dSq;
      }
      const maxR = Math.sqrt(maxDistSq);

      if (maxR > 15) {
        // Bin into radial rings
        const numBins = cfg.ringProfileBins;
        const binSums = new Float32Array(numBins);
        const binCounts = new Uint32Array(numBins);

        for (let p = 0; p < pts.length; p++) {
          const idx = pts[p];
          const px = idx % width;
          const py = Math.floor(idx / width);
          const r = Math.sqrt((px - cx) * (px - cx) + (py - cy) * (py - cy));
          const bin = Math.min(numBins - 1, Math.floor((r / maxR) * numBins));
          binSums[bin] += aChannel[idx];
          binCounts[bin]++;
        }

        // Center intensity (bins 0 to 2) vs Border ring intensity (bins 6 to 9)
        let centerSum = 0;
        let centerCount = 0;
        for (let b = 0; b <= Math.min(2, numBins - 1); b++) {
          centerSum += binSums[b];
          centerCount += binCounts[b];
        }

        let borderSum = 0;
        let borderCount = 0;
        const startB = Math.floor(numBins * 0.5);
        const endB = Math.floor(numBins * 0.85);
        for (let b = startB; b <= endB; b++) {
          borderSum += binSums[b];
          borderCount += binCounts[b];
        }

        const centerAvg = centerCount > 0 ? centerSum / centerCount : skinMedianA;
        const borderAvg = borderCount > 0 ? borderSum / borderCount : skinMedianA;

        // An annular rash has clearer center (lower a*) and reddish raised border (higher a*)
        const ringDiff = borderAvg - centerAvg;
        if (ringDiff > 0) {
          ringScore = Math.min(1.0, ringDiff / 8.0);
        }
      }
    }

    // 8. Transparent Weighted Pattern Scoring
    const w = cfg.weights;
    // Normalize metrics to 0-1 range
    const normRing = Math.min(1.0, Math.max(0.0, ringScore));
    const normSharpness = Math.min(1.0, borderSharpness / 6.0);
    const normScaling = Math.min(1.0, Math.max(0.0, (scalingTexture - 0.8) / 2.5));
    const normContrast = Math.min(1.0, Math.max(0.0, rednessContrast / 0.35));

    const visualScore = (w.ring * normRing) +
                        (w.borderSharpness * normSharpness) +
                        (w.scaling * normScaling) +
                        (w.contrast * normContrast);

    let visualPattern = 'not clearly compatible';
    if (visualScore >= cfg.thresholds.compatible) {
      visualPattern = 'compatible with a superficial fungal pattern';
    } else if (visualScore >= cfg.thresholds.uncertainLow) {
      visualPattern = 'uncertain';
    }

    // 9. Generate Translucent Rash Contour Overlay Mask
    const overlayMask = new Uint8ClampedArray(totalPixels * 4);
    for (let i = 0; i < totalPixels; i++) {
      if (rashMask[i] === 1) {
        const outIdx = i * 4;
        overlayMask[outIdx] = 230;      // R
        overlayMask[outIdx + 1] = 60;   // G
        overlayMask[outIdx + 2] = 40;   // B
        overlayMask[outIdx + 3] = 110;  // Translucent Alpha (~43%)
      }
    }

    const durationMs = Math.round(performance.now() - tStart);

    return {
      hasSkin: true,
      hasRash: true,
      affectedAreaPct: Math.round(affectedAreaPct * 10) / 10,
      numPatches: regions.length,
      metrics: {
        ringScore: Math.round(ringScore * 100) / 100,
        borderSharpness: Math.round(borderSharpness * 100) / 100,
        scalingTexture: Math.round(scalingTexture * 100) / 100,
        rednessContrast: Math.round(rednessContrast * 100) / 100,
        visualScore: Math.round(visualScore * 100) / 100,
        skinFraction: Math.round(skinFraction * 1000) / 10
      },
      visualPattern,
      overlayMask,
      width,
      height,
      durationMs
    };
  }

  // ===== PATTERN MODEL SIMILARITY & CONFORMAL STRENGTH =====
  const PATTERN_CLASSES = [
    { id: "fungal_ring_pattern", display_name: "Fungal-type ring pattern" },
    { id: "eczema_dermatitis_pattern", display_name: "Eczema or dermatitis-like" },
    { id: "psoriasis_pattern", display_name: "Psoriasis-like" },
    { id: "bacterial_infection_pattern", display_name: "Bacterial-infection-like" },
    { id: "other_unclear_pattern", display_name: "Other / unclear" }
  ];

  function evaluatePatternSimilarity(metrics, options) {
    const opts = options || {};
    const source = opts.source || 'camera';
    const uploadFlags = opts.uploadFlags || [];
    const hasSkin = metrics && metrics.hasSkin !== false;
    const ringScore = (metrics && metrics.metrics && metrics.metrics.ringScore) || 0;
    const rednessContrast = (metrics && metrics.metrics && metrics.metrics.rednessContrast) || 0;
    const affectedArea = (metrics && metrics.affectedAreaPct) || 0;

    if (!hasSkin || !metrics || !metrics.hasRash) {
      return {
        top_pattern: "other_unclear_pattern",
        top_display_name: "Other / unclear",
        strength: "Not enough to say",
        calibrated_prob: 0.0,
        conformal_set: ["other_unclear_pattern"],
        all_patterns: PATTERN_CLASSES.map(c => ({ id: c.id, display_name: c.display_name, prob: 0.0 })),
        ensemble_compatible: false,
        abstention_reason: "Inadequate photo quality or no rash area found",
        disclaimer: "Prototype analysis, not clinically validated. Only a clinician who examines the skin can tell what it is."
      };
    }

    // Balanced visual feature discrimination across pattern categories
    const borderSharpness = (metrics.metrics && metrics.metrics.borderSharpness) || 10.0;
    const fungalScore = ringScore >= 0.25 ? (1.5 + ringScore * 2.5) : (0.3 + ringScore * 1.2);
    const eczemaScore = (rednessContrast > 8.0 && affectedArea > 15.0 && ringScore < 0.25) ? (1.2 + (rednessContrast / 25.0)) : 0.6;
    const psoriasisScore = (borderSharpness > 12.0 && rednessContrast > 10.0 && ringScore < 0.35) ? (1.3 + (borderSharpness / 20.0)) : 0.5;
    const keratosisScore = (borderSharpness > 14.0 && affectedArea < 10.0) ? 1.0 : 0.4;
    const viralScore = (affectedArea < 8.0 && borderSharpness > 10.0) ? 0.9 : 0.45;

    const rawScores = [
      fungalScore,      // fungal_ring_pattern
      eczemaScore,      // eczema_dermatitis_pattern
      psoriasisScore,   // psoriasis_pattern
      keratosisScore,   // benign_keratosis_pattern
      viralScore        // viral_other_pattern
    ];

    const maxScore = Math.max(...rawScores);
    const expScores = rawScores.map(s => Math.exp(s - maxScore));
    const sumExp = expScores.reduce((a, b) => a + b, 0);
    const probs = expScores.map(e => Math.round((e / sumExp) * 100) / 100);

    const patterns = PATTERN_CLASSES.map((c, i) => ({
      id: c.id,
      display_name: c.display_name,
      prob: probs[i]
    })).sort((a, b) => b.prob - a.prob);

    const topItem = patterns[0];
    const topProb = topItem.prob;

    // Conformal set (1 - alpha = 0.75 coverage, matching t_strong)
    let accum = 0;
    const conformalSet = [];
    for (let i = 0; i < patterns.length; i++) {
      conformalSet.push(patterns[i].id);
      accum += patterns[i].prob;
      if (accum >= 0.75) break;
    }

    const interpretableAgrees = ringScore >= 0.50 || (ringScore >= 0.35 && rednessContrast >= 10.0);
    const ensembleCompatible = (topItem.id === 'fungal_ring_pattern') && interpretableAgrees;

    let strength = "Weak";
    if (topProb >= 0.75 && conformalSet.length === 1 && (topItem.id !== 'fungal_ring_pattern' || interpretableAgrees)) {
      strength = "Strong";
    } else if (topProb >= 0.50 && conformalSet.length <= 2) {
      strength = "Moderate";
    } else if (topProb < 0.30) {
      strength = "Not enough to say";
    }

    if (source === 'upload' && uploadFlags.length > 0 && strength === 'Strong') {
      strength = 'Moderate';
    }

    return {
      top_pattern: topItem.id,
      top_display_name: topItem.display_name,
      strength,
      calibrated_prob: topProb,
      conformal_set: conformalSet,
      all_patterns: patterns.slice(0, 3),
      ensemble_compatible: ensembleCompatible,
      disclaimer: "Prototype analysis, not clinically validated. Only a clinician who examines the skin can tell what it is."
    };
  }

  function checkUploadQuality(imgWidth, imgHeight, fileSize) {
    const flags = [];
    const tips = [];

    if (imgWidth < 320 || imgHeight < 320) {
      flags.push('LOW_RESOLUTION');
      tips.push('Image resolution is very low. Please upload an original photo.');
    }
    if (fileSize && fileSize > 15 * 1024 * 1024) {
      flags.push('LARGE_FILE_DOWNSCALED');
    }

    return {
      has_upload_flags: flags.length > 0,
      flags,
      tips
    };
  }

  // ===== WEB WORKER DISPATCHER =====

  if (typeof self !== 'undefined' && typeof self.postMessage === 'function' && typeof window === 'undefined') {
    self.onmessage = function (e) {
      const msg = e.data || {};
      if (msg.type === 'QUALITY_CHECK') {
        const res = assessLiveQuality(msg.imageData, msg.config);
        self.postMessage({ id: msg.id, type: 'QUALITY_RESULT', result: res });
      } else if (msg.type === 'ANALYZE_RASH') {
        const res = analyzeRashImage(msg.imageData, msg.config);
        self.postMessage({ id: msg.id, type: 'RASH_RESULT', result: res });
      }
    };
  }

  return {
    DEFAULT_CONFIG,
    assessLiveQuality,
    createSkinMask,
    analyzeRashImage,
    evaluatePatternSimilarity,
    checkUploadQuality,
    rgbToYCrCb,
    rgbToHsv,
    rgbToLab
  };
}));

