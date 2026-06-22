/**
 * @fileoverview CV Builder — recruiter selection interface.
 *
 * Manages the builder zone (columns D–H) inside the existing "CV Control
 * Panel" sheet tab. The recruiter loads one employee's parsed data into
 * this zone, unchecks any items they don't want, types a summary, then
 * triggers generation via CV Generator → CV Builder → Generate CV from Builder.
 *
 * Row layout (fixed):
 *   Row 1     — CV BUILDER header        (D1:H1 merged, navy)
 *   Row 2     — Loaded Employee metadata  (D2 label, E2:H2 merged, light blue)
 *   Rows 3–5  — Summary text area        (D3 label, E3:H5 merged, white/editable)
 *   Row 6     — thin spacer
 *   Rows 7–9  — Selection counters       (read-only, amber)
 *   Row 10    — thin spacer
 *   Row 11+   — Dynamic: PROJECTS / SKILLS / TRAINING sections
 *
 * Column layout (within builder zone):
 *   D (col 4) — Include checkbox
 *   E (col 5) — Project Name / Category / Training Name
 *   F (col 6) — Client / Skill Name / Provider
 *   G (col 7) — Period / Year
 *   H (col 8) — Role
 *
 * The employee list (cols A–B) is never touched by this module.
 */

const CvBuilderRepository = {

  // ── Layout constants ───────────────────────────────────────────────────────

  COL_START:   4,   // D
  COL_INCLUDE: 4,   // D — checkbox column
  COL_NAME:    5,   // E — project name / skill category / training name
  COL_CLIENT:  6,   // F — client / skill / provider
  COL_PERIOD:  7,   // G — period / year
  COL_ROLE:    8,   // H — role

  ROW_HEADER:           1,
  ROW_LOADED_EMPLOYEE:  2,
  ROW_SUMMARY_START:    3,
  ROW_SUMMARY_END:      5,
  ROW_COUNTER_PROJECTS: 7,
  ROW_COUNTER_SKILLS:   8,
  ROW_COUNTER_TRAINING: 9,
  ROW_CONTENT_START:    11,

  MARKER_PROJECTS: '▶ PROJECTS',
  MARKER_SKILLS:   '▶ SKILLS',
  MARKER_TRAINING: '▶ TRAINING',

  COLOR_NAVY:       '#1B3A6B',
  COLOR_METADATA:   '#D6E4F0',
  COLOR_COUNTER:    '#FEF9E7',
  COLOR_COL_HEADER: '#F3F3F3',

  // ── Public API ─────────────────────────────────────────────────────────────

  /**
   * Populates the D:H builder zone with the employee's parsed CV data.
   * All items are pre-checked. Summary text is preserved across loads.
   *
   * @param {string} employeeName
   * @param {Object} cvModel  result of DataAggregationService.buildEmployeeCvModel()
   * @return {{projectCount: number, skillCount: number, trainingCount: number}}
   */
  loadEmployeeData(employeeName, cvModel) {
    const sheet = this._getSheet_();

    // Preserve any summary the recruiter typed from a previous load.
    const savedSummary = String(
      sheet.getRange(this.ROW_SUMMARY_START, this.COL_NAME).getValue()
    );

    // Wipe the entire builder zone — clears content, formatting, and validation.
    // breakApart() is called explicitly because clear() does NOT unmerge cells;
    // without it, setValues() on rows that were previously merged section headers
    // throws "You can't change part of a merge" on second and subsequent loads.
    const clearRows = Math.max(sheet.getLastRow() + 10, 300);
    const builderZone = sheet.getRange(1, this.COL_START, clearRows, 5);
    builderZone.clear();
    builderZone.breakApart();

    // Write fixed structural rows 1–10 (header, metadata, counters).
    this._writeMetadataBlock_(sheet, employeeName, savedSummary);

    // Flatten and write dynamic sections starting at row 11.
    const projects = cvModel.projects              || [];
    const skills   = this._flattenSkills_(cvModel.technicalSkills || []);
    const training = cvModel.training              || [];

    let row = this.ROW_CONTENT_START;
    row = this._writeSection_(sheet, row, this.MARKER_PROJECTS,
      ['Include', 'Project Name', 'Client', 'Period', 'Role'],
      projects.map((p) => [true, p.name || '', p.client || '', p.period || '', p.role || ''])
    );
    row = this._writeSection_(sheet, row, this.MARKER_SKILLS,
      ['Include', 'Category', 'Skill', '', ''],
      skills.map((s) => [true, s.category, s.skill, '', ''])
    );
    row = this._writeSection_(sheet, row, this.MARKER_TRAINING,
      ['Include', 'Training Name', 'Provider', 'Year', ''],
      training.map((t) => [true, t.name || '', t.provider || '', t.year || '', ''])
    );

    // Write initial counter values (all items pre-selected on first load).
    this._writeCounters_(sheet, projects.length, skills.length, training.length);

    // Set builder column widths.
    this._setColumnWidths_(sheet);

    return {
      projectCount:  projects.length,
      skillCount:    skills.length,
      trainingCount: training.length,
    };
  },

  /**
   * Reads the current state of the builder zone and returns a selectionOverride
   * object for CvGenerationService.generateCvForEmployee(), or null if no
   * employee has been loaded yet.
   *
   * @return {{employeeName: string, summary: string,
   *           projectNames: string[], selectedSkills: string[],
   *           trainingNames: string[]} | null}
   */
  getSelections() {
    const sheet = this._getSheet_();

    const employeeName = String(
      sheet.getRange(this.ROW_LOADED_EMPLOYEE, this.COL_NAME).getValue()
    ).trim();
    if (!employeeName) return null;

    const summary = String(
      sheet.getRange(this.ROW_SUMMARY_START, this.COL_NAME).getValue()
    ).trim();

    const lastRow = sheet.getLastRow();
    if (lastRow < this.ROW_CONTENT_START) {
      return { employeeName, summary, projectNames: [], selectedSkills: [], trainingNames: [] };
    }

    const numRows = lastRow - this.ROW_CONTENT_START + 1;
    const data = sheet.getRange(
      this.ROW_CONTENT_START, this.COL_INCLUDE, numRows, 5
    ).getValues();

    const projectNames   = [];
    const selectedSkills = [];
    const trainingNames  = [];
    let currentSection   = null;

    for (let i = 0; i < data.length; i++) {
      const d0 = data[i][0]; // col D: checkbox boolean / section marker / col header / spacer

      // Detect section transitions first (markers are strings).
      if (d0 === this.MARKER_PROJECTS) { currentSection = 'PROJECTS'; continue; }
      if (d0 === this.MARKER_SKILLS)   { currentSection = 'SKILLS';   continue; }
      if (d0 === this.MARKER_TRAINING) { currentSection = 'TRAINING'; continue; }
      // Skip column-header rows, spacer rows, '(none found)' rows — all non-boolean.
      if (typeof d0 !== 'boolean') continue;
      // Skip unchecked rows.
      if (!d0) continue;

      const colE = String(data[i][1]).trim(); // E: project name / category
      const colF = String(data[i][2]).trim(); // F: client / skill name / provider

      if      (currentSection === 'PROJECTS')  { if (colE) projectNames.push(colE); }
      else if (currentSection === 'SKILLS')    { if (colF) selectedSkills.push(colF); }
      else if (currentSection === 'TRAINING')  { if (colE) trainingNames.push(colE); }
    }

    return { employeeName, summary, projectNames, selectedSkills, trainingNames };
  },

  /**
   * Recounts currently checked items and updates the amber counter block
   * (rows 7–9). Called by generateCvFromBuilder() before generation so the
   * recruiter can see the final tally before the result dialog appears.
   *
   * @param {{projectNames: string[], selectedSkills: string[],
   *          trainingNames: string[]}} selections  result of getSelections()
   */
  updateCounters(selections) {
    if (!selections) return;
    this._writeCounters_(
      this._getSheet_(),
      selections.projectNames.length,
      selections.selectedSkills.length,
      selections.trainingNames.length
    );
  },

  // ── Private helpers ────────────────────────────────────────────────────────

  /** Returns the "CV Control Panel" sheet from the active spreadsheet. */
  _getSheet_() {
    return SpreadsheetApp.getActiveSpreadsheet()
      .getSheetByName(CONFIG_STATIC.CONTROL_PANEL_SHEET_NAME);
  },

  /**
   * Writes the fixed structural rows 1–10:
   *   Row 1   — CV BUILDER header
   *   Row 2   — Loaded Employee metadata
   *   Rows 3–5 — Summary textarea
   *   Rows 7–9 — Counter block labels (values written by _writeCounters_)
   * Rows 6 and 10 are left empty as visual spacers.
   */
  _writeMetadataBlock_(sheet, employeeName, savedSummary) {
    const cs = this.COL_START; // 4 = col D
    const cw = 5;              // 5 columns: D:H

    // Row 1 — "CV BUILDER" header (merged D1:H1, navy)
    sheet.getRange(this.ROW_HEADER, cs, 1, cw)
         .merge()
         .setValue('CV BUILDER')
         .setBackground(this.COLOR_NAVY)
         .setFontColor('#FFFFFF')
         .setFontWeight('bold')
         .setFontSize(13)
         .setHorizontalAlignment('center')
         .setVerticalAlignment('middle');

    // Row 2 — Loaded Employee (metadata light blue; label D2, merged name E2:H2)
    sheet.getRange(this.ROW_LOADED_EMPLOYEE, cs, 1, cw)
         .setBackground(this.COLOR_METADATA);
    sheet.getRange(this.ROW_LOADED_EMPLOYEE, cs)
         .setValue('Loaded Employee:')
         .setFontWeight('bold');
    sheet.getRange(this.ROW_LOADED_EMPLOYEE, cs + 1, 1, cw - 1)
         .merge()
         .setValue(employeeName)
         .setFontColor('#555555')
         .setFontStyle('italic');

    // Rows 3–5 — Summary textarea
    // D3:D5 = label column, light blue
    sheet.getRange(this.ROW_SUMMARY_START, cs, 3, 1)
         .setBackground(this.COLOR_METADATA);
    sheet.getRange(this.ROW_SUMMARY_START, cs)
         .setValue('Summary:')
         .setFontWeight('bold')
         .setVerticalAlignment('top');
    // E3:H5 = editable textarea (merged, white, word-wrap)
    sheet.getRange(this.ROW_SUMMARY_START, cs + 1, 3, cw - 1)
         .merge()
         .setValue(savedSummary)
         .setWrap(true)
         .setVerticalAlignment('top')
         .setBackground('#FFFFFF');

    // Rows 7–9 — Counter block (amber; labels in D, values written by _writeCounters_)
    const counterLabels = [
      'Projects Selected:',
      'Skills Selected:',
      'Training Selected:',
    ];
    counterLabels.forEach((label, i) => {
      const r = this.ROW_COUNTER_PROJECTS + i;
      sheet.getRange(r, cs, 1, cw).setBackground(this.COLOR_COUNTER);
      sheet.getRange(r, cs)
           .setValue(label)
           .setFontWeight('bold');
    });
  },

  /**
   * Writes one content section: section header + column-label row + data rows
   * + trailing spacer row. Returns the next available row index.
   *
   * @param {GoogleAppsScript.Spreadsheet.Sheet} sheet
   * @param {number} startRow
   * @param {string} marker     section title (also the scan target in getSelections)
   * @param {string[]} colHeaders  5-element array of column header labels
   * @param {Array[]} dataRows     each inner array: [include(bool), c1, c2, c3, c4]
   * @return {number} first row after this section's trailing spacer
   */
  _writeSection_(sheet, startRow, marker, colHeaders, dataRows) {
    const cs = this.COL_START;
    const cw = 5;
    let row = startRow;

    // Section header — merged D:H, navy
    sheet.getRange(row, cs, 1, cw)
         .merge()
         .setValue(marker)
         .setBackground(this.COLOR_NAVY)
         .setFontColor('#FFFFFF')
         .setFontWeight('bold');
    row++;

    // Column header row — light gray
    sheet.getRange(row, cs, 1, cw)
         .setValues([colHeaders])
         .setBackground(this.COLOR_COL_HEADER)
         .setFontWeight('bold');
    row++;

    if (dataRows.length > 0) {
      // Apply checkbox validation to col D before setting values so that
      // true/false values render as checked/unchecked checkboxes.
      const checkboxRule = SpreadsheetApp.newDataValidation()
        .requireCheckbox()
        .build();
      sheet.getRange(row, this.COL_INCLUDE, dataRows.length, 1)
           .setDataValidation(checkboxRule);
      // Write all column values (col D = true = pre-checked).
      sheet.getRange(row, cs, dataRows.length, cw).setValues(dataRows);
      row += dataRows.length;
    } else {
      sheet.getRange(row, cs)
           .setValue('(none found)')
           .setFontStyle('italic')
           .setFontColor('#999999');
      row++;
    }

    row++; // trailing spacer row (empty, default height)
    return row;
  },

  /**
   * Writes numeric counter values to the amber block (E7, E8, E9).
   * Called by loadEmployeeData() with total counts and by
   * updateCounters() with selected counts.
   */
  _writeCounters_(sheet, projectCount, skillCount, trainingCount) {
    sheet.getRange(this.ROW_COUNTER_PROJECTS, this.COL_NAME).setValue(projectCount);
    sheet.getRange(this.ROW_COUNTER_SKILLS,   this.COL_NAME).setValue(skillCount);
    sheet.getRange(this.ROW_COUNTER_TRAINING, this.COL_NAME).setValue(trainingCount);
  },

  /**
   * Flattens [{category, skills: string[]}] into [{category, skill}] pairs
   * so each skill gets its own selectable row in the builder.
   *
   * @param {Array<{category: string, skills: string[]}>} technicalSkills
   * @return {Array<{category: string, skill: string}>}
   */
  _flattenSkills_(technicalSkills) {
    const flat = [];
    (technicalSkills || []).forEach((group) => {
      (group.values || []).forEach((skill) => {
        flat.push({ category: group.category || '', skill });
      });
    });
    return flat;
  },

  /** Sets builder column widths D:H. */
  _setColumnWidths_(sheet) {
    sheet.setColumnWidth(this.COL_INCLUDE, 55);  // D — Include
    sheet.setColumnWidth(this.COL_NAME,    210); // E — Name / Category
    sheet.setColumnWidth(this.COL_CLIENT,  150); // F — Client / Skill / Provider
    sheet.setColumnWidth(this.COL_PERIOD,  100); // G — Period / Year
    sheet.setColumnWidth(this.COL_ROLE,    140); // H — Role
  },
};
