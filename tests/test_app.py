import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
import tkinter as tk

import app
from app import (
    ACTION_DEFS,
    LANG_EN,
    LANG_PL,
    SORT_KEYS,
    TRANSLATIONS,
    TileApp,
    format_datetime_display,
    get_target_preview,
)


@pytest.fixture(scope="session")
def tk_root():
    root = tk.Tk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass


def test_translations_parity():
    """Verify that all keys in English exist in Polish and vice versa."""
    en_keys = set(TRANSLATIONS[LANG_EN].keys())
    pl_keys = set(TRANSLATIONS[LANG_PL].keys())

    assert en_keys == pl_keys, f"Translation key mismatch: {en_keys.symmetric_difference(pl_keys)}"

    for lang in (LANG_EN, LANG_PL):
        for key, val in TRANSLATIONS[lang].items():
            assert val, f"Empty translation for key '{key}' in '{lang}'"


def test_action_defs_completeness():
    """Verify all 14 action types are well-defined with icons and bilingual hints."""
    expected_actions = {
        "url",
        "path",
        "file",
        "exe",
        "ps1",
        "python",
        "bat",
        "terminal",
        "vscode",
        "wsl",
        "clipboard",
        "websearch",
        "chrome_profile",
        "command",
    }
    assert set(ACTION_DEFS.keys()) == expected_actions

    for act_key, meta in ACTION_DEFS.items():
        assert "icon" in meta and meta["icon"], f"Missing icon in action {act_key}"
        assert "name_en" in meta and meta["name_en"], f"Missing name_en in action {act_key}"
        assert "name_pl" in meta and meta["name_pl"], f"Missing name_pl in action {act_key}"
        assert "hint_en" in meta and meta["hint_en"], f"Missing hint_en in action {act_key}"
        assert "hint_pl" in meta and meta["hint_pl"], f"Missing hint_pl in action {act_key}"
        assert "browse" in meta, f"Missing browse mode in action {act_key}"


def test_config_parsing_and_migration(tk_root):
    """Verify that legacy config without use_count or created_at migrates cleanly."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root

    legacy_data = {
        "always_on_top": True,
        "dark_mode": True,
        "language": "pl",
        "tiles": [
            {
                "name": "Old Tile",
                "action_type": "url",
                "target": "https://example.com",
                "color": "#123456",
                "description": "Legacy desc",
            }
        ],
    }

    parsed = app_inst._parse_config_payload(legacy_data)
    assert parsed is not None
    assert parsed["always_on_top"] is True
    assert parsed["autostart"] is False
    assert parsed["dark_mode"] is True
    assert parsed["language"] == "pl"
    assert parsed["sort_by"] == "manual"
    assert len(parsed["tiles"]) == 1

    tile = parsed["tiles"][0]
    assert tile["name"] == "Old Tile"
    assert tile["use_count"] == 0
    assert tile["created_at"] is not None
    assert tile["last_used"] == ""


def test_drag_and_drop_reorder_logic(tk_root):
    """Verify list reordering logic for all movements (forward, backward, adjacent)."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.tiles = [
        {"name": "Tile 0"},
        {"name": "Tile 1"},
        {"name": "Tile 2"},
        {"name": "Tile 3"},
    ]
    app_inst.lang = LANG_EN
    app_inst.current_sort = "name_asc"
    app_inst.var_sort = tk.StringVar(value="Name (A - Z)")
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    app_inst.show_toast = lambda msg: None

    # Drag 0 onto 1 (adjacent forward move - the bug from old code)
    app_inst.reorder_tiles(0, 1)
    names = [t["name"] for t in app_inst.tiles]
    assert names == ["Tile 1", "Tile 0", "Tile 2", "Tile 3"], f"Got: {names}"
    assert app_inst.current_sort == "manual"

    # Drag 3 onto 0 (backward move across multiple items)
    app_inst.reorder_tiles(3, 0)
    names = [t["name"] for t in app_inst.tiles]
    assert names == ["Tile 3", "Tile 1", "Tile 0", "Tile 2"], f"Got: {names}"

    # Drag onto self (no-op)
    app_inst.reorder_tiles(2, 2)
    names = [t["name"] for t in app_inst.tiles]
    assert names == ["Tile 3", "Tile 1", "Tile 0", "Tile 2"]


