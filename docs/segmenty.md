# Segmenty

BartoszUP to modularny monolit: jeden proces Django, jedna baza, aplikacje z importami tylko w dół. Kierunek (import-linter w `pyproject.toml`, kontrakt „Module layers”):

`apps.privacy` → `apps.listings` → `apps.profiles` | `apps.organizations` → `apps.accounts` → `apps.core`.

`profiles` i `organizations` nie importują się nawzajem. Wołanie w górę jest zabronione. Niższy moduł pokazuje dane wyższego tagami szablonów (`apps/listings/templatetags/listing_tags.py`), nie importem Pythona. `config` i pliki wdrożenia leżą poza tym stosem: składają aplikacje. Żadna aplikacja nie importuje `config`.

Lokalny kontrakt każdego katalogu jest w jego `AGENTS.md`. Ten plik jest mapą całości.

## `config`

Ustawienia i złożenie URL-i. Nie jest aplikacją Django.

- **Posiada:** `config/settings/base.py` oraz nakładki `dev.py`, `test.py`, `prod.py`, `demo.py`; `config/urls.py` (`urlpatterns`, `healthz`); `config/wsgi.py` i `config/asgi.py` (`application`); `config/sitemaps.py` (`sitemaps`).
- **Wolno importować:** aplikacje, żeby podłączyć adresy i mapę stron. Aplikacje czytają `django.conf.settings`, nie ten pakiet.
- **Powierzchnia:** `DJANGO_SETTINGS_MODULE` wskazuje `config.settings.dev`, `config.settings.test`, `config.settings.prod` albo `config.settings.demo`. Wejście procesu: `config.wsgi:application` (gunicorn; domyślnie `config.settings.prod`). Adresy: `config.urls.urlpatterns`, w tym `healthz/` → `healthz`. Mapa: `config.sitemaps.sitemaps` (klucze `listings`, `profiles`, `organizations`, `landing`).
- **Wymiana bez edycji aplikacji:** inna nakładka ustawień. Poczta: `config.settings.base` bierze `EMAIL_URL` przez `env.email_url` (domyślnie `consolemail://`). `config.settings.demo` ustawia `EMAIL_BACKEND` na `django.core.mail.backends.console.EmailBackend`. `config.settings.test` ustawia `django.core.mail.backends.locmem.EmailBackend`. `apps.listings.services.send_inquiry` wysyła przez `django.core.mail.EmailMessage`, więc backend da się podmienić w ustawieniach.

## `apps/core`

Dane wspólne i techniczne. Najniższa warstwa.

- **Posiada:** `TimeStampedModel`, `ReferenceModel`, `Voivodeship`, `City`, `Specialization`, `TherapyApproach`, `RateLimitCounter`; fixture `apps/core/fixtures/reference_data.json`; slugi polskie; licznik limitów; weryfikację Turnstile; `SecurityHeadersMiddleware`; context processor `site`.
- **Wolno importować:** nic z `apps.*`.
- **Powierzchnia:** `apps.core.text.slugify_pl`, `unique_slug`. `apps.core.ratelimit.ratelimit`, `check`, `hit`, `client_ip`, `rate_limited_response`, `purge_old_windows`, `parse_rate`. `apps.core.captcha.is_enabled`, `verify` (pole formularza `TOKEN_FIELD`). `apps.core.middleware.SecurityHeadersMiddleware`. `apps.core.context_processors.site`. Modele wyżej.
- **Wymiana bez edycji reszty:** klucze Turnstile i limity są w ustawieniach (`TURNSTILE_SITE_KEY`, `TURNSTILE_SECRET_KEY`, `RATE_LIMITS`), nie w wyższych aplikacjach. Podmiana samego `core` wymaga tych samych nazw.

## `apps/accounts`

Jedno konto, login e-mailem. Nie ma tu `urls.py`: `config.urls` podpina `allauth.urls` pod `konto/`.

- **Posiada:** `User`, `EmailUserManager`, `SignupForm`, `UserNameForm`, `require_user`, `has_verified_email`. `ACCOUNT_SIGNUP_FORM_CLASS` w `config.settings.base` to `apps.accounts.forms.SignupForm`.
- **Wolno importować:** `apps.core`. Dziś modele i `services.py` nie importują innych aplikacji.
- **Nie wolno:** `organizations`, `profiles`, `listings`, `privacy`.
- **Powierzchnia:** `apps.accounts.models.User`. `apps.accounts.services.require_user`, `has_verified_email`. `apps.accounts.forms.UserNameForm` (woła `profiles.views`), `SignupForm` (ustawienia).
- **Wymiana bez edycji reszty:** dostawca logowania zostaje w allauth i w ustawieniach (`GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`). Wyższe moduły mają dalej dostać `User`, `require_user` i `has_verified_email`.

## `apps/organizations`

Poradnie, fundacje, członkostwo.

- **Posiada:** `Organization`, `OrganizationQuerySet.public`, `Membership` (`Role`, `MANAGER_ROLES`), widoki pod `organizacje/`.
- **Wolno importować:** `apps.accounts`, `apps.core`.
- **Nie wolno:** `profiles`, `listings`, `privacy`.
- **Powierzchnia:** `apps.organizations.services.can_manage_organization`, `managed_organizations`, `create_organization`, alias `AnyUser`. `Organization.objects.public()`. `Membership` z `Role` i `MANAGER_ROLES`. Ogłoszenia organizacji na stronie idą tagiem `organization_listings`, nie importem `listings`.
- **Wymiana bez edycji reszty:** reguła „kto zarządza” zostaje w tych trzech funkcjach. `listings.permissions` woła `can_manage_organization`. `listings.forms` i `listings.views` wołają `managed_organizations`. `listings.models` i `listings.templatetags.listing_tags` oraz `config.sitemaps` czytają `Organization`. `privacy.services` czyta `Organization` i `Membership`.

