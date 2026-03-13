# DOCX Combiner - Enhanced Script

A Python script that combines multiple DOCX files into a single text file with formatting preservation, ordered by creation date.

## Features

- **Smart Processing**: Processes DOCX files ordered by creation date (oldest first)
- **Clear Separators**: Each document includes metadata header with filename, dates, size, and word count
- **Formatting Preservation**: Maintains paragraph breaks, tables, and basic text structure
- **Error Handling**: Skips corrupted files with warnings, continues processing
- **Progress Indication**: Real-time progress bar for large file collections
- **Flexible Options**: Optional recursive directory processing, custom output paths
- **Comprehensive Logging**: Detailed logs and processing statistics
- **Dry Run Mode**: Preview files without processing

## Installation

1. Install required dependencies:
```bash
pip install -r requirements_docx_combiner.txt
```

Or install manually:
```bash
pip install python-docx tqdm
```

## Usage

### Basic Usage
```bash
# Process current directory, output to Output.txt
python docx_combiner.py

# Process specific directory
python docx_combiner.py --input-dir /path/to/documents

# Custom output filename
python docx_combiner.py --output-file combined_docs.txt
```

### Advanced Options
```bash
# Include subdirectories recursively
python docx_combiner.py --recursive

# Preview files without processing
python docx_combiner.py --dry-run

# Verbose logging
python docx_combiner.py --verbose

# Combine multiple options
python docx_combiner.py --input-dir ./documents --recursive --output-file all_docs.txt --verbose
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--input-dir` | `-i` | Input directory containing DOCX files | Current directory |
| `--output-file` | `-o` | Output filename | Output.txt |
| `--recursive` | `-r` | Process subdirectories recursively | False |
| `--dry-run` | | Preview files without processing | False |
| `--verbose` | `-v` | Enable verbose logging | False |
| `--help` | `-h` | Show help message | |

## Output Format

The combined text file includes:

1. **Header Section**: Processing metadata and summary
2. **Document Sections**: Each DOCX file with:
   - Document separator (80 characters)
   - Filename and path information
   - Creation and modification dates
   - File size and word count
   - Extracted text content with preserved formatting
3. **Footer Section**: Processing statistics and error summary

### Example Output Structure
```
COMBINED DOCX FILES
================================================================================
Generated: 2025-09-13 18:56:24
Source Directory: C:\Documents
Recursive Processing: No
Total Files Found: 5
================================================================================

================================================================================
DOCUMENT: report_2023.docx
PATH: report_2023.docx
CREATED: 2023-01-15 09:30:45
MODIFIED: 2023-01-15 14:22:10
SIZE: 45,231 bytes
WORD COUNT: 2,847 words
================================================================================

[Document content with preserved formatting...]

================================================================================
PROCESSING SUMMARY
================================================================================
Files Successfully Processed: 5
Files Skipped (Errors): 0
Total Word Count: 12,456
Processing Completed: 2025-09-13 18:56:30
================================================================================
```

## Error Handling

The script handles various error conditions gracefully:

- **Corrupted DOCX files**: Skipped with warning, processing continues
- **Permission errors**: Logged and reported
- **Missing files**: Handled during directory scanning
- **Invalid directories**: Validation before processing starts

All errors are logged to `docx_combiner.log` and included in the output summary.

## Technical Details

### Text Extraction
- Uses `python-docx` library for reliable DOCX parsing
- Preserves paragraph structure and line breaks
- Extracts table content with basic formatting (pipe-separated columns)
- Handles embedded objects gracefully

### File Processing
- Files sorted by creation date (`st_ctime`)
- Fallback to alphabetical sorting if date access fails
- Cross-platform compatibility (Windows/Mac/Linux)
- Memory-efficient processing for large files

### Logging
- Dual logging: console output and log file
- Configurable verbosity levels
- Processing statistics and error tracking
- Progress indication with `tqdm`

## Troubleshooting

### Common Issues

1. **"python-docx not found"**
   - Install dependencies: `pip install python-docx`

2. **Permission denied errors**
   - Check directory permissions
   - Run with appropriate user privileges
   - Check if files are open in other applications

3. **Empty output file**
   - Verify DOCX files exist in specified directory
   - Check file extensions (must be .docx)
   - Use `--dry-run` to preview files

4. **Corrupted file warnings**
   - Normal behavior for password-protected or damaged files
   - Files are skipped automatically
   - Check error summary for details

### Debug Mode
Use `--verbose` flag for detailed logging:
```bash
python docx_combiner.py --verbose
```

Check `docx_combiner.log` for complete processing details.

## Examples

### Process Current Directory
```bash
python docx_combiner.py
```

### Process Specific Directory with Subdirectories
```bash
python docx_combiner.py --input-dir "C:\My Documents" --recursive --output-file "all_documents.txt"
```

### Preview Processing
```bash
python docx_combiner.py --input-dir ./reports --recursive --dry-run
```

## Dependencies

- **python-docx**: DOCX file parsing and text extraction
- **tqdm**: Progress bar functionality
- **pathlib**: Cross-platform path handling (built-in)
- **argparse**: Command line interface (built-in)
- **logging**: Error handling and debugging (built-in)

## License

This script is provided as-is for educational and practical use.
