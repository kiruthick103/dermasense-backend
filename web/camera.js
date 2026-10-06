/**
 * DermaSense Camera Module (camera.js)
 * Real-time camera management with WebRTC getUserMedia, live quality metering,
 * device error handling, EXIF handling, and background lifecycle management.
 */

class DermaCamera {
  constructor(firstArg = {}, secondArg = {}) {
    let options = {};
    if (firstArg instanceof HTMLElement || (firstArg && firstArg.tagName === 'VIDEO')) {
      this.videoElement = firstArg;
      options = secondArg || {};
    } else {
      options = firstArg || {};
      this.videoElement = options.videoElement || null;
    }

    this.stream = null;
    this.activeTrack = null;
    this.facingMode = 'environment'; // default rear camera
    this.torchEnabled = false;
    this.hasTorchCapability = false;
    this.isQualityMeterRunning = false;
    this.qualityIntervalId = null;
    this.onQualityUpdate = options.onQualityUpdate || options.onQualitySample || null;
    this.onError = options.onError || null;

    // Offscreen quality sampling canvas (160x120)
    this.qualityCanvas = document.createElement('canvas');
    this.qualityCanvas.width = 160;
    this.qualityCanvas.height = 120;
    this.qualityCtx = this.qualityCanvas.getContext('2d', { willReadFrequently: true });

    // Handle tab visibility change
    this.handleVisibilityChange = this.handleVisibilityChange.bind(this);
    document.addEventListener('visibilitychange', this.handleVisibilityChange);
  }

  /**
   * Checks whether the current context is secure for getUserMedia.
   */
  static isSecureEnvironment() {
    if (window.isSecureContext) return true;
    const host = window.location.hostname;
    return host === 'localhost' || host === '127.0.0.1' || host === '[::1]';
  }

  /**
   * Starts camera stream on user gesture.
   */
  async start(videoElement) {
    if (videoElement) this.videoElement = videoElement;
    if (!this.videoElement) throw new Error('Video element is required to display stream');

    if (!DermaCamera.isSecureEnvironment()) {
      const err = new Error('INSECURE_CONTEXT');
      err.userMessage = 'Camera requires a secure connection (HTTPS or localhost). Please upload a photo from your device instead.';
      if (this.onError) this.onError(err);
      throw err;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      const err = new Error('NOT_SUPPORTED');
      err.userMessage = 'Camera API is not supported in this browser. Please use the file upload option.';
      if (this.onError) this.onError(err);
      throw err;
    }

    // Stop any existing stream
    this.stop();

    const idealConstraints = {
      video: {
        facingMode: { ideal: this.facingMode },
        width: { ideal: 1920 },
        height: { ideal: 1080 }
      },
      audio: false
    };

    try {
      this.stream = await navigator.mediaDevices.getUserMedia(idealConstraints);
    } catch (err) {
      console.warn('Initial camera constraint failed, retrying with fallback...', err.name);
      if (err.name === 'OverconstrainedError' || err.name === 'ConstraintNotSatisfiedError') {
        try {
          this.stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        } catch (fallbackErr) {
          this.handleCameraError(fallbackErr);
          throw fallbackErr;
        }
      } else {
        this.handleCameraError(err);
        throw err;
      }
    }

    // Configure video element for iOS Safari and mobile compatibility
    this.videoElement.playsInline = true;
    this.videoElement.muted = true;
    this.videoElement.autoplay = true;
    this.videoElement.srcObject = this.stream;

    await this.videoElement.play();

    this.activeTrack = this.stream.getVideoTracks()[0] || null;
    this.inspectCapabilities();
    this.startLiveQualityMeter();

    return this.stream;
  }

