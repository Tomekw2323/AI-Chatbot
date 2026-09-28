# 0007. One account type; organizations with memberships

- Status: Proposed – awaiting developer review
- Date: 2026-09-28

## Context

Actors are specialists, organizations (clinics, NGOs, public institutions such as OPS, room
owners) and later patients. The same person is often several of these: a psychotherapist who
also runs a practice and rents out its room; a clinic owner who is a practising psychologist.

## Decision

- One custom `accounts.User` model (email as the login, no username), created from day one so it
  never needs a painful swap later.
- Roles are **relationships, not flags**: a user is a specialist if they have a
  `profiles.SpecialistProfile`; they act for an organization through
  `organizations.Membership(role = owner | admin | member)`.
- Owners/admins manage the organization and all its listings; members are listed but cannot edit.
- A listing optionally belongs to an organization; without one it is a personal listing.

## Consequences

- No "choose your account type" step at signup; one login for everything.
- Permission checks are object-level (`can_manage_organization`, `can_edit_listing`) rather than
  global Django permissions/groups, which are reserved for staff/moderators.
- Patients in Phase 3 will be regular users too, which keeps login simple but means patient data
  must be separated by model/module, not by user type (see ADR 0009).
