# Przewodnik techniczny BartoszUP

Dla osoby, która nadzoruje zmiany i nie pisała tego kodu. Kod aplikacji na `main` jest taki jak w `71a0980` (przewodniki doszły w `5d1d911`, 2026-09-28). Opisuje to, co jest w repozytorium, i pytania przy przejęciu, których pierwsza wersja nie zamykała. Rezerwacji wizyt i płatności w kodzie nie ma.

Krótszy opis dla właściciela: [jak-dziala.md](jak-dziala.md).

## Stos

| Warstwa | Co jest |
| --- | --- |
| Język | Python 3.13 (`requires-python` w `pyproject.toml`) |
| Aplikacja | Django 5.2 LTS, jeden proces WSGI |
| Baza pełnej wersji i testów | PostgreSQL 17 (`psycopg`) |
| Baza demo | SQLite, wymuszona w `config/settings/demo.py` |
| Konta | django-allauth 65.19 (`account` + `socialaccount`, provider Google) |
| Listy | django-filter |
| HTML | Szablony Django, HTMX 2.0.11 (`static/vendor/htmx-2.0.11.min.js`), Tailwind CSS 4.3.3 przez `django-tailwind-cli` (bez Node) |
| Statyczne pliki | WhiteNoise; w produkcji `CompressedManifestStaticFilesStorage` |
| Serwer | gunicorn (obraz Docker, cel `prod`) |
| Konfiguracja | `django-environ`, zmienne z `.env` / środowiska (`.env.example`) |
| Narzędzia | uv, ruff (w tym reguły bandit `S`), mypy + django-stubs, pytest + factory_boy, import-linter, pre-commit, pip-audit |

Decyzje: [docs/adr/README.md](adr/README.md). Stos: ADR 0003, 0004, 0010.

## Drzewo projektu

Katalogi na gałęzi `main`. Migracje, cache i pliki generowane są pominięte. Krótki komentarz jest tylko przy nazwie, która nie jest oczywista.

```text
.
├── manage.py
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── docker-compose.yml
├── render.yaml                        # pełna wersja: web, cron, Postgres
├── render.demo.yaml                   # darmowe demo na SQLite
├── .env.example
├── .pre-commit-config.yaml
├── .cursor/rules/
├── .github/workflows/ci.yml
├── AGENTS.md
├── CONTRIBUTING.md
├── README.md
├── apps/
│   ├── accounts/
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── forms.py
│   │   └── admin.py
│   ├── core/
│   │   ├── models.py
│   │   ├── middleware.py
│   │   ├── ratelimit.py
│   │   ├── captcha.py
│   │   ├── text.py                    # slugi, w tym „ł”
│   │   ├── context_processors.py
│   │   ├── admin.py
│   │   └── fixtures/
│   │       └── reference_data.json    # słownik: województwa, miasta, specjalizacje, nurty
│   ├── listings/
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   ├── filters.py
│   │   ├── permissions.py
│   │   ├── admin.py
│   │   ├── templatetags/
│   │   │   └── listing_tags.py        # ogłoszenia na stronie organizacji
│   │   └── management/commands/
│   │       ├── daily_maintenance.py
│   │       ├── expire_listings.py
│   │       ├── prepare_demo.py
│   │       └── seed_demo.py
│   ├── organizations/
│   │   ├── models.py
│   │   ├── services.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── forms.py
│   │   └── admin.py
│   ├── privacy/
│   │   ├── services.py
│   │   ├── views.py
│   │   └── urls.py
│   └── profiles/
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── forms.py
│       ├── filters.py
│       └── admin.py
├── config/
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py
│   ├── sitemaps.py
│   └── settings/
│       ├── base.py
│       ├── dev.py
│       ├── test.py
│       ├── prod.py
│       └── demo.py
├── templates/
│   ├── base.html
│   ├── home.html
│   ├── 403.html
│   ├── 404.html
│   ├── 429.html
│   ├── robots.txt
│   ├── includes/
│   │   ├── form_fields.html
│   │   └── pagination.html
│   ├── allauth/
│   │   ├── elements/
│   │   │   └── button.html
│   │   └── layouts/
│   │       └── base.html
│   ├── listings/
│   │   ├── listing_list.html
│   │   ├── listing_detail.html
│   │   ├── listing_form.html
│   │   ├── dashboard.html
│   │   ├── _listing_card.html
│   │   ├── _listing_results.html
│   │   ├── _listing_compact_list.html
│   │   ├── _delete_listing.html
│   │   └── email/
│   │       └── inquiry.txt
│   ├── profiles/
│   │   ├── specialist_list.html
│   │   ├── specialist_detail.html
│   │   ├── profile_form.html
│   │   └── _specialist_results.html
│   ├── organizations/
│   │   ├── organization_detail.html
│   │   └── organization_form.html
│   └── privacy/
│       ├── my_data.html
│       ├── privacy_policy.html
│       └── terms.html
├── static/
│   ├── js/
│   │   └── listing-form.js
│   └── vendor/
│       └── htmx-2.0.11.min.js
├── assets/
│   └── css/
│       └── source.css                 # źródło klas Tailwinda
├── scripts/
│   └── run_demo.sh
└── docs/
    ├── przewodnik-techniczny.md
    ├── jak-dziala.md
    ├── architecture.md
    ├── domain-model.md
    ├── security.md
    ├── deployment.md
    ├── roadmap.md
    ├── preview/
    └── adr/
```

`/konto/` obsługuje allauth, więc w `accounts` są `models.py`, `services.py` i `forms.py`. `services.py` jest też w `listings`, `organizations` i `privacy`. Widok w `profiles` woła `SpecialistProfile`. Szablony są w `templates/` (`DIRS` w `config/settings/base.py`). Testy są w `apps/<aplikacja>/tests/`.

Poniżej ścieżka żądania i warstwy importu. Kolejność middleware i mapa URL są w następnej sekcji. Reguły wołań są w „Aplikacje i kierunek importów”.

```text
przeglądarka
└── middleware
    └── config/urls.py
        └── views
            └── services
                └── models

apps.privacy
└── apps.listings
    ├── apps.profiles
    │   └── apps.accounts
    │       └── apps.core
    └── apps.organizations
        └── apps.accounts
            └── apps.core
```

