#!/usr/bin/env python3
"""Build script to create a standalone Windows executable using PyInstaller."""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*70}")
    print(f"  {text}")
    print(f"{'='*70}\n")


def print_step(text):
    """Print a step message."""
    print(f"✓ {text}")


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n→ {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error: {e}")
        if e.stderr:
            print(e.stderr)
        return False


def main():
    """Build the standalone Windows executable."""
    print_header("Power BI Theme Creator - Windows EXE Builder")

    # Check if we're on Windows
    if sys.platform != "win32":
        print("⚠ Note: Building on Linux/Mac for Windows deployment")
        print("  The executable will work on Windows.")
        print("  (For production builds, use Windows machine for best compatibility)")

    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ required")
        return 1
    print_step(f"Python {sys.version_info.major}.{sys.version_info.minor} detected")

    # Check if build_exe.spec exists
    spec_file = Path("build_exe.spec")
    if not spec_file.exists():
        print("✗ build_exe.spec not found in current directory")
        print("  Make sure you're in the project root directory")
        return 1
    print_step("Found build_exe.spec")

    # Check if main.py exists
    if not Path("main.py").exists():
        print("✗ main.py not found in current directory")
        return 1
    print_step("Found main.py")

    # Install PyInstaller
    print_step("Checking PyInstaller installation...")
    if not run_command(
        "python -m pip install -q pyinstaller",
        "Installing PyInstaller"
    ):
        print("✗ Failed to install PyInstaller")
        return 1

    # Clean old builds
    print_step("Cleaning old builds...")
    for folder in ["build", "dist"]:
        if Path(folder).exists():
            shutil.rmtree(folder)
            print(f"  Removed {folder}/")

    # Run PyInstaller
    print_header("Building Executable")
    if not run_command(
        f"pyinstaller build_exe.spec",
        "Running PyInstaller"
    ):
        print("✗ PyInstaller build failed")
        return 1

    # Check if exe was created (name differs by platform)
    exe_candidates = [
        Path("dist/PowerBI_Theme_Creator.exe"),  # Windows
        Path("dist/PowerBI_Theme_Creator"),      # Linux/Mac
    ]
    exe_file = next((f for f in exe_candidates if f.exists()), None)
    if not exe_file:
        print("✗ Executable not created")
        return 1

    # On Linux/Mac, rename to .exe for consistency
    if sys.platform != "win32" and exe_file.suffix != ".exe":
        exe_renamed = exe_file.with_suffix(".exe")
        exe_file.rename(exe_renamed)
        exe_file = exe_renamed

    # Get file size
    exe_size_mb = exe_file.stat().st_size / (1024 * 1024)

    print_header("Build Complete! ✅")
    print(f"📦 Executable created: {exe_file}")
    print(f"📏 File size: {exe_size_mb:.1f} MB")
    print(f"\n📁 Entire dist folder (with all dependencies):")
    dist_size_mb = sum(
        f.stat().st_size for f in Path("dist").rglob("*") if f.is_file()
    ) / (1024 * 1024)
    print(f"   Total size: {dist_size_mb:.1f} MB")

    print(f"\n✨ Next steps:")
    print(f"   1. Test the exe: dist/PowerBI_Theme_Creator.exe")
    print(f"   2. Verify it works on your target Windows machine")
    print(f"   3. Zip the 'dist/' folder for distribution")
    print(f"   4. Share dist/PowerBI_Theme_Creator.exe with others")

    print(f"\n📋 What's included:")
    print(f"   • Python runtime (bundled)")
    print(f"   • PySide6 (GUI framework)")
    print(f"   • All application code")
    print(f"   • All dependencies")
    print(f"   • No Python installation needed on target machine!")

    print(f"\n📖 For more details, see: build_windows_exe.md")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Build cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
