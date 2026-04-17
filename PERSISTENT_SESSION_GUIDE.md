# Persistent Session Feature Guide

## 🎯 Overview

The Zalo Group Checker now supports **persistent browser sessions**, meaning you only need to login to Zalo Web **once**. Your login session is automatically saved and reused for all future checks.

## ✨ Benefits

- ⚡ **Faster workflow** - Skip login every time
- 🔒 **Secure** - Session stored only on your computer
- 🎯 **Convenient** - Login once, use many times
- 💾 **Automatic** - No configuration needed

## 🚀 How It Works

### First Run
1. Start the application: `python src/main.py`
2. Click "Start Checking"
3. Browser opens → Login to Zalo Web manually
4. Complete your checking task
5. **Session is automatically saved** ✅

### Subsequent Runs
1. Start the application
2. Click "Start Checking"
3. Browser opens → **Already logged in!** 🎉
4. Checking starts immediately

## 📁 Where Is Session Data Stored?

Session data (cookies, localStorage, etc.) is stored in:

**Location:** `~/.zalo_checker_browser_data/`

**Platform-specific paths:**
- **Windows:** `C:\Users\YourUsername\.zalo_checker_browser_data\`
- **macOS:** `/Users/YourUsername/.zalo_checker_browser_data/`
- **Linux:** `/home/YourUsername/.zalo_checker_browser_data/`

## 🔄 Managing Your Session

### Option 1: Clear via UI
1. Open the application
2. Click "🔄 Clear Login Session" button
3. Confirm the action
4. Session deleted ✅

### Option 2: Manual deletion
Delete the folder:
```bash
# Windows (Command Prompt)
rmdir /s "%USERPROFILE%\.zalo_checker_browser_data"

# macOS/Linux
rm -rf ~/.zalo_checker_browser_data
```

## 🔐 Security & Privacy

### Is it safe?
✅ **Yes!** Here's why:

1. **Local storage only** - Data never leaves your computer
2. **Same as Chrome/Firefox** - Uses standard browser data storage
3. **You control it** - Can delete anytime
4. **No passwords stored** - Only session tokens (cookies)

### What data is saved?
- Cookies (including Zalo session cookies)
- localStorage data
- IndexedDB data
- Browser cache

### What is NOT saved?
- ❌ Your password
- ❌ Personal messages
- ❌ Private information
- ❌ Credit card data

## ⚙️ Technical Details

### Implementation
The app uses Playwright's `launch_persistent_context()` which:
- Creates a persistent browser profile
- Saves all browser data between runs
- Works exactly like your regular browser

### Code Reference
```python
# In src/scraper/browser_manager.py
self.context = self.playwright.chromium.launch_persistent_context(
    user_data_dir=str(self.user_data_dir),
    headless=False,
    # ... other options
)
```

### Disabling Persistent Mode
If you prefer to login every time (not recommended), modify:

```python
# In src/scraper/zalo_scraper.py
self.browser_manager = BrowserManager(
    headless=False,
    use_persistent_context=False  # Disable persistent session
)
```

## 🐛 Troubleshooting

### Session expired or not working?
**Solution:** Clear the session and login again
1. Click "🔄 Clear Login Session"
2. Restart and login

### Browser shows "Profile in use" error?
**Cause:** Another instance is running
**Solution:** 
1. Close all Zalo Checker instances
2. Close any Chrome windows opened by the app
3. Try again

### Want to use multiple Zalo accounts?
**Not recommended with persistent session**
**Workaround:**
1. Clear session before switching accounts
2. Or disable persistent mode

## 📊 Comparison

| Feature | Without Persistent Session | With Persistent Session |
|---------|---------------------------|------------------------|
| Login frequency | Every time | Once |
| Setup time | ~2-5 min each time | ~2-5 min first time only |
| Subsequent runs | Slow (wait for login) | Fast (immediate) |
| Session management | N/A | Clear button available |
| Privacy | No data saved | Data saved locally |

## 💡 Best Practices

1. **Security:**
   - Clear session if sharing computer
   - Don't share the `.zalo_checker_browser_data` folder

2. **Performance:**
   - Keep persistent mode enabled (default)
   - Clear session if experiencing issues

3. **Multiple Users:**
   - Each OS user has their own session
   - Don't manually edit session files

## ❓ FAQ

**Q: Will this work if I change my password?**
A: You'll need to clear session and login again.

**Q: Can I copy the session to another computer?**
A: Not recommended. Zalo may detect and block it.

**Q: How long does the session last?**
A: Depends on Zalo's session timeout (usually weeks/months).

**Q: Is this feature safe to use at work?**
A: Yes, but follow your company's policy on automated tools.

**Q: Can I use this with a VPN?**
A: Yes, but IP changes might trigger re-login.

## 🎓 Advanced Usage

### Backup Your Session
```bash
# Create backup
cp -r ~/.zalo_checker_browser_data ~/.zalo_checker_browser_data.backup

# Restore backup
rm -rf ~/.zalo_checker_browser_data
cp -r ~/.zalo_checker_browser_data.backup ~/.zalo_checker_browser_data
```

### Check Session Size
```bash
# Windows
dir "%USERPROFILE%\.zalo_checker_browser_data" /s

# macOS/Linux
du -sh ~/.zalo_checker_browser_data
```

### Multiple Profiles (Advanced)
Modify `BrowserManager.__init__()` to use different directories:
```python
self.user_data_dir = Path.home() / f'.zalo_checker_profile_{profile_name}'
```

## 📞 Support

If you have issues with persistent sessions:
1. Try clearing the session first
2. Check the logs in `logs/app.log`
3. Verify the directory permissions
4. Ensure no other processes are using the profile

---

**Version:** 1.3.0  
**Last Updated:** 2026-02-12