Pierwsze drzewo to kolejność obsługi żądania: przeglądarka, middleware, `config/urls.py`, widok, `services.py`, model. Drugie jest z kontraktu import-linter (`pyproject.toml`, `[tool.importlinter]`): warstwa wyżej może importować każdą niższą. `profiles` i `organizations` są rodzeństwem. `config` może importować każdą aplikację.

## Przepływ żądania

1. Przeglądarka woła HTTPS. Na Render proxy dokleja `X-Forwarded-Proto` i adres klienta do `X-Forwarded-For`. `TRUSTED_PROXY_COUNT` mówi, ile ostatnich wpisów `X-Forwarded-For` ufać (`apps/core/ratelimit.py`, `client_ip`). Lokalnie `0` — liczy się `REMOTE_ADDR`.
2. gunicorn ładuje `config.wsgi`. Moduł ustawień: `DJANGO_SETTINGS_MODULE`.
3. Kolejność `MIDDLEWARE` w `config/settings/base.py`: `SecurityMiddleware`, WhiteNoise, sesja, locale, `CommonMiddleware`, CSRF, auth, messages, clickjacking, CSP (`django-csp`), `apps.core.middleware.SecurityHeadersMiddleware` (`Permissions-Policy`, `Cross-Origin-Resource-Policy`), allauth, `django_htmx` (ustawia `request.htmx`).
4. `config/urls.py` rozdziela ścieżki. Widok jest cienki: sprawdza uprawnienie, woła `services.py`, renderuje szablon.
5. Odpowiedź to HTML. Filtry list (`listings`, `profiles`) przy `request.htmx` zwracają partial `_*.html`; bez JS formularz GET i tak działa.
6. Zapis, który zmienia stan, jest POST z tokenem CSRF (HTMX dokleja go w `hx-headers` w `templates/base.html`).
7. Mail (weryfikacja, zapytanie) idzie synchronicznie w tym samym żądaniu. Kolejki zadań nie ma. Nieudana wysyłka zapytania zostawia `Inquiry.email_sent = False` i loguje tylko `inquiry_id` (`apps/listings/services.py`, `send_inquiry`).

`/healthz/` zwraca tekst `ok`. `/sitemap.xml` i `/robots.txt` są publiczne.

Mapa URL (`config/urls.py` i `urls.py` aplikacji):

| Ścieżka | Widok |
| --- | --- |
| `/` | `listings.views.home` |
| `/panel/` | `listings.views.dashboard` (`login_required`) |
| `/ogloszenia/` | lista + filtry |
| `/ogloszenia/<kind>/` i `/ogloszenia/<kind>/<miasto>/` | ta sama lista; slug rodzaju: `praca`, `staze`, `wolontariat`, `szukam-pracy`, `gabinety` (`Listing.KIND_URL_SLUGS`) |
| `/ogloszenia/dodaj/`, `<pk>/edytuj/`, `<pk>/<action>/zmien-status/`, `<pk>/usun/` | tworzenie, edycja, `publish`/`archive`, kasowanie |
| `/ogloszenia/<pk>/wiadomosc/`, `<pk>/zglos/` | zapytanie, zgłoszenie |
| `/ogloszenia/<pk>/<slug>/` | szczegół; zły slug robi przekierowanie 301 na aktualny |
| `/specjalisci/`, `/specjalisci/moj-profil/`, `/specjalisci/<slug>/` | lista, edycja własnego profilu, szczegół |
| `/organizacje/dodaj/`, `/organizacje/<slug>/`, `…/edytuj/` | brak listy organizacji w menu |
| `/konto/…` | allauth (`account_login`, `account_signup`, `account_logout`, `account_email`, reset hasła, Google: `/konto/google/login/callback/`) |
| `/prywatnosc/moje-dane/`, `…/eksport/`, `…/usun-konto/`, `regulamin/`, `polityka-prywatnosci/` | RODO i strony prawne |
| `ADMIN_URL` | Django admin. Domyślnie `admin/`. Produkcja wymaga niezgadywalnej ścieżki. |

## Aplikacje i kierunek importów

Jedna aplikacja, jedna baza (poza demo). Kierunek, od góry do dołu — wyższa warstwa może importować niższą, odwrotnie nie:

`apps.privacy` → `apps.listings` → `apps.profiles` | `apps.organizations` → `apps.accounts` → `apps.core`

`profiles` i `organizations` są rodzeństwem: żaden nie importuje drugiego. Kontrakt import-linter: `pyproject.toml`, sekcja `[tool.importlinter]`, warstwy jak wyżej. CI woła `uv run lint-imports`.

Reguły (ADR 0002, [architecture.md](architecture.md)):

- Wołanie między aplikacjami idzie przez `services.py` niższej (przykład: `organizations.services.can_manage_organization`, `managed_organizations`, `create_organization`). Nie odpytywać `Membership` z `listings`.
- Klucz obcy „w górę” jest zakazany. Strona organizacji pokazuje ogłoszenia tagiem `organization_listings` z `apps/listings/templatetags/listing_tags.py`, nie importem Pythona w `organizations`.
- `config/` (URL, sitemap) stoi nad aplikacjami i może importować każdą.
- Widoki: uprawnienia w `permissions.py` / `services.py`, kilka kroków i mail w `services.py`, niezmienniki w `models.clean()` i ograniczeniach bazy.
- Użytkownik w kodzie: `apps.accounts.models.User`. W kluczach obcych: `settings.AUTH_USER_MODEL`. W widoku po `login_required`: `accounts.services.require_user(request)` — bez `assert`.
- Publiczne listy: `Listing.objects.public()`, `SpecialistProfile.objects.public()`, `Organization.objects.public()`. Nie składać tych warunków drugi raz w widoku.
- Status ogłoszenia zmienia się przez `publish()` / `archive()` / `expire()`, nie przez ręczne przypisanie w widoku. Wyjątek operacyjny: `expire_due_listings()` robi `QuerySet.update` na wierszach już wybranych przez `due_to_expire()`.

`INSTALLED_APPS` układa aplikacje lokalne w tej samej kolejności co warstwy, od dołu (`core` … `privacy`).

## Model danych

Pełny diagram: [domain-model.md](domain-model.md). Słownik referencyjny: `apps/core/fixtures/reference_data.json` (stałe pk — ponowne `loaddata` nadpisuje poprawki moderatora).

