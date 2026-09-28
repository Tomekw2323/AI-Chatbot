# 0014. Rate limiting stored in PostgreSQL

- Status: Accepted (2026-09-28)
- Date: 2026-09-28

## Context

We need rate limits for login, signup, password reset, inquiries, reports and listing creation
that hold across several gunicorn workers and instances. The usual libraries
(django-ratelimit) require an atomic shared cache, i.e. Redis or Memcached, which is another
paid service to run for a very small app.

## Decision

- **Authentication flows** use django-allauth's built-in rate limits (`ACCOUNT_RATE_LIMITS`:
  signup 10/h per IP, failed logins 10/min per IP and 5/15 min per account, password reset
  10/h per IP and 3/h per address). They use Django's cache, configured as the
  **database cache** (`createcachetable`), which is shared by all workers. allauth tolerates
  its non-atomic increments; the limits are approximate but effective against brute force.
- **Application limits** use `apps.core.ratelimit`: fixed windows in the `RateLimitCounter`
  table, incremented with one atomic `INSERT ... ON CONFLICT DO UPDATE ... RETURNING`. Views use
  `@ratelimit("<scope>")` or `ratelimit.check()`; rates live in `settings.RATE_LIMITS`
  (`"10/h/user,30/h/ip"`). Exceeding a limit returns HTTP 429.
- The client IP comes from `X-Forwarded-For` only for the `TRUSTED_PROXY_COUNT` hops appended by
  our own proxy (Render: 1); forged entries to the left are ignored. allauth uses the same count.
- `daily_maintenance` deletes counters older than two days.

## Consequences

- No Redis; one extra small table, a few writes per protected POST.
- Fixed windows allow bursts at window edges (up to 2x the limit briefly). Acceptable here.
- If traffic grows or Redis is added for other reasons (task queue), switch the cache to Redis
  and consider django-ratelimit; the `@ratelimit(scope)` call sites stay the same.
