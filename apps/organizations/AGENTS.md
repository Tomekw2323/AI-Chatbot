# apps/organizations

Local contract. The map of every segment is `docs/segmenty.md`.

## Owns

Clinics, NGOs, and membership: `Organization`, `OrganizationQuerySet.public`, `Membership` (`Role`, `MANAGER_ROLES`), views under `organizacje/`.

## Must not import

`apps.profiles`, `apps.listings`, `apps.privacy`. Allowed: `apps.accounts`, `apps.core`.

Organization pages show listings through the `organization_listings` template tag, not a Python import of `listings`.

## Public surface

- `apps.organizations.services.can_manage_organization`
- `apps.organizations.services.managed_organizations`
- `apps.organizations.services.create_organization`
- `apps.organizations.services.AnyUser`
- `Organization.objects.public()`
- `Membership.Role`, `Membership.MANAGER_ROLES`

`listings.permissions` calls `can_manage_organization`. `listings.forms` and `listings.views` call `managed_organizations`. `privacy.services` reads `Organization` and `Membership`.

## Replace without editing other apps

Keep the three service functions and `Organization.objects.public()`. Permission rules stay in `services.py`; other apps do not query `Membership` for “who may manage”.

## How to test

```bash
uv run pytest apps/organizations/tests
```