| Model | Aplikacja | Znaczenie |
| --- | --- | --- |
| `User` | `accounts` | E-mail jako login (`username` wyłączony). `terms_accepted_at` przy rejestracji. `is_staff` = moderator. |
| `SpecialistProfile` | `profiles` | Jeden na użytkownika. Zawód, miasto, specjalizacje, nurty, kontakt, `open_to_work`, `is_public`, `is_blocked`. `visible_to_patients` jest w schemacie, domyślnie `False`, żaden widok go nie czyta. |
| `Organization`, `Membership` | `organizations` | Rodzaje: clinic, private_practice, ngo, public_institution, room_provider, other. Role: `owner`, `admin`, `member`. `MANAGER_ROLES` = owner i admin. `is_verified` i `is_blocked` ustawia admin, nie formularz. |
| `Listing` | `listings` | Jedna tabela, pięć `kind` (ADR 0006). Pola rodzaju są puste, gdy nie pasują (`ListingForm.clean`). |
| `RoomAvailabilityBlock` | `listings` | Cykliczny blok tygodnia przy gabinecie. Koniec po starcie (check w bazie). To nie jest kalendarz rezerwacji. |
| `Inquiry` | `listings` | Wiadomość z ogłoszenia. `sender` puste u gościa i po skasowaniu konta. |
| `ListingReport` | `listings` | Jedno zgłoszenie na parę ogłoszenie + użytkownik (`uniq_report_per_user`). |
| `Voivodeship`, `City`, `Specialization`, `TherapyApproach` | `core` | 16 województw, 54 miasta (14 z `is_featured`), 23 specjalizacje, 16 nurtów. `is_active=False` wycofuje pozycję bez kasowania. |
| `RateLimitCounter` | `core` | Okna limitów (ADR 0014). |

Wspólne `created_at` / `updated_at`: `TimeStampedModel`. Slugi: `apps.core.text.slugify_pl` (obsługa „ł”) i `unique_slug`. Slug ogłoszenia przepisuje się z tytułu przy każdym `save`.

`Listing.clean`: „szukam pracy” nie może mieć organizacji; gabinet wymaga `price_amount` i `price_unit`; `salary_min` ≤ `salary_max` (to samo trzyma `CheckConstraint` `listing_salary_range_valid`).

### Pięć rodzajów, jedna tabela, zero szóstego

ADR 0006. Nie ma osobnych tabel na pracę, staż, wolontariat, „szukam pracy” i gabinet. Nie ma też rodzaju na „zlecenie”, „szukam gabinetu” ani ofertę dla pacjenta. Zlecenie z grupy na Facebooku to `kind=job` plus `employment_type` (`b2b` albo `civil_contract`). „Szukam gabinetu” nie ma kolumny. `open_to_work` na `SpecialistProfile` to „szukam pracy / współpracy”, nie szukanie sali.

Które kolumny formularz zostawia (`ListingForm.clean`, `FIELDS_BY_KIND` w `apps/listings/forms.py`; reszta idzie na `None` albo `""`):

| `kind` | Zostaje | Czyszczone |
| --- | --- | --- |
| `job` | `employment_type`, `work_mode`, `salary_min`, `salary_max`, `salary_period` | pola gabinetu |
| `internship` | to samo co `job` | pola gabinetu |
| `volunteering` | `work_mode` | pensja i pola gabinetu |
| `job_seeking` | `employment_type`, `work_mode`; `organization` wymuszone na `None` | pensja i pola gabinetu |
| `room_rental` | `price_amount`, `price_unit`, `room_area_m2`, `amenities`, `availability_description` plus do 21 wierszy `RoomAvailabilityBlock` | pensja i tryb pracy |

Jedna cena na wiersz. Godzina i miesiąc naraz to dwa `Listing`, nie dwa `price_unit`. Filtr `ListingFilter` nie ma `employment_type`. `ordering` sortuje `published_at` albo `price_amount` (parametr `price`). Widełki `salary_*` nie biorą udziału w sortowaniu. Szukaj (`filter_q`) obejmuje `title` i `description`, nie `employment_type`.

`Organization.kind` (`clinic`, `private_practice`, `ngo`, `public_institution`, `room_provider`, `other`) nie zmienia dozwolonych ogłoszeń. To etykieta. `tax_id` (NIP) nie ma walidatora rejestru. `Membership.job_title` jest w modelu i w eksporcie RODO; `OrganizationForm` go nie ma, strona organizacji (`templates/organizations/organization_detail.html`) nie renderuje członków.

`recipient_email_for` (`apps/listings/services.py`) zwraca `listing.contact_email` albo `listing.author.email`. E-mail organizacji sam się tam nie podstawia.

Widoczność publiczna ogłoszenia (`is_publicly_visible` i `public()`): `status=published`, `expires_at` puste albo w przyszłości, `is_flagged=False`, organizacja nie jest `is_blocked`. `public()` nie patrzy na `SpecialistProfile.is_blocked` ani na `author.is_active`. Zablokowanie wizytówki nie zdejmuje prywatnych ogłoszeń. Cron tylko porządkuje status. Po terminie ogłoszenie znika z list zanim status zdąży zmienić się na `expired`.

### Bloki gabinetu to nie kalendarz

`RoomAvailabilityBlock`: `weekday` 0–6 (poniedziałek = 0), `start_time`, `end_time`. Check w bazie: `end_time > start_time` (`availability_block_end_after_start`). Nie ma daty, strefy na samym polu `TimeField`, zakazu nakładania okien ani unikalności `(listing, weekday)`. Formset: `extra=2`, `max_num=21` (`AvailabilityFormSet`).

Zapis w `apps/listings/views.py`, `_save_listing_form`: formset jest walidowany i zapisywany tylko gdy `kind == room_rental`. Przy innym rodzaju `availability_blocks` są kasowane. Szablon pokazuje bloki tylko przy `listing.is_room_rental`.

Nie ma tabeli rezerwacji, holda, płatności ani „wyłączności”. Cena za miesiąc plus `availability_description` to jedyny sposób zapisać stały najem, i jest to tekst. ADR 0006: kalendarz fazy 2 ma być osobnym modułem (`rooms` / bookable slots), a nie dorabianiem kolumn do `RoomAvailabilityBlock`. `docs/domain-model.md` mówi to samo: konkretne sloty to osobna tabela wskazująca na blok, jeszcze nieistniejąca.

Profil publiczny: `is_public`, nie `is_blocked`, `user.is_active`. Organizacja publiczna: `is_public` i nie `is_blocked`.

## Cykl życia ogłoszenia

