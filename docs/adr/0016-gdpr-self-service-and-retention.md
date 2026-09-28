# 0016. GDPR self-service: export, deletion, retention, no tracking

- Status: Accepted (2026-09-28)
- Date: 2026-09-28

## Context

RODO/GDPR gives users the rights of access and portability (art. 15, 20) and erasure (art. 17),
and requires storage limitation and accountability for consent. Handling these by email does not
scale and is error-prone.

## Decision

- New top-level module **`apps.privacy`** (above all others, because it must see all personal
  data) with a "Moje dane" page:
  - **Export**: JSON download of account, email addresses, connected providers, profile,
    memberships, listings, inquiries sent and received, reports. POST only, requires recent
    re-authentication (allauth), rate limited, `Cache-Control: no-store`.
  - **Account deletion**: requires recent re-authentication and typing the account email.
    Deletes the user, profile, personal listings, memberships and sent inquiries. Organizations
    are never left unmanaged: sole-member organizations are deleted; ownership passes to the
    longest-standing admin; if only plain members remain, deletion is blocked with an explanation.
    Organization listings the user authored stay with the organization.
- **Consent record**: signup requires accepting the terms and acknowledging the privacy policy;
  the time is stored in `User.terms_accepted_at`.
- **Retention**: inquiries are deleted after `INQUIRY_RETENTION_DAYS` (default 365) by the
  daily cron; rate-limit counters after two days.
- **No tracking**: only strictly necessary cookies (session, CSRF), no analytics, no ad pixels,
  so no cookie banner is required. Adding analytics later requires a consent mechanism or a
  cookieless tool (e.g. Plausible, EU-hosted).
- **Logs**: never log message contents or email addresses; log object ids only. Views handling
  messages mark their POST parameters as sensitive so error reports do not contain them.
- Terms and privacy policy pages exist as clearly marked **drafts** for a lawyer to finalise.

## Consequences

- Most data-subject requests are self-service; staff handle only exceptions.
- Deleting an account is irreversible; backups still contain data until they rotate (document
  the backup retention of the hosting provider in the privacy policy).
