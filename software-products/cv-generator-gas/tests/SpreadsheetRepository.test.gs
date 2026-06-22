/**
 * @fileoverview Tests for SpreadsheetRepository internals.
 *
 * These tests exercise the column-group detection algorithm and field
 * extraction using synthetic header + data row arrays (no live sheet needed).
 */

const SpreadsheetRepositoryTests = {
  _name: 'SpreadsheetRepository',

  // Synthetic header row: 1 employee-name col + 2 project blocks + 1 training block
  _makeHeaders_() {
    return [
      'Nama lengkap',             // col 0 — employee name
      'Nama klien',               // col 1 — project block 1 start
      'Nama project',
      'Periode Pengerjaan',
      'Peran Kamu',
      'Tech Stack dan tools yang digunakan',
      'Tanggung Jawab Utama dalam Project ini',
      'Pencapaian dalam project ini',
      'Nama klien',               // col 8 — project block 2 start
      'Nama project',
      'Periode Pengerjaan',
      'Peran Kamu',
      'Tech Stack dan tools yang digunakan',
      'Tanggung Jawab Utama dalam Project ini',
      'Pencapaian dalam project ini',
      'Nama Training / Sertifikasi (1)', // col 15 — training block 1 start
      'Tahun Training/Sertifikasi',
      'Output & Kompetensi Utama yang Dipelajari / Dikuasai',
      'Status Pembiayaan Training / Sertifikasi ini',
    ];
  },

  test_detectColumnGroups_findsProjectGroups() {
    const headers = this._makeHeaders_();
    const { projectGroups, trainingGroups, employeeNameColIdx } =
      SpreadsheetRepository._detectColumnGroups_(headers);

    assertEqual(employeeNameColIdx, 0, 'Employee name col');
    assertEqual(projectGroups.length, 2, 'Should find 2 project groups');
    assertEqual(trainingGroups.length, 1, 'Should find 1 training group');
  },

  test_detectColumnGroups_mapsFieldsCorrectly() {
    const headers = this._makeHeaders_();
    const { projectGroups } = SpreadsheetRepository._detectColumnGroups_(headers);

    // Group 1: starts at col 1
    const g1 = projectGroups[0];
    assertTrue('client' in g1, 'Group 1 should have client field');
    assertEqual(g1.client, 1, 'client should be col 1');
    assertEqual(g1.name, 2, 'project name should be col 2');
    assertEqual(g1.period, 3);
    assertEqual(g1.role, 4);
    assertEqual(g1.tools, 5);
    assertEqual(g1.responsibility, 6);
    assertEqual(g1.achievement, 7);

    // Group 2: starts at col 8
    const g2 = projectGroups[1];
    assertEqual(g2.client, 8);
    assertEqual(g2.name, 9);
  },

  test_extractProjectFromGroup_returnsProject() {
    const headers = this._makeHeaders_();
    const { projectGroups } = SpreadsheetRepository._detectColumnGroups_(headers);

    const row = new Array(19).fill('');
    row[0] = 'Kevin Januar Hasang';
    row[1] = 'Astra Honda Motor';           // client
    row[2] = 'AHM Sales Claim';             // name
    row[3] = 'Sept 2021 – Now';             // period
    row[4] = 'System Analyst';              // role
    row[5] = 'Oracle, Java';               // tools
    row[6] = 'Design architect';            // responsibility
    row[7] = 'Increased performance by 30%'; // achievement

    const project = SpreadsheetRepository._extractProjectFromGroup_(row, projectGroups[0]);
    assertNotNull(project);
    assertEqual(project.name, 'AHM Sales Claim');
    assertEqual(project.client, 'Astra Honda Motor');
    assertEqual(project.role, 'System Analyst');
    assertTrue(project.isOngoing, 'Should detect ongoing project');
    assertTrue(project.responsibility.indexOf('Increased performance') !== -1);
  },

  test_extractProjectFromGroup_returnsNullForEmptyGroup() {
    const headers = this._makeHeaders_();
    const { projectGroups } = SpreadsheetRepository._detectColumnGroups_(headers);

    const row = new Array(19).fill(''); // all empty
    const project = SpreadsheetRepository._extractProjectFromGroup_(row, projectGroups[0]);
    assertNull(project, 'Empty group should return null');
  },

  test_extractTrainingFromGroup_returnsTraining() {
    const headers = this._makeHeaders_();
    const { trainingGroups } = SpreadsheetRepository._detectColumnGroups_(headers);

    const row = new Array(19).fill('');
    row[15] = 'Professional Cloud Database Engineer';
    row[16] = '2024';
    row[17] = 'Google';
    row[18] = 'Mandiri';

    const training = SpreadsheetRepository._extractTrainingFromGroup_(row, trainingGroups[0]);
    assertNotNull(training);
    assertEqual(training.name, 'Professional Cloud Database Engineer');
    assertEqual(training.year, '2024');
    assertEqual(training.outputCompetency, 'Google');
  },
};