## `apps/profiles`

Wizytówka specjalisty. Nie ma `services.py`.

- **Posiada:** `SpecialistProfile`, `SpecialistProfileQuerySet.public`, `SpecialistProfileFilter` (tylko widoki tego modułu), adresy pod `specjalisci/`.
- **Wolno importować:** `apps.accounts`, `apps.core`.
- **Nie wolno:** `organizations`, `listings`, `privacy`.
- **Powierzchnia dla innych segmentów:** `apps.profiles.models.SpecialistProfile` i `SpecialistProfile.objects.public()`. Wołają to `listings.views`, `privacy.services` i `config.sitemaps`. Ogłoszenia osoby na wizytówce: tag `personal_listings`.
- **Wymiana bez edycji reszty:** inna wizytówka, jeśli zostaje `SpecialistProfile.objects.public()` i powiązanie `user`.

## `apps/listings`

Tablica ogłoszeń: praca, staż, wolontariat, „szukam pracy”, wynajem gabinetu. Jedna tabela `Listing`.

- **Posiada:** `Listing`, `RoomAvailabilityBlock`, `Inquiry`, `ListingReport`, formularze, filtry, widoki pod `ogloszenia/` oraz `home` i `dashboard` podpięte w `config.urls`. Polecenia: `daily_maintenance`, `expire_listings`, `prepare_demo`, `seed_demo`.
- **Wolno importować:** `profiles`, `organizations`, `accounts`, `core`.
- **Nie wolno:** `privacy`.
- **Powierzchnia:** `Listing.objects.public()`, `ListingQuerySet.due_to_expire`, `Listing.publish`, `archive`, `expire`, `Listing.KIND_URL_SLUGS`, `InvalidTransitionError`. `apps.listings.services.expire_due_listings`, `purge_old_inquiries`, `send_inquiry`, `report_listing`, `recipient_email_for`, `DuplicateReportError`. `apps.listings.permissions.can_edit_listing`, `can_view_listing`, `can_post_for_organization`, `can_send_inquiry`, `can_report_listing`. Tagi: `organization_listings`, `personal_listings`, `kind_badge_class`, `query_transform`.
- **Kto to woła z zewnątrz:** `privacy.services` czyta `Listing`, `Inquiry`, `ListingReport`. `config.sitemaps` używa `Listing.objects.public()` i `Listing.KIND_URL_SLUGS`. Cron z `render.yaml` uruchamia `daily_maintenance`, które woła `expire_due_listings`, `purge_old_inquiries` i `apps.core.ratelimit.purge_old_windows`.
- **Wymiana bez edycji reszty:** później wynajem gabinetu da się wyjąć do modułu `rooms` (ADR 0006). `RoomAvailabilityBlock` jest używany tylko wewnątrz `apps/listings`. Inne segmenty wołają `Listing`, nie ten model. Dopóki zostają `Listing.objects.public()`, `publish`, `archive`, `expire` i `KIND_URL_SLUGS`, `privacy` i `config.sitemaps` nie wymagają zmian.

## `apps/privacy`

Eksport i usunięcie konta oraz strony regulaminu. Najwyższa warstwa: widzi dane osobowe z niższych modułów.

- **Posiada:** `export_user_data`, `delete_account`, `AccountDeletionBlockedError`; widoki `my_data`, `export_data`, `delete_account_view`, `terms`, `privacy_policy` pod `prywatnosc/`.
- **Wolno importować:** `listings`, `profiles`, `organizations`, `accounts`, `core`. W kodzie `services.py` są to modele: `User`, `Inquiry`, `Listing`, `ListingReport`, `Membership`, `Organization`, `SpecialistProfile`, plus modele allauth `EmailAddress` i `SocialAccount`.
- **Nie wolno:** niższe aplikacje nie importują `privacy`.
- **Powierzchnia:** `apps.privacy.services.export_user_data`, `delete_account`, `AccountDeletionBlockedError`. Widoki wołają je same; żaden inny segment ich nie importuje.
- **Wymiana bez edycji reszty:** inna realizacja eksportu i kasowania, jeśli te dwie funkcje i wyjątek zostają, a niższe modele z listy wyżej nie zmieniają pól, które eksport czyta.

## Wdrożenie

Dwa plany Render, te same aplikacje.

| | `render.yaml` | `render.demo.yaml` |
| --- | --- | --- |
| Ustawienia | `config.settings.prod` | `config.settings.demo` |
| Start | obraz, `preDeployCommand`: `migrate` i `createcachetable` | `dockerCommand`: `sh scripts/run_demo.sh` (`prepare_demo`, potem gunicorn) |
| Baza | Postgres `bartoszup-db` | brak; SQLite w kontenerze |
| Cron | `python manage.py daily_maintenance` | brak |

Podmiana planu nie wymaga edycji aplikacji: zmienia się plik blueprintu i `DJANGO_SETTINGS_MODULE`. Nie podstawiać jednego pliku za drugi przy wdrożeniu (ADR 0017, `docs/deployment.md`).
