/**
 * @fileoverview Manual test runner for the MSI CV Generator.
 *
 * These are unit-style tests designed to run INSIDE the Apps Script editor
 * (no external test framework needed). Run runAllTests() from the editor's
 * function dropdown and check the execution log for PASS / FAIL output.
 *
 * Tests are deterministic and do not make network calls or modify Drive/
 * Sheets state — they exercise pure logic (parsing, date utilities, text
 * normalization, data aggregation, template engine table algorithms).
 */

/**
 * Global test entry point. Run this from the Apps Script editor.
 * Results appear in the execution log (View > Logs or Ctrl+Enter).
 */
function runAllTests() {
  const suites = [
    TextUtilsTests,
    DateUtilsTests,
    SpreadsheetRepositoryTests,
    EmployeeRepositoryTests,
    TemplateEngineTests,
    DataAggregationTests,
  ];

  let totalPass = 0;
  let totalFail = 0;

  suites.forEach((suite) => {
    const name = suite._name || '(unnamed suite)';
    console.log('\n══════ ' + name + ' ══════');

    Object.keys(suite).forEach((key) => {
      if (key.startsWith('test_') && typeof suite[key] === 'function') {
        try {
          suite[key]();
          console.log('  ✓ PASS  ' + key);
          totalPass++;
        } catch (e) {
          console.log('  ✗ FAIL  ' + key + '\n         ' + e.message);
          totalFail++;
        }
      }
    });
  });

  console.log('\n══════ RESULTS ══════');
  console.log('Passed: ' + totalPass);
  console.log('Failed: ' + totalFail);
  console.log('Total:  ' + (totalPass + totalFail));
}

// ── Assertion helpers ─────────────────────────────────────────────────────

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(
      (message ? message + ' — ' : '') +
      'Expected ' + JSON.stringify(expected) +
      ' but got ' + JSON.stringify(actual)
    );
  }
}

function assertDeepEqual(actual, expected, message) {
  const a = JSON.stringify(actual);
  const b = JSON.stringify(expected);
  if (a !== b) {
    throw new Error(
      (message ? message + ' — ' : '') +
      'Expected ' + b + ' but got ' + a
    );
  }
}

function assertTrue(condition, message) {
  if (!condition) throw new Error(message || 'Expected true but got false');
}

function assertFalse(condition, message) {
  if (condition) throw new Error(message || 'Expected false but got true');
}

function assertNull(value, message) {
  if (value !== null && value !== undefined) {
    throw new Error((message || 'Expected null/undefined but got') + ': ' + JSON.stringify(value));
  }
}

function assertNotNull(value, message) {
  if (value === null || value === undefined) {
    throw new Error(message || 'Expected non-null value');
  }
}
