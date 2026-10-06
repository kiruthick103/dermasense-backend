/**
 * Golden Vector Parity Test for JavaScript Deterministic Ladder.
 * Reads tests/golden_vectors.json and verifies that JavaScript logic produces
 * identical category and urgency ratings as the Python engine.
 */

const fs = require('fs');
const path = require('path');
const assert = require('assert');

const goldenPath = path.join(__dirname, 'golden_vectors.json');
const raw = fs.readFileSync(goldenPath, 'utf8');
const vectors = JSON.parse(raw);

function runJsDeterministicLadder(inp) {
  const danger = inp.danger_signs || [];
  let steroidRisk = 0;
  let fungalPoints = 0;

  // 1. Any danger sign -> D immediately
  if (danger.length > 0) {
    return { category: 'D', urgency: 'EMERGENT', bypassed_model: true };
  }

  // 2. Contradictions -> C
  if (inp.used_any_cream === 'NO' && (inp.steroid_name_visible === 'YES' || inp.spread_despite_treatment === 'YES')) {
    return { category: 'C', urgency: 'ROUTINE', has_contradiction: true };
  }

  // 3. Steroid risk
  if (inp.used_any_cream === 'YES' && inp.prescribed_by_clinician === 'NO') steroidRisk += 2;
  if (inp.steroid_name_visible === 'YES') steroidRisk += 3;
  if (inp.spread_despite_treatment === 'YES') steroidRisk += 2;
  if (inp.returned_after_stopping === 'YES') steroidRisk += 1;
  if (inp.combination_wording === 'YES') steroidRisk += 1;

  // 4. Fungal pattern
  const pat = inp.pattern_model || {};
  if (pat.top_class === 'fungal_ring_pattern' && (pat.strength === 'Strong' || pat.strength === 'Moderate')) {
    fungalPoints += 2;
  }
  if (inp.itchy_ring_or_scaly === 'YES') fungalPoints += 1;
  if (inp.duration === 'YES') fungalPoints += 1;

  // 5. Ladder
  let category = 'C';
  let urgency = 'ROUTINE';

  if (steroidRisk >= 3) {
    category = 'B';
    urgency = 'ELEVATED';
  } else if (inp.image_quality && inp.image_quality.acceptable === false) {
    category = 'C';
    urgency = 'ROUTINE';
  } else if (fungalPoints >= 2) {
    category = 'A';
    urgency = 'ROUTINE';
  } else {
    category = 'C';
    urgency = 'ROUTINE';
  }

  // Vulnerable flag elevates urgency
  if (inp.vulnerable_flags && inp.vulnerable_flags.length > 0 && urgency === 'ROUTINE') {
    urgency = 'ELEVATED';
  }

  return { category, urgency, steroidRisk, fungalPoints };
}

console.log('🧪 Starting JavaScript Golden Vector Parity Test...');
for (const v of vectors) {
  const actual = runJsDeterministicLadder(v.input);
  assert.strictEqual(actual.category, v.expected.category, `Vector ${v.id} category mismatch`);
  assert.strictEqual(actual.urgency, v.expected.urgency, `Vector ${v.id} urgency mismatch`);
  console.log(`✓ Vector ${v.id}: ${v.name} -> Cat ${actual.category} (${actual.urgency}) MATCH`);
}

console.log('\n🎉 ALL GOLDEN VECTORS PASS IN JAVASCRIPT WITH 100% PARITY!\n');
