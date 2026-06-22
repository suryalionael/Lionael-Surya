/**
 * @fileoverview Data aggregation service for the MSI CV Generator.
 *
 * Applies the per-field source-prioritization table from
 * CV_FORMAT_ANALYSIS.md §5 to build a normalized "CV model" for one employee:
 *
 *   Employee Form  →  Project Spreadsheet  →  Existing CV  →  default / omit
 *
 * The returned cvModel is the only input TemplateEngine.populate() needs.
 */

const DataAggregationService = {

  /**
   * Builds the normalized CV model for `employeeName`.
   *
   * @param {string} employeeName  as it appears in the Control Panel /
   *        Drive folder name
   * @return {Object}  cvModel shape:
   *   {
   *     name, position, yearsExperience, summary, languages,
   *     additionalInformation, lastUpdated,
   *     technicalSkills: [{category, values:[]}],
   *     education: [{degree, major, institution, year}],
   *     training: [{name, provider, year}],
   *     workExperience: [{position, company, period, location, bullets:[]}],
   *     projects: [{name, client, period, role, responsibility, tools,
   *                 startDate, endDate, isOngoing}],
   *     _meta: {sourcesUsed, folderId}
   *   }
   * @throws {Error}  if the employee folder cannot be found (caller decides
   *   whether to abort just this employee or the whole batch)
   */
  buildEmployeeCvModel(employeeName) {
    // ── Locate employee folder ───────────────────────────────────────────────
    const folderInfo = EmployeeRepository.findEmployeeFolder(employeeName);
    ErrorHandler.assert(
      folderInfo,
      'Employee folder not found for "' + employeeName + '" in Drive folder ' +
      CONFIG_STATIC.EMPLOYEE_FOLDER_ID + '. Check that the folder name matches ' +
      'the Control Panel entry (case/whitespace-insensitive).'
    );
    CvLogger.log('INFO', 'AGGREGATION', employeeName, 'Employee folder found',
      { folderId: folderInfo.folderId });

    // ── Load Employee Form + Existing CV ────────────────────────────────────
    const { employeeForm, existingCv } =
      EmployeeRepository.getEmployeeDocuments(folderInfo.folderId);

    if (!employeeForm) {
      CvLogger.log('WARN', 'AGGREGATION', employeeName,
        'Employee Form not found in folder — relying on Existing CV and Spreadsheet');
    }
    if (!existingCv) {
      CvLogger.log('WARN', 'AGGREGATION', employeeName, 'Existing CV not found in folder');
    }

    const formData = EmployeeRepository.parseDocument(employeeForm);
    const cvData   = EmployeeRepository.parseDocument(existingCv);

    // ── Load Project Spreadsheet data ───────────────────────────────────────
    const sheetEntry = SpreadsheetRepository.getEmployeeData(employeeName);
    if (!sheetEntry) {
      CvLogger.log('WARN', 'AGGREGATION', employeeName,
        'No Project Spreadsheet rows matched this employee name');
    }
    const sheetProjects  = sheetEntry ? sheetEntry.projects  : [];
    const sheetTrainings = sheetEntry ? sheetEntry.trainings : [];

    // ── Apply per-field prioritization ──────────────────────────────────────
    const sourcesUsed = {};
    const model = {};

    // {{NAME}}: Employee Form → folder name → Existing CV → folder name
    model.name = formData.name || folderInfo.name || cvData.name || folderInfo.name;
    sourcesUsed.name = formData.name ? 'employeeForm'
      : (cvData.name ? 'existingCv' : 'folderName');

    // {{POSITION}}: Employee Form → Existing CV → "-"
    model.position = formData.position || cvData.position || '-';
    sourcesUsed.position = formData.position ? 'employeeForm'
      : (cvData.position ? 'existingCv' : 'default');

    // {{YEARS_EXPERIENCE}}: Employee Form (explicit) → computed from Work
    // Experience → omit (null)
    if (formData.yearsExperience != null) {
      model.yearsExperience = formData.yearsExperience;
      sourcesUsed.yearsExperience = 'employeeForm';
    } else {
      const weList = formData.workExperience.length
        ? formData.workExperience : cvData.workExperience;
      const computed = this._computeYears_(weList);
      model.yearsExperience = computed;
      sourcesUsed.yearsExperience = computed != null ? 'computed' : 'omitted';
    }

    // {{SUMMARY}}: Employee Form → omit
    model.summary = formData.summary || '';
    sourcesUsed.summary = formData.summary ? 'employeeForm' : 'omitted';

    // {{TECHNICAL_SKILLS}}: Employee Form → Existing CV → omit
    model.technicalSkills = formData.technicalSkills.length
      ? formData.technicalSkills : cvData.technicalSkills;
    sourcesUsed.technicalSkills = formData.technicalSkills.length ? 'employeeForm'
      : (cvData.technicalSkills.length ? 'existingCv' : 'omitted');

    // {{WORK_EXPERIENCE}}: Employee Form → Existing CV → omit
    model.workExperience = formData.workExperience.length
      ? formData.workExperience : cvData.workExperience;
    sourcesUsed.workExperience = formData.workExperience.length ? 'employeeForm'
      : (cvData.workExperience.length ? 'existingCv' : 'omitted');

    // {{EDUCATION}}: Employee Form → Existing CV → omit
    model.education = formData.education.length
      ? formData.education : cvData.education;
    sourcesUsed.education = formData.education.length ? 'employeeForm'
      : (cvData.education.length ? 'existingCv' : 'omitted');

    // {{TRAINING}} / {{CERTIFICATIONS}}: Employee Form → Spreadsheet → omit
    // Merged and de-duplicated (certifications folded into training per §2.3).
    model.training = this._mergeTraining_(formData.training, sheetTrainings);
    sourcesUsed.training = formData.training.length
      ? 'employeeForm+spreadsheet'
      : (sheetTrainings.length ? 'spreadsheet' : 'omitted');

    // {{LANGUAGES}}: Employee Form → Existing CV → "Indonesian" default
    model.languages = formData.languages || cvData.languages || 'Indonesian';
    sourcesUsed.languages = formData.languages ? 'employeeForm'
      : (cvData.languages ? 'existingCv' : 'default');

    // {{PROJECTS}}: Spreadsheet → Existing CV "PROJECT EXPERIENCE" → omit
    const rawProjects = sheetProjects.length ? sheetProjects : cvData.projects;
    model.projects = this._sortProjects_(rawProjects);
    sourcesUsed.projects = sheetProjects.length ? 'spreadsheet'
      : (cvData.projects.length ? 'existingCv' : 'omitted');

    // {{ADDITIONAL_INFORMATION}}: Employee Form → omit
    model.additionalInformation = formData.additionalInformation || '';
    sourcesUsed.additionalInformation =
      formData.additionalInformation ? 'employeeForm' : 'omitted';

    // {{LAST_UPDATED}}: generated at run time
    model.lastUpdated = DateUtils.formatMonthYear(new Date());
    sourcesUsed.lastUpdated = 'generated';

    model._meta = { sourcesUsed, folderId: folderInfo.folderId };

    CvLogger.log('INFO', 'AGGREGATION', employeeName, 'CV model built', { sourcesUsed });
    return model;
  },

  // ── Private helpers ───────────────────────────────────────────────────────

  /**
   * Computes years of experience from the earliest work experience start date
   * to today. Returns null if no parseable dates are available.
   *
   * @param {Array} workExperience
   * @return {number|null}
   */
  _computeYears_(workExperience) {
    const starts = (workExperience || [])
      .map((w) => DateUtils.parsePeriodString(w.period).startDate)
      .filter(Boolean);
    if (starts.length === 0) return null;
    const earliest = starts.reduce((a, b) => (a < b ? a : b));
    return DateUtils.yearsFrom(earliest);
  },

  /**
   * Merges Employee Form training entries with Project Spreadsheet training/
   * certification entries, de-duplicating by normalized (name, year).
   * The spreadsheet's "Output & Kompetensi..." column is used as Provider
   * when it looks like an org name (short, no sentence punctuation).
   *
   * @param {Array} formTraining
   * @param {Array} sheetTraining
   * @return {Array}
   */
  _mergeTraining_(formTraining, sheetTraining) {
    const merged = [];

    (formTraining || []).forEach((t) => merged.push({
      name:     t.name,
      provider: t.provider || '',
      year:     t.year || '',
      type:     'training',
    }));

    (sheetTraining || []).forEach((t) => merged.push({
      name:     t.name,
      provider: this._inferProvider_(t.outputCompetency),
      year:     t.year || '',
      type:     /certif/i.test(t.name) ? 'certification' : 'training',
    }));

    return TextUtils.dedupeBy(
      merged,
      (t) => TextUtils.normalizeName(t.name) + '|' + String(t.year).trim()
    );
  },

  /**
   * If `text` looks like an organization name (≤40 chars, no sentence-ending
   * punctuation), use it as the Provider; otherwise return empty string.
   *
   * @param {string} text
   * @return {string}
   */
  _inferProvider_(text) {
    const s = String(text || '').trim();
    if (!s) return '';
    if (s.length <= 40 && !/[.!?]/.test(s)) return s;
    return '';
  },

  /**
   * Sorts projects in reverse chronological order:
   *   Primary:   End Date descending (ongoing / "Sekarang" = latest)
   *   Secondary: Start Date descending
   *
   * Per CV_FORMAT_ANALYSIS.md §6 and the spec's project-sort rule.
   *
   * @param {Array} projects
   * @return {Array}
   */
  _sortProjects_(projects) {
    const FAR_FUTURE = new Date(8640000000000000); // Date.MAX_VALUE equivalent
    const effectiveEnd = (p) =>
      p.isOngoing ? FAR_FUTURE : (p.endDate || p.startDate || new Date(0));
    const effectiveStart = (p) => p.startDate || new Date(0);

    return (projects || []).slice().sort((a, b) => {
      const endDiff = effectiveEnd(b).getTime() - effectiveEnd(a).getTime();
      if (endDiff !== 0) return endDiff;
      return effectiveStart(b).getTime() - effectiveStart(a).getTime();
    });
  },
};
