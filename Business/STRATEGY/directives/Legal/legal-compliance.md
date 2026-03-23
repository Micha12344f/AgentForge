# Legal Compliance

> UK GDPR, FCA regulations, IB agreements, and data protection compliance for Hedge Edge.

## Compliance Domains

### 1. UK GDPR & Data Protection Act 2018
- All personal data processing must have a lawful basis
- Maintain a Data Processing Register (`resources/Legal/data-processing-register.md`)
- DSAR (Data Subject Access Requests) must be handled within 30 days (`resources/Legal/dsar-process.md`)
- Privacy policy must be accessible and up to date (`resources/Legal/privacy-policy-template.md`)
- **Audit tool**: `executions/Legal/gdpr_compliance_checker.py`

### 2. FCA Financial Promotions (COBS 4)
- All marketing material referencing financial products must be fair, clear, and not misleading
- Risk disclaimers required on all landing pages and emails (`resources/Legal/risk-disclaimers.md`)
- Financial promotions rules apply to prop firm hedging products (`resources/Legal/fca-financial-promotions.md`)
- **Audit tool**: `executions/Legal/financial_promotions_auditor.py`

### 3. IB Agreement Compliance
- Review all introducing broker agreements before signing (`resources/Legal/ib-agreement-checklist.md`)
- Understand regulatory landscape for prop firm partnerships (`resources/Legal/prop-firm-regulatory-landscape.md`)
- Terms of service must cover all product usage scenarios (`resources/Legal/terms-of-service-template.md`)

### 4. Legal Knowledge Base
- Feed all legal documents into NotebookLM via `executions/Legal/enrich_legal_notebook.py`
- Query legal questions via `executions/Legal/legal_query_engine.py`
- Interactive guide: `resources/Legal/legal_compliance_guide.ipynb`

## Compliance Cadence

- **Monthly**: GDPR audit via `gdpr_compliance_checker.py`
- **Per-campaign**: FCA promotions check via `financial_promotions_auditor.py`
- **Per-agreement**: IB agreement review via checklist
- **Ongoing**: Legal knowledge base enrichment
