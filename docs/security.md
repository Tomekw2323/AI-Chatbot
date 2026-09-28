# Security

Status as of 2026-09-28. Decisions: ADR 0012–0016. Report vulnerabilities privately to the
maintainers (see "Missing" below: a `SECURITY.md` contact is still to be set).

## Threat model

### Assets

| Asset | Why it matters |
| --- | --- |
| User accounts (email, password hash, Google link) | Account takeover lets an attacker publish in someone's name |
| Personal data: names, contact details, inquiries, profiles | GDPR; reputational damage for specialists |
| Organization control (owner/admin roles) | Hijacked clinic pages and fake job offers |
| Moderation (Django admin, staff accounts) | Full read/write over all data |
| Platform reputation | A board full of scams or spam kills the product |

### Actors

- **Anonymous visitor / crawler**: reads public pages, may try guest contact.
- **Registered user**: legitimate or malicious (spammer, scammer posting fake rooms or jobs).
- **Organization member** trying to exceed their role.
- **Staff moderator**: trusted, but their account is a high-value target.
- **External attacker**: credential stuffing, bots, XSS/CSRF, dependency supply chain.

### Trust boundaries

Browser ↔ Render proxy (TLS) ↔ Django ↔ PostgreSQL; Django → SMTP provider, Google OAuth,
Cloudflare Turnstile. Everything from the browser, including `X-Forwarded-For`, is untrusted.

### Main threats (STRIDE-style)

| Threat | Example | Primary controls |
| --- | --- | --- |
| Spoofing | Credential stuffing, brute force | allauth rate limits, strong password validators, email verification, Google login |
| Tampering | Editing someone else's listing via its id (IDOR) | Object-level permission checks, CSRF |
| Repudiation | "I never accepted the terms" | `terms_accepted_at`, timestamps on all records |
| Information disclosure | Draft/flagged listings, emails in logs | `public()` querysets, 404 for invisible objects, no PII in logs |
| Denial of service / abuse | Spam inquiries, mass listing creation | Rate limits, Turnstile, verified email, reports + auto-hide |
| Elevation of privilege | Member acting as admin, self-verifying an organization | Role checks in `services.py`, form field allow-lists |

## Controls (OWASP Top 10 2021)

Every control listed here has automated tests (file in brackets).

### A01 Broken access control

- Object-level checks for every state-changing endpoint: `listings.permissions`,
  `organizations.services.can_manage_organization`. Edit/delete/publish/archive by a stranger or
  plain member returns 403; invisible objects return 404. [`listings/tests/test_security.py`
  `TestObjectLevelAuthorization`, `test_permissions.py`, `organizations/tests/*`]
- Forms use explicit field allow-lists; moderation fields (`is_flagged`, `status`, `author`,
  `is_verified`, `is_blocked`) cannot be mass-assigned. [`TestMassAssignment`,
  `test_verification_and_blocking_cannot_be_self_assigned`]
- Organization selector in the listing form only offers organizations the user manages.
  [`test_cannot_post_for_foreign_organization`]
- State changes are POST-only (`require_POST`), GET returns 405.
- Open redirects: `next` is validated with `url_has_allowed_host_and_scheme`. [`TestOpenRedirect`]
- Admin is staff-only and mounted at a secret path (`DJANGO_ADMIN_URL`). [`test_admin_*`,
  `test_production_refuses_guessable_admin_url`]

### A02 Cryptographic failures

- HTTPS everywhere in production (SSL redirect, HSTS 1 year incl. subdomains), `Secure`,
  `HttpOnly`, `__Host-` prefixed session and CSRF cookies. [`test_production_settings_are_hardened`]
- Passwords hashed with Django's PBKDF2 default. Secrets only from environment variables;
  production refuses weak or placeholder `DJANGO_SECRET_KEY`. [`test_production_requires_strong_secret_key`]

### A03 Injection (incl. XSS)

- ORM only; the single raw SQL statement (rate limiter) uses parameters.
- Templates autoescape; a test fails if any HTML template uses `|safe`, `mark_safe` or
  `{% autoescape off %}`. User content is plain text (no Markdown/HTML rendering).
  [`test_no_template_disables_autoescaping`, `TestXss`, `test_bio_is_escaped`]
- URL fields accept only http(s), so `javascript:` links are rejected. [`test_website_must_be_http`]
- Emails are plain text; no HTML emails built from user input. [`test_inquiry_email_is_plain_text`]
- CSP forbids inline scripts and `eval`, limiting the impact of any missed escaping.

### A04 Insecure design

- Abuse controls designed in: verified email before posting/contacting, rate limits, Turnstile for
  guests, user reports with automatic hiding, post-moderation (ADR 0012–0014).
- Guests can never choose the recipient of an inquiry; recipients see unverified senders.

### A05 Security misconfiguration

- `manage.py check --deploy --fail-level WARNING` runs in CI with production settings.
- CSP (django-csp), `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`, COOP, CORP,
  `Permissions-Policy`. [`TestHeaders`]
