# Zalo Group Membership Checker - Technical Architecture

## Application Flow

```mermaid
flowchart TD
    Start([User Starts App]) --> LoadUI[Load PyQt6 Main Window]
    LoadUI --> WaitInput[Wait for User Input]
    WaitInput --> SelectExcel[User Selects Excel File]
    SelectExcel --> EnterLink[User Enters Zalo Group Link]
    EnterLink --> ClickStart[User Clicks Start Button]
    ClickStart --> ValidateInputs{Validate Inputs}
    ValidateInputs -->|Invalid| ShowError[Show Error Message]
    ShowError --> WaitInput
    ValidateInputs -->|Valid| ReadExcel[Read Excel File]
    ReadExcel --> ParseUsernames[Extract Username Column]
    ParseUsernames --> InitBrowser[Initialize Playwright Browser]
    InitBrowser --> OpenZalo[Open Zalo Web]
    OpenZalo --> WaitLogin{User Logged In?}
    WaitLogin -->|No| ShowLoginPrompt[Prompt User to Login]
    ShowLoginPrompt --> WaitLogin
    WaitLogin -->|Yes| NavigateGroup[Navigate to Group Link]
    NavigateGroup --> LoadMembers[Load All Group Members]
    LoadMembers --> ScrollPage{More Members?}
    ScrollPage -->|Yes| Scroll[Scroll Down]
    Scroll --> Wait[Wait for Load]
    Wait --> ScrollPage
    ScrollPage -->|No| ExtractMembers[Extract All Member Names]
    ExtractMembers --> CompareNames[Compare Excel Names with Group Members]
    CompareNames --> FindMissing[Identify Missing Members]
    FindMissing --> DisplayResults[Display Results in UI]
    DisplayResults --> SaveOutput[Save to Excel/CSV File]
    SaveOutput --> CloseBrowser[Close Browser]
    CloseBrowser --> Done([Process Complete])
```

## Module Interaction Diagram

```mermaid
graph LR
    UI[Main UI Window] -->|File Path| ER[Excel Reader]
    UI -->|Group URL| ZS[Zalo Scraper]
    ER -->|Username List| CM[Comparator]
    ZS -->|Member List| CM
    CM -->|Missing Users| EW[Excel Writer]
    CM -->|Results| UI
    EW -->|File Path| UI
    
    ZS --> BM[Browser Manager]
    ZS --> PR[HTML Parser]
    BM -->|Browser Instance| ZS
    PR -->|Parsed Data| ZS
```

## Class Structure

```mermaid
classDiagram
    class MainWindow {
        +QLineEdit groupLinkInput
        +QPushButton selectFileBtn
        +QPushButton startBtn
        +QProgressBar progressBar
        +QTextEdit resultsDisplay
        +selectExcelFile()
        +startProcess()
        +updateProgress()
        +displayResults()
    }
    
    class ExcelReader {
        +str filePath
        +str columnName
        +readFile()
        +parseColumn()
        +getUsernames()
    }
    
    class ExcelWriter {
        +str outputPath
        +list data
        +writeToExcel()
        +writeToCSV()
    }
    
    class ZaloScraper {
        +str groupUrl
        +BrowserManager browser
        +HTMLParser parser
        +initialize()
        +login()
        +navigateToGroup()
        +scrapeMembers()
        +close()
    }
    
    class BrowserManager {
        +Browser browser
        +Page page
        +launch()
        +navigate()
        +waitForElement()
        +scroll()
        +close()
    }
    
    class HTMLParser {
        +str html
        +parseMembers()
        +extractUsernames()
    }
    
    class Comparator {
        +list excelNames
        +list groupMembers
        +float threshold
        +compareExact()
        +compareFuzzy()
        +findMissing()
    }
    
    class Config {
        +dict settings
        +load()
        +save()
        +get()
    }
    
    class Logger {
        +str logFile
        +info()
        +error()
        +debug()
    }
    
    MainWindow --> ExcelReader
    MainWindow --> ExcelWriter
    MainWindow --> ZaloScraper
    MainWindow --> Comparator
    ZaloScraper --> BrowserManager
    ZaloScraper --> HTMLParser
    Comparator --> Logger
    MainWindow --> Config
```

## Data Flow

