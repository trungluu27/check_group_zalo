# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies (First Time Only)

**On macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

**On Windows:**
```bash
setup.bat
```

**Or manually:**
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Step 2: Prepare Your Data

Create an Excel file (`.xlsx` or `.xls`) with a column containing Zalo usernames:

| username | email | notes |
|----------|-------|-------|
| John Doe | john@example.com | Manager |
| Jane Smith | jane@example.com | Developer |

**Note**: The column can be named: `username`, `name`, `user`, `ten`, or similar.

### Step 3: Run the Application

```bash
# Make sure virtual environment is activated
source venv/bin/activate  # macOS/Linux

# Run the app
python src/main.py
```

Or use the run script:
```bash
./run.sh  # macOS/Linux
```

### Step 4: Use the Application

1. **Click "📁 Select Excel File"** → Choose your Excel file
2. **Enter Zalo Group Link** → Paste the group URL (e.g., `https://chat.zalo.me/g/...`)
3. **Configure Options** (optional):
   - ✅ Use Fuzzy Matching (recommended)
   - Adjust threshold (85% default)
4. **Click "▶️ Start Checking"**
5. **Login to Zalo Web** when browser opens
6. **Wait** for the process to complete (5-30 minutes depending on group size)
7. **View results** in the app and in `output/missing_members.xlsx`

## 📋 What You'll Get

The app will create `output/missing_members.xlsx` with:
- **Sheet 1**: List of usernames NOT found in the group
- **Sheet 2**: Metadata (date, totals, group info)

## 🔍 Matching Options

### Exact Matching
- Fast but strict
- "John Doe" ≠ "Doe John"
- Case-insensitive

### Fuzzy Matching (Recommended)
- Handles typos and variations
- "John Doe" ≈ "Doe John" ≈ "john doe"
- Configurable threshold (85% = 85% similarity required)

## ⚡ Tips

- **Large Groups**: May take 10-30 minutes to scrape all members
- **Login**: You must manually login each time you run the app
- **Threshold**: Lower = more matches (but less accurate), Higher = fewer matches (but more accurate)
- **Logs**: Check `logs/app.log` for detailed information

## ❓ Common Issues

### "No members found"
- Verify the group URL is correct
- Check if you can access the group while logged in
- Zalo Web structure may have changed

### "Login timeout"
- Login within 5 minutes of browser opening
- Ensure stable internet connection

### "Column not found"
- Rename your Excel column to "username" or "name"
- Or ensure it contains "user" or "name" in the column header

## 📚 Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [plans/](plans/) folder for technical architecture
- Run tests: `python tests/run_tests.py`

---

**Need help?** Check `logs/app.log` for detailed error messages.
