/**
 * @fileoverview Centralized configuration for the MSI CV Generator.
 *
 * Static constants (known at deploy time) live in CONFIG_STATIC.
 * Runtime IDs created by Setup (template doc, output folder) are
 * persisted via PropertiesService and merged in by getConfig().
 *
 * No other file should reference raw ID strings or sheet names —
 * always use getConfig() or CONFIG_STATIC.
 */

const CONFIG_STATIC = Object.freeze({
  // ── Data sources (known at write-time) ───────────────────────────────────
  PROJECT_SPREADSHEET_ID: '1IM7ItINxVSP4hO9bAWDmWsumsMQ5ooC07vrbHYxtv5g',
  PROJECT_SHEET_GID: 1789711707, // "Form Responses 1" (Google Forms auto-assigned gid)
  EMPLOYEE_FOLDER_ID: '1u_A2vAhR2u5BeHYVLAD5K3DON2Eo4ht7',

  // ── Runtime IDs (null until Setup runs, then read from Script Properties) ─
  TEMPLATE_DOCUMENT_ID: null,
  GENERATED_CV_FOLDER_ID: null,

  // ── Control Panel spreadsheet sheet names ─────────────────────────────────
  CONTROL_PANEL_SHEET_NAME: 'CV Control Panel',
  LOGS_SHEET_NAME: 'Logs',
  SUMMARY_SHEET_NAME: 'Last Run Summary',

  // ── Drive folder / file names used during Setup ───────────────────────────
  CV_GENERATOR_FOLDER_NAME: 'CV Generator',
  GENERATED_CVS_FOLDER_NAME: 'Generated CVs',
  TEMPLATE_DOC_NAME: 'MSI CV Template',

  // ── Employee-repository file-name matchers (RegExp) ───────────────────────
  // Matches the "Employee Form" file inside each employee's Drive folder.
  EMPLOYEE_FORM_FILENAME_PATTERN: /employee\s*form/i,
  // Matches the "Existing CV" file (Google Doc or .docx) inside each folder.
  EXISTING_CV_FILENAME_PATTERN: /\bcv\b|curriculum\s*vitae/i,
  // Files matching this pattern are IGNORED (personal identity documents).
  IDENTITY_DOC_PATTERN: /\b(ktp|npwp|kk|birth\s*cert(?:ificate)?|family\s*card|akte|akta)\b/i,
});

// ─────────────────────────────────────────────────────────────────────────────
// Placeholder token registry — single source of truth for all {{...}} tokens.
// ─────────────────────────────────────────────────────────────────────────────
const PLACEHOLDERS = Object.freeze({
  // Top-level section markers (resolved in the template body):
  NAME:                   '{{NAME}}',
  POSITION:               '{{POSITION}}',
  YEARS_EXPERIENCE:       '{{YEARS_EXPERIENCE}}',
  SUMMARY:                '{{SUMMARY}}',
  LANGUAGES:              '{{LANGUAGES}}',
  ADDITIONAL_INFORMATION: '{{ADDITIONAL_INFORMATION}}',
  LAST_UPDATED:           '{{LAST_UPDATED}}',

  // Supported but unused by default (merged into TRAINING table per analysis §2.3):
  CERTIFICATIONS:         '{{CERTIFICATIONS}}',

  // Sentinel markers for dynamic section insertion points:
  TECHNICAL_SKILLS: '{{TECHNICAL_SKILLS}}', // replaced by table rows
  WORK_EXPERIENCE:  '{{WORK_EXPERIENCE}}',  // paragraph block sentinel
  EDUCATION:        '{{EDUCATION}}',        // replaced by table rows
  TRAINING:         '{{TRAINING}}',         // replaced by table rows
  PROJECTS:         '{{PROJECTS}}',         // paragraph block sentinel

  // Row-level tokens inside the Technical Skills table:
  SKILL_CATEGORY: '{{SKILL_CATEGORY}}',
  SKILL_VALUES:   '{{SKILL_VALUES}}',

  // Row-level tokens inside the Education table:
  EDU_DEGREE:      '{{EDU_DEGREE}}',
  EDU_MAJOR:       '{{EDU_MAJOR}}',
  EDU_INSTITUTION: '{{EDU_INSTITUTION}}',
  EDU_YEAR:        '{{EDU_YEAR}}',

  // Row-level tokens inside the Training & Professional Development table:
  TRAINING_NAME:     '{{TRAINING_NAME}}',
  TRAINING_PROVIDER: '{{TRAINING_PROVIDER}}',
  TRAINING_YEAR:     '{{TRAINING_YEAR}}',

  // Anchor paragraphs for Work Experience and Key Projects blocks:
  WORK_ENTRY:    '{{WORK_ENTRY}}',
  PROJECT_ENTRY: '{{PROJECT_ENTRY}}',
});

// Section heading texts as they appear in the generated document — used by
// TemplateEngine to locate and optionally remove entire sections.
const SECTION_HEADINGS = Object.freeze({
  PROFESSIONAL_SUMMARY:        'PROFESSIONAL SUMMARY',
  TECHNICAL_SKILLS:            'TECHNICAL SKILLS',
  WORK_EXPERIENCE:             'WORK EXPERIENCE',
  EDUCATION:                   'EDUCATION',
  TRAINING:                    'TRAINING & PROFESSIONAL DEVELOPMENT',
  KEY_PROJECTS:                'KEY PROJECTS',
  ADDITIONAL_INFORMATION:      'ADDITIONAL INFORMATION',
});

// ─────────────────────────────────────────────────────────────────────────────
// Runtime config accessor
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Returns merged config: static constants + any runtime IDs persisted by
 * Setup via Script Properties. Always call this instead of CONFIG_STATIC
 * directly when you need TEMPLATE_DOCUMENT_ID or GENERATED_CV_FOLDER_ID.
 *
 * @return {Object}
 */
function getConfig() {
  const props = PropertiesService.getScriptProperties().getProperties();
  return Object.assign({}, CONFIG_STATIC, {
    TEMPLATE_DOCUMENT_ID: props['TEMPLATE_DOCUMENT_ID'] || null,
    GENERATED_CV_FOLDER_ID: props['GENERATED_CV_FOLDER_ID'] || null,
  });
}

/**
 * Returns true if Setup has been run and the required runtime IDs are
 * available. Call this at the start of any generation function.
 *
 * @return {boolean}
 */
function isConfigured() {
  const cfg = getConfig();
  return !!(cfg.TEMPLATE_DOCUMENT_ID && cfg.GENERATED_CV_FOLDER_ID);
}
