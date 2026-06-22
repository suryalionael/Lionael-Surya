/**
 * @fileoverview CV generation controller.
 *
 * Provides the menu-bound global functions:
 *   generateSelectedCvs()  — generate CVs for checked employees only
 *   generateAllCvs()       — generate CVs for ALL discovered employees
 *   refreshEmployeeList()  — sync Control Panel rows with Drive folders
 *
 * These must be top-level (not inside an object) because Apps Script's
 * ui.createMenu().addItem(label, functionName) requires a global function
 * name as a string — it cannot reference object methods.
 *
 * The actual batch logic lives in CvController._runBatch_() to avoid
 * code duplication between the two generation entry points.
 */

// ── Global menu entry points ───────────────────────────────────────────────

/** Menu: Tools → Convert All DOCX to Google Docs */
function convertAllDocxToGoogleDocs() {
  const ui = SpreadsheetApp.getUi();
  let results;

  try {
    results = DocxMigrationService.migrateAll();
  } catch (err) {
    CvLogger.log('ERROR', 'DOCX_MIGRATION', '-',
      'Migration aborted: ' + err.message, { stack: err.stack || '' });
    ui.alert(
      'CV Generator — Migration Error',
      'Migration failed to start:\n\n' + err.message +
      '\n\nCheck the Logs sheet for details.',
      ui.ButtonSet.OK
    );
    return;
  }

  const converted = results.filter((r) => r.status === 'CONVERTED').length;
  const skipped   = results.filter((r) => r.status === 'SKIPPED').length;
  const failed    = results.filter((r) => r.status === 'ERROR').length;

  let message =
    'DOCX Migration Complete\n\n' +
    '✓ Converted:  ' + converted + '\n' +
    '⊖ Skipped:    ' + skipped + '  (Google Doc already exists)\n' +
    '✗ Failed:     ' + failed;

  if (failed > 0) {
    const failLines = results
      .filter((r) => r.status === 'ERROR')
      .map((r) =>
        '  • ' + r.employeeName + ' / ' + r.sourceDocxName +
        ' : ' + (r.error || 'unknown error')
      )
      .join('\n');
    message += '\n\nFailed files:\n' + failLines;
    message += '\n\nSee the Logs sheet for full details.';
  }

  ui.alert('CV Generator', message, ui.ButtonSet.OK);
}

/** Menu: Generate Selected CVs */
function generateSelectedCvs() {
  CvController.generateSelectedCvs();
}

/** Menu: Generate All CVs */
function generateAllCvs() {
  CvController.generateAllCvs();
}

/**
 * Menu: Refresh Employee List
 * Also called internally by generateAllCvs() to ensure the list is current.
 */
