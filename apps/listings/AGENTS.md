# apps/listings

Local contract. The map of every segment is `docs/segmenty.md`.

## Owns

The board: job, internship, volunteering, job-seeking, and room rental on one `Listing` table. Also `RoomAvailabilityBlock`, `Inquiry`, `ListingReport`, forms, filters, routes under `ogloszenia/`, plus `home` and `dashboard` included from `config.urls`. Commands: `daily_maintenance`, `expire_listings`, `prepare_demo`, `seed_demo`.

## Must not import

`apps.privacy`. Allowed: `apps.profiles`, `apps.organizations`, `apps.accounts`, `apps.core`.

Status changes go through `Listing.publish()`, `archive()`, and `expire()`. Public lists use `Listing.objects.public()`.

## Public surface

- `Listing.objects.public()`, `ListingQuerySet.due_to_expire`, `Listing.KIND_URL_SLUGS`, `InvalidTransitionError`
- `apps.listings.services.expire_due_listings`, `purge_old_inquiries`, `send_inquiry`, `report_listing`, `recipient_email_for`, `DuplicateReportError`
- `apps.listings.permissions.can_edit_listing`, `can_view_listing`, `can_post_for_organization`, `can_send_inquiry`, `can_report_listing`
- Template tags `organization_listings`, `personal_listings`, `kind_badge_class`, `query_transform`

Outside this app, `privacy.services` reads `Listing`, `Inquiry`, and `ListingReport`. `config.sitemaps` uses `Listing.objects.public()` and `Listing.KIND_URL_SLUGS`. `RoomAvailabilityBlock` is not imported outside this app.

## Replace without editing other apps

Room rental can later move to a `rooms` module (ADR 0006) while `Listing.objects.public()`, `publish`, `archive`, `expire`, and `KIND_URL_SLUGS` stay. Mail sending stays on `django.core.mail.EmailMessage`; the backend is settings (`EMAIL_URL`).

## How to test

```bash
uv run pytest apps/listings/tests
```
