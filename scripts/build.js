/**
 * DermaSense Frontend Build Script
 * Synchronizes web/ to public/, validates JavaScript syntax, and verifies static assets.
 */
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('====================================================');
console.log('DERMASENSE FRONTEND BUILD PROCESS');
console.log('====================================================');

const ROOT_DIR = path.resolve(__dirname, '..');
const WEB_DIR = path.join(ROOT_DIR, 'web');
const PUBLIC_DIR = path.join(ROOT_DIR, 'public');

// 1. Validate JavaScript syntax
const jsFiles = ['portal.js', 'camera.js'];
jsFiles.forEach(file => {
  const filePath = path.join(WEB_DIR, file);
  if (fs.existsSync(filePath)) {
    try {
      execSync(`node --check "${filePath}"`, { stdio: 'pipe' });
      console.log(`✓ JavaScript syntax valid: ${file}`);
    } catch (e) {
      console.error(`✗ Syntax error in ${file}:`, e.message);
      process.exit(1);
    }
  }
});

// 2. Synchronize web/ to public/
function copyRecursive(src, dest) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true });
  }
  const entries = fs.readdirSync(src, { withFileTypes: true });
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyRecursive(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}

copyRecursive(WEB_DIR, PUBLIC_DIR);
console.log('✓ Synchronized web/ -> public/ successfully.');

// 3. Verify public files exist
const requiredFiles = ['index.html', 'portal.js', 'camera.js'];
let allFound = true;
requiredFiles.forEach(f => {
  const p = path.join(PUBLIC_DIR, f);
  if (!fs.existsSync(p)) {
    console.error(`✗ Missing required file in public/: ${f}`);
    allFound = false;
  } else {
    const stat = fs.statSync(p);
    console.log(`✓ Verified public/${f} (${(stat.size / 1024).toFixed(1)} KB)`);
  }
});

if (!allFound) {
  process.exit(1);
}

console.log('====================================================');
console.log('FRONTEND BUILD COMPLETE: SUCCESS');
console.log('====================================================');
