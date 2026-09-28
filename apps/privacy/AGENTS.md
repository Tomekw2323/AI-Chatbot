# apps/privacy

Local contract. The map of every segment is `docs/segmenty.md`.

## Owns

Account export and erasure, plus the terms and privacy-policy pages: `export_user_data`, `delete_account`, `AccountDeletionBlockedError`, views `my_data`, `export_data`, `delete_account_view`, `terms`, `privacy_policy` under `prywatnosc/`.

## Must not

Lower apps must not import `apps.privacy`. This app may import `listings`, `profiles`, `organizations`, `accounts`, and `core`.

`services.py` reads models, not the lower `services.py` modules: `User`, `Inquiry`, `Listing`, `ListingReport`, `Membership`, `Organization`, `SpecialistProfile`, plus allauth `EmailAddress` and `SocialAccount`.

## Public surface

- `apps.privacy.services.export_user_data`
- `apps.privacy.services.delete_account`
- `apps.privacy.services.AccountDeletionBlockedError`

Only this app’s views call them in production. New personal data has to be added to export and deletion here.

## Replace without editing other apps

Another export or deletion implementation can replace these two functions and the exception. It still has to read the models listed above; changing those models’ fields means editing this module too.

## How to test

```bash
uv run pytest apps/privacy/tests
```
