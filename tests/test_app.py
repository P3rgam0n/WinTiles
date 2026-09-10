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
    """Verify get_target_preview formats short labels cleanly."""
    assert get_target_preview("url", "https://console.cloud.google.com/vertex-ai") == "console.cloud.google.com/..."
    assert get_target_preview("path", "C:\\Users\\cuksy\\Desktop\\MyFolder") == "MyFolder"
    assert get_target_preview("exe", "C:\\Tools\\App.exe") == "App.exe"
    assert get_target_preview("url", "https://google.com", description="Custom Desc") == "Custom Desc"


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
        assert len(tile_app.tiles) >= 14
        for tile in tile_app.tiles:
            assert tile["name"]
            assert tile["action_type"] in ACTION_DEFS
            assert "target" in tile
            assert "use_count" in tile
            assert "created_at" in tile
    finally:
        app.PRIMARY_CONFIG_FILE = old_primary
        app.FALLBACK_CONFIG_FILE = old_fallback
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
    monkeypatch.setattr(app.os, "startfile", lambda p: called.update({"startfile": p}))
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
    monkeypatch.setattr(app.os, "startfile", lambda p: called.update({"startfile": p}))
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


def test_drag_and_drop_gap_detection(tk_root, tmp_path):
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
        sub_top.update()
        card0 = tile_app.rendered_cards[0]["card"]
        card1 = tile_app.rendered_cards[1]["card"]
        r0 = (card0.winfo_rootx(), card0.winfo_rooty(), card0.winfo_width(), card0.winfo_height())
        r1 = (card1.winfo_rootx(), card1.winfo_rooty(), card1.winfo_width(), card1.winfo_height())

        # Midpoint in horizontal gap between card 0 and card 1
        gap_x = (r0[0] + r0[2] + r1[0]) // 2
        mid_y = r0[1] + r0[3] // 2

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
    monkeypatch.setattr(app.os, "startfile", lambda p: called.update({"startfile": p}))

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
    monkeypatch.setattr(app.sys, "executable", "D:\\Git\\kafelki\\dist\\app.exe")

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


def test_tooltip_suppressed_when_minimized(tk_root, tmp_path):
    """Verify Tooltip.show does not pop up if the toplevel window is minimized or not normal."""
    sub_top = tk.Toplevel(tk_root)
    lbl = tk.Label(sub_top, text="info")
    lbl.pack()
    sub_top.update()

    tt = app.Tooltip(lbl, lambda: "Tip content")

    # Iconify window
    sub_top.iconify()
    sub_top.update()

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


