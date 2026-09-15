# Changelog

All notable changes to the WinTiles project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
- **Standalone Windows Executable**:
  - Automated build script (`build_exe.py`) packaging standalone `WinTiles.exe` and release archives.
  - Multi-resolution Windows application icon (`assets/icon.ico`).
  - GitHub Actions CI/CD release workflow for automatic `.exe` publication upon tag push.
- **Quality & Security**:
  - Fully sanitized default configuration with public example tiles.
  - Comprehensive automated unit test suite.
