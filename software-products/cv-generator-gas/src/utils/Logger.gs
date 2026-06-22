/**
 * @fileoverview Structured logger for the MSI CV Generator.
 *
 * CvLogger.log() writes to two sinks:
 *   1. console.log() — always available, visible in Apps Script "Executions"
 *      view and Stackdriver Logging.
 *   2. The "Logs" sheet in the bound Control Panel spreadsheet — visible to
 *      HR without opening any developer tooling. Best-effort; failures are
 *      swallowed so logging never aborts the caller's actual work.
 */

const CvLogger = {

  /**
   * Emits a structured log entry.
   *
   * @param {'INFO'|'WARN'|'ERROR'} level
   * @param {string} step   e.g. 'SETUP','AGGREGATION','GENERATION','BATCH',
   *                        'SPREADSHEET','EMPLOYEE_REPO','TEMPLATE','CONTROL_PANEL'
   * @param {string} employeeName  employee name, or '-' for non-employee-scoped entries
   * @param {string} message
   * @param {Object} [meta]  optional extra data; JSON-stringified in the Logs sheet
   */
  log(level, step, employeeName, message, meta) {
    const timestamp = new Date();
    const metaStr = meta ? JSON.stringify(meta) : '';
    const line = '[' + level + '][' + step + '][' + (employeeName || '-') + '] ' +
                 message + (metaStr ? ' ' + metaStr : '');

    console.log(line);

    try {
      ControlPanelRepository.appendLogEntry({
        timestamp,
        level,
        step,
        employeeName: employeeName || '-',
        message,
        meta: metaStr,
      });
    } catch (e) {
      // Swallow — logging must never abort the caller.
      console.error('Failed to write log entry to Logs sheet: ' + e.message);
    }
  },
};
