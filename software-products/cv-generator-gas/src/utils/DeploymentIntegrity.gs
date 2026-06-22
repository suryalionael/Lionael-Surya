/**
 * @fileoverview Deployment integrity enforcer.
 *
 * Rule  9 — DeploymentIntegrity.check() verifies services, methods, forbidden
 *            legacy code, config version, and SetupController build path.
 * Rule 10 — Hard fail: locks the system on any failure; blocks CV generation.
 * Rule 11 — check() is called from onOpen(); assertNotLocked() is called at
 *            the entry point of every major service method.
 * Rule 12 — Drift → LOCKED MODE. Only ./deploy.sh can unlock (by producing
 *            a clean deployment that passes check() on the next onOpen()).
 *
 * LOCKED MODE:
 *   - DeploymentIntegrity.check() fails → sets Script Properties LOCK_KEY +
 *     LOCK_DETAIL → shows blocking alert.
 *   - DeploymentIntegrity.assertNotLocked() reads LOCK_KEY → throws "SYSTEM
 *     LOCKED" Error, caught by service try/catch → returns failure response.
 *   - check() passes on a good deploy → clears the lock.
 */

var DeploymentIntegrity = {

  LOCK_KEY:    'DEPLOYMENT_LOCKED',
  LOCK_DETAIL: 'DEPLOYMENT_LOCK_DETAIL',

  /**
   * Canonical manifest of every service that must exist after a correct deploy,
   * with the exact methods that are required and the legacy methods that must
   * NOT exist (their presence signals a stale or partial deployment).
   */
  MANIFEST: [
    {
      name:      'TemplateBuilderService',
      required:  ['createTemplate', 'buildAndRegister'],
      forbidden: [
        // Editor-only variants that were created without going through deploy.sh
        'buildTemplateFromScratch',
        'createTemplateInRoot',
        'prepareTemplate',
      ],
    },
    {
      name:      'CvGenerationService',
      required:  ['generateCvForEmployee'],
      forbidden: [
        // Legacy retry wrapper added directly in the editor — must not exist
        '_safeOpenDoc_',
      ],
    },
    {
      name:      'SetupController',
      required:  ['run', '_ensureTemplateDocument_', 'registerMasterTemplate'],
      forbidden: [],
    },
    {
      name:      'TemplateEngine',
      required:  ['populate'],
      forbidden: [],
    },
    {
      name:      'DataAggregationService',
      required:  ['buildEmployeeCvModel'],
      forbidden: [],
    },
    {
      name:      'CvLogger',
      required:  ['log'],
      forbidden: [],
    },
    {
      name:      'ErrorHandler',
      required:  ['assert', 'withErrorBoundary'],
      forbidden: [],
    },
  ],

  // ── Public API ─────────────────────────────────────────────────────────────

  /**
   * Full integrity check. Call from onOpen() after the menu is registered.
   *
   * Checks (Rule 9):
   *   1+2. All services and required methods exist.
   *   4.   SYSTEM_VERSION is defined (Config.gs present).
   *   5.   TemplateBuilderService has the exact required method set.
   *   6.   SetupController exposes the auto-build path (_ensureTemplateDocument_).
   *   7.   CvGenerationService has no legacy fallback code (_safeOpenDoc_, etc.).
   *
   * Note on Rule 9.3 (no unknown files in deployed target): GAS runtime has
   * no introspection API to list editor files. This check lives in deploy.sh
   * (clasp push --force guarantees clean state; grep guards against forbidden
   * source patterns before the push).
   *
   * @return {boolean} true if the deployment is valid
   */
  check() {
    const failures = [];

    // Rule 9.4 — SYSTEM_VERSION must be defined (Config.gs was deployed)
    if (typeof SYSTEM_VERSION === 'undefined') {
      failures.push('[MISSING CONSTANT] SYSTEM_VERSION — Config.gs not deployed');
    }

    // Rules 9.1 / 9.2 / 9.5 / 9.7 — service + method + forbidden checks
    // SERVICES uses property getters, so each access resolves the live object
    // at call time — no factory invocation, no load-order dependency.
    for (const entry of this.MANIFEST) {
      const svc = SERVICES[entry.name];

      if (!svc) {
        failures.push('[MISSING SERVICE] ' + entry.name);
        continue;
      }

      for (const m of entry.required) {
        if (typeof svc[m] !== 'function') {
          failures.push('[MISSING METHOD] ' + entry.name + '.' + m + '()');
        }
      }

      for (const f of entry.forbidden) {
        if (typeof svc[f] === 'function') {
          failures.push('[FORBIDDEN METHOD] ' + entry.name + '.' + f +
                        '() — stale / partial deploy detected');
        }
      }
    }

    // Rule 9.6 — SetupController must expose the template auto-build path
    if (typeof SetupController !== 'undefined' &&
        typeof SetupController._ensureTemplateDocument_ !== 'function') {
      failures.push('[BUILD PATH MISSING] SetupController._ensureTemplateDocument_()');
    }

    if (failures.length === 0) {
      this._clearLock_();
      try {
        CvLogger.log('INFO', 'DEPLOY_INTEGRITY', '-', 'Check passed',
          { version: SYSTEM_VERSION });
      } catch (_) {}
      return true;
    }

    this._setLock_(failures);
    this._showAlert_(failures);
    return false;
  },

  /**
   * Pre-execution guard. Throws immediately if the system is in LOCKED MODE.
   *
   * Place this as the FIRST statement inside the try-block of every major
   * service method (CvGenerationService, SetupController, etc.).
   * The thrown Error is caught by the existing service-level try/catch and
   * returned as a failure response — no special handling required.
   *
   * @throws {Error} "SYSTEM LOCKED — REDEPLOY REQUIRED" with failure details
   */
  assertNotLocked() {
    const props  = PropertiesService.getScriptProperties();
    const locked = props.getProperty(this.LOCK_KEY);
    if (!locked) return;

    const detail = props.getProperty(this.LOCK_DETAIL) || '';
    throw new Error(
      'SYSTEM LOCKED — REDEPLOY REQUIRED\n\n' +
      detail + '\n\n' +
      'Fix: run  ./deploy.sh  from the local repository,\n' +
      'then reload the spreadsheet.'
    );
  },

  // ── Private ────────────────────────────────────────────────────────────────

  _setLock_(failures) {
    const props = PropertiesService.getScriptProperties();
    props.setProperty(this.LOCK_KEY, 'true');
    props.setProperty(
      this.LOCK_DETAIL,
      'Deployment failures:\n' + failures.map((f) => '  ' + f).join('\n')
    );
    try { CvLogger.log('ERROR', 'DEPLOY_INTEGRITY', '-', 'LOCKED', { failures }); } catch (_) {}
  },

  _clearLock_() {
    const props = PropertiesService.getScriptProperties();
    props.deleteProperty(this.LOCK_KEY);
    props.deleteProperty(this.LOCK_DETAIL);
  },

  _showAlert_(failures) {
    const version = typeof SYSTEM_VERSION !== 'undefined' ? SYSTEM_VERSION : 'MISSING';
    const body = [
      'SYSTEM_VERSION : ' + version,
      '',
      'The following checks FAILED:',
      ...failures.map((f) => '  ' + f),
      '',
      'CV generation is BLOCKED until the deployment is fixed.',
      '',
      'Required action:',
      '  1. Fix only the LOCAL repository (never the Apps Script editor).',
      '  2. Run  ./deploy.sh  (clasp push --force).',
      '  3. Reload this spreadsheet.',
    ].join('\n');

    SpreadsheetApp.getUi().alert(
      'CV Generator — DEPLOYMENT INTEGRITY FAILURE',
      body,
      SpreadsheetApp.getUi().ButtonSet.OK
    );
  },
};
