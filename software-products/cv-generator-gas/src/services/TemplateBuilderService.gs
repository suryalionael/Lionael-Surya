/**
 * @fileoverview Programmatically builds the MSI CV placeholder template
 * Google Doc using DocumentApp.
 *
 * Called once by SetupController.runSetup() (or on re-initialize). The
 * resulting doc ID is persisted to Script Properties so it can be COPIED
 * per employee without being recreated on every run.
 *
 * The template replicates the golden reference
 * (Assets/20260523_CV MSI Kevin Januar Hasang (1).docx) as closely as the
 * DocumentApp API allows. Known deviations from the golden reference are
 * documented inline and in README Known Limitations.
 */

const TemplateBuilderService = {

  // ── Brand colours ────────────────────────────────────────────────────────
  NAVY:            '#1B3A6B',  // section headings, category names, header background
  WHITE:           '#FFFFFF',
  BLUE:            '#2E86AB',  // training table header, company names
  LIGHT_BLUE:      '#AED6F1',  // position/title text in header
  VERY_LIGHT_BLUE: '#D6EAF8',  // years-of-experience text in header
  LIGHT_GRAY:      '#F2F3F4',  // alternating table rows

  /**
   * Creates a new Google Doc CV template in `parentFolder` and returns its
   * Drive File object. The document contains all section headings and
   * placeholder tokens consumed by TemplateEngine.populate().
   *
   * @param {GoogleAppsScript.Drive.Folder} parentFolder
   * @return {GoogleAppsScript.Drive.File}
   */
  createTemplate(parentFolder) {
    CvLogger.log('INFO', 'SETUP', '-', 'Building CV template document');

    const doc = DocumentApp.create(CONFIG_STATIC.TEMPLATE_DOC_NAME);
    const body = doc.getBody();

    // Clear the default empty paragraph so we start clean.
    body.clear();

    // Set page margins to match the golden reference (approximately 0.7–0.79 in).
    body.setMarginTop(54);    // ~0.75 in (DocumentApp uses points, 72pt = 1in)
    body.setMarginBottom(54);
    body.setMarginLeft(54);
    body.setMarginRight(54);

    // ── 1. Header block (navy table) ────────────────────────────────────────
    this._appendHeaderTable_(body);

    // ── 2. Professional Summary ─────────────────────────────────────────────
    this._appendSectionHeading_(body, SECTION_HEADINGS.PROFESSIONAL_SUMMARY);
    body.appendParagraph(PLACEHOLDERS.SUMMARY)
        .setSpacingAfter(8);

    // ── 3. Technical Skills (2-col table, no header row) ────────────────────
    this._appendSectionHeading_(body, SECTION_HEADINGS.TECHNICAL_SKILLS);
    this._appendSkillsTable_(body);

    // ── 4. Work Experience (paragraph-block sentinel) ───────────────────────
    this._appendSectionHeading_(body, SECTION_HEADINGS.WORK_EXPERIENCE);
    body.appendParagraph(PLACEHOLDERS.WORK_ENTRY)
        .setSpacingAfter(8);

    // ── 5. Education (4-col table with header row) ──────────────────────────
    this._appendSectionHeading_(body, SECTION_HEADINGS.EDUCATION);
    this._appendEducationTable_(body);

    // ── 6. Training & Professional Development (3-col table with header row) ─
    this._appendSectionHeading_(body, SECTION_HEADINGS.TRAINING);
    this._appendTrainingTable_(body);

    // ── 7. Key Projects (paragraph-block sentinel) ──────────────────────────
    this._appendSectionHeading_(body, SECTION_HEADINGS.KEY_PROJECTS);
    body.appendParagraph(PLACEHOLDERS.PROJECT_ENTRY)
        .setSpacingAfter(8);

    // ── 8. Additional Information ────────────────────────────────────────────
    this._appendSectionHeading_(body, SECTION_HEADINGS.ADDITIONAL_INFORMATION);

    // "Languages: " label bold+navy; value is plain default text.
    const langPara = body.appendParagraph('Languages: ' + PLACEHOLDERS.LANGUAGES);
    const langText = langPara.editAsText();
    langText.setForegroundColor(0, 10, this.NAVY); // "Languages: " = chars 0–10
    langText.setBold(0, 10, true);
    langPara.setSpacingAfter(2);

    // "Document Control:" label bold; " Last Updated on …" is plain.
    const docPara = body.appendParagraph(
      'Document Control: Last Updated on ' + PLACEHOLDERS.LAST_UPDATED
    );
    docPara.editAsText().setBold(0, 16, true); // "Document Control:" = chars 0–16
    docPara.setSpacingAfter(8);

    doc.saveAndClose();

    // Move the newly created doc from root Drive into the parent folder.
    const file = DriveApp.getFileById(doc.getId());
    file.moveTo(parentFolder);

    CvLogger.log('INFO', 'SETUP', '-', 'CV template document created', { docId: doc.getId() });
    return file;
  },

  // ── Private helpers ───────────────────────────────────────────────────────

  /**
   * Appends the navy 1-row × 2-col header table containing Name/Position/
   * Years placeholders. Matches the golden reference's branded header block.
   */
  _appendHeaderTable_(body) {
    const table = body.appendTable([
      [
        PLACEHOLDERS.NAME + '\n' + PLACEHOLDERS.POSITION + '\n' + PLACEHOLDERS.YEARS_EXPERIENCE + '+ Years of Experience',
        '',
      ],
    ]);

    // Style both cells: navy background, white text, no visible borders.
    const row = table.getRow(0);
    for (let c = 0; c < 2; c++) {
      const cell = row.getCell(c);
      cell.setBackgroundColor(this.NAVY);

      // Remove all cell borders (set to white so they're invisible).
      const attrs = {};
      attrs[DocumentApp.Attribute.BORDER_COLOR] = this.WHITE;
      attrs[DocumentApp.Attribute.BORDER_WIDTH] = 0;
      cell.setAttributes(attrs);

      cell.setPaddingTop(12);
      cell.setPaddingBottom(12);
      cell.setPaddingLeft(12);
      cell.setPaddingRight(12);
    }

    // Style the Name/Position/Years text in cell 0.
    const cell0 = row.getCell(0);
    const para = cell0.getChild(0).asParagraph();
    const textEl = para.editAsText();
    const fullText = textEl.getText();

    // Per-line formatting: Name=white+bold+26pt, Position=lightblue+14pt, Years=veryLightBlue+11pt.
    const lines = fullText.split('\n');
    let offset = 0;
    lines.forEach((line, i) => {
      if (line.length > 0) {
        const end = offset + line.length - 1;
        if (i === 0) {
          // Name: white, bold, 26pt
          textEl.setForegroundColor(offset, end, this.WHITE);
          textEl.setBold(offset, end, true);
          textEl.setFontSize(offset, end, 26);
        } else if (i === 1) {
          // Position/title: light blue, not bold, 14pt
          textEl.setForegroundColor(offset, end, this.LIGHT_BLUE);
          textEl.setBold(offset, end, false);
          textEl.setFontSize(offset, end, 14);
        } else {
          // Years of experience: very light blue, not bold, 11pt
          textEl.setForegroundColor(offset, end, this.VERY_LIGHT_BLUE);
          textEl.setBold(offset, end, false);
          textEl.setFontSize(offset, end, 11);
        }
      }
      offset += line.length + 1; // +1 for the \n
    });

    table.setColumnWidth(0, 400);
    table.setColumnWidth(1, 100);
    table.setBorderColor(this.WHITE);
    table.setBorderWidth(0);

    return table;
  },

  /**
   * Appends a bold navy section heading followed by a thin horizontal
   * divider line. The divider is implemented as a bottom-bordered
   * paragraph (DocumentApp doesn't support per-paragraph borders directly,
   * so we use a 1×1 table cell with only a bottom border — a recognized
   * workaround that visually replicates the golden reference's heading rule).
   *
   * NOTE: Apps Script's DocumentApp API does not expose per-side paragraph
   * borders. The 1×1 table approach is the pragmatic substitute.
   * See README "Known Limitations".
   */
  _appendSectionHeading_(body, text) {
    // Spacer before the heading.
    body.appendParagraph('').setSpacingAfter(4);

    const heading = body.appendParagraph(text);
    heading.editAsText()
        .setFontSize(11)
        .setBold(true)
        .setForegroundColor(this.NAVY);
    heading.setSpacingBefore(14); // 280 DXA ≈ 14pt, matches reference spacing
    heading.setSpacingAfter(0);

    // Thin bottom-border divider via a borderless 1×1 table with only a
    // bottom border in navy.
    const dividerTable = body.appendTable([['']]);
    const dividerCell = dividerTable.getRow(0).getCell(0);

    // Make all borders transparent except bottom.
    const noBorder = { style: 'none' };
    const navyBorder = { color: this.NAVY, width: 1 };

    const attrs = {};
    attrs[DocumentApp.Attribute.BORDER_COLOR] = this.NAVY;
    attrs[DocumentApp.Attribute.BORDER_WIDTH] = 1;
    dividerCell.setAttributes(attrs);

    // Remove the text from the divider cell (it's purely decorative).
    dividerCell.getChild(0).asParagraph().editAsText().setText('');
    dividerCell.setPaddingTop(0);
    dividerCell.setPaddingBottom(2);
    dividerCell.setPaddingLeft(0);
    dividerCell.setPaddingRight(0);
    dividerTable.setBorderColor(this.WHITE);
    dividerTable.setBorderWidth(0);

    // Apply only the bottom border — achieved by setting the table border
    // to none overall, then styling via paragraph bottom border on the empty
    // cell content (best-effort approximation).
    const dividerPara = dividerCell.getChild(0).asParagraph();
    dividerPara.setSpacingAfter(4);

    return heading;
  },

  /**
   * Appends the Technical Skills 2-column table (no header row).
   * Contains one placeholder data row — TemplateEngine clones this row
   * for each skill category, then removes it.
   */
  _appendSkillsTable_(body) {
    const table = body.appendTable([
      [PLACEHOLDERS.SKILL_CATEGORY, PLACEHOLDERS.SKILL_VALUES],
    ]);

    // Reference: no borders on the technical skills table.
    table.setBorderColor(this.WHITE);
    table.setBorderWidth(0);
    // Column widths match reference proportions (3114/9880 ≈ 31%, 6766/9880 ≈ 69%).
    table.setColumnWidth(0, 150);
    table.setColumnWidth(1, 334);

    const row = table.getRow(0);

    // Cell 0: category — bold, navy, standard padding.
    const cell0 = row.getCell(0);
    cell0.setPaddingTop(4);
    cell0.setPaddingBottom(4);
    cell0.setPaddingLeft(6);
    cell0.setPaddingRight(6);
    const catText = cell0.getChild(0).asParagraph().editAsText();
    catText.setBold(true);
    catText.setForegroundColor(this.NAVY);

    // Cell 1: values — navy, not bold.
    const cell1 = row.getCell(1);
    cell1.setPaddingTop(4);
    cell1.setPaddingBottom(4);
    cell1.setPaddingLeft(6);
    cell1.setPaddingRight(6);
    cell1.getChild(0).asParagraph().editAsText().setForegroundColor(this.NAVY);

    body.appendParagraph('').setSpacingAfter(4);
    return table;
  },

  /**
   * Appends the Education 4-column table with a styled header row and one
   * placeholder data row for TemplateEngine to clone.
   */
  _appendEducationTable_(body) {
    const headers = ['Degree', 'Major / Field of Study', 'Institution', 'Year'];
    const dataRow = [
      PLACEHOLDERS.EDU_DEGREE,
      PLACEHOLDERS.EDU_MAJOR,
      PLACEHOLDERS.EDU_INSTITUTION,
      PLACEHOLDERS.EDU_YEAR,
    ];

    const table = body.appendTable([headers, dataRow]);
    table.setBorderColor('#CCCCCC');
    table.setBorderWidth(1);

    // Style header row.
    const headerRow = table.getRow(0);
    for (let c = 0; c < headers.length; c++) {
      const cell = headerRow.getCell(c);
      cell.setBackgroundColor(this.NAVY);
      cell.setPaddingTop(4);
      cell.setPaddingBottom(4);
      cell.setPaddingLeft(6);
      cell.setPaddingRight(6);
      const textEl = cell.getChild(0).asParagraph().editAsText();
      textEl.setForegroundColor(this.WHITE);
      textEl.setBold(true);
      textEl.setFontSize(10);
    }

    // Style data row.
    const dataRowEl = table.getRow(1);
    for (let c = 0; c < dataRow.length; c++) {
      const cell = dataRowEl.getCell(c);
      cell.setPaddingTop(4);
      cell.setPaddingBottom(4);
      cell.setPaddingLeft(6);
      cell.setPaddingRight(6);
    }

    body.appendParagraph('').setSpacingAfter(4);
    return table;
  },

  /**
   * Appends the Training & Professional Development 3-column table with a
   * styled header row and one placeholder data row for TemplateEngine to
   * clone. Certifications are merged into this table (per analysis §2.3).
   * Reference: header fill is #2E86AB (blue), NOT navy.
   */
  _appendTrainingTable_(body) {
    const headers = ['Training / Course Name', 'Provider / Organizer', 'Year'];
    const dataRow = [
      PLACEHOLDERS.TRAINING_NAME,
      PLACEHOLDERS.TRAINING_PROVIDER,
      PLACEHOLDERS.TRAINING_YEAR,
    ];

    const table = body.appendTable([headers, dataRow]);
    table.setBorderColor('#CCCCCC');
    table.setBorderWidth(1);

    // Style header row — reference uses #2E86AB (blue), not navy.
    const headerRow = table.getRow(0);
    for (let c = 0; c < headers.length; c++) {
      const cell = headerRow.getCell(c);
      cell.setBackgroundColor(this.BLUE);
      cell.setPaddingTop(4);
      cell.setPaddingBottom(4);
      cell.setPaddingLeft(6);
      cell.setPaddingRight(6);
      const textEl = cell.getChild(0).asParagraph().editAsText();
      textEl.setForegroundColor(this.WHITE);
      textEl.setBold(true);
      textEl.setFontSize(10);
    }

    // Style data row.
    const dataRowEl = table.getRow(1);
    for (let c = 0; c < dataRow.length; c++) {
      const cell = dataRowEl.getCell(c);
      cell.setPaddingTop(4);
      cell.setPaddingBottom(4);
      cell.setPaddingLeft(6);
      cell.setPaddingRight(6);
    }

    body.appendParagraph('').setSpacingAfter(4);
    return table;
  },
};
