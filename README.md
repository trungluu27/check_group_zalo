# Zalo Group Membership Checker

A Python desktop application for macOS that checks whether Zalo usernames from an Excel file are members of a specified Zalo group.

## Features

- ✅ **User-friendly GUI** built with PyQt6
- 📁 **Excel file support** (.xlsx and .xls formats)
- 🌐 **Web automation** using Playwright to scrape Zalo group members
- 🔍 **Smart matching** with both exact and fuzzy name comparison
- 💾 **Excel output** with detailed results
- 📊 **Real-time progress** tracking
- 🔐 **Manual login** support for Zalo Web authentication

## Prerequisites

- **macOS** 11.0 or higher
- **Python** 3.9 or higher
- **pip** package manager

## Installation

### 1. Clone or Download the Project

```bash
cd check_group_zalo
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

```bash
playwright install chromium
```

## Usage

### Running the Application

```bash
python src/main.py
```

### Step-by-Step Guide

1. **Select Excel File**
   - Click the "📁 Select Excel File" button
   - Choose your Excel file containing usernames
   - The file should have a column with Zalo usernames (e.g., "username", "name", "user")

2. **Enter Group Link**
   - Paste the Zalo group URL in the text field
   - Format: `https://chat.zalo.me/g/...`

3. **Configure Options** (Optional)
   - Toggle "Use Fuzzy Matching" for flexible name comparison
   - Adjust "Matching Threshold" (default: 85%)

4. **Start Process**
   - Click "▶️ Start Checking"
   - A browser window will open
   - **First time only:** Manually login to Zalo Web when prompted
   - **Next times:** Session is automatically restored (no login needed!)
   - Wait for the scraping to complete (may take several minutes)

5. **View Results**
   - Results will be displayed in the application
   - Output file saved to: `output/missing_members.xlsx`

### 🔐 Login Session Management

**Persistent Session Feature:**
- ✅ Login **once** and your session is saved
- ✅ No need to re-login for future checks
- ✅ Session data stored locally in: `~/.zalo_checker_browser_data`

**To logout/clear session:**
- Click "🔄 Clear Login Session" button
- Or manually delete the folder: `~/.zalo_checker_browser_data`

**Note:** Session data is stored only on your computer and never sent anywhere.

## Excel File Format

Your Excel file should contain a column with Zalo usernames. Example:

| username | email | notes |
|----------|-------|-------|
| John Doe | john@example.com | Manager |
| Jane Smith | jane@example.com | Developer |
| Bob Johnson | bob@example.com | Designer |

The application will auto-detect columns named: "username", "name", "user", "ten", or similar.

## Output File

The application generates an Excel file (`output/missing_members.xlsx`) with two sheets:

1. **Missing Members**: List of usernames not found in the group
2. **Metadata**: Information about the check (date, totals, group URL, etc.)

## Matching Methods

### Exact Matching
- Case-insensitive exact string comparison
- Faster but less flexible

### Fuzzy Matching (Recommended)
- Uses multiple algorithms: ratio, partial ratio, token sort, token set
- Handles typos, extra spaces, word order differences
- Configurable threshold (default: 85%)
- Example: "John Doe" matches "Doe John" or "john doe"

## Troubleshooting

### "No members found in group" ⚠️ IMPORTANT
This is the most common issue when Zalo Web updates their HTML structure.

**Quick Fix:**
1. When the browser opens, press **F12** to open Developer Tools
2. Go to **Console** tab
3. Copy and paste the entire content of `browser_console_helper.js` file
4. Press Enter to run the script
5. The script will test different selectors and show which ones work
6. Follow the recommendations to update the selector

**Detailed Guide:**
- See [`DEBUG_SELECTORS.md`](DEBUG_SELECTORS.md) for step-by-step instructions
- The debug script runs automatically and shows page structure analysis
- Use browser inspection tools to find the correct CSS selectors

### "DLL load failed" or "ImportError" on Windows
- **Solution**: Update PyQt6 version
  ```bash
  pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
  pip install PyQt6==6.7.1
  ```

### "attempted relative import beyond top-level package"
- **Solution**: This has been fixed. Make sure you're running from the project root:
  ```bash
  python src/main.py
  ```

### "Login timeout"
- **Solution**: Complete the login process faster (within 5 minutes)
- Ensure stable internet connection

### "Column not found in Excel"
- **Solution**: Ensure your Excel file has a column with usernames
- Rename the column to "username" or "name" for auto-detection

### Browser doesn't open
- **Solution**: Reinstall Playwright browsers
  ```bash
  playwright install chromium
  ```

### Permission errors on macOS
- **Solution**: Grant necessary permissions in System Preferences > Security & Privacy

## Project Structure

```
check_group_zalo/
├── src/
│   ├── main.py                    # Application entry point
│   ├── excel/
│   │   ├── reader.py              # Excel file reader
│   │   └── writer.py              # Excel/CSV writer
│   ├── scraper/
│   │   ├── browser_manager.py     # Browser automation
│   │   └── zalo_scraper.py        # Zalo web scraper
│   ├── core/
│   │   └── comparator.py          # Name comparison logic
│   └── ui/
│       └── main_window.py         # Main GUI window
├── output/                        # Output files directory
├── logs/                          # Application logs
├── plans/                         # Project documentation
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Technical Details

### Dependencies
- **PyQt6**: GUI framework
- **Playwright**: Web automation
- **pandas**: Data processing
- **openpyxl**: Excel file handling
- **fuzzywuzzy**: Fuzzy string matching

### How It Works

1. **Read Excel**: Parse usernames from Excel file
2. **Open Browser**: Launch Chromium via Playwright
3. **Manual Login**: User logs into Zalo Web
4. **Navigate**: Go to specified group URL
5. **Scrape**: Extract all member names using scroll automation
6. **Compare**: Match Excel names with group members
7. **Output**: Generate Excel file with missing members

## Important Notes

- **Login Required**: You must manually login to Zalo Web for each session
- **Time Intensive**: Large groups may take 10-30 minutes to scrape
- **Selector Dependency**: If Zalo updates their web interface, selectors may need adjustment
- **Rate Limiting**: Excessive requests may trigger anti-automation measures

## Privacy & Security

- ✅ No credentials stored
- ✅ All processing done locally
- ✅ No data sent to external servers
- ✅ Browser session closed after completion

## Limitations

- Requires active internet connection
- Zalo Web must be accessible
- Group must be accessible to the logged-in account
- Names must have some similarity for fuzzy matching to work

## Future Enhancements

- [ ] Batch processing for multiple groups
- [ ] Export to multiple formats (CSV, JSON, PDF)
- [ ] Scheduled automatic checks
- [ ] Member tracking over time
- [ ] Cross-platform support (Windows, Linux)

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review logs in `logs/app.log`
3. Verify Zalo Web structure hasn't changed

## License

This project is provided as-is for personal and educational use.

## Version

**1.0.0** - Initial release

---

**Note**: This tool is for legitimate membership verification purposes only. Use responsibly and in accordance with Zalo's terms of service.
