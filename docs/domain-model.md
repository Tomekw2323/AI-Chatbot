# Domain model

## Entity-relationship diagram

```mermaid
erDiagram
    USER ||--o| SPECIALIST_PROFILE : "has (optional)"
    USER ||--o{ MEMBERSHIP : "has"
    ORGANIZATION ||--o{ MEMBERSHIP : "has"
    USER ||--o{ LISTING : "authors"
    ORGANIZATION |o--o{ LISTING : "published on behalf of"
    LISTING ||--o{ ROOM_AVAILABILITY_BLOCK : "room rentals only"
    LISTING ||--o{ INQUIRY : "receives"
    USER |o--o{ INQUIRY : "sends"

    VOIVODESHIP ||--o{ CITY : "contains"
    CITY ||--o{ ORGANIZATION : "located in"
    CITY ||--o{ SPECIALIST_PROFILE : "located in"
    CITY ||--o{ LISTING : "located in"
    SPECIALIZATION }o--o{ SPECIALIST_PROFILE : "tags"
    SPECIALIZATION }o--o{ LISTING : "categorizes"
    THERAPY_APPROACH }o--o{ SPECIALIST_PROFILE : "tags"

    USER {
        bigint id PK
        string email UK "login"
        string first_name
        string last_name
        bool is_active
        bool is_staff "moderators"
    }
    ORGANIZATION {
        bigint id PK
        string name
        string slug UK
        enum kind "clinic | private_practice | ngo | public_institution | room_provider | other"
        bigint city_id FK
        string address
        string contact_email
        string tax_id "NIP, optional"
        bool is_public
        bool is_verified "set by moderator"
        bool is_blocked "moderation"
    }
    MEMBERSHIP {
        bigint id PK
        bigint organization_id FK
        bigint user_id FK
        enum role "owner | admin | member"
        string job_title
    }
    SPECIALIST_PROFILE {
        bigint id PK
        bigint user_id FK,UK
        string slug UK
        string academic_title
        enum profession
        string headline
        text bio
        bigint city_id FK
        bool works_online
        string license_number
        string contact_email "public"
        bool open_to_work
        bool is_public
        bool is_blocked "moderation"
        bool visible_to_patients "Phase 3, default false"
    }
    LISTING {
        bigint id PK
        enum kind "job | internship | volunteering | job_seeking | room_rental"
        string title
        text description
        bigint author_id FK
        bigint organization_id FK "nullable"
        bigint city_id FK
        string address
        string contact_email "defaults to author email"
        enum status "draft | published | expired | archived"
        datetime published_at
        datetime expires_at
        bool is_flagged "hidden by moderation"
        text moderation_note
        enum employment_type "offers"
        enum work_mode "offers"
        int salary_min "offers"
        int salary_max "offers"
        enum salary_period "offers"
        decimal price_amount "room rental, required"
        enum price_unit "room rental: hour | day | month"
        int room_area_m2 "room rental"
        string amenities "room rental"
        text availability_description "room rental"
    }
    ROOM_AVAILABILITY_BLOCK {
        bigint id PK
        bigint listing_id FK
        int weekday "0 = Monday"
        time start_time
        time end_time "> start_time (DB check)"
    }
    INQUIRY {
        bigint id PK
        bigint listing_id FK
        bigint sender_id FK "nullable (SET NULL)"
        string sender_email
        string recipient_email
        text message
        bool email_sent
    }
    VOIVODESHIP {
        bigint id PK
        string name
        string slug UK
    }
    CITY {
        bigint id PK
        string name
        string slug UK
        bigint voivodeship_id FK
        bool is_featured
    }
    SPECIALIZATION {
        bigint id PK
        string name UK
        string slug UK
        bool is_active
    }
    THERAPY_APPROACH {
        bigint id PK
        string name UK
        string slug UK
        bool is_active
    }
```

All non-reference tables also have `created_at` / `updated_at` (`core.TimeStampedModel`).

## Key decisions

- **One account type.** A `User` becomes a specialist by creating a `SpecialistProfile` and acts
  for a clinic through a `Membership`. The same person can do both (ADR 0007).
- **One `Listing` table for all five kinds** with nullable kind-specific columns, validated in
  `Listing.clean()` and `ListingForm.clean()` (irrelevant fields are cleared on save). One list
  page, one filter, one moderation queue (ADR 0006).
- **Reference data** (cities, voivodeships, specializations, therapy approaches) lives in `core`,
  is loaded from `apps/core/fixtures/reference_data.json` and edited in the admin. Entries are
  retired with `is_active = False`, never deleted (they are referenced with `PROTECT`).

## Listing lifecycle

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> published : publish()
    draft --> archived : archive()
    published --> expired : expires_at passed (expire_listings cron)
    published --> archived : archive()
    expired --> published : publish() (renews expires_at)
    expired --> archived : archive()
    archived --> [*]
```

- `publish()` sets `published_at = now` and `expires_at = now + LISTING_DEFAULT_LIFETIME_DAYS`
  (default 60).
- Public visibility is computed, not stored: **published, `expires_at` in the future, not
  flagged, organization not blocked** (`Listing.objects.public()` and
  `Listing.is_publicly_visible`). The cron job only tidies statuses; an overdue listing is hidden
  even before it runs.
- Invalid transitions raise `InvalidTransitionError`; the UI shows an error message.

## Moderation

Post-moderation (publish first, moderate after) to keep friction low for the MVP. Staff users
work in `/admin/`:

- `Listing.is_flagged` (+ `moderation_note`) hides a listing; bulk actions "hide"/"restore".
- `Organization.is_blocked` hides the organization and all its listings;
  `Organization.is_verified` shows a "verified" badge.
- `SpecialistProfile.is_blocked` hides a profile.

A user-facing "report this listing" button and a pre-moderation mode for new accounts are on the
roadmap.

## Permissions

| Action | Who |
| --- | --- |
| View public listing / profile / organization | Everyone |
| View draft/expired/flagged listing | Author, owners/admins of its organization |
| Create listing | Any signed-in user (for an organization: only its owner/admin) |
| Edit / publish / archive listing | Author, owners/admins of its organization |
| Send inquiry | Signed-in users, only for publicly visible listings that are not their own |
| Edit organization | Its owners/admins |
| Edit specialist profile | Its user |
| Moderate | Staff (Django admin) |

Code: `apps/listings/permissions.py`, `apps/organizations/services.py`. Tests:
`apps/listings/tests/test_permissions.py`, `apps/organizations/tests/`.

## Prepared for Phase 3 (patient booking), not built

- `SpecialistProfile` holds only **professional, publishable** data and is separate from `User`.
  Exposing it to patients means a new patient-facing view filtered by `visible_to_patients`
  (already in the schema, default `False`, not used by any view).
- Patients would be regular `User`s; bookings would live in a new `booking` app above
  `profiles`/`organizations` (e.g. `Service`, `Appointment`, `AvailabilitySlot`) so the existing
  modules do not change.
- **No health data is stored anywhere in the MVP.** Inquiries are B2B (job/room related). Phase 3
  will process special-category data (GDPR art. 9); see [roadmap](roadmap.md) and ADR 0009.
- `RoomAvailabilityBlock` (recurring weekly blocks) is the seed of the Phase 2 room calendar;
  concrete bookable slots will be a separate table referencing it.