```
draft --publish--> published --(expires_at)--> expired
  |                    |                          |
  +------archive-----> archived <-----archive-----+
                         expired --publish--> published
archived nie ma wyjścia.
```

`publish()` ustawia `published_at = now` i `expires_at = now + LISTING_DEFAULT_LIFETIME_DAYS` (domyślnie 60, `config/settings/base.py`). Niedozwolone przejście rzuca `InvalidTransitionError`; widok pokazuje komunikat.

Przyciski w `templates/listings/listing_form.html` i `dashboard.html`:

- `action=save` — zapis bez zmiany statusu (nowe zostaje `draft`).
- `action=publish` — tylko gdy `can_transition_to(published)` (draft i expired).
- POST `listings:transition` z `action` `publish` albo `archive`. Pole `next` przechodzi przez `url_has_allowed_host_and_scheme`.
- Usunięcie: POST `listing_delete`, `login_required` + `can_edit_listing`. Potwierdzenie w `templates/listings/_delete_listing.html`.

Tworzenie i zmiana statusu wymagają `verified_email_required`. Samo kasowanie wymaga tylko logowania i prawa do obiektu.

Codzienne porządki: `python manage.py daily_maintenance` (`expire_due_listings`, `purge_old_inquiries`, `purge_old_windows`). Starsze polecenie `expire_listings` robi tylko wygaszanie. W `render.yaml` cron `15 3 * * *` (03:15 UTC). Na demo crona nie ma.

## Uprawnienia

Kod: `apps/listings/permissions.py`, `apps/organizations/services.py`. Testy: `apps/listings/tests/test_permissions.py`, `test_security.py`, `apps/organizations/tests/`.

| Akcja | Kto | Odmowa |
| --- | --- | --- |
| Czytać publiczne ogłoszenie, profil, organizację | Każdy | niewidoczne ogłoszenie: 404 (`can_view_listing`) |
| Czytać szkic / wygasłe / ukryte / z zablokowanej organizacji | Autor albo owner/admin tej organizacji | 404 dla reszty |
| Tworzyć ogłoszenie | Zalogowany z potwierdzonym e-mailem. W imieniu organizacji: tylko owner/admin (`managed_organizations` w queryset pola) | brak weryfikacji: strona allauth; obca organizacja odrzucona w formularzu |
| Edytować, publikować, archiwizować | Autor albo owner/admin | 403 `PermissionDenied` |
| Kasować ogłoszenie | To samo, wystarczy login | 403 |
| Pisać wiadomość | Publiczne ogłoszenie; nie autor. Zalogowany: `has_verified_email`. Gość: tylko gdy `captcha.is_enabled()` | 403 albo redirect na login, gdy Turnstile wyłączony |
| Zgłosić | Zalogowany, zweryfikowany, nie autor, ogłoszenie publiczne | 403 |
| Utworzyć organizację | Zweryfikowany (`ratelimit("organization_create")`) | twórca dostaje `Membership.role=owner` |
| Edytować organizację | owner/admin | 403; queryset edycji to `Organization.objects.all()`, więc da się wejść w niepubliczną |
| Edytować profil | Właściciel, zweryfikowany e-mail | jeden profil na user |
| Eksport i kasowanie konta | Właściciel konta, `reauthentication_required` | allauth prosi o hasło |
| Moderować | `is_staff` w adminie | |

`member` nie zarządza organizacją ani jej ogłoszeniami. Na stronie nie ma zaproszeń — `Membership` dodaje się w adminie (`MembershipInline`). Roadmap wymienia zaproszenia jako rzecz przed startem, nie jako funkcję.

Ról produktowych na `User` nie ma (ADR 0007). Specjalista to obecność `SpecialistProfile` (jeden, `OneToOne`). Poradnia to `Membership`. `is_staff` / `is_superuser` to moderator w Django admin, nie rola na stronie. Pacjent nie jest osobnym modelem ani grupą Django. Faza 3, jeśli powstanie, ma użyć tego samego `User` (ADR 0007 i 0009), a dane wizyty trzymać w nowym module, nie w polu na użytkowniku.

Google: provider jest w `INSTALLED_APPS`, przycisk pojawia się dopiero gdy oba `GOOGLE_CLIENT_ID` i `GOOGLE_CLIENT_SECRET` są niepuste (`config/settings/base.py`, `SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT`). `ACCOUNT_LOGOUT_ON_GET = False`. `SESSION_COOKIE_AGE` nie jest nadpisane (zostaje domyślne dwa tygodnie Django).

Kasowanie konta (`privacy.services.delete_account`):

- jedyny członek → organizacja jest kasowana (ogłoszenia kaskadą);
- jest inny owner → nic nie awansuje;
- nie ma drugiego ownera, jest admin → najstarszy admin (`created_at`) dostaje `owner`;
- są tylko `member` → `AccountDeletionBlockedError`, widok pokazuje komunikat i nie kasuje;
- ogłoszenia organizacji autora przechodzą na owner/admin (kolejność `-role`, `created_at`); prywatne ogłoszenia znikają z userem (`CASCADE`);
- `Inquiry` nadawcy i wiersze z tym samym `sender_email` są kasowane przed `user.delete()`.

Eksport: `privacy.services.export_user_data` — JSON, `Content-Disposition`, `Cache-Control: no-store`. Są: konto, `EmailAddress`, `SocialAccount` (provider, bez tokenów w tym słowniku), profil (bez `is_blocked` i bez `visible_to_patients`), członkostwa z `job_title`, ogłoszenia autora, `inquiries_sent`, `inquiries_received`, zgłoszenia złożone przez użytkownika.

`inquiries_received` to `Inquiry` przy `listing__author=user`, nie przy organizacjach, którymi user zarządza. Właściciel poradni nie zobaczy w eksporcie wiadomości do ogłoszenia, którego autorem jest ktoś inny. Widoku skrzynki nie ma: `InquiryAdmin` w `apps/listings/admin.py` jest dla `is_staff`, a panel (`templates/listings/dashboard.html`) zapytań nie listuje.

## Kontrola bezpieczeństwa

Szczegóły i luki: [security.md](security.md). ADR 0012–0016.

