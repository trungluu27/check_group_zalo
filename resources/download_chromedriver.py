"""
Download the correct ChromeDriver binary for bundling into the app.

This script:
1. Detects the Chrome version installed on the build machine
2. Downloads the matching ChromeDriver binary from Google's CDN
3. Places it in resources/chromedriver/ for PyInstaller to bundle

Run this script ONCE before building with PyInstaller:
    python resources/download_chromedriver.py

Requirements: pip install requests (already included via selenium dependency chain)
"""

import os
import sys
import platform
import zipfile
import shutil
import urllib.request
import json
import subprocess
from pathlib import Path


OUTPUT_DIR = Path(__file__).parent / "chromedriver"

# ChromeDriver JSON API endpoint (Chrome for Testing)
CFT_API = "https://googlechromelabs.github.io/chrome-for-testing/known-good-versions-with-downloads.json"
# Latest stable release info
LATEST_API = "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"


def get_platform_key() -> str:
    system = platform.system()
    machine = platform.machine().lower()
    if system == "Windows":
        return "win64" if "64" in machine or machine == "amd64" else "win32"
    elif system == "Darwin":
        return "mac-arm64" if machine == "arm64" else "mac-x64"
    else:
        return "linux64"


def get_chrome_version_windows() -> str:
    import subprocess
    try:
        result = subprocess.run(
            ["reg", "query",
             r"HKEY_CURRENT_USER\Software\Google\Chrome\BLBeacon",
             "/v", "version"],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if "version" in line.lower():
                return line.strip().split()[-1]
    except Exception:
        pass
    # Fallback: check common install paths
    paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for p in paths:
        if Path(p).exists():
            import subprocess
            result = subprocess.run(
                ["powershell", "-command",
                 f"(Get-Item '{p}').VersionInfo.FileVersion"],
                capture_output=True, text=True
            )
            ver = result.stdout.strip()
            if ver:
                return ver
    return None


def get_chrome_version_macos() -> str:
    import subprocess
    paths = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for p in paths:
        if Path(p).exists():
            result = subprocess.run([p, "--version"], capture_output=True, text=True)
            parts = result.stdout.strip().split()
            if parts:
                return parts[-1]
    return None


def get_chrome_version_linux() -> str:
    import subprocess
    for cmd in [["google-chrome", "--version"], ["chromium-browser", "--version"], ["chromium", "--version"]]:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            parts = result.stdout.strip().split()
            if parts:
                return parts[-1]
        except Exception:
            continue
    return None


def get_chrome_major_version() -> int:
    system = platform.system()
    ver = None
    if system == "Windows":
        ver = get_chrome_version_windows()
    elif system == "Darwin":
        ver = get_chrome_version_macos()
    else:
        ver = get_chrome_version_linux()

    if ver:
        try:
            major = int(ver.split(".")[0])
            print(f"[INFO] Detected Chrome version: {ver} (major: {major})")
            return major
        except Exception:
            pass

    print("[WARNING] Could not detect Chrome version. Using latest stable ChromeDriver.")
    return None


def fetch_json(url: str) -> dict:
    print(f"[INFO] Fetching: {url}")
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode())


