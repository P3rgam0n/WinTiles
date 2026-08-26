# Kafelki - prosta nakladka do pracy (Windows 11)

## Co potrafi
- Wyswietla okno z kafelkami.
- Klikniecie kafelka uruchamia akcje:
  - otwarcie URL,
  - otwarcie sciezki w Eksploratorze,
  - uruchomienie pliku `.exe`,
  - uruchomienie skryptu PowerShell (`.ps1`) po samej sciezce,
  - uruchomienie skryptu Python (`.py`) po samej sciezce,
  - uruchomienie Google Chrome na wskazanym profilu,
  - uruchomienie komendy/skryptu.
- PPM na kafelku: edycja/usuwanie.
- LPM + przeciagniecie: zmiana kolejnosci kafelkow.
- Przycisk `+ Dodaj kafelek` dodaje nowy kafelek.
- Opcja `Zawsze na wierzchu` (wlacz/wyłącz).
- Ustawienia zapisywane sa automatycznie do `tiles.json`.

## Uruchomienie
1. Upewnij sie, ze masz Python 3 (na Windows 11 zwykle wystarczy).
2. Uruchom:
   - `run.bat` (dwuklik), albo
   - `python app.py` w terminalu.

## Format konfiguracji
Plik `tiles.json` ma postac obiektu:

```json
{
  "always_on_top": false,
  "tiles": [
    {
      "name": "Google",
      "action_type": "url",
      "target": "https://www.google.com",
      "color": "#1f6feb"
    }
  ]
}
```

`action_type`:
- `url` - link WWW,
- `path` - sciezka do folderu/pliku,
- `exe` - uruchomienie pliku wykonywalnego `.exe` po sciezce,
- `ps1` - uruchomienie skryptu PowerShell po sciezce pliku,
- `python` - uruchomienie skryptu Python po sciezce pliku,
- `chrome_profile` - uruchomienie Chrome na profilu po sciezce, np.
  `C:\Users\cuksy\AppData\Local\Google\Chrome\User Data\Default`,
  jesli ten profil juz dziala, aplikacja przelacza na jego otwarte okno zamiast otwierac nowy,
- `command` - polecenie systemowe (np. uruchomienie skryptu).

`color`:
- kolor tla kafelka, np. `#1f6feb` albo `red`.