- Publikacja od razu, moderacja potem (ADR 0012). `Listing.is_flagged` chowa niezależnie od statusu. Trzy otwarte zgłoszenia (`LISTING_REPORTS_AUTO_FLAG`) ustawiają flagę i dopisują `moderation_note`. `ListingReportAdmin.mark_resolved` tylko ustawia `is_resolved` — nie zdejmuje flagi. Flaga schodzi akcją „Przywróć zaznaczone”.
- `Organization.is_blocked` chowa organizację i jej ogłoszenia (`public()`). `SpecialistProfile.is_blocked` chowa profil. `is_verified` to tylko odznaka.
- Formularze mają jawną listę pól. Nie ma na nich `is_flagged`, `status`, `author`, `is_verified`, `is_blocked`, `visible_to_patients`.
- Turnstile (ADR 0013): `apps/core/captcha.py`. Bez obu kluczy `is_enabled()` jest fałszem, formularz gościa się nie renderuje, POST gościa idzie na login. Token sprawdzany po stronie serwera; błąd sieci = odmowa.
- Limity aplikacji, `settings.RATE_LIMITS`, dekorator `@ratelimit` i `check()` — okno stałe, `INSERT … ON CONFLICT` w PostgreSQL (na demo ten sam SQL na SQLite). Przekroczenie: szablon `429.html`, status 429.

| Zakres | Limit |
| --- | --- |
| `listing_create` | 10/h i 50/d na użytkownika (tylko tworzenie, nie edycja) |
| `organization_create` | 5/d na użytkownika |
| `inquiry` | 10/h na użytkownika, 30/h na IP |
| `inquiry_guest` | 3/h i 10/d na IP |
| `listing_report` | 10/h na użytkownika |
| `data_export` | 5/h na użytkownika |

Osobno allauth (`ACCOUNT_RATE_LIMITS`): signup 10/h/IP, złe logowanie 10/min/IP i 5/15 min na konto, reset hasła 10/h/IP i 3/h na adres. Liczniki allauth siedzą w cache bazy (`django_cache`, `createcachetable`).

- Hasło: min. 10 znaków, niepodobne do danych użytkownika, nie z listy popularnych, nie czysto numeryczne.
- `ACCOUNT_PREVENT_ENUMERATION = True`. `ACCOUNT_EMAIL_VERIFICATION`: w `prod.py` na sztywno `mandatory`.
- CSRF na POST, ciasteczka `HttpOnly`. Produkcja: `Secure`, nazwy `__Host-sessionid` i `__Host-csrftoken`, HSTS rok, przekierowanie na HTTPS, `SECURE_PROXY_SSL_HEADER`.
- CSP: `default-src 'self'`, skrypty tylko self i `https://challenges.cloudflare.com`, bez skryptów inline. `style-src` dopuszcza `'unsafe-inline'` (atrybuty w adminie). `form-action` obejmuje `https://accounts.google.com`.
- Szablony HTML nie wyłączają autoescape (test). Treść użytkownika jest tekstem (`whitespace-pre-line`), bez Markdownu. Mail zapytania to plik tekstowy `templates/listings/email/inquiry.txt` (tam `{% autoescape off %}` jest świadome — to nie HTML).
- `DATA_UPLOAD_MAX_MEMORY_SIZE` = 1 MB. Żaden widok nie przyjmuje plików.
- Admin produkcji: `DJANGO_ADMIN_URL` musi kończyć się `/` i nie może być `admin` ani pusty. `SECRET_KEY` co najmniej 50 znaków, nie `change-me…`.
- POST parametrów zapytania: `@sensitive_post_parameters`. Logi nie zawierają e-maili ani treści.

`verified_email_required` (allauth 65.19) sprawdza `EmailAddress.verified=True` także wtedy, gdy weryfikacja przy rejestracji jest `optional`. Brak potwierdzenia: ponowna wysyłka maila i szablon `account/verified_email_required.html`. Własny `has_verified_email` robi to samo zapytanie dla wiadomości i pokazuje polski komunikat.

## Ustawienia: dev, test, prod, demo

Wspólne: `config/settings/base.py`. `DEMO_MODE` domyślnie `False` (pasek w `templates/base.html` przez context processor `apps.core.context_processors.site`).

| | `dev.py` | `test.py` | `prod.py` | `demo.py` |
| --- | --- | --- | --- | --- |
| `DEBUG` | True | False | False | False |
| Baza | `DATABASE_URL` (Postgres w compose) | Postgres w pytest (CI); lint używa sqlite tylko do `makemigrations` | `DATABASE_URL` Postgres | SQLite, `DATABASE_URL` nadpisany zanim `base` go czyta. Ścieżka: `DEMO_SQLITE_PATH` albo plik w katalogu tymczasowym. `CONN_MAX_AGE=0` |
| Weryfikacja e-mail | `optional`, chyba że env | `optional` | zawsze `mandatory` | `optional` |
| Mail | z `EMAIL_URL`; compose: Mailpit `smtp://mailpit:1025` | locmem | `EMAIL_URL` z panelu Render | `console.EmailBackend` — nic nie dochodzi do skrzynki |
| HTTPS / HSTS / secure cookies | nie | nie | tak | tak (proxy Render) |
| Admin URL | domyślnie `admin/` | — | obowiązkowy, niezgadywalny | domyślnie `admin/` (plik demo go nie ustawia) |
| Statyczne | zwykły storage przy `runserver` | — | manifest WhiteNoise | ten sam manifest co obraz |
| `DEMO_MODE` | False | False | False | True |

Demo dokleja `RENDER_EXTERNAL_HOSTNAME` do `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` i `SITE_URL`. Start procesu: `scripts/run_demo.sh` → `prepare_demo` → gunicorn z `--workers 1`. `prepare_demo` odmawia pracy, gdy `DEMO_MODE` jest wyłączony: `migrate`, ewentualnie `createcachetable`, `loaddata reference_data`, `seed_demo`.

`seed_demo` odmawia, gdy nie ma ani `DEBUG`, ani `DEMO_MODE`. Jest idempotentny. Superuser `admin@example.com` powstaje tylko przy `DEBUG`. Na publicznym demo go nie ma. Hasło próbek: `demo12345`. Konta `anna@example.com`, `piotr@example.com`, `ola@example.com` mają `EmailAddress.verified=True`. Treść próbek: `apps/listings/management/commands/seed_demo.py`. Drugi przebieg nie dubluje ogłoszeń (`if Listing.objects.exists(): return` jest za organizacjami i profilami, więc same ogłoszenia powstają raz).

