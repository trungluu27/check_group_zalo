# Testing & Deployment Guide

## Running Tests

### Unit Tests

Run all unit tests:
```bash
# Activate virtual environment first
source venv/bin/activate

# Run tests
python tests/run_tests.py
```

Run specific test modules:
```bash
python tests/test_excel_reader.py
python tests/test_excel_writer.py
python tests/test_comparator.py
```

### Manual Testing Checklist

#### Before Testing
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] Playwright browsers installed
- [ ] Sample Excel file prepared
- [ ] Valid Zalo group URL available

#### Test Cases

1. **Excel File Handling**
   - [ ] Load .xlsx file successfully
   - [ ] Load .xls file successfully
   - [ ] Handle missing file gracefully
   - [ ] Auto-detect username column
   - [ ] Handle empty Excel file

2. **UI Functionality**
   - [ ] File selection dialog works
   - [ ] Group URL input accepts valid URLs
   - [ ] Start button validates inputs
   - [ ] Progress bar shows activity
   - [ ] Status messages display correctly

3. **Web Scraping**
   - [ ] Browser launches successfully
   - [ ] Login prompt appears
   - [ ] Navigate to group after login
   - [ ] Scrape members with scroll automation
   - [ ] Handle large groups (100+ members)
   - [ ] Browser closes after completion

4. **Comparison Logic**
   - [ ] Exact matching finds correct matches
   - [ ] Fuzzy matching handles variations
   - [ ] Case-insensitive comparison works
   - [ ] Threshold adjustment affects results
   - [ ] Empty lists handled gracefully

5. **Output Generation**
   - [ ] Excel file created in output directory
   - [ ] Missing Members sheet contains correct data
   - [ ] Metadata sheet includes all info
   - [ ] File opens without errors

6. **Error Handling**
   - [ ] Invalid file format shows error
   - [ ] Missing URL shows warning
   - [ ] Login timeout handled gracefully
   - [ ] Network errors logged
   - [ ] Browser crash recovery

## Performance Testing

### Small Group Test (< 50 members)
- Expected time: 2-5 minutes
- Memory usage: < 200 MB
- Success rate: > 95%

### Medium Group Test (50-200 members)
- Expected time: 5-15 minutes
- Memory usage: < 500 MB
- Success rate: > 90%

### Large Group Test (200+ members)
- Expected time: 15-30 minutes
- Memory usage: < 1 GB
- Success rate: > 85%

## Deployment

### Option 1: Source Distribution (Recommended for Development)

Share the entire project folder with:
```
check_group_zalo/
├── src/
├── requirements.txt
├── setup.sh
├── run.sh
└── README.md
```

Users run:
```bash
./setup.sh
./run.sh
```

### Option 2: PyInstaller (Standalone Executable)

Create a standalone macOS application:

1. **Install PyInstaller**:
```bash
pip install pyinstaller
```

2. **Create spec file**:
```bash
pyi-makespec --onefile --windowed --name "ZaloGroupChecker" src/main.py
```

3. **Edit ZaloGroupChecker.spec**:
```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config.json', '.'),
        ('resources', 'resources'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'playwright',
        'pandas',
        'openpyxl',
        'fuzzywuzzy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ZaloGroupChecker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='ZaloGroupChecker.app',
    icon=None,
    bundle_identifier='com.yourname.zalogroupchecker',
)
```

4. **Build the application**:
```bash
pyinstaller ZaloGroupChecker.spec
```

5. **Find the app**:
```bash
open dist/
# ZaloGroupChecker.app will be in the dist folder
```

6. **Distribute**:
   - Compress the .app file
   - Share with users
   - Users need to install Playwright separately:
     ```bash
     playwright install chromium
     ```

### Option 3: DMG Package (Professional Distribution)

Create a disk image for easy installation:

1. **Install create-dmg**:
```bash
brew install create-dmg
```

2. **Create DMG**:
```bash
create-dmg \
  --volname "Zalo Group Checker" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "ZaloGroupChecker.app" 200 190 \
  --hide-extension "ZaloGroupChecker.app" \
  --app-drop-link 600 185 \
  "ZaloGroupChecker.dmg" \
  "dist/"
```

## Troubleshooting Deployment Issues

### PyInstaller Issues

**Problem**: ModuleNotFoundError after building
**Solution**: Add missing modules to `hiddenimports` in spec file

**Problem**: Large executable size (> 100 MB)
**Solution**: Expected due to bundled dependencies. Use UPX compression.

**Problem**: App crashes on startup
**Solution**: Run from terminal to see error messages:
```bash
./dist/ZaloGroupChecker.app/Contents/MacOS/ZaloGroupChecker
```

### Playwright Issues

**Problem**: Browser not found in packaged app
**Solution**: Users must install Playwright browsers separately:
```bash
playwright install chromium
```

**Problem**: Permission denied on macOS
**Solution**: System Preferences > Security & Privacy > Allow

## Distribution Checklist

Before distributing to users:

- [ ] Test on clean macOS system
- [ ] Verify all dependencies included
- [ ] Check file permissions (chmod +x for scripts)
- [ ] Test with various Excel file formats
- [ ] Verify output directory creation
- [ ] Test error handling
- [ ] Update version numbers
- [ ] Create release notes
- [ ] Prepare user documentation
- [ ] Test installation process

## Maintenance

### Regular Updates

1. **Update Dependencies**:
```bash
pip install --upgrade -r requirements.txt
```

2. **Update Playwright**:
```bash
playwright install --force chromium
```

3. **Test After Updates**:
```bash
python tests/run_tests.py
```

### Monitoring

Check logs regularly:
```bash
tail -f logs/app.log
```

### User Feedback

Collect feedback on:
- Performance issues
- UI improvements
- Feature requests
- Bug reports

## Security Considerations

- ✅ No credentials stored in code
- ✅ All data processed locally
- ✅ No external API calls (except Zalo Web)
- ✅ Secure browser session handling
- ⚠️ Users responsible for their Zalo credentials
- ⚠️ Respect Zalo's terms of service

## Support

Provide users with:
1. README.md
2. QUICKSTART.md
3. Sample Excel file
4. Contact information for support

---

**Last Updated**: 2026-02-12
