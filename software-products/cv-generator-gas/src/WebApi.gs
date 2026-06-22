/**
 * @fileoverview HTTP API layer for the MSI CV Engine web dashboard.
 *
 * Core engine files (DataAggregationService, CvGenerationService, etc.) are
 * NOT modified here.
 *
 * DEPLOYMENT:
 *   Deploy → New deployment → Web App
 *   Execute as: Me | Who has access: Anyone with Google Account
 *   Paste the /exec URL into dashboard/js/config.js → CONFIG.GAS_URL
 *
 * API surface:
 *   GET  ?action=getEmployees
 *   GET  ?action=getEmployeeData&name=<name>
 *   GET  ?action=getJobStatus&jobId=<id>      → {status, result?, error?}
 *   POST {action:"saveCVData",  payload:{…}}  → {success, savedAt}
 *   POST {action:"generateCV",  payload:{…}}  → {jobId, status:"QUEUED"}
 *   POST {action:"generateProfessionalSummary", payload:{…}} → {success, summary}
 *
 * Async job lifecycle (all stored in PropertiesService):
 *   QUEUED → PROCESSING → WRITING_DOC → DONE | FAILED
 *
 *   queueCvJob()         writes QUEUED  + payload
 *   processCvJobQueue()  transitions QUEUED→PROCESSING (under strict lock),
 *                        then PROCESSING→WRITING_DOC→DONE|FAILED
 *   getJobStatus()       reads status; auto-fails jobs stuck in PROCESSING > 10 min
 */

// ── HTTP handlers ─────────────────────────────────────────────────────────────

function doGet(e) {
  return _route_(e.parameter || {}, null);
}

function doPost(e) {
  let body = {};
  try { body = JSON.parse(e.postData.contents || '{}'); } catch (_) {}
  const params = Object.assign({}, e.parameter || {}, body);
  return _route_(params, body.payload || null);
}

function _route_(params, payload) {
  const action = String(params.action || '');
  let result;
  try {
    switch (action) {
      case 'getEmployees':   result = getEmployees();                  break;
      case 'getEmployeeData':result = getEmployeeData(params.name || params.employeeName || params.employee);   break;
      case 'saveCVData':     result = saveCVData(payload || params);  break;
      case 'generateCV':     result = queueCvJob(payload || params);  break;
      case 'getJobStatus':   result = getJobStatus(params.jobId);     break;
      case 'generateProfessionalSummary':
        result = GeminiService.generateProfessionalSummary(payload || params);
        break;
      default:               result = { error: 'Unknown action: ' + action };
    }
  } catch (err) {
    result = { error: err.message };
    CvLogger.log('ERROR', 'WEB_API', '-', action + ' threw: ' + err.message,
      { stack: err.stack || '' });
  }
  return ContentService
    .createTextOutput(JSON.stringify(result))
    .setMimeType(ContentService.MimeType.JSON);
}

// ── Standard endpoints ────────────────────────────────────────────────────────

function getEmployees() {
  const EXCLUDED = new Set(['0. RESIGN', '1. Internship', '2. Freelance-Outsource']);
  const folders = EmployeeRepository.discoverEmployeeFolders();
  return {
    employees: folders
      .map(f => f.name.trim())
      .filter(name => !EXCLUDED.has(name))
      .sort((a, b) => a.localeCompare(b)),
  };
}

function getEmployeeData(name) {
  if (!name) return { error: 'Employee name is required' };
  const model = DataAggregationService.buildEmployeeCvModel(name);
  return JSON.parse(JSON.stringify(model, (k, v) =>
    v instanceof Date ? v.toISOString() : v
  ));
}

function saveCVData(payload) {
  if (!payload || !payload.employeeName) return { error: 'employeeName is required' };
  PropertiesService.getScriptProperties()
    .setProperty('draft_' + payload.employeeName, JSON.stringify(payload));
  return { success: true, savedAt: new Date().toISOString() };
}

// ── Async CV job system ───────────────────────────────────────────────────────
//
// Storage: PropertiesService only (persistent, no expiry risk).
//   cvjob_status_<jobId>  — small status record (kept 1 h after completion)
//   cvjob_payload_<jobId> — full selection payload (deleted after processing)
//
// PropertiesService limits: 9 KB per property, 500 KB total.
// Typical CV payload is 3–6 KB — well within limits.
//
// Idempotency: only jobs in QUEUED state are picked up by the trigger.
// The transition QUEUED→PROCESSING happens atomically inside the strict
// LockService lock, so a double-fired trigger finds nothing to do.
//
// Stuck-job guard: getJobStatus() auto-reports PROCESSING > 10 min as FAILED.

const _JOB_STUCK_MS_   = 10 * 60 * 1000; // 10 min
const _JOB_RETAIN_MS_  = 60 * 60 * 1000; // 1 hour retention after completion
const _PAYLOAD_MAX_B_  = 8500;            // warn when payload approaches 9 KB limit

/**
 * Queues a CV generation job. Returns immediately with {jobId, status:"QUEUED"}.
 */
