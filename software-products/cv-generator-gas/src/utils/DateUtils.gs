/**
 * @fileoverview Date parsing and formatting utilities.
 *
 * Handles the wide variety of date formats found in the employee data sources:
 *   - "Mar 2017 – Now"         (Indonesian/English mixed, en-dash)
 *   - "Maret 2020 – September 2020"  (Indonesian month names)
 *   - "Juli 2025 - Sekarang"   (Indonesian "now")
 *   - "2010 - 2014"            (year-only range)
 *   - "Sept 2013 – Jan 2014"   (abbreviated months)
 *   - "May-August 2025"        (same-year range, hyphen separator)
 */

const DateUtils = {

  // ── Indonesian month name map ─────────────────────────────────────────────
  _ID_MONTHS_: {
    januari: 0, februari: 1, maret: 2, april: 3, mei: 4, juni: 5,
    juli: 6, agustus: 7, september: 8, oktober: 9, november: 10, desember: 11,
    // Common abbreviations:
    jan: 0, feb: 1, mar: 2, apr: 3, // mei already above
    jun: 5, jul: 6, agu: 7, ags: 7, sep: 8, okt: 9, nov: 10, des: 11,
  },

  // ── English month name map ────────────────────────────────────────────────
  _EN_MONTHS_: {
    january: 0, february: 1, march: 2, april: 3, may: 4, june: 5,
    july: 6, august: 7, september: 8, october: 9, november: 10, december: 11,
    jan: 0, feb: 1, mar: 2, apr: 3, jun: 5, jul: 6, aug: 7,
    sep: 8, sept: 8, oct: 9, nov: 10, dec: 11,
  },

  // ── "Ongoing" keywords ────────────────────────────────────────────────────
  _ONGOING_RE_: /\b(now|present|sekarang|current|ongoing)\b/i,

  /**
   * Parses a free-text period string into start date, end date, and
   * isOngoing flag.
   *
   * @param {string} periodStr  e.g. "Maret 2020 – September 2020"
   * @return {{startDate: Date|null, endDate: Date|null, isOngoing: boolean}}
   */
  parsePeriodString(periodStr) {
    const text = String(periodStr || '').trim();
    if (!text) return { startDate: null, endDate: null, isOngoing: false };

    // Normalize separators: en-dash, em-dash, or " - " → " | "
    const normalized = text.replace(/\s*[–—]\s*|\s+-\s+/g, ' | ');
    const parts = normalized.split('|').map((p) => p.trim());

    const startDate = this._parseDate_(parts[0]);
    let endDate = null;
    let isOngoing = false;

    if (parts.length >= 2) {
      if (this._ONGOING_RE_.test(parts[1])) {
        isOngoing = true;
      } else {
        endDate = this._parseDate_(parts[1]);
        // Handle "Month-Month Year" same-year ranges (e.g. "May-August 2025")
        if (!endDate && parts[1]) {
          // Try appending the year from the start string.
          const yearMatch = text.match(/\b(\d{4})\b/);
          if (yearMatch) {
            endDate = this._parseDate_(parts[1] + ' ' + yearMatch[1]);
          }
        }
      }
    }

    return { startDate, endDate, isOngoing };
  },

  /**
   * Parses a single date token: "Maret 2020", "Mar 2017", "2014", etc.
   *
   * @param {string} token
   * @return {Date|null}
   */
  _parseDate_(token) {
    if (!token) return null;
    const t = token.trim().toLowerCase();

    // Year-only: "2014"
    const yearOnly = t.match(/^(\d{4})$/);
    if (yearOnly) return new Date(parseInt(yearOnly[1], 10), 0, 1);

    // "Month YYYY" or "Month. YYYY"
    const monthYear = t.match(/^([a-z]+)\.?\s+(\d{4})$/);
    if (monthYear) {
      const monthName = monthYear[1].replace(/\.$/, '');
      const year = parseInt(monthYear[2], 10);
      const monthIdx = this._ID_MONTHS_[monthName] !== undefined
        ? this._ID_MONTHS_[monthName]
        : this._EN_MONTHS_[monthName];
      if (monthIdx !== undefined) return new Date(year, monthIdx, 1);
    }

    // Fallback: let JS parse it.
    const d = new Date(token);
    return isNaN(d.getTime()) ? null : d;
  },

  /**
   * Extracts the first 4-digit year found in a text string.
   *
   * @param {string} text
   * @return {string}  e.g. "2024", or "" if not found
   */
  extractYear(text) {
    const m = String(text || '').match(/\b(\d{4})\b/);
    return m ? m[1] : '';
  },

  /**
   * Formats a Date as "Month, YYYY" (English), e.g. "May, 2026".
   * Used for the "Last Updated on <Month, Year>" line.
   *
   * @param {Date} date
   * @return {string}
   */
  formatMonthYear(date) {
    const months = [
      'January','February','March','April','May','June',
      'July','August','September','October','November','December',
    ];
    return months[date.getMonth()] + ', ' + date.getFullYear();
  },

  /**
   * Computes full years between `startDate` and today, rounded down.
   *
   * @param {Date} startDate
   * @return {number}
   */
  yearsFrom(startDate) {
    if (!startDate) return 0;
    const ms = Date.now() - startDate.getTime();
    return Math.floor(ms / (365.25 * 24 * 3600 * 1000));
  },
};