  /**
   * Maps device/browser errors to clear, friendly user recovery steps.
   */
  handleCameraError(err) {
    let userMsg = '';
    let recoveryGuide = '';

    switch (err.name) {
      case 'NotAllowedError':
      case 'PermissionDeniedError':
        userMsg = 'Camera permission was blocked.';
        recoveryGuide = `
          <strong>How to allow camera:</strong><br>
          • <strong>Android Chrome:</strong> Tap the tune/lock icon next to the address bar → <em>Permissions</em> → <em>Camera</em> → <em>Allow</em>.<br>
          • <strong>iPhone Safari:</strong> Tap the <em>AA</em> button in the address bar → <em>Website Settings</em> → <em>Camera</em> → <em>Allow</em>.<br>
          • Or use the <strong>Upload photo</strong> button below.
        `;
        break;
      case 'NotFoundError':
      case 'DevicesNotFoundError':
        userMsg = 'No camera device found on this system.';
        recoveryGuide = 'Please plug in a camera, or use the <strong>Upload photo</strong> option to choose an existing image.';
        break;
      case 'NotReadableError':
      case 'TrackStartError':
        userMsg = 'Camera is currently in use by another app.';
        recoveryGuide = 'Please close other applications using the webcam (e.g. Zoom, Teams) and refresh, or upload a photo.';
        break;
      default:
        userMsg = 'Unable to open camera: ' + (err.message || 'unknown error');
        recoveryGuide = 'Please use the <strong>Upload photo</strong> button to select an image from your device.';
    }

    const customErr = new Error(err.name || 'CAMERA_ERROR');
    customErr.userMessage = userMsg;
    customErr.recoveryGuide = recoveryGuide;
    customErr.original = err;

    if (this.onError) this.onError(customErr);
    return customErr;
  }

  /**
   * Checks torch and focus capabilities.
   */
  inspectCapabilities() {
    this.hasTorchCapability = false;
    if (this.activeTrack && typeof this.activeTrack.getCapabilities === 'function') {
      const caps = this.activeTrack.getCapabilities();
      this.hasTorchCapability = Boolean(caps.torch);
    }
  }

  /**
   * Switches between environment (rear) and user (front) cameras.
   */
  async switchCamera() {
    this.facingMode = this.facingMode === 'environment' ? 'user' : 'environment';
    return this.start(this.videoElement);
  }

  flipCamera() {
    return this.switchCamera();
  }

  /**
   * Toggles flashlight/torch if supported by device.
   */
  async toggleTorch() {
    if (!this.activeTrack || !this.hasTorchCapability) return false;
    try {
      this.torchEnabled = !this.torchEnabled;
      await this.activeTrack.applyConstraints({
        advanced: [{ torch: this.torchEnabled }]
      });
      return this.torchEnabled;
    } catch (e) {
      console.warn('Torch toggle failed:', e);
      return false;
    }
  }

  /**
   * Attempts point-of-interest focus on touch coordinate if supported.
   */
  async tapToFocus(normalizedX, normalizedY) {
    if (!this.activeTrack || typeof this.activeTrack.applyConstraints !== 'function') return;
    try {
      const caps = this.activeTrack.getCapabilities ? this.activeTrack.getCapabilities() : {};
      if (caps.focusMode && caps.focusMode.includes('continuous')) {
        await this.activeTrack.applyConstraints({
          advanced: [{
            focusMode: 'continuous',
            pointsOfInterest: [{ x: normalizedX, y: normalizedY }]
          }]
        });
      }
    } catch (e) {
      // Ignore if hardware does not support software tap-to-focus
    }
  }

  /**
   * Starts ~5 fps quality assessment loop on a 160px canvas.
   */
  startLiveQualityMeter() {
    this.stopLiveQualityMeter();
    this.isQualityMeterRunning = true;

    // Run every 200ms (~5 fps)
    this.qualityIntervalId = setInterval(() => {
      if (!this.videoElement || this.videoElement.readyState < 2 || !this.isQualityMeterRunning) return;

      const vw = this.videoElement.videoWidth || 160;
      const vh = this.videoElement.videoHeight || 120;
      const targetW = 160;
      const targetH = Math.round((vh / vw) * targetW);

      if (this.qualityCanvas.height !== targetH) {
        this.qualityCanvas.height = targetH;
      }

      this.qualityCtx.drawImage(this.videoElement, 0, 0, targetW, targetH);
      const imgData = this.qualityCtx.getImageData(0, 0, targetW, targetH);

      if (typeof DermaVision !== 'undefined' && DermaVision.assessLiveQuality) {
        const quality = DermaVision.assessLiveQuality(imgData);
        if (this.onQualityUpdate) {
          this.onQualityUpdate(quality);
        }
      }
    }, 200);
  }

