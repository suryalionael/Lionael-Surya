/**
 * @fileoverview Tests for TextUtils.
 */

const TextUtilsTests = {
  _name: 'TextUtils',

  test_normalizeName_trimsAndLowercases() {
    assertEqual(TextUtils.normalizeName('  Kevin Januar H.  '), 'kevin januar h');
  },

  test_normalizeName_collapsesWhitespace() {
    assertEqual(TextUtils.normalizeName('Krista  Nadella'), 'krista nadella');
  },

  test_normalizeName_emptyString() {
    assertEqual(TextUtils.normalizeName(''), '');
    assertEqual(TextUtils.normalizeName(null), '');
  },

  test_namesMatch_caseInsensitive() {
    assertTrue(TextUtils.namesMatch('Kevin Januar H', 'kevin januar h'));
  },

  test_namesMatch_trimmed() {
    assertTrue(TextUtils.namesMatch('  Owen Djoenaedi  ', 'Owen Djoenaedi'));
  },

  test_namesMatch_differentNames() {
    assertFalse(TextUtils.namesMatch('Kevin', 'Krista'));
  },

  test_joinNonEmpty_skipsBlank() {
    assertEqual(TextUtils.joinNonEmpty(['PT MSI', '', 'Jakarta'], ' | '), 'PT MSI | Jakarta');
  },

  test_joinNonEmpty_allBlank() {
    assertEqual(TextUtils.joinNonEmpty([null, '', undefined], ' | '), '');
  },

  test_dedupeBy_removesSecondOccurrence() {
    const arr = [
      { name: 'AWS', year: '2024' },
      { name: 'GCP', year: '2023' },
      { name: 'AWS', year: '2024' },  // duplicate
    ];
    const result = TextUtils.dedupeBy(arr, (t) => t.name + '|' + t.year);
    assertEqual(result.length, 2);
    assertEqual(result[0].name, 'AWS');
    assertEqual(result[1].name, 'GCP');
  },
};
