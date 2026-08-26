import json
import os
import subprocess
import sys
import tkinter as tk
import ctypes
from pathlib import Path
from tkinter import colorchooser, messagebox, ttk
import webbrowser


APP_CONFIG_DIR_NAME = "Kafelki"
COLUMNS = 4
TILE_WIDTH = 18
TILE_HEIGHT = 4
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

TRANSLATIONS = {
    LANG_EN: {
        "app_title": "Tiles - Work Helper",
        "add_tile": "+ Add Tile",
        "save": "Save",
        "always_on_top": "Always on top",
        "dark_mode": "Dark mode",
        "language": "Language:",
        "hint_mouse": "LMB: run | RMB: edit/delete",
        "edit": "Edit",
        "delete": "Delete",
        "edit_tile_title": "Edit Tile",
        "add_tile_title": "Add Tile",
        "name": "Name:",
        "action_type": "Action type:",
        "target": "Target / command:",
        "color": "Tile color:",
        "description": "Description (optional):",
        "choose_color": "Choose...",
        "cancel": "Cancel",
        "new_tile_default_name": "New Tile",
        "hint_dialog": (
            "url: https://...\n"
            "path: C:\\folder\\...\n"
            "exe: C:\\Program Files\\App\\app.exe\n"
            "ps1: C:\\scripts\\task.ps1 (path only)\n"
            "python: C:\\scripts\\task.py (path only)\n"
            "chrome_profile: C:\\...\\Google\\Chrome\\User Data\\Default\n"
            "command: any command, e.g. powershell -File C:\\script.ps1"
        ),
        "error": "Error",
        "error_name_empty": "Tile name cannot be empty.",
        "error_action_type": "Invalid action type.",
        "error_target_empty": "Field 'Target / command' cannot be empty.",
        "error_color": "Invalid color format (e.g. #1f6feb).",
        "saved_title": "Saved",
        "saved_msg": "Settings saved in:\n{}",
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
            "chrome.exe not found.\n"
            "Check Google Chrome installation (standard path)."
        ),
        "chrome_profile_invalid": (
            "Invalid Chrome profile path.\n"
            "Provide e.g.: C:\\Users\\<user>\\AppData\\Local\\Google\\Chrome\\User Data\\Default"
        ),
        "unknown_action": "Unknown action type: {}",
    },
    LANG_PL: {
        "app_title": "Kafelki - Ułatwienie Pracy",
        "add_tile": "+ Dodaj kafelek",
        "save": "Zapisz",
        "always_on_top": "Zawsze na wierzchu",
        "dark_mode": "Tryb ciemny",
        "language": "Język:",
        "hint_mouse": "LPM: uruchom | PPM: edytuj/usuń",
        "edit": "Edytuj",
        "delete": "Usuń",
        "edit_tile_title": "Edycja kafelka",
        "add_tile_title": "Dodaj kafelek",
        "name": "Nazwa:",
        "action_type": "Typ akcji:",
        "target": "Cel / komenda:",
        "color": "Kolor kafelka:",
        "description": "Opis (opcjonalnie):",
        "choose_color": "Wybierz...",
        "cancel": "Anuluj",
        "new_tile_default_name": "Nowy kafelek",
        "hint_dialog": (
            "url: https://...\n"
            "path: C:\\folder\\...\n"
            "exe: C:\\Program Files\\App\\app.exe\n"
            "ps1: C:\\skrypty\\zadanie.ps1 (tylko sciezka)\n"
            "python: C:\\skrypty\\zadanie.py (tylko sciezka)\n"
            "chrome_profile: C:\\...\\Google\\Chrome\\User Data\\Default\n"
            "command: dowolne polecenie, np. powershell -File C:\\skrypt.ps1"
        ),
        "error": "Błąd",
        "error_name_empty": "Nazwa kafelka nie może być pusta.",
        "error_action_type": "Nieprawidłowy typ akcji.",
        "error_target_empty": "Pole 'Cel / komenda' nie może być puste.",
        "error_color": "Nieprawidłowy kolor (np. #1f6feb).",
        "saved_title": "Zapisano",
        "saved_msg": "Ustawienia zapisane w:\n{}",
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
            "Nie znaleziono chrome.exe.\n"
            "Sprawdź instalację Google Chrome (standardowa ścieżka)."
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
        return Path(appdata) / APP_CONFIG_DIR_NAME / "tiles.json"
    return Path.home() / ".kafelki" / "tiles.json"


def _bundled_seed_config_file():
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass) / "tiles.json"
    return Path(__file__).resolve().with_name("tiles.json")


