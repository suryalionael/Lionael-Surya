/**
 * @fileoverview Tests for DateUtils.
 */

const DateUtilsTests = {
  _name: 'DateUtils',

  test_parsePeriodString_englishMonths() {
    const r = DateUtils.parsePeriodString('Mar 2017 – Now');
    assertNotNull(r.startDate);
    assertEqual(r.startDate.getFullYear(), 2017);
    assertEqual(r.startDate.getMonth(), 2); // March = index 2
    assertTrue(r.isOngoing);
  },

  test_parsePeriodString_indonesianMonths() {
    const r = DateUtils.parsePeriodString('Maret 2020 – September 2020');
    assertNotNull(r.startDate);
    assertEqual(r.startDate.getFullYear(), 2020);
    assertEqual(r.startDate.getMonth(), 2);
    assertNotNull(r.endDate);
    assertEqual(r.endDate.getMonth(), 8); // September = index 8
    assertFalse(r.isOngoing);
  },

  test_parsePeriodString_sekarang() {
    const r = DateUtils.parsePeriodString('Juli 2025 - Sekarang');
    assertTrue(r.isOngoing);
    assertEqual(r.startDate.getMonth(), 6); // July = index 6
  },

  test_parsePeriodString_yearOnly() {
    const r = DateUtils.parsePeriodString('2010 - 2014');
    assertNotNull(r.startDate);
    assertEqual(r.startDate.getFullYear(), 2010);
    assertEqual(r.endDate.getFullYear(), 2014);
  },

  test_parsePeriodString_empty() {
    const r = DateUtils.parsePeriodString('');
    assertNull(r.startDate);
    assertNull(r.endDate);
    assertFalse(r.isOngoing);
  },

  test_extractYear_found() {
    assertEqual(DateUtils.extractYear('Financial Consolidation 2026'), '2026');
  },

  test_extractYear_notFound() {
    assertEqual(DateUtils.extractYear('No year here'), '');
  },

  test_formatMonthYear() {
    const d = new Date(2026, 4, 23); // May 2026
    assertEqual(DateUtils.formatMonthYear(d), 'May, 2026');
  },
};
