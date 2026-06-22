/**
 * @fileoverview Gemini-powered Professional Summary generation.
 *
 * Scoped to Professional Summary only — does not touch
 * DataAggregationService, CvGenerationService, TemplateEngine, or any
 * part of the core CV-document generation path.
 *
 * Requires GEMINI_API_KEY in Script Properties and the
 * script.external_request OAuth scope (already declared in appsscript.json).
 */

var GeminiService = {

  _MODEL_:   'gemini-2.5-flash',
  _API_URL_: 'https://generativelanguage.googleapis.com/v1beta/models/',

  /**
   * Generates an 80–120 word professional CV summary from supplied employee
   * data only. Never invents facts not present in cvData.
   *
   * @param {Object} cvData  { employeeName, role, yearsExperience, projects, skills }
   * @return {{success: boolean, summary?: string, error?: string}}
   */
  generateProfessionalSummary(cvData) {
    if (!cvData || !cvData.employeeName) {
      return { success: false, error: 'employeeName is required' };
    }

    const apiKey = PropertiesService.getScriptProperties().getProperty('GEMINI_API_KEY');
    if (!apiKey) {
      return { success: false, error: 'GEMINI_API_KEY is not configured in Script Properties' };
    }

    const prompt = this._buildPrompt_(cvData);
    const url = this._API_URL_ + this._MODEL_ + ':generateContent?key=' + apiKey;

    const requestBody = {
      contents: [{ parts: [{ text: prompt }] }],
      generationConfig: {
        temperature:     0.4,
        maxOutputTokens: 400,
      },
    };

    let response;
    try {
      response = UrlFetchApp.fetch(url, {
        method:             'post',
        contentType:        'application/json',
        payload:            JSON.stringify(requestBody),
        muteHttpExceptions: true,
      });
    } catch (err) {
      CvLogger.log('ERROR', 'GEMINI', cvData.employeeName,
        'UrlFetchApp threw: ' + err.message);
      return { success: false, error: 'Could not reach Gemini API: ' + err.message };
    }

    const code = response.getResponseCode();
    const raw  = response.getContentText();

    if (code !== 200) {
      CvLogger.log('ERROR', 'GEMINI', cvData.employeeName,
        'Gemini API returned HTTP ' + code, { body: raw.slice(0, 500) });
      return { success: false, error: 'Gemini API error (HTTP ' + code + ')' };
    }

    let parsed;
    try {
      parsed = JSON.parse(raw);
    } catch (err) {
      CvLogger.log('ERROR', 'GEMINI', cvData.employeeName,
        'Could not parse Gemini response JSON', { body: raw.slice(0, 500) });
      return { success: false, error: 'Could not parse Gemini response' };
    }

    const text = parsed.candidates &&
      parsed.candidates[0] &&
      parsed.candidates[0].content &&
      parsed.candidates[0].content.parts &&
      parsed.candidates[0].content.parts[0] &&
      parsed.candidates[0].content.parts[0].text;

    if (!text) {
      CvLogger.log('ERROR', 'GEMINI', cvData.employeeName,
        'Gemini response had no text', { body: raw.slice(0, 500) });
      return { success: false, error: 'Gemini did not return a summary' };
    }

    const summary = text.trim();
    CvLogger.log('INFO', 'GEMINI', cvData.employeeName,
      'Summary generated', { chars: summary.length });

    return { success: true, summary };
  },

  /**
   * Builds the generation prompt strictly from supplied cvData fields.
   * @private
   */
  _buildPrompt_(cvData) {
    const role  = cvData.role || 'Not specified';
    const years = cvData.yearsExperience ? cvData.yearsExperience + ' years' : 'Not specified';

    const skills = (cvData.skills || [])
      .map((s) => (s && (s.skill || s)) || '')
      .filter(Boolean)
      .join(', ') || 'None supplied';

    const projects = (cvData.projects || [])
      .map((p) => {
        const header = [p.name, p.client, p.role].filter(Boolean).join(' — ');
        return header + (p.responsibility ? ': ' + p.responsibility : '');
      })
      .filter(Boolean)
      .join('\n') || 'None supplied';

    return [
      'You are writing a Professional Summary for a corporate consulting CV.',
      '',
      'Employee data (use ONLY this — do not invent or assume anything not listed):',
      'Name: ' + cvData.employeeName,
      'Role: ' + role,
      'Years of experience: ' + years,
      'Skills: ' + skills,
      'Projects:',
      projects,
      '',
      'Write a Professional Summary with these strict requirements:',
      '- 80 to 120 words',
      '- Corporate consulting tone, suitable for a client-facing CV',
      '- Neutral CV register: no first person ("I"), no third person ("he/she/they")',
      '- Use only the data supplied above — never hallucinate employers, certifications, or skills not listed',
      '- Mention the experience level naturally, do not just restate the number',
      '- Highlight leadership, technical expertise, and domain knowledge where the data supports it',
      '- Return ONLY the summary text — no headings, no quotation marks, no markdown',
    ].join('\n');
  },
};
