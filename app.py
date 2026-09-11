import copy
import ctypes
import json
import os
import subprocess
import sys
import tkinter as tk
import urllib.parse
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import colorchooser, filedialog, messagebox, ttk

APP_CONFIG_DIR_NAME = "WinTiles"
DEFAULT_CHROME_EXE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
DEFAULT_TILE_COLOR = "#1f6feb"

LANG_EN = "en"
LANG_PL = "pl"

LANG_NAMES = {
    LANG_EN: "English",
    LANG_PL: "Polski",
}
LANG_CODES = {
    "English": LANG_EN,
    "Polski": LANG_PL,
}

SORT_KEYS = [
    "manual",
    "most_used",
    "recently_used",
    "name_asc",
    "name_desc",
    "date_newest",
    "date_oldest",
    "action_type",
]

PL_ALPHABET = "aąbcćdeęfghijklłmnńoóprsśtuwyzźż"
PL_ORDER = {char: i for i, char in enumerate(PL_ALPHABET)}


def polish_sort_key(text):
    result = []
    for ch in str(text).lower():
        if ch in PL_ORDER:
            result.append(PL_ORDER[ch])
        else:
            result.append(1000 + ord(ch))
    return result

PRESET_COLORS = [
    ("#4f46e5", "Indigo"),
    ("#0284c7", "Sky"),
    ("#06b6d4", "Cyan"),
    ("#10b981", "Emerald"),
    ("#84cc16", "Lime"),
    ("#f59e0b", "Amber"),
    ("#ea580c", "Orange"),
    ("#f43f5e", "Rose"),
    ("#ec4899", "Pink"),
    ("#8b5cf6", "Purple"),
    ("#7c3aed", "Violet"),
    ("#64748b", "Slate"),
]

ACTION_DEFS = {
    "url": {
        "icon": "🌐",
        "name_en": "Web URL",
        "name_pl": "Strona WWW (URL)",
        "hint_en": "https://example.com or any web address",
        "hint_pl": "https://example.com lub dowolny adres WWW",
        "browse": None,
    },
    "path": {
        "icon": "📁",
        "name_en": "Folder (Explorer)",
        "name_pl": "Folder w Eksploratorze",
        "hint_en": "Folder path, e.g. C:\\Users\\Username\\Documents",
        "hint_pl": "Ścieżka do folderu, np. C:\\Users\\Nazwa\\Dokumenty",
        "browse": "folder",
    },
    "file": {
        "icon": "📄",
        "name_en": "Open File (Default App)",
        "name_pl": "Otwórz plik (program domyślny)",
        "hint_en": "Document or file, e.g. C:\\docs\\report.pdf",
        "hint_pl": "Dokument lub plik, np. C:\\dokumenty\\raport.pdf",
        "browse": "file",
    },
    "exe": {
        "icon": "⚙️",
        "name_en": "Application (.exe)",
        "name_pl": "Program (.exe)",
        "hint_en": "Executable file, e.g. C:\\Program Files\\App\\app.exe",
        "hint_pl": "Plik wykonywalny, np. C:\\Program Files\\App\\app.exe",
        "browse": "exe",
    },
    "ps1": {
        "icon": "📜",
        "name_en": "PowerShell Script (.ps1)",
        "name_pl": "Skrypt PowerShell (.ps1)",
        "hint_en": "PowerShell script path, e.g. C:\\scripts\\task.ps1",
        "hint_pl": "Ścieżka do skryptu PowerShell, np. C:\\skrypty\\zadanie.ps1",
        "browse": "ps1",
    },
    "python": {
        "icon": "🐍",
        "name_en": "Python Script (.py)",
        "name_pl": "Skrypt Python (.py)",
        "hint_en": "Python script path, e.g. C:\\scripts\\script.py",
        "hint_pl": "Ścieżka do skryptu Python, np. C:\\skrypty\\skrypt.py",
        "browse": "python",
    },
    "bat": {
        "icon": "⚡",
        "name_en": "Batch Script (.bat / .cmd)",
        "name_pl": "Skrypt wsadowy (.bat / .cmd)",
        "hint_en": "Batch file path, e.g. C:\\scripts\\build.bat",
        "hint_pl": "Ścieżka do pliku wsadowego, np. C:\\skrypty\\start.bat",
        "browse": "bat",
    },
    "terminal": {
        "icon": "💻",
        "name_en": "Open Terminal in Folder",
        "name_pl": "Otwórz Terminal w folderze",
        "hint_en": "Folder path to open in Windows Terminal or PowerShell",
        "hint_pl": "Ścieżka folderu do otwarcia w Windows Terminal / PowerShell",
        "browse": "folder",
    },
    "vscode": {
        "icon": "📝",
        "name_en": "Open in VS Code",
        "name_pl": "Otwórz w VS Code",
        "hint_en": "Folder or file to open in Visual Studio Code",
        "hint_pl": "Ścieżka folderu lub pliku do otwarcia w Visual Studio Code",
        "browse": "any",
    },
    "wsl": {
        "icon": "🐧",
        "name_en": "WSL (Linux)",
        "name_pl": "WSL (Linux)",
        "hint_en": "Directory (e.g. /var/www or D:\\Git) or command (e.g. htop)",
        "hint_pl": "Folder (np. /var/www lub D:\\Git) lub polecenie (np. htop)",
        "browse": "folder",
    },
    "clipboard": {
        "icon": "📋",
        "name_en": "Copy to Clipboard",
        "name_pl": "Kopiuj tekst do schowka",
        "hint_en": "Any prompt, template, snippet, token, or text to copy",
        "hint_pl": "Dowolny prompt, szablon, snippet, token lub tekst do skopiowania",
        "browse": None,
    },
    "websearch": {
        "icon": "🔍",
        "name_en": "Google Search",
        "name_pl": "Szukaj w Google",
        "hint_en": "Search query or phrase to look up in default browser",
        "hint_pl": "Fraza lub zapytanie do wyszukania w przeglądarce",
        "browse": None,
    },
    "chrome_profile": {
        "icon": "🌐",
        "name_en": "Chrome Profile",
        "name_pl": "Profil Google Chrome",
        "hint_en": "Path e.g. C:\\...\\Google\\Chrome\\User Data\\Profile 1",
        "hint_pl": "Ścieżka np. C:\\...\\Google\\Chrome\\User Data\\Profile 1",
        "browse": "folder",
    },
    "command": {
        "icon": "⌨️",
        "name_en": "Shell Command",
        "name_pl": "Polecenie konsoli (shell)",
        "hint_en": "Any system command, e.g. ping 8.8.8.8 -t",
        "hint_pl": "Dowolne polecenie systemowe, np. ping 8.8.8.8 -t",
        "browse": None,
    },
}

TRANSLATIONS = {
    LANG_EN: {
        "app_title": "WinTiles - Work Helper",
        "search_placeholder": "Search tiles (name, type, target)...",
        "add_tile": "+ Add Tile",
        "save": "Save",
        "saved_title": "Saved",
        "saved_msg": "Settings saved in:\n{}",
        "saved_toast": "✓ Settings saved successfully",
        "always_on_top": "Always on top",
        "dark_mode": "Dark mode",
        "light_mode": "Light mode",
        "language": "Language:",
        "sort_label": "Sort:",
        "sort_manual": "Custom order",
        "sort_most_used": "Most used",
        "sort_recently_used": "Recently used",
        "sort_name_asc": "Name (A - Z)",
        "sort_name_desc": "Name (Z - A)",
        "sort_date_newest": "Date added (newest)",
        "sort_date_oldest": "Date added (oldest)",
        "sort_action_type": "Action type",
        "hint_mouse": "LMB: run | Hold & drag: move | RMB: menu | Ctrl+Wheel: opacity",
        "run": "Run",
        "edit": "Edit",
        "duplicate": "Duplicate",
        "reset_stats": "Reset usage count",
        "delete": "Delete",
        "edit_tile_title": "Edit Tile",
        "add_tile_title": "Add Tile",
        "name": "Name:",
        "action_type": "Action type:",
        "target": "Target / command / path:",
        "color": "Tile color:",
        "presets": "Presets:",
        "description": "Description (optional):",
        "choose_color": "Custom...",
        "browse_file": "Browse file...",
        "browse_folder": "Browse folder...",
        "cancel": "Cancel",
        "new_tile_default_name": "New Tile",
        "copy_suffix": " (Copy)",
        "empty_search": "No tiles matching '{}'",
        "clear_search": "Clear search",
        "status_tile_count": "{} tiles",
        "status_filtered_count": "Showing {} of {} tiles",
        "toast_reordered": "Moved '{}' to position {}",
        "toast_duplicated": "Duplicated '{}'",
        "toast_deleted": "Deleted '{}'",
        "toast_sorted": "Sorted by: {}",
        "toast_copied": "Copied to clipboard: {}",
        "toast_stats_reset": "Reset usage count for '{}'",
        "tt_used": "Used: {} times",
        "tt_added": "Added: {}",
        "tt_last_used": "Last used: {}",
        "tt_topmost": "Always on top (keep window above other windows)",
        "tt_dark_mode": "Toggle theme (dark / light mode)",
        "tt_clear_search": "Clear search filter",
        "tt_add_tile": "Add a new tile",
        "tt_save": "Save layout and settings",
        "opacity_toast": "Window opacity: {}%",
        "error": "Error",
        "error_name_empty": "Tile name cannot be empty.",
        "error_action_type": "Invalid action type.",
        "error_target_empty": "Field 'Target / command / path' cannot be empty.",
        "error_color": "Invalid color format (e.g. #1f6feb).",
        "save_error_title": "Save Error",
        "delete_title": "Delete Tile",
        "delete_confirm": "Are you sure you want to delete '{}'?",
        "run_error_title": "Execution Error",
        "path_not_found": "Path does not exist:\n{}",
        "exe_not_found": "EXE file does not exist:\n{}",
        "path_is_dir": "Specified path is a directory, not an EXE file:\n{}",
        "script_not_found": "Script does not exist:\n{}",
        "chrome_profile_not_found": "Chrome profile does not exist:\n{}",
        "chrome_exe_not_found": (
            "chrome.exe not found.\nCheck Google Chrome installation (standard path)."
        ),
        "chrome_profile_invalid": (
            "Invalid Chrome profile path.\n"
            "Provide e.g.: C:\\Users\\<user>\\AppData\\Local\\Google\\Chrome\\User Data\\Default"
        ),
        "unknown_action": "Unknown action type: {}",
    },
    LANG_PL: {
        "app_title": "WinTiles - Ułatwienie Pracy",
        "search_placeholder": "Szukaj kafelków (nazwa, typ, cel)...",
        "add_tile": "+ Dodaj kafelek",
        "save": "Zapisz",
        "saved_title": "Zapisano",
        "saved_msg": "Ustawienia zapisane w:\n{}",
        "saved_toast": "✓ Pomyślnie zapisano ustawienia",
        "always_on_top": "Zawsze na wierzchu",
        "dark_mode": "Tryb ciemny",
        "light_mode": "Tryb jasny",
        "language": "Język:",
        "sort_label": "Sortuj:",
        "sort_manual": "Kolejność własna",
        "sort_most_used": "Najczęściej używane",
        "sort_recently_used": "Ostatnio używane",
        "sort_name_asc": "Nazwa (A - Z)",
        "sort_name_desc": "Nazwa (Z - A)",
        "sort_date_newest": "Data dodania (najnowsze)",
        "sort_date_oldest": "Data dodania (najstarsze)",
        "sort_action_type": "Typ akcji",
        "hint_mouse": "LPM: uruchom | Przytrzymaj LPM: przenieś | PPM: menu | Ctrl+Rolka: przezroczystość",
        "run": "Uruchom",
        "edit": "Edytuj",
        "duplicate": "Duplikuj",
        "reset_stats": "Resetuj licznik",
        "delete": "Usuń",
        "edit_tile_title": "Edycja kafelka",
        "add_tile_title": "Dodaj kafelek",
        "name": "Nazwa:",
        "action_type": "Typ akcji:",
        "target": "Cel / polecenie / ścieżka:",
        "color": "Kolor kafelka:",
        "presets": "Paleta:",
        "description": "Opis (opcjonalnie):",
        "choose_color": "Inny...",
        "browse_file": "Wybierz plik...",
        "browse_folder": "Wybierz folder...",
        "cancel": "Anuluj",
        "new_tile_default_name": "Nowy kafelek",
        "copy_suffix": " (Kopia)",
        "empty_search": "Brak kafelków spełniających kryteria '{}'",
        "clear_search": "Wyczyść wyszukiwanie",
        "status_tile_count": "Kafelków: {}",
        "status_filtered_count": "Wyświetlono {} z {} kafelków",
        "toast_reordered": "Przeniesiono '{}' na pozycję {}",
        "toast_duplicated": "Zduplikowano '{}'",
        "toast_deleted": "Usunięto '{}'",
        "toast_sorted": "Posortowano: {}",
        "toast_copied": "Skopiowano do schowka: {}",
        "toast_stats_reset": "Zresetowano licznik dla '{}'",
        "tt_used": "Użyto: {} razy",
        "tt_added": "Dodano: {}",
        "tt_last_used": "Ostatnio: {}",
        "tt_topmost": "Zawsze na wierzchu (utrzymuj okno nad innymi oknami)",
        "tt_dark_mode": "Przełącz motyw (ciemny / jasny)",
        "tt_clear_search": "Wyczyść pole wyszukiwania",
        "tt_add_tile": "Dodaj nowy kafelek",
        "tt_save": "Zapisz układ i ustawienia",
        "opacity_toast": "Przezroczystość okna: {}%",
        "error": "Błąd",
        "error_name_empty": "Nazwa kafelka nie może być pusta.",
        "error_action_type": "Nieprawidłowy typ akcji.",
        "error_target_empty": "Pole 'Cel / polecenie / ścieżka' nie może być puste.",
        "error_color": "Nieprawidłowy kolor (np. #1f6feb).",
        "save_error_title": "Błąd zapisu",
        "delete_title": "Usuń kafelek",
        "delete_confirm": "Czy na pewno usunąć '{}'?",
        "run_error_title": "Błąd uruchamiania",
        "path_not_found": "Ścieżka nie istnieje:\n{}",
        "exe_not_found": "Plik EXE nie istnieje:\n{}",
        "path_is_dir": "Podana ścieżka jest folderem, nie plikiem EXE:\n{}",
        "script_not_found": "Skrypt nie istnieje:\n{}",
        "chrome_profile_not_found": "Profil Chrome nie istnieje:\n{}",
        "chrome_exe_not_found": (
            "Nie znaleziono chrome.exe.\nSprawdź instalację Google Chrome (standardowa ścieżka)."
        ),
        "chrome_profile_invalid": (
            "Nieprawidłowa ścieżka profilu Chrome.\n"
            "Podaj np.: C:\\Users\\<user>\\AppData\\Local\\Google\\Chrome\\User Data\\Default"
        ),
        "unknown_action": "Nieznany typ akcji: {}",
    },
}


