/**
 * @fileoverview Repository for reading employee data from the Drive folder
 * hierarchy (Employee Data Repository, ID in CONFIG_STATIC.EMPLOYEE_FOLDER_ID).
 *
 * Expected structure per employee:
 *   <Employee Name>/
 *     Employee Form      (primary data — Priority 1)
 *     Existing CV        (fallback — Priority 3)
 *     Supporting Docs    (IGNORED — KTP/NPWP/KK/birth certs/etc.)
 *
 * Files matching CONFIG_STATIC.IDENTITY_DOC_PATTERN are skipped entirely.
 *
 * Parsing uses a label-based state machine that recognises the section
 * vocabulary from the legacy CV format (BACKGROUND / FORMAL EDUCATION /
 * NON-FORMAL EDUCATION / TECHNICAL SKILL / Other skills / WORKING EXPERIENCES /
 * PROJECT EXPERIENCE) — the same labels found in the "Employee Form" and
 * "Existing CV" files in production. Both Google Doc and Google Sheet mime
 * types are handled: Docs are flattened to a line array via body iteration;
 * Sheets are flattened via "ColA: ColB" row formatting.
 *
 * See CV_FORMAT_ANALYSIS.md §4 for the full field vocabulary reference.
 */

const EmployeeRepository = {

  // ── Section-header label regexes ──────────────────────────────────────────
  LABELS: Object.freeze({
    BACKGROUND:          /^BACKGROUND$/i,
    FORMAL_EDUCATION:    /^FORMAL\s+EDUCATION$/i,
    NON_FORMAL_EDUCATION:/^NON[-–]?\s*FORMAL\s*\/\s*INFORMAL\s+EDUCATION/i,
    TECHNICAL_SKILL:     /^TECHNICAL\s+SKILL/i,
    OTHER_SKILLS:        /^Other\s+skills/i,
    WORKING_EXPERIENCES: /^WORKING\s+EXPERIENCES?$/i,
    PROJECT_EXPERIENCE:  /^PROJECT\s+EXPERIENCE$/i,
  }),

  // Sub-labels within PROJECT EXPERIENCE entries (order is INCONSISTENT
  // across entries per CV_FORMAT_ANALYSIS.md §2.1 — match by regex, not position).
  PROJECT_SUBLABELS: Object.freeze({
    ROLE:           /^Role\s*:/i,
    DESCRIPTION:    /^Description\s*:/i,
    RESPONSIBILITY: /^Responsibilit(?:y|ies)\s*:/i,
    TOOLS:          /^Tools?\s*:/i,
    TEAM_MEMBERS:   /^Team\s+[Mm]embers?\s*:/i,
  }),

  // ── Public API ────────────────────────────────────────────────────────────

  /**
   * Returns all employee folders discovered under EMPLOYEE_FOLDER_ID.
   *
   * @return {Array<{name: string, folderId: string}>}
   */
  discoverEmployeeFolders() {
    const root = DriveApp.getFolderById(CONFIG_STATIC.EMPLOYEE_FOLDER_ID);
    const iter = root.getFolders();
    const found = [];
    while (iter.hasNext()) {
      const folder = iter.next();
      found.push({ name: folder.getName(), folderId: folder.getId() });
    }
    CvLogger.log('INFO', 'EMPLOYEE_REPO', '-', 'Discovered employee folders', { count: found.length });
    return found;
  },

  /**
   * Finds an employee folder by name (case/whitespace-insensitive match).
   *
   * @param {string} employeeName
   * @return {{name: string, folderId: string}|null}
   */
  findEmployeeFolder(employeeName) {
    const folders = this.discoverEmployeeFolders();
    const match = folders.find((f) => TextUtils.namesMatch(f.name, employeeName));
    return match || null;
  },

  /**
   * Finds "Employee Form" and "Existing CV" files inside an employee folder.
   * Skips identity documents. Returns null for either if not found.
   *
   * @param {string} folderId
   * @return {{employeeForm: GoogleAppsScript.Drive.File|null,
   *           existingCv: GoogleAppsScript.Drive.File|null}}
   */
  getEmployeeDocuments(folderId) {
    const folder = DriveApp.getFolderById(folderId);
    const employeeName = folder.getName(); // used for preference logging only
    const fileIter = folder.getFiles();
    const formCandidates = [];
    const cvCandidates   = [];

    while (fileIter.hasNext()) {
      const f = fileIter.next();
      const fname = f.getName();

      // Skip personal identity documents unconditionally.
      if (CONFIG_STATIC.IDENTITY_DOC_PATTERN.test(fname)) continue;

      if (CONFIG_STATIC.EMPLOYEE_FORM_FILENAME_PATTERN.test(fname)) {
        formCandidates.push(f);
      } else if (CONFIG_STATIC.EXISTING_CV_FILENAME_PATTERN.test(fname)) {
        cvCandidates.push(f);
      }
    }

    return {
      employeeForm: this._preferGoogleDoc_(formCandidates, 'Employee Form', employeeName),
      existingCv:   this._preferGoogleDoc_(cvCandidates,   'Existing CV',   employeeName),
    };
  },

  /**
   * Opens and parses a Drive file (Google Doc or Google Sheet) using the
   * label-based state machine.
   *
   * @param {GoogleAppsScript.Drive.File|null} file
   * @return {Object}  normalized extraction shape (see _emptyExtraction_)
   */
  parseDocument(file) {
    if (!file) return this._emptyExtraction_();

    const mimeType = file.getMimeType();
    try {
      if (mimeType === MimeType.GOOGLE_DOCS) {
        const doc = DocumentApp.openById(file.getId());
        return this._parseGoogleDoc_(doc);
      }
      if (mimeType === MimeType.GOOGLE_SHEETS) {
        const ss = SpreadsheetApp.openById(file.getId());
        return this._parseGoogleSheet_(ss);
      }
      // For .docx files stored natively (not converted to Google Docs):
      // We cannot open them with DocumentApp directly, so we log a warning
      // and return empty. HR should convert these to Google Docs format.
      CvLogger.log('WARN', 'EMPLOYEE_REPO', '-',
        'Unsupported file type for label-based parsing: ' + mimeType +
        ' (' + file.getName() + '). Convert to Google Docs for full extraction.');
      return this._emptyExtraction_();
    } catch (e) {
      CvLogger.log('ERROR', 'EMPLOYEE_REPO', '-',
        'Failed to parse document: ' + file.getName() + ': ' + e.message);
      return this._emptyExtraction_();
    }
  },

  // ── Private: extraction result shape ─────────────────────────────────────

  _emptyExtraction_() {
    return {
      name: '',
      position: '',
      yearsExperience: null,
      summary: '',
      languages: '',
      additionalInformation: '',
      technicalSkills: [],   // [{category, values:[]}]
      education: [],         // [{degree, major, institution, year}]
      training: [],          // [{name, provider, year}]
      workExperience: [],    // [{position, company, location, period, bullets:[]}]
      projects: [],          // [{name, client, period, role, responsibility, tools, startDate, endDate, isOngoing}]
    };
  },

  // ── Private: Google Doc parsing ───────────────────────────────────────────

  _parseGoogleDoc_(doc) {
    const body = doc.getBody();
    const lines = this._docBodyToLines_(body);
    return this._linesToExtraction_(lines);
  },

  /**
   * Flattens a document body into an array of {text, isBold, isListItem}.
   * Handles plain paragraphs, list items, and 2-column key/value tables
   * (some Employee Form variants use a table layout instead of paragraphs).
   */
  _docBodyToLines_(body) {
    const lines = [];
    const n = body.getNumChildren();
    for (let i = 0; i < n; i++) {
      const child = body.getChild(i);
      const type = child.getType();

      if (type === DocumentApp.ElementType.PARAGRAPH ||
          type === DocumentApp.ElementType.LIST_ITEM) {
        const raw = child.asText ? child.asText().getText() : child.getText();
        const trimmed = String(raw || '').trim();
        if (!trimmed) continue;
        lines.push({
          text: trimmed,
          isBold: this._isLineBold_(child),
          isListItem: type === DocumentApp.ElementType.LIST_ITEM,
        });
      } else if (type === DocumentApp.ElementType.TABLE) {
        const table = child.asTable();
        for (let r = 0; r < table.getNumRows(); r++) {
          const row = table.getRow(r);
          if (row.getNumCells() >= 2) {
            const key = row.getCell(0).getText().trim();
            const val = row.getCell(1).getText().trim();
            if (key) lines.push({ text: key + ': ' + val, isBold: false, isListItem: false });
          } else if (row.getNumCells() === 1) {
            const t = row.getCell(0).getText().trim();
            if (t) lines.push({ text: t, isBold: false, isListItem: false });
          }
        }
      }
    }
    return lines;
  },

  _isLineBold_(element) {
    try {
      const text = element.editAsText();
      if (text.getText().length === 0) return false;
      return text.isBold(0) === true;
    } catch (e) {
      return false;
    }
  },

  // ── Private: Google Sheet parsing ─────────────────────────────────────────

  _parseGoogleSheet_(spreadsheet) {
    const sheet = spreadsheet.getSheets()[0];
    const values = sheet.getDataRange().getValues();
    const lines = [];
    values.forEach((row) => {
      const nonEmpty = row.map((c) => String(c || '').trim()).filter(Boolean);
      if (nonEmpty.length === 0) return;
      if (nonEmpty.length === 1) {
        lines.push({ text: nonEmpty[0], isBold: false, isListItem: false });
      } else if (nonEmpty.length === 2) {
        lines.push({ text: nonEmpty[0] + ': ' + nonEmpty[1], isBold: false, isListItem: false });
      } else {
        lines.push({ text: nonEmpty.join(' | '), isBold: false, isListItem: false });
      }
    });
    return this._linesToExtraction_(lines);
  },

  // ── Private: line-array state machine ─────────────────────────────────────

  /**
   * Core label-based extraction. Iterates the line array, dispatches each
   * line to per-section handlers, and returns a normalized extraction object.
   */
  _linesToExtraction_(lines) {
    const result = this._emptyExtraction_();
    let section = null;

    for (let i = 0; i < lines.length; i++) {
      const { text } = lines[i];

      // ── Section header detection ─────────────────────────────────────────
      if (this.LABELS.BACKGROUND.test(text))            { section = 'BACKGROUND'; continue; }
      if (this.LABELS.FORMAL_EDUCATION.test(text))      { section = 'FORMAL_EDUCATION'; continue; }
      if (this.LABELS.NON_FORMAL_EDUCATION.test(text))  { section = 'NON_FORMAL_EDUCATION'; continue; }
      if (this.LABELS.TECHNICAL_SKILL.test(text))       { section = 'TECHNICAL_SKILL'; continue; }
      if (this.LABELS.OTHER_SKILLS.test(text))          { section = 'OTHER_SKILLS'; continue; }
      if (this.LABELS.WORKING_EXPERIENCES.test(text))   { section = 'WORKING_EXPERIENCES'; continue; }
      if (this.LABELS.PROJECT_EXPERIENCE.test(text))    { section = 'PROJECT_EXPERIENCE'; continue; }

      // ── Per-section dispatch ─────────────────────────────────────────────
      switch (section) {
        case 'BACKGROUND':
          this._handleBackground_(result, text);
          break;
        case 'FORMAL_EDUCATION':
          i = this._handleFormalEducation_(result, lines, i);
          break;
        case 'NON_FORMAL_EDUCATION':
          i = this._handleNonFormalEducation_(result, lines, i);
          break;
        case 'TECHNICAL_SKILL':
          this._handleTechnicalSkill_(result, text);
          break;
        case 'OTHER_SKILLS':
          this._handleOtherSkills_(result, text);
          break;
        case 'WORKING_EXPERIENCES':
          i = this._handleWorkExperience_(result, lines, i);
          break;
        case 'PROJECT_EXPERIENCE':
          i = this._handleProjectExperience_(result, lines, i);
          break;
        default:
          // Lines before any recognized section header: preamble key/value.
          this._handlePreamble_(result, text);
          break;
      }
    }

    return result;
  },

  // ── Private: section handlers ─────────────────────────────────────────────

  _handlePreamble_(result, text) {
    const mName = text.match(/^(?:Full\s+)?Name\s*:\s*(.+)$/i);
    if (mName) { result.name = result.name || mName[1].trim(); return; }
    const mPos = text.match(/^(?:Position|Current\s+Position|Job\s+Title)\s*:\s*(.+)$/i);
    if (mPos) { result.position = result.position || mPos[1].trim(); return; }
    const mYears = text.match(/^Years?\s+of\s+Experience\s*:\s*(\d+)/i);
    if (mYears) { result.yearsExperience = parseInt(mYears[1], 10); return; }
    const mSummary = text.match(/^(?:Professional\s+)?Summary\s*:\s*(.+)$/i);
    if (mSummary) {
      result.summary = result.summary ? result.summary + ' ' + mSummary[1].trim() : mSummary[1].trim();
    }
  },

  _handleBackground_(result, text) {
    const mName = text.match(/^Name\s*:\s*(.+)$/i);
    if (mName) { result.name = result.name || mName[1].trim(); return; }
    const mPos = text.match(/^(?:Position|Current\s+Position|Job\s+Title)\s*:\s*(.+)$/i);
    if (mPos) { result.position = result.position || mPos[1].trim(); }
    // Date of birth / Marital Status intentionally not extracted (not used in new CV format).
  },

  /**
   * Formal Education — paired-line pattern:
   *   Line A: "INSTITUTION (Location) YYYY - YYYY"
   *   Line B: "Degree (Major)"
   * Returns the index of the last line consumed.
   */
  _handleFormalEducation_(result, lines, startIndex) {
    const text = lines[startIndex].text;

    // Pattern A: institution with year range in parens OR at end of line.
    const mInst = text.match(/^(.+?)\s+\(([^)]*)\)\s+(\d{4})\s*[-–]\s*(\d{4}|\w+)\s*$/);
    if (mInst) {
      result._pendingEducation = {
        institution: mInst[1].trim(),
        year: mInst[3] + '-' + mInst[4],
        degree: '', major: '',
      };
      // Peek at next line for the Degree (Major) line.
      if (startIndex + 1 < lines.length) {
        const next = lines[startIndex + 1].text;
        const mDeg = next.match(/^(.+?)\s+\(([^)]+)\)\s*$/);
        if (mDeg) {
          result._pendingEducation.degree = mDeg[1].trim();
          result._pendingEducation.major = mDeg[2].trim();
          result.education.push(result._pendingEducation);
          delete result._pendingEducation;
          return startIndex + 1;
        }
        // Degree line without parenthesized major.
        if (!this._isAnySectionHeader_(next)) {
          result._pendingEducation.degree = next.trim();
          result.education.push(result._pendingEducation);
          delete result._pendingEducation;
          return startIndex + 1;
        }
      }
      if (result._pendingEducation) {
        result.education.push(result._pendingEducation);
        delete result._pendingEducation;
      }
      return startIndex;
    }

    // Standalone "Sarjana Komputer S.Kom (Science, Technology, ...)" degree line
    // following a pending education entry from a previous call.
    if (result._pendingEducation) {
      const mDeg = text.match(/^(.+?)\s+\(([^)]+)\)\s*$/);
      if (mDeg) {
        result._pendingEducation.degree = mDeg[1].trim();
        result._pendingEducation.major = mDeg[2].trim();
      } else {
        result._pendingEducation.degree = text;
      }
      result.education.push(result._pendingEducation);
      delete result._pendingEducation;
    }

    return startIndex;
  },

  /**
   * Non-formal / Informal Education — date-range + multi-line name.
   * Returns the index of the last line consumed.
   */
  _handleNonFormalEducation_(result, lines, startIndex) {
    const dateRangeRe = /^([A-Za-z]{2,9}\.?\s*\d{4})\s*[-–]\s*([A-Za-z]{2,9}\.?\s*\d{4}|[A-Za-z]+)\s*$/;
    const text = lines[startIndex].text;
    const mDate = text.match(dateRangeRe);
    if (!mDate) return startIndex;

    const entry = {
      name: '',
      provider: '',
      year: DateUtils.extractYear(mDate[2]) || DateUtils.extractYear(mDate[1]),
    };

    let i = startIndex + 1;
    for (; i < lines.length; i++) {
      const t = lines[i].text;
      if (dateRangeRe.test(t) || this._isAnySectionHeader_(t)) break;
      const mOn = t.match(/^On\s+(.+)$/i);
      if (mOn) {
        entry.provider = mOn[1].trim();
      } else if (!entry.name) {
        entry.name = t;
      } else {
        entry.name += ' ' + t;
      }
    }

    if (entry.name) result.training.push(entry);
    return i - 1;
  },

  _handleTechnicalSkill_(result, text) {
    const m = text.match(/^(.+?)\s*:\s*(.*)$/);
    if (!m) return;
    const category = m[1].trim();
    const valuesRaw = m[2].trim();
    if (!category) return;
    const values = valuesRaw
      ? valuesRaw.split(/[,，]/).map((v) => v.trim().replace(/^:\s*/, '')).filter(Boolean)
      : [];
    if (values.length === 0) return; // skip empty "BI Tools:" etc.
    result.technicalSkills.push({ category, values });
  },

  _handleOtherSkills_(result, text) {
    const m = text.match(/^Languages?\s*:\s*(.+)$/i);
    if (m) result.languages = m[1].trim();
  },

  /**
   * Working Experiences — multi-line consumer: date range → position–company →
   * "Job description:" label → bullet lines.
   * Returns the index of the last line consumed.
   */
  _handleWorkExperience_(result, lines, startIndex) {
    const dateRangeRe = /^(.+?)\s*[-–]\s*(.+?)\s*$/;
    const text = lines[startIndex].text;

    // First line in this section must be a date range.
    if (!this._looksLikePeriod_(text)) return startIndex;

    const period = text;
    let i = startIndex + 1;
    if (i >= lines.length) return startIndex;

    // Second line: "POSITION – Company, Location"
    const titleLine = lines[i].text;
    const mTitle = titleLine.match(/^(.+?)\s+[-–]\s+(.+)$/);
    let position = titleLine;
    let company = '';
    let location = '';
    if (mTitle) {
      position = mTitle[1].trim();
      const parts = mTitle[2].split(/,(.+)/); // split on first comma
      company = (parts[0] || '').trim();
      location = (parts[1] || '').trim();
    }

    i++;
    const bullets = [];
    for (; i < lines.length; i++) {
      const t = lines[i].text;
      if (/^Job\s+description\s*:?\s*$/i.test(t)) continue; // skip the label line
      if (this._looksLikePeriod_(t)) break;
      if (this._isAnySectionHeader_(t)) break;
      bullets.push(t);
    }

    result.workExperience.push({ position, company, location, period, bullets });
    return i - 1;
  },

  /**
   * Project Experience — multi-line consumer: "Name – Client" → period →
   * sub-label lines (Role/Description/Responsibility/Tools/Team Members in
   * ANY order, per CV_FORMAT_ANALYSIS §2.1).
   * Returns the index of the last line consumed.
   */
  _handleProjectExperience_(result, lines, startIndex) {
    const text = lines[startIndex].text;
    if (this._isAnySectionHeader_(text)) return startIndex;
    if (this._matchesProjectSublabel_(text)) return startIndex;

    const mTitle = text.match(/^(.+?)\s*[-–,]\s*(.+)$/);
    if (!mTitle) return startIndex;

    const name = mTitle[1].trim();
    const client = mTitle[2].trim();
    let period = '';
    const sub = { role: '', description: '', responsibility: '', tools: '' };

    let i = startIndex + 1;
    for (; i < lines.length; i++) {
      const t = lines[i].text;
      if (this._isAnySectionHeader_(t)) break;

      if (!period && this._looksLikePeriod_(t) && !this._matchesProjectSublabel_(t)) {
        period = t;
        continue;
      }
      if (this.PROJECT_SUBLABELS.ROLE.test(t))           { sub.role = this._afterColon_(t); continue; }
      if (this.PROJECT_SUBLABELS.DESCRIPTION.test(t))    { sub.description = this._afterColon_(t); continue; }
      if (this.PROJECT_SUBLABELS.RESPONSIBILITY.test(t)) { sub.responsibility = this._afterColon_(t); continue; }
      if (this.PROJECT_SUBLABELS.TOOLS.test(t))          { sub.tools = this._afterColon_(t); continue; }
      if (this.PROJECT_SUBLABELS.TEAM_MEMBERS.test(t))   { continue; } // not used in new CV

      // A line with a dash that matches no sublabel = next project title.
      if (/[-–]/.test(t) && !this._matchesProjectSublabel_(t)) break;

      // Continuation: append to description.
      sub.description = sub.description ? sub.description + ' ' + t : t;
    }

    const parsed = DateUtils.parsePeriodString(period);
    result.projects.push({
      name, client, period,
      startDate: parsed.startDate,
      endDate: parsed.endDate,
      isOngoing: parsed.isOngoing,
      role: sub.role,
      responsibility: TextUtils.joinNonEmpty([sub.description, sub.responsibility], ' '),
      tools: sub.tools,
    });

    return i - 1;
  },

  // ── Private: helper predicates ────────────────────────────────────────────

  _isAnySectionHeader_(text) {
    return Object.keys(this.LABELS).some((k) => this.LABELS[k].test(text));
  },

  _matchesProjectSublabel_(text) {
    return Object.keys(this.PROJECT_SUBLABELS).some((k) => this.PROJECT_SUBLABELS[k].test(text));
  },

  _looksLikePeriod_(text) {
    // Matches patterns like "Mar 2017 – Now", "2010 - 2014", "Maret 2020 – September 2020"
    return /\b\d{4}\b/.test(text) && /[-–]/.test(text);
  },

  _afterColon_(text) {
    const idx = text.indexOf(':');
    return idx === -1 ? '' : text.slice(idx + 1).trim();
  },

  /**
   * Given an array of Drive file candidates that matched a filename pattern,
   * returns the best one: a native Google Doc is preferred over any other
   * MIME type (e.g. DOCX). Falls back to candidates[0] when no Google Doc
   * is present, preserving the original single-match behaviour.
   *
   * Logs an INFO entry when a Google Doc is actively chosen over a non-Docs
   * alternative (i.e. when the preference actually changes the outcome).
   *
   * @param {GoogleAppsScript.Drive.File[]} candidates
   * @param {string} role  'Employee Form' or 'Existing CV' — for log clarity
   * @param {string} employeeName
   * @return {GoogleAppsScript.Drive.File|null}
   */
  _preferGoogleDoc_(candidates, role, employeeName) {
    if (candidates.length === 0) return null;
    const gdoc = candidates.find((f) => f.getMimeType() === MimeType.GOOGLE_DOCS);
    if (gdoc && candidates.length > 1) {
      CvLogger.log('INFO', 'EMPLOYEE_REPO', employeeName,
        'Google Doc preferred over DOCX for ' + role,
        {
          selectedFileName: gdoc.getName(),
          selectedMimeType: gdoc.getMimeType(),
        });
    }
    return gdoc || candidates[0];
  },
};