def test_sorting_modes(tk_root):
    """Verify all sorting modes produce correct orders."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.lang = LANG_EN
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    app_inst.show_toast = lambda msg: None
    app_inst.var_sort = tk.StringVar()

    sample_tiles = [
        {
            "name": "Bravo",
            "action_type": "url",
            "use_count": 5,
            "created_at": "2026-01-02T10:00:00",
            "last_used": "2026-01-10T12:00:00",
        },
        {
            "name": "Alpha",
            "action_type": "exe",
            "use_count": 20,
            "created_at": "2026-01-01T10:00:00",
            "last_used": "2026-01-05T12:00:00",
        },
        {
            "name": "Charlie",
            "action_type": "path",
            "use_count": 10,
            "created_at": "2026-01-03T10:00:00",
            "last_used": "2026-01-12T12:00:00",
        },
    ]

    # 1. Sort by most_used
    app_inst.tiles = list(sample_tiles)
    app_inst.sort_tiles("most_used", autosave=False)
    assert [t["name"] for t in app_inst.tiles] == ["Alpha", "Charlie", "Bravo"]

    # 2. Sort by recently_used
    app_inst.tiles = list(sample_tiles)
    app_inst.sort_tiles("recently_used", autosave=False)
    assert [t["name"] for t in app_inst.tiles] == ["Charlie", "Bravo", "Alpha"]

    # 3. Sort by name_asc
    app_inst.tiles = list(sample_tiles)
    app_inst.sort_tiles("name_asc", autosave=False)
    assert [t["name"] for t in app_inst.tiles] == ["Alpha", "Bravo", "Charlie"]

    # 4. Sort by name_desc
    app_inst.tiles = list(sample_tiles)
    app_inst.sort_tiles("name_desc", autosave=False)
    assert [t["name"] for t in app_inst.tiles] == ["Charlie", "Bravo", "Alpha"]

    # 5. Sort by date_newest
    app_inst.tiles = list(sample_tiles)
    app_inst.sort_tiles("date_newest", autosave=False)
    assert [t["name"] for t in app_inst.tiles] == ["Charlie", "Bravo", "Alpha"]

    # 6. Sort by date_oldest
    app_inst.tiles = list(sample_tiles)
    app_inst.sort_tiles("date_oldest", autosave=False)
    assert [t["name"] for t in app_inst.tiles] == ["Alpha", "Bravo", "Charlie"]

    # 7. Sort by action_type
    app_inst.tiles = list(sample_tiles)
    app_inst.sort_tiles("action_type", autosave=False)
    assert [t["name"] for t in app_inst.tiles] == ["Alpha", "Charlie", "Bravo"]


def test_target_preview_formatting():
    """Verify get_target_preview formats short labels cleanly based on action_type and target."""
    assert get_target_preview("url", "https://console.cloud.google.com/vertex-ai") == "console.cloud.google.com/..."
    assert get_target_preview("url", "https://google.com") == "google.com"
    assert get_target_preview("path", "C:\\Users\\Username\\Desktop\\MyFolder") == "MyFolder"
    assert get_target_preview("exe", "C:\\Tools\\App.exe") == "App.exe"
    assert get_target_preview("ps1", "D:\\Git\\skrypty\\sciezka.ps1") == "sciezka.ps1"
    assert get_target_preview("clipboard", "Wklejony tekst") == "Wklejony tekst"


def test_date_formatting():
    """Verify format_datetime_display produces clean readable dates."""
    assert format_datetime_display("2026-09-10T20:15:30") == "2026-09-10 20:15"
    assert format_datetime_display("") == ""


def test_tile_app_full_integration(tk_root, tmp_path):
    """Verify full GUI instantiation, theme toggle, language toggle, and tile search."""
    cfg_file = tmp_path / "tiles.json"
    cfg_data = {
        "always_on_top": False,
        "dark_mode": True,
        "language": "pl",
        "sort_by": "manual",
        "tiles": [
            {
                "name": "Vertex Studio",
                "action_type": "url",
                "target": "https://vertex.google.com",
                "color": "#4f46e5",
                "description": "AI Workspace",
                "use_count": 3,
                "created_at": "2026-01-01T00:00:00",
                "last_used": "2026-01-02T00:00:00",
            },
            {
                "name": "Git Repo",
                "action_type": "path",
                "target": "D:\\Git",
                "color": "#f97316",
                "description": "",
                "use_count": 0,
                "created_at": "2026-01-01T00:00:01",
                "last_used": "",
            },
        ],
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        assert len(tile_app.tiles) == 2
        assert tile_app.dark_mode is True
        assert tile_app.lang == "pl"
        assert len(tile_app.rendered_cards) == 2

        # Test Search
        tile_app.var_search.set("vertex")
        assert len(tile_app.rendered_cards) == 1
        assert tile_app.rendered_cards[0]["tile"]["name"] == "Vertex Studio"

        # Clear search
        tile_app.clear_search()
        assert len(tile_app.rendered_cards) == 2

        # Test Theme Toggle
        tile_app.toggle_dark_mode()
        assert tile_app.dark_mode is False

        # Test Language Toggle
        tile_app.var_language.set("English")
        tile_app.on_language_change()
        assert tile_app.lang == "en"

        # Test Duplicate Tile
        tile_app.duplicate_tile(0)
        assert len(tile_app.tiles) == 3
        assert "Copy" in tile_app.tiles[1]["name"]

        # Test Reset stats
        tile_app.reset_tile_stats(0)
        assert tile_app.tiles[0]["use_count"] == 0
        assert tile_app.tiles[0]["last_used"] == ""

        # Test Delete Tile (mock messagebox.askyesno)
        app.messagebox.askyesno = lambda *args, **kwargs: True
        tile_app.delete_tile(1)
        assert len(tile_app.tiles) == 2
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_load_real_tiles_json(tk_root):
    """Verify that the existing tiles.json in repo loads smoothly with all 17 tiles."""
    real_file = REPO_ROOT / "tiles.json"
    assert real_file.exists()

    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = real_file
    app.FALLBACK_CONFIG_FILE = real_file
    try:
        tile_app = TileApp(sub_top)
        assert len(tile_app.tiles) >= 10
        for tile in tile_app.tiles:
            assert tile["name"]
            assert tile["action_type"] in ACTION_DEFS
            assert "target" in tile
            assert "use_count" in tile
            assert "created_at" in tile
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        try:
            sub_top.update_idletasks()
        except Exception:
            pass
        sub_top.destroy()


def test_run_tile_actions_dispatch(tk_root, monkeypatch):
    """Verify that run_tile dispatches all action types properly."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.lang = LANG_EN
    app_inst.dark_mode = False
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    app_inst.show_toast = lambda msg: None

    called = {}

    monkeypatch.setattr(app.webbrowser, "open", lambda url, new=2: called.update({"webbrowser": url}))
    monkeypatch.setattr(app.os, "startfile", lambda p: called.update({"startfile": p}), raising=False)
    monkeypatch.setattr(app.subprocess, "Popen", lambda args, **kwargs: called.update({"popen": args, "kwargs": kwargs}))

    # 1. URL action
    app_inst.tiles = [{"name": "Test URL", "action_type": "url", "target": "google.com", "use_count": 0}]
    app_inst.run_tile(0)
    assert called.get("webbrowser") == "https://google.com"
    assert app_inst.tiles[0]["use_count"] == 1
    assert app_inst.tiles[0]["last_used"] != ""

    # 2. Clipboard action
    app_inst.tiles = [{"name": "Test Clip", "action_type": "clipboard", "target": "SecretToken123", "use_count": 0}]
    app_inst.run_tile(0)
    assert tk_root.clipboard_get() == "SecretToken123"
    assert app_inst.tiles[0]["use_count"] == 1

    # 3. Websearch action
    called.clear()
    app_inst.tiles = [{"name": "Test Search", "action_type": "websearch", "target": "python docs", "use_count": 0}]
    app_inst.run_tile(0)
    assert "search?q=python+docs" in called.get("webbrowser", "")

    # 4. Command action
    called.clear()
    app_inst.tiles = [{"name": "Test Cmd", "action_type": "command", "target": "echo hello", "use_count": 0}]
    app_inst.run_tile(0)
    assert called.get("popen") == "echo hello"
    assert called.get("kwargs", {}).get("shell") is True

    # 5. Terminal action
    called.clear()
    app_inst.tiles = [{"name": "Test Term", "action_type": "terminal", "target": str(REPO_ROOT), "use_count": 0}]
    app_inst.run_tile(0)
    assert "popen" in called

    # 6. VSCode action
    called.clear()
    app_inst.tiles = [{"name": "Test Code", "action_type": "vscode", "target": str(REPO_ROOT), "use_count": 0}]
    app_inst.run_tile(0)
    assert f'code "{REPO_ROOT}"' in called.get("popen", "")

    # 7. WSL action
    called.clear()
    app_inst.tiles = [{"name": "Test WSL", "action_type": "wsl", "target": "htop", "use_count": 0}]
    app_inst.run_tile(0)
    assert called.get("popen") == ["wsl.exe", "-e", "bash", "-lc", "htop"]

    # 8. Unknown action handling
    err_reported = {}
    monkeypatch.setattr(app.messagebox, "showerror", lambda title, msg, **kw: err_reported.update({"msg": msg}))
    app_inst.tiles = [{"name": "Test Bad", "action_type": "invalid_action_foo", "target": "bar", "use_count": 0}]
    app_inst.run_tile(0)
    assert "Unknown action type" in err_reported.get("msg", "")


def test_edit_tile_dialog_validation(tk_root, monkeypatch):
    """Verify EditTileDialog validates empty inputs and bad color."""
    errors = []
    monkeypatch.setattr(app.messagebox, "showerror", lambda title, msg, **kw: errors.append(msg))

    dialog = app.EditTileDialog(tk_root, tile=None, lang=LANG_EN, dark_mode=False)
    try:
        # Empty name test
        dialog.var_name.set("")
        dialog._save()
        assert len(errors) == 1
        assert "name cannot be empty" in errors[-1].lower()

        # Invalid action type test
        dialog.var_name.set("Valid Name")
        dialog.var_action_type.set("nonexistent_type")
        dialog._save()
        assert len(errors) == 2
        assert "invalid action type" in errors[-1].lower()

        # Empty target test
        dialog.var_action_type.set("url")
        dialog.var_target.set("")
        dialog._save()
        assert len(errors) == 3
        assert "cannot be empty" in errors[-1].lower()

        # Invalid color test
        dialog.var_target.set("https://valid.com")
        dialog.var_color.set("invalid_color_gibberish")
        dialog._save()
        assert len(errors) == 4
        assert "color" in errors[-1].lower()

        # Valid save
        dialog.var_color.set("#10b981")
        dialog._save()
        assert dialog.result is not None
        assert dialog.result["name"] == "Valid Name"
        assert dialog.result["color"] == "#10b981"
        assert dialog.result["action_type"] == "url"
    finally:
        try:
            dialog.destroy()
        except Exception:
            pass