Skutek dla nowego konta na demo: allauth wpuszcza je bez kliknięcia w link (`optional`), ale `verified_email_required` i `has_verified_email` i tak żądają zweryfikowanego adresu. Mail potwierdzający ląduje w logu gunicorna. Publikacja, profil, organizacja, zgłoszenie i wiadomość na świeżym koncie demo nie przejdą. Przechodzą na trzech kontach z `seed_demo`.

## Jak uruchomić i testować lokalnie

Wymagania: Docker Compose v2, albo uv + sam Postgres.

```bash
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser
```

Aplikacja: http://localhost:8000 (admin lokalnie `/admin/`). Mailpit: http://localhost:8025. Compose ustawia `config.settings.dev`, migruje, ładuje `reference_data` i odpala `tailwind runserver`.

Bez kontenera aplikacji:

```bash
uv sync
docker compose up -d db
uv run python manage.py migrate && uv run python manage.py loaddata reference_data
uv run python manage.py tailwind runserver
```

Przed oddaniem zmiany (tak samo robi CI, plus `pip-audit` i budowa obrazu):

```bash
uv run ruff format .
uv run ruff check .
uv run mypy .
uv run lint-imports
uv run python manage.py makemigrations --check --dry-run
uv run pytest --cov
```

Testy tylko na PostgreSQL (`config/settings/test.py` czyta `DATABASE_URL`; lokalnie ten sam URL co w `.env.example`: `postgres://bartoszup:bartoszup@localhost:5432/bartoszup`). Pytest nie ma `conftest.py`. Jeden plik: `uv run pytest apps/listings/tests/test_permissions.py`. CI woła `uv run pytest --create-db --cov`. Lokalnie `addopts` ma `--reuse-db` (`pyproject.toml`).

Job linta w `.github/workflows/ci.yml` ustawia `DATABASE_URL=sqlite:///ci.db` tylko po to, żeby przeszły `makemigrations --check` i mypy. Same testy idą osobnym jobem na Postgres 17. Testów nie przerzuca się na SQLite: kontrakt repozytorium to PostgreSQL (`AGENTS.md`), a limiter i tak jest opisany pod Postgres (ADR 0014), nawet jeśli demo wykonuje ten sam `INSERT … ON CONFLICT` na SQLite.

Próg pokrycia: 97% (`[tool.coverage.report] fail_under` w `pyproject.toml`), gałęzie włączone. Pomiar omija `*/migrations/*` i `*/tests/*`. Nowy warunek uprawnień: test dozwolony i odmowa. Nowy filtr: test, że zawęża. CI: ruff (z bandit `S`), mypy, import-linter, `makemigrations --check`, `check --deploy` na `prod`, pytest z Postgres 17, `pip-audit --strict`, budowa celu Docker `prod`.

Mail lokalnie: compose stawia Mailpit, `EMAIL_URL=smtp://mailpit:1025`, skrzynka http://localhost:8025. Bez compose `base.py` bierze `EMAIL_URL` z domyślnym `consolemail://` — listy widać w terminalu procesu.

Obraz produkcyjny lokalnie: sekcja na końcu [deployment.md](deployment.md). `Dockerfile` ma cele `base`, `dev`, `build` (tailwind + `collectstatic` przy atrapie ustawień prod), `prod` (użytkownik `app`, gunicorn, `WEB_CONCURRENCY` domyślnie 3).

## Co wdraża `render.yaml`, a co `render.demo.yaml`

Nie mieszać tych plików. ADR 0011 i 0017, [deployment.md](deployment.md).

| | `render.yaml` — pełna wersja | `render.demo.yaml` — demo |
| --- | --- | --- |
| Status | Nie wdrożone. Adres w pliku: `bartoszup.onrender.com` | Adres usługi: `bartoszup-demo.onrender.com` |
| Plan | web Starter, cron Starter, Postgres Basic 256 MB, region Frankfurt, Postgres 17 | jedna usługa web, `plan: free`, Frankfurt, bez bazy i bez crona |
| Ustawienia | `config.settings.prod` | `config.settings.demo` |
| Start | `preDeployCommand`: `migrate` i `createcachetable`. Obraz trzyma CMD gunicorn, `WEB_CONCURRENCY=2` | `dockerCommand`: `sh scripts/run_demo.sh` (migrate + fixture + seed przy każdym starcie procesu, 1 worker) |
| Sekrety `sync: false` | `EMAIL_URL`, `DEFAULT_FROM_EMAIL`, Google, `DJANGO_ADMIN_EMAILS`, `DJANGO_ADMIN_URL`, oba klucze Turnstile | brak — poczta, Google i Turnstile są wyłączone |
| Dane | `loaddata reference_data` raz, ręcznie, potem `createsuperuser` | przy każdym starcie od nowa, bo dysk planu Free nie jest trwały |
| Health | `/healthz/` | `/healthz/` |

Plan Free zasypia bez ruchu (u Rendera zwykle po około 15 minutach). Następne wejście czeka na start procesu; `prepare_demo` buduje schemat i próbki od zera. Konta założone przez odwiedzających znikają razem z uśpieniem. ADR 0017: na tym adresie nie zbierać prawdziwych danych osobowych.

`render.yaml` nie jest tym, czym stoi demo. Włączenie go zakłada płatny web, cron i Postgres.

## Gdzie zmieniać zachowanie

| Chcesz zmienić | Plik |
| --- | --- |
| Kto może edytować ogłoszenie, pisać, zgłaszać | `apps/listings/permissions.py` + testy w `test_permissions.py` / `test_security.py` |
| Kto zarządza organizacją | `Membership.MANAGER_ROLES`, `organizations/services.py` |
| Przejścia statusu, 60 dni, widoczność publiczna | `Listing.publish` / `ALLOWED_TRANSITIONS` / `public()`; dni: `LISTING_DEFAULT_LIFETIME_DAYS` |
| Pola formularza ogłoszenia i które pola zostają przy danym `kind` | `apps/listings/forms.py` (`FIELDS_BY_KIND`), szablon `templates/listings/listing_form.html`, chowanie pól: `static/js/listing-form.js` |
| Filtry listy | `apps/listings/filters.py`, `apps/profiles/filters.py` |
| Tekst maila do autora | `templates/listings/email/inquiry.txt`, wysyłka w `listings/services.py` |
| Próg auto-ukrycia | `LISTING_REPORTS_AUTO_FLAG` |
| Limity | `RATE_LIMITS` i `ACCOUNT_RATE_LIMITS` w `base.py` |
| Retencja wiadomości | `INQUIRY_RETENTION_DAYS`, cron `daily_maintenance` |
| Pasek demo | `DEMO_MODE` i `templates/base.html` |
| Próbki demo | `seed_demo.py` (odmowa poza DEBUG/DEMO_MODE) |
| Słownik miast i specjalizacji | fixture `reference_data.json` (pk stabilne) albo admin |
| Moderacja | `apps/*/admin.py` |
| Eksport / kasowanie konta | `apps/privacy/services.py` — nowe dane osobowe dopisać tu i w teście |
| Teksty dla użytkownika | polski, `gettext_lazy` / `{% translate %}`. Angielski zostaje w kodzie, komentarzach i commitach (ADR 0005) |
| Nowa decyzja o kształcie systemu | nowy plik w `docs/adr/` ze `template.md`, wpis w `docs/adr/README.md` |
| Zmiana modelu | migracja w tym samym commicie + `docs/domain-model.md` |

