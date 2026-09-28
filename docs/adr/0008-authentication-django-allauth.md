# 0008. Authentication with django-allauth (email + Google)

- Status: Proposed – awaiting developer review
- Date: 2026-09-28

## Context

We need signup, login, email verification, password reset and Google sign-in, in Polish, without
building security-sensitive flows ourselves.

## Decision

Use **django-allauth** (`account` + `socialaccount` with the Google provider):

- Email-only login (`ACCOUNT_LOGIN_METHODS = {"email"}`), no usernames.
- Email verification: mandatory in production, optional in development.
- Signup collects first and last name (`accounts.forms.SignupForm`).
- Google login is enabled automatically when `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are
  set (configured in settings, not in the database). Existing accounts are connected by verified
  email.
- allauth pages are rendered inside the site layout (`templates/allauth/layouts/base.html`).

## Consequences

- Well-maintained, secure flows with Polish translations for free; MFA and passkeys are available
  in allauth later if needed.
- Rate limiting of login attempts is handled by allauth defaults; review before launch.