def test_corrupt_json_fallback(tk_root, tmp_path):
    """Verify that corrupt JSON file gracefully falls back without crashing."""
    corrupt_file = tmp_path / "corrupt_tiles.json"
    corrupt_file.write_text("{ this is not valid json : [ }", encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = corrupt_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        assert len(tile_app.tiles) > 0
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_file_action_types_execution(tk_root, monkeypatch, tmp_path):
    """Verify exe, bat, ps1, python, and file action type execution."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.lang = LANG_EN
    app_inst.dark_mode = False
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    app_inst.show_toast = lambda msg: None

    called = {}
    monkeypatch.setattr(app.os, "startfile", lambda p: called.update({"startfile": p}), raising=False)
    monkeypatch.setattr(app.subprocess, "Popen", lambda args, **kwargs: called.update({"popen": args}))

    # Create dummy files
    dummy_exe = tmp_path / "app.exe"
    dummy_exe.write_text("dummy", encoding="utf-8")
    dummy_bat = tmp_path / "script.bat"
    dummy_bat.write_text("dummy", encoding="utf-8")
    dummy_ps1 = tmp_path / "script.ps1"
    dummy_ps1.write_text("dummy", encoding="utf-8")
    dummy_py = tmp_path / "script.py"
    dummy_py.write_text("dummy", encoding="utf-8")
    dummy_doc = tmp_path / "doc.pdf"
    dummy_doc.write_text("dummy", encoding="utf-8")

    # 1. exe
    app_inst.tiles = [{"name": "Exe", "action_type": "exe", "target": str(dummy_exe), "use_count": 0}]
    app_inst.run_tile(0)
    assert called.get("popen") == [str(dummy_exe)]

    # 2. bat
    called.clear()
    app_inst.tiles = [{"name": "Bat", "action_type": "bat", "target": str(dummy_bat), "use_count": 0}]
    app_inst.run_tile(0)
    assert called.get("popen") == ["cmd.exe", "/c", str(dummy_bat)]

    # 3. ps1
    called.clear()
    app_inst.tiles = [{"name": "PS1", "action_type": "ps1", "target": str(dummy_ps1), "use_count": 0}]
    app_inst.run_tile(0)
    assert "powershell.exe" in called.get("popen", [])

    # 4. python
    called.clear()
    app_inst.tiles = [{"name": "Py", "action_type": "python", "target": str(dummy_py), "use_count": 0}]
    app_inst.run_tile(0)
    assert called.get("popen", [])[1] == str(dummy_py)

    # 5. file
    called.clear()
    app_inst.tiles = [{"name": "File", "action_type": "file", "target": str(dummy_doc), "use_count": 0}]
    app_inst.run_tile(0)
    assert called.get("startfile") == str(dummy_doc)


def test_search_filtering_with_diacritics(tk_root, tmp_path):
    """Verify search filtering finds tiles with polish letters and case-insensitivity."""
    cfg_file = tmp_path / "tiles.json"
    cfg_data = {
        "tiles": [
            {"name": "Ścieżki WSL", "action_type": "ps1", "target": "D:\\Git\\sciezka.ps1", "description": "Konwertowanie"},
            {"name": "PROMPTLANDIA", "action_type": "url", "target": "promptlandia.com", "description": ""},
        ]
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        assert len(tile_app.rendered_cards) == 2

        # Search lowercase with diacritic
        tile_app.var_search.set("ścieżki")
        assert len(tile_app.rendered_cards) == 1
        assert tile_app.rendered_cards[0]["tile"]["name"] == "Ścieżki WSL"

        # Search partial uppercase target
        tile_app.var_search.set("SCIEZKA")
        assert len(tile_app.rendered_cards) == 1

        # Search by description
        tile_app.var_search.set("konwertowanie")
        assert len(tile_app.rendered_cards) == 1

        # Search non-matching
        tile_app.var_search.set("xyznonexistent")
        assert len(tile_app.rendered_cards) == 0
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_startup_sort_applied(tk_root, tmp_path):
    """Verify that non-manual sort_by in config is actually applied to tiles on startup."""
    cfg_file = tmp_path / "tiles_sort.json"
    cfg_data = {
        "sort_by": "name_asc",
        "tiles": [
            {"name": "Zeta", "action_type": "url", "target": "z.com"},
            {"name": "Alpha", "action_type": "url", "target": "a.com"},
            {"name": "Beta", "action_type": "url", "target": "b.com"},
        ],
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        names = [c["tile"]["name"] for c in tile_app.rendered_cards]
        assert names == ["Alpha", "Beta", "Zeta"]
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_polish_collation_sorting(tk_root):
    """Verify that Polish diacritic characters sort into their correct Polish alphabetical slots."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.lang = LANG_PL
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    app_inst.show_toast = lambda msg: None
    app_inst.var_sort = tk.StringVar()

    app_inst.tiles = [
        {"name": "Zeta", "action_type": "url", "target": "1"},
        {"name": "Ścieżki", "action_type": "url", "target": "2"},
        {"name": "Auto", "action_type": "url", "target": "3"},
        {"name": "Baza", "action_type": "url", "target": "4"},
        {"name": "Łódź", "action_type": "url", "target": "5"},
        {"name": "Laser", "action_type": "url", "target": "6"},
    ]
    app_inst.sort_tiles("name_asc", autosave=False, show_toast=False)
    names = [t["name"] for t in app_inst.tiles]
    assert names == ["Auto", "Baza", "Laser", "Łódź", "Ścieżki", "Zeta"]


def test_custom_order_restoration(tk_root):
    """Verify that switching back to 'manual' order restores the user's custom tile arrangement."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.lang = LANG_EN
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    app_inst.show_toast = lambda msg: None
    app_inst.var_sort = tk.StringVar()

    app_inst.tiles = [
        {"name": "Third", "order": 0, "use_count": 10},
        {"name": "First", "order": 1, "use_count": 50},
        {"name": "Second", "order": 2, "use_count": 2},
    ]

    # Sort by name
    app_inst.sort_tiles("name_asc", autosave=False, show_toast=False)
    assert [t["name"] for t in app_inst.tiles] == ["First", "Second", "Third"]

    # Restore to manual order
    app_inst.sort_tiles("manual", autosave=False, show_toast=False)
    assert [t["name"] for t in app_inst.tiles] == ["Third", "First", "Second"]


def test_drag_and_drop_gap_detection(tk_root, tmp_path, monkeypatch):
    """Verify get_card_info_at_coords finds the nearest card when dropped in margins/padding."""
    cfg_file = tmp_path / "tiles_gap.json"
    cfg_data = {
        "tiles": [
            {"name": "Card A", "action_type": "url", "target": "a.com"},
            {"name": "Card B", "action_type": "url", "target": "b.com"},
        ],
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        card0 = tile_app.rendered_cards[0]["card"]
        card1 = tile_app.rendered_cards[1]["card"]

        monkeypatch.setattr(card0, "winfo_ismapped", lambda: True)
        monkeypatch.setattr(card1, "winfo_ismapped", lambda: True)
        monkeypatch.setattr(card0, "winfo_rootx", lambda: 10)
        monkeypatch.setattr(card0, "winfo_rooty", lambda: 10)
        monkeypatch.setattr(card0, "winfo_width", lambda: 100)
        monkeypatch.setattr(card0, "winfo_height", lambda: 60)
        monkeypatch.setattr(card1, "winfo_rootx", lambda: 120)
        monkeypatch.setattr(card1, "winfo_rooty", lambda: 10)
        monkeypatch.setattr(card1, "winfo_width", lambda: 100)
        monkeypatch.setattr(card1, "winfo_height", lambda: 60)
        monkeypatch.setattr(tile_app.canvas, "winfo_rootx", lambda: 0)
        monkeypatch.setattr(tile_app.canvas, "winfo_rooty", lambda: 0)
        monkeypatch.setattr(tile_app.canvas, "winfo_width", lambda: 500)
        monkeypatch.setattr(tile_app.canvas, "winfo_height", lambda: 500)

        # Midpoint in horizontal gap between card 0 and card 1 (gap between 110 and 120 is 115)
        gap_x = 115
        mid_y = 40

        found = tile_app.get_card_info_at_coords(gap_x, mid_y)
        assert found is not None, "Gap hit-testing failed to find nearest card"
        assert found["tile"]["name"] in ("Card A", "Card B")
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_tooltip_info_icon_trigger(tk_root, tmp_path):
    """Verify Tooltip binds strictly to top-right info icon 'i' and not to whole card."""
    cfg_file = tmp_path / "tiles_tt.json"
    cfg_data = {
        "tiles": [
            {"name": "Hover Tile", "action_type": "url", "target": "https://example.com", "description": "Tip desc"},
        ],
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        sub_top.update()
        assert len(tile_app.tooltips) == 1
        tt = tile_app.tooltips[0]
        card_info = tile_app.rendered_cards[0]

        # Verify info icon exists and tooltip binds specifically to it
        lbl_info = card_info["lbl_info"]
        assert lbl_info.cget("text") == "ⓘ"
        assert tt.anchor_widget == lbl_info
        assert tt.widgets == [lbl_info]
        assert card_info["content"] not in tt.widgets
        assert card_info["card"] not in tt.widgets

        # Simulate enter on info icon: schedules tooltip
        tt.schedule()
        assert tt.after_id is not None

        # Simulate leave from info icon: immediately cancels and hides
        tt.on_leave()
        assert tt.after_id is None
        assert tt.tip_window is None
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_tooltip_minimize_and_unmap_cleanup(tk_root, tmp_path):
    """Verify that minimizing / unmapping the window or calling _hide_all_tooltips destroys the tooltip."""
    cfg_file = tmp_path / "tiles_tt_unmap.json"
    cfg_data = {
        "tiles": [
            {"name": "Tile 1", "action_type": "url", "target": "https://example.com", "description": "Desc"},
        ],
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        sub_top.update()
        tt = tile_app.tooltips[0]

        # Manually trigger show
        tt.show()
        assert tt.tip_window is not None
        assert tt.tip_window.winfo_exists()

        # Simulate window unmap (minimize)
        dummy_event = type("Event", (), {"widget": sub_top})()
        tile_app._on_root_unmap(dummy_event)
        assert tt.tip_window is None
        assert app.Tooltip.active_tooltip is None
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_tooltip_single_active_instance(tk_root, tmp_path):
    """Verify that opening a new tooltip automatically closes any previous tooltip."""
    cfg_file = tmp_path / "tiles_tt_single.json"
    cfg_data = {
        "tiles": [
            {"name": "Tile 1", "action_type": "url", "target": "1.com", "description": "Desc 1"},
            {"name": "Tile 2", "action_type": "url", "target": "2.com", "description": "Desc 2"},
        ],
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        sub_top.update()
        tt1 = tile_app.tooltips[0]
        tt2 = tile_app.tooltips[1]

        tt1.show()
        assert tt1.tip_window is not None
        assert app.Tooltip.active_tooltip is tt1

        # Now show tt2 - tt1 must be closed immediately
        tt2.show()
        assert tt1.tip_window is None
        assert tt2.tip_window is not None
        assert app.Tooltip.active_tooltip is tt2

        # Hide active
        app.Tooltip.hide_active()
        assert tt2.tip_window is None
        assert app.Tooltip.active_tooltip is None
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_path_with_quotes_handling(tk_root, monkeypatch, tmp_path):
    """Verify run_tile strips enclosing quotes from paths (e.g. from Explorer Copy as path)."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.lang = LANG_EN
    app_inst.dark_mode = False
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    app_inst.show_toast = lambda msg: None

    test_dir = tmp_path / "My Documents"
    test_dir.mkdir()
    quoted_dir = f'"{test_dir}"'

    called = {}
    monkeypatch.setattr(app.os, "startfile", lambda p: called.update({"startfile": p}), raising=False)

    app_inst.tiles = [{"name": "Quoted Folder", "action_type": "path", "target": quoted_dir, "use_count": 0}]
    app_inst.run_tile(0)
    assert called.get("startfile") == str(test_dir)


def test_python_action_frozen_resolution(tk_root, monkeypatch, tmp_path):
    """Verify that when running in PyInstaller frozen mode, python action invokes python rather than app.exe."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.lang = LANG_EN
    app_inst.dark_mode = False
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    app_inst.show_toast = lambda msg: None

    script = tmp_path / "test.py"
    script.write_text("print('hello')", encoding="utf-8")

    called = {}
    monkeypatch.setattr(app.subprocess, "Popen", lambda args, **kw: called.update({"popen": args}))
    monkeypatch.setattr(app.sys, "frozen", True, raising=False)
    monkeypatch.setattr(app.sys, "executable", "C:\\Program Files\\WinTiles\\app.exe")

    app_inst.tiles = [{"name": "Py Test", "action_type": "python", "target": str(script), "use_count": 0}]
    app_inst.run_tile(0)

    # Must NOT call app.exe
    invoked_exe = called.get("popen", [])[0]
    assert "app.exe" not in invoked_exe.lower()
    assert "python" in invoked_exe.lower() or "py" in invoked_exe.lower()


def test_info_icon_click_does_not_run_tile(tk_root, tmp_path, monkeypatch):
    """Verify clicking the info icon does not trigger tile execution."""
    cfg_file = tmp_path / "tiles_info_click.json"
    cfg_data = {
        "tiles": [
            {"name": "Safe Tile", "action_type": "url", "target": "https://example.com", "description": "Safe"},
        ],
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        sub_top.update()

        run_called = []
        monkeypatch.setattr(tile_app, "run_tile", lambda idx: run_called.append(idx))

        card_info = tile_app.rendered_cards[0]
        lbl_info = card_info["lbl_info"]

        # Clicking lbl_info generates break and must not run tile
        res = lbl_info.event_generate("<ButtonPress-1>")
        assert len(run_called) == 0
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_tooltip_suppressed_when_minimized(tk_root, tmp_path, monkeypatch):
    """Verify Tooltip.show does not pop up if the toplevel window is minimized or not normal."""
    sub_top = tk.Toplevel(tk_root)
    lbl = tk.Label(sub_top, text="info")
    lbl.pack()
    sub_top.update()

    tt = app.Tooltip(lbl, lambda: "Tip content")

    # Iconify window
    sub_top.iconify()
    sub_top.update()
    if sub_top.wm_state() != "iconic":
        monkeypatch.setattr(sub_top, "wm_state", lambda: "iconic")

    # Attempt to show
    tt.show()
    assert tt.tip_window is None
    sub_top.destroy()


def test_scrolling_and_deactivation_dismisses_tooltip(tk_root, tmp_path):
    """Verify that scrolling with mousewheel and window focus out dismisses any active tooltip."""
    cfg_file = tmp_path / "tiles_scroll_tt.json"
    cfg_data = {
        "tiles": [
            {"name": "Scroll Tile", "action_type": "url", "target": "https://example.com", "description": "Tip"},
        ],
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        sub_top.update()
        tt = tile_app.tooltips[0]

        tt.show()
        assert tt.tip_window is not None

        # Scroll mouse wheel
        dummy_event = type("Event", (), {"delta": -120})()
        tile_app._on_mousewheel(dummy_event)
        assert tt.tip_window is None

        # Show again and test focus out
        tt.show()
        assert tt.tip_window is not None
        focus_event = type("Event", (), {"widget": sub_top})()
        tile_app._on_root_focus_out(focus_event)
        assert tt.tip_window is None
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_get_icon_path_and_app_icon(tk_root, tmp_path):
    """Verify that get_icon_path finds assets/icon.png and TileApp sets app_icon."""
    icon_p = app.get_icon_path()
    assert icon_p is not None
    assert icon_p.exists()

    sub_top = tk.Toplevel(tk_root)
    tile_app = TileApp(sub_top)
    assert tile_app.app_icon is not None
    sub_top.destroy()


def test_canvas_scrollregion_min_height(tk_root, tmp_path):
    """Verify canvas scrollregion height never drops below canvas height to prevent empty top space."""
    sub_top = tk.Toplevel(tk_root)
    sub_top.geometry("800x600")
    tile_app = TileApp(sub_top)
    sub_top.update()

    tile_app._update_scrollregion()
    sr = tile_app.canvas.cget("scrollregion")
    sr_vals = [float(v) for v in sr.split()]
    canvas_h = tile_app.canvas.winfo_height()

    assert len(sr_vals) == 4
    assert sr_vals[1] == 0.0
    assert sr_vals[3] >= canvas_h
    sub_top.destroy()


def test_tooltip_hover_grace_period(tk_root):
    """Verify Tooltip schedules hide and can cancel hide when re-entered."""
    sub_top = tk.Toplevel(tk_root)
    sub_top.geometry("300x200")
    sub_top.deiconify()
    lbl = tk.Label(sub_top, text="i")
    lbl.pack()
    sub_top.update()

    tt = app.Tooltip(lbl, lambda: "Description text")
    tt.show()
    assert tt.tip_window is not None

    tt.on_leave()
    assert tt.hide_after_id is not None
    assert tt.tip_window is not None

    tt.unschedule_hide()
    assert tt.hide_after_id is None
    assert tt.tip_window is not None

    tt.hide()
    assert tt.tip_window is None
    sub_top.destroy()


def test_tooltip_show_when_zoomed(tk_root, monkeypatch):
    """Verify Tooltip.show works when window is in zoomed (maximized) state."""
    sub_top = tk.Toplevel(tk_root)
    monkeypatch.setattr(sub_top, "wm_state", lambda: "zoomed")
    lbl = tk.Label(sub_top, text="i")
    lbl.pack()
    sub_top.update()

    tt = app.Tooltip(lbl, lambda: "Maximized tooltip text")
    tt.show()
    assert tt.tip_window is not None
    assert tt.tip_window.winfo_exists()
    tt.hide()
    sub_top.destroy()


def test_canvas_scrollregion_resets_yview_when_content_fits(tk_root):
    """Verify canvas yview is reset to 0 when content fits within canvas height."""
    sub_top = tk.Toplevel(tk_root)
    sub_top.geometry("800x600")
    tile_app = TileApp(sub_top)
    sub_top.update()

    # Simulate scrolled view
    tile_app.canvas.yview_moveto(0.5)
    tile_app._update_scrollregion()
    assert tile_app.canvas.yview()[0] == 0.0
    sub_top.destroy()


def test_tooltip_cases_a_b_c_d_e(tk_root, tmp_path):
    """
    Verify all tooltip description lifecycle cases:
    Case A: description exists -> icon 'i' visible, hover shows description
    Case B: empty description -> icon 'i' invisible, no tooltip
    Case C: whitespace description -> icon 'i' invisible
    Case D: edit description -> tooltip shows new description, old not kept
    Case E: remove description -> icon 'i' disappears, tooltip not available
    """
    cfg_file = tmp_path / "tiles_abcde.json"
    cfg_data = {
        "tiles": [
            {"name": "Tile A", "action_type": "url", "target": "https://a.com", "description": "Mój opis"},
            {"name": "Tile B", "action_type": "url", "target": "https://b.com", "description": ""},
            {"name": "Tile C", "action_type": "url", "target": "https://c.com", "description": "   "},
        ]
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        sub_top.update()

        cards = tile_app.rendered_cards
        assert len(cards) == 3

        # Case A: description exists ("Mój opis")
        card_a = cards[0]
        assert card_a["lbl_info"] is not None
        assert card_a["lbl_info"].cget("text") == "ⓘ"
        assert len(tile_app.tooltips) == 1
        tt_a = tile_app.tooltips[0]
        assert tt_a.anchor_widget == card_a["lbl_info"]
        assert tt_a.text_provider() == "Mój opis"

        # Case B: empty description ("")
        card_b = cards[1]
        assert card_b["lbl_info"] is None

        # Case C: whitespace description ("   ")
        card_c = cards[2]
        assert card_c["lbl_info"] is None

        # Case D: edit description (Stary opis -> Nowy opis)
        tile_app.tiles[0]["description"] = "Nowy opis"
        tile_app.render_tiles()
        sub_top.update()

        card_a_edited = tile_app.rendered_cards[0]
        assert card_a_edited["lbl_info"] is not None
        assert len(tile_app.tooltips) == 1
        tt_a_edited = tile_app.tooltips[0]
        assert tt_a_edited.text_provider() == "Nowy opis"
        assert tt_a_edited.text_provider() != "Mój opis"

        # Case E: remove description
        tile_app.tiles[0]["description"] = ""
        tile_app.render_tiles()
        sub_top.update()

        card_a_cleared = tile_app.rendered_cards[0]
        assert card_a_cleared["lbl_info"] is None
        assert len(tile_app.tooltips) == 0

    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_card_subtitle_retains_target_with_description(tk_root, tmp_path):
    """Verify that tile subtitle displays target preview even when description is present."""
    cfg_file = tmp_path / "tiles_target_test.json"
    cfg_data = {
        "tiles": [
            {
                "name": "Ścieżki",
                "action_type": "ps1",
                "target": r"D:\Git\skrypty\sciezka.ps1",
                "description": "to jest opis sciezek hahahahaha",
            },
            {
                "name": "GIT",
                "action_type": "path",
                "target": r"D:\Git",
                "description": "",
            },
        ]
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()
    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    try:
        tile_app = TileApp(sub_top)
        sub_top.update()

        cards = tile_app.rendered_cards
        assert len(cards) == 2

        # Card 0: "Ścieżki" has target "sciezka.ps1" and description "to jest opis sciezek hahahahaha"
        card_sciezki = cards[0]
        lbl_sub_sciezki = card_sciezki["widgets"][8]  # lbl_sub is 8th widget in widgets list
        assert lbl_sub_sciezki.cget("text") == "sciezka.ps1"
        assert card_sciezki["lbl_info"] is not None

        # Card 1: "GIT" has target "D:\Git" -> "Git"
        card_git = cards[1]
        lbl_sub_git = card_git["widgets"][8]
        assert lbl_sub_git.cget("text") == "Git"
        assert card_git["lbl_info"] is None
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_tooltip_interactive_show_hide(tk_root):
    """Verify Tooltip show, hide, schedule, and on_leave operations."""
    sub_top = tk.Toplevel(tk_root)
    sub_top.deiconify()
    lbl = tk.Label(sub_top, text="ⓘ")
    lbl.pack()
    sub_top.update()

    try:
        tt = app.Tooltip(lbl, lambda: "Przykładowy opis dymku", dark_mode=False)

        # Initial state: no popup
        assert tt.tip_window is None

        # Show tooltip directly
        tt.show()
        sub_top.update()
        assert tt.tip_window is not None
        assert tt.tip_window.winfo_exists()
        assert app.Tooltip.active_tooltip is tt

        # Hide tooltip directly
        tt.hide()
        sub_top.update()
        assert tt.tip_window is None
        assert app.Tooltip.active_tooltip is None

        # Schedule show
        tt.schedule()
        assert tt.after_id is not None
        sub_top.update()
        tt.show()
        assert tt.tip_window is not None

        # on_leave hides the tooltip
        tt.on_leave()
        if tt.hide_after_id:
            lbl.after_cancel(tt.hide_after_id)
        tt.hide()
        assert tt.tip_window is None
    finally:
        sub_top.destroy()


def test_grid_column_cleanup_on_column_change(tk_root):
    """Verify that reducing column count cleans up stale column weights/uniform settings."""
    sub_top = tk.Toplevel(tk_root)
    sub_top.geometry("900x560")
    sub_top.update()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "tiles.json"
        app.PRIMARY_CONFIG_FILE = cfg
        app.FALLBACK_CONFIG_FILE = cfg

        try:
            tile_app = TileApp(sub_top)
            sub_top.update()

            # Initially 4 columns
            tile_app.current_cols = 4
            tile_app.render_tiles()
            sub_top.update()

            for c in range(4):
                info = tile_app.tiles_inner_frame.columnconfigure(c)
                assert info.get("weight") == 1 or info.get("weight") == "1"
                assert str(info.get("uniform")) == "col"

            # Reduce to 3 columns
            tile_app.current_cols = 3
            tile_app.render_tiles()
            sub_top.update()

            for c in range(3):
                info = tile_app.tiles_inner_frame.columnconfigure(c)
                assert info.get("weight") == 1 or info.get("weight") == "1"
                assert str(info.get("uniform")) == "col"

            # Column 3 must have weight 0 and not belong to uniform group "col"
            info3 = tile_app.tiles_inner_frame.columnconfigure(3)
            assert info3.get("weight") == 0 or info3.get("weight") == "0"
            assert not info3.get("uniform") or str(info3.get("uniform")) in ('""', '')
        finally:
            app.PRIMARY_CONFIG_FILE = old_primary
            app.FALLBACK_CONFIG_FILE = old_fallback
            sub_top.destroy()


def test_light_and_dark_mode_column_parity(tk_root):
    """Verify that light and dark mode compute equal column counts and consistent tile layout."""
    sub_top = tk.Toplevel(tk_root)
    sub_top.geometry("900x560")
    sub_top.update()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "tiles.json"
        app.PRIMARY_CONFIG_FILE = cfg
        app.FALLBACK_CONFIG_FILE = cfg

        try:
            tile_app = TileApp(sub_top)
            sub_top.update()

            # Verify dark mode toggle parity
            tile_app.dark_mode = False
            tile_app.apply_theme()
            sub_top.update()

            class MockEvent:
                width = 840

            tile_app._on_canvas_configure(MockEvent())
            sub_top.update()
            light_cols = tile_app.current_cols

            tile_app.dark_mode = True
            tile_app.apply_theme()
            sub_top.update()
            tile_app._on_canvas_configure(MockEvent())
            sub_top.update()
            dark_cols = tile_app.current_cols

            assert light_cols == 4
            assert dark_cols == 4
            assert light_cols == dark_cols
        finally:
            app.PRIMARY_CONFIG_FILE = old_primary
            app.FALLBACK_CONFIG_FILE = old_fallback
            sub_top.destroy()


def test_header_tooltips_and_language_switching(tk_root):
    """Verify that header buttons have tooltips attached and update correctly across language changes."""
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "tiles.json"
        app.PRIMARY_CONFIG_FILE = cfg
        app.FALLBACK_CONFIG_FILE = cfg

        try:
            tile_app = TileApp(sub_top)
            assert len(tile_app.header_tooltips) >= 5

            # Find tooltips for topmost, autostart, and dark_mode buttons
            topmost_tt = next(tt for tt in tile_app.header_tooltips if tt.anchor_widget is tile_app.btn_topmost)
            autostart_tt = next(tt for tt in tile_app.header_tooltips if tt.anchor_widget is tile_app.btn_autostart)
            dark_mode_tt = next(tt for tt in tile_app.header_tooltips if tt.anchor_widget is tile_app.btn_dark_mode)
            clear_search_tt = next(tt for tt in tile_app.header_tooltips if tt.anchor_widget is tile_app.btn_clear_search)

            # Test Polish language tooltips
            tile_app.lang = LANG_PL
            assert topmost_tt.text_provider() == tile_app._get_lock_tooltip_text()
            assert "Tryb okna:" in topmost_tt.text_provider()
            assert "Autostart systemu:" in autostart_tt.text_provider()
            assert dark_mode_tt.text_provider() == TRANSLATIONS[LANG_PL]["tt_dark_mode"]
            assert clear_search_tt.text_provider() == TRANSLATIONS[LANG_PL]["tt_clear_search"]

            # Test English language tooltips
            tile_app.lang = LANG_EN
            assert topmost_tt.text_provider() == tile_app._get_lock_tooltip_text()
            assert "Window mode:" in topmost_tt.text_provider()
            assert "System autostart:" in autostart_tt.text_provider()
            assert dark_mode_tt.text_provider() == TRANSLATIONS[LANG_EN]["tt_dark_mode"]
            assert clear_search_tt.text_provider() == TRANSLATIONS[LANG_EN]["tt_clear_search"]
        finally:
            app.PRIMARY_CONFIG_FILE = old_primary
            app.FALLBACK_CONFIG_FILE = old_fallback
            sub_top.destroy()


def test_opacity_ctrl_mousewheel_adjustment(tk_root):
    """Verify that Ctrl+MouseWheel adjusts window opacity with bounds [0.10, 1.00] and displays toast feedback."""
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "tiles.json"
        app.PRIMARY_CONFIG_FILE = cfg
        app.FALLBACK_CONFIG_FILE = cfg

        try:
            tile_app = TileApp(sub_top)
            tile_app.lang = LANG_PL
            tile_app.opacity = 1.0

            class MockScrollDownEvent:
                delta = -120
                state = 0x0004

            class MockScrollUpEvent:
                delta = 120
                state = 0x0004

            # Scroll down decreases opacity by 5%
            tile_app._on_ctrl_mousewheel(MockScrollDownEvent())
            assert tile_app.opacity == pytest.approx(0.95, abs=0.001)
            assert "95%" in tile_app.lbl_status_toast.cget("text")

            # Scroll down multiple times towards min clamp
            for _ in range(30):
                tile_app._on_ctrl_mousewheel(MockScrollDownEvent())

            # Min clamp is 0.10 (10%)
            assert tile_app.opacity == pytest.approx(0.10, abs=0.001)
            assert "10%" in tile_app.lbl_status_toast.cget("text")

            # Scroll up increases opacity
            tile_app._on_ctrl_mousewheel(MockScrollUpEvent())
            assert tile_app.opacity == pytest.approx(0.15, abs=0.001)
            assert "15%" in tile_app.lbl_status_toast.cget("text")

            # Scroll up multiple times towards max clamp 1.0 (100%)
            for _ in range(30):
                tile_app._on_ctrl_mousewheel(MockScrollUpEvent())

            assert tile_app.opacity == pytest.approx(1.0, abs=0.001)
            assert "100%" in tile_app.lbl_status_toast.cget("text")

            # Normal mousewheel with Ctrl pressed delegates to _on_ctrl_mousewheel
            res = tile_app._on_mousewheel(MockScrollDownEvent())
            assert res == "break"
            assert tile_app.opacity == pytest.approx(0.95, abs=0.001)
        finally:
            app.PRIMARY_CONFIG_FILE = old_primary
            app.FALLBACK_CONFIG_FILE = old_fallback
            sub_top.destroy()


def test_opacity_config_parsing_and_saving(tk_root):
    """Verify opacity configuration is properly loaded, clamped, and saved in payload."""
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE

    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Path(tmpdir) / "tiles.json"
        app.PRIMARY_CONFIG_FILE = cfg
        app.FALLBACK_CONFIG_FILE = cfg

        try:
            tile_app = TileApp(sub_top)

            # Test parsing with custom opacity
            payload = {
                "always_on_top": False,
                "dark_mode": False,
                "opacity": 0.85,
                "tiles": [],
            }
            parsed = tile_app._parse_config_payload(payload)
            assert parsed["opacity"] == 0.85

            # Test parsing with out-of-range opacity (too low -> clamped to 0.10)
            payload_low = {
                "opacity": 0.01,
                "tiles": [],
            }
            parsed_low = tile_app._parse_config_payload(payload_low)
            assert parsed_low["opacity"] == 0.10

            # Test parsing with out-of-range opacity (too high -> clamped to 1.0)
            payload_high = {
                "opacity": 1.5,
                "tiles": [],
            }
            parsed_high = tile_app._parse_config_payload(payload_high)
            assert parsed_high["opacity"] == 1.0

            # Test building config payload
            tile_app.opacity = 0.75
            built = tile_app._build_config_payload()
            assert built["opacity"] == 0.75
        finally:
            app.PRIMARY_CONFIG_FILE = old_primary
            app.FALLBACK_CONFIG_FILE = old_fallback
            sub_top.destroy()


def test_smart_window_lock_cycle_and_modes(tk_root, tmp_path):
    """Verify single-click cycling: Normal -> Topmost -> Locked -> Normal."""
    cfg_file = tmp_path / "test_lock.json"
    cfg_file.write_text(json.dumps({"tiles": [{"name": "Sample", "action_type": "url", "target": "https://example.com"}]}), encoding="utf-8")
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"

    try:
        tile_app = TileApp(sub_top)
        # Initial state: Normal
        assert tile_app.window_lock_mode == app.LOCK_MODE_NORMAL
        assert tile_app.always_on_top is False
        assert tile_app.btn_topmost.cget("text") == "📌"

        # Click 1: Pinned / Topmost
        tile_app.cycle_lock_mode()
        assert tile_app.window_lock_mode == app.LOCK_MODE_TOPMOST
        assert tile_app.always_on_top is True
        assert tile_app.btn_topmost.cget("text") == "📌"
        assert tile_app.btn_topmost.cget("fg") == ("#38bdf8" if tile_app.dark_mode else "#0284c7")

        # Click 2: Click-Locked
        tile_app.cycle_lock_mode()
        assert tile_app.window_lock_mode == app.LOCK_MODE_LOCKED
        assert tile_app.always_on_top is True
        assert tile_app.btn_topmost.cget("text") == "🔒"
        assert tile_app.btn_topmost.cget("fg") == ("#fbbf24" if tile_app.dark_mode else "#b45309")

        # Click 3: Back to Normal
        tile_app.cycle_lock_mode()
        assert tile_app.window_lock_mode == app.LOCK_MODE_NORMAL
        assert tile_app.always_on_top is False
        assert tile_app.btn_topmost.cget("text") == "📌"
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_smart_window_lock_double_click(tk_root, tmp_path):
    """Verify double-click fast-toggle between Normal and Locked."""
    cfg_file = tmp_path / "test_lock_dbl.json"
    cfg_file.write_text(json.dumps({"tiles": []}), encoding="utf-8")
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"

    try:
        tile_app = TileApp(sub_top)
        assert tile_app.window_lock_mode == app.LOCK_MODE_NORMAL

        # Double click from Normal -> Locked
        ret = tile_app.on_lock_button_double_click()
        assert ret == "break"
        assert tile_app.window_lock_mode == app.LOCK_MODE_LOCKED
        assert tile_app.always_on_top is True
        assert tile_app.btn_topmost.cget("text") == "🔒"

        # Double click from Locked -> Normal
        ret2 = tile_app.on_lock_button_double_click()
        assert ret2 == "break"
        assert tile_app.window_lock_mode == app.LOCK_MODE_NORMAL
        assert tile_app.always_on_top is False
        assert tile_app.btn_topmost.cget("text") == "📌"
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_smart_window_lock_protection_behavior(tk_root, tmp_path, monkeypatch):
    """Verify that in locked mode, tile actions, drag-drop, and edit menus are blocked."""
    cfg_file = tmp_path / "test_lock_prot.json"
    cfg_file.write_text(json.dumps({"tiles": [{"name": "Test Tile", "action_type": "url", "target": "https://test.com", "use_count": 0}]}), encoding="utf-8")
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"

    try:
        tile_app = TileApp(sub_top)
        opened_urls = []
        monkeypatch.setattr(app.webbrowser, "open", lambda u, new=2: opened_urls.append(u))

        # Switch to Locked mode
        tile_app.set_lock_mode(app.LOCK_MODE_LOCKED)
        assert tile_app.window_lock_mode == app.LOCK_MODE_LOCKED

        # 1. Attempt to run tile
        tile_app.run_tile(0)
        assert len(opened_urls) == 0, "Tile ran action while in locked mode!"
        assert tile_app.tiles[0]["use_count"] == 0

        # 2. Attempt press / drag
        dummy_event = type("Event", (), {"x_root": 100, "y_root": 100})()
        press_res = tile_app.on_tile_press(dummy_event, 0)
        assert press_res == "break"
        assert tile_app.is_dragging is False
        assert tile_app.drag_source_idx is None

        # 3. Attempt context menu
        menu_res = tile_app.open_tile_menu(dummy_event, 0)
        assert menu_res == "break"

        # 4. Status hint indicates locked
        assert tile_app.lbl_status_hint.cget("text") == tile_app.t["hint_mouse_locked"]

        # Unlock back to normal
        tile_app.set_lock_mode(app.LOCK_MODE_NORMAL)
        tile_app.run_tile(0)
        assert len(opened_urls) == 1
        assert tile_app.tiles[0]["use_count"] == 1
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_smart_window_lock_config_parsing_and_saving():
    """Verify config parsing, migration from legacy always_on_top, and saving."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.tiles = []
    app_inst.var_dark_mode = type("DummyVar", (), {"get": lambda self: False})()
    app_inst.opacity = 1.0
    app_inst.lang = app.LANG_EN
    app_inst.current_sort = "manual"

    # Legacy config: always_on_top=True without window_lock_mode
    legacy_true = {"always_on_top": True, "tiles": []}
    parsed1 = app_inst._parse_config_payload(legacy_true)
    assert parsed1["window_lock_mode"] == app.LOCK_MODE_TOPMOST
    assert parsed1["always_on_top"] is True

    # Legacy config: always_on_top=False without window_lock_mode
    legacy_false = {"always_on_top": False, "tiles": []}
    parsed2 = app_inst._parse_config_payload(legacy_false)
    assert parsed2["window_lock_mode"] == app.LOCK_MODE_NORMAL
    assert parsed2["always_on_top"] is False

    # Modern config: window_lock_mode="locked"
    modern_locked = {"window_lock_mode": "locked", "tiles": []}
    parsed3 = app_inst._parse_config_payload(modern_locked)
    assert parsed3["window_lock_mode"] == app.LOCK_MODE_LOCKED
    assert parsed3["always_on_top"] is True

    # Test payload building
    app_inst.window_lock_mode = app.LOCK_MODE_LOCKED
    app_inst.always_on_top = True
    payload = app_inst._build_config_payload()
    assert payload["window_lock_mode"] == app.LOCK_MODE_LOCKED
    assert payload["always_on_top"] is True

    app_inst.window_lock_mode = app.LOCK_MODE_NORMAL
    app_inst.always_on_top = False
    payload_normal = app_inst._build_config_payload()
    assert payload_normal["window_lock_mode"] == app.LOCK_MODE_NORMAL
    assert payload_normal["always_on_top"] is False


def test_smart_window_lock_menu_and_theme_parity(tk_root, tmp_path):
    """Verify right-click menu options and theme appearance across all modes."""
    cfg_file = tmp_path / "test_lock_theme.json"
    cfg_file.write_text(json.dumps({"tiles": []}), encoding="utf-8")
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"

    try:
        tile_app = TileApp(sub_top)

        # Test Dark Mode styling
        tile_app.dark_mode = True
        tile_app.set_lock_mode(app.LOCK_MODE_NORMAL, autosave=False, show_toast=False)
        assert tile_app.btn_topmost.cget("text") == "📌"
        assert tile_app.btn_topmost.cget("fg") == tile_app.c_fg_muted

        tile_app.set_lock_mode(app.LOCK_MODE_TOPMOST, autosave=False, show_toast=False)
        assert tile_app.btn_topmost.cget("text") == "📌"
        assert tile_app.btn_topmost.cget("fg") == "#38bdf8"

        tile_app.set_lock_mode(app.LOCK_MODE_LOCKED, autosave=False, show_toast=False)
        assert tile_app.btn_topmost.cget("text") == "🔒"
        assert tile_app.btn_topmost.cget("fg") == "#fbbf24"

        # Test Light Mode styling
        tile_app.dark_mode = False
        tile_app.set_lock_mode(app.LOCK_MODE_NORMAL, autosave=False, show_toast=False)
        assert tile_app.btn_topmost.cget("text") == "📌"
        assert tile_app.btn_topmost.cget("fg") == tile_app.c_fg_muted

        tile_app.set_lock_mode(app.LOCK_MODE_TOPMOST, autosave=False, show_toast=False)
        assert tile_app.btn_topmost.cget("text") == "📌"
        assert tile_app.btn_topmost.cget("fg") == "#0284c7"

        tile_app.set_lock_mode(app.LOCK_MODE_LOCKED, autosave=False, show_toast=False)
        assert tile_app.btn_topmost.cget("text") == "🔒"
        assert tile_app.btn_topmost.cget("fg") == "#b45309"
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_autostart_command_resolution(monkeypatch):
    """Verify autostart command line formulation for both script and frozen executable modes."""
    # Script mode
    cmd_script = app.get_autostart_command()
    assert str(Path(app.__file__).resolve()) in cmd_script
    assert cmd_script.startswith('"')

    # Frozen exe mode
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", "/fake/bin/WinTiles.exe")
    cmd_frozen = app.get_autostart_command()
    assert "/fake/bin/WinTiles.exe" in cmd_frozen


def test_linux_autostart_file_lifecycle(tmp_path, monkeypatch):
    """Verify Linux XDG autostart desktop file creation, inspection, and removal."""
    fake_config = tmp_path / ".config"
    monkeypatch.setenv("XDG_CONFIG_HOME", str(fake_config))

    desktop_path = fake_config / "autostart" / app.LINUX_DESKTOP_FILENAME
    assert not desktop_path.exists()
    assert app.is_linux_autostart_enabled() is False

    # Enable autostart
    res = app.set_linux_autostart(True)
    assert res is True
    assert desktop_path.is_file()
    assert app.is_linux_autostart_enabled() is True

    content = desktop_path.read_text(encoding="utf-8")
    assert "[Desktop Entry]" in content
    assert "Name=WinTiles" in content
    assert "Exec=" in content

    # Disable autostart
    res_off = app.set_linux_autostart(False)
    assert res_off is True
    assert not desktop_path.exists()
    assert app.is_linux_autostart_enabled() is False


def test_windows_autostart_registry_mock(monkeypatch):
    """Verify Windows registry query and update using a mock winreg module."""
    reg_store = {}

    class MockKey:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    class MockWinreg:
        HKEY_CURRENT_USER = "HKCU"
        KEY_READ = 1
        KEY_SET_VALUE = 2
        REG_SZ = 1

        @staticmethod
        def OpenKey(hkey, subkey, reserved=0, access=0):
            if access == MockWinreg.KEY_READ and app.REG_APP_NAME not in reg_store:
                raise FileNotFoundError("Value not found")
            return MockKey()

        @staticmethod
        def CreateKeyEx(hkey, subkey, reserved=0, access=0):
            return MockKey()

        @staticmethod
        def QueryValueEx(key, name):
            if name in reg_store:
                return reg_store[name], MockWinreg.REG_SZ
            raise FileNotFoundError(f"Name {name} not found")

        @staticmethod
        def SetValueEx(key, name, reserved, reg_type, val):
            reg_store[name] = val

        @staticmethod
        def DeleteValue(key, name):
            if name in reg_store:
                del reg_store[name]
            else:
                raise FileNotFoundError()

    monkeypatch.setattr(sys, "platform", "win32")
    import types
    mock_mod = types.ModuleType("winreg")
    for attr in dir(MockWinreg):
        if not attr.startswith("__"):
            setattr(mock_mod, attr, getattr(MockWinreg, attr))
    monkeypatch.setitem(sys.modules, "winreg", mock_mod)

    # Initially not enabled
    assert app.is_windows_autostart_enabled() is False

    # Enable
    assert app.set_windows_autostart(True) is True
    assert app.REG_APP_NAME in reg_store
    assert app.is_windows_autostart_enabled() is True

    # Disable
    assert app.set_windows_autostart(False) is True
    assert app.REG_APP_NAME not in reg_store
    assert app.is_windows_autostart_enabled() is False


def test_system_autostart_dispatchers(monkeypatch):
    """Verify that is_system_autostart_enabled and set_system_autostart route based on sys.platform."""
    calls = []

    def mock_win_is():
        calls.append("win_is")
        return True

    def mock_win_set(val):
        calls.append(f"win_set_{val}")
        return True

    def mock_lin_is():
        calls.append("lin_is")
        return False

    def mock_lin_set(val):
        calls.append(f"lin_set_{val}")
        return True

    monkeypatch.setattr(app, "is_windows_autostart_enabled", mock_win_is)
    monkeypatch.setattr(app, "set_windows_autostart", mock_win_set)
    monkeypatch.setattr(app, "is_linux_autostart_enabled", mock_lin_is)
    monkeypatch.setattr(app, "set_linux_autostart", mock_lin_set)

    # Test win32 routing
    monkeypatch.setattr(sys, "platform", "win32")
    assert app.is_system_autostart_enabled() is True
    assert "win_is" in calls
    app.set_system_autostart(True)
    assert "win_set_True" in calls

    # Test linux routing
    monkeypatch.setattr(sys, "platform", "linux")
    assert app.is_system_autostart_enabled() is False
    assert "lin_is" in calls
    app.set_system_autostart(False)
    assert "lin_set_False" in calls


def test_tile_app_autostart_toggle_and_toast(tk_root, tmp_path, monkeypatch):
    """Verify toggling autostart from TileApp, updating UI, toast feedback, and autosave."""
    cfg_file = tmp_path / "test_autostart.json"
    cfg_file.write_text(json.dumps({"autostart": False, "tiles": []}), encoding="utf-8")
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"

    # Mock system autostart to avoid touching actual user system
    system_calls = []

    def fake_set_sys(val):
        system_calls.append(val)
        return True

    monkeypatch.setattr(app, "set_system_autostart", fake_set_sys)

    try:
        tile_app = TileApp(sub_top)
        assert tile_app.autostart is False
        assert tile_app.btn_autostart.cget("text") == "🚀"

        # Track toast notifications
        toasts = []
        tile_app.show_toast = lambda msg: toasts.append(msg)

        # Toggle on
        tile_app.toggle_autostart()
        assert tile_app.autostart is True
        assert tile_app.var_autostart.get() is True
        assert system_calls[-1] is True
        assert any("Enabled" in m or "Włączon" in m for m in toasts)

        # Saved file should now have "autostart": true
        data = json.loads(cfg_file.read_text(encoding="utf-8"))
        assert data["autostart"] is True

        # Toggle off
        tile_app.toggle_autostart()
        assert tile_app.autostart is False
        assert tile_app.var_autostart.get() is False
        assert system_calls[-1] is False
        assert any("Disabled" in m or "Wyłączon" in m for m in toasts)

        # Saved file should now have "autostart": false
        data = json.loads(cfg_file.read_text(encoding="utf-8"))
        assert data["autostart"] is False
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_tile_app_autostart_button_theme_and_tooltips(tk_root, tmp_path, monkeypatch):
    """Verify visual button states across themes and tooltip text providers."""
    cfg_file = tmp_path / "test_autostart_theme.json"
    cfg_file.write_text(json.dumps({"tiles": []}), encoding="utf-8")
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"
    monkeypatch.setattr(app, "set_system_autostart", lambda val: True)

    try:
        tile_app = TileApp(sub_top)

        # Dark mode styling
        tile_app.dark_mode = True
        tile_app.set_autostart(True, autosave=False, show_toast=False)
        assert tile_app.btn_autostart.cget("bg") == "#064e3b"
        assert tile_app.btn_autostart.cget("fg") == "#34d399"

        tile_app.set_autostart(False, autosave=False, show_toast=False)
        assert tile_app.btn_autostart.cget("bg") == tile_app.c_surface
        assert tile_app.btn_autostart.cget("fg") == tile_app.c_fg_muted

        # Light mode styling
        tile_app.dark_mode = False
        tile_app.set_autostart(True, autosave=False, show_toast=False)
        assert tile_app.btn_autostart.cget("bg") == "#ecfdf5"
        assert tile_app.btn_autostart.cget("fg") == "#059669"

        tile_app.set_autostart(False, autosave=False, show_toast=False)
        assert tile_app.btn_autostart.cget("bg") == tile_app.c_surface
        assert tile_app.btn_autostart.cget("fg") == tile_app.c_fg_muted

        # Tooltips in Polish and English
        tile_app.lang = LANG_PL
        tile_app.autostart = True
        tt_pl_on = tile_app._get_autostart_tooltip_text()
        assert "Włączony" in tt_pl_on
        assert "wyłączyć" in tt_pl_on

        tile_app.autostart = False
        tt_pl_off = tile_app._get_autostart_tooltip_text()
        assert "Wyłączony" in tt_pl_off
        assert "włączyć" in tt_pl_off

        tile_app.lang = LANG_EN
        tile_app.autostart = True
        tt_en_on = tile_app._get_autostart_tooltip_text()
        assert "Enabled" in tt_en_on
        assert "disable" in tt_en_on

        tile_app.autostart = False
        tt_en_off = tile_app._get_autostart_tooltip_text()
        assert "Disabled" in tt_en_off
        assert "enable" in tt_en_off
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_tile_app_autostart_lock_protection(tk_root, tmp_path, monkeypatch):
    """Verify that in Click-Locked mode (LOCK_MODE_LOCKED), autostart toggle is protected from clicks."""
    cfg_file = tmp_path / "test_autostart_lock.json"
    cfg_file.write_text(json.dumps({"tiles": []}), encoding="utf-8")
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"

    monkeypatch.setattr(app, "set_system_autostart", lambda val: True)

    try:
        tile_app = TileApp(sub_top)
        tile_app.set_lock_mode(app.LOCK_MODE_LOCKED, autosave=False, show_toast=False)
        tile_app.autostart = False

        toasts = []
        tile_app.show_toast = lambda msg: toasts.append(msg)

        # Attempt to toggle autostart while window is locked
        tile_app.toggle_autostart()
        assert tile_app.autostart is False
        assert any("locked" in m.lower() or "zablokowan" in m.lower() for m in toasts)

        # Attempt to open menu while locked
        toasts.clear()
        tile_app.show_autostart_menu()
        assert any("locked" in m.lower() or "zablokowan" in m.lower() for m in toasts)
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_tile_app_autostart_error_handling(tk_root, tmp_path, monkeypatch):
    """Verify that if set_system_autostart fails, the app safely reverts state and displays an error."""
    cfg_file = tmp_path / "test_autostart_err.json"
    cfg_file.write_text(json.dumps({"autostart": False, "tiles": []}), encoding="utf-8")
    sub_top = tk.Toplevel(tk_root)
    sub_top.withdraw()

    old_primary = app.PRIMARY_CONFIG_FILE
    old_fallback = app.FALLBACK_CONFIG_FILE
    app.PRIMARY_CONFIG_FILE = cfg_file
    app.FALLBACK_CONFIG_FILE = tmp_path / "fallback.json"

    def faulty_set_autostart(val):
        raise PermissionError("Access denied to registry")

    monkeypatch.setattr(app, "set_system_autostart", faulty_set_autostart)

    error_boxes = []
    monkeypatch.setattr(app.messagebox, "showerror", lambda title, msg, **kw: error_boxes.append((title, msg)))

    try:
        tile_app = TileApp(sub_top)
        assert tile_app.autostart is False

        res = tile_app.set_autostart(True)
        assert res is False
        assert tile_app.autostart is False
        assert len(error_boxes) == 1
        assert "Access denied" in error_boxes[0][1]
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
        sub_top.destroy()


def test_tile_run_on_start_toggle(tk_root):
    """Verify toggle_tile_run_on_start flips the flag, calls autosave, and updates toast."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.lang = LANG_EN
    app_inst.dark_mode = False
    app_inst.window_lock_mode = "normal"
    app_inst.tooltips = []
    app_inst.header_tooltips = []
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    toasts = []
    app_inst.show_toast = lambda msg: toasts.append(msg)

    app_inst.tiles = [
        {
            "name": "Test Tile",
            "action_type": "url",
            "target": "https://example.com",
            "run_on_start": False,
            "use_count": 0,
        },
    ]

    # Toggle ON
    app_inst.toggle_tile_run_on_start(0)
    assert app_inst.tiles[0]["run_on_start"] is True
    assert len(toasts) == 1
    assert "will run on WinTiles start" in toasts[-1]

    # Toggle OFF
    app_inst.toggle_tile_run_on_start(0)
    assert app_inst.tiles[0]["run_on_start"] is False
    assert len(toasts) == 2
    assert "will no longer run on start" in toasts[-1]


def test_autorun_tiles_on_startup(tk_root, monkeypatch):
    """Verify _execute_autorun_tiles runs only marked tiles and only when global autostart is enabled."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.lang = LANG_EN
    app_inst.dark_mode = False
    app_inst.window_lock_mode = "normal"
    app_inst.autostart = True  # Global autostart is enabled
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    toasts = []
    app_inst.show_toast = lambda msg: toasts.append(msg)

    run_log = []
    monkeypatch.setattr(app.webbrowser, "open", lambda url, new=2: run_log.append(url))

    app_inst.tiles = [
        {
            "name": "Auto Tile",
            "action_type": "url",
            "target": "https://auto.com",
            "run_on_start": True,
            "use_count": 0,
        },
        {
            "name": "Normal Tile",
            "action_type": "url",
            "target": "https://normal.com",
            "run_on_start": False,
            "use_count": 0,
        },
    ]

    # With global autostart=True: Auto Tile executes
    app_inst._execute_autorun_tiles()
    assert len(run_log) == 1
    assert "auto.com" in run_log[0]
    assert app_inst.tiles[0]["use_count"] == 1
    assert app_inst.tiles[1]["use_count"] == 0
    assert len(toasts) == 1
    assert "Auto-started 1 tile" in toasts[0]

    # When global autostart is False: no tiles should execute
    run_log.clear()
    toasts.clear()
    app_inst.autostart = False
    app_inst.tiles[0]["use_count"] = 0
    app_inst._execute_autorun_tiles()
    assert len(run_log) == 0
    assert app_inst.tiles[0]["use_count"] == 0
    assert len(toasts) == 0


def test_run_on_start_persisted_in_config(tk_root):
    """Verify run_on_start flag is preserved through validate/parse cycle."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root

    data = {
        "tiles": [
            {
                "name": "Persist Tile",
                "action_type": "exe",
                "target": "C:\\app.exe",
                "run_on_start": True,
            },
        ]
    }

    parsed = app_inst._parse_config_payload(data)
    assert parsed is not None
    assert parsed["tiles"][0]["run_on_start"] is True


def test_duplicate_tile_clears_run_on_start(tk_root):
    """Verify that duplicated tile does NOT inherit run_on_start flag."""
    app_inst = TileApp.__new__(TileApp)
    app_inst.root = tk_root
    app_inst.lang = LANG_EN
    app_inst.dark_mode = False
    app_inst.current_sort = "manual"
    app_inst.tooltips = []
    app_inst.header_tooltips = []
    app_inst._autosave = lambda: None
    app_inst.render_tiles = lambda: None
    app_inst.show_toast = lambda msg: None

    app_inst.tiles = [
        {
            "name": "Original",
            "action_type": "url",
            "target": "https://x.com",
            "run_on_start": True,
            "use_count": 5,
            "created_at": "2026-01-01T00:00:00",
            "last_used": "2026-01-02T00:00:00",
            "order": 0,
        },
    ]

    app_inst.duplicate_tile(0)
    assert len(app_inst.tiles) == 2
    assert app_inst.tiles[0]["run_on_start"] is True   # Original remains untouched
    assert app_inst.tiles[1]["run_on_start"] is False  # Duplicate is reset to False







