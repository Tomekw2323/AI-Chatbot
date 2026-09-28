# 0012. Publish immediately, moderate afterwards, with abuse controls

- Status: Accepted (2026-09-28)
- Date: 2026-09-28

## Context

Open question from the initial review: pre-moderate listings, or publish immediately? Early
traction depends on low friction (people used to posting in a Facebook group), but an open board
attracts spam, scams (fake room rentals, advance-fee "job offers") and unethical offers.

## Decision

**Post-moderation**: listings go live when the author publishes them. Abuse is contained by:

1. **Verified email required** to create, edit or publish listings, create organizations, edit
   profiles, send member inquiries and report listings (allauth `verified_email_required`,
   `accounts.services.has_verified_email`). Production also enforces verification at signup.
2. **Rate limits** on listing creation (10/h, 50/day per user), organization creation (5/day),
   inquiries and reports (ADR 0014).
3. **User reports** (`ListingReport`: spam, fraud, inappropriate, outdated, other), one per user
   per listing. With `LISTING_REPORTS_AUTO_FLAG` (default 3) distinct open reports the listing
   is hidden automatically (`is_flagged`) until a moderator reviews it in the admin.
4. **Moderator tools** in the admin: hide/restore listings, resolve reports, block organizations
   and profiles, mark organizations as verified.
5. Organization "verified" badges are set only by moderators (not by users; tested).

Pre-moderation can be switched on later per account age or organization verification if abuse
appears; the lifecycle model already supports it (a "pending review" status would sit between
draft and published).

## Consequences

- Zero waiting time for honest users; spam requires verified accounts and is throttled.
- A small number of reports can hide a legitimate listing (griefing). Mitigation: reports require
  verified accounts, one per user, and moderators restore listings in one click.
- Moderators must watch the report queue (admin → "Zgłoszenia ogłoszeń").
