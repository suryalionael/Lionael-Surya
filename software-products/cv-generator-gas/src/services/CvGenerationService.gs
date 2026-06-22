/**
 * @fileoverview Single-employee CV generation pipeline.
 *
 * CvGenerationService.generateCvForEmployee() orchestrates:
 *   1. Data aggregation   (DataAggregationService)
 *   2. Output-folder preparation
 *   3. Template copy
 *   4. Template population (TemplateEngine)
 *   5. .pdf export        (UrlFetchApp + getOAuthToken)
 *   6. .docx export
 *
 * The function NEVER throws — it self-catches and returns a normalized
 * {success, employeeName, docUrl, pdfUrl, docxUrl, error} result so the
 * batch runner can continue on individual failures.
 *
 * See implementation plan §6 for the full pipeline specification.
 * See README "Troubleshooting" for the UrlFetchApp scope requirement and
 * the Advanced Drive Service alternative if external_request is blocked.
 */

const CvGenerationService = {

  /**
   * Generates one employee's CV (Google Doc + PDF + .docx export).
   *
   * @param {string} employeeName
   * @param {{summary: string, projectNames: string[], selectedSkills: string[],
   *          trainingNames: string[]} | null | undefined} selectionOverride
   *   Optional recruiter selections from CvBuilderRepository.getSelections().
   *   When null/undefined the full aggregated model is used (existing behaviour).
   * @return {{success: boolean, employeeName: string,
   *           docUrl: ?string, pdfUrl: ?string, docxUrl: ?string,
   *           error: ?string}}
   */
  generateCvForEmployee(employeeName, selectionOverride) {
    const cfg = getConfig();

    if (!isConfigured()) {
      return {
        success: false, employeeName,
        error: 'Setup has not been run. Open CV Generator menu → Setup / Re-initialize.',
      };
    }

    let copiedFile = null;

    try {
      // ── Step 1: Aggregate employee data ─────────────────────────────────
      const cvModel = DataAggregationService.buildEmployeeCvModel(employeeName);
      const model = this._applySelectionOverride_(cvModel, selectionOverride);
      CvLogger.log('INFO', 'GENERATION', employeeName, 'CV model ready');

      // ── Step 2: Ensure per-employee output subfolder ─────────────────────
      const employeeFolder = this._ensureEmployeeFolder_(cfg, employeeName);

      // ── Step 3: Copy the template ────────────────────────────────────────
      const templateFile = DriveApp.getFileById(cfg.TEMPLATE_DOCUMENT_ID);
      copiedFile = templateFile.makeCopy('__CV_temp_' + employeeName, employeeFolder);
      CvLogger.log('INFO', 'GENERATION', employeeName, 'Template copied',
        { copyId: copiedFile.getId() });

      // ── Step 4: Populate the copy ────────────────────────────────────────
      const doc = DocumentApp.openById(copiedFile.getId());
      TemplateEngine.populate(doc, model); // saves and closes the doc
      CvLogger.log('INFO', 'GENERATION', employeeName, 'Template populated');

      // Rename the populated Google Doc to the final employee name.
      copiedFile.setName(employeeName);
      const docUrl = copiedFile.getUrl();
      CvLogger.log('INFO', 'GENERATION', employeeName, 'Google Doc ready', { docUrl });

      // ── Step 5: Export PDF ───────────────────────────────────────────────
      const pdfBlob = this._exportDoc_(copiedFile.getId(), 'pdf');
      const pdfFile = employeeFolder.createFile(pdfBlob).setName(employeeName + '.pdf');
      const pdfUrl = pdfFile.getUrl();
      CvLogger.log('INFO', 'GENERATION', employeeName, 'PDF exported', { pdfUrl });

      // ── Step 6: Export .docx ─────────────────────────────────────────────
      const docxBlob = this._exportDoc_(copiedFile.getId(), 'docx');
      const docxFile = employeeFolder.createFile(docxBlob).setName(employeeName + '.docx');
      const docxUrl = docxFile.getUrl();
      CvLogger.log('INFO', 'GENERATION', employeeName, '.docx exported', { docxUrl });

      return { success: true, employeeName, docUrl, pdfUrl, docxUrl };

    } catch (err) {
      CvLogger.log('ERROR', 'GENERATION', employeeName,
        'CV generation failed: ' + err.message, { stack: err.stack || '' });

      // Best-effort cleanup of the half-created template copy so repeated
      // runs don't accumulate orphaned "__CV_temp_*" files.
      if (copiedFile) {
        try { copiedFile.setTrashed(true); } catch (e) { /* ignore cleanup failure */ }
      }

      return { success: false, employeeName, error: err.message };
    }
  },

  // ── Private helpers ───────────────────────────────────────────────────────

  /**
   * Ensures GENERATED_CV_FOLDER_ID/<Employee Name>/ exists and returns it.
   *
   * @param {Object} cfg  result of getConfig()
   * @param {string} employeeName
   * @return {GoogleAppsScript.Drive.Folder}
   */
  _ensureEmployeeFolder_(cfg, employeeName) {
    const root = DriveApp.getFolderById(cfg.GENERATED_CV_FOLDER_ID);
    const existing = root.getFoldersByName(employeeName);
    if (existing.hasNext()) return existing.next();
    return root.createFolder(employeeName);
  },

  /**
   * Applies recruiter selections to a cvModel, returning a filtered copy.
   * No-ops when override is null/undefined (existing batch-generation paths).
   *
   * Filtered fields:
   *   summary        — replaced verbatim if recruiter typed one
   *   projects       — whitelist by project name
   *   technicalSkills — individual skills whitelisted; empty categories dropped
   *   training       — whitelist by training name
   *
   * All other fields (name, position, workExperience, education, languages,
   * etc.) pass through unchanged.
   *
   * @param {Object} cvModel
   * @param {Object|null|undefined} override
   * @return {Object}
   */
  _applySelectionOverride_(cvModel, override) {
    if (!override) return cvModel;
    const m = Object.assign({}, cvModel);

    // DEBUG LOGGING — remove after diagnosis
    Logger.log('[OVERRIDE] cvModel.technicalSkills BEFORE override (' +
      (cvModel.technicalSkills || []).length + ' groups):');
    Logger.log(JSON.stringify(cvModel.technicalSkills, null, 2));
    Logger.log('[OVERRIDE] override.selectedSkills (' +
      (override.selectedSkills || []).length + ' skills):');
    Logger.log(JSON.stringify(override.selectedSkills, null, 2));

    if (override.summary) {
      m.summary = override.summary;
    }
    if (override.projectNames) {
      m.projects = (m.projects || []).filter(
        (p) => override.projectNames.indexOf(p.name) !== -1
      );
    }
    if (override.selectedSkills) {
      m.technicalSkills = (m.technicalSkills || [])
        .map((group) => ({
          category: group.category,
          values: (group.values || []).filter(
            (skill) => override.selectedSkills.indexOf(skill) !== -1
          ),
        }))
        .filter((group) => group.values.length > 0);
    }
    if (override.trainingNames) {
      m.training = (m.training || []).filter(
        (t) => override.trainingNames.indexOf(t.name) !== -1
      );
    }

    // DEBUG LOGGING — remove after diagnosis
    Logger.log('[OVERRIDE] m.technicalSkills AFTER override (' +
      (m.technicalSkills || []).length + ' groups):');
    Logger.log(JSON.stringify(m.technicalSkills, null, 2));

    return m;
  },

  /**
   * Exports a Google Doc (by ID) as either PDF or DOCX and returns the Blob.
   *
   * Uses UrlFetchApp + ScriptApp.getOAuthToken() — zero configuration
   * required (no Advanced Drive Service enablement needed), but requires the
   * `https://www.googleapis.com/auth/script.external_request` OAuth scope
   * declared in appsscript.json.
   *
   * Troubleshooting: if your Workspace org blocks external_request scope,
   * replace the UrlFetchApp call with:
   *   Drive.Files.export(docId, mimeType)
   * after enabling the Drive API v3 Advanced Service in the Apps Script
   * project (Extensions > Apps Script > Services > Drive API).
   *
   * @param {string} docId
   * @param {'pdf'|'docx'} format
   * @return {GoogleAppsScript.Base.Blob}
   */
  _exportDoc_(docId, format) {
    const mimeFormat = format === 'pdf' ? 'pdf'
      : 'vnd.openxmlformats-officedocument.wordprocessingml.document';
    const url = 'https://docs.google.com/document/d/' + docId +
                '/export?format=' + format;

    const response = UrlFetchApp.fetch(url, {
      headers: { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() },
      muteHttpExceptions: true,
    });

    ErrorHandler.assert(
      response.getResponseCode() === 200,
      'Export to ' + format + ' failed (HTTP ' + response.getResponseCode() +
      '). If your Workspace org blocks script.external_request, see README ' +
      'Troubleshooting for the Advanced Drive Service alternative.'
    );

    return response.getBlob().setName('cv.' + format);
  },
};
