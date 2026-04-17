# Hướng dẫn Bundle Playwright Browser vào .app

## Tổng quan

Có 2 cách build ứng dụng:

### Option 1: Không bundle browser (Nhẹ hơn)
- **Kích thước**: ~200-300MB
- **Ưu điểm**: App nhẹ, build nhanh
- **Nhược điểm**: User phải cài Playwright browsers
- **File**: [`ZaloGroupChecker.spec`](../ZaloGroupChecker.spec)
- **Script**: [`build_app.sh`](../build_app.sh)

### Option 2: Bundle browser (Khuyên dùng)
- **Kích thước**: ~500-700MB
- **Ưu điểm**: User không cần cài gì thêm, chạy ngay
- **Nhược điểm**: App nặng hơn, build lâu hơn
- **File**: [`ZaloGroupChecker_with_browser.spec`](../ZaloGroupChecker_with_browser.spec)
- **Script**: [`build_app_with_browser.sh`](../build_app_with_browser.sh)

## Cách Build với Browser Bundle

### Bước 1: Cài đặt Playwright browsers trước

```bash
# Activate virtual environment
source venv/bin/activate

# Install Playwright
pip install playwright

# Install Chromium browser
playwright install chromium
```

Browser sẽ được cài vào: `~/Library/Caches/ms-playwright/chromium-*/`

### Bước 2: Build app với browser

```bash
# Sử dụng script tự động
chmod +x build_app_with_browser.sh
./build_app_with_browser.sh
```

Hoặc thủ công:

```bash
# Build với spec file có browser
pyinstaller ZaloGroupChecker_with_browser.spec
```

### Bước 3: Kiểm tra

```bash
# Kiểm tra browser đã được bundle chưa
ls -la dist/ZaloGroupChecker.app/Contents/Resources/ms-playwright/

# Test app
open dist/ZaloGroupChecker.app
```

## Cách hoạt động

### 1. Spec File Configuration

File [`ZaloGroupChecker_with_browser.spec`](../ZaloGroupChecker_with_browser.spec) có:

```python
# Tìm Chromium browser
playwright_browsers = Path.home() / 'Library' / 'Caches' / 'ms-playwright'
chromium_dirs = list(playwright_browsers.glob('chromium-*'))

# Bundle vào app
browser_binaries = [(str(chromium_path), 'ms-playwright/chromium')]
```

### 2. Browser Manager Update

File [`src/scraper/browser_manager_bundled.py`](../src/scraper/browser_manager_bundled.py) tự động:

```python
def _setup_browser_path(self):
    if getattr(sys, 'frozen', False):
        # Running as bundled app
        bundle_dir = Path(sys._MEIPASS)
        browser_path = bundle_dir / 'ms-playwright' / 'chromium'
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(bundle_dir / 'ms-playwright')
```

## So sánh 2 phương pháp

| Tiêu chí | Không Bundle | Bundle Browser |
|----------|--------------|----------------|
| Kích thước .app | 200-300MB | 500-700MB |
| Kích thước .dmg | 100-150MB | 250-350MB |
| Thời gian build | 2-5 phút | 5-10 phút |
| User cần cài | Playwright | Không |
| Phù hợp | Developer | End user |

## Hướng dẫn cho End User

### Với Bundle Browser (Khuyên dùng)

```
HƯỚNG DẪN CÀI ĐẶT
==================

1. Tải file ZaloGroupChecker-1.0.0-bundled.dmg
2. Double-click để mở
3. Kéo ZaloGroupChecker.app vào Applications
4. Double-click để chạy
5. Xử lý cảnh báo "unidentified developer" (nếu có)

✅ KHÔNG CẦN cài Python
✅ KHÔNG CẦN cài Playwright
✅ Chạy ngay lập tức!
```

### Không Bundle Browser

```
HƯỚNG DẪN CÀI ĐẶT
==================

1. Tải file ZaloGroupChecker-1.0.0.dmg
2. Cài đặt app vào Applications
3. Cài Python 3.9+ (nếu chưa có)
4. Mở Terminal và chạy:
   pip3 install playwright
   playwright install chromium
5. Chạy app

⚠️ CẦN cài Python và Playwright
```

## Troubleshooting

### Browser không tìm thấy sau khi bundle

**Nguyên nhân**: Browser path không đúng

**Giải pháp**:
```bash
# Kiểm tra browser có trong app không
ls -la dist/ZaloGroupChecker.app/Contents/Resources/ms-playwright/

# Nếu không có, rebuild với:
playwright install chromium
./build_app_with_browser.sh
```

### App quá nặng

**Giải pháp 1**: Dùng version không bundle
```bash
./build_app.sh
```

**Giải pháp 2**: Compress DMG tốt hơn
```bash
# Sử dụng compression cao hơn khi tạo DMG
hdiutil create -volname "Zalo Checker" -srcfolder dist/ZaloGroupChecker.app \
  -ov -format UDZO -imagekey zlib-level=9 ZaloGroupChecker.dmg
```

### Permission errors

```bash
# Fix permissions
chmod -R 755 dist/ZaloGroupChecker.app
xattr -cr dist/ZaloGroupChecker.app
```

## Best Practices

### Cho Distribution

1. **Bundle browser** cho end users (dễ dùng nhất)
2. **Tạo DMG** với background đẹp
3. **Code sign** nếu có Apple Developer Account
4. **Notarize** cho macOS 10.15+
5. **Test** trên máy sạch trước khi phát hành

### Cho Development

1. **Không bundle** browser (build nhanh)
2. **Cài Playwright** locally
3. **Test** với `python src/main.py`

## Kết luận

**Khuyến nghị**: Sử dụng **bundle browser** cho end users để trải nghiệm tốt nhất!

```bash
# Build lần cuối cho distribution
./build_app_with_browser.sh

# Distribute file này
dist/ZaloGroupChecker-1.0.0-bundled.dmg
```

Users chỉ cần:
1. Download DMG
2. Install app
3. Run!

Không cần cài Python, Playwright hay bất cứ thứ gì khác! 🎉
