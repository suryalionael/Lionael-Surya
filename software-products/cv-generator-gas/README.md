# MSI Employee CV Generator

Automated, deterministic CV generation for PT Magna Solusi Indonesia (MSI). Pulls employee data from Drive and a Google Form Responses spreadsheet, populates an MSI-branded placeholder template, and exports a `.pdf` and `.docx` for each employee — all from a Google Sheets menu with no coding or Apps Script editor access required by HR.

**No AI. No external APIs.** Pure Google Apps Script + Drive + Docs + Sheets.

---

## Overview

```
Employee Data (Drive)           Project Experience (Sheets)
     │                                     │
     ▼                                     ▼
EmployeeRepository            SpreadsheetRepository
     │                                     │
     └──────────────┬──────────────────────┘
                    ▼
          DataAggregationService
          (per-field prioritization)
                    │
                    ▼
            TemplateEngine
          (populate template copy)
                    │
               ┌────┴────┐
               ▼         ▼
           PDF export  .docx export
               │         │
               └────┬────┘
                    ▼
         Generated CVs/<Employee Name>/
```

See [docs/architecture.md](docs/architecture.md) for the full Mermaid data-flow diagram.

---

## Architecture

```
src/
├── config/           Config.gs              — IDs, placeholders, filenames
├── controllers/      MenuController.gs      — onOpen() menu trigger
│                     CvController.gs        — generate selected / all; batch loop
│                     SetupController.gs     — idempotent initialization
├── services/         TemplateBuilderService.gs — builds the template Doc
│                     DataAggregationService.gs — source prioritization
│                     CvGenerationService.gs    — single-employee pipeline
├── repositories/     SpreadsheetRepository.gs  — project spreadsheet reader
│                     EmployeeRepository.gs     — Drive folder + Doc/Sheet parser
│                     ControlPanelRepository.gs — Control Panel / Logs / Summary sheets
├── templates/        TemplateEngine.gs      — placeholder sub + table/block cloning
└── utils/            Logger.gs  ErrorHandler.gs  DateUtils.gs  TextUtils.gs

tests/                runAllTests() + per-module *.test.gs
docs/                 architecture.md
```

**Data prioritization** (per field, not per document):  
Employee Form → Project Spreadsheet → Existing CV → default / omit

---

## Installation & Deployment

### Option A — Manual copy-paste (no Node/npm required)

1. Create a new **Google Sheet** and name it **"CV Control Panel"**.
2. Open **Extensions → Apps Script**.
3. In the Apps Script editor, click **Project Settings** (⚙️) → check **"Show "appsscript.json" manifest file in editor"**.
4. Replace the contents of `appsscript.json` with this repository's [`appsscript.json`](appsscript.json).
5. For each `.gs` file in `src/` (create in this order to match dependency flow):
   ```
   config/Config.gs
   utils/Logger.gs
   utils/ErrorHandler.gs
   utils/DateUtils.gs
   utils/TextUtils.gs
   repositories/ControlPanelRepository.gs
   repositories/SpreadsheetRepository.gs
   repositories/EmployeeRepository.gs
   services/TemplateBuilderService.gs
   services/DataAggregationService.gs
   services/CvGenerationService.gs
   templates/TemplateEngine.gs
   controllers/SetupController.gs
   controllers/CvController.gs
   controllers/MenuController.gs
   ```
   - Click **+** (Add a file) → **Script** → name it (e.g. `Config`) → paste the contents.
6. Optionally add the `tests/` files the same way if you want to run the test suite.
7. **Save** (Ctrl+S). Close the editor.
8. **Reload** the "CV Control Panel" spreadsheet — the **"CV Generator"** menu should appear.
9. Run **CV Generator → Setup / Re-initialize** to complete configuration.

### Option B — clasp (once Node.js ≥ 18 is installed)

```bash
npm install -g @google/clasp
clasp login
clasp create --type sheets --title "CV Control Panel" --rootDir ./src
# Copy the scriptId from the generated .clasp.json into your own (see .clasp.json.example)
clasp push
```

Then open the bound spreadsheet; the menu appears on the next open.

---

## Configuration & Setup Walkthrough

The first time you use the system (or after moving it to a new Drive account):

1. Open the **"CV Control Panel"** Google Sheet.
2. Click **CV Generator → Setup / Re-initialize**.
3. When prompted, grant the following OAuth permissions:
   - View and manage your Google Drive files
   - View and manage your Google Spreadsheets
   - View and manage your Google Docs documents
   - Connect to an external service (for PDF/docx export)
