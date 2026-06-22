# Expense Tracker Automation

**Status:** 🔜 Planned

## Business Problem

Small-business bookkeeping (and personal finance tracking) often means manually copying transactions from bank/credit statement exports into a ledger spreadsheet every month — tedious and error-prone, with category totals computed by hand.

## Objective

Build a Google Apps Script tool that ingests a bank statement export (CSV), auto-categorizes transactions using rule-based matching, appends them to a running ledger, and generates a monthly summary report — automatically, on a schedule.

## Planned Tech Stack

- Google Apps Script, Google Sheets API
- JavaScript (Apps Script runtime)
- Time-driven triggers for scheduled monthly reports

## Planned Deliverables

- [ ] CSV import + parsing
- [ ] Rule-based auto-categorization (merchant name → category mapping, editable by the user)
- [ ] Monthly summary sheet (spend by category, month-over-month trend)
- [ ] Scheduled trigger for automatic monthly report generation

---
Back to [Software Products](../README.md) · [main portfolio](../../README.md).
