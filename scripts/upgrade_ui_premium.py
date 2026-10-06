"""
Script to upgrade DermaSense to a Private Premium Clinical Healthcare UI
Replaces bureaucratic/government styles with a high-end luxury clinical SaaS interface.
"""
import re
import os

INDEX_HTML_PATH = os.path.join(os.path.dirname(__file__), '..', 'web', 'index.html')
PORTAL_JS_PATH = os.path.join(os.path.dirname(__file__), '..', 'web', 'portal.js')

with open(INDEX_HTML_PATH, 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update font link in <head>
old_fonts = '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;600;700&family=Noto+Sans+Devanagari:wght@400;600;700&family=Noto+Sans+Kannada:wght@400;600;700&display=swap" rel="stylesheet">'
new_fonts = '<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=Noto+Sans+Devanagari:wght@400;600;700&family=Noto+Sans+Kannada:wght@400;600;700&display=swap" rel="stylesheet">'

if old_fonts in html:
    html = html.replace(old_fonts, new_fonts)

print("Updated fonts in head.")

# 2. Extract <style>...</style> block
style_start = html.find('<style>')
style_end = html.find('</style>')

if style_start != -1 and style_end != -1:
    premium_css = """<style>
/* ==========================================================================
   DERMASENSE PRECISION CLINICAL AI - LUXURY PRIVATE HEALTHCARE DESIGN SYSTEM
   Modern, responsive, ultra-clean clinical interface with WCAG 2.1 AA contrast
   ========================================================================== */
:root {
  /* Retain variables for test suite & backward-compatibility, mapped to luxury tokens */
  --gov-navy: #0f172a;           /* Deep obsidian slate */
  --gov-navy-dark: #020617;      /* Midnight */
  --gov-navy-light: #f1f5f9;     /* Soft slate highlight */
  --gov-green: #10b981;          /* Medical Emerald */
  --gov-green-light: #ecfdf5;    /* Emerald tint */
  --gov-saffron: #f59e0b;        /* Amber gold */
  --gov-saffron-light: #fffbeb;  /* Amber tint */
  --gov-red: #f43f5e;            /* Clinical Rose / Emergent Red */
  --gov-red-light: #fff1f2;      /* Rose tint */
  --gov-amber: #d97706;          /* Deep Amber */
  --gov-amber-light: #fffbeb;
  --gov-slate: #64748b;          /* Cool Slate */
  --gov-slate-light: #f8fafc;

  /* Private Clinical Luxury Theme Tokens */
  --clinic-primary: #0f172a;
  --clinic-accent: #4f46e5;       /* Electric Royal Indigo */
  --clinic-accent-hover: #4338ca;
  --clinic-accent-light: #eef2ff;
  --clinic-glow: rgba(79, 70, 229, 0.22);
  --clinic-teal: #0d9488;
  --clinic-teal-light: #f0fdfa;
  --clinic-emerald: #10b981;
  --clinic-rose: #f43f5e;
  --clinic-amber: #f59e0b;

  --text-main: #0f172a;
  --text-muted: #64748b;
  --text-light: #94a3b8;
  --surface-bg: #f8fafc;
  --card-bg: #ffffff;
  --border-color: #e2e8f0;
  --border-focus: #4f46e5;

  --radius: 12px;
  --radius-lg: 18px;
  --radius-sm: 8px;
  --font-base: 'Plus Jakarta Sans', 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  --root-font-size: 16px;
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.07), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
  --shadow-lg: 0 10px 15px -3px rgba(15, 23, 42, 0.06), 0 4px 6px -4px rgba(15, 23, 42, 0.03);
  --shadow-premium: 0 20px 25px -5px rgba(15, 23, 42, 0.07), 0 8px 10px -6px rgba(15, 23, 42, 0.03);
}

/* High Contrast Mode */
html.high-contrast {
  --gov-navy: #000000;
  --gov-navy-dark: #000000;
  --gov-navy-light: #ffff00;
  --gov-green: #005500;
  --gov-red: #880000;
  --text-main: #000000;
  --text-muted: #222222;
  --surface-bg: #ffffff;
  --card-bg: #ffffff;
  --border-color: #000000;
}
html.high-contrast * {
  border-color: #000000 !important;
}

/* Base Styles */
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  font-size: var(--root-font-size);
  background-color: var(--surface-bg);
  color: var(--text-main);
  font-family: var(--font-base);
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

body {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: radial-gradient(circle at top right, rgba(99, 102, 241, 0.04) 0%, transparent 60%),
              radial-gradient(circle at top left, rgba(16, 185, 129, 0.03) 0%, transparent 50%),
              var(--surface-bg);
}

/* Skip Link */
.skip-link {
  position: absolute;
  top: -50px;
  left: 12px;
  background: var(--clinic-accent);
  color: #ffffff;
  padding: 8px 16px;
  z-index: 10000;
  text-decoration: none;
  font-weight: 700;
  border-radius: var(--radius-sm);
  transition: top 0.2s;
  box-shadow: var(--shadow-md);
}
.skip-link:focus {
  top: 12px;
  outline: 3px solid #6366f1;
}

/* Remove decorative government tricolour strip completely */
.gov-tricolour-strip {
  display: none !important;
}

/* Accessible Utility Bar - Private Health Platform Header */
.gov-utility-bar {
  background: #0f172a;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  font-size: 0.8125rem;
  color: #94a3b8;
  padding: 2px 0;
}
.gov-utility-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 6px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}
.utility-actions {
  display: flex;
  align-items: center;
  gap: 14px;
}
.font-resizer, .contrast-toggle, .lang-picker {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}
.util-btn {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.15);
  padding: 3px 10px;
  font-size: 0.75rem;
  font-weight: 700;
  color: #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  min-height: 26px;
  transition: all 0.15s ease;
}
.util-btn:hover, .util-btn:focus-visible {
  background: var(--clinic-accent);
  color: #ffffff;
  border-color: var(--clinic-accent);
  outline: none;
}

/* Header Ribbon (Mandatory Clinical Advisory) */
.gov-disclaimer-ribbon {
  background: linear-gradient(90deg, #eef2ff 0%, #f5f3ff 100%);
  border-bottom: 1px solid #e0e7ff;
  color: #3730a3;
  font-size: 0.8125rem;
  font-weight: 600;
  text-align: center;
  padding: 6px 16px;
  letter-spacing: 0.2px;
}

/* Demo Mode Banner */
.demo-mode-banner {
  background: linear-gradient(90deg, #ecfdf5 0%, #f0fdf4 100%);
  border-bottom: 1px solid #bbf7d0;
  color: #065f46;
  font-size: 0.8125rem;
  font-weight: 700;
  text-align: center;
  padding: 5px 14px;
  letter-spacing: 0.4px;
}

/* Main Header - Sleek Glassmorphism */
.gov-header {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-color);
  padding: 14px 20px;
  position: sticky;
  top: 0;
  z-index: 1000;
  box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.03);
}
.gov-header-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}
.portal-brand {
  display: flex;
  align-items: center;
  gap: 14px;
  text-decoration: none;
  color: var(--clinic-primary);
}
.portal-icon {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
  border: none;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  flex-shrink: 0;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
}
.portal-titles {
  display: flex;
  flex-direction: column;
}
.portal-name {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--clinic-primary);
  line-height: 1.2;
  letter-spacing: -0.4px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.portal-tagline {
  font-size: 0.8125rem;
  color: var(--text-muted);
  font-weight: 500;
}
.portal-badge-pro {
  font-size: 0.6875rem;
  font-weight: 800;
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
  color: #ffffff;
  padding: 2px 7px;
  border-radius: 20px;
  letter-spacing: 0.5px;
}
.portal-auth-status {
  display: flex;
  align-items: center;
  gap: 10px;
}
.portal-badge {
  font-size: 0.75rem;
  font-weight: 700;
  background: #f1f5f9;
  color: #475569;
  padding: 4px 10px;
  border-radius: 20px;
  border: 1px solid #cbd5e1;
}

/* Primary Navigation Bar */
.gov-navbar {
  background: #0f172a;
  color: #ffffff;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.gov-nav-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  overflow-x: auto;
  white-space: nowrap;
  padding: 0 10px;
}
.nav-link {
  color: #cbd5e1;
  text-decoration: none;
  padding: 12px 18px;
  font-size: 0.875rem;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-bottom: 2px solid transparent;
  transition: all 0.2s ease;
  position: relative;
}
.nav-link:hover, .nav-link:focus-visible {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.05);
  outline: none;
}
.nav-link.active {
  color: #ffffff;
  font-weight: 700;
  border-bottom-color: var(--clinic-accent);
}
.nav-link.active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 20%;
  right: 20%;
  height: 2px;
  background: #818cf8;
  box-shadow: 0 0 8px #818cf8;
}

/* Main Container */
.gov-main {
  flex: 1;
  max-width: 1200px;
  width: 100%;
  margin: 0 auto;
  padding: 28px 20px;
}

/* Emergency Alert Strip - Sleek Urgent Care Card */
.gov-emergency-strip {
  background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%);
  border: 1px solid #fecdd3;
  border-left: 5px solid var(--clinic-rose);
  padding: 14px 20px;
  margin-bottom: 24px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 14px;
  box-shadow: var(--shadow-sm);
}
.emergency-content {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #881337;
  font-size: 0.9375rem;
  font-weight: 600;
}
.emergency-phone-btn {
  background: var(--clinic-rose);
  color: #ffffff;
  padding: 8px 18px;
  font-size: 0.875rem;
  font-weight: 700;
  text-decoration: none;
  border-radius: var(--radius-sm);
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 3px 10px rgba(244, 63, 94, 0.3);
  transition: all 0.2s ease;
}
.emergency-phone-btn:hover, .emergency-phone-btn:focus-visible {
  background: #e11d48;
  transform: translateY(-1px);
  box-shadow: 0 5px 14px rgba(244, 63, 94, 0.4);
}

/* Screen Wrapper */
.screen-panel {
  display: none;
}
.screen-panel.active {
  display: block;
}

/* Wizard Layout */
.wizard-layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 28px;
  align-items: start;
}
@media (max-width: 860px) {
  .wizard-layout {
    grid-template-columns: 1fr;
  }
  .desktop-steps {
    display: none !important;
  }
}

/* Step Bar on Mobile */
.mobile-step-bar {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  padding: 12px 18px;
  border-radius: var(--radius);
  margin-bottom: 18px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.875rem;
  box-shadow: var(--shadow-sm);
}
@media (min-width: 861px) {
  .mobile-step-bar {
    display: none !important;
  }
}

/* Desktop Step Timeline */
.desktop-steps {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-md);
}
.step-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  position: relative;
}
.step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.875rem;
  color: var(--text-muted);
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  font-weight: 500;
  transition: all 0.2s ease;
}
.step-item.active {
  background: var(--clinic-accent-light);
  color: var(--clinic-accent);
  font-weight: 700;
  border-left: 3px solid var(--clinic-accent);
}
.step-item.completed {
  color: var(--clinic-emerald);
}
.step-badge {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  border: 1.5px solid currentColor;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  flex-shrink: 0;
  transition: all 0.2s ease;
}
.step-item.active .step-badge {
  background: var(--clinic-accent);
  color: #ffffff;
  border-color: var(--clinic-accent);
  box-shadow: 0 0 10px var(--clinic-glow);
}
.step-item.completed .step-badge {
  background: var(--clinic-emerald);
  color: #ffffff;
  border-color: var(--clinic-emerald);
}

/* Cards */
.gov-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 28px;
  box-shadow: var(--shadow-md);
  transition: box-shadow 0.2s ease;
}
.gov-card-header {
  border-bottom: 1px solid var(--border-color);
  padding-bottom: 18px;
  margin-bottom: 22px;
}
.gov-card-title {
  font-size: 1.45rem;
  font-weight: 800;
  color: var(--clinic-primary);
  line-height: 1.3;
  letter-spacing: -0.3px;
}
.gov-card-desc {
  font-size: 0.9375rem;
  color: var(--text-muted);
  margin-top: 6px;
  line-height: 1.5;
}

/* Form Controls & Fieldsets */
fieldset.gov-fieldset {
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 20px 18px;
  margin-bottom: 22px;
  background: #ffffff;
}
legend.gov-legend {
  font-size: 1rem;
  font-weight: 700;
  color: var(--clinic-primary);
  padding: 0 10px;
}
.req-marker {
  color: var(--clinic-rose);
  font-weight: 800;
  margin-left: 3px;
}

/* Choice Cards */
.choice-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 12px;
}
.choice-grid-3 {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.choice-grid-areas {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-top: 12px;
}
.choice-card {
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius);
  padding: 14px 16px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 52px;
  background: #ffffff;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
}
.choice-card:hover {
  border-color: #818cf8;
  background: #faf5ff;
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}
.choice-card.selected {
  border-color: var(--clinic-accent);
  background: #eef2ff;
  color: #1e1b4b;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.12);
}
.choice-card input[type="radio"],
.choice-card input[type="checkbox"] {
  width: 20px;
  height: 20px;
  accent-color: var(--clinic-accent);
  flex-shrink: 0;
}
.choice-label {
  font-size: 0.9375rem;
  line-height: 1.4;
}
.choice-hint {
  display: block;
  font-size: 0.8125rem;
  color: var(--text-muted);
  font-weight: 400;
  margin-top: 3px;
}

/* Buttons */
.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 22px;
  font-size: 0.9375rem;
  font-weight: 600;
  border-radius: var(--radius);
  cursor: pointer;
  min-height: 48px;
  border: 1px solid transparent;
  text-decoration: none;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  font-family: inherit;
}
.btn-primary {
  background: linear-gradient(135deg, #4f46e5 0%, #4338ca 100%);
  color: #ffffff;
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.35);
}
.btn-primary:hover, .btn-primary:focus-visible {
  background: linear-gradient(135deg, #4338ca 0%, #3730a3 100%);
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(79, 70, 229, 0.45);
  outline: none;
}
.btn-primary:disabled {
  background: #cbd5e1;
  color: #94a3b8;
  box-shadow: none;
  cursor: not-allowed;
  transform: none;
}
.btn-secondary {
  background: #ffffff;
  color: var(--clinic-primary);
  border-color: var(--border-color);
  box-shadow: var(--shadow-sm);
}
.btn-secondary:hover, .btn-secondary:focus-visible {
  background: var(--surface-bg);
  border-color: #cbd5e1;
  transform: translateY(-1px);
}
.btn-danger {
  background: linear-gradient(135deg, #f43f5e 0%, #e11d48 100%);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(244, 63, 94, 0.3);
}
.btn-danger:hover {
  background: #be123c;
  transform: translateY(-1px);
}
.btn-success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #ffffff;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}
.btn-success:hover {
  background: #047857;
  transform: translateY(-1px);
}
.btn-sm {
  min-height: 36px;
  padding: 6px 14px;
  font-size: 0.8125rem;
  border-radius: var(--radius-sm);
}

/* Photo Slots */
.photo-slot-card {
  border: 2px dashed #cbd5e1;
  border-radius: var(--radius-lg);
  padding: 22px;
  background: #f8fafc;
  margin-bottom: 20px;
  transition: all 0.2s ease;
}
.photo-slot-card:hover {
  border-color: var(--clinic-accent);
  background: #fdf4ff;
}
.photo-slot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.photo-slot-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* Automatic Analysis Progress Box */
.analysis-progress-box {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 18px;
  margin-top: 18px;
  position: relative;
  overflow: hidden;
}
.progress-step-item {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 0.875rem;
  color: var(--text-muted);
  margin-bottom: 8px;
  transition: color 0.2s;
}
.progress-step-item.active {
  color: var(--clinic-accent);
  font-weight: 700;
}
.progress-step-item.done {
  color: var(--clinic-emerald);
  font-weight: 600;
}

/* Live Camera Viewfinder */
.camera-card-wrap {
  border: 1px solid #334155;
  border-radius: var(--radius-lg);
  overflow: hidden;
  background: #020617;
  position: relative;
  max-width: 600px;
  margin: 0 auto;
  box-shadow: var(--shadow-premium);
}
#liveVideo {
  width: 100%;
  max-height: 420px;
  object-fit: cover;
  display: block;
}
.camera-reticle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 220px;
  height: 220px;
  border: 2px dashed rgba(255, 255, 255, 0.75);
  border-radius: var(--radius);
  pointer-events: none;
  box-shadow: 0 0 0 9999px rgba(0, 0, 0, 0.35);
}
.quality-ring-badge {
  position: absolute;
  top: 14px;
  left: 14px;
  background: rgba(15, 23, 42, 0.85);
  backdrop-filter: blur(8px);
  border: 1.5px solid rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 5px 14px;
  font-size: 0.8125rem;
  color: #ffffff;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}
.quality-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #9ca3af;
}
.camera-controls-bar {
  background: #0f172a;
  padding: 16px;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
}
.btn-shutter {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #ffffff;
  border: 4px solid var(--clinic-accent);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  box-shadow: 0 0 20px rgba(79, 70, 229, 0.4);
}
.btn-shutter:hover, .btn-shutter:focus-visible {
  outline: 3px solid #818cf8;
  transform: scale(1.06);
}
.cam-tool-btn {
  background: rgba(255, 255, 255, 0.1);
  color: #ffffff;
  border: 1px solid rgba(255, 255, 255, 0.2);
  padding: 9px 14px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 0.8125rem;
  font-weight: 600;
  transition: background 0.15s;
}
.cam-tool-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* Category Result Cards - Executive Clinical Aesthetic */
.result-hero {
  border: 1.5px solid;
  border-radius: var(--radius-lg);
  padding: 26px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-lg);
}
.result-hero.cat-a { border-color: #f59e0b; background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%); }
.result-hero.cat-b { border-color: #d97706; background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); }
.result-hero.cat-c { border-color: #64748b; background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); }
.result-hero.cat-d { border-color: #f43f5e; background: linear-gradient(135deg, #fff1f2 0%, #ffe4e6 100%); }

.res-badge-wrap {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 14px;
}
.res-ring-badge {
  width: 52px;
  height: 52px;
  border-radius: 50%;
  color: #ffffff;
  font-size: 1.6rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: var(--shadow-md);
}
.cat-a .res-ring-badge { background: #f59e0b; }
.cat-b .res-ring-badge { background: #d97706; }
.cat-c .res-ring-badge { background: #64748b; }
.cat-d .res-ring-badge { background: #f43f5e; box-shadow: 0 0 16px rgba(244, 63, 94, 0.4); }

.res-title {
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--clinic-primary);
  letter-spacing: -0.3px;
}
.res-urgency-tag {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 800;
  padding: 3px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  margin-top: 5px;
  letter-spacing: 0.6px;
}
.cat-a .res-urgency-tag { background: #fde68a; color: #92400e; }
.cat-b .res-urgency-tag { background: #fcd34d; color: #78350f; }
.cat-c .res-urgency-tag { background: #e2e8f0; color: #334155; }
.cat-d .res-urgency-tag { background: #fecdd3; color: #9f1239; }

.res-action-box {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  padding: 18px;
  margin-top: 16px;
  font-size: 1rem;
  font-weight: 600;
  color: var(--clinic-primary);
  box-shadow: var(--shadow-sm);
}

/* "Looks similar to" Panel */
.looks-similar-panel {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-left: 5px solid var(--clinic-accent);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 22px;
  box-shadow: var(--shadow-sm);
}
.strength-badge {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
}
.strength-strong { background: #ecfdf5; color: #047857; border: 1px solid #a7f3d0; }
.strength-moderate { background: #fffbeb; color: #b45309; border: 1px solid #fde68a; }
.strength-weak { background: #f8fafc; color: #475569; border: 1px solid #cbd5e1; }
.strength-abstain { background: #fff1f2; color: #be123c; border: 1px solid #fecdd3; }

/* Details & Tables */
details.gov-details {
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  margin-top: 16px;
  background: #ffffff;
  overflow: hidden;
}
details.gov-details summary {
  padding: 14px 18px;
  font-weight: 700;
  color: var(--clinic-primary);
  cursor: pointer;
  list-style: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.15s;
}
details.gov-details summary:hover {
  background: #f8fafc;
}
details.gov-details summary::-webkit-details-marker { display: none; }
details.gov-details summary::after { content: "▼"; font-size: 0.75rem; transition: transform 0.2s; color: var(--text-muted); }
details.gov-details[open] summary::after { transform: rotate(180deg); }
.details-content {
  padding: 16px 18px 20px 18px;
  border-top: 1px solid var(--border-color);
  font-size: 0.875rem;
}
.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
  font-size: 0.875rem;
}
.data-table th, .data-table td {
  border: 1px solid var(--border-color);
  padding: 10px 12px;
  text-align: left;
}
.data-table th { background: #f8fafc; font-weight: 700; color: var(--clinic-primary); }

/* Role Cards Grid for Sign-In */
.role-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}
.role-card-btn {
  background: #ffffff;
  border: 1.5px solid var(--border-color);
  border-radius: var(--radius);
  padding: 18px 14px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
}
.role-card-btn:hover, .role-card-btn.active {
  border-color: var(--clinic-accent);
  background: var(--clinic-accent-light);
  transform: translateY(-2px);
  box-shadow: 0 4px 14px rgba(79, 70, 229, 0.15);
  outline: none;
}
.role-icon {
  width: 38px;
  height: 38px;
  margin: 0 auto 10px auto;
  color: var(--clinic-accent);
}

/* Formal Private Healthcare Footer */
.gov-footer {
  background: #090d16;
  color: #94a3b8;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  margin-top: auto;
  font-size: 0.8125rem;
}
.gov-footer-inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 20px 24px 20px;
}
.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.footer-link {
  color: #cbd5e1;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.15s;
}
.footer-link:hover, .footer-link:focus-visible {
  color: #ffffff;
  text-decoration: underline;
}
.footer-disclaimer {
  color: #64748b;
  line-height: 1.6;
  margin-bottom: 16px;
}
.footer-meta {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  color: #475569;
  font-size: 0.75rem;
}

/* ==========================================================================
   MULTI-PORTAL HEALTHCARE PLATFORM STYLES - EXECUTIVE PRIVATE SUITE
   ========================================================================== */
.portal-layout {
  display: flex;
  min-height: calc(100vh - 120px);
  background: var(--surface-bg);
  position: relative;
}

.portal-sidebar {
  width: 260px;
  background: #0f172a;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 100;
}

.portal-sidebar-header {
  padding: 20px 18px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: #0f172a;
}

.portal-role-avatar {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1rem;
  flex-shrink: 0;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

.portal-nav {
  display: flex;
  flex-direction: column;
  padding: 14px 10px;
  gap: 6px;
  flex: 1;
}

.portal-nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: var(--radius-sm);
  border: none;
  background: transparent;
  color: #94a3b8;
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  text-align: left;
  width: 100%;
  transition: all 0.15s ease;
  position: relative;
  font-family: inherit;
}

.portal-nav-item:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #ffffff;
}

.portal-nav-item.active {
  background: linear-gradient(90deg, rgba(79, 70, 229, 0.25) 0%, rgba(99, 102, 241, 0.15) 100%);
  color: #ffffff;
  border-left: 3px solid #818cf8;
}

.portal-sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.portal-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
}

.portal-topbar {
  background: #ffffff;
  border-bottom: 1px solid var(--border-color);
  padding: 14px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.portal-icon-btn {
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 50%;
  width: 38px;
  height: 38px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  font-size: 1.15rem;
  transition: background 0.15s;
}
.portal-icon-btn:hover {
  background: #f1f5f9;
}

.topbar-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: var(--clinic-rose);
  color: #ffffff;
  font-size: 0.6875rem;
  font-weight: 800;
  padding: 2px 6px;
  border-radius: 10px;
  border: 1.5px solid #ffffff;
}

.portal-content-box {
  padding: 28px;
  flex: 1;
}

.portal-metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 18px;
}

.metric-card {
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}
.metric-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.metric-label {
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

.metric-value {
  font-size: 1.9rem;
  font-weight: 800;
  color: var(--clinic-primary);
  margin: 8px 0 3px 0;
  letter-spacing: -0.5px;
}

.metric-sub {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.status-pill {
  font-size: 0.6875rem;
  font-weight: 800;
  padding: 4px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  display: inline-block;
  letter-spacing: 0.4px;
}

.status-pending_asha { background: #fffbeb; color: #b45309; }
.status-assigned_doctor { background: #e0f2fe; color: #0284c7; }
.status-doctor_reviewed { background: #ecfdf5; color: #059669; }
.status-completed { background: #f0fdf4; color: #16a34a; }
.status-emergent { background: #fff1f2; color: #e11d48; box-shadow: 0 0 8px rgba(244, 63, 94, 0.2); }
.status-scheduled { background: #f5f3ff; color: #7c3aed; }

.portal-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  max-width: 90vw;
  height: 100vh;
  background: #ffffff;
  box-shadow: -6px 0 25px rgba(0, 0, 0, 0.12);
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.drawer-header {
  padding: 18px 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.drawer-body {
  padding: 20px;
  flex: 1;
  overflow-y: auto;
}

.portal-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-dialog {
  background: #ffffff;
  border-radius: var(--radius-lg);
  max-width: 580px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: var(--shadow-premium);
}

.modal-dialog.modal-lg {
  max-width: 860px;
}

.modal-header {
  padding: 18px 22px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: 22px;
  overflow-y: auto;
  flex: 1;
}

.modal-footer {
  padding: 14px 22px;
  border-top: 1px solid var(--border-color);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  background: var(--surface-bg);
}

.portal-toast {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #0f172a;
  color: #ffffff;
  padding: 14px 22px;
  border-radius: var(--radius);
  box-shadow: var(--shadow-premium);
  z-index: 2000;
  font-size: 0.875rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  animation: slideUp 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.mobile-sidebar-toggle {
  display: none;
  background: none;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 6px 10px;
}

.dropdown-quick-role {
  position: relative;
}

.quick-role-menu {
  position: absolute;
  top: 100%;
  right: 0;
  background: #ffffff;
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  box-shadow: var(--shadow-lg);
  min-width: 210px;
  z-index: 150;
  padding: 8px 0;
  margin-top: 6px;
}

.quick-role-menu button {
  display: block;
  width: 100%;
  padding: 9px 16px;
  border: none;
  background: none;
  text-align: left;
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  color: var(--clinic-primary);
  transition: background 0.15s;
}

.quick-role-menu button:hover {
  background: var(--clinic-accent-light);
  color: var(--clinic-accent);
}

.auth-tabs-bar {
  display: flex;
  border-bottom: 2px solid var(--border-color);
  margin-bottom: 20px;
}

.auth-tab-btn {
  flex: 1;
  padding: 12px 16px;
  border: none;
  background: transparent;
  font-size: 0.875rem;
  font-weight: 700;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  text-align: center;
  transition: all 0.15s;
}

.auth-tab-btn.active {
  color: var(--clinic-accent);
  border-bottom-color: var(--clinic-accent);
}

/* Custom Private Clinical Hero Elements */
.hero-card {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  border: 1px solid rgba(79, 70, 229, 0.15);
  box-shadow: var(--shadow-premium);
  position: relative;
  overflow: hidden;
}
.hero-card::after {
  content: '';
  position: absolute;
  top: -80px;
  right: -80px;
  width: 250px;
  height: 250px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.12) 0%, transparent 70%);
  pointer-events: none;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: #eef2ff;
  color: #4f46e5;
  border: 1px solid #c7d2fe;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 800;
  margin-bottom: 14px;
  letter-spacing: 0.5px;
}
.hero-metrics-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
  flex-wrap: wrap;
}
.hero-metric-item {
  display: flex;
  flex-direction: column;
}
.h-metric-val {
  font-size: 1.15rem;
  font-weight: 800;
  color: var(--clinic-primary);
}
.h-metric-lbl {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
}
.hero-metric-divider {
  width: 1px;
  height: 28px;
  background: var(--border-color);
}

.pulse-indicator-green {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10b981;
  display: inline-block;
  box-shadow: 0 0 8px #10b981;
  animation: pulseDot 2s infinite;
}

@keyframes pulseDot {
  0% { transform: scale(0.95); opacity: 0.8; }
  50% { transform: scale(1.2); opacity: 1; }
  100% { transform: scale(0.95); opacity: 0.8; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@media (max-width: 768px) {
  .mobile-sidebar-toggle { display: block; }
  .portal-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    transform: translateX(-100%);
  }
  .portal-sidebar.open {
    transform: translateX(0);
    box-shadow: 6px 0 25px rgba(0, 0, 0, 0.4);
  }
  .doc-modal-grid { grid-template-columns: 1fr !important; }
  .analyst-charts-grid { grid-template-columns: 1fr !important; }
}
</style>"""
    html = html[:style_start] + premium_css + html[style_end + len('</style>'):]
    print("Replaced CSS with Private Premium Clinical Design System.")

# 3. Upgrade HTML Header and Utility Bar
# Remove government reference in utility bar
html = re.sub(
    r'<span>Government Hospital Health Portal Screening Support</span>',
    r'<div style="display:flex;align-items:center;gap:8px;"><span class="pulse-indicator-green" aria-hidden="true"></span><span style="font-weight:600;color:#e2e8f0;">DermaSense™ Precision Clinical AI Suite &bull; Multi-Model Ensemble Active</span></div>',
    html
)

# Header Ribbon Disclaimer
html = re.sub(
    r'<div class="gov-disclaimer-ribbon" role="note">\s*Prototype screening aid\. Not an official government or hospital service\.\s*</div>',
    r'<div class="gov-disclaimer-ribbon" role="note"><span style="background:#4f46e5;color:#ffffff;font-size:0.6875rem;padding:2px 8px;border-radius:12px;font-weight:800;margin-right:8px;">CLINICAL DECISION AID</span> Screening & triage decision support. Prototype research build — not an autonomous clinical diagnosis. Always consult a qualified dermatologist.</div>',
    html
)

# Portal Header Brand Title
html = re.sub(
    r'<span class="portal-name">DermaSense: Skin Rash Screening and Referral Aid</span>\s*<span class="portal-tagline">Clinical Decision Support & Community Referral Portal</span>',
    r'<span class="portal-name">DermaSense <span class="portal-badge-pro">CLINICAL AI</span></span>\n        <span class="portal-tagline">Precision Dermatological Screening & Referral System</span>',
    html
)

# Emergency strip text
html = re.sub(
    r'<span>In an emergency go to the nearest hospital or call <strong>108</strong> \(National Ambulance Service\) or <strong>112</strong>\.</span>',
    r'<span><strong>24/7 Rapid Emergency Response:</strong> If experiencing acute swelling, fever, or respiratory distress, seek immediate hospital care or call <strong>108 / 112</strong> immediately.</span>',
    html
)

# Home View Hero Card upgrade
old_hero = """  <section id="view-home" class="screen-panel active">
    <div class="gov-card" style="margin-bottom:24px;">
      <h1 class="gov-card-title" style="font-size:1.75rem;margin-bottom:8px;">Skin Rash Screening and Referral Portal</h1>
      <p style="color:var(--text-muted);font-size:1.0625rem;max-width:760px;margin-bottom:20px;">
        A rapid, deterministic clinical decision aid designed for community screening in India. Helps patients and primary healthcare workers determine the urgency of a rash and appropriate referral steps. Works offline without account.
      </p>
      <div style="display:flex;gap:12px;flex-wrap:wrap;">
        <button type="button" class="btn btn-primary" onclick="startScreeningFlow()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.5 3h3v5a4.5 4.5 0 0 0 9 0V3h3"/><path d="M12 12.5V17a3 3 0 0 0 3 3h2a2 2 0 1 0 0-4h-2"/><circle cx="19" cy="18" r="1"/></svg>
          Check a Skin Rash
        </button>
        <button type="button" class="btn btn-secondary" onclick="navigateTo('signin')">Role Sign In & Demo</button>
        <button type="button" class="btn btn-secondary" onclick="navigateTo('how')">Learn How it Works</button>
      </div>
    </div>"""

new_hero = """  <section id="view-home" class="screen-panel active">
    <div class="gov-card hero-card" style="margin-bottom:24px;">
      <div class="hero-badge">
        <span class="pulse-indicator-green"></span>
        <span>ADVANCED CLINICAL DERMATOLOGY SUITE &bull; 5 ACTIVE MODELS</span>
      </div>
      <h1 class="gov-card-title" style="font-size:2.1rem;margin-bottom:10px;font-weight:800;letter-spacing:-0.5px;">Precision Skin Rash Screening & Referral Platform</h1>
      <p style="color:var(--text-muted);font-size:1.0625rem;max-width:760px;margin-bottom:24px;line-height:1.6;">
        Next-generation multi-model neural vision analysis (MobileNetV3, EfficientNet, 22-Class Edge, SkinCNN, DermaAI) synchronized with deterministic clinical safety protocols for rapid, explainable skin condition screening and primary care referral.
      </p>
      <div style="display:flex;gap:14px;flex-wrap:wrap;align-items:center;">
        <button type="button" class="btn btn-primary" onclick="startScreeningFlow()" style="padding:12px 26px;font-size:1rem;">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.5 3h3v5a4.5 4.5 0 0 0 9 0V3h3"/><path d="M12 12.5V17a3 3 0 0 0 3 3h2a2 2 0 1 0 0-4h-2"/><circle cx="19" cy="18" r="1"/></svg>
          Start Clinical Screening &rarr;
        </button>
        <button type="button" class="btn btn-secondary" onclick="navigateTo('signin')" style="padding:12px 20px;">Staff & Clinical Portals</button>
        <button type="button" class="btn btn-secondary" onclick="navigateTo('how')" style="padding:12px 20px;">Evidence & Model Specs</button>
      </div>

      <div class="hero-metrics-bar">
        <div class="hero-metric-item">
          <span class="h-metric-val">5 Models Active</span>
          <span class="h-metric-lbl">Synchronized Neural Ensembles</span>
        </div>
        <div class="hero-metric-divider"></div>
        <div class="hero-metric-item">
          <span class="h-metric-val">100% Deterministic</span>
          <span class="h-metric-lbl">Rule-Based Safety Backbone</span>
        </div>
        <div class="hero-metric-divider"></div>
        <div class="hero-metric-item">
          <span class="h-metric-val">Zero-Retention</span>
          <span class="h-metric-lbl">Transient In-Memory Evaluation</span>
        </div>
      </div>
    </div>"""

if old_hero in html:
    html = html.replace(old_hero, new_hero)
    print("Replaced home hero section with modern private clinical layout.")

# Footer text upgrade
html = re.sub(
    r'<span>Portal Version: v2\.2 \(Role-Based Indian Hospital Health Portal\)</span>',
    r'<span>Platform: DermaSense™ Precision Clinical AI Suite (v3.2 Production)</span>',
    html
)
html = re.sub(
    r'<span>Standards: WCAG 2\.1 AA / GIGW 3\.0 Conformance</span>',
    r'<span>Standards: WCAG 2.1 AA / Clinical Decision Support Framework</span>',
    html
)

with open(INDEX_HTML_PATH, 'w', encoding='utf-8') as f:
    f.write(html)

print("Saved updated web/index.html successfully.")
