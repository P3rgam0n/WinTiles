# Changelog

All notable changes to the WinTiles project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.5.0] - 2026-10-13

### Added
- **System Startup & Autostart Toggle Button (`🚀`)**:
  - Full operating system autostart integration allowing users to toggle whether WinTiles launches automatically on system boot.
  - Native Windows Registry integration (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`) supporting both packaged standalone executables (`WinTiles.exe`) and Python source execution (`pythonw.exe` / `python.exe`).
  - Cross-platform support for Linux via XDG Autostart desktop entry specification (`~/.config/autostart/WinTiles.desktop`).
  - Modern, responsive header toolbar button (`🚀`) with distinct visual feedback:
    - **Active state**: Emerald green container (`#064e3b` / `#34d399` in dark mode, `#ecfdf5` / `#059669` in light mode) with high-visibility accent border.
    - **Inactive state**: Clean neutral surface style matching other toolbar buttons.
  - Multi-faceted control mechanisms:
    - **Single Click**: Instant toggle between enabled and disabled with instant toast notifications.
    - **Right Click**: Context popup menu for direct explicit selection ("Enable start on system boot" / "Disable start on system boot").
    - **Global Keyboard Shortcut**: `Ctrl + B` for rapid toggling.
  - Integration with Click-Locked HUD mode (prevents accidental modification when locked).
  - Contextual hover tooltips dynamically indicating current autostart status and toggle instructions in both Polish and English.
  - Full configuration persistence in `tiles.json` (`"autostart": true/false`) with legacy configuration backward-compatibility.
- **Automated Tests**:
  - Added comprehensive test suite with 8 new unit and integration tests covering command line formatting, Linux desktop file lifecycle, Windows registry operations with mocks, OS dispatchers, UI toggle, theme parity, lock protection, and error handling (52 total passing tests).

## [1.1.0] - 2026-10-11

### Added
- **Minimalist Smart Window Lock & Protection (Tri-State Button)**:
  - Multi-state intelligent locking combining window pinning and click-protection in a single minimalist control without extra buttons.
  - Three distinct operating modes:
    - `Standard Window` (`📌` Neutral Gray) – standard Z-order and full interactivity.
    - `Always on Top` (`📌` Sky Blue / Cyan) – pinned on top with full interactivity.
    - `Click-Locked HUD` (`🔒` Amber Gold) – pinned on top with click protection (tiles cannot be clicked, dragged, or edited accidentally, creating a safe reference HUD overlay).
  - Diverse interaction triggers:
    - **Single Click**: cycles modes (`Standard` ➔ `Always on Top` ➔ `Click-Locked` ➔ `Standard`).
    - **Double Click**: fast-toggle shortcut directly between `Standard` and `Click-Locked`.
    - **Right Click**: context popup menu for direct mode selection.
    - **Global Keyboard Shortcut**: `Ctrl + L` for rapid mode switching from anywhere.
  - Informative toast feedback when clicking protected tiles or changing modes.
  - Dynamic status bar hints and context-aware tooltips in both Polish and English.
  - Full backward and forward compatibility in `tiles.json` configuration parsing and serialization.
- **Automated Tests**:
  - Expanded test suite with unit and integration tests covering cycling, double-click shortcuts, tile protection, theme parity, and configuration migration.

## [1.0.1] - 2026-09-15

### Added
- **Standalone Windows Executable**:
  - Automated build script (`build_exe.py`) packaging standalone `WinTiles.exe` and release archives.
  - Multi-resolution Windows application icon (`assets/icon.ico`).
  - GitHub Actions CI/CD release workflow for automatic `.exe` publication upon tag push.
- **Documentation**:
  - Direct download instructions and release section in `README.md`.

## [1.0.0] - 2026-09-14

### Added
- **Initial Public Release** of WinTiles desktop productivity launcher for Windows 11.
- **14 Supported Action Types**:
  - `url` – Open web pages in default browser.
  - `path` – Open folders in Windows Explorer.
  - `file` – Open documents or files in default applications.
  - `exe` – Run executable files (`.exe`).
  - `ps1` – Execute PowerShell scripts (`.ps1`).
  - `python` – Execute Python scripts (`.py`).
  - `bat` – Execute batch files (`.bat` / `.cmd`).
  - `terminal` – Launch Windows Terminal or PowerShell in a specific directory.
  - `vscode` – Open files or folders directly in Visual Studio Code.
  - `wsl` – Run Linux commands or bash shells via WSL.
  - `clipboard` – Copy prompts, templates, or tokens to the clipboard with toast feedback.
  - `websearch` – Execute Google web searches directly in browser.
  - `chrome_profile` – Launch or switch to specific Google Chrome profiles.
  - `command` – Execute custom Windows shell commands.
- **Interactive UI & Drag & Drop**:
  - Drag & Drop tile reordering with semi-transparent drag preview.
  - Tile descriptions with hover info tooltips („ⓘ”).
  - Real-time live search filter by tile name, action type, target path, or description.
  - Smooth window opacity adjustment via `Ctrl + Mouse Wheel` (100% to 10%).
  - Dark and Light theme support with native Windows 11 DWM title bar integration.
  - Bilingual interface support (English & Polish).
- **Quality & Security**:
  - Fully sanitized default configuration with public example tiles.
  - Comprehensive automated unit test suite.
