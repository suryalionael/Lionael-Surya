/**
 * @fileoverview Tests for EmployeeRepository's label-based parser.
 *
 * Tests exercise _linesToExtraction_() directly with synthetic line arrays
 * modeled on the legacy CV format — no Drive access required.
 */

const EmployeeRepositoryTests = {
  _name: 'EmployeeRepository',

  _line_(text, isBold, isListItem) {
    return { text, isBold: isBold || false, isListItem: isListItem || false };
  },

  test_parsesBackground() {
    const lines = [
      this._line_('BACKGROUND', true),
      this._line_('Name\t:\t Kevin Januar Hasang'),
    ];
    const r = EmployeeRepository._linesToExtraction_(lines);
    assertEqual(r.name, 'Kevin Januar Hasang', 'Name should be extracted');
  },

  test_parsesTechnicalSkill() {
    const lines = [
      this._line_('TECHNICAL SKILL', true),
      this._line_('Databases : MySQL, PostgreSQL'),
      this._line_('Programming Languages : Java, PHP'),
    ];
    const r = EmployeeRepository._linesToExtraction_(lines);
    assertEqual(r.technicalSkills.length, 2);
    assertEqual(r.technicalSkills[0].category, 'Databases');
    assertDeepEqual(r.technicalSkills[0].values, ['MySQL', 'PostgreSQL']);
    assertEqual(r.technicalSkills[1].category, 'Programming Languages');
  },

  test_parsesTechnicalSkillSkipsEmptyValues() {
    const lines = [
      this._line_('TECHNICAL SKILL', true),
      this._line_('BI Tools : '),    // empty — should be skipped
      this._line_('Databases : MySQL'),
    ];
    const r = EmployeeRepository._linesToExtraction_(lines);
    assertEqual(r.technicalSkills.length, 1, 'Empty category should be skipped');
    assertEqual(r.technicalSkills[0].category, 'Databases');
  },

  test_parsesOtherSkillsLanguages() {
    const lines = [
      this._line_('Other skills:', true),
      this._line_('Languages: English, Indonesian'),
    ];
    const r = EmployeeRepository._linesToExtraction_(lines);
    assertEqual(r.languages, 'English, Indonesian');
  },

  test_parsesWorkExperience() {
    const lines = [
      this._line_('WORKING EXPERIENCES', true),
      this._line_('Mar 2017 – Now'),
      this._line_('TECHNICAL LEAD – PT. Magna Solusi Indonesia, Jakarta, Indonesia'),
      this._line_('Job description:'),
      this._line_('Design architect & develop application'),
      this._line_('Manage and coach developer teams'),
    ];
    const r = EmployeeRepository._linesToExtraction_(lines);
    assertEqual(r.workExperience.length, 1);
    const we = r.workExperience[0];
    assertEqual(we.position, 'TECHNICAL LEAD');
    assertEqual(we.company, 'PT. Magna Solusi Indonesia');
    assertTrue(we.location.indexOf('Jakarta') !== -1);
    assertEqual(we.bullets.length, 2);
  },

  test_parsesProjectExperience_inconsistentOrder() {
    // Golden reference note: Role may appear before or after Description.
    const lines = [
      this._line_('PROJECT EXPERIENCE', true),
      this._line_('AHM Sales Claim – Astra Honda Motor'),
      this._line_('Sept 2021 – Now'),
      this._line_('Role: System Analyst'),
      this._line_('Description: Application to assign and claim budgets.'),
      this._line_('Tools: Oracle Database, Java'),
    ];
    const r = EmployeeRepository._linesToExtraction_(lines);
    assertEqual(r.projects.length, 1);
    const p = r.projects[0];
    assertEqual(p.name, 'AHM Sales Claim');
    assertEqual(p.client, 'Astra Honda Motor');
    assertEqual(p.role, 'System Analyst');
    assertEqual(p.tools, 'Oracle Database, Java');
    assertTrue(p.isOngoing);
  },

  test_parsesEducation() {
    const lines = [
      this._line_('FORMAL EDUCATION'),
      this._line_('BINA NUSANTARA University (Jakarta, Indonesia) 2010 - 2014'),
      this._line_('Bachelor Degree (Faculty of Information Technology)'),
    ];
    const r = EmployeeRepository._linesToExtraction_(lines);
    assertEqual(r.education.length, 1);
    const edu = r.education[0];
    assertEqual(edu.institution, 'BINA NUSANTARA University');
    assertEqual(edu.year, '2010-2014');
    assertEqual(edu.degree, 'Bachelor Degree');
    assertEqual(edu.major, 'Faculty of Information Technology');
  },

  test_parsesNonFormalEducation() {
    const lines = [
      this._line_('NON–FORMAL/INFORMAL EDUCATION (Course/Seminar/Training/Workshop Attended)'),
      this._line_('Sept 2013 – Jan 2014'),
      this._line_('IBM DB2 Academic Associate'),
      this._line_('On Bina Nusantara University'),
    ];
    const r = EmployeeRepository._linesToExtraction_(lines);
    assertEqual(r.training.length, 1);
    const t = r.training[0];
    assertEqual(t.name, 'IBM DB2 Academic Associate');
    assertEqual(t.provider, 'Bina Nusantara University');
    assertEqual(t.year, '2014'); // extracted from "Jan 2014"
  },
};
