# WinTiles - nowoczesna nakładka do pracy (Windows 11)

Lekka, szybka i elegancka aplikacja desktopowa w Python/Tkinter pozwalająca na błyskawiczne uruchamianie stron, folderów, programów, skryptów, poleceń WSL, edytora VS Code oraz kopiowanie przydatnych promptów i tekstów do schowka.

---

## Nowości i możliwości aplikacji

### 1. Przeciąganie i upuszczanie (Drag & Drop)
- Wciśnij i przytrzymaj **LPM** na kafelku, aby go "złapać".
- Podczas przeciągania kursor zmienia się na uchwyt, pojawia się półprzezroczysty miniaturowy podgląd przeciąganego kafelka, a kafelek docelowy podświetla się na błękitny kolor.
- Upuszczenie na inny kafelek natychmiast przenosi kafelek na wskazaną pozycję.
- Przeniesienie automatycznie przestawia tryb sortowania na „Kolejność własna” i zapisuje zmiany.

### 2. Dedykowany opis i inteligentny tooltip informacyjny („ⓘ”)
- Każdy kafelek może posiadać opcjonalny opis (`Opis (opcjonalnie)` / `Description (optional)`).
- Gdy kafelek ma zdefiniowany opis, w jego prawym górnym rogu wyświetla się estetyczna ikona informacyjna **„ⓘ”**.
- Najechanie kursorem na ikonę **„ⓘ”** natychmiast wyświetla dymek podpowiedzi (tooltip) z wprowadzonym opisem.
- Jeżeli opis jest pusty, zawiera wyłącznie białe znaki lub zostanie usunięty podczas edycji, ikona **„ⓘ”** nie jest renderowana, zachowując czystość i minimalizm interfejsu.

### 3. Sortowanie kafelków
W prawym górnym rogu dostępna jest lista wyboru trybu sortowania:
- **Kolejność własna (Manual)** – domyślna kolejność ułożona ręcznie przez użytkownika (metodą przeciągnij i upuść).
- **Najczęściej używane (Most used)** – automatyczne sortowanie według licznika kliknięć/uruchomień (`use_count`).
- **Ostatnio używane (Recently used)** – kafelki uruchamiane najświeżej pojawiają się na początku.
- **Nazwa (A - Z)** oraz **Nazwa (Z - A)** – alfabetyczne sortowanie według nazwy (z obsługą polskich znaków diakrytycznych).
- **Data dodania (najnowsze)** oraz **Data dodania (najstarsze)** – sortowanie chronologiczne.
- **Typ akcji (Action type)** – grupowanie kafelków według rodzaju akcji.

### 4. Rozbudowane typy akcji (14 rodzajów)
1. `url` – otwiera stronę WWW w domyślnej przeglądarce (automatycznie uzupełnia `https://`).
2. `path` – otwiera folder w Eksploratorze Windows.
3. `file` – otwiera dowolny plik (PDF, dokument, obraz, arkusz) w powiązanym programie domyślnym.
4. `exe` – uruchamia plik wykonywalny `.exe` (samodzielnie lub z argumentami).
5. `ps1` – uruchamia skrypt PowerShell (`powershell.exe -NoProfile -ExecutionPolicy Bypass -File ...`).
6. `python` – uruchamia skrypt Python (`.py`) bezpośrednio interpreterem Python.
7. `bat` – uruchamia skrypt wsadowy Windows (`.bat` / `.cmd`).
8. `terminal` – otwiera Windows Terminal (`wt.exe`) lub PowerShell we wskazanym folderze.
9. `vscode` – otwiera wskazany folder lub plik w Visual Studio Code (`code "<ścieżka>"`).
10. `wsl` – uruchamia polecenie bash lub terminal we wskazanym folderze w środowisku WSL (Linux).
11. `clipboard` – kopiuje wprowadzony tekst (np. prompt AI, szablon, token, hasło) do schowka systemowego i wyświetla powiadomienie toast.
12. `websearch` – wyszukuje podaną frazę bezpośrednio w Google.
13. `chrome_profile` – uruchamia Google Chrome na wskazanym profilu użytkownika (lub aktywuje już otwarte okno tego profilu).
14. `command` – uruchamia dowolne polecenie w konsoli Windows.

### 5. Nowoczesny interfejs UI
- **Pasek tytułu Windows 11**: natywny ciemny pasek tytułowy w trybie Dark Mode dzięki integracji z Windows Desktop Window Manager (DWM).
- **Karty kafelków**: nowoczesne karty z kolorowym paskiem akcentowym, czytelną ikoną emoji, wytłuszczoną nazwą, etykietą typu akcji, subtelnym podtytułem oraz licznikiem użyć (`⚡`).
- **Płynne przewijanie (Scrollable Canvas)**: responsywna siatka dostosowująca liczbę kolumn (od 1 do 6) do szerokości okna z obsługą kółka myszy.
- **Wyszukiwarka na żywo (Live Search)**: błyskawiczne filtrowanie kafelków w czasie rzeczywistym po nazwie, typie akcji, ścieżce/celu lub opisie z przyciskiem szybkiego czyszczenia `✕`.
- **Menu kontekstowe pod PPM**:
  - 🚀 Uruchom
  - ✏️ Edytuj
  - 📋 Duplikuj (błyskawiczne klonowanie kafelka)
  - 🔄 Resetuj licznik użyć
  - 🗑️ Usuń
- **Wygodne okno edycji/dodawania**:
  - Przycisk „Wybierz plik...” / „Wybierz folder...” automatycznie dostosowany do typu akcji.
  - Paleta 12 gotowych, nowoczesnych kolorów akcentowych + próbnik systemowy.
  - Dynamiczna podpowiedź wyjaśniająca składnię dla wybranego typu akcji.
- **Powiadomienia Toast**: delikatne komunikaty statusowe w dolnym pasku (np. „Skopiowano do schowka”, „Przeniesiono kafelek”, „Zapisano ustawienia”).

---

## Uruchomienie

1. Wymagany Python 3.8+ (testowano na Python 3.13).
2. Uruchomienie:
   - Dwuklik w `run.bat`, lub
   - Polecenie w terminalu:
     ```powershell
     python app.py
     ```

## Testy automatyczne

Projekt posiada pełny zestaw testów jednostkowych i integracyjnych:
```powershell
pytest -v
```

---

## Format konfiguracji (`tiles.json`)

Plik `tiles.json` zapisywany jest w katalogu aplikacji (lub w `%APPDATA%\WinTiles\tiles.json` / `~/.wintiles/tiles.json` z automatycznym fallbackiem do `%APPDATA%\Kafelki` dla zachowania pełnej kompatybilności wstecznej). Przykładowa struktura:

```json
{
  "always_on_top": false,
  "dark_mode": true,
  "language": "pl",
  "sort_by": "manual",
  "tiles": [
    {
      "name": "VERTEX AI",
      "action_type": "url",
      "target": "https://console.cloud.google.com/vertex-ai/studio/multimodal",
      "color": "#4f46e5",
      "description": "Studio Gemini",
      "use_count": 14,
      "created_at": "2026-01-01T12:00:00",
      "last_used": "2026-09-10T20:00:00",
      "order": 0
    }
  ]
}
```

Aplikacja jest w 100% kompatybilna wstecz ze starszym formatem `tiles.json` – automatycznie uzupełnia brakujące pola bez utraty żadnych istniejących danych.