def _primary_config_file():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().with_name("tiles.json")
    return Path(__file__).resolve().with_name("tiles.json")


def _fallback_config_file():
    appdata = os.getenv("APPDATA")
    if appdata:
        p = Path(appdata) / APP_CONFIG_DIR_NAME / "tiles.json"
        if p.exists():
            return p
        old_p = Path(appdata) / "Kafelki" / "tiles.json"
        if old_p.exists():
            return old_p
        return p
    default_p = Path.home() / ".wintiles" / "tiles.json"
    old_home_p = Path.home() / ".kafelki" / "tiles.json"
    if not default_p.exists() and old_home_p.exists():
        return old_home_p
    return default_p


def _bundled_seed_config_file():
    return Path(__file__).resolve().with_name("tiles.json")


PRIMARY_CONFIG_FILE = _primary_config_file()
FALLBACK_CONFIG_FILE = _fallback_config_file()
BUNDLED_SEED_CONFIG_FILE = _bundled_seed_config_file()


def get_icon_path():
    p = Path(__file__).resolve().parent / "assets" / "icon.png"
    if p.exists():
        return p
    return None

DEFAULT_TILES = [
    {
        "name": "Google",
        "action_type": "url",
        "target": "https://www.google.com",
        "description": "Google Search Engine",
        "color": "#4f46e5",
        "use_count": 0,
        "created_at": "2026-01-01T00:00:00",
        "last_used": "",
    },
    {
        "name": "Pulpit",
        "action_type": "path",
        "target": str(Path.home() / "Desktop"),
        "description": "User Desktop Folder",
        "color": "#0284c7",
        "use_count": 0,
        "created_at": "2026-01-01T00:00:01",
        "last_used": "",
    },
]


def apply_windows_dark_titlebar(window, dark: bool):
    if sys.platform != "win32":
        return
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id()) or window.winfo_id()
        val = ctypes.c_int(1 if dark else 0)
        res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 20, ctypes.byref(val), ctypes.sizeof(val)
        )
        if res != 0:
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 19, ctypes.byref(val), ctypes.sizeof(val)
            )
    except Exception:
        pass


def format_datetime_display(iso_str):
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return str(iso_str)[:16].replace("T", " ")


def get_target_preview(action_type, target):
    target = target.strip()
    if action_type == "url":
        clean = target.replace("https://", "").replace("http://", "").rstrip("/")
        return clean if len(clean) <= 28 else clean[:25] + "..."
    if action_type in ("path", "folder", "terminal"):
        name = Path(target).name or target
        return name if len(name) <= 26 else name[:23] + "..."
    if action_type in ("exe", "file", "ps1", "python", "bat", "chrome_profile", "vscode"):
        name = Path(target).name or target
        return name if len(name) <= 26 else name[:23] + "..."
    if action_type == "clipboard":
        return target if len(target) <= 24 else target[:21] + "..."
    return target if len(target) <= 26 else target[:23] + "..."


class Tooltip:
    active_tooltip = None

    def __init__(self, widgets, text_provider, dark_mode=False):
        if isinstance(widgets, (list, tuple)):
            self.widgets = list(widgets)
            self.anchor_widget = widgets[0] if widgets else None
        else:
            self.widgets = [widgets]
            self.anchor_widget = widgets

        self.text_provider = text_provider
        self.dark_mode = dark_mode
        self.tip_window = None
        self.after_id = None
        self.hide_after_id = None

        for w in self.widgets:
            w.bind("<Enter>", self.schedule, add="+")
            w.bind("<Motion>", self.on_motion, add="+")
            w.bind("<Leave>", self.on_leave, add="+")
            w.bind("<ButtonPress>", self.hide, add="+")
            w.bind("<Destroy>", lambda e: self.hide(), add="+")

    def schedule(self, event=None):
        self.unschedule_hide()
        if self.tip_window:
            return
        self.unschedule()
        if not self.anchor_widget:
            return
        if Tooltip.active_tooltip and Tooltip.active_tooltip is not self:
            Tooltip.active_tooltip.hide()
        self.after_id = self.anchor_widget.after(60, self.show)

    def on_motion(self, event=None):
        if not self.tip_window and not self.after_id:
            self.schedule()

    def unschedule(self):
        if self.after_id and self.anchor_widget:
            try:
                self.anchor_widget.after_cancel(self.after_id)
            except Exception:
                pass
            self.after_id = None

    def unschedule_hide(self):
        if self.hide_after_id and self.anchor_widget:
            try:
                self.anchor_widget.after_cancel(self.hide_after_id)
            except Exception:
                pass
            self.hide_after_id = None

    def on_leave(self, event=None):
        self.unschedule()
        if self.tip_window and self.anchor_widget:
            self.unschedule_hide()
            self.hide_after_id = self.anchor_widget.after(120, self.check_pointer_and_hide)
        else:
            self.hide()

    def check_pointer_and_hide(self):
        if not self.tip_window or not self.anchor_widget:
            return
        try:
            if not self.anchor_widget.winfo_exists():
                self.hide()
                return
            px, py = self.anchor_widget.winfo_pointerxy()
            ax = self.anchor_widget.winfo_rootx()
            ay = self.anchor_widget.winfo_rooty()
            aw = self.anchor_widget.winfo_width()
            ah = self.anchor_widget.winfo_height()
            if ax <= px <= ax + aw and ay <= py <= ay + ah:
                return

            if self.tip_window.winfo_exists():
                tx = self.tip_window.winfo_rootx()
                ty = self.tip_window.winfo_rooty()
                tw = self.tip_window.winfo_width()
                th = self.tip_window.winfo_height()
                if tx <= px <= tx + tw and ty <= py <= ty + th:
                    return
        except tk.TclError:
            pass
        self.hide()

    def show(self, event=None):
        self.unschedule_hide()
        self.unschedule()
        if self.tip_window:
            return

        if not self.anchor_widget:
            return

        try:
            if not self.anchor_widget.winfo_exists() or not self.anchor_widget.winfo_ismapped():
                return
            root = self.anchor_widget.winfo_toplevel()
            if not root.winfo_exists() or root.wm_state() in ("iconic", "withdrawn"):
                return
        except (tk.TclError, AttributeError):
            return

        text = self.text_provider() if callable(self.text_provider) else self.text_provider
        if not text or not str(text).strip():
            return

        if Tooltip.active_tooltip and Tooltip.active_tooltip is not self:
            Tooltip.active_tooltip.hide()

        try:
            anchor_rx = self.anchor_widget.winfo_rootx()
            anchor_ry = self.anchor_widget.winfo_rooty()
            anchor_w = self.anchor_widget.winfo_width()
            anchor_h = self.anchor_widget.winfo_height()
            screen_width = self.anchor_widget.winfo_screenwidth()
            screen_height = self.anchor_widget.winfo_screenheight()
        except tk.TclError:
            return

        self.tip_window = tw = tk.Toplevel(root)
        tw.wm_withdraw()
        tw.wm_overrideredirect(True)
        try:
            tw.wm_attributes("-topmost", True)
        except tk.TclError:
            pass

        Tooltip.active_tooltip = self

        is_dark = self.dark_mode() if callable(self.dark_mode) else bool(self.dark_mode)
        bg_color = "#27272a" if is_dark else "#ffffff"
        fg_color = "#f4f4f5" if is_dark else "#0f172a"
        border_color = "#3f3f46" if is_dark else "#cbd5e1"

        frame = tk.Frame(tw, background=border_color, bd=1)
        frame.pack(fill="both", expand=True)

        label = tk.Label(
            frame,
            text=str(text).strip(),
            justify="left",
            background=bg_color,
            foreground=fg_color,
            wraplength=340,
            padx=10,
            pady=6,
            font=("Segoe UI", 9),
        )
        label.pack()

        tw.bind("<Enter>", lambda e: self.unschedule_hide(), add="+")
        label.bind("<Enter>", lambda e: self.unschedule_hide(), add="+")
        tw.bind("<Leave>", self.on_leave, add="+")
        label.bind("<Leave>", self.on_leave, add="+")

        tw.bind("<ButtonPress>", lambda e: self.hide(), add="+")
        label.bind("<ButtonPress>", lambda e: self.hide(), add="+")

        tw.update_idletasks()
        tip_w = tw.winfo_reqwidth()
        tip_h = tw.winfo_reqheight()

        x = anchor_rx + anchor_w - tip_w
        y = anchor_ry + anchor_h + 4

        if x < 10:
            x = max(10, anchor_rx)
        if x + tip_w > screen_width - 10:
            x = screen_width - tip_w - 10
        if y + tip_h > screen_height - 10:
            y = max(10, anchor_ry - tip_h - 4)

        tw.wm_geometry(f"{tip_w}x{tip_h}+{x}+{y}")
        tw.wm_deiconify()
        tw.lift()

    def hide(self, event=None):
        self.unschedule_hide()
        self.unschedule()
        if Tooltip.active_tooltip is self:
            Tooltip.active_tooltip = None
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except tk.TclError:
                pass
            self.tip_window = None

    @classmethod
    def hide_active(cls):
        if cls.active_tooltip:
            cls.active_tooltip.hide()



