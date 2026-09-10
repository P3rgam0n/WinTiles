# Dziennik Zmian (Changelog)

Wszystkie istotne zmiany w projekcie Kafelki są dokumentowane w tym pliku.
Format bazuje na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/), a projekt stosuje [Semantic Versioning](https://semver.org/lang/pl/).

## [1.0.0] - 2026-09-10

### Dodano
- **Przeciąganie i upuszczanie LPM (Drag & Drop)**:
  - Możliwość chwycenia kafelka lewym przyciskiem myszy i przeciągnięcia na inną pozycję na siatce.
  - Półprzezroczysty miniaturowy podgląd przeciąganego kafelka (drag ghost) podążający za kursorem.
  - Podświetlanie kafelka docelowego oraz inteligentne wykrywanie najbliższego kafelka w odstępach siatki (eliminacja martwych stref).
  - Automatyczne przewijanie canvasu przy przeciąganiu przy górnej i dolnej krawędzi.
  - Obsługa klawisza Escape do natychmiastowego anulowania aktywnego przeciągania.
- **Sortowanie kafelków**:
  - 8 trybów sortowania: Kolejność własna, Najczęściej używane, Ostatnio używane, Nazwa (A - Z), Nazwa (Z - A), Data dodania (najnowsze), Data dodania (najstarsze), Typ akcji.
  - Pełne wsparcie dla polskiej alfabetycznej kolacji znaków diakrytycznych (ą, ć, ę, ł, ń, ó, ś, ź, ż).
  - Zachowywanie i natychmiastowe przywracanie kolejności własnej (`order`) po przełączaniu trybów sortowania.
  - Automatyczne aplikowanie sortowania przy uruchomieniu aplikacji.
- **Rozszerzone typy akcji (14 rodzajów)**:
  - Dodano akcje: `file` (domyślny program systemowy), `bat` (skrypt wsadowy), `terminal` (Windows Terminal / PowerShell w folderze), `vscode` (otwarcie folderu/pliku w VS Code), `wsl` (uruchomienie konsoli lub polecenia w WSL), `clipboard` (kopiowanie promptu/tekstu do schowka z powiadomieniem toast), `websearch` (wyszukiwanie w Google).
  - Obsługa ścieżek w cudzysłowach (np. z systemowego „Kopiuj jako ścieżkę”).
  - Bezpieczne uruchamianie skryptów Python ze skompilowanego pliku wykonywalnego (`.exe`).
- **Nowoczesny interfejs UI**:
  - Ciemny pasek tytułowy Windows 11 poprzez Desktop Window Manager (DWM).
  - Nowoczesne karty kafelków z kolorowymi paskami akcentowymi, czytelną typografią, etykietami typów i licznikami użyć.
  - Płynny, niefikający efekt najechania kursorem (hover) obejmujący całą kartę i elementy potomne.
  - Prawidłowo działające podpowiedzi (tooltips) wyświetlające się przy najechaniu na dowolny element kafelka (tekst, ikona, tło).
  - Wyszukiwarka na żywo ze stanem pustym i szybkim czyszczeniem.
  - Menu kontekstowe pod PPM (uruchom, edytuj, duplikuj, resetuj licznik, usuń).
  - Pasek statusu z powiadomieniami toast i licznikiem kafelków.
  - Responsywna siatka z obsługą kółka myszy.
- **Zestaw 21 testów automatycznych** (`tests/test_app.py`) weryfikujący wszystkie funkcje, sortowanie, kolację, drag&drop, migrację i obsługę błędów.

### Poprawiono
- Naprawiono błąd braku sortowania na starcie aplikacji przy skonfigurowanym trybie innym niż manualny.
- Naprawiono błąd braku wyświetlania tooltipów po najechaniu na etykiety tekstowe wewnątrz kafelka.
- Naprawiono błąd anulowania upuszczenia przy puszczeniu przycisku myszy w odstępach między kafelkami.
- Naprawiono błąd utraty kolejności manualnej po posortowaniu kafelków.
- Naprawiono uruchamianie skryptów `.py` ze spakowanego pliku `.exe`.
- Naprawiono otwieranie ścieżek zawierających cudzysłowy w akcjach `path`, `file`, `chrome_profile`, `wsl`.
