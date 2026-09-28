# Dokumentacja

Indeks według liter z [SCOPE.md](../SCOPE.md). Pliki zostają tam, gdzie już są. Litery znaczą: Subject, Context, Outcomes and out of scope, Practices, Execution.

## S — Subject

Czym jest BartoszUP, dla kogo, czym demo różni się od pełnego produktu.

- [SCOPE.md](../SCOPE.md) — plik wejścia
- [README.md](../README.md) — opis produktu, podgląd, szybki start
- [jak-dziala.md](jak-dziala.md) — co da się zrobić na stronie; demo a `main` (te same ekrany, żółty pasek)
- [roadmap.md](roadmap.md) — fazy 1–3

## C — Context

Stos, architektura, decyzje już podjęte.

- [architecture.md](architecture.md) — kontekst, kontenery, granice modułów
- [segmenty.md](segmenty.md) — segmenty monolitu i nazwy, które wolno wołać z innego segmentu
- [przewodnik-techniczny.md](przewodnik-techniczny.md) — stos, drzewo katalogów, przepływ żądania
- [domain-model.md](domain-model.md) — model danych, cykl życia, moderacja
- [deployment.md](deployment.md) — Render, zmienne, notatki RODO przy wdrożeniu
- [adr/README.md](adr/README.md) — spis ADR 0001–0017
- [adr/template.md](adr/template.md) — szablon nowej decyzji
- [adr/0001-record-architecture-decisions.md](adr/0001-record-architecture-decisions.md)
- [adr/0002-modular-monolith.md](adr/0002-modular-monolith.md)
- [adr/0003-django-and-postgresql.md](adr/0003-django-and-postgresql.md)
- [adr/0004-server-rendered-html-htmx-tailwind.md](adr/0004-server-rendered-html-htmx-tailwind.md)
- [adr/0005-polish-only-ui-i18n-ready.md](adr/0005-polish-only-ui-i18n-ready.md)
- [adr/0006-single-listing-table.md](adr/0006-single-listing-table.md)
- [adr/0007-single-account-type-organizations.md](adr/0007-single-account-type-organizations.md)
- [adr/0008-authentication-django-allauth.md](adr/0008-authentication-django-allauth.md)
- [adr/0009-gdpr-eu-hosting-no-health-data.md](adr/0009-gdpr-eu-hosting-no-health-data.md)
- [adr/0010-tooling.md](adr/0010-tooling.md)
- [adr/0011-hosting-render-frankfurt.md](adr/0011-hosting-render-frankfurt.md)
- [adr/0012-moderation-and-posting-rules.md](adr/0012-moderation-and-posting-rules.md)
- [adr/0013-guest-contact-with-turnstile.md](adr/0013-guest-contact-with-turnstile.md)
- [adr/0014-rate-limiting-in-postgresql.md](adr/0014-rate-limiting-in-postgresql.md)
- [adr/0015-http-security-hardening.md](adr/0015-http-security-hardening.md)
- [adr/0016-gdpr-self-service-and-retention.md](adr/0016-gdpr-self-service-and-retention.md)
- [adr/0017-free-demo-sqlite.md](adr/0017-free-demo-sqlite.md)

## O — Outcomes and out of scope

Co działa dziś i czego nie budować (rezerwacja wizyt, płatności, drugi serwis).

- [roadmap.md](roadmap.md) — faza 1 zbudowana, faza 2 płatności, faza 3 pacjenci
- [jak-dziala.md](jak-dziala.md) — demo a pełna wersja, modele pieniędzy (nie zbudowane), luki grupy
- [domain-model.md](domain-model.md) — pola przygotowane pod fazę 3, bez widoków
- [adr/0002-modular-monolith.md](adr/0002-modular-monolith.md) — jeden deploy, nie mikroserwisy
- [adr/0006-single-listing-table.md](adr/0006-single-listing-table.md) — kalendarz zostaje na później
- [adr/0009-gdpr-eu-hosting-no-health-data.md](adr/0009-gdpr-eu-hosting-no-health-data.md) — bez danych o zdrowiu

## P — Practices

Jak zmieniać kod, granice modułów, testy, bezpieczeństwo, język.

- [AGENTS.md](../AGENTS.md) — krótkie reguły przy każdej zmianie
- [CONTRIBUTING.md](../CONTRIBUTING.md) — gałęzie, Conventional Commits, review
- [security.md](security.md) — model zagrożeń, kontrolki, znane luki
- [.cursor/rules/](../.cursor/rules/) — te same reguły dla Cursora
- [adr/0005-polish-only-ui-i18n-ready.md](adr/0005-polish-only-ui-i18n-ready.md) — polski interfejs
- [adr/0010-tooling.md](adr/0010-tooling.md) — uv, ruff, mypy, pytest, import-linter
- [adr/0012-moderation-and-posting-rules.md](adr/0012-moderation-and-posting-rules.md)
- [adr/0014-rate-limiting-in-postgresql.md](adr/0014-rate-limiting-in-postgresql.md)
- [adr/0015-http-security-hardening.md](adr/0015-http-security-hardening.md)
- [adr/0016-gdpr-self-service-and-retention.md](adr/0016-gdpr-self-service-and-retention.md)

## E — Execution

Instalacja, uruchomienie, testy, różnica plików Render.

- [README.md](../README.md) — pięć poleceń szybkiego startu
- [przewodnik-techniczny.md](przewodnik-techniczny.md) — uruchomienie lokalne i oba pliki Render
- [deployment.md](deployment.md) — checklista pierwszego płatnego wdrożenia
- [../render.demo.yaml](../render.demo.yaml) — darmowe demo, SQLite, bez crona
- [../render.yaml](../render.yaml) — płatny start: web, Postgres, cron, Frankfurt
- [../docker-compose.yml](../docker-compose.yml) — Postgres, Mailpit i aplikacja lokalnie
- [../.env.example](../.env.example) — zmienne środowiska
- [adr/0011-hosting-render-frankfurt.md](adr/0011-hosting-render-frankfurt.md)
- [adr/0017-free-demo-sqlite.md](adr/0017-free-demo-sqlite.md)
