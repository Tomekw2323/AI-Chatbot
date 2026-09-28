# 0006. One `Listing` table for all listing kinds

- Status: Proposed – awaiting developer review
- Date: 2026-09-28

## Context

There are five listing kinds: job, internship, volunteering, job-seeking and room rental. They
share most attributes (title, description, author, organization, city, categories, lifecycle,
moderation) but have some kind-specific fields (salary vs. room price, area, availability).
Users expect one searchable board filtered by city, kind and category.

Options: (a) one table with nullable kind-specific columns; (b) a base table plus one-to-one
detail tables per kind (multi-table inheritance); (c) separate tables per kind.

## Decision

**(a) One `Listing` table** with a `kind` discriminator and nullable kind-specific columns.
Validation per kind lives in `Listing.clean()` (e.g. room rental requires a price) and
`ListingForm.clean()` (clears fields that do not apply to the chosen kind). DB check constraints
cover invariants that must never break (salary range, availability block times). Recurring room
availability is a child table `RoomAvailabilityBlock`.

## Consequences

- One queryset, one filter, one list template, one moderation queue, no joins for listing pages.
- Some columns are empty for some kinds (a few nullable columns is cheap in Postgres).
- If room rental grows much richer (Phase 2 calendar, bookings, payments), extract it to a
  `rooms` module with its own model referencing `Listing` or replacing it for that kind. The
  `kind` field and module boundaries keep that migration contained.
