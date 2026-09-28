# 0013. Guests may contact listing authors only through Cloudflare Turnstile

- Status: Accepted (2026-09-28)
- Date: 2026-09-28

## Context

Requiring an account to answer a job offer or ask about a room loses many legitimate contacts
(students, people browsing from a Facebook link). An unauthenticated email-sending form is a
spam and harassment vector, and a relay for sending arbitrary text to arbitrary recipients.

## Decision

- Guests can send an inquiry with name, email and message **only if Cloudflare Turnstile is
  configured** (`TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`). Without keys the form is not
  shown and the endpoint redirects to login: fail closed.
- The token is verified server-side (`core.captcha.verify`) against Cloudflare's `siteverify`
  endpoint with the client IP; any network error counts as failure.
- Guest inquiries are rate limited per IP (3/h, 10/day), stricter than member inquiries
  (10/h per user, 30/h per IP).
- Recipients see that a guest's email address is unverified; replies go to it via `Reply-To`,
  the recipient's own address is never revealed to the sender by the platform.
- The recipient address is always the listing's contact email; the guest cannot choose it.

Turnstile was chosen over reCAPTCHA/hCaptcha because it is free, has no puzzle for most users
and does not use tracking cookies, which keeps us free of a cookie-consent banner (ADR 0016).

## Consequences

- One more external dependency (Cloudflare) in the guest path, allowed in the CSP
  (`script-src` and `frame-src` `https://challenges.cloudflare.com`).
- Cloudflare becomes a data processor for guest IP addresses; list it in the privacy policy.
