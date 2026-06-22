/**
 * @fileoverview One-time migration utility: converts DOCX files stored in
 * employee Drive folders into native Google Docs so that
 * EmployeeRepository.parseDocument() can open and parse them with its
 * label-based state machine.
 *
 * Entry point: DocxMigrationService.migrateAll()
 * Menu:        CV Generator → Tools → Convert All DOCX to Google Docs
 *
 * Conversion uses the Drive API v3 files.copy endpoint with a mimeType
 * override — the same UrlFetchApp + getOAuthToken() pattern used by
 * CvGenerationService._exportDoc_().
 *
 * The original DOCX files are NEVER deleted or modified. The converted
 * Google Doc is placed in the same employee folder with the same name
 * minus the ".docx" extension.
 *
 * NOTE: MimeType.MICROSOFT_WORD === 'application/msword' — this is the
 * legacy binary Word 97-2003 (.doc) format. Modern .docx files use
 * DOCX_MIME defined below. Do not use MimeType.MICROSOFT_WORD to detect
 * .docx files.
 */

/** MIME type for modern Word (.docx) files. */
const DOCX_MIME =
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

const DocxMigrationService = {

  /**
   * Iterates all employee subfolders under EMPLOYEE_FOLDER_ID, finds every
   * .docx file (by MIME type), and converts each to a native Google Doc in
   * the same folder — unless a Google Doc with the same base name already
   * exists, in which case the file is skipped.
   *
   * @return {Array<{
   *   employeeName: string,
   *   sourceDocxName: string,
   *   sourceDocxId: string,
   *   convertedGoogleDocId: string|null,
   *   convertedUrl: string|null,
   *   status: 'CONVERTED'|'SKIPPED'|'ERROR',
   *   error: string|null
   * }>}
   */
  migrateAll() {
    const root = DriveApp.getFolderById(CONFIG_STATIC.EMPLOYEE_FOLDER_ID);
    const folderIter = root.getFolders();
    const allResults = [];

    while (folderIter.hasNext()) {
      const folder = folderIter.next();
      const employeeName = folder.getName();
      CvLogger.log('INFO', 'DOCX_MIGRATION', employeeName,
        'Scanning folder for DOCX files');

      const folderResults = this._migrateFolder_(folder, employeeName);
      folderResults.forEach((r) => allResults.push(r));
    }

    const converted = allResults.filter((r) => r.status === 'CONVERTED').length;
    const skipped   = allResults.filter((r) => r.status === 'SKIPPED').length;
    const failed    = allResults.filter((r) => r.status === 'ERROR').length;

    CvLogger.log('INFO', 'DOCX_MIGRATION', '-', 'Migration complete', {
      total: allResults.length,
      converted,
      skipped,
      failed,
    });

    return allResults;
  },

  // ── Private ───────────────────────────────────────────────────────────────

  /**
   * Processes all DOCX files in one employee folder.
   *
   * @param {GoogleAppsScript.Drive.Folder} folder
   * @param {string} employeeName
   * @return {Array}
   */
  _migrateFolder_(folder, employeeName) {
    const results = [];
    const fileIter = folder.getFilesByType(DOCX_MIME);

    while (fileIter.hasNext()) {
      const docxFile = fileIter.next();
      const sourceDocxName = docxFile.getName();
      const sourceDocxId   = docxFile.getId();
      const baseName = sourceDocxName.replace(/\.docx$/i, '');

      const result = {
        employeeName,
        sourceDocxName,
        sourceDocxId,
        convertedGoogleDocId: null,
        convertedUrl:         null,
        status:               null,
        error:                null,
      };

      try {
        if (this._googleDocExists_(folder, baseName)) {
          result.status = 'SKIPPED';
          CvLogger.log('INFO', 'DOCX_MIGRATION', employeeName,
            'Skipped — Google Doc already exists',
            { sourceDocxName, baseName });
        } else {
          const converted = this._convertDocxToGoogleDoc_(docxFile, folder, baseName);
          result.convertedGoogleDocId = converted.id;
          result.convertedUrl         = converted.url;
          result.status               = 'CONVERTED';
          CvLogger.log('INFO', 'DOCX_MIGRATION', employeeName,
            'Converted successfully',
            { sourceDocxName, sourceDocxId, convertedGoogleDocId: converted.id });
        }
      } catch (err) {
        result.status = 'ERROR';
        result.error  = err.message;
        CvLogger.log('ERROR', 'DOCX_MIGRATION', employeeName,
          'Conversion failed: ' + err.message,
          { sourceDocxName, sourceDocxId });
      }

      results.push(result);
    }

    return results;
  },

  /**
   * Returns true if `folder` already contains a native Google Doc whose name
   * exactly matches `baseName` (case-sensitive, matching Drive's own lookup).
   *
   * @param {GoogleAppsScript.Drive.Folder} folder
   * @param {string} baseName  DOCX filename with ".docx" stripped
   * @return {boolean}
   */
  _googleDocExists_(folder, baseName) {
    const iter = folder.getFilesByName(baseName);
    while (iter.hasNext()) {
      if (iter.next().getMimeType() === MimeType.GOOGLE_DOCS) return true;
    }
    return false;
  },

  /**
   * Calls the Drive API v3 files.copy endpoint with a mimeType of
   * 'application/vnd.google-apps.document', which instructs the Drive
   * backend to perform server-side DOCX-to-Docs conversion. The resulting
   * Google Doc is placed directly in `folder`.
   *
   * Authentication follows the same pattern as CvGenerationService._exportDoc_():
   * UrlFetchApp + ScriptApp.getOAuthToken(). Requires the
   * 'https://www.googleapis.com/auth/script.external_request' OAuth scope
   * declared in appsscript.json.
   *
   * @param {GoogleAppsScript.Drive.File} docxFile
   * @param {GoogleAppsScript.Drive.Folder} folder
   * @param {string} baseName  desired name for the converted Google Doc
   * @return {{id: string, url: string}}
   */
  _convertDocxToGoogleDoc_(docxFile, folder, baseName) {
    const apiUrl = 'https://www.googleapis.com/drive/v3/files/' +
                   docxFile.getId() + '/copy';

    const response = UrlFetchApp.fetch(apiUrl, {
      method:      'post',
      contentType: 'application/json',
      headers:     { Authorization: 'Bearer ' + ScriptApp.getOAuthToken() },
      payload:     JSON.stringify({
        name:     baseName,
        parents:  [folder.getId()],
        mimeType: MimeType.GOOGLE_DOCS,
      }),
      muteHttpExceptions: true,
    });

    const code = response.getResponseCode();
    ErrorHandler.assert(
      code === 200,
      'Drive API files.copy returned HTTP ' + code + ': ' +
      response.getContentText().slice(0, 300)
    );

    const body = JSON.parse(response.getContentText());
    return {
      id:  body.id,
      url: 'https://docs.google.com/document/d/' + body.id + '/edit',
    };
  },
};
