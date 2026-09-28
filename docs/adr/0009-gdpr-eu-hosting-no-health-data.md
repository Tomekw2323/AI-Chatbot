# 0009. GDPR (RODO): EU hosting, no health data before Phase 3

- Status: Proposed – awaiting developer review
- Date: 2026-09-28

## Context

The platform processes personal data of Polish users (specialists, organization staff). Phase 3
(patient booking) would process **special-category data** under GDPR art. 9: the mere fact that
someone books a psychologist or psychiatrist reveals information about their health.

## Decision

- **Host application, database, backups and email provider in the EU/EEA** (Render Frankfurt,
  ADR 0011; choose an EU email provider).
- **MVP stores no health data**: no patient accounts, no reasons for visits, no notes. Inquiries
  are B2B (jobs, rooms). Profiles contain only data the specialist chooses to publish.
- Keep the patient-facing part separable: `SpecialistProfile.visible_to_patients` exists but is
  unused; bookings will live in a new module (possibly with a separate database/schema) so it can
  have stricter access control, encryption, audit logging and retention.
- Data minimisation now: collect only what features need; public contact data is opt-in per
  field; users can hide profiles.

## Consequences

- Before public launch: privacy policy, terms, processing register, data processing agreements
  with Render/email provider, account deletion flow, retention policy for inquiries.
- Before Phase 3: DPIA (art. 35), legal basis analysis (art. 9(2)(a) explicit consent or 9(2)(h)
  with specialists as controllers), likely a DPO, security review. Budget legal advice.
