# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-16

### Added

**Config & Setup**
- `src/config/Config.gs` — `CONFIG_STATIC` constants (spreadsheet ID, Drive folder ID, sheet names, filename patterns), `PLACEHOLDERS` token registry, `SECTION_HEADINGS` map, `getConfig()` merging static config with Script Properties runtime IDs, `isConfigured()` guard
- `src/controllers/SetupController.gs` — idempotent `runSetup()`: creates/locates output folder hierarchy in Drive, builds/reuses the placeholder CV template Doc, initializes Control Panel sheets, syncs employee list; shows a confirmation dialog with links
- `src/services/TemplateBuilderService.gs` — programmatically builds the 8-section MSI-branded placeholder Google Doc (navy `#1B3A6B` header table, section headings with divider approximation, Technical Skills 2-col table, Education 4-col table, Training 3-col table, Work Experience and Key Projects sentinel paragraphs, Additional Information block)

**Utilities**
- `src/utils/Logger.gs` — `CvLogger.log()`: structured log entries to `console.log` + the "Logs" sheet in the Control Panel spreadsheet (best-effort, swallows sheet-write failures)
- `src/utils/ErrorHandler.gs` — `withErrorBoundary()` (batch-continue error wrapper), `assert()` (precondition checker)
- `src/utils/DateUtils.gs` — `parsePeriodString()` (Indonesian/English month names, "Sekarang"/"Now" ongoing detection, year-only ranges), `formatMonthYear()`, `extractYear()`, `yearsFrom()`
- `src/utils/TextUtils.gs` — `normalizeName()`, `namesMatch()`, `joinNonEmpty()`, `dedupeBy()`, `titleCase()`, `truncate()`

**Repositories**
- `src/repositories/ControlPanelRepository.gs` — manages CV Control Panel (additive employee list sync, checkbox data validation), Logs sheet (append-only, 2000-row cap, navy header), Last Run Summary sheet (cleared/rewritten per run, color-coded status)
- `src/repositories/SpreadsheetRepository.gs` — repeating column-group detection for the wide Google Form Responses layout (no hardcoded indexes); project extraction (period parsing, responsibility + achievement merge); training/certification extraction; single-execution result cache
- `src/repositories/EmployeeRepository.gs` — Drive folder discovery; Employee Form / Existing CV file location (skips identity documents: KTP/NPWP/KK/birth certs/family cards); label-based state machine parser for Google Doc and Google Sheet mime types using the legacy CV section vocabulary

**Template Engine**
- `src/templates/TemplateEngine.gs` — four-step population pipeline: (1) simple placeholder substitution via `Body.replaceText`, (2) table-row cloning via `TableRow.copy()` + `insertTableRow()` + row-scoped `replaceText`, (3) paragraph-block insertion via `body.insertParagraph()` and `body.insertListItem()` with native `GlyphType.BULLET`, (4) section omission (entire heading + content removed when data array is empty)

**Services**
- `src/services/DataAggregationService.gs` — per-field source prioritization (Employee Form → Spreadsheet → Existing CV → default/omit per `CV_FORMAT_ANALYSIS.md §5`); training merge + de-duplication by `(name, year)`; projects sorted reverse-chronologically (ongoing/Sekarang = latest); years-of-experience computed from earliest work start date when not explicit
- `src/services/CvGenerationService.gs` — single-employee pipeline: data aggregation → output folder preparation → template copy → template population → PDF export → `.docx` export via `UrlFetchApp + getOAuthToken()`; self-catches all errors; cleans up orphaned template copies

**Controllers**
- `src/controllers/MenuController.gs` — `onOpen()` trigger: installs "CV Generator" custom menu (Generate Selected CVs / Generate All CVs / Refresh Employee List / Setup / Re-initialize)
- `src/controllers/CvController.gs` — global wrapper functions (required for menu binding) + `CvController._runBatch_()`: iterates employees inside `ErrorHandler.withErrorBoundary`, writes Last Run Summary, shows detailed UI alert with per-employee failure list

**Tests**
- `tests/TestRunner.gs` — `runAllTests()` entry point and assertion helpers
- `tests/TextUtils.test.gs`, `tests/DateUtils.test.gs`, `tests/SpreadsheetRepository.test.gs`, `tests/EmployeeRepository.test.gs`, `tests/TemplateEngine.test.gs`, `tests/DataAggregation.test.gs` — test suites exercising pure logic without live Drive/Sheets access

**Documentation**
- `README.md` — overview, architecture, installation (manual copy-paste + optional clasp paths), configuration/setup walkthrough, folder structure, HR user guide, known limitations, troubleshooting
- `docs/architecture.md` — Mermaid data-flow diagram, layer responsibility table, section-omission model, template engine algorithm descriptions, known Apps Script API limitations table
- `CHANGELOG.md` (this file)
- `CV_FORMAT_ANALYSIS.md` — pre-implementation analysis of the three reference assets and the Project Experience spreadsheet (authoritative format/mapping reference, not modified post-analysis)
- `appsscript.json` — V8 runtime, `Asia/Jakarta` timezone, required OAuth scopes
- `.clasp.json.example` — template for future clasp users
- `.gitignore`
