import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
DIST_DIR = REPO_ROOT / "dist"
BUILD_DIR = REPO_ROOT / "build"
RELEASE_DIR = REPO_ROOT / "release"
ASSETS_DIR = REPO_ROOT / "assets"
ICON_PNG = ASSETS_DIR / "icon.png"
ICON_ICO = ASSETS_DIR / "icon.ico"
VERSION_FILE = REPO_ROOT / "VERSION"


def ensure_icon():
    """Ensure icon.ico exists; generate from icon.png if needed."""
    if ICON_ICO.exists():
        print(f"[OK] Found icon: {ICON_ICO}")
        return True
    if ICON_PNG.exists():
        print(f"[INFO] Generating icon.ico from {ICON_PNG}...")
        try:
            from PIL import Image

            img = Image.open(ICON_PNG)
            img.save(
                ICON_ICO,
                format="ICO",
                sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
            )
            print(f"[OK] Generated: {ICON_ICO}")
            return True
        except Exception as exc:
            print(f"[WARN] Failed to generate icon.ico with PIL: {exc}")
            return False
    return False


def get_version():
    """Read version string from VERSION file."""
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "v1.0.0"


def build_executable():
    """Run PyInstaller to create standalone WinTiles.exe."""
    print("=" * 60)
    print("Building WinTiles Standalone Executable (.exe)")
    print("=" * 60)

    has_icon = ensure_icon()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconsole",
        "--onefile",
        "--name",
        "WinTiles",
        "--clean",
        "--add-data",
        f"{ASSETS_DIR}{os.pathsep}assets",
    ]

    if (REPO_ROOT / "tiles.json").exists():
        cmd.extend(["--add-data", f"{REPO_ROOT / 'tiles.json'}{os.pathsep}."])

    if has_icon and ICON_ICO.exists():
        cmd.extend(["--icon", str(ICON_ICO)])

    cmd.append(str(REPO_ROOT / "app.py"))

    print(f"Executing: {' '.join(cmd)}\n")
    result = subprocess.run(cmd, cwd=str(REPO_ROOT), check=False)

    if result.returncode != 0:
        print(f"\n[ERROR] PyInstaller build failed with exit code {result.returncode}")
        return False

    exe_path = DIST_DIR / "WinTiles.exe"
    if not exe_path.exists():
        print(f"\n[ERROR] Output executable not found at: {exe_path}")
        return False

    exe_size_mb = exe_path.stat().st_size / (1024 * 1024)
    print(f"\n[SUCCESS] Built: {exe_path} ({exe_size_mb:.2f} MB)")

    # Prepare release package
    RELEASE_DIR.mkdir(parents=True, exist_ok=True)
    version = get_version()
    dest_exe = RELEASE_DIR / "WinTiles.exe"
    shutil.copy2(exe_path, dest_exe)

    zip_name = f"WinTiles-{version}-windows-x64.zip"
    zip_path = RELEASE_DIR / zip_name
    print(f"[INFO] Creating release archive: {zip_path}...")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(dest_exe, arcname="WinTiles.exe")
        if (REPO_ROOT / "README.md").exists():
            zf.write(REPO_ROOT / "README.md", arcname="README.md")
        if (REPO_ROOT / "CHANGELOG.md").exists():
            zf.write(REPO_ROOT / "CHANGELOG.md", arcname="CHANGELOG.md")
        if (REPO_ROOT / "tiles.json").exists():
            zf.write(REPO_ROOT / "tiles.json", arcname="tiles.sample.json")

    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"[SUCCESS] Release archive ready: {zip_path} ({zip_size_mb:.2f} MB)")
    print("=" * 60)
    print("Ready to upload to GitHub Releases!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)
