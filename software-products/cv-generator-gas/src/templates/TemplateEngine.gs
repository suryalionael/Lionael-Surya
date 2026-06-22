/**
 * @fileoverview Template population engine for the MSI CV Generator.
 *
 * TemplateEngine.populate(doc, cvModel) transforms a copy of the placeholder
 * template into a fully-populated CV by applying four operations in order:
 *
 *   1. Simple placeholder substitution  (Body.replaceText — traverses all
 *      nested elements including tables)
 *   2. Table-row cloning                (Technical Skills / Education / Training)
 *   3. Paragraph-block insertion        (Work Experience / Key Projects)
 *   4. Section omission                 (removes entire heading + content when
 *      the corresponding data array is empty)
 *
 * The engine never uses literal "•" bullet characters — Work Experience
 * responsibility lines are inserted as native Google Docs list items
 * (GlyphType.BULLET) via Body.insertListItem().
 *
 * See implementation plan §3 for the algorithm details.
 */

const TemplateEngine = {

  /**
   * Populates `doc` in-place with data from `cvModel`, then saves and closes
   * the document.
   *
   * @param {GoogleAppsScript.Document.Document} doc  an open, editable copy
   *   of the template (produced by DriveApp.getFileById(...).makeCopy(...))
   * @param {Object} cvModel  output of DataAggregationService.buildEmployeeCvModel()
   */
  populate(doc, cvModel) {
    const body = doc.getBody();

    // ── Step 1: Simple placeholder substitution ──────────────────────────────
    // replaceText() on Body traverses ALL child elements including tables,
    // so this handles the header block ({{NAME}}, {{POSITION}}, etc.) as well
    // as any section sentinels that haven't been replaced yet.
    this._substituteSimplePlaceholders_(body, cvModel);

    // ── Step 2: Table-row cloning ─────────────────────────────────────────────
    this._populateSkillsTable_(body, cvModel.technicalSkills);
    this._populateEducationTable_(body, cvModel.education);
    this._populateTrainingTable_(body, cvModel.training);

    // ── Step 3: Paragraph-block insertion (replaces sentinel paragraphs) ──────
    this._populateWorkExperience_(body, cvModel.workExperience);
    this._populateKeyProjects_(body, cvModel.projects);

    // ── Step 4: Section omission (remove empty sections AFTER population) ─────
    this._omitEmptySections_(body, cvModel);

    doc.saveAndClose();
  },

  // ─────────────────────────────────────────────────────────────────────────
  // Step 1 — Simple placeholder substitution
  // ─────────────────────────────────────────────────────────────────────────

  _substituteSimplePlaceholders_(body, cvModel) {
    const re = (token) => token.replace(/[{}]/g, '\\$&'); // escape {{ }}

    body.replaceText(re(PLACEHOLDERS.NAME),     cvModel.name || '');
    body.replaceText(re(PLACEHOLDERS.POSITION), cvModel.position || '');

    const yearsText = cvModel.yearsExperience != null
      ? String(cvModel.yearsExperience) : '';
    body.replaceText(re(PLACEHOLDERS.YEARS_EXPERIENCE), yearsText);

    body.replaceText(re(PLACEHOLDERS.SUMMARY),
      cvModel.summary || '');
    body.replaceText(re(PLACEHOLDERS.LANGUAGES),
      cvModel.languages || '');
    body.replaceText(re(PLACEHOLDERS.ADDITIONAL_INFORMATION),
      cvModel.additionalInformation || '');
    body.replaceText(re(PLACEHOLDERS.LAST_UPDATED),
      cvModel.lastUpdated || DateUtils.formatMonthYear(new Date()));
  },

  // ─────────────────────────────────────────────────────────────────────────
  // Step 2 — Table-row cloning helpers
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Finds the first table in `body` that contains `anchorText` in any cell,
   * and returns { table, templateRowIndex }.
   *
   * @param {GoogleAppsScript.Document.Body} body
   * @param {string} anchorText
   * @return {{table: GoogleAppsScript.Document.Table, templateRowIndex: number}|null}
   */
  _findTableWithPlaceholder_(body, anchorText) {
    const n = body.getNumChildren();
    for (let i = 0; i < n; i++) {
      const child = body.getChild(i);
      if (child.getType() !== DocumentApp.ElementType.TABLE) continue;
      const table = child.asTable();
      for (let r = 0; r < table.getNumRows(); r++) {
        const rowText = table.getRow(r).getText();
        if (rowText.indexOf(anchorText) !== -1) {
          return { table, templateRowIndex: r };
        }
      }
    }
    return null;
  },

  /**
   * Generic table population: clones the template row for each data item,
   * calls `fillFn(newRow, item)` to replace placeholders in the clone, then
   * removes the original template row.
   *
   * @param {GoogleAppsScript.Document.Body} body
   * @param {string} anchorPlaceholder  text that identifies the template row
   * @param {Array} items
   * @param {function(GoogleAppsScript.Document.TableRow, Object)} fillFn
   */
  _populateTable_(body, anchorPlaceholder, items, fillFn) {
    const found = this._findTableWithPlaceholder_(body, anchorPlaceholder);
    if (!found) return; // table may have been removed by section-omission pre-pass

    const { table, templateRowIndex } = found;

    // Clone the template row for each data item, inserting BEFORE the template row
    // so we can delete the template row at a stable index afterwards.
    let insertIndex = templateRowIndex;
    items.forEach((item, index) => {
      // insertIndex equals the template row's current position after each prior insert.
      const newRow = table.getRow(insertIndex).copy();
      table.insertTableRow(insertIndex, newRow);
      fillFn(newRow, item, index);
      insertIndex++;
    });

    // Remove the original (now-shifted) template placeholder row.
    table.removeRow(templateRowIndex + items.length);
  },

  _populateSkillsTable_(body, technicalSkills) {
    // DEBUG LOGGING — remove after diagnosis
    Logger.log('[TEMPLATE] technicalSkills received by _populateSkillsTable_ (' +
      (technicalSkills || []).length + ' groups):');
    Logger.log(JSON.stringify(technicalSkills, null, 2));

    this._populateTable_(body, PLACEHOLDERS.SKILL_CATEGORY, technicalSkills,
      (row, skill) => {
        row.replaceText(
          PLACEHOLDERS.SKILL_CATEGORY.replace(/[{}]/g, '\\$&'),
          skill.category || ''
        );
        // Values prefixed with ': ' to match reference format (': Windows/NT, Linux').
        row.replaceText(
          PLACEHOLDERS.SKILL_VALUES.replace(/[{}]/g, '\\$&'),
          (skill.values || []).length > 0
            ? ': ' + (skill.values || []).join(', ')
            : ''
        );
      }
    );
  },

  _populateEducationTable_(body, education) {
    this._populateTable_(body, PLACEHOLDERS.EDU_DEGREE, education,
      (row, edu) => {
        const re = (t) => t.replace(/[{}]/g, '\\$&');
        row.replaceText(re(PLACEHOLDERS.EDU_DEGREE),      edu.degree || '');
        row.replaceText(re(PLACEHOLDERS.EDU_MAJOR),       edu.major || '');
        row.replaceText(re(PLACEHOLDERS.EDU_INSTITUTION), edu.institution || '');
        row.replaceText(re(PLACEHOLDERS.EDU_YEAR),        edu.year || '');
      }
    );
  },

  _populateTrainingTable_(body, training) {
    this._populateTable_(body, PLACEHOLDERS.TRAINING_NAME, training,
      (row, t, index) => {
        // Alternating row backgrounds: #F2F3F4 (odd rows) / #FFFFFF (even rows).
        const bg = index % 2 === 0 ? '#F2F3F4' : '#FFFFFF';
        for (let c = 0; c < row.getNumCells(); c++) {
          row.getCell(c).setBackgroundColor(bg);
        }
        const re = (tok) => tok.replace(/[{}]/g, '\\$&');
        row.replaceText(re(PLACEHOLDERS.TRAINING_NAME),     t.name || '');
        row.replaceText(re(PLACEHOLDERS.TRAINING_PROVIDER), t.provider || '');
        row.replaceText(re(PLACEHOLDERS.TRAINING_YEAR),     t.year || '');
      }
    );
  },

  // ─────────────────────────────────────────────────────────────────────────
  // Step 3 — Paragraph-block insertion
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Finds the index of the first paragraph in `body` whose text exactly
   * matches `sentinelText`, removes it, and returns the index so the caller
   * can insert content at that position.
   *
   * @param {GoogleAppsScript.Document.Body} body
   * @param {string} sentinelText
   * @return {number}  insertion index, or -1 if sentinel not found
   */
  _removeSentinelAndGetIndex_(body, sentinelText) {
    const n = body.getNumChildren();
    for (let i = 0; i < n; i++) {
      const child = body.getChild(i);
      if (child.getType() === DocumentApp.ElementType.PARAGRAPH) {
        if (child.asParagraph().getText().trim() === sentinelText.trim()) {
          body.removeChild(child);
          return i;
        }
      }
    }
    return -1;
  },

  /**
   * Replaces the {{WORK_ENTRY}} sentinel with fully-formatted Work Experience
   * entries. Each entry renders as:
   *   Position (bold)
   *   Company | Period | Location
   *   • Bullet (native list item)
   *   [blank separator between entries]
   *
   * @param {GoogleAppsScript.Document.Body} body
   * @param {Array} workExperience
   */
  _populateWorkExperience_(body, workExperience) {
    let insertIdx = this._removeSentinelAndGetIndex_(body, PLACEHOLDERS.WORK_ENTRY);
    if (insertIdx === -1) return;

    workExperience.forEach((entry, ei) => {
      // Position line — bold, navy.
      const posPara = body.insertParagraph(insertIdx++, entry.position || '');
      const posText = posPara.editAsText();
      posText.setBold(true);
      posText.setForegroundColor('#1B3A6B');
      posPara.setSpacingBefore(4);
      posPara.setSpacingAfter(2);

      // Company | Period | Location line — rich text: company=bold+blue, rest=italic+gray.
      const compSegs = this._buildTitleSegments_(
        entry.company || '', [entry.period, entry.location].filter(Boolean), '#2E86AB'
      );
      const compLine = compSegs.map(s => s.text).join('');
      const compPara = body.insertParagraph(insertIdx++, compLine);
      if (compSegs.length > 0 && compLine.length > 0) {
        this._applySegmentFormatting_(compPara.editAsText(), compSegs);
      }
      compPara.setSpacingAfter(2);

      // Responsibility bullet lines — black, justified.
      (entry.bullets || []).forEach((bullet) => {
        const li = body.insertListItem(insertIdx++, bullet);
        li.setGlyphType(DocumentApp.GlyphType.BULLET);
        li.setNestingLevel(0);
        li.setSpacingAfter(1);
        li.editAsText().setForegroundColor('#000000');
        li.setAlignment(DocumentApp.HorizontalAlignment.JUSTIFY);
      });

      // Blank separator between entries (not after the last one).
      if (ei < workExperience.length - 1) {
        body.insertParagraph(insertIdx++, '').setSpacingAfter(4);
      }
    });
  },

  /**
   * Replaces the {{PROJECT_ENTRY}} sentinel with fully-formatted Key Project
   * entries. Each entry renders as:
   *   Project Name | Client | Period (bold)
   *   Role:           <value>
   *   Responsibility: <value>
   *   Tools:          <value>
   *   [blank separator between entries]
   *
   * @param {GoogleAppsScript.Document.Body} body
   * @param {Array} projects
   */
  _populateKeyProjects_(body, projects) {
    let insertIdx = this._removeSentinelAndGetIndex_(body, PLACEHOLDERS.PROJECT_ENTRY);
    if (insertIdx === -1) return;

    projects.forEach((project, pi) => {
      // Project name | client | period — rich text: name=bold+navy, rest=italic+gray.
      const titleSegs = this._buildTitleSegments_(
        project.name || '', [project.client, project.period].filter(Boolean), '#1B3A6B'
      );
      const fullTitle = titleSegs.map(s => s.text).join('');
      const titlePara = body.insertParagraph(insertIdx++, fullTitle);
      if (titleSegs.length > 0 && fullTitle.length > 0) {
        this._applySegmentFormatting_(titlePara.editAsText(), titleSegs);
      }
      titlePara.setSpacingBefore(4);
      titlePara.setSpacingAfter(2);

      // Role / Responsibility / Tools lines — tab-aligned, justified.
      if (project.role) {
        body.insertParagraph(insertIdx++, 'Role\t\t\t: ' + project.role)
            .setSpacingAfter(1)
            .setAlignment(DocumentApp.HorizontalAlignment.JUSTIFY);
      }
      if (project.responsibility) {
        body.insertParagraph(insertIdx++, 'Responsibility\t: ' + project.responsibility)
            .setSpacingAfter(1)
            .setAlignment(DocumentApp.HorizontalAlignment.JUSTIFY);
      }
      if (project.tools) {
        body.insertParagraph(insertIdx++, 'Tools\t\t\t: ' + project.tools)
            .setSpacingAfter(1)
            .setAlignment(DocumentApp.HorizontalAlignment.JUSTIFY);
      }

      // Blank separator.
      if (pi < projects.length - 1) {
        body.insertParagraph(insertIdx++, '').setSpacingAfter(4);
      }
    });
  },

  // ─────────────────────────────────────────────────────────────────────────
  // Rich-text segment helpers (used by Work Experience and Key Projects)
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Builds a segment array for a "Name | Part | Part" title line.
   * The name gets `nameColor` + bold; separators and other parts get
   * gray (#5D6D7E) + italic, matching the reference format.
   *
   * @param {string} name
   * @param {string[]} others  additional parts (client, period, location, …)
   * @param {string} nameColor  hex color for the name segment
   * @return {{text:string, bold:boolean, color:string, italic:boolean}[]}
   */
  _buildTitleSegments_(name, others, nameColor) {
    const segments = [];
    if (name) {
      segments.push({ text: name, bold: true, color: nameColor, italic: false });
    }
    others.forEach((part) => {
      if (part) {
        segments.push({ text: ' | ', bold: false, color: '#5D6D7E', italic: false });
        segments.push({ text: part, bold: false, color: '#5D6D7E', italic: true });
      }
    });
    return segments;
  },

  /**
   * Applies per-segment color/bold/italic formatting to an already-populated
   * Text element using character offsets.
   *
   * @param {GoogleAppsScript.Document.Text} textEl
   * @param {{text:string, bold:boolean, color:string, italic:boolean}[]} segments
   */
  _applySegmentFormatting_(textEl, segments) {
    let pos = 0;
    segments.forEach((seg) => {
      if (!seg.text) return;
      const end = pos + seg.text.length - 1;
      textEl.setForegroundColor(pos, end, seg.color);
      if (seg.bold)   textEl.setBold(pos, end, true);
      if (seg.italic) textEl.setItalic(pos, end, true);
      pos += seg.text.length;
    });
  },

  // ─────────────────────────────────────────────────────────────────────────
  // Step 4 — Section omission
  // ─────────────────────────────────────────────────────────────────────────

  /**
   * Removes entire sections (heading + divider + content) when the
   * corresponding data is empty, per CV_FORMAT_ANALYSIS.md §5 omission rule.
   * Operates after all population steps so we know which sections are empty.
   *
   * @param {GoogleAppsScript.Document.Body} body
   * @param {Object} cvModel
   */
  _omitEmptySections_(body, cvModel) {
    const shouldOmit = {
      [SECTION_HEADINGS.PROFESSIONAL_SUMMARY]: !cvModel.summary,
      [SECTION_HEADINGS.TECHNICAL_SKILLS]:     !cvModel.technicalSkills || cvModel.technicalSkills.length === 0,
      [SECTION_HEADINGS.WORK_EXPERIENCE]:      !cvModel.workExperience || cvModel.workExperience.length === 0,
      [SECTION_HEADINGS.EDUCATION]:            !cvModel.education || cvModel.education.length === 0,
      [SECTION_HEADINGS.TRAINING]:             !cvModel.training || cvModel.training.length === 0,
      [SECTION_HEADINGS.KEY_PROJECTS]:         !cvModel.projects || cvModel.projects.length === 0,
      [SECTION_HEADINGS.ADDITIONAL_INFORMATION]: !cvModel.additionalInformation && !cvModel.languages,
    };

    Object.keys(shouldOmit).forEach((headingText) => {
      if (shouldOmit[headingText]) {
        this._removeSection_(body, headingText);
      }
    });
  },

  /**
   * Removes the section heading paragraph (and immediately following spacer/
   * divider table) plus all body children up to the next section heading.
   *
   * A "section heading" is identified by its text matching one of the
   * SECTION_HEADINGS values. The section ends at the next recognized
   * heading or the end of the document.
   *
   * @param {GoogleAppsScript.Document.Body} body
   * @param {string} headingText
   */
  _removeSection_(body, headingText) {
    const knownHeadings = Object.values(SECTION_HEADINGS);
    let headingIdx = -1;

    // Find the heading paragraph.
    for (let i = 0; i < body.getNumChildren(); i++) {
      const child = body.getChild(i);
      if (child.getType() === DocumentApp.ElementType.PARAGRAPH) {
        if (child.asParagraph().getText().trim() === headingText) {
          headingIdx = i;
          break;
        }
      }
    }

    if (headingIdx === -1) return; // heading not found (already removed?)

    // Find the end of the section: the next recognized heading paragraph.
    let endIdx = body.getNumChildren();
    for (let i = headingIdx + 1; i < body.getNumChildren(); i++) {
      const child = body.getChild(i);
      if (child.getType() === DocumentApp.ElementType.PARAGRAPH) {
        const t = child.asParagraph().getText().trim();
        if (knownHeadings.indexOf(t) !== -1) {
          endIdx = i;
          break;
        }
      }
    }

    // Delete from headingIdx up to (but NOT including) endIdx, in REVERSE
    // order so index shifts don't affect our targeting.
    // Also remove the blank spacer paragraph just BEFORE the heading (if any).
    const deleteFrom = headingIdx > 0 ? headingIdx - 1 : headingIdx;
    // Check if the preceding element is a blank spacer.
    let startDelete = headingIdx;
    if (headingIdx > 0) {
      const prev = body.getChild(headingIdx - 1);
      if (prev.getType() === DocumentApp.ElementType.PARAGRAPH &&
          prev.asParagraph().getText().trim() === '') {
        startDelete = headingIdx - 1;
      }
    }

    for (let i = endIdx - 1; i >= startDelete; i--) {
      body.removeChild(body.getChild(i));
    }
  },
};
