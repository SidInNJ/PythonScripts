# Markdown to DOCX Converter

A robust Python utility to convert Markdown files to DOCX format with advanced formatting support.

## Installation

Install required dependencies:
```bash
pip install -r requirements_md_to_docx.txt
```

Or install individually:
```bash
pip install python-docx markdown
```

## Usage

### Basic Usage
```bash
# Convert all .md files in current directory
python md_to_docx.py

# Convert specific file
python md_to_docx.py -f document.md

# Convert with verbose output
python md_to_docx.py -v
```

### Advanced Options
```bash
# Specify input directory
python md_to_docx.py -d /path/to/markdown/files

# Specify output directory
python md_to_docx.py -o /path/to/output

# Force overwrite existing files
python md_to_docx.py --force

# Combine options
python md_to_docx.py -f document.md -o ./output -v --force
```

## Features

- **Batch Processing**: Convert all .md files in a directory or specific files
- **Advanced Markdown Support**: Tables, code blocks, footnotes, math equations
- **Smart Skipping**: Automatically skips already converted files (unless forced)
- **Robust Error Handling**: Comprehensive logging and error reporting
- **Flexible Output**: Same directory or custom output location
- **Professional Formatting**: Preserves Markdown structure and styling

## Supported Markdown Features

- Headers (H1-H6)
- **Bold** and *italic* text
- Lists (ordered and unordered)
- Code blocks and inline code
- Tables
- Blockquotes
- Footnotes
- Links
- Line breaks

## Command Line Options

- `-f, --file`: Convert specific Markdown file
- `-d, --directory`: Input directory (default: current directory)
- `-o, --output`: Output directory (default: same as input)
- `-v, --verbose`: Enable verbose logging
- `--force`: Overwrite existing DOCX files
- `--version`: Show version information
- `-h, --help`: Show help message

## Examples

Convert all Markdown files in current directory:
```bash
python md_to_docx.py
```

Convert specific file with verbose output:
```bash
python md_to_docx.py -f README.md -v
```

Process files from different directory and save to output folder:
```bash
python md_to_docx.py -d ./docs -o ./converted --force
```
