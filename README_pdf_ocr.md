# PDF OCR Converter

Convert image-based PDFs to text-searchable PDFs using OCR (Optical Character Recognition). This script handles large files efficiently by processing pages in batches and overlaying invisible text while preserving the original visual appearance.

## Features

- **Large File Support**: Efficiently handles large PDFs (25MB+) using batch processing
- **Invisible Text Overlay**: Preserves original appearance while adding searchability
- **Progress Tracking**: Shows processing progress for large files
- **Memory Efficient**: Processes pages in configurable batches to manage memory usage
- **Error Handling**: Graceful handling of corrupted files and OCR failures
- **Flexible Input**: Command-line arguments or interactive prompts

## Prerequisites

### 1. Install Tesseract OCR Engine

**Windows:**
- Download from: https://github.com/UB-Mannheim/tesseract/wiki
- Install and add to PATH, or install via chocolatey: `choco install tesseract`

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

### 2. Install Python Dependencies

```bash
pip install -r requirements_pdf_ocr.txt
```

## Usage

### Command Line Usage

```bash
# Basic usage - will prompt for filename if not provided
python pdf_ocr_converter.py

# Specify input file
python pdf_ocr_converter.py input.pdf

# Specify both input and output files
python pdf_ocr_converter.py input.pdf -o output_searchable.pdf

# Adjust batch size for memory management (default: 5 pages)
python pdf_ocr_converter.py input.pdf --batch-size 3

# Adjust DPI for OCR quality (default: 300)
python pdf_ocr_converter.py input.pdf --dpi 200
```

### Interactive Usage

If you run the script without arguments, it will prompt for the input filename:

```bash
python pdf_ocr_converter.py
Enter PDF filename (default: combined.pdf): my_document.pdf
```

## Output

- Creates a new PDF with "_searchable" suffix (e.g., `document_searchable.pdf`)
- Original visual appearance is preserved
- Text is searchable and selectable
- File size may be larger due to embedded OCR text data

## Performance Tips

### For Large Files (25MB+):
- **Reduce batch size**: Use `--batch-size 3` or `--batch-size 2` for very large files
- **Lower DPI**: Use `--dpi 200` for faster processing (slightly lower OCR quality)
- **Free up memory**: Close other applications during processing

### For Better OCR Quality:
- **Higher DPI**: Use `--dpi 400` for better text recognition
- **Ensure good image quality**: Clean, high-contrast source images work best

## Example Output

```
2024-01-15 10:30:15 - INFO - Processing PDF: 45 pages, 25.3 MB
2024-01-15 10:30:16 - INFO - Processing pages 1 to 5
2024-01-15 10:30:18 - INFO - Processing page 1 with OCR...
2024-01-15 10:30:20 - INFO - Processing page 2 with OCR...
...
2024-01-15 10:32:45 - INFO - Progress: 100.0% (45/45 pages)
2024-01-15 10:32:46 - INFO - Merging pages into final PDF...
2024-01-15 10:32:48 - INFO - Successfully created searchable PDF: document_searchable.pdf (28.7 MB)

Searchable PDF created: document_searchable.pdf
```

## Troubleshooting

### Common Issues:

1. **"Tesseract not found"**
   - Ensure Tesseract is installed and in your PATH
   - On Windows, you may need to add the installation directory to PATH

2. **Memory errors with large files**
   - Reduce batch size: `--batch-size 2`
   - Lower DPI: `--dpi 200`
   - Close other applications

3. **Poor OCR quality**
   - Increase DPI: `--dpi 400`
   - Ensure source PDF has good image quality
   - Check if PDF already contains text (script will warn you)

4. **Slow processing**
   - This is normal for large files
   - Consider processing smaller sections separately
   - Use lower DPI for faster processing

## Dependencies

- `pytesseract`: Python wrapper for Tesseract OCR
- `pdf2image`: Convert PDF pages to images
- `Pillow`: Image processing
- `reportlab`: PDF generation
- `PyPDF2`: PDF manipulation
- `PyMuPDF`: Advanced PDF handling

## License

This script is provided as-is for educational and practical use.