function refreshEmployeeList() {
  try {
    const discovered = EmployeeRepository.discoverEmployeeFolders();
    ControlPanelRepository.setEmployeeList(discovered.map((f) => f.name));
    CvLogger.log('INFO', 'CONTROL_PANEL', '-', 'Employee list refreshed',
      { count: discovered.length });
    SpreadsheetApp.getUi().alert(
      'CV Generator',
      'Employee list refreshed. Found ' + discovered.length + ' employee folder(s).',
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  } catch (err) {
    CvLogger.log('ERROR', 'CONTROL_PANEL', '-',
      'Failed to refresh employee list: ' + err.message);
    SpreadsheetApp.getUi().alert(
      'CV Generator — Error',
      'Could not refresh employee list: ' + err.message,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  }
}

/** Menu: CV Builder → Load Employee Data */
function loadCvBuilderData() {
  const ui = SpreadsheetApp.getUi();
  const checked = ControlPanelRepository.getCheckedEmployees();

  if (checked.length === 0) {
    ui.alert(
      'CV Builder',
      'No employee is selected.\n\n' +
      'Tick the "Generate" checkbox next to one employee in the Control Panel, ' +
      'then try again.',
      ui.ButtonSet.OK
    );
    return;
  }
  if (checked.length > 1) {
    ui.alert(
      'CV Builder',
      checked.length + ' employees are selected.\n\n' +
      'The builder works with one employee at a time. ' +
      'Uncheck all but one, then try again.',
      ui.ButtonSet.OK
    );
    return;
  }

  const employeeName = checked[0];
  try {
    CvLogger.log('INFO', 'CV_BUILDER', employeeName, 'Loading employee data for builder');
    const cvModel = DataAggregationService.buildEmployeeCvModel(employeeName);
    const counts  = CvBuilderRepository.loadEmployeeData(employeeName, cvModel);
    CvLogger.log('INFO', 'CV_BUILDER', employeeName, 'Builder data loaded', counts);
    SpreadsheetApp.getActiveSpreadsheet().toast(
      'Loaded ' + counts.projectCount + ' projects, ' +
      counts.skillCount + ' skills, ' +
      counts.trainingCount + ' training items for ' + employeeName + '.\n\n' +
      'Scroll right to the CV BUILDER zone to make your selections.',
      'CV Builder — Ready',
      8
    );
  } catch (err) {
    CvLogger.log('ERROR', 'CV_BUILDER', employeeName,
      'Failed to load builder data: ' + err.message, { stack: err.stack || '' });
    ui.alert(
      'CV Builder — Error',
      'Could not load data for ' + employeeName + ':\n\n' + err.message +
      '\n\nCheck the Logs sheet for details.',
      ui.ButtonSet.OK
    );
  }
}

/** Menu: CV Builder → Generate CV from Builder */
function generateCvFromBuilder() {
  const ui = SpreadsheetApp.getUi();

  let selections;
  try {
    selections = CvBuilderRepository.getSelections();
  } catch (err) {
    ui.alert(
      'CV Builder — Error',
      'Could not read builder selections:\n\n' + err.message,
      ui.ButtonSet.OK
    );
    return;
  }

  if (!selections) {
    ui.alert(
      'CV Builder',
      'No employee data is loaded.\n\n' +
      'Use CV Generator → CV Builder → Load Employee Data first.',
      ui.ButtonSet.OK
    );
    return;
  }

  // Recalculate and display current selection counts before generating.
  CvBuilderRepository.updateCounters(selections);
  SpreadsheetApp.flush();

  CvLogger.log('INFO', 'CV_BUILDER', selections.employeeName,
    'Generating CV from builder', {
      projects: selections.projectNames.length,
      skills:   selections.selectedSkills.length,
      training: selections.trainingNames.length,
    });

  const result = CvGenerationService.generateCvForEmployee(
    selections.employeeName, selections
  );

  if (result.success) {
    ui.alert(
      'CV Builder — Done',
      'CV generated for ' + result.employeeName + '.\n\n' +
      'Google Doc: ' + (result.docUrl  || '—') + '\n' +
      'PDF:        ' + (result.pdfUrl  || '—') + '\n' +
      '.docx:      ' + (result.docxUrl || '—'),
      ui.ButtonSet.OK
    );
  } else {
    ui.alert(
      'CV Builder — Generation Failed',
      'Could not generate CV for ' + result.employeeName + ':\n\n' +
      (result.error || 'unknown error') +
      '\n\nCheck the Logs sheet for details.',
      ui.ButtonSet.OK
    );
  }
}

// ── Controller object ──────────────────────────────────────────────────────

const CvController = {

  /**
   * Reads checked rows from the Control Panel and runs the generation
   * pipeline for each selected employee.
   */
  generateSelectedCvs() {
    const ui = SpreadsheetApp.getUi();
    const employees = ControlPanelRepository.getCheckedEmployees();

    if (employees.length === 0) {
      ui.alert(
        'CV Generator',
        'No employees are checked for generation.\n\n' +
        'Tick the "Generate" checkbox next to the employees you want to process, ' +
        'then try again.',
        ui.ButtonSet.OK
      );
      return;
    }

    this._runBatch_(employees, 'Generate Selected CVs');
  },

  /**
   * Discovers all employee folders, refreshes the Control Panel list, then
   * runs the generation pipeline for every employee.
   */
  generateAllCvs() {
    // Refresh the list first so newly-added employees are included in this run.
    try {
      const discovered = EmployeeRepository.discoverEmployeeFolders();
      ControlPanelRepository.setEmployeeList(discovered.map((f) => f.name));
    } catch (err) {
      CvLogger.log('WARN', 'BATCH', '-',
        'Employee list refresh failed before Generate All: ' + err.message);
    }

    const employees = ControlPanelRepository.getAllEmployeeRows().map((r) => r.name);

    if (employees.length === 0) {
      SpreadsheetApp.getUi().alert(
        'CV Generator',
        'No employee folders were found in the configured Drive repository.\n\n' +
        'Check that EMPLOYEE_FOLDER_ID in Config.gs points to the correct folder ' +
        'and that the script has access to it.',
        SpreadsheetApp.getUi().ButtonSet.OK
      );
      return;
    }

    this._runBatch_(employees, 'Generate All CVs');
  },

  /**
   * Shared batch runner. Iterates employees, calls
   * CvGenerationService.generateCvForEmployee() inside
   * ErrorHandler.withErrorBoundary() (defensive double-catch — the service
   * already self-catches, but this ensures no single employee can crash the
   * loop via an unexpected throw at any level), tallies results, writes the
   * Last Run Summary sheet, and shows a UI alert.
   *
   * @param {string[]} employees
   * @param {string} actionLabel
   */
  _runBatch_(employees, actionLabel) {
    const ui = SpreadsheetApp.getUi();

    CvLogger.log('INFO', 'BATCH', '-',
      actionLabel + ' started', { count: employees.length });

    const results = employees.map((employeeName) =>
      ErrorHandler.withErrorBoundary(
        () => CvGenerationService.generateCvForEmployee(employeeName),
        { step: 'GENERATION', employeeName }
      )
    );

    const successCount = results.filter((r) => r.success).length;
    const failureCount = results.length - successCount;

    ControlPanelRepository.writeRunSummary(results, actionLabel);

    CvLogger.log('INFO', 'BATCH', '-', actionLabel + ' finished',
      { total: results.length, successCount, failureCount });

    // ── Build summary dialog message ─────────────────────────────────────
    let message = actionLabel + ' complete.\n\n' +
      '✓ Success: ' + successCount + '\n' +
      '✗ Failed:  ' + failureCount + '\n' +
      'Total:     ' + results.length;

    if (failureCount > 0) {
      const failLines = results
        .filter((r) => !r.success)
        .map((r) => '  • ' + r.employeeName + ': ' + (r.error || 'unknown error'))
        .join('\n');
      message += '\n\nFailed employees:\n' + failLines;
      message += '\n\nSee the "Logs" and "Last Run Summary" sheet tabs for details.';
    } else {
      message += '\n\nGenerated CVs are saved in the "Generated CVs" Drive folder.';
    }

    ui.alert('CV Generator', message, ui.ButtonSet.OK);
  },
};