class EditTileDialog(tk.Toplevel):
    def __init__(self, master, tile=None, lang=LANG_EN, dark_mode=False):
        super().__init__(master)
        self.lang = lang
        self.dark_mode = dark_mode
        self.t = TRANSLATIONS.get(lang, TRANSLATIONS[LANG_EN])

        is_edit = tile is not None and bool((tile or {}).get("name"))
        default_name = self.t["new_tile_default_name"]

        self.title(self.t["edit_tile_title"] if is_edit else self.t["add_tile_title"])
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.result = None

        self.var_name = tk.StringVar(value=(tile or {}).get("name", default_name))
        initial_action = (tile or {}).get("action_type", "url")
        if initial_action not in ACTION_DEFS:
            initial_action = "url"
        self.var_action_type = tk.StringVar(value=initial_action)
        self.var_target = tk.StringVar(value=(tile or {}).get("target", ""))
        self.var_color = tk.StringVar(value=(tile or {}).get("color", DEFAULT_TILE_COLOR))
        self.var_description = tk.StringVar(value=(tile or {}).get("description", ""))

        self.existing_use_count = int((tile or {}).get("use_count", 0))
        self.existing_created_at = (tile or {}).get("created_at")
        self.existing_last_used = (tile or {}).get("last_used", "")
        self.existing_order = (tile or {}).get("order")

        self._apply_dialog_theme()
        self._build_ui()
        self._update_action_details()
        apply_windows_dark_titlebar(self, self.dark_mode)

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Return>", lambda _e: self._save())
        self.bind("<Escape>", lambda _e: self._cancel())
        if master and master.winfo_viewable():
            try:
                self.wait_visibility()
                self.focus_force()
            except tk.TclError:
                pass
        else:
            try:
                self.focus_force()
            except tk.TclError:
                pass

    def _apply_dialog_theme(self):
        self.bg_color = "#18181b" if self.dark_mode else "#f8fafc"
        self.fg_color = "#f4f4f5" if self.dark_mode else "#0f172a"
        self.card_bg = "#27272a" if self.dark_mode else "#ffffff"
        self.border_color = "#3f3f46" if self.dark_mode else "#e2e8f0"
        self.muted_fg = "#a1a1aa" if self.dark_mode else "#64748b"
        self.configure(bg=self.bg_color)

    def _build_ui(self):
        container = tk.Frame(self, bg=self.bg_color, padx=16, pady=16)
        container.pack(fill="both", expand=True)

        # Name field
        tk.Label(
            container,
            text=self.t["name"],
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.entry_name = ttk.Entry(container, textvariable=self.var_name, width=44)
        self.entry_name.grid(row=0, column=1, columnspan=2, sticky="ew", pady=(0, 6))

        # Action type combobox
        tk.Label(
            container,
            text=self.t["action_type"],
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=1, column=0, sticky="w", pady=(0, 6))

        action_keys = list(ACTION_DEFS.keys())
        self.action_display_map = {}
        display_values = []
        for k in action_keys:
            d = ACTION_DEFS[k]
            label_text = d["name_pl"] if self.lang == LANG_PL else d["name_en"]
            display_str = f"{d['icon']}  {k} - {label_text}"
            self.action_display_map[display_str] = k
            self.action_display_map[k] = display_str
            display_values.append(display_str)

        self.var_action_display = tk.StringVar(
            value=self.action_display_map.get(self.var_action_type.get(), display_values[0])
        )
        self.combo_action = ttk.Combobox(
            container,
            textvariable=self.var_action_display,
            values=display_values,
            state="readonly",
            width=41,
        )
        self.combo_action.grid(row=1, column=1, columnspan=2, sticky="ew", pady=(0, 6))
        self.combo_action.bind("<<ComboboxSelected>>", self._on_action_type_changed)

        # Target field + Browse button
        tk.Label(
            container,
            text=self.t["target"],
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=2, column=0, sticky="w", pady=(0, 6))

        target_row = tk.Frame(container, bg=self.bg_color)
        target_row.grid(row=2, column=1, columnspan=2, sticky="ew", pady=(0, 6))
        target_row.columnconfigure(0, weight=1)

        self.entry_target = ttk.Entry(target_row, textvariable=self.var_target)
        self.entry_target.grid(row=0, column=0, sticky="ew")

        self.btn_browse = ttk.Button(target_row, text=self.t["browse_file"], command=self._browse_target)
        self.btn_browse.grid(row=0, column=1, padx=(6, 0))

        # Dynamic Hint
        self.lbl_hint = tk.Label(
            container,
            text="",
            bg=self.card_bg,
            fg=self.muted_fg,
            font=("Segoe UI", 8),
            wraplength=380,
            justify="left",
            padx=8,
            pady=4,
            relief="solid",
            bd=1,
            highlightthickness=0,
        )
        self.lbl_hint.grid(row=3, column=1, columnspan=2, sticky="ew", pady=(0, 8))

        # Color row & Presets
        tk.Label(
            container,
            text=self.t["color"],
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=4, column=0, sticky="w", pady=(0, 4))

        color_row = tk.Frame(container, bg=self.bg_color)
        color_row.grid(row=4, column=1, columnspan=2, sticky="ew", pady=(0, 4))

        self.color_preview = tk.Frame(
            color_row,
            width=24,
            height=24,
            bg=self.var_color.get(),
            highlightthickness=1,
            highlightbackground=self.border_color,
        )
        self.color_preview.pack(side="left", padx=(0, 6))

        ttk.Entry(color_row, textvariable=self.var_color, width=12).pack(side="left")
        ttk.Button(color_row, text=self.t["choose_color"], command=self._pick_color).pack(
            side="left", padx=(6, 0)
        )

        # Preset swatches
        swatch_frame = tk.Frame(container, bg=self.bg_color)
        swatch_frame.grid(row=5, column=1, columnspan=2, sticky="w", pady=(0, 8))
        tk.Label(
            swatch_frame,
            text=self.t["presets"],
            bg=self.bg_color,
            fg=self.muted_fg,
            font=("Segoe UI", 8),
        ).pack(side="left", padx=(0, 6))

        for hex_code, color_name in PRESET_COLORS:
            btn = tk.Button(
                swatch_frame,
                bg=hex_code,
                activebackground=hex_code,
                width=2,
                height=1,
                bd=0,
                relief="flat",
                cursor="hand2",
                command=lambda c=hex_code: self._select_preset_color(c),
            )
            btn.pack(side="left", padx=2)

        # Description
        tk.Label(
            container,
            text=self.t["description"],
            bg=self.bg_color,
            fg=self.fg_color,
            font=("Segoe UI", 9, "bold"),
        ).grid(row=6, column=0, sticky="w", pady=(0, 12))
        ttk.Entry(container, textvariable=self.var_description, width=44).grid(
            row=6, column=1, columnspan=2, sticky="ew", pady=(0, 12)
        )

        # Action Buttons
        btn_bar = tk.Frame(container, bg=self.bg_color)
        btn_bar.grid(row=7, column=0, columnspan=3, sticky="e", pady=(4, 0))

        ttk.Button(btn_bar, text=self.t["cancel"], command=self._cancel).pack(side="right")
        ttk.Button(btn_bar, text=self.t["save"], command=self._save).pack(side="right", padx=(0, 8))

    def _select_preset_color(self, hex_code):
        self.var_color.set(hex_code)
        self.color_preview.configure(bg=hex_code)

    def _on_action_type_changed(self, event=None):
        disp = self.var_action_display.get()
        act_key = self.action_display_map.get(disp, "url")
        self.var_action_type.set(act_key)
        self._update_action_details()

    def _update_action_details(self):
        act_key = self.var_action_type.get()
        meta = ACTION_DEFS.get(act_key, ACTION_DEFS["url"])
        hint_text = meta["hint_pl"] if self.lang == LANG_PL else meta["hint_en"]
        self.lbl_hint.configure(text=f"💡 {hint_text}")

        browse_mode = meta.get("browse")
        if browse_mode == "folder":
            self.btn_browse.configure(text=self.t["browse_folder"], state="normal")
        elif browse_mode in ("file", "exe", "ps1", "python", "bat"):
            self.btn_browse.configure(text=self.t["browse_file"], state="normal")
        elif browse_mode == "any":
            self.btn_browse.configure(text=self.t["browse_folder"], state="normal")
        else:
            self.btn_browse.configure(state="disabled")

    def _browse_target(self):
        act_key = self.var_action_type.get()
        meta = ACTION_DEFS.get(act_key, {})
        browse_mode = meta.get("browse")

        selected = None
        if browse_mode == "folder":
            selected = filedialog.askdirectory(parent=self, title=self.t["browse_folder"])
        elif browse_mode == "exe":
            selected = filedialog.askopenfilename(
                parent=self,
                title=self.t["browse_file"],
                filetypes=[("Executable", "*.exe;*.com"), ("All files", "*.*")],
            )
        elif browse_mode == "ps1":
            selected = filedialog.askopenfilename(
                parent=self,
                title=self.t["browse_file"],
                filetypes=[("PowerShell Script", "*.ps1"), ("All files", "*.*")],
            )
        elif browse_mode == "python":
            selected = filedialog.askopenfilename(
                parent=self,
                title=self.t["browse_file"],
                filetypes=[("Python Script", "*.py;*.pyw"), ("All files", "*.*")],
            )
        elif browse_mode == "bat":
            selected = filedialog.askopenfilename(
                parent=self,
                title=self.t["browse_file"],
                filetypes=[("Batch File", "*.bat;*.cmd"), ("All files", "*.*")],
            )
        elif browse_mode == "file":
            selected = filedialog.askopenfilename(
                parent=self,
                title=self.t["browse_file"],
                filetypes=[("All files", "*.*")],
            )
        elif browse_mode == "any":
            selected = filedialog.askdirectory(parent=self, title=self.t["browse_folder"])
            if not selected:
                selected = filedialog.askopenfilename(
                    parent=self,
                    title=self.t["browse_file"],
                    filetypes=[("All files", "*.*")],
                )

        if selected:
            selected_path = str(Path(selected))
            self.var_target.set(selected_path)
            # Auto fill name if currently default
            cur_name = self.var_name.get().strip()
            if cur_name in ("", self.t["new_tile_default_name"], TRANSLATIONS[LANG_EN]["new_tile_default_name"]):
                stem_name = Path(selected_path).stem or Path(selected_path).name
                if stem_name:
                    self.var_name.set(stem_name)

    def _pick_color(self):
        chosen = colorchooser.askcolor(initialcolor=self.var_color.get(), parent=self)
        if chosen and chosen[1]:
            self.var_color.set(chosen[1])
            self.color_preview.configure(bg=chosen[1])

    def _save(self):
        name = self.var_name.get().strip()
        action_type = self.var_action_type.get().strip()
        target = self.var_target.get().strip()
        color = self.var_color.get().strip() or DEFAULT_TILE_COLOR
        description = self.var_description.get().strip()

        if not name:
            messagebox.showerror(self.t["error"], self.t["error_name_empty"], parent=self)
            return
        if action_type not in ACTION_DEFS:
            messagebox.showerror(self.t["error"], self.t["error_action_type"], parent=self)
            return
        if not target and action_type not in ("wsl",):
            messagebox.showerror(self.t["error"], self.t["error_target_empty"], parent=self)
            return
        try:
            self.winfo_rgb(color)
        except tk.TclError:
            messagebox.showerror(self.t["error"], self.t["error_color"], parent=self)
            return

        created_at = self.existing_created_at or datetime.now().isoformat()

        self.result = {
            "name": name,
            "action_type": action_type,
            "target": target,
            "color": color,
            "description": description,
            "use_count": self.existing_use_count,
            "created_at": created_at,
            "last_used": self.existing_last_used,
        }
        if self.existing_order is not None:
            self.result["order"] = self.existing_order
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class TileApp:
    def __init__(self, root):
        self.root = root
        self.config_file = PRIMARY_CONFIG_FILE
        self.tooltips = []
        self.rendered_cards = []
        self.header_tooltips = []

        # Application Icon
        try:
            if sys.platform == "win32":
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("wintiles.app.v1")
        except Exception:
            pass

        icon_path = get_icon_path()
        if icon_path:
            try:
                self.app_icon = tk.PhotoImage(file=str(icon_path))
                self.root.iconphoto(True, self.app_icon)
            except Exception:
                self.app_icon = None
        else:
            self.app_icon = None

        config = self._load_config()
        self.tiles = config["tiles"]
        self.always_on_top = bool(config["always_on_top"])
        self.dark_mode = bool(config.get("dark_mode", False))
        self.opacity = float(config.get("opacity", 1.0))
        self.opacity = max(0.10, min(1.0, self.opacity))
        self.lang = config.get("language", LANG_EN)
        if self.lang not in (LANG_EN, LANG_PL):
            self.lang = LANG_EN

        self.current_sort = config.get("sort_by", "manual")
        if self.current_sort not in SORT_KEYS:
            self.current_sort = "manual"

        self.search_query = ""
        self.toast_timer = None

        # Drag state
        self.drag_source_idx = None
        self.drag_start_pos = None
        self.is_dragging = False
        self.drag_ghost = None
        self.drag_hover_target = None

        self.var_topmost = tk.BooleanVar(value=self.always_on_top)
        self.var_dark_mode = tk.BooleanVar(value=self.dark_mode)
        self.var_language = tk.StringVar(value=LANG_NAMES.get(self.lang, "English"))
        self.var_search = tk.StringVar(value="")
        self.var_search.trace_add("write", lambda *args: self.on_search_changed())

        self.root.attributes("-topmost", self.always_on_top)
        try:
            self.root.attributes("-alpha", self.opacity)
        except Exception:
            pass
        self.root.minsize(760, 480)
        self.root.geometry("900x560")

        self.current_cols = 4

        self._build_main_layout()
        self.root.bind("<Escape>", self._on_escape_pressed)
        self.root.bind("<Unmap>", self._on_root_unmap, add="+")
        self.root.bind("<Deactivate>", lambda e: self._hide_all_tooltips(), add="+")
        self.root.bind("<FocusOut>", self._on_root_focus_out, add="+")
        self.apply_theme()
        self.update_ui_language()
        if self.current_sort != "manual":
            self.sort_tiles(self.current_sort, autosave=False, show_toast=False)
        else:
            self.sort_tiles("manual", autosave=False, show_toast=False)

    @property
    def t(self):
        return TRANSLATIONS.get(self.lang, TRANSLATIONS[LANG_EN])

    def _build_main_layout(self):
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill="both", expand=True)

        # Header bar
        self.header_bar = tk.Frame(self.main_container, padx=12, pady=10)
        self.header_bar.pack(fill="x")

        # Header Left: Brand Logo & Title
        self.brand_frame = tk.Frame(self.header_bar)
        self.brand_frame.pack(side="left")

        self.lbl_logo = tk.Label(
            self.brand_frame,
            text="⚡",
            font=("Segoe UI Emoji", 14),
        )
        self.lbl_logo.pack(side="left", padx=(0, 4))

        self.lbl_title = tk.Label(
            self.brand_frame,
            text="WinTiles",
            font=("Segoe UI", 12, "bold"),
        )
        self.lbl_title.pack(side="left")

        self.lbl_badge_count = tk.Label(
            self.brand_frame,
            text=f"({len(self.tiles)})",
            font=("Segoe UI", 9),
        )
        self.lbl_badge_count.pack(side="left", padx=(6, 12))

        # Header Center: Search bar
        self.search_frame = tk.Frame(self.header_bar, highlightthickness=1)
        self.search_frame.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self.lbl_search_icon = tk.Label(
            self.search_frame,
            text="🔍",
            font=("Segoe UI Emoji", 9),
        )
        self.lbl_search_icon.pack(side="left", padx=(6, 2))

        self.entry_search = tk.Entry(
            self.search_frame,
            textvariable=self.var_search,
            font=("Segoe UI", 9),
            bd=0,
            highlightthickness=0,
        )
        self.entry_search.pack(side="left", fill="x", expand=True, padx=4, pady=4)

        self.btn_clear_search = tk.Button(
            self.search_frame,
            text="✕",
            font=("Segoe UI", 8),
            bd=0,
            cursor="hand2",
            command=self.clear_search,
        )
        self.btn_clear_search.pack(side="right", padx=(2, 6))

        # Header Right Controls
        self.ctrl_frame = tk.Frame(self.header_bar)
        self.ctrl_frame.pack(side="right")

        # Sort dropdown
        self.lbl_sort = tk.Label(self.ctrl_frame, font=("Segoe UI", 9))
        self.lbl_sort.pack(side="left", padx=(0, 4))

        self.var_sort = tk.StringVar()
        self.combo_sort = ttk.Combobox(
            self.ctrl_frame,
            textvariable=self.var_sort,
            state="readonly",
            width=18,
        )
        self.combo_sort.pack(side="left", padx=(0, 8))
        self.combo_sort.bind("<<ComboboxSelected>>", self.on_sort_selected)

        # Add Tile Button (Primary Accent)
        self.btn_add_tile = tk.Button(
            self.ctrl_frame,
            font=("Segoe UI", 9, "bold"),
            bd=0,
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.add_tile,
        )
        self.btn_add_tile.pack(side="left", padx=(0, 6))

        # Save Button
        self.btn_save = ttk.Button(self.ctrl_frame, command=self.save_tiles)
        self.btn_save.pack(side="left", padx=(0, 6))

        # Topmost Toggle Button
        self.btn_topmost = tk.Button(
            self.ctrl_frame,
            text="📌",
            font=("Segoe UI Emoji", 10),
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=4,
            pady=2,
            command=self.toggle_always_on_top,
        )
        self.btn_topmost.pack(side="left", padx=(0, 6))

        # Dark Mode Toggle Button
        self.btn_dark_mode = tk.Button(
            self.ctrl_frame,
            text="🌙",
            font=("Segoe UI Emoji", 10),
            bd=1,
            relief="solid",
            cursor="hand2",
            padx=4,
            pady=2,
            command=self.toggle_dark_mode,
        )
        self.btn_dark_mode.pack(side="left", padx=(0, 6))

        # Language dropdown
        self.combo_lang = ttk.Combobox(
            self.ctrl_frame,
            textvariable=self.var_language,
            values=["Polski", "English"],
            state="readonly",
            width=8,
        )
        self.combo_lang.pack(side="left")
        self.combo_lang.bind("<<ComboboxSelected>>", self.on_language_change)

        # Scrollable Tiles Canvas
        self.content_container = tk.Frame(self.main_container)
        self.content_container.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        self.canvas = tk.Canvas(self.content_container, bd=0, highlightthickness=0)

        def _on_scrollbar_scroll(*args):
            self._hide_all_tooltips()
            self.canvas.yview(*args)

        self.scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", command=_on_scrollbar_scroll)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.tiles_inner_frame = tk.Frame(self.canvas)
        self.inner_frame_id = self.canvas.create_window((0, 0), window=self.tiles_inner_frame, anchor="nw")

        self.tiles_inner_frame.bind("<Configure>", self._on_inner_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.tiles_inner_frame.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<ButtonPress>", lambda e: self._hide_all_tooltips(), add="+")
        self.tiles_inner_frame.bind("<ButtonPress>", lambda e: self._hide_all_tooltips(), add="+")

        # Bottom Status Bar
        self.status_bar = tk.Frame(self.main_container, height=26, padx=12, pady=4)
        self.status_bar.pack(fill="x", side="bottom")

        self.lbl_status_hint = tk.Label(self.status_bar, font=("Segoe UI", 9))
        self.lbl_status_hint.pack(side="left")

        self.lbl_status_toast = tk.Label(self.status_bar, font=("Segoe UI", 9, "bold"))
        self.lbl_status_toast.pack(side="left", padx=(16, 0))

        self.lbl_status_count = tk.Label(self.status_bar, font=("Segoe UI", 9))
        self.lbl_status_count.pack(side="right")

        # Header tooltips
        self.header_tooltips = [
            Tooltip(self.btn_topmost, lambda: self.t["tt_topmost"], dark_mode=lambda: self.dark_mode),
            Tooltip(self.btn_dark_mode, lambda: self.t["tt_dark_mode"], dark_mode=lambda: self.dark_mode),
            Tooltip(self.btn_clear_search, lambda: self.t["tt_clear_search"], dark_mode=lambda: self.dark_mode),
            Tooltip(self.btn_add_tile, lambda: self.t["tt_add_tile"], dark_mode=lambda: self.dark_mode),
            Tooltip(self.btn_save, lambda: self.t["tt_save"], dark_mode=lambda: self.dark_mode),
        ]

        # Ctrl + MouseWheel transparency controls
        self.root.bind_all("<Control-MouseWheel>", self._on_ctrl_mousewheel)
        self.root.bind_all("<Control-Button-4>", lambda e: self._on_ctrl_mousewheel(type("Event", (), {"delta": 120, "state": getattr(e, "state", 0)})()))
        self.root.bind_all("<Control-Button-5>", lambda e: self._on_ctrl_mousewheel(type("Event", (), {"delta": -120, "state": getattr(e, "state", 0)})()))

    def _update_scrollregion(self):
        bbox = self.canvas.bbox("all")
        if bbox:
            canvas_h = self.canvas.winfo_height()
            content_h = bbox[3] - bbox[1]
            max_h = max(canvas_h, content_h)
            self.canvas.configure(scrollregion=(0, 0, bbox[2], max_h))
            if content_h <= canvas_h:
                self.canvas.yview_moveto(0)

    def _on_inner_frame_configure(self, event=None):
        self._update_scrollregion()

    def _on_canvas_configure(self, event):
        self._hide_all_tooltips()
        canvas_width = event.width
        self.canvas.itemconfig(self.inner_frame_id, width=canvas_width)

        new_cols = max(1, min(6, canvas_width // 200))
        if new_cols != self.current_cols:
            self.current_cols = new_cols
            self.render_tiles()
        else:
            self._update_scrollregion()

    def _on_mousewheel(self, event):
        self._hide_all_tooltips()
        if getattr(event, "state", 0) & 0x0004 or getattr(event, "state", 0) & 4:
            return self._on_ctrl_mousewheel(event)
        bbox = self.canvas.bbox("all")
        content_h = (bbox[3] - bbox[1]) if bbox else 0
        if content_h > self.canvas.winfo_height():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_ctrl_mousewheel(self, event):
        self._hide_all_tooltips()
        delta = getattr(event, "delta", 0)
        if not delta:
            return "break"
        steps = delta / 120.0
        change = steps * 0.05
        new_opacity = round(self.opacity + change, 2)
        new_opacity = max(0.10, min(1.0, new_opacity))
        if new_opacity != self.opacity:
            self.opacity = new_opacity
            try:
                self.root.attributes("-alpha", self.opacity)
            except Exception:
                pass
            pct = int(round(self.opacity * 100))
            self.show_toast(self.t["opacity_toast"].format(pct))
            self._autosave()
        return "break"

    def show_toast(self, message, duration_ms=2500):
        if self.toast_timer:
            self.root.after_cancel(self.toast_timer)
            self.toast_timer = None
        accent_color = "#34d399" if self.dark_mode else "#059669"
        self.lbl_status_toast.configure(text=message, fg=accent_color)
        self.toast_timer = self.root.after(duration_ms, self._clear_toast)

    def _clear_toast(self):
        self.lbl_status_toast.configure(text="")
        self.toast_timer = None

    def clear_search(self):
        self.var_search.set("")

    def on_search_changed(self):
        self.search_query = self.var_search.get().strip().lower()
        self.render_tiles()

    def update_ui_language(self):
        t = self.t
        self.root.title(t["app_title"])
        self.lbl_title.configure(text=t["app_title"].split(" - ")[0])
        self.btn_add_tile.configure(text=t["add_tile"])
        self.btn_save.configure(text=t["save"])
        self.lbl_sort.configure(text=t["sort_label"])
        self.lbl_status_hint.configure(text=t["hint_mouse"])

        sort_display_values = [
            t["sort_manual"],
            t["sort_most_used"],
            t["sort_recently_used"],
            t["sort_name_asc"],
            t["sort_name_desc"],
            t["sort_date_newest"],
            t["sort_date_oldest"],
            t["sort_action_type"],
        ]
        self.combo_sort.configure(values=sort_display_values)

        key_to_disp = {
            "manual": t["sort_manual"],
            "most_used": t["sort_most_used"],
            "recently_used": t["sort_recently_used"],
            "name_asc": t["sort_name_asc"],
            "name_desc": t["sort_name_desc"],
            "date_newest": t["sort_date_newest"],
            "date_oldest": t["sort_date_oldest"],
            "action_type": t["sort_action_type"],
        }
        self.var_sort.set(key_to_disp.get(self.current_sort, t["sort_manual"]))

        self.btn_topmost.configure(
            text="📌",
            relief="sunken" if self.var_topmost.get() else "solid",
        )
        self.btn_dark_mode.configure(text="🌙" if self.dark_mode else "☀️")

    def on_language_change(self, event=None):
        chosen = self.var_language.get()
        self.lang = LANG_CODES.get(chosen, LANG_EN)
        self.update_ui_language()
        self.render_tiles()
        self._autosave()

    def toggle_always_on_top(self):
        new_val = not self.var_topmost.get()
        self.var_topmost.set(new_val)
        self.root.attributes("-topmost", new_val)
        self.btn_topmost.configure(relief="sunken" if new_val else "solid")
        self._autosave()

    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        self.var_dark_mode.set(self.dark_mode)
        self.apply_theme()
        self.update_ui_language()
        self.render_tiles()
        self._autosave()

    def apply_theme(self):
        style = ttk.Style(self.root)

        if self.dark_mode:
            self.c_bg = "#18181b"
            self.c_surface = "#27272a"
            self.c_surface_hover = "#323238"
            self.c_border = "#3f3f46"
            self.c_border_drop = "#38bdf8"
            self.c_fg = "#f4f4f5"
            self.c_fg_muted = "#a1a1aa"
            self.c_input = "#1e1e24"
            self.c_accent = "#4f46e5"
            self.c_accent_active = "#4338ca"
            self.c_accent_fg = "#ffffff"
        else:
            self.c_bg = "#f8fafc"
            self.c_surface = "#ffffff"
            self.c_surface_hover = "#f1f5f9"
            self.c_border = "#e2e8f0"
            self.c_border_drop = "#0284c7"
            self.c_fg = "#0f172a"
            self.c_fg_muted = "#64748b"
            self.c_input = "#ffffff"
            self.c_accent = "#4f46e5"
            self.c_accent_active = "#4338ca"
            self.c_accent_fg = "#ffffff"

        self.root.configure(bg=self.c_bg)
        self.main_container.configure(bg=self.c_bg)
        self.header_bar.configure(bg=self.c_surface)
        self.brand_frame.configure(bg=self.c_surface)
        self.ctrl_frame.configure(bg=self.c_surface)
        self.search_frame.configure(bg=self.c_input, highlightbackground=self.c_border)
        self.lbl_search_icon.configure(bg=self.c_input, fg=self.c_fg_muted)
        self.entry_search.configure(bg=self.c_input, fg=self.c_fg, insertbackground=self.c_fg)
        self.btn_clear_search.configure(bg=self.c_input, fg=self.c_fg_muted, activebackground=self.c_input)

        self.lbl_logo.configure(bg=self.c_surface, fg=self.c_accent)
        self.lbl_title.configure(bg=self.c_surface, fg=self.c_fg)
        self.lbl_badge_count.configure(bg=self.c_surface, fg=self.c_fg_muted)
        self.lbl_sort.configure(bg=self.c_surface, fg=self.c_fg)

        self.btn_add_tile.configure(
            bg=self.c_accent,
            fg=self.c_accent_fg,
            activebackground=self.c_accent_active,
            activeforeground=self.c_accent_fg,
        )

        self.btn_topmost.configure(
            bg=self.c_surface,
            fg=self.c_fg,
            highlightbackground=self.c_border,
            activebackground=self.c_surface_hover,
        )
        self.btn_dark_mode.configure(
            bg=self.c_surface,
            fg=self.c_fg,
            highlightbackground=self.c_border,
            activebackground=self.c_surface_hover,
        )

        self.content_container.configure(bg=self.c_bg)
        self.canvas.configure(bg=self.c_bg)
        self.tiles_inner_frame.configure(bg=self.c_bg)

        self.status_bar.configure(bg=self.c_surface)
        self.lbl_status_hint.configure(bg=self.c_surface, fg=self.c_fg_muted)
        self.lbl_status_count.configure(bg=self.c_surface, fg=self.c_fg_muted)

        # Style ttk widgets
        if self.dark_mode:
            style.theme_use("default")
            style.configure(".", background=self.c_surface, foreground=self.c_fg)
            style.configure("TFrame", background=self.c_bg)
            style.configure("TLabel", background=self.c_surface, foreground=self.c_fg)
            style.configure("TButton", background="#3f3f46", foreground=self.c_fg, borderwidth=1)
            style.map("TButton", background=[("active", "#52525b")])
            style.configure(
                "TCombobox",
                fieldbackground=self.c_input,
                background="#3f3f46",
                foreground=self.c_fg,
                arrowcolor=self.c_fg,
            )
            style.map(
                "TCombobox",
                fieldbackground=[("readonly", self.c_input)],
                foreground=[("readonly", self.c_fg)],
            )
            style.configure("TEntry", fieldbackground=self.c_input, foreground=self.c_fg)
        else:
            if "vista" in style.theme_names():
                style.theme_use("vista")
            else:
                style.theme_use("default")
            style.configure(".", background=self.c_surface, foreground=self.c_fg)
            style.configure("TFrame", background=self.c_bg)
            style.configure("TLabel", background=self.c_surface, foreground=self.c_fg)
            style.configure("TButton", background="#e2e8f0", foreground=self.c_fg)
            style.map("TButton", background=[("active", "#cbd5e1")])
            style.configure(
                "TCombobox",
                fieldbackground="#ffffff",
                background="#e2e8f0",
                foreground="#000000",
            )
            style.map(
                "TCombobox",
                fieldbackground=[("readonly", "#ffffff")],
                foreground=[("readonly", "#000000")],
            )
            style.configure("TEntry", fieldbackground="#ffffff", foreground="#000000")

        apply_windows_dark_titlebar(self.root, self.dark_mode)

    def _validate_tiles(self, data):
        valid = []
        if isinstance(data, list):
            for i, item in enumerate(data):
                if (
                    isinstance(item, dict)
                    and isinstance(item.get("name"), str)
                    and isinstance(item.get("action_type"), str)
                    and isinstance(item.get("target"), str)
                ):
                    action_type = item["action_type"].strip().lower()
                    tile = {
                        "name": item["name"],
                        "action_type": action_type,
                        "target": item["target"],
                        "color": item.get("color", DEFAULT_TILE_COLOR),
                        "description": item.get("description", "")
                        if isinstance(item.get("description"), str)
                        else "",
                        "use_count": int(item.get("use_count", 0)),
                        "created_at": item.get("created_at")
                        or datetime.fromtimestamp(1700000000 + i * 60).isoformat(),
                        "last_used": str(item.get("last_used") or ""),
                        "order": int(item.get("order", i)),
                    }
                    valid.append(tile)

        return valid

    def _parse_config_payload(self, data):
        if isinstance(data, list):
            tiles = self._validate_tiles(data)
            if tiles:
                return {
                    "always_on_top": False,
                    "dark_mode": False,
                    "opacity": 1.0,
                    "language": LANG_EN,
                    "sort_by": "manual",
                    "tiles": tiles,
                }
            return None

        if isinstance(data, dict):
            tiles = self._validate_tiles(data.get("tiles"))
            always_on_top = bool(data.get("always_on_top", False))
            dark_mode = bool(data.get("dark_mode", False))
            try:
                opacity = float(data.get("opacity", 1.0))
                opacity = max(0.10, min(1.0, round(opacity, 2)))
            except (ValueError, TypeError):
                opacity = 1.0
            language = str(data.get("language", LANG_EN))
            sort_by = str(data.get("sort_by", "manual"))
            if language not in (LANG_EN, LANG_PL):
                language = LANG_EN
            if sort_by not in SORT_KEYS:
                sort_by = "manual"
            if tiles is not None:
                return {
                    "always_on_top": always_on_top,
                    "dark_mode": dark_mode,
                    "opacity": opacity,
                    "language": language,
                    "sort_by": sort_by,
                    "tiles": tiles,
                }
            return None

        return None

    def _try_read_payload(self, path):
        if not path or not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        return self._parse_config_payload(data)

    def _load_config(self):
        for candidate in [self.config_file, FALLBACK_CONFIG_FILE]:
            payload = self._try_read_payload(candidate)
            if payload:
                self.config_file = candidate
                return payload

        payload = self._try_read_payload(BUNDLED_SEED_CONFIG_FILE)
        if not payload:
            payload = {
                "always_on_top": False,
                "dark_mode": False,
                "opacity": 1.0,
                "language": LANG_EN,
                "sort_by": "manual",
                "tiles": list(DEFAULT_TILES),
            }
        self._write_config(payload)
        return payload

    def _write_config(self, payload):
        serialized = json.dumps(payload, indent=2, ensure_ascii=False)
        write_candidates = [self.config_file, FALLBACK_CONFIG_FILE]
        seen = set()
        last_error = None

        for candidate in write_candidates:
            candidate_key = str(candidate).lower()
            if candidate_key in seen:
                continue
            seen.add(candidate_key)
            try:
                candidate.parent.mkdir(parents=True, exist_ok=True)
                candidate.write_text(serialized, encoding="utf-8")
                self.config_file = candidate
                return
            except OSError as exc:
                last_error = exc

        if last_error:
            raise last_error

    def _build_config_payload(self):
        return {
            "always_on_top": bool(self.var_topmost.get()),
            "dark_mode": bool(self.var_dark_mode.get()),
            "opacity": round(float(self.opacity), 2),
            "language": self.lang,
            "sort_by": self.current_sort,
            "tiles": self.tiles,
        }

    def save_tiles(self):
        try:
            self._write_config(self._build_config_payload())
            self.show_toast(self.t["saved_toast"])
        except OSError as exc:
            messagebox.showerror(self.t["save_error_title"], str(exc), parent=self.root)

    def _autosave(self):
        try:
            self._write_config(self._build_config_payload())
        except OSError:
            pass

    def _hide_all_tooltips(self):
        Tooltip.hide_active()
        for tt in getattr(self, "tooltips", []):
            tt.hide()
        for tt in getattr(self, "header_tooltips", []):
            tt.hide()

    def on_sort_selected(self, event=None):
        disp = self.var_sort.get()
        t = self.t
        disp_to_key = {
            t["sort_manual"]: "manual",
            t["sort_most_used"]: "most_used",
            t["sort_recently_used"]: "recently_used",
            t["sort_name_asc"]: "name_asc",
            t["sort_name_desc"]: "name_desc",
            t["sort_date_newest"]: "date_newest",
            t["sort_date_oldest"]: "date_oldest",
            t["sort_action_type"]: "action_type",
        }
        key = disp_to_key.get(disp, "manual")
        self.sort_tiles(key)

    def sort_tiles(self, mode, autosave=True, show_toast=True):
        self.current_sort = mode
        if mode == "manual":
            self.tiles.sort(key=lambda item: int(item.get("order", 0)))
        elif mode == "most_used":
            self.tiles.sort(
                key=lambda item: (-int(item.get("use_count", 0)), polish_sort_key(item.get("name", "")))
            )
        elif mode == "recently_used":
            self.tiles.sort(
                key=lambda item: (str(item.get("last_used") or ""), polish_sort_key(item.get("name", ""))),
                reverse=True,
            )
        elif mode == "name_asc":
            self.tiles.sort(key=lambda item: polish_sort_key(item.get("name", "")))
        elif mode == "name_desc":
            self.tiles.sort(key=lambda item: polish_sort_key(item.get("name", "")), reverse=True)
        elif mode == "date_newest":
            self.tiles.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
        elif mode == "date_oldest":
            self.tiles.sort(key=lambda item: str(item.get("created_at") or ""))
        elif mode == "action_type":
            self.tiles.sort(
                key=lambda item: (
                    str(item.get("action_type", "")).lower(),
                    polish_sort_key(item.get("name", "")),
                )
            )

        self.render_tiles()
        if autosave:
            self._autosave()

        if show_toast:
            sort_name = self.var_sort.get()
            self.show_toast(self.t["toast_sorted"].format(sort_name))


    def render_tiles(self):
        self._hide_all_tooltips()
        self.tooltips = []
        self.rendered_cards = []

        for child in self.tiles_inner_frame.winfo_children():
            child.destroy()

        cols = self.current_cols
        for i in range(max(10, cols + 4)):
            self.tiles_inner_frame.columnconfigure(i, weight=0, uniform="")
        for i in range(cols):
            self.tiles_inner_frame.columnconfigure(i, weight=1, uniform="col")

        # Filter tiles if search query is present
        filtered_items = []
        for index, tile in enumerate(self.tiles):
            if self.search_query:
                q = self.search_query
                name_match = q in str(tile.get("name", "")).lower()
                type_match = q in str(tile.get("action_type", "")).lower()
                target_match = q in str(tile.get("target", "")).lower()
                desc_match = q in str(tile.get("description", "")).lower()
                if not (name_match or type_match or target_match or desc_match):
                    continue
            filtered_items.append((index, tile))

        # Update count labels
        total_count = len(self.tiles)
        shown_count = len(filtered_items)
        self.lbl_badge_count.configure(text=f"({total_count})")

        if self.search_query:
            self.lbl_status_count.configure(
                text=self.t["status_filtered_count"].format(shown_count, total_count)
            )
        else:
            self.lbl_status_count.configure(text=self.t["status_tile_count"].format(total_count))

        # Empty state
        if not filtered_items:
            empty_box = tk.Frame(self.tiles_inner_frame, bg=self.c_bg, pady=40)
            empty_box.grid(row=0, column=0, columnspan=cols, sticky="nsew")

            tk.Label(
                empty_box,
                text="🔍",
                font=("Segoe UI Emoji", 28),
                bg=self.c_bg,
                fg=self.c_fg_muted,
            ).pack()
            tk.Label(
                empty_box,
                text=self.t["empty_search"].format(self.search_query),
                font=("Segoe UI", 11),
                bg=self.c_bg,
                fg=self.c_fg_muted,
                pady=6,
            ).pack()
            btn_reset = ttk.Button(empty_box, text=self.t["clear_search"], command=self.clear_search)
            btn_reset.pack(pady=4)
            return

        # Render cards
        for grid_idx, (real_index, tile) in enumerate(filtered_items):
            row = grid_idx // cols
            col = grid_idx % cols

            tile_color = self._safe_tile_color(tile.get("color", DEFAULT_TILE_COLOR))
            action_type = tile.get("action_type", "url")
            meta = ACTION_DEFS.get(action_type, ACTION_DEFS["url"])
            icon = meta["icon"]

            # Card container
            card = tk.Frame(
                self.tiles_inner_frame,
                bg=self.c_surface,
                highlightthickness=1,
                highlightbackground=self.c_border,
                cursor="hand2",
            )
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            card.real_index = real_index

            # Color strip on the left
            color_strip = tk.Frame(card, width=5, bg=tile_color)
            color_strip.pack(side="left", fill="y")

            # Main content area
            content = tk.Frame(card, bg=self.c_surface, padx=8, pady=6)
            content.pack(side="left", fill="both", expand=True)

            # Top Row: Icon + Title + Count Badge + Info Icon ("i")
            top_row = tk.Frame(content, bg=self.c_surface)
            top_row.pack(fill="x", expand=True)

            lbl_icon = tk.Label(
                top_row,
                text=icon,
                font=("Segoe UI Emoji", 11),
                bg=self.c_surface,
                fg=self.c_fg,
            )
            lbl_icon.pack(side="left", padx=(0, 4))

            # Info icon ("i") in the top right corner - only displayed when description exists
            desc = self._build_tooltip_text(tile)
            lbl_info = None
            if desc:
                lbl_info = tk.Label(
                    top_row,
                    text="ⓘ",
                    font=("Segoe UI", 9),
                    bg=self.c_surface,
                    fg=self.c_fg_muted,
                    cursor="hand2",
                    padx=2,
                )
                lbl_info.pack(side="right")

            use_count = int(tile.get("use_count", 0))
            if use_count > 0:
                lbl_cnt = tk.Label(
                    top_row,
                    text=f"⚡{use_count}",
                    font=("Segoe UI", 7, "bold"),
                    bg="#3f3f46" if self.dark_mode else "#f1f5f9",
                    fg="#fbbf24" if self.dark_mode else "#d97706",
                    padx=4,
                    pady=1,
                )
                lbl_cnt.pack(side="right", padx=(0, 4))

            title_text = tile["name"]
            lbl_name = tk.Label(
                top_row,
                text=title_text,
                font=("Segoe UI", 9, "bold"),
                bg=self.c_surface,
                fg=self.c_fg,
                anchor="w",
            )
            lbl_name.pack(side="left", fill="x", expand=True)

            # Bottom Row: Action Type Badge + Subtitle
            bot_row = tk.Frame(content, bg=self.c_surface)
            bot_row.pack(fill="x", expand=True, pady=(2, 0))

            lbl_badge = tk.Label(
                bot_row,
                text=action_type.upper(),
                font=("Segoe UI", 7, "bold"),
                bg=self.c_surface,
                fg=tile_color,
            )
            lbl_badge.pack(side="left", padx=(0, 4))

            sub_text = get_target_preview(action_type, tile.get("target", ""))
            lbl_sub = tk.Label(
                bot_row,
                text=sub_text,
                font=("Segoe UI", 8),
                bg=self.c_surface,
                fg=self.c_fg_muted,
                anchor="w",
            )
            lbl_sub.pack(side="left", fill="x", expand=True)

            # Store card reference
            hover_widgets = [top_row, lbl_icon, lbl_name, bot_row, lbl_badge, lbl_sub]
            if lbl_info is not None:
                hover_widgets.append(lbl_info)

            card_info = {
                "card": card,
                "content": content,
                "real_index": real_index,
                "tile": tile,
                "tile_color": tile_color,
                "widgets": [card, color_strip, content, top_row, lbl_icon, lbl_name, bot_row, lbl_badge, lbl_sub],
                "hover_widgets": hover_widgets,
                "lbl_info": lbl_info,
            }
            if use_count > 0:
                card_info["widgets"].append(lbl_cnt)
            self.rendered_cards.append(card_info)

            if lbl_info is not None:
                # Tooltip strictly on the info icon in the top right corner displaying the description
                tt_func = lambda t=tile: self._build_tooltip_text(t)
                tt = Tooltip(lbl_info, tt_func, dark_mode=lambda: self.dark_mode)
                self.tooltips.append(tt)

                # Visual hover effects on the info icon itself
                info_hover_fg = "#38bdf8" if self.dark_mode else "#0284c7"
                info_normal_fg = self.c_fg_muted
                lbl_info.bind("<Enter>", lambda e, l=lbl_info, c=info_hover_fg: l.configure(fg=c), add="+")
                lbl_info.bind("<Leave>", lambda e, l=lbl_info, c=info_normal_fg: l.configure(fg=c), add="+")
                # Prevent click on info icon from running tile or dragging
                lbl_info.bind("<ButtonPress-1>", lambda e: "break", add="+")
                lbl_info.bind("<ButtonRelease-1>", lambda e: "break", add="+")
                lbl_info.bind("<MouseWheel>", self._on_mousewheel, add="+")

            # Bind mouse events to card and all child widgets
            self._bind_card_events(card_info)

    def _build_tooltip_text(self, tile):
        return str(tile.get("description") or "").strip()

    def _bind_card_events(self, card_info):
        real_idx = card_info["real_index"]

        def on_press(e):
            self.on_tile_press(e, real_idx)

        def on_motion(e):
            self.on_tile_motion(e)

        def on_release(e):
            self.on_tile_release(e)

        def on_context(e):
            self.open_tile_menu(e, real_idx)

        def on_enter(e):
            self.on_tile_enter(card_info)

        def on_leave(e):
            self.on_tile_leave(e, card_info)

        for w in card_info["widgets"]:
            w.bind("<ButtonPress-1>", on_press, add="+")
            w.bind("<B1-Motion>", on_motion, add="+")
            w.bind("<ButtonRelease-1>", on_release, add="+")
            w.bind("<Button-3>", on_context, add="+")
            w.bind("<Enter>", on_enter, add="+")
            w.bind("<Leave>", on_leave, add="+")
            w.bind("<MouseWheel>", self._on_mousewheel, add="+")

    def on_tile_enter(self, card_info):
        if self.is_dragging:
            return
        card = card_info["card"]
        card.configure(
            highlightbackground=card_info["tile_color"],
            bg=self.c_surface_hover,
        )
        card_info["content"].configure(bg=self.c_surface_hover)
        for w in card_info.get("hover_widgets", []):
            try:
                w.configure(bg=self.c_surface_hover)
            except tk.TclError:
                pass

    def on_tile_leave(self, event, card_info):
        if self.is_dragging:
            return
        card = card_info["card"]
        if event:
            try:
                rx = card.winfo_rootx()
                ry = card.winfo_rooty()
                rw = card.winfo_width()
                rh = card.winfo_height()
                if rx <= event.x_root <= rx + rw and ry <= event.y_root <= ry + rh:
                    return
            except tk.TclError:
                pass
        card.configure(
            highlightbackground=self.c_border,
            bg=self.c_surface,
        )
        card_info["content"].configure(bg=self.c_surface)
        for w in card_info.get("hover_widgets", []):
            try:
                w.configure(bg=self.c_surface)
            except tk.TclError:
                pass

    def get_card_info_at_coords(self, x_root, y_root):
        cx = self.canvas.winfo_rootx()
        cy = self.canvas.winfo_rooty()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        if not (cx <= x_root <= cx + cw and cy <= y_root <= cy + ch):
            return None

        # 1. Exact hit test
        for item in self.rendered_cards:
            card = item["card"]
            if not card.winfo_ismapped():
                continue
            rx = card.winfo_rootx()
            ry = card.winfo_rooty()
            rw = card.winfo_width()
            rh = card.winfo_height()
            if rx <= x_root <= rx + rw and ry <= y_root <= ry + rh:
                return item

        # 2. Nearest card within margin gap (+16px padding)
        best_item = None
        best_dist = float("inf")
        for item in self.rendered_cards:
            card = item["card"]
            if not card.winfo_ismapped():
                continue
            rx = card.winfo_rootx()
            ry = card.winfo_rooty()
            rw = card.winfo_width()
            rh = card.winfo_height()
            pad = 16
            if (rx - pad) <= x_root <= (rx + rw + pad) and (ry - pad) <= y_root <= (ry + rh + pad):
                center_x = rx + rw / 2
                center_y = ry + rh / 2
                dist = (x_root - center_x) ** 2 + (y_root - center_y) ** 2
                if dist < best_dist:
                    best_dist = dist
                    best_item = item

        return best_item


    def on_tile_press(self, event, real_index):
        self._hide_all_tooltips()
        self.drag_source_idx = real_index
        self.drag_start_pos = (event.x_root, event.y_root)
        self.is_dragging = False
        self.drag_hover_target = None

    def on_tile_motion(self, event):
        if self.drag_source_idx is None or self.drag_start_pos is None:
            return

        dx = abs(event.x_root - self.drag_start_pos[0])
        dy = abs(event.y_root - self.drag_start_pos[1])

        if not self.is_dragging and (dx > 6 or dy > 6):
            self.is_dragging = True
            self._hide_all_tooltips()
            self.root.configure(cursor="fleur")
            self._create_drag_ghost(self.drag_source_idx)

        if self.is_dragging:
            if self.drag_ghost:
                self.drag_ghost.wm_geometry(f"+{event.x_root + 16}+{event.y_root + 16}")

            # Check card under cursor
            hover_item = self.get_card_info_at_coords(event.x_root, event.y_root)
            hover_idx = hover_item["real_index"] if hover_item else None

            if hover_idx != self.drag_hover_target:
                # Clear previous highlight
                if self.drag_hover_target is not None:
                    for item in self.rendered_cards:
                        if item["real_index"] == self.drag_hover_target:
                            item["card"].configure(
                                highlightbackground=self.c_border,
                                highlightthickness=1,
                            )
                self.drag_hover_target = hover_idx
                # Apply highlight on new target
                if hover_idx is not None and hover_idx != self.drag_source_idx:
                    hover_item["card"].configure(
                        highlightbackground=self.c_border_drop,
                        highlightthickness=2,
                    )

            # Auto-scroll canvas if dragging near top/bottom edge
            cy = self.canvas.winfo_rooty()
            ch = self.canvas.winfo_height()
            bbox = self.canvas.bbox("all")
            content_h = (bbox[3] - bbox[1]) if bbox else 0
            if content_h > ch:
                y_top, y_bot = self.canvas.yview()
                if event.y_root < cy + 30 and y_top > 0.001:
                    self.canvas.yview_scroll(-1, "units")
                elif event.y_root > cy + ch - 30 and y_bot < 0.999:
                    self.canvas.yview_scroll(1, "units")

    def _create_drag_ghost(self, source_index):
        tile = self.tiles[source_index]
        self.drag_ghost = tw = tk.Toplevel(self.root)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)
        try:
            tw.wm_attributes("-alpha", 0.90)
        except Exception:
            pass

        ghost_box = tk.Frame(
            tw,
            bg=self.c_surface,
            highlightthickness=2,
            highlightbackground=self.c_accent,
            padx=10,
            pady=6,
        )
        ghost_box.pack(fill="both", expand=True)

        tile_color = self._safe_tile_color(tile.get("color", DEFAULT_TILE_COLOR))
        pill = tk.Frame(ghost_box, width=4, bg=tile_color)
        pill.pack(side="left", fill="y", padx=(0, 6))

        act_type = tile.get("action_type", "url")
        icon = ACTION_DEFS.get(act_type, {}).get("icon", "⚡")

        lbl_i = tk.Label(
            ghost_box,
            text=icon,
            font=("Segoe UI Emoji", 10),
            bg=self.c_surface,
            fg=self.c_fg,
        )
        lbl_i.pack(side="left", padx=(0, 4))

        lbl_t = tk.Label(
            ghost_box,
            text=tile.get("name", ""),
            font=("Segoe UI", 9, "bold"),
            bg=self.c_surface,
            fg=self.c_fg,
        )
        lbl_t.pack(side="left")

    def on_tile_release(self, event):
        if self.drag_source_idx is None:
            return

        source_idx = self.drag_source_idx
        was_dragging = self.is_dragging

        # Clean up drag state
        self.drag_source_idx = None
        self.drag_start_pos = None
        self.is_dragging = False
        self.drag_hover_target = None
        self.root.configure(cursor="")

        if self.drag_ghost:
            try:
                self.drag_ghost.destroy()
            except tk.TclError:
                pass
            self.drag_ghost = None

        if not was_dragging:
            # Click action -> Run tile
            self.run_tile(source_idx)
            return

        # Drag & Drop finish
        hover_item = self.get_card_info_at_coords(event.x_root, event.y_root)
        target_idx = hover_item["real_index"] if hover_item else None

        if target_idx is not None and target_idx != source_idx:
            self.reorder_tiles(source_idx, target_idx)
        else:
            self.render_tiles()

    def _on_escape_pressed(self, event=None):
        self._hide_all_tooltips()
        if self.is_dragging:
            self._cancel_drag()
        elif self.search_query:
            self.clear_search()

    def _on_root_unmap(self, event):
        if event.widget == self.root:
            self._hide_all_tooltips()

    def _on_root_focus_out(self, event):
        if event.widget == self.root:
            self._hide_all_tooltips()

    def _cancel_drag(self):
        self.drag_source_idx = None
        self.drag_start_pos = None
        self.is_dragging = False
        self.drag_hover_target = None
        self.root.configure(cursor="")
        if self.drag_ghost:
            try:
                self.drag_ghost.destroy()
            except tk.TclError:
                pass
            self.drag_ghost = None
        self.render_tiles()

    def reorder_tiles(self, source_index, target_index):
        if source_index == target_index:
            return

        tile = self.tiles.pop(source_index)
        self.tiles.insert(target_index, tile)

        for idx, t in enumerate(self.tiles):
            t["order"] = idx

        # Switch sort mode to manual order
        self.current_sort = "manual"
        self.var_sort.set(self.t["sort_manual"])

        self.render_tiles()
        self._autosave()
        self.show_toast(self.t["toast_reordered"].format(tile["name"], target_index + 1))

    def run_tile(self, index):
        tile = self.tiles[index]
        action_type = tile["action_type"].strip().lower()
        target = tile["target"].strip()

        try:
            if action_type == "url":
                dest = target
                if not dest.startswith(("http://", "https://")):
                    dest = "https://" + dest
                webbrowser.open(dest, new=2)

            elif action_type in ("path", "file"):
                clean_target = os.path.expandvars(target.strip('"\''))
                path = Path(clean_target).expanduser()
                if not path.exists():
                    raise FileNotFoundError(self.t["path_not_found"].format(path))
                os.startfile(str(path))  # type: ignore[attr-defined]

            elif action_type == "exe":
                cand_path = Path(os.path.expandvars(target.strip('"\''))).expanduser()
                if cand_path.exists():
                    if cand_path.is_dir():
                        raise IsADirectoryError(self.t["path_is_dir"].format(cand_path))
                    subprocess.Popen([str(cand_path)])
                else:
                    subprocess.Popen(target, shell=True)

            elif action_type == "ps1":
                script_path = Path(os.path.expandvars(target.strip('"\''))).expanduser()
                if not script_path.exists():
                    raise FileNotFoundError(self.t["script_not_found"].format(script_path))
                subprocess.Popen(
                    [
                        "powershell.exe",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        str(script_path),
                    ]
                )

            elif action_type == "python":
                script_path = Path(os.path.expandvars(target.strip('"\''))).expanduser()
                if not script_path.exists():
                    raise FileNotFoundError(self.t["script_not_found"].format(script_path))
                python_exe = "python"
                if not getattr(sys, "frozen", False) and sys.executable and "python" in Path(sys.executable).stem.lower():
                    python_exe = sys.executable
                else:
                    import shutil
                    cand = shutil.which("python") or shutil.which("python3") or shutil.which("py")
                    if cand:
                        python_exe = cand
                subprocess.Popen([python_exe, str(script_path)])

            elif action_type == "bat":
                bat_path = Path(os.path.expandvars(target.strip('"\''))).expanduser()
                if not bat_path.exists():
                    raise FileNotFoundError(self.t["path_not_found"].format(bat_path))
                subprocess.Popen(["cmd.exe", "/c", str(bat_path)])

            elif action_type == "terminal":
                folder_path = Path(os.path.expandvars(target.strip('"\''))).expanduser()
                if not folder_path.exists():
                    folder_path = Path.home()
                try:
                    subprocess.Popen(["wt.exe", "-d", str(folder_path)])
                except Exception:
                    subprocess.Popen(
                        [
                            "powershell.exe",
                            "-NoExit",
                            "-Command",
                            f"Set-Location -LiteralPath '{folder_path}'",
                        ]
                    )

            elif action_type == "vscode":
                target_norm = os.path.expandvars(target.strip('"\''))
                import shutil
                code_bin = shutil.which("code") or shutil.which("code.cmd")
                if code_bin:
                    subprocess.Popen([code_bin, target_norm])
                else:
                    subprocess.Popen(f'code "{target_norm}"', shell=True)

            elif action_type == "wsl":
                cmd_target = target.strip().strip('"\'')
                if not cmd_target or cmd_target in ("~", "/"):
                    subprocess.Popen(["wsl.exe"])
                else:
                    folder_cand = Path(os.path.expandvars(cmd_target)).expanduser()
                    if folder_cand.exists() and folder_cand.is_dir():
                        subprocess.Popen(["wsl.exe", "--cd", str(folder_cand)])
                    else:
                        subprocess.Popen(["wsl.exe", "-e", "bash", "-lc", cmd_target])

            elif action_type == "clipboard":
                self.root.clipboard_clear()
                self.root.clipboard_append(target)
                self.root.update()
                snippet = (target[:35] + "...") if len(target) > 35 else target
                self.show_toast(self.t["toast_copied"].format(snippet))

            elif action_type == "websearch":
                q = urllib.parse.quote_plus(target.strip())
                webbrowser.open(f"https://www.google.com/search?q={q}", new=2)

            elif action_type == "chrome_profile":
                profile_path = Path(os.path.expandvars(target.strip('"\''))).expanduser()
                if not profile_path.exists():
                    raise FileNotFoundError(self.t["chrome_profile_not_found"].format(profile_path))

                chrome_exe = self._resolve_chrome_exe()
                user_data_dir, profile_dir = self._extract_chrome_profile_parts(profile_path)
                running_pid = self._find_running_chrome_profile(user_data_dir, profile_dir)
                if running_pid and self._focus_window_by_pid(running_pid):
                    pass

                else:
                    subprocess.Popen(
                        [
                            str(chrome_exe),
                            f"--user-data-dir={user_data_dir}",
                            f"--profile-directory={profile_dir}",
                        ]
                    )

            elif action_type == "command":
                subprocess.Popen(target, shell=True)

            else:
                raise ValueError(self.t["unknown_action"].format(action_type))

            # Update usage stats
            tile["use_count"] = int(tile.get("use_count", 0)) + 1
            tile["last_used"] = datetime.now().isoformat()
            self._autosave()
            self.render_tiles()

        except Exception as exc:
            messagebox.showerror(self.t["run_error_title"], str(exc), parent=self.root)

    def _resolve_chrome_exe(self):
        candidates = [
            DEFAULT_CHROME_EXE,
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(self.t["chrome_exe_not_found"])

    def _extract_chrome_profile_parts(self, profile_path):
        profile_name = profile_path.name
        parent_name = profile_path.parent.name.lower()

        if parent_name == "user data":
            return profile_path.parent, profile_name

        if profile_name.lower() == "user data":
            return profile_path, "Default"

        raise ValueError(self.t["chrome_profile_invalid"])

    def _find_running_chrome_profile(self, user_data_dir, profile_dir):
        ps_script = (
            "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" "
            "| Select-Object ProcessId, CommandLine "
            "| ConvertTo-Json -Compress"
        )
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0 or not result.stdout.strip():
                return None

            payload = json.loads(result.stdout.strip())
            records = payload if isinstance(payload, list) else [payload]

            user_data_norm = self._normalize_path_for_match(str(user_data_dir))
            profile_norm = str(profile_dir).strip().lower()
            default_user_data = self._normalize_path_for_match(
                str(Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")).expanduser())
            )
            is_default_profile = profile_norm == "default"
            is_default_user_data = user_data_norm == default_user_data

            for rec in records:
                cmd = str(rec.get("CommandLine") or "").lower()
                pid = rec.get("ProcessId")
                if not cmd or not pid:
                    continue
                cmd_norm = self._normalize_path_for_match(cmd)
                has_user_data_flag = "--user-data-dir" in cmd
                has_profile_flag = "--profile-directory" in cmd

                user_match = (user_data_norm in cmd_norm) if has_user_data_flag else is_default_user_data
                profile_match = (profile_norm in cmd) if has_profile_flag else is_default_profile

                if user_match and profile_match:
                    return int(pid)

            if is_default_profile and is_default_user_data:
                for rec in records:
                    cmd = str(rec.get("CommandLine") or "").lower()
                    pid = rec.get("ProcessId")
                    if not pid:
                        continue
                    if "--user-data-dir" in cmd or "--profile-directory" in cmd:
                        continue
                    if self._pid_has_visible_window(int(pid)):
                        return int(pid)
        except Exception:
            return None
        return None

    def _focus_window_by_pid(self, pid):
        user32 = ctypes.windll.user32
        target_hwnds = []

        enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def _enum_windows(hwnd, _lparam):
            proc_id = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
            if proc_id.value != pid:
                return True
            if not user32.IsWindowVisible(hwnd):
                return True
            if user32.GetWindowTextLengthW(hwnd) == 0:
                return True
            target_hwnds.append(hwnd)
            return True

        user32.EnumWindows(enum_proc(_enum_windows), 0)
        if not target_hwnds:
            return False

        hwnd = target_hwnds[0]
        SW_RESTORE = 9
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2
        user32.ShowWindow(hwnd, SW_RESTORE)
        if user32.SetForegroundWindow(hwnd):
            return True

        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        return bool(user32.SetForegroundWindow(hwnd))

    def _pid_has_visible_window(self, pid):
        user32 = ctypes.windll.user32
        found = {"value": False}
        enum_proc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

        def _enum_windows(hwnd, _lparam):
            proc_id = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(proc_id))
            if proc_id.value != pid:
                return True
            if user32.IsWindowVisible(hwnd) and user32.GetWindowTextLengthW(hwnd) > 0:
                found["value"] = True
                return False
            return True

        user32.EnumWindows(enum_proc(_enum_windows), 0)
        return found["value"]

    def _normalize_path_for_match(self, value):
        return value.replace('"', "").replace("/", "\\").lower()

    def add_tile(self):
        self._hide_all_tooltips()
        dialog = EditTileDialog(
            self.root,
            tile={
                "name": self.t["new_tile_default_name"],
                "action_type": "url",
                "target": "",
                "color": DEFAULT_TILE_COLOR,
                "description": "",
                "use_count": 0,
                "created_at": datetime.now().isoformat(),
                "last_used": "",
                "order": len(self.tiles),
            },
            lang=self.lang,
            dark_mode=self.dark_mode,
        )
        self.root.wait_window(dialog)
        if dialog.result:
            dialog.result["order"] = len(self.tiles)
            self.tiles.append(dialog.result)
            if self.current_sort != "manual":
                self.sort_tiles(self.current_sort, autosave=False, show_toast=False)
            else:
                self.render_tiles()
            self._autosave()
            self.show_toast(f"✓ {dialog.result['name']}")

    def edit_tile(self, index):
        self._hide_all_tooltips()
        dialog = EditTileDialog(
            self.root,
            tile=self.tiles[index],
            lang=self.lang,
            dark_mode=self.dark_mode,
        )
        self.root.wait_window(dialog)
        if dialog.result:
            dialog.result["order"] = self.tiles[index].get("order", index)
            self.tiles[index] = dialog.result
            if self.current_sort != "manual":
                self.sort_tiles(self.current_sort, autosave=False, show_toast=False)
            else:
                self.render_tiles()
            self._autosave()
            self.show_toast(f"✓ {dialog.result['name']}")

    def duplicate_tile(self, index):
        self._hide_all_tooltips()
        source = self.tiles[index]
        dup = copy.deepcopy(source)
        dup["name"] = f"{dup['name']}{self.t['copy_suffix']}"
        dup["use_count"] = 0
        dup["created_at"] = datetime.now().isoformat()
        dup["last_used"] = ""

        self.tiles.insert(index + 1, dup)
        for idx, t in enumerate(self.tiles):
            t["order"] = idx

        if self.current_sort != "manual":
            self.sort_tiles(self.current_sort, autosave=False, show_toast=False)
        else:
            self.render_tiles()
        self._autosave()
        self.show_toast(self.t["toast_duplicated"].format(dup["name"]))

    def reset_tile_stats(self, index):
        self._hide_all_tooltips()
        tile = self.tiles[index]
        tile["use_count"] = 0
        tile["last_used"] = ""
        self.render_tiles()
        self._autosave()
        self.show_toast(self.t["toast_stats_reset"].format(tile["name"]))

    def delete_tile(self, index):
        self._hide_all_tooltips()
        tile_name = self.tiles[index]["name"]
        if messagebox.askyesno(
            self.t["delete_title"],
            self.t["delete_confirm"].format(tile_name),
            parent=self.root,
        ):
            del self.tiles[index]
            for idx, t in enumerate(self.tiles):
                t["order"] = idx
            self.render_tiles()
            self._autosave()
            self.show_toast(self.t["toast_deleted"].format(tile_name))


    def open_tile_menu(self, event, index):
        self._hide_all_tooltips()
        bg = "#27272a" if self.dark_mode else "#ffffff"
        fg = "#f4f4f5" if self.dark_mode else "#0f172a"
        active_bg = "#4f46e5" if self.dark_mode else "#e0e7ff"
        active_fg = "#ffffff" if self.dark_mode else "#1e1b4b"

        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=active_fg,
            font=("Segoe UI", 9),
        )
        menu.add_command(label=f"🚀  {self.t['run']}", command=lambda: self.run_tile(index))
        menu.add_command(label=f"✏️  {self.t['edit']}", command=lambda: self.edit_tile(index))
        menu.add_command(label=f"📋  {self.t['duplicate']}", command=lambda: self.duplicate_tile(index))
        menu.add_command(label=f"🔄  {self.t['reset_stats']}", command=lambda: self.reset_tile_stats(index))
        menu.add_separator()
        menu.add_command(label=f"🗑️  {self.t['delete']}", command=lambda: self.delete_tile(index))
        menu.tk_popup(event.x_root, event.y_root)

    def _safe_tile_color(self, color):
        candidate = (color or "").strip() or DEFAULT_TILE_COLOR
        try:
            self.root.winfo_rgb(candidate)
            return candidate
        except tk.TclError:
            return DEFAULT_TILE_COLOR


def main():
    root = tk.Tk()
    app = TileApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
