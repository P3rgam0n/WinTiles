# Dziennik Zmian (Changelog)

Wszystkie istotne zmiany w projekcie WinTiles są dokumentowane w tym pliku.
Format bazuje na [Keep a Changelog](https://keepachangelog.com/pl/1.0.0/), a projekt stosuje [Semantic Versioning](https://semver.org/lang/pl/).

## [1.2.0] - 2026-09-10

### Zmieniono
- **Rebranding na WinTiles**:
  - Zaktualizowano oficjalną nazwę aplikacji, nagłówek interfejsu UI, tytuły okien oraz AppUserModelID (`wintiles.app.v1`).
  - Zaktualizowano domyślny katalog konfiguracyjny do `%APPDATA%\WinTiles` oraz `~/.wintiles` z zachowaniem 100% kompatybilności wstecznej z dotychczasowym `%APPDATA%\Kafelki` i `~/.kafelki`.
- **Usunięcie workflowów i artefaktów `.exe`**:
  - Usunięto plik specyfikacji PyInstaller (`app.spec`), binaria `app.exe` oraz katalogi `build/` i `dist/`.
  - Rozszerzono `.gitignore` o zabezpieczenie przed plikami `*.exe`, `*.spec`, `build/`, `dist/` i `release/`.
  - Aplikacja działa bezpośrednio jako lekki skrypt Python (`run.bat` / `python app.py`).
- **Uporządkowanie struktury repozytorium**:
  - Usunięto przestarzałe i rozbieżne kopie skryptów (`app_exe.py`, `app — kopia.py`) oraz niepotrzebne pliki tymczasowe `.codex-tmp`.
  - Uproszczono i wyczyszczono logikę wykrywania ścieżek zasobów i konfiguracji w `app.py`.

### Poprawiono
- **Naprawa `Description (optional)` i tooltipa informacyjnego („ⓘ”)**:
  - Ściśle powiązano widoczność ikony „ⓘ” z obecnością opisu kafelka: ikona pojawia się wyłącznie wtedy, gdy kafelek posiada niepusty opis.
  - Hover na ikonie „ⓘ” wyświetla zdefiniowany opis kafelka.
  - Kafelki z pustym opisem lub zawierające wyłącznie spacje/białe znaki nie renderują ikony „ⓘ” i nie tworzą pustego tooltipa.
  - Edycja opisu kafelka natychmiast odświeża treść dymku, a wyczyszczenie opisu natychmiast usuwa ikonę „ⓘ” z widoku kafelka.
  - Dodano pełen zestaw testów automatycznych weryfikujących przypadki A, B, C, D i E cyklu życia opisu i tooltipa.

## [1.1.3] - 2026-09-10

### Poprawiono
- **Wyświetlanie opisu podpowiedzi w trybie pełnoekranowym (Maximized / Zoomed)**:
  - Poprawiono warunek sprawdzający stan okna `root.wm_state()`, który wcześniej odrzucał pokazywanie tooltipu gdy okno było zmaksymalizowane (`zoomed`). Podpowiedzi na ikonie "ⓘ" działają teraz prawidłowo zarówno w trybie okienkowym, jak i pełnoekranowym.
- **Wyeliminowanie wolnego pola u góry okna**:
  - Wzbogacono `_update_scrollregion` o automatyczne zerowanie pozycji pionowej (`yview_moveto(0)`) w sytuacjach gdy rozmiar zawartości mieści się w widocznym obszarze canvasu.

## [1.1.2] - 2026-09-10

### Poprawiono
- **Wyświetlanie opisu podpowiedzi po najechaniu na "ⓘ"**:
  - Naprawiono płynność i natychmiastowe zamykanie podpowiedzi (tooltip) przy najechaniu na ikonę "ⓘ".
  - Dodano krótkie opóźnienie ochronne (grace period) przy opuszczaniu ikony "ⓘ" oraz obsługę najechania myszą bezpośrednio na okienko podpowiedzi.
- **Wyeliminowanie wolnego pola u góry okna przy przeciąganiu kafelka (Drag & Drop)**:
  - Naprawiono automatyczne przewijanie canvasu — zablokowano ujemne i przedwczesne przewijanie u góry okna gdy wysokość zawartości jest mniejsza lub równa wysokości okna canvas.
- **Ładowanie ikony aplikacji (`assets/icon.png`)**:
  - Podpięto ładowanie dedykowanej ikony `assets/icon.png` do okna aplikacji (`root.iconphoto`) oraz identyfikatora AppUserModelID dla paska zadań Windows.

## [1.1.1] - 2026-09-10

### Dodano
- **Nowa ikona aplikacji (2K)**: Wygenerowano dedykowaną, nowoczesną ikonę 3D Fluent Design w rozdzielczości 2K (`assets/icon.png`) reprezentującą siatkę kafelków z motywami akrylowego szkła i neonowego podświetlenia.

## [1.1.0] - 2026-09-10

### Dodano
- **Dedykowana ikona informacji "ⓘ" na kafelkach**:
  - W prawym górnym rogu każdego kafelka dodano dyskretną ikonę informacji "ⓘ".
  - Podpowiedzi (tooltips) wyświetlają się wyłącznie po najechaniu kursorem myszy na ikonę "ⓘ" w prawym górnym rogu, eliminując niepożądane wyskakiwanie tooltipów przy zwykłym poruszaniu się po kafelkach.
  - Płynny efekt najechania kursorem na ikonę "ⓘ" (akcentowy kolor podświetlenia) oraz kursor `hand2`.
  - Kliknięcie w ikonę "ⓘ" nie uruchamia akcji kafelka ani nie inicjuje przeciągania (pełna izolacja zdarzeń myszy).
  - Inteligentne pozycjonowanie dymku podpowiedzi wyrównane do prawej krawędzi ikony z automatycznym zabezpieczeniem przed wyjściem poza ekran.

### Poprawiono
- **Natychmiastowe zamykanie podpowiedzi**:
  - Naprawiono błąd zacinających się podpowiedzi — po opuszczeniu ikony "ⓘ" podpowiedź znika natychmiastowo bez żadnych opóźnień i bez pozostawania na ekranie.
- **Eliminacja „duchów” tooltipów na pulpicie i przy minimalizacji**:
  - Rozwiązano problem pozostawania dymków na pulpicie Windows po zminimalizowaniu aplikacji lub przełączeniu okien (ustawienie `transient` względem okna głównego).
  - Automatyczne natychmiastowe niszczenie wszystkich tooltipów przy zdarzeniach minimalizacji (`<Unmap>`), utraty aktywności (`<Deactivate>`), utraty fokusu (`<FocusOut>`), przewijaniu kółkiem myszy (`<MouseWheel>`), zmianie rozmiaru canvasu oraz wciśnięciu klawisza Escape.
  - Zaimplementowano gwarancję pojedynczej aktywnej podpowiedzi (`active_tooltip`), wykluczając możliwość jednoczesnego zablokowania wielu okienek na pulpicie.
  - Naprawiono błąd w `_hide_all_tooltips`, który przedwcześnie czyścił referencje do zarządzanych obiektów tooltipów.

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
