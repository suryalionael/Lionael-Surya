/**
 * @fileoverview Error handling utilities for the MSI CV Generator.
 *
 * ErrorHandler.withErrorBoundary() is the batch-continue primitive: it wraps
 * any per-employee pipeline call so a single employee's failure never aborts
 * the rest of the batch.
 *
 * ErrorHandler.assert() is the precondition checker: it throws a descriptive
 * Error that propagates to the nearest CvGenerationService try/catch, which
 * converts it to a per-employee failure result without crashing the batch.
 */

const ErrorHandler = {

  /**
   * Executes `fn` and catches any thrown Error, converting it into a
   * normalized failure result. If `fn` already returns a `{success, ...}`
   * object (as CvGenerationService.generateCvForEmployee does, since it
   * self-catches), that object passes through unchanged on success.
   *
   * @param {function(): Object} fn  zero-arg function to execute
   * @param {{step: string, employeeName: string}} context  for logging
   * @return {Object}  either fn()'s return value or
   *                   {success: false, employeeName, error: string}
   */
  withErrorBoundary(fn, context) {
    try {
      return fn();
    } catch (err) {
      CvLogger.log(
        'ERROR',
        context.step || 'UNKNOWN',
        context.employeeName || '-',
        'Unhandled exception: ' + err.message,
        { stack: err.stack || '' }
      );
      return {
        success: false,
        employeeName: context.employeeName || '-',
        error: err.message,
      };
    }
  },

  /**
   * Throws a descriptive Error if `condition` is falsy. Used for
   * precondition checks (missing folder, template, etc.) that should abort
   * the CURRENT employee's pipeline but are caught before reaching the
   * batch loop.
   *
   * @param {*} condition
   * @param {string} message
   * @throws {Error}
   */
  assert(condition, message) {
    if (!condition) throw new Error(message);
  },
};