def is_expected_binary_format(binary_path: Path, platform_key: str) -> bool:
    """
    Validate downloaded chromedriver header for target platform.
    Prevents bundling HTML/error files or wrong-OS executables.
    """
    try:
        with open(binary_path, "rb") as f:
            magic = f.read(4)
    except Exception:
        return False

    if platform_key.startswith("mac"):
        # Prefer system `file` output on macOS to avoid false negatives with
        # newer universal/fat variants.
        try:
            result = subprocess.run(
                ["file", str(binary_path)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            file_out = (result.stdout or "") + (result.stderr or "")
            if "Mach-O" in file_out:
                return True
        except Exception:
            pass

        mach_o_magics = {
            b"\xfe\xed\xfa\xce",
            b"\xce\xfa\xed\xfe",
            b"\xfe\xed\xfa\xcf",
            b"\xcf\xfa\xed\xfe",
            b"\xca\xfe\xba\xbe",
            b"\xbe\xba\xfe\xca",
            b"\xca\xfe\xba\xbf",
            b"\xbf\xba\xfe\xca",
        }
        return magic in mach_o_magics
    if platform_key.startswith("linux"):
        return magic == b"\x7fELF"
    if platform_key.startswith("win"):
        return magic[:2] == b"MZ"
    return True


def find_chromedriver_url(major_version: int, platform_key: str) -> str:
    # Use latest stable if no version detected
    if major_version is None:
        data = fetch_json(LATEST_API)
        downloads = data["channels"]["Stable"]["downloads"].get("chromedriver", [])
        for item in downloads:
            if item["platform"] == platform_key:
                return item["url"]
        raise RuntimeError(f"No stable ChromeDriver found for platform: {platform_key}")

    # Find the best matching version from known-good list
    data = fetch_json(CFT_API)
    best_url = None
    best_ver = None

    for entry in data["versions"]:
        ver_str = entry.get("version", "")
        try:
            entry_major = int(ver_str.split(".")[0])
        except Exception:
            continue

        if entry_major != major_version:
            continue

        downloads = entry.get("downloads", {}).get("chromedriver", [])
        for item in downloads:
            if item["platform"] == platform_key:
                best_url = item["url"]
                best_ver = ver_str
                break  # take last matching (they're ordered ascending)

    if not best_url:
        # Fall back to latest stable
        print(f"[WARNING] No ChromeDriver for Chrome {major_version}. Using latest stable.")
        return find_chromedriver_url(None, platform_key)

    print(f"[INFO] Found ChromeDriver {best_ver} for {platform_key}")
    return best_url


def download_chromedriver(url: str, platform_key: str) -> Path:
    zip_path = OUTPUT_DIR / "chromedriver_download.zip"
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR, ignore_errors=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Downloading ChromeDriver from: {url}")
    urllib.request.urlretrieve(url, zip_path)
    print(f"[INFO] Downloaded {zip_path.stat().st_size // 1024} KB")

    # Extract the binary
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        # Find chromedriver binary inside zip
        binary_name = "chromedriver.exe" if "win" in platform_key else "chromedriver"
        target_name = None
        for name in names:
            if name.endswith(binary_name) and not name.endswith("/"):
                target_name = name
                break

        if not target_name:
            raise RuntimeError(f"chromedriver binary not found in zip. Contents: {names}")

        # Extract to OUTPUT_DIR
        with zf.open(target_name) as src:
            dest = OUTPUT_DIR / binary_name
            with open(dest, "wb") as dst:
                dst.write(src.read())
        print(f"[INFO] Extracted: {dest}")

    # Remove zip
    zip_path.unlink()

    # Set executable permission on Unix
    if platform_key != "win64" and platform_key != "win32":
        dest = OUTPUT_DIR / "chromedriver"
        dest.chmod(0o755)

    dest = OUTPUT_DIR / binary_name
    if not is_expected_binary_format(dest, platform_key):
        raise RuntimeError(
            f"Downloaded chromedriver has unexpected binary format for {platform_key}: {dest}"
        )

    return OUTPUT_DIR


def main():
    print("=" * 50)
    print(" ChromeDriver Downloader for PyInstaller Bundle")
    print("=" * 50)
    print()

    platform_key = get_platform_key()
    print(f"[INFO] Build platform: {platform_key}")

    major_version = get_chrome_major_version()

    try:
        url = find_chromedriver_url(major_version, platform_key)
        output = download_chromedriver(url, platform_key)
        print()
        print(f"[OK] ChromeDriver saved to: {output}")
        print(f"     Files: {list(output.iterdir())}")
        print()
        print("ChromeDriver is ready to be bundled by PyInstaller.")
        print("Run your build script now.")
    except Exception as e:
        print(f"\n[ERROR] Failed to download ChromeDriver: {e}")
        print("\nAlternative: install webdriver-manager and the app will")
        print("download ChromeDriver automatically on first run.")
        sys.exit(1)


if __name__ == "__main__":
    main()
