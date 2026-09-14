# Changelog

All notable changes to the WinTiles project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.0] - 2026-09-14

### Security & Privacy Audit
- **Default Configuration Sanitization (`tiles.json`)**:
  - Removed all personal paths, local user directories, private scripts, Chrome profiles, and cloud project IDs from the repository.
  - Replaced default configuration with generic public example tiles (Google Search, WinTiles GitHub, PowerShell, System Notepad, Public Documents, Command Prompt, VS Code Workspace, Terminal in Folder, Sample Prompt, Google Web Search).
- **Test Data & Git Hygiene**:
  - Updated test file paths in `tests/test_app.py` to use generic placeholders (`C:\Users\Username\...`).
  - Extended `.gitignore` to cover temporary scratch files (`scratch/`), build outputs (`build/`, `dist/`), release archives (`release/`), and PyInstaller artifacts (`*.spec`, `*.exe`).

### Branding & Author Attribution
- **Creator Footer & GitHub Link**:
  - Added permanent author attribution in the application status bar: **👤 Michał Jura** with an interactive link to GitHub: [https://github.com/P3rgam0n](https://github.com/P3rgam0n).
  - Designed the status bar to react to theme switching (Dark/Light mode) and language selection (EN/PL) with tooltip feedback.

### Application Preview & Documentation
- **UI Screenshot (`assets/preview.png`)**:
  - Captured a clean application screenshot in English dark mode: `assets/preview.png`.
  - Embedded the preview image at the top of `README.md`.
- **English Documentation**:
  - Fully translated `README.md` and `CHANGELOG.md` to English for international distribution.

## [1.3.0] - 2026-09-11

### Added
- **Header Icon Tooltips**:
  - Added contextual tooltips when hovering over header buttons (Topmost **📌**, Dark Mode **🌙 / ☀️**, Clear Search **✕**, Add Tile, Save).
  - Tooltips dynamically adapt to active themes and languages (EN / PL).
- **Smooth Window Transparency (`Ctrl + Mouse Wheel`)**:
  - Added Ctrl + Mouse Wheel shortcut to adjust window opacity between 100% and 10% in 5% increments.
  - Added real-time percentage feedback on the status bar (e.g. `Window opacity: 85%`).
  - Opacity setting persists in `tiles.json` under `opacity`.
- **Automated Test Coverage**:
  - Added integration tests for header tooltips, language switching, and opacity control.

## [1.2.2] - 2026-09-11

### Fixed
- **Grid Layout Consistency**:
  - Cleared column weight configuration prior to re-rendering tiles to prevent empty space gaps.
  - Adjusted column calculation threshold to guarantee 4 columns in default window size (900x560 px) in both light and dark themes.

## [1.2.1] - 2026-09-11

### Fixed
- **Target Preview Formatting & Tooltip Pointer Tracking**:
  - Resolved subtitle truncation and tooltip positioning on Windows.

## [1.2.0] - 2026-09-11

### Added
- **WinTiles Rebranding & Consolidations**:
  - Rebranded application identifiers and configuration directory to WinTiles.