- `DEBUG` is always off outside `dev.py`; production refuses to start with a guessable admin path.

### A06 Vulnerable and outdated components

- `pip-audit --strict` in CI on the locked dependency set; Dependabot for uv, GitHub Actions and
  Docker base images (`.github/dependabot.yml`). Django 5.2 LTS.

### A07 Identification and authentication failures

- django-allauth: email verification (mandatory in production), enumeration prevention,
  rate limits on failed logins (10/min/IP, 5/15 min per account), signup and password reset.
  [`test_failed_logins_are_rate_limited`, `test_signup_is_rate_limited`]
- Password validators: minimum 10 characters, not common, not numeric, not similar to the user.
  [`test_password_validators_reject_weak_passwords`, `test_signup_rejects_weak_password`]
- Sensitive actions (data export, account deletion) require recent re-authentication.
  [`test_download_requires_recent_login`, `test_requires_recent_login`]

### A08 Software and data integrity failures

- Locked dependencies (`uv.lock`, `--frozen` in CI and Docker). Vendored HTMX file, no CDN
  scripts except Turnstile. CI on every push/PR; `main` protection recommended.

### A09 Logging and monitoring failures

- Structured logging to stdout; ids only, never emails or message bodies. POST parameters of
  inquiry views are marked sensitive so Django error reports do not include them. Auto-hidden
  listings log a warning.

### A10 SSRF

- The only outbound HTTP call made on user input is Turnstile verification to a fixed URL; no
  user-supplied URLs are fetched.

### CSRF

- Django CSRF middleware on all POSTs (HTMX sends the token via `hx-headers`), `SameSite=Lax`
  cookies, CSRF cookie `HttpOnly`. [`test_csrf_is_enforced`]

### Rate limits (current values, `config/settings/base.py`)

| Action | Limit |
| --- | --- |
| Signup | 10/h per IP |
| Failed login | 10/min per IP, 5/15 min per account |
| Password reset | 10/h per IP, 3/h per address |
| Create listing | 10/h and 50/day per user |
| Create organization | 5/day per user |
| Inquiry (member) | 10/h per user, 30/h per IP |
| Inquiry (guest, Turnstile) | 3/h and 10/day per IP |
| Report listing | 10/h per user |
| Data export | 5/h per user |

## GDPR (RODO) controls

- EU hosting (Render Frankfurt), no health data in Phase 1 (ADR 0009).
- Self-service data export (JSON) and account deletion with rules that never orphan an
  organization (ADR 0016). [`privacy/tests/test_privacy.py`]
- Consent to terms/privacy policy recorded at signup (`terms_accepted_at`).
- Retention: inquiries deleted after 365 days, rate-limit counters after 2 days (daily cron).
- Only strictly necessary cookies; no analytics or tracking, so no consent banner is required.
- Draft terms and privacy policy pages, clearly marked for legal review.

## File uploads (not implemented yet: plan)

Images (organization logos, profile photos, room photos) are planned. Requirements before
enabling any upload:

1. Store in EU object storage (S3-compatible, private bucket), never on the web container disk.
2. Accept only JPEG/PNG/WebP, max 5 MB, validated by decoding with Pillow (not by extension or
   `Content-Type`); re-encode server-side, strip EXIF (location data), cap dimensions.
3. Random object names (UUID); never use the client filename in paths.
4. Serve through signed URLs or a separate domain/CDN with `Content-Disposition` and
   `nosniff`, so an uploaded file can never execute in our origin; extend `img-src` in the CSP.
5. Rate limit uploads and count them against a per-user quota; delete files with the account.

Until then `DATA_UPLOAD_MAX_MEMORY_SIZE` is 1 MB and no view accepts files.

## Missing / known risks

| Item | Risk | Suggested next step |
| --- | --- | --- |
| MFA for staff | Stolen moderator password = full data access | Enable allauth MFA (TOTP/passkeys), require it for `is_staff` |
| Security contact | Researchers cannot report issues | Add `SECURITY.md` with an email and enable GitHub private vulnerability reporting |
| Error tracking / alerting | Attacks and failures go unnoticed | Sentry (EU region) with PII scrubbing |
| `TRUSTED_PROXY_COUNT` on Render | Wrong value = IP-based limits bypassable or everyone sharing one IP | Verify `X-Forwarded-For` format after the first deploy |
| Fixed-window limits | Bursts up to 2x at window edges | Acceptable; sliding windows or Redis later |
| Report griefing | Three accounts can hide a listing | Moderators review the queue; raise threshold or weight by account age |
| Email deliverability/spoofing | Our mails land in spam or get spoofed | SPF, DKIM, DMARC on the sending domain |
| Backups | Deleted accounts persist in backups until rotation | Document backup retention in the privacy policy |
| Legal texts | Draft terms/policy are not legally valid | Lawyer review before public launch |
| Penetration test | Unknown unknowns | External test before Phase 2 (payments) |
| `style-src 'unsafe-inline'` | CSS injection is possible if escaping ever fails | Move admin to nonces/hashes or a separate CSP for `/admin` |
