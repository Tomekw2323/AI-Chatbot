# Roadmap

Dokument dla właściciela i programisty. Szczegóły techniczne: [architektura](architecture.md),
[model danych](domain-model.md), [decyzje (ADR)](adr/).

## Faza 1: MVP (B2B) – obecny etap

Cel: zastąpić grupę na Facebooku jednym, przeszukiwalnym miejscem.

**Zbudowane w szkielecie:**

- Konta: rejestracja e-mailem (z weryfikacją), logowanie Google (po podaniu kluczy), jeden typ
  konta dla wszystkich.
- Organizacje (poradnie, fundacje, OPS-y, właściciele gabinetów) z członkami i rolami
  (właściciel / administrator / członek zespołu).
- Wizytówki specjalistów: zawód, miasto, specjalizacje, nurty, kontakt, znacznik „szukam pracy”.
- Tablica ogłoszeń, 5 rodzajów: praca, staż/praktyki, wolontariat, „szukam pracy/stażu”, wynajem
  gabinetu (cena za godzinę/dzień/miesiąc, stałe bloki dostępności, opis dostępności).
- Filtry: miasto, województwo, rodzaj, kategoria (specjalizacja), tryb pracy, szukanie tekstowe,
  sortowanie; strony pod SEO, np. `/ogloszenia/gabinety/wroclaw/`, mapa strony.
- Cykl życia ogłoszenia: szkic → opublikowane → wygasłe (po 60 dniach) → archiwum.
- Moderacja w panelu administratora: ukrywanie ogłoszeń, blokowanie organizacji i profili,
  weryfikacja organizacji.
- Kontakt: formularz wiadomości do autora ogłoszenia (e-mail z możliwością odpowiedzi).

**Do zrobienia przed publicznym startem:**

- Regulamin, polityka prywatności, zgody RODO przy rejestracji, strona „kontakt”.
- Domena, konto na Render (Frankfurt), dostawca e-maili w UE, klucze Google OAuth.
- Przycisk „zgłoś ogłoszenie” i prosty limit wiadomości (ochrona przed spamem).
- Zdjęcia (logo organizacji, zdjęcie profilowe, zdjęcia gabinetu) – wymaga magazynu plików w UE
  (np. S3-kompatybilny w regionie UE).
- Zaproszenia członków do organizacji z poziomu strony (dziś: przez panel administratora).
- Analityka zgodna z RODO (np. Plausible) i monitoring błędów (np. Sentry EU).

## Faza 2: kalendarz gabinetów, płatności, promowanie

- **Kalendarz gabinetów**: konkretne terminy do zarezerwowania na bazie bloków dostępności,
  rezerwacja godzin/dni, potwierdzenia e-mail, anulowanie.
- **Płatności**: Przelewy24 (BLIK, przelewy – standard w Polsce) lub Stripe (karty, BLIK,
  Przelewy24 przez Stripe). Najprościej zacząć od Stripe Checkout; Przelewy24 bezpośrednio, gdy
  prowizje zaczną mieć znaczenie. Faktury VAT (np. integracja z Fakturownią).
- **Ogłoszenia promowane**: wyróżnienie na liście i na stronie głównej na X dni, płatne jednorazowo.
- Pakiety dla organizacji (np. N ogłoszeń miesięcznie), powiadomienia e-mail o nowych ofertach
  (alerty według miasta i rodzaju).
- Kolejka zadań w tle (wysyłka e-maili, wygaszanie, płatności).

## Faza 3: rezerwacja wizyt pacjentów (B2C)

- Publiczny katalog specjalistów dla pacjentów (flaga `visible_to_patients` jest już w modelu),
  usługi i cennik, kalendarz wizyt, rezerwacja i przypomnienia.
- **RODO art. 9 (dane szczególnej kategorii)**: sam fakt umówienia wizyty u psychologa/psychiatry
  jest daną o zdrowiu. Wymaga to m.in.:
  - wyraźnej podstawy prawnej (art. 9 ust. 2 lit. a – wyraźna zgoda, lub lit. h – świadczenie
    opieki zdrowotnej przez specjalistę jako administratora danych, z platformą jako podmiotem
    przetwarzającym i umową powierzenia),
  - oceny skutków dla ochrony danych (DPIA, art. 35),
  - minimalizacji danych (nie zbieramy powodu wizyty ani notatek), szyfrowania, rejestrowania
    dostępu, osobnych uprawnień, polityki retencji,
  - hostingu i podprocesorów w EOG, rejestru czynności przetwarzania, wyznaczenia IOD
    (prawdopodobnie wymagane przy przetwarzaniu na dużą skalę),
  - konsultacji z prawnikiem specjalizującym się w ochronie danych medycznych przed startem.
- Technicznie: osobny moduł `booking` nad `profiles` i `organizations`; ewentualnie osobna baza
  lub schemat dla danych pacjentów (ADR 0009).
- Konkurencja: ZnanyLekarz (Docplanner) – wyróżnik to specjalizacja w psychoterapii i połączenie
  z rynkiem pracy i gabinetów.
