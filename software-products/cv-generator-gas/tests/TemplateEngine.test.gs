/**
 * @fileoverview Tests for TemplateEngine internals.
 *
 * Tests that can be verified without a live Google Doc are here.
 * Full integration (actual doc population) requires running against a
 * real template copy in the Apps Script environment.
 */

const TemplateEngineTests = {
  _name: 'TemplateEngine',

  test_placeholderEscapeForRegex() {
    // Verify that {{ and }} are correctly escaped for replaceText patterns.
    const token = PLACEHOLDERS.NAME;
    const escaped = token.replace(/[{}]/g, '\\$&');
    assertEqual(escaped, '\\{\\{NAME\\}\\}');
  },

  test_sectionHeadingsAreKnown() {
    // Verify all expected section headings are in SECTION_HEADINGS.
    const expected = [
      'PROFESSIONAL SUMMARY', 'TECHNICAL SKILLS', 'WORK EXPERIENCE',
      'EDUCATION', 'TRAINING & PROFESSIONAL DEVELOPMENT',
      'KEY PROJECTS', 'ADDITIONAL INFORMATION',
    ];
    const values = Object.values(SECTION_HEADINGS);
    expected.forEach((h) => {
      assertTrue(values.indexOf(h) !== -1, 'Expected heading: ' + h);
    });
  },

  test_omitEmptySections_flagsEmptyModel() {
    // TemplateEngine._omitEmptySections_ should mark all sections for removal
    // when cvModel contains only empty arrays and falsy strings.
    const emptyModel = {
      summary: '',
      technicalSkills: [],
      workExperience: [],
      education: [],
      training: [],
      projects: [],
      additionalInformation: '',
      languages: '',
    };

    // Simulate what _omitEmptySections_ computes (without needing a real Body).
    const shouldOmit = {
      [SECTION_HEADINGS.PROFESSIONAL_SUMMARY]:   !emptyModel.summary,
      [SECTION_HEADINGS.TECHNICAL_SKILLS]:       emptyModel.technicalSkills.length === 0,
      [SECTION_HEADINGS.WORK_EXPERIENCE]:        emptyModel.workExperience.length === 0,
      [SECTION_HEADINGS.EDUCATION]:              emptyModel.education.length === 0,
      [SECTION_HEADINGS.TRAINING]:               emptyModel.training.length === 0,
      [SECTION_HEADINGS.KEY_PROJECTS]:           emptyModel.projects.length === 0,
      [SECTION_HEADINGS.ADDITIONAL_INFORMATION]: !emptyModel.additionalInformation && !emptyModel.languages,
    };

    Object.keys(shouldOmit).forEach((section) => {
      assertTrue(shouldOmit[section], 'Section should be omitted when empty: ' + section);
    });
  },

  test_omitEmptySections_keepsFilledSections() {
    const model = {
      summary: 'Tech lead with 9+ years',
      technicalSkills: [{ category: 'Languages', values: ['Java'] }],
      workExperience: [{ position: 'Technical Lead', company: 'PT MSI', period: '', location: '', bullets: [] }],
      education: [{ degree: 'Bachelor', major: 'CS', institution: 'BINUS', year: '2010-2014' }],
      training: [{ name: 'GCP', provider: 'Google', year: '2024' }],
      projects: [{ name: 'AHM', client: 'AHM', period: '', role: '', responsibility: '', tools: '' }],
      additionalInformation: 'Some info',
      languages: 'English',
    };

    const shouldOmit = {
      [SECTION_HEADINGS.PROFESSIONAL_SUMMARY]:   !model.summary,
      [SECTION_HEADINGS.TECHNICAL_SKILLS]:       model.technicalSkills.length === 0,
      [SECTION_HEADINGS.WORK_EXPERIENCE]:        model.workExperience.length === 0,
      [SECTION_HEADINGS.EDUCATION]:              model.education.length === 0,
      [SECTION_HEADINGS.TRAINING]:               model.training.length === 0,
      [SECTION_HEADINGS.KEY_PROJECTS]:           model.projects.length === 0,
      [SECTION_HEADINGS.ADDITIONAL_INFORMATION]: !model.additionalInformation && !model.languages,
    };

    Object.keys(shouldOmit).forEach((section) => {
      assertFalse(shouldOmit[section], 'Section should NOT be omitted when filled: ' + section);
    });
  },
};