```mermaid
sequenceDiagram
    participant User
    participant UI as Main Window
    participant ER as Excel Reader
    participant ZS as Zalo Scraper
    participant CM as Comparator
    participant EW as Excel Writer
    
    User->>UI: Select Excel File
    User->>UI: Enter Group Link
    User->>UI: Click Start
    UI->>ER: Read Excel File
    ER-->>UI: Return Username List
    UI->>ZS: Initialize Scraper
    ZS->>ZS: Launch Browser
    ZS->>User: Prompt to Login
    User->>ZS: Complete Login
    ZS->>ZS: Navigate to Group
    ZS->>ZS: Scroll and Load Members
    ZS-->>UI: Return Member List
    UI->>CM: Compare Lists
    CM->>CM: Find Missing Members
    CM-->>UI: Return Missing List
    UI->>UI: Display Results
    UI->>EW: Save Results
    EW-->>UI: File Saved
    UI->>User: Show Completion Message
```

## Implementation Guidelines

### 1. Excel Reader Module ([`src/excel/reader.py`](src/excel/reader.py))
```python
Key Features:
- Support .xlsx and .xls formats
- Auto-detect username column or allow user to specify
- Handle empty rows and invalid data
- Return clean list of usernames

Libraries: openpyxl, pandas
```

### 2. Zalo Scraper Module ([`src/scraper/zalo_scraper.py`](src/scraper/zalo_scraper.py))
```python
Key Features:
- Playwright browser automation
- Stealth mode to avoid detection
- Handle dynamic content loading
- Scroll automation to load all members
- Extract member names from DOM

Libraries: playwright, playwright-stealth
```

### 3. Comparator Module ([`src/core/comparator.py`](src/core/comparator.py))
```python
Key Features:
- Exact string matching case-insensitive
- Fuzzy matching with configurable threshold
- Handle special characters and whitespace
- Return detailed comparison results

Libraries: fuzzywuzzy, python-Levenshtein
```

### 4. Main UI Module ([`src/ui/main_window.py`](src/ui/main_window.py))
```python
Key Features:
- Clean, intuitive interface
- Real-time progress updates
- Error message display
- Results preview
- Export options

Libraries: PyQt6
```

## Configuration File Structure

```json
{
  "browser": {
    "headless": false,
    "timeout": 30000,
    "viewport": {
      "width": 1280,
      "height": 800
    }
  },
  "scraper": {
    "scroll_pause": 2,
    "max_scroll_attempts": 50,
    "wait_for_element": 10
  },
  "excel": {
    "default_column": "username",
    "output_format": "xlsx"
  },
  "comparison": {
    "method": "fuzzy",
    "threshold": 0.85,
    "case_sensitive": false
  },
  "logging": {
    "level": "INFO",
    "file": "logs/app.log"
  }
}
```

## Error Handling Strategy

### Critical Errors (Stop Execution)
1. Excel file not found or corrupted
2. Invalid Zalo group URL format
3. Browser automation failure
4. No username column found in Excel

### Non-Critical Errors (Log & Continue)
1. Individual username parsing failures
2. Timeout on loading some members
3. Network connectivity issues (retry)

### User Notifications
- File selection errors
- Invalid input format
- Login required prompts
- Scraping progress updates
- Completion status

## Performance Optimization

### Memory Management
- Stream large Excel files
- Process members in batches
- Clear browser cache periodically

### Speed Improvements
- Parallel processing for comparison
- Efficient DOM selectors
- Minimize wait times with smart waits

### Resource Cleanup
- Close browser after completion
- Release file handles
- Clear temporary data

## Testing Strategy

### Unit Tests
- Excel reader with various file formats
- Comparator with edge cases
- Parser with different HTML structures

### Integration Tests
- Full workflow with sample data
- Browser automation scenarios
- Output file generation

### Manual Tests
- UI usability testing
- Real Zalo group testing
- Cross-platform verification

## Deployment Checklist

- [ ] All dependencies installed via requirements.txt
- [ ] Playwright browsers installed
- [ ] Configuration file created
- [ ] Sample data prepared
- [ ] README documentation complete
- [ ] Application tested on macOS
- [ ] PyInstaller spec file created
- [ ] Executable built and tested
- [ ] Installation guide written
