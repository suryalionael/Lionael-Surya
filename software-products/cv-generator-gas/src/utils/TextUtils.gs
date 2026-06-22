/**
 * @fileoverview Text manipulation utilities for the MSI CV Generator.
 *
 * Shared helpers for name normalization (used for fuzzy employee matching),
 * string joining, de-duplication, and general text cleaning.
 */

const TextUtils = {

  /**
   * Normalizes a name for fuzzy matching: lowercase, trim, collapse
   * internal whitespace, remove common punctuation and diacritics.
   * Used to match spreadsheet "Nama lengkap" values against Drive folder
   * names and Control Panel entries.
   *
   * @param {string} name
   * @return {string}
   */
  normalizeName(name) {
    return String(name || '')
      .toLowerCase()
      .trim()
      .replace(/\s+/g, ' ')           // collapse whitespace
      .replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, '') // remove punctuation
      .normalize('NFD')               // decompose diacritics
      .replace(/[̀-ͯ]/g, '') // strip combining marks
      .trim();
  },

  /**
   * Joins non-empty strings with `separator`, skipping null/undefined/blank.
   *
   * @param {Array<string|null|undefined>} parts
   * @param {string} [separator='  ']
   * @return {string}
   */
  joinNonEmpty(parts, separator) {
    const sep = separator !== undefined ? separator : '  ';
    return (parts || [])
      .map((p) => String(p || '').trim())
      .filter(Boolean)
      .join(sep);
  },

  /**
   * De-duplicates an array of objects using a key-selector function.
   * Preserves the FIRST occurrence of each unique key; later duplicates
   * are discarded.
   *
   * @param {Array<Object>} arr
   * @param {function(Object): string} keyFn
   * @return {Array<Object>}
   */
  dedupeBy(arr, keyFn) {
    const seen = {};
    return (arr || []).filter((item) => {
      const k = keyFn(item);
      if (seen[k]) return false;
      seen[k] = true;
      return true;
    });
  },

  /**
   * Capitalizes the first letter of each word in a string.
   *
   * @param {string} text
   * @return {string}
   */
  titleCase(text) {
    return String(text || '').replace(/\b\w/g, (c) => c.toUpperCase());
  },

  /**
   * Truncates `text` to `maxLength` chars, appending "…" if truncated.
   *
   * @param {string} text
   * @param {number} maxLength
   * @return {string}
   */
  truncate(text, maxLength) {
    const s = String(text || '');
    return s.length <= maxLength ? s : s.slice(0, maxLength - 1) + '…';
  },

  /**
   * Returns true if two name strings are considered a match (using
   * normalizeName on both sides). Used for employee-name lookup in the
   * Control Panel and project spreadsheet.
   *
   * @param {string} a
   * @param {string} b
   * @return {boolean}
   */
  namesMatch(a, b) {
    return this.normalizeName(a) === this.normalizeName(b);
  },
};