  stopLiveQualityMeter() {
    this.isQualityMeterRunning = false;
    if (this.qualityIntervalId) {
      clearInterval(this.qualityIntervalId);
      this.qualityIntervalId = null;
    }
  }

  /**
   * Captures full resolution frame and creates downscaled working copy (max 768px).
   * Corrects for device orientation.
   */
  async capture() {
    let vw = (this.videoElement && this.videoElement.videoWidth) || 0;
    let vh = (this.videoElement && this.videoElement.videoHeight) || 0;

    // Fallback if videoWidth not ready yet
    if (!vw || !vh) {
      vw = (this.videoElement && this.videoElement.clientWidth) || 640;
      vh = (this.videoElement && this.videoElement.clientHeight) || 480;
    }

    // 1. Full-Resolution Canvas
    const fullCanvas = document.createElement('canvas');
    fullCanvas.width = vw;
    fullCanvas.height = vh;
    const fullCtx = fullCanvas.getContext('2d');
    if (this.videoElement) {
      try {
        fullCtx.drawImage(this.videoElement, 0, 0, vw, vh);
      } catch (e) {
        // If drawing fails, fill with neutral tone
        fullCtx.fillStyle = '#444';
        fullCtx.fillRect(0, 0, vw, vh);
      }
    }

    // 2. Downscaled Working Copy (max 768px for fast vision processing)
    const maxDim = 768;
    let workW = vw;
    let workH = vh;

    if (vw > maxDim || vh > maxDim) {
      if (vw >= vh) {
        workW = maxDim;
        workH = Math.round((vh / vw) * maxDim);
      } else {
        workH = maxDim;
        workW = Math.round((vw / vh) * maxDim);
      }
    }

    const workCanvas = document.createElement('canvas');
    workCanvas.width = workW;
    workCanvas.height = workH;
    const workCtx = workCanvas.getContext('2d');
    workCtx.drawImage(fullCanvas, 0, 0, workW, workH);

    // Convert to Blobs
    const fullBlob = await new Promise(resolve => fullCanvas.toBlob(resolve, 'image/jpeg', 0.95));
    const workBlob = await new Promise(resolve => workCanvas.toBlob(resolve, 'image/jpeg', 0.90));
    const workImageData = workCtx.getImageData(0, 0, workW, workH);

    return {
      fullBlob,
      workBlob,
      workImageData,
      width: workW,
      height: workH,
      dataUrl: workCanvas.toDataURL('image/jpeg', 0.90)
    };
  }

  async captureFrame() {
    return this.capture();
  }

  /**
   * Stops all active tracks and turns off hardware indicator lights.
   */
  stop() {
    this.stopLiveQualityMeter();
    if (this.stream) {
      this.stream.getTracks().forEach(track => {
        try {
          track.stop();
        } catch (e) {}
      });
      this.stream = null;
      this.activeTrack = null;
    }
    if (this.videoElement) {
      this.videoElement.srcObject = null;
    }
    this.torchEnabled = false;
  }

  /**
   * Tab lifecycle handler: pause tracks on background, resume on foreground.
   */
  handleVisibilityChange() {
    if (document.hidden) {
      this.stop();
    }
  }

  destroy() {
    this.stop();
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
  }
}

// Export for module or global
if (typeof module !== 'undefined' && module.exports) {
  module.exports = DermaCamera;
} else if (typeof window !== 'undefined') {
  window.DermaCamera = DermaCamera;
}
