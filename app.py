import json
import os
import subprocess
import sys
import tkinter as tk
import ctypes
from pathlib import Path
from tkinter import colorchooser, messagebox, ttk
import webbrowser


APP_TITLE = "Kafelki - Ulatwienie Pracy"
APP_CONFIG_DIR_NAME = "Kafelki"
COLUMNS = 4
TILE_WIDTH = 18
TILE_HEIGHT = 4
DEFAULT_CHROME_EXE = Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe")
DEFAULT_TILE_COLOR = "#1f6feb"


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
    },
    {
        "name": "Pulpit",
        "action_type": "path",
        "target": str(Path.home() / "Desktop"),
    },
]


class EditTileDialog(tk.Toplevel):
    def __init__(self, master, tile=None):
        super().__init__(master)
        self.title("Edycja kafelka")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.result = None

        self.var_name = tk.StringVar(value=(tile or {}).get("name", "Nowy kafelek"))
        self.var_action_type = tk.StringVar(value=(tile or {}).get("action_type", "url"))
        self.var_target = tk.StringVar(value=(tile or {}).get("target", ""))
        self.var_color = tk.StringVar(value=(tile or {}).get("color", DEFAULT_TILE_COLOR))

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Return>", lambda _e: self._save())
        self.bind("<Escape>", lambda _e: self._cancel())
        self.wait_visibility()
        self.focus_force()

    def _build_ui(self):
        frame = ttk.Frame(self, padding=12)
        frame.grid(sticky="nsew")

        ttk.Label(frame, text="Nazwa:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(frame, textvariable=self.var_name, width=42).grid(
            row=0, column=1, sticky="ew", pady=(0, 6)
        )

        ttk.Label(frame, text="Typ akcji:").grid(row=1, column=0, sticky="w", pady=(0, 6))
        combo = ttk.Combobox(
            frame,
            textvariable=self.var_action_type,
            values=["url", "path", "exe", "ps1", "python", "chrome_profile", "command"],
            state="readonly",
            width=39,
        )
        combo.grid(row=1, column=1, sticky="ew", pady=(0, 6))

        ttk.Label(frame, text="Cel / komenda:").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.var_target, width=42).grid(row=2, column=1, sticky="ew")

        ttk.Label(frame, text="Kolor kafelka:").grid(row=3, column=0, sticky="w", pady=(6, 0))
        color_row = ttk.Frame(frame)
        color_row.grid(row=3, column=1, sticky="ew", pady=(6, 0))
        ttk.Entry(color_row, textvariable=self.var_color, width=32).pack(side="left")
        ttk.Button(color_row, text="Wybierz...", command=self._pick_color).pack(side="left", padx=(8, 0))

        hint = (
            "url: https://...\n"
            "path: C:\\folder\\...\n"
            "exe: C:\\Program Files\\App\\app.exe\n"
            "ps1: C:\\skrypty\\zadanie.ps1 (tylko sciezka)\n"
            "python: C:\\skrypty\\zadanie.py (tylko sciezka)\n"
            "chrome_profile: C:\\...\\Google\\Chrome\\User Data\\Default\n"
            "command: dowolne polecenie, np. powershell -File C:\\skrypt.ps1"
        )
        ttk.Label(frame, text=hint, foreground="#666666").grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(8, 10)
        )

        buttons = ttk.Frame(frame)
        buttons.grid(row=5, column=0, columnspan=2, sticky="e")
        ttk.Button(buttons, text="Anuluj", command=self._cancel).pack(side="right")
        ttk.Button(buttons, text="Zapisz", command=self._save).pack(side="right", padx=(0, 8))

    def _pick_color(self):
        chosen = colorchooser.askcolor(initialcolor=self.var_color.get(), parent=self)
        if chosen and chosen[1]:
            self.var_color.set(chosen[1])

    def _save(self):
        name = self.var_name.get().strip()
        action_type = self.var_action_type.get().strip()
        target = self.var_target.get().strip()
        color = self.var_color.get().strip() or DEFAULT_TILE_COLOR

        if not name:
            messagebox.showerror("Blad", "Nazwa kafelka nie moze byc pusta.", parent=self)
            return
        if action_type not in {"url", "path", "exe", "ps1", "python", "chrome_profile", "command"}:
            messagebox.showerror("Blad", "Nieprawidlowy typ akcji.", parent=self)
            return
        if not target:
            messagebox.showerror("Blad", "Pole 'Cel / komenda' nie moze byc puste.", parent=self)
            return
        try:
            self.winfo_rgb(color)
        except tk.TclError:
            messagebox.showerror("Blad", "Nieprawidlowy kolor (np. #1f6feb).", parent=self)
            return

        self.result = {
            "name": name,
            "action_type": action_type,
            "target": target,
            "color": color,
        }
        self.destroy()

    def _cancel(self):
        self.result = None
        self.destroy()


class TileApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.minsize(640, 420)
        self.config_file = PRIMARY_CONFIG_FILE

        config = self._load_config()
        self.tiles = config["tiles"]
        self.always_on_top = bool(config["always_on_top"])
        self.var_topmost = tk.BooleanVar(value=self.always_on_top)
        self.root.attributes("-topmost", self.always_on_top)
        self.drag_index = None
        self.drag_start_xy = None
        self.drag_moved = False

        self.main = ttk.Frame(root, padding=12)
        self.main.pack(fill="both", expand=True)

        self.toolbar = ttk.Frame(self.main)
        self.toolbar.pack(fill="x")
        ttk.Button(self.toolbar, text="+ Dodaj kafelek", command=self.add_tile).pack(side="left")
        ttk.Button(self.toolbar, text="Zapisz", command=self.save_tiles).pack(side="left", padx=(8, 0))
        ttk.Checkbutton(
            self.toolbar,
            text="Zawsze na wierzchu",
            variable=self.var_topmost,
            command=self.toggle_always_on_top,
        ).pack(side="left", padx=(12, 0))
        ttk.Label(
            self.toolbar,
            text="LPM: uruchom | PPM: edytuj/usun",
            foreground="#555555",
        ).pack(side="right")

        self.tiles_frame = ttk.Frame(self.main)
        self.tiles_frame.pack(fill="both", expand=True, pady=(12, 0))

        self.render_tiles()

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
                    valid.append(item)
        return valid

    def _parse_config_payload(self, data):
        # Backward compatibility: stary format to sama lista kafelkow.
        if isinstance(data, list):
            tiles = self._validate_tiles(data)
            if tiles:
                return {"always_on_top": False, "tiles": tiles}
            return None

        if isinstance(data, dict):
            tiles = self._validate_tiles(data.get("tiles"))
            always_on_top = bool(data.get("always_on_top", False))
            if tiles:
                return {"always_on_top": always_on_top, "tiles": tiles}
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
            payload = {"always_on_top": False, "tiles": list(DEFAULT_TILES)}
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
            "tiles": self.tiles,
        }

    def save_tiles(self):
        try:
            self._write_config(self._build_config_payload())
            messagebox.showinfo("Zapisano", f"Ustawienia zapisane w:\n{self.config_file}")
        except OSError as exc:
            messagebox.showerror("Blad zapisu", str(exc))

    def toggle_always_on_top(self):
        new_value = bool(self.var_topmost.get())
        self.root.attributes("-topmost", new_value)
        self._autosave()

    def render_tiles(self):
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

    def add_tile(self):
        dialog = EditTileDialog(
            self.root,
            tile={
                "name": "Nowy kafelek",
                "action_type": "url",
                "target": "",
                "color": DEFAULT_TILE_COLOR,
            },
        )
        self.root.wait_window(dialog)
        if dialog.result:
            self.tiles.append(dialog.result)
            self.render_tiles()
            self._autosave()

    def edit_tile(self, index):
        dialog = EditTileDialog(self.root, tile=self.tiles[index])
        self.root.wait_window(dialog)
        if dialog.result:
            self.tiles[index] = dialog.result
            self.render_tiles()
            self._autosave()

    def delete_tile(self, index):
        tile_name = self.tiles[index]["name"]
        if messagebox.askyesno("Usun kafelek", f"Czy na pewno usunac '{tile_name}'?"):
            del self.tiles[index]
            self.render_tiles()
            self._autosave()

    def _autosave(self):
        try:
            self._write_config(self._build_config_payload())
        except OSError:
            pass

    def open_tile_menu(self, event, index):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Edytuj", command=lambda: self.edit_tile(index))
        menu.add_command(label="Usun", command=lambda: self.delete_tile(index))
        menu.tk_popup(event.x_root, event.y_root)

    def _safe_tile_color(self, color):
        candidate = (color or "").strip() or DEFAULT_TILE_COLOR
        try:
            self.root.winfo_rgb(candidate)
            return candidate
        except tk.TclError:
            return DEFAULT_TILE_COLOR

    def on_tile_press(self, event, index):
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
                    raise FileNotFoundError(f"Sciezka nie istnieje:\n{path}")
                os.startfile(path)  # type: ignore[attr-defined]
            elif action_type == "exe":
                exe_path = Path(os.path.expandvars(target)).expanduser()
                if not exe_path.exists():
                    raise FileNotFoundError(f"Plik EXE nie istnieje:\n{exe_path}")
                if exe_path.is_dir():
                    raise IsADirectoryError(f"Podana sciezka jest folderem, nie plikiem EXE:\n{exe_path}")
                subprocess.Popen([str(exe_path)])
            elif action_type == "ps1":
                script_path = Path(os.path.expandvars(target)).expanduser()
                if not script_path.exists():
                    raise FileNotFoundError(f"Skrypt nie istnieje:\n{script_path}")
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
                    raise FileNotFoundError(f"Skrypt nie istnieje:\n{script_path}")
                python_exe = sys.executable if sys.executable else "python"
                subprocess.Popen([python_exe, str(script_path)])
            elif action_type == "chrome_profile":
                profile_path = Path(os.path.expandvars(target)).expanduser()
                if not profile_path.exists():
                    raise FileNotFoundError(f"Profil Chrome nie istnieje:\n{profile_path}")

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
                raise ValueError(f"Nieznany typ akcji: {action_type}")
        except Exception as exc:
            messagebox.showerror("Blad uruchamiania", str(exc))

    def _resolve_chrome_exe(self):
        candidates = [
            DEFAULT_CHROME_EXE,
            Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            Path(os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError(
            "Nie znaleziono chrome.exe.\n"
            "Sprawdz instalacje Google Chrome (standardowa sciezka)."
        )

    def _extract_chrome_profile_parts(self, profile_path):
        profile_name = profile_path.name
        parent_name = profile_path.parent.name.lower()

        # Najczestszy przypadek: ...\\User Data\\Default lub ...\\User Data\\Profile 1
        if parent_name == "user data":
            return profile_path.parent, profile_name

        # Alternatywnie pozwalamy podac samo ...\\User Data (domyslnie Default).
        if profile_name.lower() == "user data":
            return profile_path, "Default"

        raise ValueError(
            "Nieprawidlowa sciezka profilu Chrome.\n"
            "Podaj np.: C:\\Users\\<user>\\AppData\\Local\\Google\\Chrome\\User Data\\Default"
        )

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

            # 1) Dokladne dopasowanie po flagach procesu.
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

            # 2) Fallback dla standardowego profilu Default bez flag:
            # Chrome czesto startuje bez --user-data-dir i --profile-directory.
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

        # Fallback: chwilowe ustawienie TOPMOST zwykle skutecznie wyciaga okno na wierzch.
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
    style = ttk.Style()
    if "vista" in style.theme_names():
        style.theme_use("vista")
    app = TileApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
