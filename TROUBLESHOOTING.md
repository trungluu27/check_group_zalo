# Troubleshooting Guide

## Pandas Installation Error on Windows

If you encounter the error `Failed to build 'pandas' when installing build dependencies for pandas`, try these solutions in order:

### Solution 1: Upgrade pip and setuptools (Recommended First Step)

```bash
python -m pip install --upgrade pip setuptools wheel
```

Then try installing requirements again:
```bash
pip install -r requirements.txt
```

### Solution 2: Install pandas separately with pre-built wheel

```bash
pip install pandas==2.1.4 --only-binary :all:
```

Then install the rest:
```bash
pip install -r requirements.txt
```

### Solution 3: Use conda instead of pip (Highly Recommended for Windows)

If you have Anaconda or Miniconda installed:

```bash
# Create conda environment
conda create -n zalo_checker python=3.11

# Activate environment
conda activate zalo_checker

# Install pandas and other scientific packages via conda
conda install pandas openpyxl

# Install remaining packages via pip
pip install playwright PyQt6 fuzzywuzzy python-Levenshtein xlrd
```

### Solution 4: Install Microsoft C++ Build Tools

If you need to build from source, install:
- Download and install [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
- During installation, select "Desktop development with C++"
- Restart your terminal and try again

### Solution 5: Use older pandas version

Edit [`requirements.txt`](requirements.txt) and change pandas version:

```txt
pandas==2.0.3  # Instead of 2.1.4
```

Then:
```bash
pip install -r requirements.txt
```

## Platform-Specific Notes

### Windows Development
This project is designed for macOS deployment, but you can develop on Windows:

1. **Use conda** for easier dependency management
2. **Testing limitations**: PyInstaller .app bundles can only be created on macOS
3. **Alternative**: Use PyInstaller to create .exe for Windows testing, then build .app on macOS

### macOS Development
If you're on macOS and seeing this error:

```bash
# Install Xcode Command Line Tools first
xcode-select --install

# Then install requirements
pip install -r requirements.txt
```

## Quick Start After Fixing Installation

Once dependencies are installed:

```bash
# Install Playwright browsers
playwright install chromium

# Run the application
python src/main.py
```

## Still Having Issues?

1. **Check Python version**: Ensure you're using Python 3.9 or higher
   ```bash
   python --version
   ```

2. **Create fresh virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies one by one** to identify the problematic package:
   ```bash
   pip install playwright
   pip install openpyxl
   pip install pandas  # This is where it fails
   pip install PyQt6
   pip install fuzzywuzzy
   pip install python-Levenshtein
   pip install xlrd
   ```

## Alternative: Docker Development (Advanced)

If all else fails, you can develop in a Docker container:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install chromium --with-deps

COPY . .
CMD ["python", "src/main.py"]
```

## Contact

If you continue to experience issues, please provide:
- Your Python version (`python --version`)
- Your pip version (`pip --version`)
- Your operating system
- Full error message
