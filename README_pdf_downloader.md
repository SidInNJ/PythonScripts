# PDF Downloader Script

Downloads PDF files from a webpage and its dropdowns/forms, with filename filtering and organized storage.

## Features

- Downloads PDFs from direct links and form dropdowns
- Filters files by filename prefix (default: "Ordinance")
- Creates timestamped output folders (`WebPDF_YY-MM-DD_HHMMSS`)
- Handles duplicate filenames automatically
- Polite 100ms delay between downloads
- Validates downloaded files are actual PDFs
- Comprehensive error handling and logging

## Installation

```bash
pip install -r requirements_pdf_downloader.txt
```

## Usage

### Basic Usage
```bash
python pdf_downloader.py "https://www.southamptonnj.org/government/meetings/ordinance_lists.php"
```

### With Custom Filter
```bash
python pdf_downloader.py "https://example.com/documents" -f "Resolution"
```

### No Filter (Download All PDFs)
```bash
python pdf_downloader.py "https://example.com/documents" -f ""
```

### Custom Output Directory
```bash
python pdf_downloader.py "https://example.com/documents" -o "MyPDFs"
```

### Verbose Mode
```bash
python pdf_downloader.py "https://example.com/documents" -v
```

## Command Line Options

- `url` - Target URL to scrape (required)
- `-f, --filter` - Filename filter (default: "Ordinance")
- `-o, --output` - Custom output directory
- `-v, --verbose` - Enable detailed logging

## How It Works

1. **Page Scraping**: Parses HTML to find PDF links in `<a>` tags
2. **Form Processing**: Searches form dropdowns and data attributes for PDF URLs
3. **Filtering**: Checks if filenames start with the specified filter word
4. **Download**: Downloads files with proper error handling and validation
5. **Organization**: Saves files to timestamped folders with safe filenames

## Output

Files are saved to a folder named `WebPDF_YY-MM-DD_HHMMSS` (or custom directory) with:
- Original filenames preserved when possible
- Duplicate handling with numbered suffixes
- Only valid PDF files (verified by size and content-type)

## Error Handling

- Network timeouts and connection errors
- Invalid URLs and missing pages
- Non-PDF content filtering
- File validation and cleanup
- Comprehensive error reporting

## Example Output

```
Starting PDF download from: https://www.southamptonnj.org/government/meetings/ordinance_lists.php
Output directory: WebPDF_25-07-17_145339
Filename filter: files starting with 'Ordinance'
--------------------------------------------------
Found 5 PDF files to process...
✓ Downloaded: Ordinance_2025-01.pdf
✓ Downloaded: Ordinance_2025-02.pdf
✓ Downloaded: Ordinance_2025-03.pdf
--------------------------------------------------
Download complete!
Successfully downloaded: 3 files
Errors encountered: 0
Files saved to: WebPDF_25-07-17_145339
```
