/**
 * @fileoverview Setup / initialization controller.
 *
 * Exposes runSetup() as a global function bound to the "Setup / Re-initialize"
 * menu item. Idempotent — safe to call multiple times.
 *
 * What Setup does:
 *   1. Finds or creates the "Generated CVs" output folder in Drive.
 *   2. Finds or creates the CV placeholder template Google Doc.
 *   3. Ensures the Logs and Last Run Summary sheets exist.
 *   4. Populates the Control Panel employee list from Drive folders.
 *   5. Shows a confirmation dialog with links.
 */

/**
 * Global entry point for the "Setup / Re-initialize" menu item.
 * Must be a top-level function (not inside an object) for Apps Script
 * menu binding to work.
 */
function runSetup() {
  SetupController.run();
}

const SetupController = {

  run() {
    const ui = SpreadsheetApp.getUi();

    try {
      CvLogger.log('INFO', 'SETUP', '-', 'Setup started');

      // Step 1 — Ensure output folder hierarchy exists in Drive.
      const generatedCvsFolder = this._ensureOutputFolders_();
      const folderId = generatedCvsFolder.getId();

      // Persist GENERATED_CV_FOLDER_ID so getConfig() can read it.
      PropertiesService.getScriptProperties().setProperty('GENERATED_CV_FOLDER_ID', folderId);
      CvLogger.log('INFO', 'SETUP', '-', 'Output folder ready', { folderId });

      // Step 2 — Ensure template document exists.
      const cvGenParents = generatedCvsFolder.getParents();
      const cvGenFolder = cvGenParents.hasNext() ? cvGenParents.next() : DriveApp.getRootFolder();
      const templateFile = this._ensureTemplateDocument_(cvGenFolder);
      const templateId = templateFile.getId();

      PropertiesService.getScriptProperties().setProperty('TEMPLATE_DOCUMENT_ID', templateId);
      CvLogger.log('INFO', 'SETUP', '-', 'Template document ready', { templateId });

      // Step 3 — Ensure Logs and Summary sheets exist.
      ControlPanelRepository.ensureSheetsExist();
      CvLogger.log('INFO', 'SETUP', '-', 'Control Panel sheets initialized');

      // Step 4 — Sync employee list from Drive.
      refreshEmployeeList();
      CvLogger.log('INFO', 'SETUP', '-', 'Employee list refreshed');

      // Step 5 — Confirmation dialog.
      const templateUrl = templateFile.getUrl();
      const folderUrl = generatedCvsFolder.getUrl();
      ui.alert(
        'CV Generator — Setup Complete',
        'Setup finished successfully.\n\n' +
        'CV Template: ' + templateUrl + '\n\n' +
        'Output folder: ' + folderUrl + '\n\n' +
        'You may now use "Generate Selected CVs" or "Generate All CVs" from ' +
        'the CV Generator menu.\n\n' +
        'Optional: Open the template document and insert the MSI logo into ' +
        'the page header (this customization persists across all generated CVs).',
        ui.ButtonSet.OK
      );

    } catch (err) {
      CvLogger.log('ERROR', 'SETUP', '-', 'Setup failed: ' + err.message, { stack: err.stack });
      ui.alert(
        'CV Generator — Setup Error',
        'Setup encountered an error:\n\n' + err.message + '\n\n' +
        'Please check the Logs sheet and try again. If the problem persists, ' +
        'see the README Troubleshooting section.',
        ui.ButtonSet.OK
      );
    }
  },

  /**
   * Finds or creates: Drive root > "CV Generator" > "Generated CVs".
   * Returns the "Generated CVs" folder.
   *
   * @return {GoogleAppsScript.Drive.Folder}
   */
  _ensureOutputFolders_() {
    // Anchor the "CV Generator" folder next to the bound spreadsheet's
    // parent folder so everything stays organized together.
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const ssFile = DriveApp.getFileById(ss.getId());
    const ssParents = ssFile.getParents();
    const ssParent = ssParents.hasNext() ? ssParents.next() : DriveApp.getRootFolder();

    const cvGenFolder = this._findOrCreateFolder_(ssParent, CONFIG_STATIC.CV_GENERATOR_FOLDER_NAME);
    return this._findOrCreateFolder_(cvGenFolder, CONFIG_STATIC.GENERATED_CVS_FOLDER_NAME);
  },

  /**
   * Returns the template Doc file. If the Script Properties already hold a
   * valid TEMPLATE_DOCUMENT_ID, returns that file. Otherwise calls
   * TemplateBuilderService.createTemplate() to build a fresh one and places
   * it inside the "CV Generator" folder (sibling of "Generated CVs").
   *
   * @param {GoogleAppsScript.Drive.Folder} cvGenFolder  the "CV Generator" folder
   * @return {GoogleAppsScript.Drive.File}
   */
  _ensureTemplateDocument_(cvGenFolder) {
    const existingId = PropertiesService.getScriptProperties().getProperty('TEMPLATE_DOCUMENT_ID');
    if (existingId) {
      try {
        const f = DriveApp.getFileById(existingId);
        if (!f.isTrashed()) {
          CvLogger.log('INFO', 'SETUP', '-', 'Existing template found — reusing', { templateId: existingId });
          return f;
        }
      } catch (e) {
        // File not found or no access — fall through to create a new one.
        CvLogger.log('WARN', 'SETUP', '-', 'Stored template ID invalid, rebuilding template');
      }
    }
    return TemplateBuilderService.createTemplate(cvGenFolder);
  },

  /**
   * Returns a subfolder with `name` inside `parent`, creating it if absent.
   *
   * @param {GoogleAppsScript.Drive.Folder} parent
   * @param {string} name
   * @return {GoogleAppsScript.Drive.Folder}
   */
  _findOrCreateFolder_(parent, name) {
    const iter = parent.getFoldersByName(name);
    if (iter.hasNext()) return iter.next();
    return parent.createFolder(name);
  },
};
