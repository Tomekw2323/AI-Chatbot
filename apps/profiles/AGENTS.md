# apps/profiles

Local contract. The map of every segment is `docs/segmenty.md`.

## Owns

The specialist profile: `SpecialistProfile`, `SpecialistProfileQuerySet.public`, `SpecialistProfileFilter` (used only by this app’s views), routes under `specjalisci/`. There is no `services.py`.

## Must not import

`apps.organizations`, `apps.listings`, `apps.privacy`. Allowed: `apps.accounts`, `apps.core`.

Profile pages show that person’s listings through the `personal_listings` template tag.

## Public surface

Other segments call `apps.profiles.models.SpecialistProfile` and `SpecialistProfile.objects.public()`.

Production callers: `listings.views`, `privacy.services`, `config.sitemaps`. `SpecialistProfileFilter` is not a cross-app API.

## Replace without editing other apps

Keep `SpecialistProfile.objects.public()` and the `user` link. Do not import `organizations`.

## How to test

```bash
uv run pytest apps/profiles/tests
```
