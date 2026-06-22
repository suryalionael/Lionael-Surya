/**
 * @fileoverview Apps Script open trigger — installs the "CV Generator"
 * custom menu when the bound "CV Control Panel" spreadsheet is opened.
 *
 * This is the ONLY entry point HR users need to know about. They open the
 * spreadsheet and use the menu — no Apps Script editor access required.
 *
 * onOpen() must be a top-level function (not inside an object) so that Apps
 * Script recognizes it as the onOpen simple trigger.
 */

function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('CV Generator')
    .addItem('Generate Selected CVs',  'generateSelectedCvs')
    .addItem('Generate All CVs',       'generateAllCvs')
    .addSeparator()
    .addItem('Refresh Employee List',  'refreshEmployeeList')
    .addSeparator()
    .addSubMenu(
      ui.createMenu('CV Builder')
        .addItem('Load Employee Data',       'loadCvBuilderData')
        .addItem('Generate CV from Builder', 'generateCvFromBuilder')
    )
    .addSeparator()
    .addSubMenu(
      ui.createMenu('Tools')
        .addItem('Convert All DOCX to Google Docs', 'convertAllDocxToGoogleDocs')
    )
    .addSeparator()
    .addItem('Setup / Re-initialize',  'runSetup')
    .addToUi();
}
