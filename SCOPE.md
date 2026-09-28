# SCOPE

## English summary

BartoszUP is a Polish-language platform for the mental-health industry: psychologists, psychotherapists, clinics and NGOs.
The working product is a job, internship and volunteering board, "looking for work" posts, therapy-room listings, and profile pages.
The free demo (`render.demo.yaml`, SQLite, invented data) uses the same screens as `main`, plus a yellow banner; `render.yaml` (PostgreSQL, Frankfurt) is not deployed.
Patient booking, payments and a second deployable service are out of scope until a separate task and an ADR.
This file is the entry point: follow its links; `AGENTS.md` holds the short rules for changing code.

## Reguła SCOPE

Nie ma jednego branżowego pliku o nazwie SCOPE. W tym repozytorium SCOPE znaczy:

- **S — Subject:** czym jest BartoszUP, dla kogo jest, czym demo różni się od pełnego produktu.
- **C — Context:** stos, architektura, decyzje już podjęte (linki, nie kopie dokumentów).
- **O — Outcomes and out of scope:** co działa dziś i czego nie wolno jeszcze budować (rezerwacja wizyt, płatności, rozcięcie na drugi serwis).
- **P — Practices:** jak zmieniać kod, granice modułów, testy, bezpieczeństwo, język.
- **E — Execution:** dokładne polecenia instalacji, uruchomienia i testów oraz różnica między `render.demo.yaml` a `render.yaml`.

Ten plik ładuje się przy każdym wejściu. Dalej idź linkami. Indeks tych samych liter: [docs/README.md](docs/README.md).

## S — Subject

BartoszUP to polska strona dla branży zdrowia psychicznego. Ma zastąpić grupę na Facebooku jednym miejscem z wyszukiwarką.

Dla kogo: psycholog, psychoterapeuta, student, poradnia, fundacja, OPS, właściciel gabinetu, moderator. Pacjent nie jest użytkownikiem tej fazy.

Dwa filary: tablica ogłoszeń (praca, staż/praktyki, wolontariat, „szukam pracy/stażu”) oraz wynajem gabinetu na godzinę, dzień albo miesiąc, razem z wizytówkami specjalistów i organizacji.

Demo i pełny produkt to dwie różne rzeczy. Żywy adres https://bartoszup-demo.onrender.com to darmowe demo: wymyślone dane, żółty pasek, dane znikają po uśpieniu. Pełna wersja jest przygotowana w `render.yaml` (adres w pliku: https://bartoszup.onrender.com) i nie jest wdrożona. Płatności i wizyt pacjentów nie ma w żadnej z nich.

- Produkt i szybki start: [README.md](README.md)
- Co da się kliknąć na stronie: [docs/jak-dziala.md](docs/jak-dziala.md)
- Fazy dla właściciela: [docs/roadmap.md](docs/roadmap.md)

## C — Context

Jeden proces Django 5.2 na Pythonie 3.13, szablony HTML, HTMX 2, Tailwind CSS 4 bez Node.js. Pełna wersja i testy: PostgreSQL 17. Demo: SQLite. Konta: django-allauth (e-mail; Google dopiero po kluczach). Hosting docelowy: Render, region Frankfurt. Narzędzia: uv, ruff, mypy, pytest, import-linter, pre-commit.

Architektura to modularny monolit: jeden deploy, jedna baza, aplikacje Django z importami tylko w dół: `privacy` → `listings` → `profiles` | `organizations` → `accounts` → `core`. `profiles` i `organizations` nie importują się nawzajem. Wołanie między aplikacjami idzie przez `services.py` niższej warstwy. Granice pilnuje import-linter.

Decyzje 0001–0017 są przyjęte. Nowej nie wpisuje się wstecz: kopiuje się [docs/adr/template.md](docs/adr/template.md).

- Diagramy kontekstu, kontenerów i modułów: [docs/architecture.md](docs/architecture.md)
- Segmenty, które da się wymienić bez edycji pozostałych: [docs/segmenty.md](docs/segmenty.md)
- Stos, drzewo katalogów, ustawienia `dev` / `test` / `prod` / `demo`: [docs/przewodnik-techniczny.md](docs/przewodnik-techniczny.md)
- Model danych i cykl życia ogłoszenia: [docs/domain-model.md](docs/domain-model.md)
- Spis ADR: [docs/adr/README.md](docs/adr/README.md)
- Wdrożenie i zmienne: [docs/deployment.md](docs/deployment.md)

## O — Outcomes and out of scope

Działa dziś (faza 1, kod na `main`):

- Konto e-mailem, jeden typ konta, organizacje z rolami, wizytówki specjalistów.
- Pięć rodzajów ogłoszeń w jednej tabeli `Listing`: szkic, publikacja, wygaśnięcie po 60 dniach, archiwum.
- Filtry, strony pod SEO, moderacja w adminie, zgłoszenie ogłoszenia, wiadomość do autora.
- RODO przy koncie: zgoda, eksport, usunięcie konta, kasowanie starych wiadomości.
- Gość czyta strony publiczne. Publikacja i kontakt wymagają potwierdzonego e-maila. Gość pisze tylko przy włączonym Cloudflare Turnstile; na demo tego nie ma.

