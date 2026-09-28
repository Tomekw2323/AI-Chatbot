# apps/accounts

Local contract. The map of every segment is `docs/segmenty.md`.

## Owns

One account type, email as the login: `User`, `EmailUserManager`, `SignupForm`, `UserNameForm`, `require_user`, `has_verified_email`. There is no `urls.py` here. `config.urls` mounts `allauth.urls` at `konto/`. `ACCOUNT_SIGNUP_FORM_CLASS` is `apps.accounts.forms.SignupForm`.

## Must not import

`apps.organizations`, `apps.profiles`, `apps.listings`, `apps.privacy`. `apps.core` is allowed. Models and `services.py` do not import other apps today.

## Public surface

- `apps.accounts.models.User`
- `apps.accounts.services.require_user`
- `apps.accounts.services.has_verified_email`
- `apps.accounts.forms.UserNameForm` (called from `profiles.views`)
- `apps.accounts.forms.SignupForm` (settings only)

Callers of `require_user`: organization, profile, listing, and privacy views. `listings.views` also calls `has_verified_email`.

## Replace without editing other apps

Login providers stay in django-allauth and in settings (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`). Callers keep using `User`, `require_user`, and `has_verified_email`.

## How to test

```bash
uv run pytest apps/accounts/tests
```