function queueCvJob(payload) {
  if (!payload || !payload.employeeName) {
    return { error: 'employeeName is required' };
  }

  const jobId = 'cvj_' + Utilities.getUuid().replace(/-/g, '').slice(0, 16);
  const props = PropertiesService.getScriptProperties();

  // Guard: warn if payload is approaching the 9 KB property limit
  const payloadStr = JSON.stringify(payload);
  if (payloadStr.length > _PAYLOAD_MAX_B_) {
    CvLogger.log('WARN', 'JOB_QUEUE', payload.employeeName,
      'Payload approaching 9 KB PropertiesService limit',
      { bytes: payloadStr.length });
  }

  // Persist payload and initial status (both survive GAS restarts)
  props.setProperty('cvjob_payload_' + jobId, payloadStr);
  props.setProperty('cvjob_status_'  + jobId, JSON.stringify({
    status:       'QUEUED',
    employeeName: payload.employeeName,
    queuedAt:     new Date().toISOString(),
  }));

  // Try to create a time-based trigger; fall back to synchronous processing if
  // ScriptApp.getProjectTriggers() is unavailable (e.g. scope not yet authorized).
  var triggerCreated = false;
  try {
    const hasTrigger = ScriptApp.getProjectTriggers()
      .some(t => t.getHandlerFunction() === 'processCvJobQueue');
    if (!hasTrigger) {
      ScriptApp.newTrigger('processCvJobQueue').timeBased().after(30 * 1000).create();
      triggerCreated = true;
    }
    CvLogger.log('INFO', 'JOB_QUEUE', payload.employeeName,
      'Job queued (async trigger)', { jobId, triggerCreated });
    return { jobId, status: 'QUEUED' };
  } catch (triggerErr) {
    // script.scriptapp scope not yet authorized — run synchronously in this request.
    CvLogger.log('WARN', 'JOB_QUEUE', payload.employeeName,
      'Trigger creation failed; falling back to synchronous processing: ' + triggerErr.message,
      { jobId });
    processCvJobQueue();
    const finalStatus = PropertiesService.getScriptProperties()
      .getProperty('cvjob_status_' + jobId);
    const finalJob = finalStatus ? JSON.parse(finalStatus) : { status: 'FAILED', error: 'Status lost' };
    return Object.assign({ jobId }, finalJob);
  }
}

/**
 * Returns the current status of a job.
 * Auto-detects jobs stuck in PROCESSING > 10 min and reports them as FAILED.
 */
function getJobStatus(jobId) {
  if (!jobId) return { error: 'jobId is required' };

  const props = PropertiesService.getScriptProperties();
  const raw   = props.getProperty('cvjob_status_' + jobId);
  if (!raw) return { status: 'NOT_FOUND', error: 'Job not found or already cleaned up' };

  const job = _parseJson_(raw);
  if (!job) return { status: 'FAILED', error: 'Corrupt status record' };

  // Stuck-job detection: PROCESSING > 10 min → report FAILED (trigger likely died)
  if (job.status === 'PROCESSING' && job.startedAt) {
    const ageMs = Date.now() - new Date(job.startedAt).getTime();
    if (ageMs > _JOB_STUCK_MS_) {
      const stuck = {
        status:      'FAILED',
        error:       'Job was still PROCESSING after 10 minutes — the trigger may have timed out. Please retry.',
        completedAt: new Date().toISOString(),
      };
      props.setProperty('cvjob_status_' + jobId, JSON.stringify(stuck));
      return stuck;
    }
  }

  // Auto-purge completed records older than 1 hour
  if ((job.status === 'DONE' || job.status === 'FAILED') && job.completedAt) {
    if (Date.now() - new Date(job.completedAt).getTime() > _JOB_RETAIN_MS_) {
      props.deleteProperty('cvjob_status_' + jobId);
    }
  }

  return job;
}

/**
 * Top-level trigger handler — must be a named top-level function for
 * ScriptApp.newTrigger to call it.
 *
 * Uses tryLock(0): if another execution holds the lock we exit immediately
 * rather than queueing behind it for 30 s. The winning run's finally block
 * cleans up all trigger entries, so the losing run leaves nothing behind.
 * Self-deletes all processCvJobQueue triggers in the finally block.
 */
