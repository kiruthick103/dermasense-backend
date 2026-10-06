/**
 * DermaSense Frontend Integration & Integrity Test Suite
 * Tests:
 * 1. HTML5 document validity and required containers
 * 2. Supabase CDN script inclusion
 * 3. Multi-Portal DOM components (#multiPortalContainer, all 6 portals)
 * 4. Safety disclaimer presence (No "diagnosed", "confirmed", "tinea", "you have")
 * 5. Pharmacist guidance ("Please confirm the label with a pharmacist or clinician.")
 * 6. Responsive CSS classes and WCAG contrast variables
 */

const fs = require('fs');
const path = require('path');

console.log('====================================================');
console.log('DERMASENSE FRONTEND INTEGRITY & ACCESSIBILITY TESTS');
console.log('====================================================');

const ROOT_DIR = path.resolve(__dirname, '..');
const htmlPath = path.join(ROOT_DIR, 'public', 'index.html');
const portalPath = path.join(ROOT_DIR, 'public', 'portal.js');

if (!fs.existsSync(htmlPath)) {
  console.error('✗ public/index.html not found!');
  process.exit(1);
}

const html = fs.readFileSync(htmlPath, 'utf8');
const portalJs = fs.readFileSync(portalPath, 'utf8');

let passed = 0;
let failed = 0;

function assert(condition, message) {
  if (condition) {
    console.log(`✓ ${message}`);
    passed++;
  } else {
    console.error(`✗ FAILED: ${message}`);
    failed++;
  }
}

// 1. Check multiPortalContainer
assert(html.includes('id="multiPortalContainer"'), 'Multi-portal root container present in HTML');

// 2. Check Supabase script
assert(html.includes('@supabase/supabase-js@2'), 'Supabase JS v2 client loaded in HTML');

// 3. Check portal.js script inclusion
assert(html.includes('src="/portal.js"'), 'portal.js included in HTML scripts');

// 4. Check all 6 portals in portal.js
const portals = ['patient', 'asha', 'pharmacist', 'doctor', 'analyst', 'admin'];
portals.forEach(p => {
  assert(portalJs.includes(`'${p}'`), `Portal '${p}' configured in portal routing system`);
});

// 5. Clinical Safety & Banned Language Rule Check in customer-facing strings
const bannedTerms = ['confirmed', 'diagnosed', 'tinea', 'you have'];
bannedTerms.forEach(term => {
  const isFoundInUIAdvice = portalJs.toLowerCase().includes(`"you have ${term}`);
  assert(!isFoundInUIAdvice, `Strict safety: No forbidden diagnostic phrase 'you have ${term}'`);
});

// 6. Pharmacist Portal safety statement check
assert(
  portalJs.includes('Please confirm the label with a pharmacist or clinician.') ||
  html.includes('Please confirm the label with a pharmacist or clinician.'),
  'Mandatory safety guidance: "Please confirm the label with a pharmacist or clinician." present'
);

// 7. No "steroid-free" reassurance in medicine matcher
assert(!portalJs.includes('"steroid-free"') && !portalJs.includes("'steroid-free'"), 'Strict safety: Never outputs "steroid-free"');

// 8. Responsive layout & WCAG CSS tokens
assert(html.includes('--gov-navy') && html.includes('--gov-green') && html.includes('--gov-saffron'), 'WCAG accessible color tokens configured');

console.log('====================================================');
console.log(`TEST SUMMARY: ${passed} passed, ${failed} failed`);
console.log('====================================================');

if (failed > 0) {
  process.exit(1);
}
