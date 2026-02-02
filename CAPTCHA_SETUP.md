# CAPTCHA Handling Setup Guide

## Overview
The job scraper now supports manual CAPTCHA solving using browser automation. This is particularly useful for Glassdoor which uses Cloudflare protection.

## Installation

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install selenium undetected-chromedriver
```

### 2. Install ChromeDriver

#### macOS
```bash
# Using Homebrew (recommended)
brew install chromedriver

# If you get security warnings, allow it:
xattr -d com.apple.quarantine $(which chromedriver)
```

#### Linux (Ubuntu/Debian)
```bash
# Method 1: Using apt (may not be latest version)
sudo apt-get update
sudo apt-get install chromium-chromedriver

# Method 2: Download latest version
# First, check your Chrome version: google-chrome --version
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
CHROMEDRIVER_VERSION=$(cat LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip LATEST_RELEASE
```

#### Linux (Fedora/RHEL/CentOS)
```bash
# Install Chrome first if not already installed
sudo dnf install google-chrome-stable

# Download and install ChromeDriver
wget https://chromedriver.storage.googleapis.com/LATEST_RELEASE
CHROMEDRIVER_VERSION=$(cat LATEST_RELEASE)
wget https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver_linux64.zip LATEST_RELEASE
```

#### Windows
```powershell
# Method 1: Using Chocolatey (recommended)
choco install chromedriver

# Method 2: Manual installation
# 1. Check your Chrome version: Chrome menu > Help > About Google Chrome
# 2. Download matching version from: https://chromedriver.chromium.org/downloads
# 3. Extract chromedriver.exe
# 4. Add to PATH or move to C:\Windows\System32\
# 5. Or place in your project directory
```

#### Verify Installation
```bash
# Check ChromeDriver is accessible
chromedriver --version

# Should output something like: ChromeDriver 120.0.6099.109
```

## Configuration

Add the following to your `config.yaml`:

```yaml
captcha:
  enabled: true                  # Enable browser automation
  method: manual                 # Use 'manual' for human solving
  browser: undetected-chrome     # Use 'undetected-chrome' or 'chrome'
  headless: false                # Must be false for manual solving
  wait_timeout: 300              # Max seconds to wait (5 minutes)
  glassdoor_only: true           # Only use for Glassdoor (recommended)
```

### Configuration Options

- **enabled**: Set to `true` to activate CAPTCHA handling
- **method**: Currently supports `manual` (future: `auto` for CAPTCHA services)
- **browser**: 
  - `undetected-chrome`: Better at avoiding detection (recommended)
  - `chrome`: Standard ChromeDriver
- **headless**: Must be `false` for manual solving
- **wait_timeout**: How long to wait for you to solve the CAPTCHA (in seconds)
- **glassdoor_only**: If `true`, only opens browser for Glassdoor (recommended to save time)

## Usage

### Using Config File
```bash
python job_scraper.py --config config.yaml
```

### Sample Config
```yaml
job_roles:
  - DevOps Engineer
  - Site Reliability Engineer

countries:
  - germany
  - netherlands

job_sites:
  priority:
    - indeed
    - glassdoor
  disabled: []

captcha:
  enabled: true
  method: manual
  browser: undetected-chrome
  headless: false
  wait_timeout: 300
  glassdoor_only: true

search_params:
  results_per_site: 50
  hours_old: 168
```

## How It Works

1. **Browser Opens**: When Glassdoor is in your enabled sites, a Chrome browser window will open automatically
2. **CAPTCHA Detection**: The script detects Cloudflare challenge pages
3. **Manual Solving**: You solve the CAPTCHA in the browser (checkbox or image selection)
4. **Auto-Continue**: Once solved, the script automatically continues scraping
5. **Session Reuse**: The browser stays open for all Glassdoor searches, so you typically only need to solve once

## Workflow Example

```
🚀 Starting job search...
   Roles: 2
   Countries: 2
   Total searches: 4

🌐 Initializing browser for CAPTCHA handling...
   ✓ Using undetected-chromedriver (better for Cloudflare)

[1/4] 
============================================================
🌍 Country: GERMANY
💼 Role: DevOps Engineer
🔗 Sites: indeed, glassdoor
============================================================

🔓 Pre-checking glassdoor for CAPTCHA...
   URL: https://www.glassdoor.com/...

⚠️  Cloudflare challenge detected!
   📋 Please solve the CAPTCHA in the browser window
   ⏰ Waiting up to 300 seconds...
   💡 The script will continue automatically once solved

   ✅ CAPTCHA solved! Continuing...
   ✓ glassdoor CAPTCHA cleared

✓ Scraped 45 jobs
...
```

## Troubleshooting

### "Selenium not installed"
```bash
pip install selenium
```

### "undetected-chromedriver not installed"
```bash
pip install undetected-chromedriver
```
Or use standard chrome by setting `browser: chrome` in config

### "ChromeDriver not found"
**macOS:**
```bash
brew install chromedriver
```

**Linux:**
```bash
sudo apt-get install chromium-chromedriver
```

**Windows:**
Download from https://chromedriver.chromium.org/ and add to PATH

### Browser doesn't open
- Check that `headless: false` in config
- Ensure ChromeDriver version matches your Chrome version

### CAPTCHA timeout
- Increase `wait_timeout` in config (default 300 seconds = 5 minutes)
- Make sure you're actively solving the CAPTCHA
- The browser window must remain open

### Still getting blocked
- Try `undetected-chrome` instead of standard `chrome`
- Use residential proxies (requires additional setup)
- Consider excluding Glassdoor: `--exclude-sites glassdoor`

## Tips

1. **First Run**: CAPTCHA solving may be required on first run
2. **Subsequent Runs**: Browser maintains session, usually no repeated solving
3. **Multiple Countries**: Browser stays open across all searches
4. **Time Limit**: Complete CAPTCHA within the timeout period (default 5 minutes)
5. **Focus**: Keep the browser window visible while solving

## Alternative: Disable Glassdoor

If CAPTCHA is too problematic, exclude Glassdoor:

```bash
python job_scraper.py --exclude-sites glassdoor
```

Or in config.yaml:
```yaml
job_sites:
  disabled:
    - glassdoor
```

## Future Enhancements

Planned features:
- Auto-solving with 2Captcha/Anti-Captcha integration
- Proxy rotation support
- Cookie persistence for session reuse
- Support for other browsers (Firefox, Edge)
