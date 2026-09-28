# 0015. HTTP security hardening: CSP, headers, cookies, admin path

- Status: Accepted (2026-09-28)
- Date: 2026-09-28

## Context

The site renders user-generated content and has an admin with full moderation power. Defence in
depth is cheap to configure now and hard to retrofit.

## Decision

- **Content Security Policy** with django-csp, enforced (not report-only) in every environment
  so violations show up in development: `default-src 'self'`; scripts only from self and
  Cloudflare Turnstile (no inline scripts, no `eval`); `frame-ancestors 'none'`;
  `object-src 'none'`; `base-uri 'self'`; `form-action 'self' https://accounts.google.com`.
  `style-src` allows `'unsafe-inline'` because Django admin uses inline style attributes; this is
  low risk while scripts are locked down. HTMX's inline indicator styles are disabled.
- **Headers**: `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy:
  strict-origin-when-cross-origin`, `Cross-Origin-Opener-Policy: same-origin`,
  `Cross-Origin-Resource-Policy: same-origin`, a restrictive `Permissions-Policy`.
- **Production**: HTTPS redirect, HSTS 1 year with subdomains (preload opt-in), `Secure` +
  `HttpOnly` cookies with the `__Host-` prefix, CSRF cookie `HttpOnly` (the token is rendered
  into pages instead), `SameSite=Lax` (Django default).
- **Admin** is mounted at `DJANGO_ADMIN_URL`; production refuses to start with `admin/`, an empty
  value, or a value without a trailing slash. This is obscurity on top of real controls (staff
  flag, strong passwords, login rate limits), not a replacement for them.
- **Secrets**: production refuses to start with a `DJANGO_SECRET_KEY` shorter than 50 characters
  or the `.env.example` placeholder. All secrets come from environment variables only.

## Consequences

- New third-party scripts or embeds must be added to the CSP deliberately.
- Tests assert the headers, the production settings and the startup refusals.
- Next step: MFA for staff (allauth MFA) before the admin team grows.