PRIMARY_CONFIG_FILE = _primary_config_file()
FALLBACK_CONFIG_FILE = _fallback_config_file()
BUNDLED_SEED_CONFIG_FILE = _bundled_seed_config_file()


DEFAULT_TILES = [
    {
        "name": "Google",
        "action_type": "url",
        "target": "https://www.google.com",
        "description": "Google Search Engine",
    },
    {
        "name": "Pulpit",
        "action_type": "path",
        "target": str(Path.home() / "Desktop"),
        "description": "User Desktop Folder",
    },
]


class Tooltip:
    def __init__(self, widget, text, dark_mode=False):
        self.widget = widget
        self.text = text.strip() if text else ""
        self.dark_mode = dark_mode
        self.tip_window = None
        self.after_id = None
        if self.text:
            self.widget.bind("<Enter>", self.schedule, add="+")
            self.widget.bind("<Leave>", self.hide, add="+")
            self.widget.bind("<ButtonPress>", self.hide, add="+")

    def schedule(self, event=None):
        self.unschedule()
        if not self.text:
            return
        self.after_id = self.widget.after(350, self.show)

    def unschedule(self):
        if self.after_id:
            self.widget.after_cancel(self.after_id)
            self.after_id = None

    def show(self, event=None):
        if self.tip_window or not self.text:
            return

        try:
            x = self.widget.winfo_rootx() + 10
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        except tk.TclError:
            return

        screen_width = self.widget.winfo_screenwidth()
        screen_height = self.widget.winfo_screenheight()

        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_attributes("-topmost", True)

        bg_color = "#2b2b2b" if self.dark_mode else "#ffffe1"
        fg_color = "#f0f0f0" if self.dark_mode else "#000000"
        border_color = "#555555" if self.dark_mode else "#b0b0b0"

        frame = tk.Frame(tw, background=border_color, bd=1)
        frame.pack(fill="both", expand=True)

        label = tk.Label(
            frame,
            text=self.text,
            justify="left",
            background=bg_color,
            foreground=fg_color,
            wraplength=260,
            padx=8,
            pady=4,
            font=("Segoe UI", 9),
        )
        label.pack()

        tw.update_idletasks()
        tip_w = tw.winfo_width()
        tip_h = tw.winfo_height()

        if x + tip_w > screen_width - 10:
            x = screen_width - tip_w - 10
        if y + tip_h > screen_height - 10:
            y = self.widget.winfo_rooty() - tip_h - 5

        tw.wm_geometry(f"+{x}+{y}")

    def hide(self, event=None):
        self.unschedule()
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except tk.TclError:
                pass
            self.tip_window = None


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
        self.var_action_type = tk.StringVar(value=(tile or {}).get("action_type", "url"))
        self.var_target = tk.StringVar(value=(tile or {}).get("target", ""))
        self.var_color = tk.StringVar(value=(tile or {}).get("color", DEFAULT_TILE_COLOR))
        self.var_description = tk.StringVar(value=(tile or {}).get("description", ""))

        self._apply_dialog_theme()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Return>", lambda _e: self._save())
        self.bind("<Escape>", lambda _e: self._cancel())
        self.wait_visibility()
        self.focus_force()

    def _apply_dialog_theme(self):
        bg_color = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        self.configure(bg=bg_color)

    def _build_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.grid(sticky="nsew")
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text=self.t["name"]).grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.var_name, width=42).grid(
            row=0, column=1, sticky="ew", pady=(0, 6)
        )

        ttk.Label(frame, text=self.t["action_type"]).grid(row=1, column=0, sticky="w", pady=(0, 6))
        combo = ttk.Combobox(
            frame,
            textvariable=self.var_action_type,
            values=["url", "path", "exe", "ps1", "python", "chrome_profile", "command"],
            state="readonly",
            width=39,
        )
        combo.grid(row=1, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(frame, text=self.t["target"]).grid(row=2, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.var_target, width=42).grid(row=2, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(frame, text=self.t["color"]).grid(row=3, column=0, sticky="w", pady=(0, 6))
        color_row = ttk.Frame(frame)
        color_row.grid(row=3, column=1, sticky="ew", pady=(0, 6))
        ttk.Entry(color_row, textvariable=self.var_color, width=32).pack(side="left")
        ttk.Button(color_row, text=self.t["choose_color"], command=self._pick_color).pack(side="left", padx=(8, 0))

        ttk.Label(frame, text=self.t["description"]).grid(row=4, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.var_description, width=42).grid(
            row=4, column=1, sticky="ew", pady=(0, 6)
        )

        hint_fg = "#aaaaaa" if self.dark_mode else "#666666"
        ttk.Label(frame, text=self.t["hint_dialog"], foreground=hint_fg).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(8, 10)
        )

        buttons = ttk.Frame(frame)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e")
        ttk.Button(buttons, text=self.t["cancel"], command=self._cancel).pack(side="right")
        ttk.Button(buttons, text=self.t["save"], command=self._save).pack(side="right", padx=(0, 8))

    def _pick_color(self):
        chosen = colorchooser.askcolor(initialcolor=self.var_color.get(), parent=self)
        if chosen and chosen[1]:
            self.var_color.set(chosen[1])

    def _save(self):
        name = self.var_name.get().strip()
        action_type = self.var_action_type.get().strip()
        target = self.var_target.get().strip()
        color = self.var_color.get().strip() or DEFAULT_TILE_COLOR
        description = self.var_description.get().strip()

        if not name:
            messagebox.showerror(self.t["error"], self.t["error_name_empty"], parent=self)
            return
        if action_type not in {"url", "path", "exe", "ps1", "python", "chrome_profile", "command"}:
            messagebox.showerror(self.t["error"], self.t["error_action_type"], parent=self)
            return
        if not target:
            messagebox.showerror(self.t["error"], self.t["error_target_empty"], parent=self)
            return
        try:
            self.winfo_rgb(color)
        except tk.TclError:
            messagebox.showerror(self.t["error"], self.t["error_color"], parent=self)
            return

        self.result = {
            "name": name,
            "action_type": action_type,
            "target": target,
            "color": color,
            "description": description,
        }
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class TileApp:
    def __init__(self, root):
        self.root = root
        self.config_file = PRIMARY_CONFIG_FILE
        self.tooltips = []

        config = self._load_config()
        self.tiles = config["tiles"]
        self.always_on_top = bool(config["always_on_top"])
        self.dark_mode = bool(config.get("dark_mode", False))
        self.lang = config.get("language", LANG_EN)
        if self.lang not in (LANG_EN, LANG_PL):
            self.lang = LANG_EN

        self.var_topmost = tk.BooleanVar(value=self.always_on_top)
        self.var_dark_mode = tk.BooleanVar(value=self.dark_mode)
        self.var_language = tk.StringVar(value=LANG_NAMES.get(self.lang, "English"))

        self.root.attributes("-topmost", self.always_on_top)
        self.root.minsize(720, 440)

        self.drag_index = None
        self.drag_start_xy = None
        self.drag_moved = False

        self.main = ttk.Frame(root, padding=12)
        self.main.pack(fill="both", expand=True)

        self.toolbar = ttk.Frame(self.main)
        self.toolbar.pack(fill="x")

        self.btn_add_tile = ttk.Button(self.toolbar, command=self.add_tile)
        self.btn_add_tile.pack(side="left")

        self.btn_save = ttk.Button(self.toolbar, command=self.save_tiles)
        self.btn_save.pack(side="left", padx=(8, 0))

        self.chk_topmost = ttk.Checkbutton(
            self.toolbar,
            variable=self.var_topmost,
            command=self.toggle_always_on_top,
        )
        self.chk_topmost.pack(side="left", padx=(12, 0))

        self.chk_dark = ttk.Checkbutton(
            self.toolbar,
            variable=self.var_dark_mode,
            command=self.toggle_dark_mode,
        )
        self.chk_dark.pack(side="left", padx=(12, 0))

        self.lbl_lang = ttk.Label(self.toolbar)
        self.lbl_lang.pack(side="left", padx=(12, 4))

        self.combo_lang = ttk.Combobox(
            self.toolbar,
            textvariable=self.var_language,
            values=["English", "Polski"],
            state="readonly",
            width=8,
        )
        self.combo_lang.pack(side="left")
        self.combo_lang.bind("<<ComboboxSelected>>", self.on_language_change)

        self.lbl_hint = ttk.Label(self.toolbar)
        self.lbl_hint.pack(side="right")

        self.tiles_frame = ttk.Frame(self.main)
        self.tiles_frame.pack(fill="both", expand=True, pady=(12, 0))

        self.apply_theme()
        self.update_ui_language()
        self.render_tiles()

    @property
    def t(self):
        return TRANSLATIONS.get(self.lang, TRANSLATIONS[LANG_EN])

    def update_ui_language(self):
        self.root.title(self.t["app_title"])
        self.btn_add_tile.config(text=self.t["add_tile"])
        self.btn_save.config(text=self.t["save"])
        self.chk_topmost.config(text=self.t["always_on_top"])
        self.chk_dark.config(text=self.t["dark_mode"])
        self.lbl_lang.config(text=self.t["language"])
        self.lbl_hint.config(text=self.t["hint_mouse"])

    def on_language_change(self, event=None):
        chosen = self.var_language.get()
        self.lang = LANG_CODES.get(chosen, LANG_EN)
        self.update_ui_language()
        self.render_tiles()
        self._autosave()

    def toggle_dark_mode(self):
        self.apply_theme()
        self.render_tiles()
        self._autosave()

    def apply_theme(self):
        self.dark_mode = bool(self.var_dark_mode.get())
        style = ttk.Style(self.root)

        bg = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        fg = "#ffffff" if self.dark_mode else "#000000"
        entry_bg = "#2d2d2d" if self.dark_mode else "#ffffff"
        btn_bg = "#3c3c3c" if self.dark_mode else "#e1e1e1"
        btn_active = "#505050" if self.dark_mode else "#ececec"
        hint_fg = "#aaaaaa" if self.dark_mode else "#555555"

        self.root.configure(bg=bg)

        if self.dark_mode:
            style.theme_use("default")
            style.configure(".", background=bg, foreground=fg)
            style.configure("TFrame", background=bg)
            style.configure("TLabel", background=bg, foreground=fg)
            style.configure("TCheckbutton", background=bg, foreground=fg)
            style.configure("TButton", background=btn_bg, foreground=fg, borderwidth=1)
            style.map("TButton", background=[("active", btn_active)])
            style.configure("TCombobox", fieldbackground=entry_bg, background=btn_bg, foreground=fg, arrowcolor=fg)
            style.map("TCombobox", fieldbackground=[("readonly", entry_bg)], foreground=[("readonly", fg)])
            style.configure("TEntry", fieldbackground=entry_bg, foreground=fg)
        else:
            if "vista" in style.theme_names():
                style.theme_use("vista")
            else:
                style.theme_use("default")
            style.configure(".", background="#f0f0f0", foreground="#000000")
            style.configure("TFrame", background="#f0f0f0")
            style.configure("TLabel", background="#f0f0f0", foreground="#000000")
            style.configure("TCheckbutton", background="#f0f0f0", foreground="#000000")
            style.configure("TButton", background="#e1e1e1", foreground="#000000")
            style.map("TButton", background=[("active", "#ececec")])
            style.configure("TCombobox", fieldbackground="#ffffff", background="#e1e1e1", foreground="#000000")
            style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", "#000000")])
            style.configure("TEntry", fieldbackground="#ffffff", foreground="#000000")

        self.lbl_hint.configure(foreground=hint_fg)

    def _validate_tiles(self, data):
        valid = []
        if isinstance(data, list):
            for item in data:
                if (
                    isinstance(item, dict)
                    and isinstance(item.get("name"), str)
                    and isinstance(item.get("action_type"), str)
                    and isinstance(item.get("target"), str)
                ):
                    tile = {
                        "name": item["name"],
                        "action_type": item["action_type"],
                        "target": item["target"],
                        "color": item.get("color", DEFAULT_TILE_COLOR),
                        "description": item.get("description", "")
                        if isinstance(item.get("description"), str)
                        else "",
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
                    "language": LANG_EN,
                    "tiles": tiles,
                }
            return None

        if isinstance(data, dict):
            tiles = self._validate_tiles(data.get("tiles"))
            always_on_top = bool(data.get("always_on_top", False))
            dark_mode = bool(data.get("dark_mode", False))
            language = str(data.get("language", LANG_EN))
            if language not in (LANG_EN, LANG_PL):
                language = LANG_EN
            if tiles is not None:
                return {
                    "always_on_top": always_on_top,
                    "dark_mode": dark_mode,
                    "language": language,
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
                "language": LANG_EN,
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
            "language": self.lang,
            "tiles": self.tiles,
        }

    def save_tiles(self):
        try:
            self._write_config(self._build_config_payload())
            messagebox.showinfo(
                self.t["saved_title"],
                self.t["saved_msg"].format(self.config_file),
                parent=self.root,
            )
        except OSError as exc:
            messagebox.showerror(self.t["save_error_title"], str(exc), parent=self.root)

    def toggle_always_on_top(self):
        new_value = bool(self.var_topmost.get())
        self.root.attributes("-topmost", new_value)
        self._autosave()

    def _hide_all_tooltips(self):
        for tt in getattr(self, "tooltips", []):
            tt.hide()

    def render_tiles(self):
        self._hide_all_tooltips()
        self.tooltips = []

        for child in self.tiles_frame.winfo_children():
            child.destroy()

        for i in range(COLUMNS):
            self.tiles_frame.columnconfigure(i, weight=1, uniform="col")

        for index, tile in enumerate(self.tiles):
            row = index // COLUMNS
            col = index % COLUMNS

            btn = tk.Button(
                self.tiles_frame,
                text=tile["name"],
                width=TILE_WIDTH,
                height=TILE_HEIGHT,
                bg=self._safe_tile_color(tile.get("color", DEFAULT_TILE_COLOR)),
                fg="white",
                activebackground="#2a7fff",
                activeforeground="white",
                relief="raised",
                wraplength=140,
            )
            btn.tile_index = index
            btn.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")
            btn.bind("<Button-3>", lambda e, i=index: self.open_tile_menu(e, i))
            btn.bind("<ButtonPress-1>", lambda e, i=index: self.on_tile_press(e, i))
            btn.bind("<B1-Motion>", self.on_tile_motion)
            btn.bind("<ButtonRelease-1>", self.on_tile_release)

            desc = tile.get("description", "")
            if desc:
                tt = Tooltip(btn, desc, dark_mode=self.dark_mode)
                self.tooltips.append(tt)

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
            },
            lang=self.lang,
            dark_mode=self.dark_mode,
        )
        self.root.wait_window(dialog)
        if dialog.result:
            self.tiles.append(dialog.result)
            self.render_tiles()
            self._autosave()

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
            self.tiles[index] = dialog.result
            self.render_tiles()
            self._autosave()

    def delete_tile(self, index):
        self._hide_all_tooltips()
        tile_name = self.tiles[index]["name"]
        if messagebox.askyesno(
            self.t["delete_title"],
            self.t["delete_confirm"].format(tile_name),
            parent=self.root,
        ):
            del self.tiles[index]
            self.render_tiles()
            self._autosave()

    def _autosave(self):
        try:
            self._write_config(self._build_config_payload())
        except OSError:
            pass

    def open_tile_menu(self, event, index):
        self._hide_all_tooltips()
        bg = "#2d2d2d" if self.dark_mode else "#ffffff"
        fg = "#ffffff" if self.dark_mode else "#000000"
        active_bg = "#3e3e42" if self.dark_mode else "#e5e5e5"
        active_fg = "#ffffff" if self.dark_mode else "#000000"

        menu = tk.Menu(
            self.root,
            tearoff=0,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground=active_fg,
        )
        menu.add_command(label=self.t["edit"], command=lambda: self.edit_tile(index))
        menu.add_command(label=self.t["delete"], command=lambda: self.delete_tile(index))
        menu.tk_popup(event.x_root, event.y_root)

    def _safe_tile_color(self, color):
        candidate = (color or "").strip() or DEFAULT_TILE_COLOR
        try:
            self.root.winfo_rgb(candidate)
            return candidate
        except tk.TclError:
            return DEFAULT_TILE_COLOR

    def on_tile_press(self, event, index):
        self._hide_all_tooltips()
        self.drag_index = index
        self.drag_start_xy = (event.x_root, event.y_root)
        self.drag_moved = False

    def on_tile_motion(self, event):
        if self.drag_index is None or self.drag_start_xy is None:
            return
        dx = abs(event.x_root - self.drag_start_xy[0])
        dy = abs(event.y_root - self.drag_start_xy[1])
        if dx > 8 or dy > 8:
            self.drag_moved = True

    def on_tile_release(self, event):
        if self.drag_index is None:
            return

        source_index = self.drag_index
        moved = self.drag_moved

        self.drag_index = None
        self.drag_start_xy = None
        self.drag_moved = False

        if not moved:
            self.run_tile(source_index)
            return

        target_widget = self.root.winfo_containing(event.x_root, event.y_root)
        target_index = getattr(target_widget, "tile_index", None)
        if target_index is None or target_index == source_index:
            return

        self.reorder_tiles(source_index, target_index)

    def reorder_tiles(self, source_index, target_index):
        tile = self.tiles.pop(source_index)
        if source_index < target_index:
            target_index -= 1
        self.tiles.insert(target_index, tile)
        self.render_tiles()
        self._autosave()

    def run_tile(self, index):
        tile = self.tiles[index]
        action_type = tile["action_type"].strip().lower()
        target = tile["target"].strip()

        try:
            if action_type == "url":
                if not target.startswith(("http://", "https://")):
                    target = "https://" + target
                webbrowser.open(target, new=2)
            elif action_type == "path":
                path = Path(os.path.expandvars(target)).expanduser()
                if not path.exists():
                    raise FileNotFoundError(self.t["path_not_found"].format(path))
                os.startfile(path)  # type: ignore[attr-defined]
            elif action_type == "exe":
                exe_path = Path(os.path.expandvars(target)).expanduser()
                if not exe_path.exists():
                    raise FileNotFoundError(self.t["exe_not_found"].format(exe_path))
                if exe_path.is_dir():
                    raise IsADirectoryError(self.t["path_is_dir"].format(exe_path))
                subprocess.Popen([str(exe_path)])
            elif action_type == "ps1":
                script_path = Path(os.path.expandvars(target)).expanduser()
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
                script_path = Path(os.path.expandvars(target)).expanduser()
                if not script_path.exists():
                    raise FileNotFoundError(self.t["script_not_found"].format(script_path))
                python_exe = sys.executable if sys.executable else "python"
                subprocess.Popen([python_exe, str(script_path)])
            elif action_type == "chrome_profile":
                profile_path = Path(os.path.expandvars(target)).expanduser()
                if not profile_path.exists():
                    raise FileNotFoundError(self.t["chrome_profile_not_found"].format(profile_path))

                chrome_exe = self._resolve_chrome_exe()
                user_data_dir, profile_dir = self._extract_chrome_profile_parts(profile_path)
                running_pid = self._find_running_chrome_profile(user_data_dir, profile_dir)
                if running_pid and self._focus_window_by_pid(running_pid):
                    return
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


def main():
    root = tk.Tk()
    app = TileApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
