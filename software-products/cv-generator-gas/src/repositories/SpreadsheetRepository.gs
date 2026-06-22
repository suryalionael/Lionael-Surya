/**
 * @fileoverview Repository for reading the Project Experience spreadsheet.
 *
 * The spreadsheet is a Google Form Responses sheet ("Form Responses 1",
 * gid=1789711707) in WIDE format: each row is one employee's full
 * submission, and the header row contains the SAME column names repeated
 * for each project block (~11×) and training/certification block (~13×).
 *
 * This file implements the repeating column-group detection algorithm
 * described in CV_FORMAT_ANALYSIS.md §3.2 so that:
 *   - No column indexes are hardcoded.
 *   - The mapping is by header NAME within each detected group.
 *   - Column order within a group and number of groups can change without
 *     breaking the parser.
 *
 * All returned data uses the normalized extraction shape consumed by
 * DataAggregationService.
 */

const SpreadsheetRepository = {

  // ── Column-name anchors for group boundary detection ──────────────────────
  PROJECT_GROUP_ANCHOR:  /^Nama\s+klien$/i,
  TRAINING_GROUP_ANCHOR: /Nama\s+Training/i,
  EMPLOYEE_NAME_COL:     /^Nama\s+lengkap$/i,

  // ── Field name regexes (matched against header names within each group) ───
  PROJECT_FIELDS: {
    client:          /^Nama\s+klien$/i,
    name:            /^Nama\s+project$/i,
    module:          /^Nama\s+modul/i,
    period:          /^Periode\s+Pengerjaan$/i,
    role:            /^Peran\s+Kamu$/i,
    tools:           /^Tech\s+Stack/i,
    responsibility:  /^Tanggung\s+Jawab\s+Utama/i,
    achievement:     /^Pencapaian\s+dalam/i,
    continueFlag:    /^Lanjut\s+ke\s+project/i,
  },

  TRAINING_FIELDS: {
    name:            /Nama\s+Training\s*\/\s*Sertifikasi/i,
    year:            /^Tahun\s+Training/i,
    outputCompetency:/^Output\s+&\s+Kompetensi/i,
    fundingStatus:   /^Status\s+Pembiayaan/i,
    continueFlag:    /^Lanjut\s+ke\s+training/i,
  },

  // ── Cached parsed data (cleared between executions automatically since
  //    Apps Script is stateless; this only caches within one execution) ──────
  _cache_: null,

  /**
   * Returns a map of normalized employee name → { projects[], trainings[] }
   * for ALL employees in the spreadsheet. Result is cached within the
   * execution to avoid repeated Sheet reads.
   *
   * @return {Object.<string, {projects: Array, trainings: Array}>}
   */
  getAllEmployeeProjectData() {
    if (this._cache_) return this._cache_;

    const ss = SpreadsheetApp.openById(CONFIG_STATIC.PROJECT_SPREADSHEET_ID);
    const sheet = this._getResponsesSheet_(ss);
    ErrorHandler.assert(sheet, 'Project spreadsheet "Form Responses 1" sheet not found.');

    const allValues = sheet.getDataRange().getValues();
    if (allValues.length < 2) {
      CvLogger.log('WARN', 'SPREADSHEET', '-', 'Project spreadsheet appears empty (< 2 rows)');
      this._cache_ = {};
      return this._cache_;
    }

    const headers = allValues[0].map((h) => String(h).trim());
    const dataRows = allValues.slice(1);

    const { employeeNameColIdx, projectGroups, trainingGroups } =
      this._detectColumnGroups_(headers);

    CvLogger.log('INFO', 'SPREADSHEET', '-', 'Column groups detected', {
      projectGroups: projectGroups.length,
      trainingGroups: trainingGroups.length,
    });

    const result = {};

    dataRows.forEach((row) => {
      const rawName = String(row[employeeNameColIdx] || '').trim();
      if (!rawName) return;
      const key = TextUtils.normalizeName(rawName);

      if (!result[key]) {
        result[key] = { projects: [], trainings: [], rawName };
      }

      // Extract project entries from this row.
      projectGroups.forEach((group) => {
        const project = this._extractProjectFromGroup_(row, group);
        if (project) result[key].projects.push(project);
      });

      // Extract training/certification entries from this row.
      trainingGroups.forEach((group) => {
        const training = this._extractTrainingFromGroup_(row, group);
        if (training) result[key].trainings.push(training);
      });
    });

    CvLogger.log('INFO', 'SPREADSHEET', '-', 'Spreadsheet parsed', {
      employeeCount: Object.keys(result).length,
    });

    this._cache_ = result;
    return result;
  },

  /**
   * Convenience accessor: returns the parsed data for one employee.
   *
   * @param {string} employeeName
   * @return {{projects: Array, trainings: Array}|null}
   */
  getEmployeeData(employeeName) {
    const all = this.getAllEmployeeProjectData();
    const key = TextUtils.normalizeName(employeeName);
    return all[key] || null;
  },

  // ── Private: column-group detection ──────────────────────────────────────

  /**
   * Scans the header row to build:
   *   - employeeNameColIdx: index of "Nama lengkap"
   *   - projectGroups: array of fieldMaps, one per detected project block
   *   - trainingGroups: array of fieldMaps, one per detected training block
   *
   * Each fieldMap maps a logical field name (e.g. 'name', 'role') to a
   * column index, derived by matching header names within the group against
   * the PROJECT_FIELDS / TRAINING_FIELDS regexes.
   *
   * @param {string[]} headers
   * @return {{employeeNameColIdx: number, projectGroups: Array, trainingGroups: Array}}
   */
  _detectColumnGroups_(headers) {
    let employeeNameColIdx = 0;

    // Find the employee name column first.
    for (let i = 0; i < headers.length; i++) {
      if (this.EMPLOYEE_NAME_COL.test(headers[i])) {
        employeeNameColIdx = i;
        break;
      }
    }

    // Find start indices of all project groups (each occurrence of the anchor).
    const projectGroupStarts = [];
    const trainingGroupStarts = [];

    for (let i = 0; i < headers.length; i++) {
      if (this.PROJECT_GROUP_ANCHOR.test(headers[i])) {
        projectGroupStarts.push(i);
      } else if (this.TRAINING_GROUP_ANCHOR.test(headers[i])) {
        trainingGroupStarts.push(i);
      }
    }

    // Build fieldMaps for each project group.
    const projectGroups = projectGroupStarts.map((start, gi) => {
      const end = gi + 1 < projectGroupStarts.length
        ? projectGroupStarts[gi + 1]
        : (trainingGroupStarts[0] || headers.length);
      return this._buildFieldMap_(headers, start, end, this.PROJECT_FIELDS);
    });

    // Build fieldMaps for each training group.
    const trainingGroups = trainingGroupStarts.map((start, gi) => {
      const end = gi + 1 < trainingGroupStarts.length
        ? trainingGroupStarts[gi + 1]
        : headers.length;
      return this._buildFieldMap_(headers, start, end, this.TRAINING_FIELDS);
    });

    return { employeeNameColIdx, projectGroups, trainingGroups };
  },

  /**
   * Builds a { logicalField: colIndex } map for headers[start..end).
   *
   * @param {string[]} headers
   * @param {number} start  inclusive
   * @param {number} end    exclusive
   * @param {Object} fieldDefs  map of logicalField → RegExp
   * @return {Object.<string, number>}
   */
  _buildFieldMap_(headers, start, end, fieldDefs) {
    const map = {};
    for (let i = start; i < end; i++) {
      const h = headers[i];
      Object.keys(fieldDefs).forEach((field) => {
        if (!map[field] && fieldDefs[field].test(h)) {
          map[field] = i;
        }
      });
    }
    return map;
  },

  // ── Private: row extraction ───────────────────────────────────────────────

  /**
   * Extracts one project record from a data row using a pre-built fieldMap.
   * Returns null if the project name cell is empty (group not filled).
   *
   * @param {Array} row
   * @param {Object} fieldMap
   * @return {Object|null}
   */
  _extractProjectFromGroup_(row, fieldMap) {
    const get = (field) => String(row[fieldMap[field]] || '').trim();

    const projectName = get('name');
    if (!projectName) return null;

    const periodStr = get('period');
    const parsed = DateUtils.parsePeriodString(periodStr);

    return {
      name: projectName,
      client: get('client'),
      module: get('module'),
      period: periodStr,
      startDate: parsed.startDate,
      endDate: parsed.endDate,
      isOngoing: parsed.isOngoing,
      role: get('role'),
      tools: get('tools'),
      responsibility: TextUtils.joinNonEmpty([get('responsibility'), get('achievement')], ' '),
      achievement: get('achievement'),
    };
  },

  /**
   * Extracts one training/certification record from a data row.
   * Returns null if the training name cell is empty.
   *
   * @param {Array} row
   * @param {Object} fieldMap
   * @return {Object|null}
   */
  _extractTrainingFromGroup_(row, fieldMap) {
    const get = (field) => String(row[fieldMap[field]] || '').trim();

    const trainingName = get('name');
    if (!trainingName) return null;

    return {
      name: trainingName,
      year: get('year'),
      outputCompetency: get('outputCompetency'),
      fundingStatus: get('fundingStatus'),
    };
  },

  // ── Private: sheet locator ─────────────────────────────────────────────────

  /**
   * Finds the "Form Responses 1" sheet in the spreadsheet.
   * Tries GID match first, then name match, then falls back to sheet[0].
   *
   * @param {GoogleAppsScript.Spreadsheet.Spreadsheet} ss
   * @return {GoogleAppsScript.Spreadsheet.Sheet|null}
   */
  _getResponsesSheet_(ss) {
    const targetGid = CONFIG_STATIC.PROJECT_SHEET_GID;
    const sheets = ss.getSheets();

    // GID match (most reliable — the numeric GID is stable even if sheet is renamed).
    for (let i = 0; i < sheets.length; i++) {
      if (sheets[i].getSheetId() === targetGid) return sheets[i];
    }

    // Name match fallback.
    const byName = ss.getSheetByName('Form Responses 1');
    if (byName) return byName;

    // Last resort: first sheet.
    return sheets.length > 0 ? sheets[0] : null;
  },
};