function processCvJobQueue() {
  const lock = LockService.getScriptLock();

  if (!lock.tryLock(0)) {
    CvLogger.log('INFO', 'JOB_QUEUE', '-',
      'tryLock(0) failed — concurrent run in progress, exiting silently');
    return; // winning run's finally block will clean up trigger entries
  }

  try {
    // Unique ID for this execution — stamped on every claimed job for tracing.
    const runId = 'run_' + Utilities.getUuid().replace(/-/g, '').slice(0, 8);

    const props    = PropertiesService.getScriptProperties();
    const allProps = props.getProperties();

    // Collect status keys for QUEUED jobs only.
    const queuedKeys = Object.keys(allProps).filter(k => {
      if (!k.startsWith('cvjob_status_')) return false;
      const s = _parseJson_(allProps[k]);
      return s && s.status === 'QUEUED';
    });

    CvLogger.log('INFO', 'JOB_QUEUE', '-',
      'Trigger fired', { runId, queuedJobs: queuedKeys.length });

    queuedKeys.forEach(statusKey => {
      const jobId = statusKey.replace('cvjob_status_', '');

      // ── Atomic claim ─────────────────────────────────────────────────────────
      // Re-read inside the lock — if a concurrent run somehow already claimed
      // this job, its status will no longer be QUEUED, and we skip it.
      const fresh = _parseJson_(props.getProperty(statusKey));
      if (!fresh || fresh.status !== 'QUEUED') {
        CvLogger.log('INFO', 'JOB_QUEUE', jobId,
          'Skipped — no longer QUEUED', { runId, found: fresh && fresh.status });
        return;
      }

      // Stamp claimedBy + claimedAt so every stage is traceable to a runId.
      props.setProperty(statusKey, JSON.stringify({
        status:       'PROCESSING',
        employeeName: fresh.employeeName,
        claimedBy:    runId,
        claimedAt:    new Date().toISOString(),
        queuedAt:     fresh.queuedAt,
      }));

      // ── resultDocId idempotency guard ─────────────────────────────────────────
      // If this job was somehow re-queued after a prior successful run that
      // stored resultDocId, return the existing result without regenerating.
      if (fresh.resultDocId) {
        CvLogger.log('INFO', 'JOB_QUEUE', jobId,
          'resultDocId already set — skipping regeneration',
          { runId, resultDocId: fresh.resultDocId });
        _finalizeJob_(props, statusKey, {
          status:      'DONE',
          resultDocId: fresh.resultDocId,
          result:      fresh.result || {},
        });
        props.deleteProperty('cvjob_payload_' + jobId);
        return;
      }

      // ── Read payload ──────────────────────────────────────────────────────────
      const payloadRaw = props.getProperty('cvjob_payload_' + jobId);
      if (!payloadRaw) {
        _finalizeJob_(props, statusKey, {
          status: 'FAILED',
          error:  'Job payload missing from PropertiesService — storage may have been cleared.',
        });
        CvLogger.log('ERROR', 'JOB_QUEUE', jobId, 'Payload missing', { runId });
        return;
      }

      const payload = _parseJson_(payloadRaw);
      if (!payload) {
        _finalizeJob_(props, statusKey, { status: 'FAILED', error: 'Corrupt job payload' });
        return;
      }

      const name = payload.employeeName || jobId;
      CvLogger.log('INFO', 'JOB_QUEUE', name, 'Generation starting', { runId });

      // ── Run CV generation ─────────────────────────────────────────────────────
      try {
        // WRITING_DOC: Drive I/O is about to begin.
        props.setProperty(statusKey, JSON.stringify({
          status:       'WRITING_DOC',
          employeeName: name,
          claimedBy:    runId,
          queuedAt:     fresh.queuedAt,
          updatedAt:    new Date().toISOString(),
        }));

        const r = CvGenerationService.generateCvForEmployee(name, payload);

        if (r.success) {
          // Extract Drive file ID from the doc URL so callers can use it as an
          // idempotency key on any future retry path.
          const docIdMatch = (r.docUrl || '').match(/\/d\/([a-zA-Z0-9_-]+)/);
          _finalizeJob_(props, statusKey, {
            status:      'DONE',
            resultDocId: docIdMatch ? docIdMatch[1] : null,
            result: {
              docUrl:  r.docUrl  || null,
              pdfUrl:  r.pdfUrl  || null,
              docxUrl: r.docxUrl || null,
            },
          });
        } else {
          _finalizeJob_(props, statusKey, {
            status: 'FAILED',
            error:  r.error || 'CvGenerationService returned success:false',
          });
        }

        CvLogger.log(r.success ? 'INFO' : 'ERROR', 'JOB_QUEUE', name,
          'Generation finished', { runId, success: r.success });

      } catch (err) {
        _finalizeJob_(props, statusKey, { status: 'FAILED', error: err.message });
        CvLogger.log('ERROR', 'JOB_QUEUE', name,
          'Generation threw: ' + err.message, { runId, stack: err.stack || '' });
      }

      // Free PropertiesService space — payload no longer needed.
      props.deleteProperty('cvjob_payload_' + jobId);
    });

  } finally {
    lock.releaseLock();
    // Delete ALL processCvJobQueue trigger entries (no-op if scope unavailable).
    try {
      ScriptApp.getProjectTriggers()
        .filter(t => t.getHandlerFunction() === 'processCvJobQueue')
        .forEach(t => ScriptApp.deleteTrigger(t));
    } catch (_) { /* script.scriptapp scope not authorized — triggers not in use */ }
  }
}

// ── Private helpers ───────────────────────────────────────────────────────────

/** Writes a terminal job status (DONE or FAILED) with a completedAt timestamp. */
function _finalizeJob_(props, statusKey, fields) {
  props.setProperty(statusKey, JSON.stringify(
    Object.assign({ completedAt: new Date().toISOString() }, fields)
  ));
}

/** Safe JSON parse — returns null on any error instead of throwing. */
function _parseJson_(raw) {
  try { return JSON.parse(raw); } catch (_) { return null; }
}