Poza zakresem, dopóki nie ma osobnego zadania i ADR:

- Rezerwacja wizyt, katalog dla pacjentów, cennik sesji, dane o zdrowiu (RODO art. 9). Pole `visible_to_patients` jest w modelu i jest wyłączone. Nie podłączać go do listy.
- Płatności, faktury, ogłoszenia promowane i kalendarz rezerwacji godzin (faza 2). `RoomAvailabilityBlock` to stałe dni tygodnia, nie terminarz.
- Drugi serwis albo mikroserwisy. Zostaje jeden deploy (ADR 0002). Osobny moduł rezerwacji jest tematem fazy 3, nie bieżącej zmiany.
- Zdjęcia, CV i inne pliki. Nie dodawać `FileField` na dysk kontenera.

- Co jest zbudowane i co czeka: [docs/roadmap.md](docs/roadmap.md)
- Zachowanie strony, porównanie demo i kierunki: [docs/jak-dziala.md](docs/jak-dziala.md)
- Schemat „na później”, bez widoków: [docs/domain-model.md](docs/domain-model.md)
- Zakaz danych o zdrowiu: [docs/adr/0009-gdpr-eu-hosting-no-health-data.md](docs/adr/0009-gdpr-eu-hosting-no-health-data.md)
- Monolit, nie drugi serwis: [docs/adr/0002-modular-monolith.md](docs/adr/0002-modular-monolith.md)

### Żywe demo a kod na `main`

Ekrany wyglądają prawie tak samo. Demo i `main` dzielą szablony. Na https://bartoszup-demo.onrender.com nad menu jest żółty pasek: „To jest demo. Dane są wymyślone i nie jest to prawdziwa usługa.” Strona główna bez paska (lokalnie, `DEMO_MODE` wyłączone): [docs/preview/preview-home.png](docs/preview/preview-home.png).

| | `render.demo.yaml` (żywe demo) | `render.yaml` (pełna wersja, nie wdrożona) |
| --- | --- | --- |
| Wygląd | Te same ekrany plus żółty pasek | Te same ekrany, bez paska. Osobnego projektu graficznego nie ma. |
| Dane | SQLite w kontenerze. Plan Free zasypia, dysk znika, przy starcie próbki wracają od nowa. | PostgreSQL. Konta i ogłoszenia zostają. |
| Konta próbek | Trzy: `anna@example.com`, `piotr@example.com`, `ola@example.com`, hasło `demo12345`. Superusera nie ma. | Brak próbek. Moderator ma tajny adres admina. |
| Poczta | Nie wychodzi. Świeże konto nie potwierdzi adresu, więc nie opublikuje. | Ma wychodzić, gdy ktoś wpisze `EMAIL_URL`. |
| Gość | Bez Turnstile nie ma formularza. Widać „Zaloguj się”. | Formularz gościa, gdy są klucze Turnstile. |
| Cron | Nie ma `daily_maintenance`. | Jest: wygaszanie ogłoszeń i kasowanie starych wiadomości. |

Płatności i rezerwacji wizyt nie ma w żadnej z tych kolumn. To nie jest różnica demo i pełnej wersji.

### Pieniądze (nie zbudowane)

W kodzie dodanie ogłoszenia nic nie kosztuje. Poniższe modele są tylko kierunkiem. Cen nie ma, bo nikt ich nie ustalił. Szczegóły faz: [docs/roadmap.md](docs/roadmap.md).

- Ogłoszenie promowane: wyróżnienie na liście i na stronie głównej. Trzeba dodać oznaczenie opłaconego ogłoszenia i sortowanie. Faza 2.
- Abonament poradni: pakiet liczby ogłoszeń w okresie. Trzeba dodać zapis abonamentu przy organizacji i bramkę w `publish()`. Faza 2.
- Prowizja od wynajmu gabinetu: dopiero gdy istnieje kalendarz rezerwacji, od zakończonej rezerwacji. Dziś `RoomAvailabilityBlock` nikogo nie rezerwuje. Faza 2, [ADR 0006](docs/adr/0006-single-listing-table.md).
- Opłata od wizyty pacjenta: później, przy rezerwacji B2C. Dziś nie ma konta pacjenta ani cennika sesji. Faza 3, [ADR 0009](docs/adr/0009-gdpr-eu-hosting-no-health-data.md).

### Kierunki (nie zbudowane)

Produkt, który obecny model już dopuszcza, a kodu jeszcze nie ma: filtr B2B na istniejącym polu formy zatrudnienia; rodzaj albo znacznik „szukam gabinetu”; zdjęcia i CV po magazynie plików w UE; zaproszenia do organizacji ze strony (dziś robi to admin); sprawdzenie numeru uprawnień w rejestrze (dziś to zwykły tekst); katalog pacjentów na fladze `visible_to_patients`. Luki grupy: [docs/jak-dziala.md](docs/jak-dziala.md). Plan: [docs/roadmap.md](docs/roadmap.md).

