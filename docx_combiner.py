#!/usr/bin/env python3
"""
DOCX Combiner - Enhanced Script
Combines multiple DOCX files into a single text file with formatting preservation.

Features:
- Processes DOCX files ordered by creation date
- Clear document separators with metadata
- Optional recursive directory processing
- Error handling with warnings for corrupted files
- Progress indication
- Formatting preservation
- Command line interface with sensible defaults
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
import logging
from typing import List, Tuple, Optional
from tqdm import tqdm

try:
    from docx import Document
    from docx.document import Document as DocxDocument
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import _Cell, Table
    from docx.text.paragraph import Paragraph
except ImportError:
    print("Error: python-docx is required. Install with: pip install python-docx")
    sys.exit(1)


class DocxCombiner:
    """Main class for combining DOCX files into a single text output."""
    
    def __init__(self, input_dir: str, output_file: str, recursive: bool = False, 
                 dry_run: bool = False, verbose: bool = False):
        self.input_dir = Path(input_dir).resolve()
        self.output_file = Path(output_file).resolve()
        self.recursive = recursive
        self.dry_run = dry_run
        self.verbose = verbose
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('docx_combiner.log')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'files_skipped': 0,
            'total_words': 0,
            'errors': []
        }
    
    def find_docx_files(self) -> List[Path]:
        """Find all DOCX files in the specified directory."""
        pattern = "**/*.docx" if self.recursive else "*.docx"
        docx_files = []
        
        try:
            for file_path in self.input_dir.glob(pattern):
                if file_path.is_file() and not file_path.name.startswith('~'):
                    docx_files.append(file_path)
        except PermissionError as e:
            self.logger.error(f"Permission denied accessing directory: {e}")
            return []
        
        # Sort by creation date (oldest first)
        try:
            docx_files.sort(key=lambda x: x.stat().st_ctime)
        except OSError as e:
            self.logger.warning(f"Could not sort by creation date: {e}")
            docx_files.sort()  # Fallback to alphabetical sort
        
        return docx_files
    
    def extract_text_from_docx(self, file_path: Path) -> Tuple[str, int]:
        """
        Extract text from a DOCX file with formatting preservation.
        Returns tuple of (text_content, word_count)
        """
        try:
            doc = Document(str(file_path))
            text_parts = []
            word_count = 0
            
            for element in doc.element.body:
                if isinstance(element, CT_P):
                    # Handle paragraphs
                    paragraph = Paragraph(element, doc)
                    para_text = paragraph.text.strip()
                    if para_text:
                        text_parts.append(para_text)
                        word_count += len(para_text.split())
                    else:
                        text_parts.append("")  # Preserve empty lines
                        
                elif isinstance(element, CT_Tbl):
                    # Handle tables
                    table = Table(element, doc)
                    table_text = self._extract_table_text(table)
                    if table_text:
                        text_parts.append(table_text)
                        word_count += len(table_text.split())
            
            return "\n".join(text_parts), word_count
            
        except Exception as e:
            raise Exception(f"Failed to extract text: {str(e)}")
    
    def _extract_table_text(self, table: Table) -> str:
        """Extract text from a table with basic formatting."""
        table_lines = []
        
        for row in table.rows:
            row_cells = []
            for cell in row.cells:
                cell_text = cell.text.strip().replace('\n', ' ')
                row_cells.append(cell_text)
            
            if any(cell.strip() for cell in row_cells):  # Skip empty rows
                table_lines.append(" | ".join(row_cells))
        
        if table_lines:
            return "\n".join(table_lines) + "\n"
        return ""
    
    def get_file_metadata(self, file_path: Path) -> dict:
        """Get metadata for a file."""
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime),
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'relative_path': file_path.relative_to(self.input_dir)
            }
        except OSError as e:
            self.logger.warning(f"Could not get metadata for {file_path}: {e}")
            return {
                'name': file_path.name,
                'size': 0,
                'created': datetime.now(),
                'modified': datetime.now(),
                'relative_path': file_path.relative_to(self.input_dir)
            }
    
    def create_document_separator(self, metadata: dict, word_count: int) -> str:
        """Create a separator for each document."""
        separator = "=" * 80 + "\n"
        separator += f"DOCUMENT: {metadata['name']}\n"
        separator += f"PATH: {metadata['relative_path']}\n"
        separator += f"CREATED: {metadata['created'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        separator += f"MODIFIED: {metadata['modified'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        separator += f"SIZE: {metadata['size']:,} bytes\n"
        separator += f"WORD COUNT: {word_count:,} words\n"
        separator += "=" * 80 + "\n\n"
        return separator
    
    def process_files(self) -> bool:
        """Process all DOCX files and combine them."""
        docx_files = self.find_docx_files()
        
        if not docx_files:
            self.logger.warning(f"No DOCX files found in {self.input_dir}")
            return False
        
        self.logger.info(f"Found {len(docx_files)} DOCX files")
        
        if self.dry_run:
            self.logger.info("DRY RUN MODE - Files that would be processed:")
            for file_path in docx_files:
                metadata = self.get_file_metadata(file_path)
                print(f"  - {metadata['relative_path']} ({metadata['created'].strftime('%Y-%m-%d %H:%M:%S')})")
            return True
        
        # Create output directory if it doesn't exist
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(self.output_file, 'w', encoding='utf-8') as output:
                # Write header
                header = self._create_header(len(docx_files))
                output.write(header)
                
                # Process each file with progress bar
                with tqdm(total=len(docx_files), desc="Processing files") as pbar:
                    for file_path in docx_files:
                        try:
                            metadata = self.get_file_metadata(file_path)
                            pbar.set_description(f"Processing {metadata['name']}")
                            
                            # Extract text
                            text_content, word_count = self.extract_text_from_docx(file_path)
                            
                            # Write separator and content
                            separator = self.create_document_separator(metadata, word_count)
                            output.write(separator)
                            output.write(text_content)
                            output.write("\n\n")
                            
                            # Update statistics
                            self.stats['files_processed'] += 1
                            self.stats['total_words'] += word_count
                            
                        except Exception as e:
                            error_msg = f"Error processing {file_path.name}: {str(e)}"
                            self.logger.warning(error_msg)
                            self.stats['errors'].append(error_msg)
                            self.stats['files_skipped'] += 1
                            
                            # Write error notice in output
                            output.write(f"[ERROR: Could not process {file_path.name} - {str(e)}]\n\n")
                        
                        pbar.update(1)
                
                # Write footer with statistics
                footer = self._create_footer()
                output.write(footer)
        
        except IOError as e:
            self.logger.error(f"Could not write to output file {self.output_file}: {e}")
            return False
        
        return True
    
    def _create_header(self, total_files: int) -> str:
        """Create header for the combined document."""
        header = "COMBINED DOCX FILES\n"
        header += "=" * 80 + "\n"
        header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        header += f"Source Directory: {self.input_dir}\n"
        header += f"Recursive Processing: {'Yes' if self.recursive else 'No'}\n"
        header += f"Total Files Found: {total_files}\n"
        header += "=" * 80 + "\n\n"
        return header
    
    def _create_footer(self) -> str:
        """Create footer with processing statistics."""
        footer = "\n" + "=" * 80 + "\n"
        footer += "PROCESSING SUMMARY\n"
        footer += "=" * 80 + "\n"
        footer += f"Files Successfully Processed: {self.stats['files_processed']}\n"
        footer += f"Files Skipped (Errors): {self.stats['files_skipped']}\n"
        footer += f"Total Word Count: {self.stats['total_words']:,}\n"
        footer += f"Processing Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if self.stats['errors']:
            footer += "\nERRORS ENCOUNTERED:\n"
            for error in self.stats['errors']:
                footer += f"  - {error}\n"
        
        footer += "=" * 80 + "\n"
        return footer
    
    def print_summary(self):
        """Print processing summary."""
        print(f"\nProcessing completed!")
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files skipped: {self.stats['files_skipped']}")
        print(f"Total words: {self.stats['total_words']:,}")
        print(f"Output file: {self.output_file}")
        
        if self.stats['errors']:
            print(f"\nWarnings/Errors ({len(self.stats['errors'])}):")
            for error in self.stats['errors']:
                print(f"  - {error}")


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Combine DOCX files into a single text file, ordered by creation date.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Process current directory
  %(prog)s --input-dir /path/to/docs         # Process specific directory
  %(prog)s --recursive                       # Include subdirectories
  %(prog)s --output-file combined.txt        # Custom output filename
  %(prog)s --dry-run                         # Preview files without processing
        """
    )
    
    parser.add_argument(
        '--input-dir', '-i',
        default='.',
        help='Input directory containing DOCX files (default: current directory)'
    )
    
    parser.add_argument(
        '--output-file', '-o',
        default='Output.txt',
        help='Output filename (default: Output.txt)'
    )
    
    parser.add_argument(
        '--recursive', '-r',
        action='store_true',
        help='Process subdirectories recursively'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what files would be processed without actually processing them'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    input_path = Path(args.input_dir)
    if not input_path.exists():
        print(f"Error: Input directory '{input_path}' does not exist.")
        sys.exit(1)
    
    if not input_path.is_dir():
        print(f"Error: '{input_path}' is not a directory.")
        sys.exit(1)
    
    # Create combiner and process files
    combiner = DocxCombiner(
        input_dir=args.input_dir,
        output_file=args.output_file,
        recursive=args.recursive,
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    success = combiner.process_files()
    
    if not args.dry_run:
        combiner.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
