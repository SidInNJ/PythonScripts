#!/usr/bin/env python3
"""
PDF OCR Converter - Convert image-based PDFs to text-searchable PDFs
Handles large files efficiently by processing pages in batches and overlaying invisible text.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
import argparse
from typing import List, Optional
import logging

try:
    import pytesseract
    from pdf2image import convert_from_path
    from PIL import Image
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from PyPDF2 import PdfReader, PdfWriter
    import fitz  # PyMuPDF for better PDF handling
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Please install required packages: pip install -r requirements.txt")
    sys.exit(1)

# Configure Tesseract path for Windows
if os.name == 'nt':  # Windows
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
    else:
        print("Tesseract not found at expected location. Please ensure it's installed.")
        sys.exit(1)
    
    # Add common Poppler paths to PATH for pdf2image
    poppler_paths = [
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files\poppler\bin",
        r"C:\tools\poppler\Library\bin",
        r"C:\tools\poppler\bin",
        r"C:\poppler\bin"
    ]
    
    for poppler_path in poppler_paths:
        if os.path.exists(poppler_path) and poppler_path not in os.environ.get('PATH', ''):
            os.environ['PATH'] = poppler_path + os.pathsep + os.environ.get('PATH', '')
            logger.info(f"Added Poppler path to environment: {poppler_path}")
            break
    else:
        print("\nWARNING: POPPLER NOT FOUND")
        print("pdf2image requires Poppler to convert PDF pages to images.")
        print("\nTo install Poppler:")
        print("1. Run as Administrator: choco install poppler")
        print("2. Or download from: https://github.com/oschwartz10612/poppler-windows/releases/")
        print("3. Extract to C:\\Program Files\\poppler and add C:\\Program Files\\poppler\\Library\\bin to PATH")
        print("\nThen restart your command prompt and try again.")
        sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFOCRConverter:
    """Convert image-based PDFs to searchable PDFs with OCR text overlay."""
    
    def __init__(self, batch_size: int = 5, dpi: int = 300, tesseract_config: str = '--oem 3 --psm 6'):
        """
        Initialize the PDF OCR converter.
        
        Args:
            batch_size: Number of pages to process at once (for memory management)
            dpi: Resolution for PDF to image conversion
            tesseract_config: Tesseract OCR configuration
        """
        self.batch_size = batch_size
        self.dpi = dpi
        self.tesseract_config = tesseract_config
        self.temp_dir = None
        
    def __enter__(self):
        """Context manager entry."""
        self.temp_dir = tempfile.mkdtemp()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup temp files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """Get basic information about the PDF."""
        try:
            doc = fitz.open(pdf_path)
            info = {
                'page_count': len(doc),
                'file_size': os.path.getsize(pdf_path),
                'has_text': any(page.get_text().strip() for page in doc[:5])  # Check first 5 pages
            }
            doc.close()
            return info
        except Exception as e:
            logger.error(f"Error reading PDF info: {e}")
            return {'page_count': 0, 'file_size': 0, 'has_text': False}
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """Extract text from a PIL Image using OCR."""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Perform OCR
            text = pytesseract.image_to_string(image, config=self.tesseract_config)
            return text.strip()
        except Exception as e:
            logger.warning(f"OCR failed for image: {e}")
            return ""
    
    def get_text_positions(self, image: Image.Image) -> List[dict]:
        """Get text positions and content from image using OCR."""
        try:
            # Get detailed OCR data with bounding boxes
            data = pytesseract.image_to_data(image, config=self.tesseract_config, output_type=pytesseract.Output.DICT)
            
            text_blocks = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text and int(data['conf'][i]) > 30:  # Confidence threshold
                    text_blocks.append({
                        'text': text,
                        'x': data['left'][i],
                        'y': data['top'][i],
                        'width': data['width'][i],
                        'height': data['height'][i],
                        'confidence': data['conf'][i]
                    })
            
            return text_blocks
        except Exception as e:
            logger.warning(f"Failed to get text positions: {e}")
            return []
    
    def create_searchable_page(self, image: Image.Image, page_num: int) -> str:
        """Create a searchable PDF page with invisible text overlay."""
        try:
            # Save image temporarily
            image_path = os.path.join(self.temp_dir, f"page_{page_num}.png")
            image.save(image_path, "PNG")
            
            # Create PDF with image and invisible text overlay
            pdf_path = os.path.join(self.temp_dir, f"page_{page_num}.pdf")
            
            # Get image dimensions
            img_width, img_height = image.size
            
            # Create PDF canvas
            c = canvas.Canvas(pdf_path, pagesize=(img_width, img_height))
            
            # Add the image
            c.drawImage(image_path, 0, 0, width=img_width, height=img_height)
            
            # Get text positions from OCR
            text_blocks = self.get_text_positions(image)
            
            # Add invisible text overlay
            for block in text_blocks:
                # Convert coordinates (PIL uses top-left origin, PDF uses bottom-left)
                x = block['x']
                y = img_height - block['y'] - block['height']
                
                # Set text properties (invisible)
                c.setFillColorRGB(0, 0, 0, alpha=0)  # Transparent text
                c.setFont("Helvetica", max(8, block['height'] * 0.8))  # Scale font to text height
                
                # Add the text
                text_object = c.beginText(x, y)
                text_object.textOut(block['text'])
                c.drawText(text_object)
            
            c.save()
            return pdf_path
            
        except Exception as e:
            logger.error(f"Failed to create searchable page {page_num}: {e}")
            return None
    
    def process_pdf_batch(self, pdf_path: str, start_page: int, end_page: int) -> List[str]:
        """Process a batch of PDF pages."""
        try:
            logger.info(f"Processing pages {start_page + 1} to {end_page}")
            
            # Convert PDF pages to images
            images = convert_from_path(
                pdf_path,
                dpi=self.dpi,
                first_page=start_page + 1,
                last_page=end_page,
                thread_count=2  # Limit threads for memory management
            )
            
            # Process each image
            page_pdfs = []
            for i, image in enumerate(images):
                page_num = start_page + i
                logger.info(f"Processing page {page_num + 1} with OCR...")
                
                page_pdf = self.create_searchable_page(image, page_num)
                if page_pdf:
                    page_pdfs.append(page_pdf)
            
            return page_pdfs
            
        except Exception as e:
            logger.error(f"Failed to process batch {start_page}-{end_page}: {e}")
            return []
    
    def merge_pdfs(self, pdf_files: List[str], output_path: str) -> bool:
        """Merge multiple PDF files into one."""
        try:
            writer = PdfWriter()
            
            for pdf_file in pdf_files:
                if os.path.exists(pdf_file):
                    reader = PdfReader(pdf_file)
                    for page in reader.pages:
                        writer.add_page(page)
            
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to merge PDFs: {e}")
            return False
    
    def convert_pdf(self, input_path: str, output_path: str) -> bool:
        """Convert an image-based PDF to a searchable PDF."""
        try:
            # Get PDF information
            pdf_info = self.get_pdf_info(input_path)
            logger.info(f"Processing PDF: {pdf_info['page_count']} pages, {pdf_info['file_size'] / (1024*1024):.1f} MB")
            
            if pdf_info['has_text']:
                logger.warning("PDF already contains text. Consider if OCR is necessary.")
            
            # Process pages in batches
            all_page_pdfs = []
            total_pages = pdf_info['page_count']
            
            for start_page in range(0, total_pages, self.batch_size):
                end_page = min(start_page + self.batch_size, total_pages)
                
                # Process batch
                batch_pdfs = self.process_pdf_batch(input_path, start_page, end_page)
                all_page_pdfs.extend(batch_pdfs)
                
                # Progress update
                progress = (end_page / total_pages) * 100
                logger.info(f"Progress: {progress:.1f}% ({end_page}/{total_pages} pages)")
            
            # Merge all pages
            logger.info("Merging pages into final PDF...")
            success = self.merge_pdfs(all_page_pdfs, output_path)
            
            if success:
                output_size = os.path.getsize(output_path) / (1024*1024)
                logger.info(f"Successfully created searchable PDF: {output_path} ({output_size:.1f} MB)")
                return True
            else:
                logger.error("Failed to merge pages")
                return False
                
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return False

def get_input_filename() -> str:
    """Get input filename from user or use default."""
    if len(sys.argv) > 1:
        return sys.argv[1]
    
    filename = input("Enter PDF filename (default: combined.pdf): ").strip()
    return filename if filename else "combined.pdf"

def get_output_filename(input_path: str) -> str:
    """Generate output filename."""
    input_path = Path(input_path)
    output_name = input_path.stem + "_searchable" + input_path.suffix
    return str(input_path.parent / output_name)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Convert image-based PDFs to searchable PDFs")
    parser.add_argument("input", nargs='?', help="Input PDF file path")
    parser.add_argument("-o", "--output", help="Output PDF file path")
    parser.add_argument("--batch-size", type=int, default=5, help="Pages to process at once (default: 5)")
    parser.add_argument("--dpi", type=int, default=300, help="Image resolution for OCR (default: 300)")
    
    args = parser.parse_args()
    
    # Get input file
    if args.input:
        input_path = args.input
    else:
        input_path = get_input_filename()
    
    # Validate input file
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    
    # Get output file
    output_path = args.output if args.output else get_output_filename(input_path)
    
    # Check if output file already exists
    if os.path.exists(output_path):
        response = input(f"Output file {output_path} already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            logger.info("Operation cancelled.")
            sys.exit(0)
    
    # Convert PDF
    logger.info(f"Starting conversion: {input_path} -> {output_path}")
    
    with PDFOCRConverter(batch_size=args.batch_size, dpi=args.dpi) as converter:
        success = converter.convert_pdf(input_path, output_path)
    
    if success:
        logger.info("Conversion completed successfully!")
        print(f"\nSearchable PDF created: {output_path}")
    else:
        logger.error("Conversion failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
