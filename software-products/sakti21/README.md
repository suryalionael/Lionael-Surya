# Sakti 21 — Indonesian PPh 21 Payroll Tax Calculator

**Multi-tenant SaaS payroll tax calculator** for Indonesian employee income tax (PPh 21), serving 64 companies from one shared instance.

Built in TypeScript + Next.js + PostgreSQL + Prisma. Originally deployed on Glide; rebuilt for production with proper auth, row-level multi-tenancy, and server-side PDF generation.

**[Live source repository →](https://github.com/suryalionael/sakti21)** (private during client use; access available on request)

---

## What It Does

Sakti 21 automates Indonesian PPh 21 employee income tax calculation for payroll teams managing multiple client companies:

1. **Employee master data** — bulk CSV import or manual entry
2. **Monthly salary input** — CSV import or manual entry
3. **Automatic PPh 21 calculation** — TER (effective rate) method for Jan–Nov, progressive Pasal 17 bracket reconciliation for Dec/termination. Supports **Gross** (employee-borne) and **Gross Up** (company-borne) tax modes
4. **Payroll reports** — monthly/annual per company, CSV export for all data
5. **Payslips** — on-screen and server-generated PDF per employee/month

---

## Business Problem

Indonesian payroll providers need to:
- Calculate monthly PPh 21 withholding under constantly-updated tax regulations
- Manage 60+ client companies from one system
- Generate compliant payslips and tax reports
- Import/export salary data in bulk

**Before Sakti 21:** Manual Excel calculations, error-prone, non-scalable.

**After Sakti 21:** Automated tax calculation with versioned tax reference data, multi-tenant architecture, bulk CSV workflows, and PDF payslip generation.

---

## Technical Highlights

- **Multi-tenant architecture** — row-level isolation via Prisma middleware
- **Versioned tax reference data** — PTKP rates, TER tables, and Pasal 17 brackets stored as effective-dated database rows, not hardcoded
- **CSV validation pipeline** — schema validation + referential integrity checks before import
- **Server-side PDF generation** — React component → Playwright headless render → PDF
- **Full test coverage** — unit tests for tax logic, integration tests for CSV import
- **Production-hardened** — accessibility audit, error boundaries, loading states, toast notifications

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 15, React, TypeScript, Tailwind CSS, shadcn/ui |
| **Backend** | Next.js API routes, NextAuth (auth) |
| **Database** | PostgreSQL 16, Prisma ORM |
| **PDF generation** | Playwright |
| **Deployment** | Docker Compose (local), Vercel/Railway (production candidates) |

---

## Architecture

**Data model:**
```
Company (tenant root)
  ├─ Branch
  ├─ Employee (master data)
  ├─ PayrollPeriod (month/year)
  │   └─ PayrollInput (salary + deductions per employee)
  │       └─ Pph21Calculation (tax result)
  └─ User (company-scoped access)

TaxReferenceData (versioned, effective-dated)
  ├─ PTKP rates (personal allowances)
  ├─ TER tables (monthly effective rates)
  └─ Pasal17Brackets (progressive annual rates)
```

**Tax calculation flow:**
1. Retrieve employee's taxable income (salary - deductions)
2. Apply PTKP allowances (marital status, dependents)
3. For Jan–Nov: TER lookup → monthly tax
4. For Dec/termination: Pasal 17 progressive brackets → annual tax → reconcile against YTD withholding
5. Store result + audit trail

---

## Key Features

- **CSV bulk import** for employees and monthly payroll inputs
- **Automatic tax calculation** with TER and Pasal 17 methods
- **Gross vs Gross Up** — toggle whether employee or company bears the tax
- **PDF payslips** — server-generated, per-employee/month
- **Role-based access** — company-scoped users via NextAuth
- **Audit trail** — all calculations stored with reference to tax rate versions used

---

## Sample Screenshots

*(Screenshots available in live repo; redacted here for client privacy)*

---

## Status

**Production-ready.** All phases 0–11 complete:
- ✅ Auth + multi-tenancy
- ✅ Company/branch/employee CRUD + CSV import
- ✅ Payroll period/input management + CSV import
- ✅ PPh 21 tax engine (TER + Pasal 17, Gross + Gross Up)
- ✅ Payroll reports + CSV export
- ✅ Payslip on-screen + PDF generation
- ✅ Accessibility/UX/production audit

Currently serving 64 companies. Source repo private during client use; access available for portfolio review on request.

---

## Why This Project Matters

1. **Real production use** — not a portfolio toy; actually deployed and serving paying clients
2. **Complex domain logic** — Indonesian tax law requires TER tables, progressive brackets, PTKP allowances, and annual reconciliation
3. **Multi-tenancy done right** — row-level isolation, not app-level filtering
4. **Full-stack ownership** — data model → business logic → UI → PDF generation → deployment
5. **Engineering rigor** — ADRs for every decision, full test coverage, documented audit trail

---

## Local Development

```bash
cp .env.example .env
docker compose up -d
npm install
npm run prisma:generate
npm run prisma:migrate
npm run db:seed
npm run dev
```

Other commands: `npm run lint`, `npm run typecheck`, `npm test`, `npm run build`

---

## Links

- **[Full documentation](https://github.com/suryalionael/sakti21/tree/main/docs)** (in live repo)
- **[Tax engine spec](https://github.com/suryalionael/sakti21/blob/main/docs/tax/tax-engine-overview.md)**
- **[Architecture decisions (ADRs)](https://github.com/suryalionael/sakti21/tree/main/docs/architecture/decisions)**
- **[Roadmap & phase delivery](https://github.com/suryalionael/sakti21/blob/main/docs/roadmap/roadmap.md)**

---

**Built:** May–Sep 2026  
**Status:** Production (64 companies)  
**Source:** Private repo; access available on request for portfolio review