Technicznie architektura już wskazuje: magazyn plików w UE ([ADR 0011](docs/adr/0011-hosting-render-frankfurt.md), [docs/security.md](docs/security.md)); kolejkę maili zamiast wysyłki w żądaniu HTTP ([docs/architecture.md](docs/architecture.md)); 2FA dla personelu ([ADR 0008](docs/adr/0008-authentication-django-allauth.md), [ADR 0015](docs/adr/0015-http-security-hardening.md)); wydzielenie wynajmu do modułu `rooms`, gdy powstanie kalendarz ([ADR 0006](docs/adr/0006-single-listing-table.md)); płatności w fazie 2. Drugiego deployu na teraz nie robić ([ADR 0002](docs/adr/0002-modular-monolith.md)).

## P — Practices

Kod, identyfikatory, komentarze, commity i dokumenty dla programistów są po angielsku. Teksty dla użytkownika są po polsku, w `gettext_lazy` albo `{% translate %}`. Adresy są polskie: `/ogloszenia/`, `/specjalisci/`, `/organizacje/`, `/panel/`.

Nie importować w górę. Niższy moduł pokazuje dane wyższego tagami szablonów (`listings/templatetags/listing_tags.py`). Widoki zostają cienkie. Status ogłoszenia zmienia się tylko przez `Listing.publish()`, `archive()` i `expire()`. Listy publiczne biorą się z `.public()`.

Zmiana stanu: `require_POST`, uprawnienie do obiektu (403 przy edycji, 404 przy niewidocznym obiekcie), test strony dozwolonej i odmowy. Publikacja i kontakt: `verified_email_required`. POST podatny na nadużycie: `@ratelimit` oraz wpis w `RATE_LIMITS`, plus test 429. Bez `|safe` i bez skryptów w HTML. Nowe dane osobowe wchodzą do eksportu i usuwania w `apps/privacy/services.py`.

Zmiana modelu: migracja w tym samym commicie i aktualizacja `docs/domain-model.md`. Istotna decyzja: nowy ADR. Commity: Conventional Commits. Gałęzie krótkie od `main`. Przed oddaniem zmiany: polecenia z sekcji E.

- Reguły przy każdej zmianie: [AGENTS.md](AGENTS.md)
- Gałęzie, commity, review: [CONTRIBUTING.md](CONTRIBUTING.md)
- Zagrożenia i kontrolki: [docs/security.md](docs/security.md)
- Skrót dla Cursora: [.cursor/rules/](.cursor/rules/)
- Język interfejsu: [docs/adr/0005-polish-only-ui-i18n-ready.md](docs/adr/0005-polish-only-ui-i18n-ready.md)

## E — Execution

Wymagania: Docker z Compose v2 albo uv i sam Postgres.

Całość w Dockerze:

```bash
git clone https://github.com/Tomekw2323/BartoszUP.git && cd BartoszUP
cp .env.example .env
docker compose up --build -d
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser
```

Aplikacja: http://localhost:8000. Poczta (Mailpit): http://localhost:8025. Admin lokalnie: `/admin/`. Po `seed_demo`: `anna@example.com`, `piotr@example.com`, `admin@example.com`, hasło `demo12345`.

Aplikacja poza kontenerem:

```bash
uv sync
docker compose up -d db
uv run python manage.py migrate && uv run python manage.py loaddata reference_data
uv run python manage.py tailwind runserver
```

Przed oddaniem zmiany (CI robi to samo oraz `pip-audit` i budowę obrazu):

```bash
uv run ruff format . && uv run ruff check .
uv run mypy .
uv run lint-imports
uv run python manage.py makemigrations --check --dry-run
uv run pytest --cov
```

Testy idą na PostgreSQL, nie na SQLite.

`render.demo.yaml` i `render.yaml` to dwa wdrożenia. Nie podstawiać jednego za drugie.

| | `render.demo.yaml` | `render.yaml` |
| --- | --- | --- |
| Rola | Darmowe demo do przeklikania | Płatny start, jeszcze nie wdrożony |
| Usługi | Jedna usługa web, plan free, bez bazy i bez crona | Web Starter, cron, Postgres 17 Basic 256 MB, Frankfurt |
| Ustawienia | `config.settings.demo` | `config.settings.prod` |
| Dane | SQLite w kontenerze, od nowa przy każdym starcie (`scripts/run_demo.sh`) | Trwała baza, migracje w `preDeployCommand` |
| Poczta, Google, Turnstile | Wyłączone | Sekrety w panelu (`sync: false`) |

- Szybki start i tabela plików Render: [README.md](README.md)
- Różnice demo i prod: [docs/przewodnik-techniczny.md](docs/przewodnik-techniczny.md)
- Checklista płatnego wdrożenia: [docs/deployment.md](docs/deployment.md)
- Dlaczego demo jest na SQLite: [docs/adr/0017-free-demo-sqlite.md](docs/adr/0017-free-demo-sqlite.md)
- Hosting Frankfurt: [docs/adr/0011-hosting-render-frankfurt.md](docs/adr/0011-hosting-render-frankfurt.md)
