/**
 * @fileoverview Repository for all three managed sheets in the bound
 * "CV Control Panel" spreadsheet:
 *
 *   ┌──────────────────────┐
 *   │  CV Control Panel    │  Employee Name | Generate (checkbox)
 *   ├──────────────────────┤
 *   │  Logs                │  Timestamp | Level | Step | Employee | Message | Meta
 *   ├──────────────────────┤
 *   │  Last Run Summary    │  Timestamp | Run Type | Employee | Status | Detail | Doc URL | PDF URL
 *   └──────────────────────┘
 *
 * The Logs sheet is append-only and capped at LOG_MAX_ROWS rows to prevent
 * unbounded growth. The Last Run Summary sheet is cleared and rewritten on
 * every batch run (it's a snapshot, not a history — the Logs sheet is the
 * persistent history).
 *
 * Employee list sync is additive: new names are appended, existing rows are
 * never deleted (preserves checkbox state; departed employees simply produce
 * a per-employee failure in the next run, which is logged and reported).
 */

const ControlPanelRepository = {

  LOG_MAX_ROWS: 2000,

  CONTROL_PANEL_HEADERS: ['Employee Name', 'Generate'],
  LOGS_HEADERS: ['Timestamp', 'Level', 'Step', 'Employee', 'Message', 'Meta'],
  SUMMARY_HEADERS: ['Timestamp', 'Run Type', 'Employee', 'Status', 'Detail', 'Doc URL', 'PDF URL'],

  _ss_() {
    return SpreadsheetApp.getActiveSpreadsheet();
  },

  // ── Sheet accessors ───────────────────────────────────────────────────────

  /**
   * Returns (creating if needed) the "CV Control Panel" sheet with its
   * header row and column-B checkbox data validation.
   *
   * @return {GoogleAppsScript.Spreadsheet.Sheet}
   */
  getControlPanelSheet() {
    const name = CONFIG_STATIC.CONTROL_PANEL_SHEET_NAME;
    let sheet = this._ss_().getSheetByName(name);
    if (!sheet) {
      sheet = this._ss_().insertSheet(name, 0); // insert as the first (leftmost) tab
      this._writeHeaderRow_(sheet, this.CONTROL_PANEL_HEADERS);
    }
    return sheet;
  },

  /**
   * Returns (creating if needed) the "Logs" sheet.
   *
   * @return {GoogleAppsScript.Spreadsheet.Sheet}
   */
  getOrCreateLogsSheet() {
    return this._getOrCreateSheet_(CONFIG_STATIC.LOGS_SHEET_NAME, this.LOGS_HEADERS);
  },

  /**
   * Returns (creating if needed) the "Last Run Summary" sheet.
   *
   * @return {GoogleAppsScript.Spreadsheet.Sheet}
   */
  getOrCreateSummarySheet() {
    return this._getOrCreateSheet_(CONFIG_STATIC.SUMMARY_SHEET_NAME, this.SUMMARY_HEADERS);
  },

  /**
   * Creates all three managed sheets if they don't exist yet. Called by
   * SetupController after the output folder and template are ready.
   */
  ensureSheetsExist() {
    this.getControlPanelSheet();
    this.getOrCreateLogsSheet();
    this.getOrCreateSummarySheet();
    // Ensure the active sheet is the Control Panel.
    this._ss_().setActiveSheet(this.getControlPanelSheet());
  },

  // ── Control Panel operations ──────────────────────────────────────────────

  /**
   * Returns employee names whose "Generate" checkbox (column B) is TRUE.
   *
   * @return {string[]}
   */
  getCheckedEmployees() {
    const sheet = this.getControlPanelSheet();
    const lastRow = sheet.getLastRow();
    if (lastRow < 2) return [];
    const values = sheet.getRange(2, 1, lastRow - 1, 2).getValues();
    return values
      .filter((row) => row[1] === true)
      .map((row) => String(row[0]).trim())
      .filter(Boolean);
  },

  /**
   * Returns ALL employee rows as {name, generate} objects.
   *
   * @return {Array<{name: string, generate: boolean}>}
   */
  getAllEmployeeRows() {
    const sheet = this.getControlPanelSheet();
    const lastRow = sheet.getLastRow();
    if (lastRow < 2) return [];
    const values = sheet.getRange(2, 1, lastRow - 1, 2).getValues();
    return values
      .map((row) => ({ name: String(row[0]).trim(), generate: row[1] === true }))
      .filter((r) => r.name);
  },

  /**
   * Additive sync of discovered employee names into the Control Panel.
   * Appends names not already present (with unchecked box). Preserves
   * existing rows and their checkbox states.
   *
   * @param {string[]} discoveredNames
   */
  setEmployeeList(discoveredNames) {
    const sheet = this.getControlPanelSheet();
    const existing = this.getAllEmployeeRows().map((r) => TextUtils.normalizeName(r.name));

    const toAppend = (discoveredNames || []).filter(
      (name) => existing.indexOf(TextUtils.normalizeName(name)) === -1
    );

    if (toAppend.length > 0) {
      const startRow = sheet.getLastRow() + 1;
      const rows = toAppend.map((name) => [name, false]);
      sheet.getRange(startRow, 1, rows.length, 2).setValues(rows);
    }

    // Ensure checkbox data validation on all data rows (idempotent — re-applying
    // to already-checked cells preserves their state).
    const lastRow = sheet.getLastRow();
    if (lastRow >= 2) {
      const rule = SpreadsheetApp.newDataValidation().requireCheckbox().build();
      sheet.getRange(2, 2, lastRow - 1, 1).setDataValidation(rule);
      // Auto-resize the Name column for readability.
      sheet.autoResizeColumn(1);
    }
  },

  // ── Logging operations ────────────────────────────────────────────────────

  /**
   * Appends one structured log row to the Logs sheet.
   * Trims oldest rows when the sheet exceeds LOG_MAX_ROWS.
   *
   * @param {{timestamp: Date, level: string, step: string, employeeName: string,
   *          message: string, meta: string}} entry
   */
  appendLogEntry(entry) {
    const sheet = this.getOrCreateLogsSheet();
    sheet.appendRow([
      entry.timestamp,
      entry.level,
      entry.step,
      entry.employeeName,
      entry.message,
      entry.meta || '',
    ]);

    // Cap growth.
    const dataRows = sheet.getLastRow() - 1; // exclude header
    if (dataRows > this.LOG_MAX_ROWS) {
      const excess = dataRows - this.LOG_MAX_ROWS;
      sheet.deleteRows(2, excess); // delete oldest rows (just after header)
    }
  },

  // ── Run Summary operations ────────────────────────────────────────────────

  /**
   * Clears and rewrites the Last Run Summary sheet with results from the
   * most recent batch run.
   *
   * @param {Array<{success: boolean, employeeName: string, error: ?string,
   *          docUrl: ?string, pdfUrl: ?string}>} results
   * @param {string} actionLabel  e.g. "Generate Selected CVs"
   */
  writeRunSummary(results, actionLabel) {
    const sheet = this.getOrCreateSummarySheet();
    sheet.clearContents();

    this._writeHeaderRow_(sheet, this.SUMMARY_HEADERS);

    const now = new Date();
    const rows = (results || []).map((r) => [
      now,
      actionLabel,
      r.employeeName,
      r.success ? 'SUCCESS' : 'FAILED',
      r.success ? '' : (r.error || ''),
      r.success ? (r.docUrl || '') : '',
      r.success ? (r.pdfUrl || '') : '',
    ]);

    if (rows.length > 0) {
      sheet.getRange(2, 1, rows.length, this.SUMMARY_HEADERS.length).setValues(rows);
    }

    // Color-code status column: green for SUCCESS, red for FAILED.
    if (rows.length > 0) {
      const statusRange = sheet.getRange(2, 4, rows.length, 1);
      const colors = results.map((r) => [r.success ? '#C6EFCE' : '#FFC7CE']);
      statusRange.setBackgrounds(colors);
    }

    sheet.autoResizeColumns(1, this.SUMMARY_HEADERS.length);
  },

  // ── Private helpers ───────────────────────────────────────────────────────

  _getOrCreateSheet_(name, headers) {
    let sheet = this._ss_().getSheetByName(name);
    if (!sheet) {
      sheet = this._ss_().insertSheet(name);
      this._writeHeaderRow_(sheet, headers);
    }
    return sheet;
  },

  _writeHeaderRow_(sheet, headers) {
    const range = sheet.getRange(1, 1, 1, headers.length);
    range.setValues([headers]);
    range.setFontWeight('bold');
    range.setBackground('#1B3A6B');
    range.setFontColor('#FFFFFF');
    sheet.setFrozenRows(1);
  },
};