Nowy widok zmieniający dane: `require_POST`, sprawdzenie obiektu (403 przy edycji cudzego, 404 przy niewidocznym), test obu stron, przy publikacji i kontakcie `verified_email_required`, przy POSTcie podatnym na nadużycie `@ratelimit` i wpis w `RATE_LIMITS` plus test 429. Bez `|safe` i bez `on*=` w HTML. Nowy zewnętrzny host (skrypt, ramka) dopisać do `CONTENT_SECURITY_POLICY` świadomie.

Faza 2 (kalendarz godzin, płatności, promowane ogłoszenia) i faza 3 (wizyty pacjentów, RODO art. 9) są opisane w [roadmap.md](roadmap.md). W kodzie ich nie ma. Nie dodawać danych o zdrowiu bez osobnego zadania i ADR (ADR 0009).

## Wskazówki do istniejących dokumentów

| Dokument | Po co |
| --- | --- |
| [architecture.md](architecture.md) | Kontekst, kontenery, granice modułów |
| [domain-model.md](domain-model.md) | ER, cykl życia, tabela uprawnień |
| [security.md](security.md) | Model zagrożeń, kontrolki, luki (MFA moderatorów, kontakt bezpieczeństwa, Sentry, weryfikacja `TRUSTED_PROXY_COUNT` po pierwszym wdrożeniu, żałoba zgłoszeniami, wersje robocze regulaminu) |
| [deployment.md](deployment.md) | Checklista pierwszego płatnego wdrożenia, zmienne, RODO operacyjne |
| [roadmap.md](roadmap.md) | Faza 1 (to, co jest), 2 (płatności), 3 (pacjenci) |
| [adr/](adr/README.md) | 0001–0017, wszystkie Accepted |
| [AGENTS.md](../AGENTS.md) | Konwencje dla zmian w kodzie |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Gałęzie, Conventional Commits |

## Różnice, które łatwo pomylić

1. Żywy adres https://bartoszup-demo.onrender.com to `render.demo.yaml` + `config.settings.demo`. `render.yaml` (Postgres, cron, prawdziwa poczta, tajny admin, miejsce na Turnstile i Google) nie jest wdrożony. [deployment.md](deployment.md) mówi o tym płatnym starcie „Nothing is deployed yet”.
2. Na demo weryfikacja przy logowaniu jest `optional`, a mail idzie do konsoli. Bramki publikacji i tak wymagają `EmailAddress.verified`. Działają konta z `seed_demo`, nie świeża rejestracja.
3. Bez kluczy Turnstile gość nie wyśle wiadomości. W `render.demo.yaml` kluczy nie ma. Pełna wersja ma je jako sekrety do wpisania; bez nich zachowa się tak samo (zamknięte, ADR 0013).
4. Demo nie uruchamia `daily_maintenance`. Lista i tak chowa ogłoszenie po `expires_at`. Status w bazie zostaje `published`, dopóki cron nie zrobi `expire()`. Na demo baza i tak powstaje od nowa przy każdym starcie.
5. Demo nie seeduje superusera. `/admin/` na demo odpowiada, konta moderatora nie ma. Produkcja w ogóle nie wstanie z adresem `admin/`.
6. Płatności i rezerwacja wizyt nie istnieją w żadnej z tych konfiguracji. `visible_to_patients` i `RoomAvailabilityBlock` są przygotowaniem pod później, bez widoków rezerwacji.
7. `config/settings/base.py` czyta `EMAIL_URL` z domyślnym `consolemail://`. `prod.py` tego nie zaostrza. Brak sekretu na Renderze nie wywala startu: weryfikacja zostaje `mandatory`, a listy idą w konsolę procesu. `render.yaml` oznacza `EMAIL_URL` jako `sync: false` — trzeba go wpisać ręcznie.
8. Cron w `render.yaml` ma własny `DJANGO_SECRET_KEY` (`generateValue: true`), inny niż web. `daily_maintenance` nie podpisuje ciasteczek, więc do wygaszania to wystarcza. Nie wołaj z crona niczego, co sprawdza podpis sesji, licząc na wspólny sekret.
9. `STORAGES["default"]` w prod i demo to `FileSystemStorage`, ale żaden widok nie przyjmuje pliku. `MEDIA_ROOT` / `MEDIA_URL` nie są ustawione. `DATA_UPLOAD_MAX_MEMORY_SIZE` to 1 MB. Plan zdjęć (UE, Pillow, EXIF, signed URL) jest w `docs/security.md` i nie jest zaimplementowany.

## Luki operacyjne

### Poczta

Wysyłka zapytania jest synchroniczna w żądaniu HTTP: `EmailMessage.send()` w `send_inquiry`. Wyjątek jest łapany, log idzie z samym `inquiry_id`, wiersz zostaje z `email_sent=False`. Nie ma ponowienia, kolejki, Celery ani workera. Mail weryfikacyjny allauth idzie tym samym backendem, też bez kolejki.

Na demo `config/settings/demo.py` wymusza `console.EmailBackend`. Na dev z compose listy łapie Mailpit. Prod bez `EMAIL_URL` też ląduje w konsoli procesu (punkt 7 wyżej). SPF/DKIM/DMARC nie są w repozytorium — `docs/security.md` wymienia je jako brak. `DEFAULT_FROM_EMAIL` jest sekretem `sync: false` w `render.yaml`.

