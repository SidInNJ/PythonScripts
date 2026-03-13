#!/usr/bin/env python3
"""
PDF Combiner Script

This script combines two PDFs of a scanned document:
- First PDF contains odd pages (1,3,5...)
- Second PDF contains even pages (2,4,6...) in reverse order
- If a third PDF exists, it's appended to the end
- Output is saved as 'Combined.pdf'

Requirements:
    pip install pikepdf
"""

import os
import re
import glob
import argparse
from collections import defaultdict
import pikepdf

def extract_number(filename):
    """Extract the numeric part from the filename."""
    match = re.search(r'(\d+)\.pdf$', filename)
    if match:
        return int(match.group(1))
    return 0

def combine_pdfs(directory="CombineSides", output_name="Combined.pdf"):
    """
    Combine PDFs from the specified directory.
    
    Args:
        directory: Directory containing the PDF files
        output_name: Name of the output PDF file
    """
    # Get all PDF files in the directory
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return
    
    # Group files by base name (everything before the number)
    file_groups = defaultdict(list)
    
    for pdf_file in pdf_files:
        base_name = re.sub(r'_\d+\.pdf$', '', pdf_file)
        file_groups[base_name].append(pdf_file)
    
    # Process each group of files
    for base_name, files in file_groups.items():
        # Sort files by the numeric part of their names
        sorted_files = sorted(files, key=extract_number)
        
        if len(sorted_files) < 2:
            print(f"Skipping {base_name}: Need at least 2 PDFs (found {len(sorted_files)})")
            continue
        
        # First PDF contains odd pages
        odd_pdf_path = sorted_files[0]
        # Second PDF contains even pages in reverse
        even_pdf_path = sorted_files[1]
        
        print(f"Processing:\n  Odd pages: {odd_pdf_path}\n  Even pages: {even_pdf_path}")
        
        try:
            # Open the PDFs
            odd_pdf = pikepdf.Pdf.open(odd_pdf_path)
            even_pdf = pikepdf.Pdf.open(even_pdf_path)
            
            # Create a new PDF for the result
            merged_pdf = pikepdf.Pdf.new()
            
            # Calculate the total number of pages
            odd_page_count = len(odd_pdf.pages)
            even_page_count = len(even_pdf.pages)
            
            # Determine the expected total page count
            # If odd_page_count > even_page_count, the document ends with odd pages
            total_pages = max(odd_page_count * 2 - even_page_count, odd_page_count + even_page_count)
            
            # Interleave the pages
            for i in range(total_pages):
                if i % 2 == 0 and i // 2 < odd_page_count:
                    # Odd page (0-indexed, so these are actually pages 1, 3, 5, etc.)
                    merged_pdf.pages.append(odd_pdf.pages[i // 2])
                elif i % 2 == 1 and even_page_count > 0:
                    # Even page (0-indexed, so these are actually pages 2, 4, 6, etc.)
                    # The even pages are in reverse order
                    even_index = even_page_count - 1 - (i // 2)
                    if even_index >= 0:
                        merged_pdf.pages.append(even_pdf.pages[even_index])
            
            # If there's a third PDF, append it
            if len(sorted_files) > 2:
                third_pdf_path = sorted_files[2]
                print(f"  Appending: {third_pdf_path}")
                third_pdf = pikepdf.Pdf.open(third_pdf_path)
                for page in third_pdf.pages:
                    merged_pdf.pages.append(page)
            
            # Save the result
            merged_pdf.save(output_name)
            print(f"Successfully created {output_name}")
            
        except Exception as e:
            print(f"Error processing {base_name}: {str(e)}")
    
def main():
    """Main function to handle command line arguments and run the PDF combiner."""
    parser = argparse.ArgumentParser(
        description="Combine PDFs from a scanned document with odd/even pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use default directory 'CombineSides' and output 'Combined.pdf'
  %(prog)s -s /path/to/pdfs                   # Use custom source directory, output to 'Combined.pdf' in that directory
  %(prog)s -s /path/to/pdfs -o MyDocument.pdf # Use custom source and output filename
  %(prog)s -o MyDocument.pdf                  # Use default source directory, custom output filename
        """
    )
    
    parser.add_argument(
        '-s', '--source',
        default='CombineSides',
        help='Source directory containing PDF files (default: CombineSides)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output PDF filename. If not provided, defaults to "Combined.pdf" in the source directory'
    )
    
    args = parser.parse_args()
    
    # Normalize paths to handle both forward and back slashes
    source_dir = os.path.normpath(args.source)
    
    # Determine output file path
    if args.output:
        # Normalize the output path as well
        normalized_output = os.path.normpath(args.output)
        
        # Add .pdf extension if not present
        if not normalized_output.lower().endswith('.pdf'):
            normalized_output += '.pdf'
        
        # If output is provided, check if it's a full path or just a filename
        if os.path.dirname(os.path.normpath(args.output)):  # Check original path for directory
            # Full path provided
            output_path = normalized_output
        else:
            # Just filename provided, put it in source directory
            output_path = os.path.join(source_dir, normalized_output)
    else:
        # No output provided, use default in source directory
        output_path = os.path.join(source_dir, "Combined.pdf")
    
    print(f"Source directory: {source_dir}")
    print(f"Output file: {output_path}")
    print()
    
    combine_pdfs(source_dir, output_path)

if __name__ == "__main__":
    main()