4. Setup automatically:
   - Creates **"CV Generator/Generated CVs/"** next to the spreadsheet in Drive
   - Builds the MSI-branded placeholder **CV Template** Google Doc
   - Creates the **Logs** and **Last Run Summary** sheet tabs
   - Populates the employee list from the Employee Data Repository
5. A confirmation dialog shows links to the template and output folder.

**Optional one-time customizations (after Setup):**
- Open the **CV Template** Doc → Insert the **MSI logo** into the page header (Insert → Headers & footers → Header). This customization persists across all generated CVs because the template is *copied* per employee, not regenerated.
- Go to **File → Page setup** → confirm **A4** paper size. Adjust if needed (see [Known Limitations](#known-limitations)).

---

## Folder Structure (in Drive)

```
CV Control Panel (Google Sheet — the bound spreadsheet)
│   ├── CV Control Panel  (sheet tab: Employee Name | Generate checkbox)
│   ├── Logs              (sheet tab: structured log history, last 2000 rows)
│   └── Last Run Summary  (sheet tab: most recent batch results)
│
CV Generator/               ← created next to the spreadsheet by Setup
├── MSI CV Template         ← placeholder Google Doc (built by Setup)
└── Generated CVs/
    ├── Kevin Januar H/
    │   ├── Kevin Januar H          (populated Google Doc)
    │   ├── Kevin Januar H.pdf
    │   └── Kevin Januar H.docx
    └── Krista Nadella/
        ├── Krista Nadella
        ├── Krista Nadella.pdf
        └── Krista Nadella.docx
```

---

## HR User Guide

### Generate CVs for selected employees
1. In the **CV Control Panel** tab, tick the **"Generate"** checkbox next to the employees you want.
2. Click **CV Generator → Generate Selected CVs**.
3. A progress summary appears when done. Generated files are in **Generated CVs/** in Drive.

### Generate CVs for all employees
1. Click **CV Generator → Generate All CVs**.
2. The system refreshes the employee list from Drive first, then processes everyone.
3. A summary dialog reports successes and failures. Failures for individual employees do not stop the others.

### Refresh the employee list
- Click **CV Generator → Refresh Employee List** after adding or renaming employee folders in Drive.
- Existing rows are never deleted (preserves checkbox states); new employees are appended with an unchecked box.

### Reading logs
- **Logs** tab: append-only log of every event (INFO / WARN / ERROR). Capped at 2000 rows; oldest trimmed automatically.
- **Last Run Summary** tab: snapshot of the most recent batch run with per-employee status, Doc URL, and PDF URL. Overwritten on each run (history is in Logs).

---

## Data Sources

### Project Experience Spreadsheet
- **ID:** `1IM7ItINxVSP4hO9bAWDmWsumsMQ5ooC07vrbHYxtv5g`
- **Sheet:** "Form Responses 1" (GID `1789711707`)
- **Format:** Wide — one row per employee submission, header names repeat ~11× for project blocks and ~13× for training/certification blocks
- **Column mapping:** Dynamic (no hardcoded indexes). Column groups are detected by finding each occurrence of the anchor column name.

### Employee Data Repository
- **Drive Folder ID:** `1u_A2vAhR2u5BeHYVLAD5K3DON2Eo4ht7`
- **Structure per employee:**
  ```
  <Employee Name>/
  ├── Employee Form   (Priority 1 — label-based parsing)
  ├── Existing CV     (Priority 3 — fallback parsing, same format)
  └── Supporting Docs (IGNORED — KTP/NPWP/KK/birth certs/family cards)
  ```
- Supported file types for parsing: **Google Docs** and **Google Sheets**.  
  Native `.docx` files stored without Google Docs conversion are logged as warnings and skipped.

---

## Known Limitations

| Limitation | Details |
|---|---|
| Section heading border | Apps Script's `DocumentApp` API does not support per-paragraph bottom borders. A thin 1×1 table with only a bottom border is used as a visual substitute (see `docs/architecture.md`). |
| A4 page size | `DocumentApp.create()` uses the Workspace locale default. After Setup, open the template Doc and verify **File → Page setup → A4**; correct if needed. The setting persists on all copies. |
| MSI logo in header | Cannot be inserted programmatically from Apps Script with full fidelity. Insert it manually once into the template Doc's header after Setup. |
| Native `.docx` Employee Forms | Files not converted to Google Docs format cannot be parsed. Google Workspace automatically converts uploaded Word files if "Convert uploads" is enabled in Drive settings. |
| Folder name matching | Employee names are matched case/whitespace-insensitively but must otherwise match between the Drive folder name and the spreadsheet's "Nama lengkap" column. Significant name variations (e.g., "Kevin H." vs "Kevin Januar Hasang") require a folder name update. |

---

## Troubleshooting

**"Setup has not been run" error**  
→ Run **CV Generator → Setup / Re-initialize** from the spreadsheet menu.

**PDF or .docx export fails (HTTP 400/403)**  
→ Check that the Apps Script project's OAuth token has the `script.external_request` scope (should be auto-granted on first run; revoke and re-authorize if missing).  
→ If your Google Workspace admin has blocked the `external_request` scope: enable the **Drive API v3 Advanced Service** (Apps Script editor → Services → Drive API) and replace `_exportDoc_()` in `CvGenerationService.gs` with:
```javascript
const blob = Drive.Files.export(docId, 'application/pdf');
```

**"Employee folder not found" in logs**  
→ The folder name in Drive must match the employee name in the Control Panel (case/whitespace-insensitive). Run **Refresh Employee List** to re-sync, then check for typos.

**Employee Form not found in folder**  
→ Check that the file name matches the `EMPLOYEE_FORM_FILENAME_PATTERN` regex in `Config.gs` (`/employee\s*form/i`). Rename the file in Drive or adjust the regex.

**Employee data looks wrong / empty sections in output**  
→ Check the **Logs** tab for `WARN` entries from `AGGREGATION` step — they report which data source was used for each field. Open the Employee Form in the affected folder and check the section labels match what `EmployeeRepository.gs` expects.

**Template is outdated after changes**  
→ Run **Setup / Re-initialize** after trashing the old template Doc in Drive — Setup detects the missing/invalid template ID and rebuilds it.

**Permission denied on Drive folder**  
→ The Apps Script runs under the account that authorized it. That account must have at least "Viewer" access to `EMPLOYEE_FOLDER_ID` and "Editor" access to `GENERATED_CV_FOLDER_ID`. Share the folders accordingly.

---

## Running the Test Suite

1. In the Apps Script editor, create `.gs` files for each file under `tests/` (if not already done — see Installation).
2. From the function dropdown at the top of the editor, select **`runAllTests`**.
3. Click **Run** (▶). Check **View → Logs** for `PASS` / `FAIL` lines.

Tests exercise pure logic (parsing, date handling, text normalization, data aggregation) using synthetic data — no Drive or Sheets access needed.

---

## Post-Deployment Validation Checklist

Run through this checklist the first time the system is deployed under an MSI Workspace account with access to real employee data:

- [ ] **Refresh Employee List** → confirm the "CV Control Panel" tab shows all expected employee names (matching actual Drive folder names).
- [ ] **Generate Selected CVs** for ONE employee → open the generated `.docx` and compare against the golden reference (`Assets/20260523_CV MSI Kevin Januar Hasang (1).docx`): section order, table structure, project sort order.
- [ ] **Employee Form file names** match `EMPLOYEE_FORM_FILENAME_PATTERN` (`/employee\s*form/i`) and `EXISTING_CV_FILENAME_PATTERN` (`/cv|curriculum\s*vitae/i`) in `Config.gs`. Adjust regexes if real file names differ.
- [ ] **Project Spreadsheet training-block column name** — `SpreadsheetRepository.gs` uses `/Nama\s+Training/i` to detect training group boundaries, matching both `"Nama Training / Sertifikasi (n)"` and numbered variants like `"(1)"`, `"(2)"`. Verify against the live sheet if uncertain.
- [ ] **PDF/docx export** succeeds (no HTTP error in Logs) — confirms `script.external_request` scope is allowed by the Workspace policy.
- [ ] **Template page size** is A4 (File → Page setup in Google Docs). If not, correct once and re-run Setup to rebuild (or manually fix the template).
- [ ] **Generate All CVs** with all employees → review Last Run Summary tab for any failures; investigate any `ERROR` entries in Logs.

---

## Portfolio Context

This project is mirrored here from its live repository: [github.com/suryalionael/cv-generator-gas](https://github.com/suryalionael/cv-generator-gas).

Back to [Software Products](../README.md) · [main portfolio](../../README.md).
