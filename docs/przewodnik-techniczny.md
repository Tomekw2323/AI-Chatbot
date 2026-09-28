# Przewodnik techniczny BartoszUP

Dla osoby, która nadzoruje zmiany i nie pisała tego kodu. Stan gałęzi `main`: `71a09807` (2026-09-28). Opisuje to, co jest w repozytorium. Rezerwacji wizyt i płatności w kodzie nie ma.

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

Widoczność publiczna ogłoszenia (`is_publicly_visible` i `public()`): `status=published`, `expires_at` puste albo w przyszłości, `is_flagged=False`, organizacja nie jest `is_blocked`. Cron tylko porządkuje status. Po terminie ogłoszenie znika z list zanim status zdąży zmienić się na `expired`.

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

Kasowanie konta (`privacy.services.delete_account`):

- jedyny członek → organizacja jest kasowana (ogłoszenia kaskadą);
- jest inny owner → nic nie awansuje;
- nie ma drugiego ownera, jest admin → najstarszy admin (`created_at`) dostaje `owner`;
- są tylko `member` → `AccountDeletionBlockedError`, widok pokazuje komunikat i nie kasuje;
- ogłoszenia organizacji autora przechodzą na owner/admin (kolejność `-role`, `created_at`); prywatne ogłoszenia znikają z userem (`CASCADE`);
- `Inquiry` nadawcy i wiersze z tym samym `sender_email` są kasowane przed `user.delete()`.

Eksport: `privacy.services.export_user_data` — JSON, `Content-Disposition`, `Cache-Control: no-store`.

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

Testy tylko na PostgreSQL (`config/settings/test.py`, `DATABASE_URL`). Próg pokrycia: 97% (`[tool.coverage.report] fail_under` w `pyproject.toml`), gałęzie włączone, migracje i testy pominięte w pomiarze. Nowy warunek uprawnień: test dozwolony i odmowa. Nowy filtr: test, że zawęża. CI (`.github/workflows/ci.yml`): ruff, mypy, import-linter, `makemigrations --check`, `check --deploy` na `prod`, pytest z Postgres 17, `pip-audit --strict`, budowa celu Docker `prod`.

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
