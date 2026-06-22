# CV Format Analysis

Analysis of the three reference assets and the Project Experience data source, performed prior to implementation of the MSI Employee CV Generator (Google Apps Script).

Assets analyzed:

1. `Assets/TEMPLATE - CV Form MSI.docx` — labeled "template", but in practice a **filled CV in the legacy format** (contains Krista Nadella's data, no `{{PLACEHOLDER}}` tokens).
2. `Assets/CV MSI - Kevin Januar Hasang.docx` — legacy-format CV for Kevin (confirms the old structure).
3. `Assets/20260523_CV MSI Kevin Januar Hasang (1).docx` — **approved golden reference**, the target output format.
4. Project Experience Spreadsheet — "MSI Project Update 2026 (Responses)" (Google Form responses, spreadsheet ID `1IM7ItINxVSP4hO9bAWDmWsumsMQ5ooC07vrbHYxtv5g`).

---

## 1. Key Finding: There Is No Existing Placeholder Template

Assets #1 and #2 are both in the **same legacy format** — plain text sections, no MSI branding, no `{{PLACEHOLDER}}` tokens. Asset #1 is mislabeled as "template" but is actually an old filled CV (Krista Nadella's data).

**Implication:** A brand-new placeholder-based Google Doc template must be created from scratch, modeled on Asset #3's structure, styling, and branding (navy header block, section dividers, tables for Technical Skills/Education/Training). This template becomes `CONFIG.TEMPLATE_DOCUMENT_ID` and is a build deliverable, not a re-use of existing assets.

---

## 2. Old Format vs. New (Approved) Format

### 2.1 Legacy Format (Assets #1 & #2)

Plain, unbranded, sequential text sections:

| Section | Content |
|---|---|
| `BACKGROUND` | Name, Date of birth, Marital Status |
| `FORMAL EDUCATION` | Institution (year range) + Degree/major, free text |
| `NON-FORMAL/INFORMAL EDUCATION` | Bulleted list: date + training/seminar name |
| `TECHNICAL SKILL` | Fixed categories: Platform, Web/Application servers, Databases, BI Tools, Programming Languages — `Category : value` lines |
| `Other skills` | Languages (free text) |
| `WORKING EXPERIENCES` | Date range, `POSITION – Company, Location`, "Job description" bullets |
| `PROJECT EXPERIENCE` | `Project – Client`, date range, then bullets for Description/Role/Responsibility/Tools/Team Members (field order is **inconsistent** between entries — sometimes Role precedes Description, sometimes not) |

No header/footer branding, no color, no tables — everything is plain paragraphs and manual bullets.

### 2.2 Approved Format (Asset #3 — Golden Reference)

Branded, structured, table-driven:

| Section | Layout |
|---|---|
| **Header block** | Single-row, 2-column table with `1B3A6B` (MSI navy) fill, white borders. Cell 1: Name (26pt, bold), Position (14pt), "`N+ Years of Experience`" (smaller). Cell 2 currently empty (reserved space / potential logo). Document header (`header1.xml`) also contains an embedded image object (MSI logo). |
| **PROFESSIONAL SUMMARY** | Heading styled `1B3A6B`, bold, 11pt, with bottom border rule. Paragraph of narrative text (2–4 sentences). |
| **TECHNICAL SKILLS** | 2-column table, **no header row**. Each row: `Category Name` \| `: comma-separated values`. Categories are **dynamic** — Kevin's are Languages/Frameworks/Databases/Cloud & Infrastructure/Monitoring & Observability, but another employee could have different categories (e.g., Platform, BI Tools). |
| **WORK EXPERIENCE** | Repeating block, no table. Per entry: Position (bold), then `Company \| Period \| Location` line, then bulleted responsibilities (native Word numbering, not unicode bullets). Reverse chronological. |
| **EDUCATION** | Table with header row: `Degree \| Major / Field of Study \| Institution \| Year`. One data row per education record. |
| **TRAINING & PROFESSIONAL DEVELOPMENT** | Table with header row: `Training / Course Name \| Provider / Organizer \| Year`. One row per training/certification — **certifications are merged into this table** (e.g., "Professional Cloud Database Engineer" appears here with an empty Provider cell). |
| **KEY PROJECTS** | Repeating block, no table. Per entry: `Project Name \| Client/Industry \| Period` (bold), then `Role:`, `Responsibility:`, `Tools:` lines. Reverse chronological (newest first), matches the spec's sort rule. |
| **ADDITIONAL INFORMATION** | Free text: Languages line, "Document Control: Last Updated on `<Month, Year>`" line. |

**Formatting standards extracted:**
- Page size A4 (`11906 x 16838` twips), margins ≈0.7–0.79in (`1134/1009/1009/1009`).
- Brand color: `#1B3A6B` (navy) for name, section headings, header block fill.
- Section headings: bold, 11pt (`sz=22`), color `1B3A6B`, single bottom border (`sz=12`).
- Name: 26pt (`sz=52`). Position subtitle: 14pt (`sz=28`).
- Lists use native Word numbering (`numPr` + `numbering.xml`) — **never literal "•" characters**.
- Document has a custom header (logo) and footer.

### 2.3 Section Discrepancy vs. Spec

The task spec lists 9 sections including a standalone **Certifications** section. The golden reference has **8 sections** and folds certifications into "Training & Professional Development". The Project Update spreadsheet's source data also bundles training and certification responses together ("Training & Certification Update").

**Resolution:** Implement `{{CERTIFICATIONS}}` as a supported placeholder (per spec, for future-proofing), but the generated template's default body merges training and certification records into the single "Training & Professional Development" table, matching the approved reference. If a future template revision adds a distinct Certifications table, the placeholder is already wired and the repository layer already tags each record's type (`training` vs `certification`) via the "Status Pembiayaan" / category fields so it can be split later without re-deriving data.

---

## 3. Project Experience Spreadsheet Structure

Sheet: **"Form Responses 1"** (a Google Form responses sheet; its internal sheet ID is the `gid=1789711707` from the provided URL — Google Forms assigns a non-zero gid to the responses sheet it creates, so this is the correct/only sheet to read).

### 3.1 Wide, Repeating-Block Layout

This is **not** a normalized one-row-per-project sheet. Each form submission is one row, and the header row contains the **same column names repeated ~11 times** (one block per project an employee can report) followed by **~13 repeated blocks for training/certification records**. Example header fragment (block repeats):

```
Nama lengkap | Nama klien | Nama project | Nama modul yang dikerjakan | Periode Pengerjaan |
Peran Kamu | Tech Stack dan tools... | Tanggung Jawab Utama... | Pencapaian dalam project ini |
Lanjut ke project lainnya | <repeat from "Nama klien" for block 2> | ... (×11)
```

Followed by training blocks:

```
Nama Training / Sertifikasi (n) | Tahun Training/Sertifikasi |
Output & Kompetensi Utama yang Dipelajari/Dikuasai | Status Pembiayaan Training/Sertifikasi ini |
Lanjut ke training/sertifikasi lainnya | <repeat> (×~13)
```

### 3.2 Implication for "Dynamic Column Mapping"

Because header names **repeat**, a naive `header → index` map collapses to the *last* occurrence of each name. The repository must instead:

1. Read the header row once.
2. Detect repeating column groups by finding each occurrence of the group's anchor column (`Nama klien` for projects, `Nama Training / Sertifikasi (n)` for training).
3. Build a list of **column-group index ranges** (one per project slot / training slot), each internally mapped by header name (so column order within a group can still evolve safely).
4. For each response row, iterate the project groups in order; a group is "present" if its `Nama project` (or equivalent anchor) cell is non-empty — stop or skip empty groups rather than relying on the "Lanjut ke project lainnya" flag (observed values are inconsistent: "Ya", "Sudah selesai", "Tidak", or blank).
5. Same approach for training/certification groups, anchored on `Nama Training / Sertifikasi`.

This keeps the requirement "no hardcoded column indexes, map by header name" while correctly handling repeated headers — the mapping is **by header name within each detected group**, and group boundaries are derived dynamically from the header row, not hardcoded counts.

### 3.3 Field Mapping (Project Blocks → CV)

| Spreadsheet column (per block) | CV field | Notes |
|---|---|---|
| `Nama lengkap` | Join key → Employee | Used to match spreadsheet rows to an employee folder (flexible match: exact, trimmed, case-insensitive) |
| `Nama klien` | Project `Client` | |
| `Nama project` | Project `Name` | Also used as "industry" hint if no separate industry field exists |
| `Nama modul yang dikerjakan` | Project `Description` (module scope) | Combined with "Pencapaian" for the Responsibility/Description narrative |
| `Periode Pengerjaan` | Project `Period` → parsed into start/end | Free text like "Agustus 2020 - Desember 2025" or "Juli 2025 - Sekarang"; "Sekarang"/"Now"/"Present" → open-ended (treated as latest for sorting) |
| `Peran Kamu` | Project `Role` | |
| `Tech Stack dan tools...` | Project `Tools` | |
| `Tanggung Jawab Utama dalam Project ini` | Project `Responsibility` | |
| `Pencapaian dalam project ini` | Project `Achievement` (appended to Responsibility/Description) | |

### 3.4 Field Mapping (Training/Certification Blocks)

| Spreadsheet column (per block) | CV field |
|---|---|
| `Nama Training / Sertifikasi (n)` | `Training / Course Name` |
| `Tahun Training/Sertifikasi` | `Year` |
| `Output & Kompetensi Utama yang Dipelajari / Dikuasai` | Used as `Provider/Organizer` if it names an org, else folded into description |
| `Status Pembiayaan Training / Sertifikasi ini` | Internal tag (funded by company vs self) — not printed, but used to help distinguish certification vs informal training if needed later |

---

## 4. Employee Data Repository

Drive folder `1u_A2vAhR2u5BeHYVLAD5K3DON2Eo4ht7` ("2. Form Data Pokok Karyawan"), structure per spec:

```
Employee Folder (one per employee, e.g. "Aditya Angga", "Kevin Januar H", "Krista Nadella")
├── Employee Form              (primary source — Priority 1)
├── Existing CV                (legacy-format CV — Priority 3)
└── Supporting Documents        (ignored: KTP/NPWP/KK/birth certs/etc.)
```

> **Access note:** the Drive connector available during this analysis could read file/folder *metadata* (folder title confirmed: "2. Form Data Pokok Karyawan") and the Project spreadsheet's content, but could not enumerate this folder's children (empty result from both `parentId` and name-based search — likely a sharing/indexing limitation of the connected account, not a structural issue). The implementation is therefore built strictly from the spec's documented structure plus the legacy CV as a proxy for "Employee Form" content. **The discovery/parsing logic must be validated against real employee folders once the Apps Script is bound/run under an MSI Workspace account with proper folder access** — this is called out explicitly in the README's setup/validation checklist.

### 4.1 "Employee Form" Expected Content

Based on the legacy CV's `BACKGROUND` / `FORMAL EDUCATION` / `TECHNICAL SKILL` / `WORKING EXPERIENCES` sections (which were presumably sourced from such a form), the Employee Form is expected to provide:

- Full Name, Current Position, Date of birth, Marital status (not used in new CV)
- Years of experience (or derivable from earliest work experience date)
- Formal education (Institution, Degree/Major, Year range)
- Non-formal education / training / certifications
- Technical skills (by category)
- Languages
- Work experience (Position, Company, Period, Location, description bullets)
- Additional information

The Employee Form may be a Google Doc, Google Sheet (Form responses), or Google Form-linked spreadsheet — the repository implementation should handle Doc and Sheet mime types and extract key/value or tabular data generically (label-based extraction: look for known section headers/labels, similar to the legacy CV structure above).

### 4.2 "Existing CV" 

Legacy-format `.docx`/Google Doc per employee (Priority 3, lowest among data sources, formatting-only reference if needed — never used over Employee Form or Project Spreadsheet data).

---

## 5. Data Prioritization & Missing Data Handling

Per spec, for each CV field, sources are consulted in order: **Employee Profile Form → Project Experience Spreadsheet → Existing Employee CV → other files.** Applied per-field (not per-document) — e.g., Technical Skills may come from the Employee Form while Key Projects come from the spreadsheet.

| Placeholder | Primary source | Fallback(s) | If all missing |
|---|---|---|---|
| `{{NAME}}` | Employee Form | Folder name, Existing CV | Folder name (always available) |
| `{{POSITION}}` | Employee Form | Existing CV | `"-"` |
| `{{YEARS_EXPERIENCE}}` | Employee Form (explicit field) | Computed from earliest Work Experience start date | omit line |
| `{{SUMMARY}}` | Employee Form | — | omit section |
| `{{TECHNICAL_SKILLS}}` | Employee Form | Existing CV | omit section |
| `{{WORK_EXPERIENCE}}` | Employee Form | Existing CV | omit section |
| `{{EDUCATION}}` | Employee Form | Existing CV | omit section |
| `{{TRAINING}}` / `{{CERTIFICATIONS}}` | Employee Form | Project Spreadsheet (training/cert blocks) | omit section |
| `{{LANGUAGES}}` | Employee Form | Existing CV | `"Indonesian"` default |
| `{{PROJECTS}}` | Project Experience Spreadsheet | Existing CV ("PROJECT EXPERIENCE" section) | omit section |
| `{{ADDITIONAL_INFORMATION}}` | Employee Form | — | omit section |
| `{{LAST_UPDATED}}` | Generated at run time | — | current date |

**Rule:** an omitted section means the entire heading + body block is removed from the generated document (no empty headings, no "N/A" placeholders left visible), to keep output clean across employees with incomplete records. This is implemented by structuring the template so each section lives in its own paragraph range that the template engine can delete wholesale when the corresponding data array is empty.

---

## 6. Dynamic Section Requirements (carried into design)

- **Technical Skills**: arbitrary number of category rows (not fixed to Kevin's 5 categories).
- **Work Experience**: arbitrary number of entries, each with arbitrary bullet count.
- **Education**: arbitrary number of rows.
- **Training & Certifications**: arbitrary number of rows, merged from Employee Form + spreadsheet, de-duplicated by (name, year).
- **Key Projects**: arbitrary number, sorted by End Date desc, then Start Date desc, "Sekarang/Now/Present" treated as latest.
- All of the above implemented via **table-row cloning** (Education/Training/Technical Skills tables) and **paragraph-block cloning** (Work Experience/Key Projects entries) in the template engine, never fixed-size placeholders.

---

## 7. Summary of Build Implications

1. **Create a new placeholder-based Google Doc template** replicating Asset #3's branding/layout (navy header block `#1B3A6B`, section heading style with bottom border, 3 tables for Technical Skills/Education/Training, repeating blocks for Work Experience/Key Projects) — this becomes `CONFIG.TEMPLATE_DOCUMENT_ID`.
2. **Spreadsheet repository must implement repeating-column-group detection**, not a flat header map.
3. **Employee repository must parse the "Employee Form"** generically (label/key-value + tabular extraction), with the legacy CV format as the field-name vocabulary reference.
4. **Section-level conditional rendering** (delete heading+body if data empty) is required for clean output across employees with varying data completeness.
5. **Folder-discovery and Employee Form parsing must be validated against real Drive data** post-deployment, since this analysis could not browse actual employee folders.
