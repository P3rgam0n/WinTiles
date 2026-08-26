# Kafelki - prosta nakladka do pracy (Windows 11)

## Co potrafi
- Wyświetla okno z kafelkami.
- Kliknięcie kafelka uruchamia akcję:
  - otwarcie URL,
  - otwarcie ścieżki w Eksploratorze,
  - uruchomienie pliku `.exe`,
  - uruchomienie skryptu PowerShell (`.ps1`) po samej ścieżce,
  - uruchomienie skryptu Python (`.py`) po samej ścieżce,
  - uruchomienie Google Chrome na wskazanym profilu,
  - uruchomienie komendy/skryptu.
- **Opcjonalny opis kafelka**: po dodaniu opisu i najechaniu myszą na kafelek wyświetla się czytelna podpowiedź (tooltip).
- **Tryb jasny / ciemny (Dark mode)**: możliwość wygodnego przełączania motywu graficznego aplikacji.
- **Wybór języka (Language)**: domyślnie język angielski (English) z możliwością szybkiej zmiany na polski.
- PPM na kafelku: edycja/usuwanie.
- LPM + przeciągnięcie: zmiana kolejności kafelków.
- Przycisk `+ Dodaj kafelek` (`+ Add Tile`) dodaje nowy kafelek.
- Opcja `Zawsze na wierzchu` (`Always on top`) (włącz/wyłącz).
- Ustawienia zapisywane są automatycznie do `tiles.json`.

## Uruchomienie
1. Upewnij się, że masz Python 3.
2. Uruchom:
   - `run.bat` (dwuklik), albo
   - `python app.py` w terminalu.

## Format konfiguracji
Plik `tiles.json` ma postać obiektu:

```json
{
  "always_on_top": false,
  "dark_mode": false,
  "language": "en",
  "tiles": [
    {
      "name": "Google",
      "action_type": "url",
      "target": "https://www.google.com",
      "color": "#1f6feb",
      "description": "Wyszukiwarka Google"
    }
  ]
}
```

`language`:
- `"en"` (domyślny English),
- `"pl"` (Polski).

`dark_mode`:
- `true` (tryb ciemny),
- `false` (tryb jasny).

`description`:
- opcjonalny tekst opisu kafelka wyświetlany po najechaniu kursorem myszy.
