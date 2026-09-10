# Building a Standalone Windows Executable

This guide explains how to create a standalone `.exe` file for Windows that requires no Python installation.

## Prerequisites

- **Windows 10/11**
- **Python 3.12+** (only needed during build, not on target machine)
- **PyInstaller** (installed automatically below)

## Quick Start

### Option 1: Automated Build Script (Recommended)

On Windows, run:

```bash
python build_windows_exe.py
```

This will:
1. Clean old builds
2. Install PyInstaller
3. Build the standalone executable
4. Create `dist/PowerBI_Theme_Creator.exe`

### Option 2: Manual Build

```bash
# Install PyInstaller
pip install pyinstaller

# Build the exe
pyinstaller build_exe.spec

# Result: dist/PowerBI_Theme_Creator.exe
```

## Output

After building, you'll have:

```
dist/
├── PowerBI_Theme_Creator.exe    # ← Standalone executable (no Python needed!)
├── PySide6/                     # Dependencies bundled inside
├── pbitheme/                    # Application code bundled inside
└── [other files]
```

## Distribution

To distribute to others:

### Option A: Single EXE File
- Zip the entire `dist/` folder
- Share the zip file
- User extracts and runs `PowerBI_Theme_Creator.exe`
- **Size:** ~400-600 MB (includes all dependencies)

### Option B: Installer (Advanced)
Use NSIS or InnoSetup to create a professional installer.

## Running on Target Machine

1. Extract `PowerBI_Theme_Creator.exe`
2. Double-click to run
3. **No Python installation required!**
4. All dependencies are bundled inside

## Troubleshooting

### "PowerBI_Theme_Creator.exe not found"
- Make sure build completed successfully
- Check `dist/` folder exists
- Try building again: `pyinstaller build_exe.spec`

### "Missing dependency" error
- The spec file should include all dependencies
- If missing, add to `hiddenimports` list in `build_exe.spec`
- Rebuild: `pyinstaller build_exe.spec`

### File size too large
- Normal for Python apps with GUI libraries
- PyInstaller includes all dependencies
- Consider OneDrive/Dropbox for distribution

### Antivirus warnings
- PyInstaller executables sometimes trigger antivirus
- This is a known issue (false positive)
- You can:
  1. Whitelist the executable
  2. Code sign the executable (advanced)
  3. Host on trusted distribution platform

## Advanced Options

### Reduce File Size
Add to `build_exe.spec` in the EXE section:
```python
upx=True,  # Enable UPX compression (if installed)
```

### Single File Executable
Modify `build_exe.spec`:
```python
exe = EXE(
    # ... other args ...
    onefile=True,  # Create single .exe instead of folder
)
```

Note: Single file exe takes longer to start (unpacks on each launch)

### Custom Icon
Replace in `build_exe.spec`:
```python
icon='path/to/your/icon.ico',
```

Create an `.ico` file from a PNG:
```python
from PIL import Image
img = Image.open("icon.png")
img.save("icon.ico")
```

## File Structure

```
PowerBI_Theme_Creator/
├── main.py                    # Entry point
├── build_exe.spec             # PyInstaller config
├── build_windows_exe.py       # Build script
├── pbitheme/
│   ├── model.py               # Theme data model
│   ├── gui/
│   │   ├── main_window.py
│   │   ├── visual_formatter.py
│   │   └── ...
│   └── ...
└── dist/
    └── PowerBI_Theme_Creator.exe  # ← Your standalone exe!
```

## Performance Notes

- **First launch:** May take 2-3 seconds (unpacking dependencies)
- **Subsequent launches:** Fast (uses cached files)
- **Memory:** ~100-150 MB at runtime
- **Disk space:** ~400-600 MB (including all dependencies)

## Updating

To update the exe:
1. Update source code
2. Rebuild: `pyinstaller build_exe.spec`
3. Test new exe
4. Distribute new `PowerBI_Theme_Creator.exe`

## Next Steps

After building:
1. ✅ Test on Windows machine without Python
2. ✅ Verify all features work
3. ✅ Check file dialogs, color pickers work
4. ✅ Test with sample theme files
5. ✅ Zip and distribute

---

**Questions?** Check PyInstaller docs: https://pyinstaller.org/