Skrzynki użytkownika nie ma. Autor pełnej wersji czyta maila u siebie. Na demo treść da się zobaczyć tylko w bazie: eksport JSON albo (lokalnie, przy `DEBUG`) konto `admin@example.com` z `seed_demo`. Publiczne demo superusera nie seeduje.

### Turnstile

`apps/core/captcha.py`: `is_enabled()` wymaga obu kluczy. `verify()` POST na stały `https://challenges.cloudflare.com/turnstile/v0/siteverify`, timeout 5 s. Pusty token, brak kluczy albo błąd sieci zwracają `False` (zamknięte, ADR 0013). Widok gościa przy wyłączonym captcha nie renderuje formularza i POST kieruje na login. CSP puszcza skrypt i ramkę tylko z `challenges.cloudflare.com` (`base.py`). `render.demo.yaml` kluczy nie deklaruje. Klucze testowe Cloudflare, które zawsze przechodzą, są opisane w `.env.example` i nie są wpisane w demo.

### Pliki

Nie ma `FileField` ani `ImageField` w modelach aplikacji. CV, logo, zdjęcie profilu i zdjęcie gabinetu nie mają gdzie wylądować. WhiteNoise serwuje pliki statyczne z obrazu, nie uploady. Dopóki nie ma magazynu w UE opisanego w `docs/security.md`, nie dodawaj pola pliku „na razie na dysk kontenera” — dysk demo i tak znika, a prod nie ma tej ścieżki w `render.yaml`.

### Cron

Jedno polecenie: `python manage.py daily_maintenance` (`apps/listings/management/commands/daily_maintenance.py`) woła `expire_due_listings`, `purge_old_inquiries` (`INQUIRY_RETENTION_DAYS`, domyślnie 365) i `purge_old_windows`. Starsze `expire_listings` robi tylko pierwsze. Harmonogram płatnego blueprintu: `15 3 * * *` w `render.yaml`, osobna usługa, region Frankfurt. Demo (`render.demo.yaml`, `scripts/run_demo.sh`) crona nie startuje.

Lista i tak chowa wiersz po `expires_at`, bo `public()` porównuje datę w żądaniu. Bez crona status w bazie zostaje `published`. Na demo i tak każda pobudka buduje SQLite od zera (`prepare_demo`).

Cache limitów allauth to tabela `django_cache` (`DatabaseCache`). Web tworzy ją w `preDeployCommand` (`render.yaml`) albo w `prepare_demo`. Bez tabeli limity allauth nie mają gdzie zapisać okna.

## Czego nie scalać

To nie jest gust. To rzeczy, które ten repozytorium już odrzuca albo które ADR każe odłożyć:

- Kierunek importów pod prąd albo zapytanie `Membership` z `listings` z pominięciem `organizations.services`. `uv run lint-imports` ma kontrakt warstw w `pyproject.toml`. Niższy moduł pokazuje ogłoszenia tagiem `organization_listings` / `personal_listings` (`apps/listings/templatetags/listing_tags.py`).
- Ręczne `listing.status = ...` w widoku. Przejścia idą przez `publish()` / `archive()` / `expire()`. Wyjątek już jest w `expire_due_listings` (`QuerySet.update` na `due_to_expire()`).
- Nowe dane osobowe bez wpisu w `privacy.services.export_user_data` i `delete_account` oraz bez testu w `apps/privacy/tests/test_privacy.py`.
- Pole moderacji albo właściciela na formularzu (`is_flagged`, `status`, `author`, `is_verified`, `is_blocked`, `visible_to_patients`).
- `|safe`, `mark_safe`, `{% autoescape off %}` w szablonie HTML, inline `<script>` albo `on*=`. Test szablonów to wyłapuje. Wyjątek świadomy: `templates/listings/email/inquiry.txt`.
- Widok zmieniający stan bez `require_POST`, bez 403/404 i bez pary testów dozwolone/odmowa. POST podatny na nadużycie bez `@ratelimit` i wpisu w `RATE_LIMITS` plus testu 429.
- Obniżenie `fail_under` poniżej 97 albo testy na SQLite.
- Sekret w kodzie. `prod.py` nie wstanie przy `DJANGO_SECRET_KEY` krótszym niż 50 znaków albo zaczynającym się od `change-me`, ani przy `DJANGO_ADMIN_URL` równym `admin/` lub bez końcowego `/`.
- Dane o zdrowiu, powód wizyty, konto pacjenta albo podpięcie `visible_to_patients` do publicznej listy bez osobnego zadania i ADR (ADR 0009). Samo pole w schemacie nie jest zgodą na fazę 3.
- Traktowanie `RoomAvailabilityBlock` jako terminarza rezerwacji (nakładanie, płatność, „zajęte”). ADR 0006 trzyma kalendarz w przyszłym module.
- `FileField` zanim powstanie magazyn z sekcji „File uploads” w `docs/security.md`.

## Katalog pacjentów, gdy przyjdzie na to zadanie

Dziś go nie ma. `SpecialistProfile.objects.public()` filtruje `is_public`, `is_blocked` i `user.is_active`. Nie filtruje `visible_to_patients`. Podpięcie tej flagi do istniejącej listy `/specjalisci/` schowałoby wizytówki branżowe (domyślnie `False`) i nadal nie dałoby cennika sesji ani rezerwacji. `open_to_work` to sygnał dla poradni, że ktoś szuka pracy, nie że przyjmuje pacjentów.

Gdy będzie osobne zadanie i ADR, punkt wejścia opisany w `docs/roadmap.md`, `docs/domain-model.md` i ADR 0009 wygląda tak:

- nowy moduł nad `profiles` i `organizations` (roadmap: `booking`), rozmawiający w dół przez `services.py`, nie przez import wewnętrznych query;
- osobny widok katalogu, świadomie filtrowany `visible_to_patients`, zostawiający obecną listę specjalistów bez tej flagi;
- brak powodu wizyty i notatek; `Inquiry` zostaje wiadomością B2B przy `Listing` — nie używać go jako zgłoszenia pacjenta;
- przed kodem, który zapisuje sam fakt wizyty: DPIA i podstawa z art. 9, hosting i podprocesorzy w EOG (ADR 0009). Samo „dorobić wyszukiwarkę” bez tego miesza dane szczególnej kategorii z tablicą ogłoszeń.

`visible_to_patients` można przeczytać w `apps/profiles/models.py`. Żaden widok, formularz ani `public()` go nie czyta. Test `test_new_profiles_are_not_exposed_to_patients` sprawdza tylko domyślne `False`.
