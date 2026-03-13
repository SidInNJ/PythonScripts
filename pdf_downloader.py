#!/usr/bin/env python3
"""
PDF Downloader Script
Downloads PDF files from a webpage and its dropdowns/forms.
Filters by filename prefix and saves to timestamped folder.
"""

import argparse
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse, quote, unquote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
import requests
from bs4 import BeautifulSoup


class PDFDownloader:
    def __init__(self, base_url, filename_filter="Ordinance", output_dir=None, verbose=False):
        self.base_url = base_url
        self.filename_filter = filename_filter.lower() if filename_filter else None
        self.verbose = verbose
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            timestamp = datetime.now().strftime("%y-%m-%d_%H%M%S")
            self.output_dir = Path(f"WebPDF_{timestamp}")
        
        self.output_dir.mkdir(exist_ok=True)
        self.downloaded_files = []
        self.errors = []

    def log(self, message):
        """Print message if verbose mode is enabled"""
        if self.verbose:
            print(f"[INFO] {message}")

    def error(self, message):
        """Print error message and add to error list"""
        error_msg = f"[ERROR] {message}"
        print(error_msg)
        self.errors.append(message)

    def is_pdf_url(self, url):
        """Check if URL points to a PDF file"""
        return url.lower().endswith('.pdf') or 'pdf' in url.lower()

    def should_download_file(self, filename):
        """Check if file should be downloaded based on filter"""
        if not self.filename_filter:
            return True
        return filename.lower().startswith(self.filename_filter)

    def get_safe_filename(self, url, suggested_name=None):
        """Generate a safe filename from URL or suggested name"""
        if suggested_name:
            # Use suggested name (link text) and ensure it has .pdf extension
            filename = suggested_name.strip()
            if not filename.endswith('.pdf'):
                filename += '.pdf'
        else:
            # Fall back to URL-based filename
            filename = os.path.basename(urlparse(url).path)
            if not filename or not filename.endswith('.pdf'):
                filename = f"document_{len(self.downloaded_files) + 1}.pdf"
        
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Handle duplicates
        base_path = self.output_dir / filename
        counter = 1
        while base_path.exists():
            name, ext = os.path.splitext(filename)
            base_path = self.output_dir / f"{name}_{counter}{ext}"
            counter += 1
        
        return base_path.name

    def should_download_file(self, filename):
        """Check if file should be downloaded based on filename filter"""
        if not self.filename_filter:
            return True
        
        # Check if filename starts with the filter (case-insensitive)
        return filename.lower().startswith(self.filename_filter)

    def download_pdf(self, url, filename=None):
        """Download a single PDF file"""
        try:
            self.log(f"Downloading: {url}")
            
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('content-type', '').lower()
            if 'pdf' not in content_type and not url.lower().endswith('.pdf'):
                self.log(f"Skipping non-PDF content: {url}")
                return False
            
            safe_filename = self.get_safe_filename(url, filename)
            
            # Check filename filter
            if not self.should_download_file(safe_filename):
                self.log(f"Skipping file (doesn't match filter): {safe_filename}")
                return False
            
            file_path = self.output_dir / safe_filename
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Verify it's a valid PDF
            if file_path.stat().st_size < 100:  # Too small to be a valid PDF
                file_path.unlink()
                self.error(f"Downloaded file too small, deleted: {safe_filename}")
                return False
            
            self.downloaded_files.append(safe_filename)
            try:
                print(f"✓ Downloaded: {safe_filename}")
            except UnicodeEncodeError:
                print(f"[OK] Downloaded: {safe_filename}")
            
            # Polite delay
            time.sleep(0.1)
            return True
            
        except Exception as e:
            self.error(f"Failed to download {url}: {str(e)}")
            return False

    def construct_pdf_url(self, href, base_url):
        """Construct proper PDF URL handling different domain structures"""
        # If it's already a full URL, return as-is
        if href.startswith(('http://', 'https://')):
            return href
        
        # Handle relative URLs
        if href.startswith('/'):
            # Absolute path - use domain from base_url
            parsed_base = urlparse(base_url)
            return f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
        
        # Special handling for southamptonnj.org - their PDFs are actually hosted on cms9files.revize.com
        if 'southamptonnj.org' in base_url:
            # For this specific site, relative PDF paths should be constructed as:
            # https://cms9files.revize.com/southamptontwpnj/ + href
            if not href.startswith('/'):
                href = '/' + href
            constructed_url = f"https://cms9files.revize.com/southamptontwpnj{href}"
        else:
            # For other sites, use standard urljoin
            constructed_url = urljoin(base_url, href)
        
        # Ensure proper URL encoding
        # Parse the URL to separate components
        parsed = urlparse(constructed_url)
        # Re-encode the path component to handle spaces and special characters
        encoded_path = quote(unquote(parsed.path), safe='/')
        # Reconstruct the URL with properly encoded path
        constructed_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}"
        if parsed.query:
            constructed_url += f"?{parsed.query}"
        if parsed.fragment:
            constructed_url += f"#{parsed.fragment}"
        
        return constructed_url

    def find_pdf_links(self, soup, base_url):
        """Find all PDF links in the page"""
        pdf_links = []
        
        # Find direct PDF links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = self.construct_pdf_url(href, base_url)
            
            if self.is_pdf_url(full_url):
                link_text = link.get_text(strip=True)
                pdf_links.append((full_url, link_text))
                self.log(f"Found PDF link: {full_url} ({link_text})")
        
        return pdf_links

    def find_form_pdf_links(self, soup, base_url):
        """Find PDF links that might be behind forms or dropdowns"""
        pdf_links = []
        
        # Look for forms that might contain PDF links
        for form in soup.find_all('form'):
            action = form.get('action', '')
            if action:
                action_url = self.construct_pdf_url(action, base_url)
                
                # Look for select dropdowns in the form
                for select in form.find_all('select'):
                    for option in select.find_all('option'):
                        value = option.get('value', '')
                        if value and self.is_pdf_url(value):
                            full_url = self.construct_pdf_url(value, base_url)
                            option_text = option.get_text(strip=True)
                            pdf_links.append((full_url, option_text))
                            self.log(f"Found PDF in form option: {full_url} ({option_text})")
        
        # Look for JavaScript-generated links or data attributes
        for element in soup.find_all(attrs={"data-url": True}):
            data_url = element.get('data-url')
            if self.is_pdf_url(data_url):
                full_url = self.construct_pdf_url(data_url, base_url)
                element_text = element.get_text(strip=True)
                pdf_links.append((full_url, element_text))
                self.log(f"Found PDF in data attribute: {full_url} ({element_text})")
        
        return pdf_links

    def scrape_page(self, url):
        """Scrape a page for PDF links"""
        try:
            self.log(f"Scraping page: {url}")
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find direct PDF links
            pdf_links = self.find_pdf_links(soup, url)
            
            # Find form-based PDF links
            form_links = self.find_form_pdf_links(soup, url)
            pdf_links.extend(form_links)
            
            return pdf_links
            
        except Exception as e:
            self.error(f"Failed to scrape {url}: {str(e)}")
            return []

    def run(self):
        """Main execution method"""
        print(f"Starting PDF download from: {self.base_url}")
        print(f"Output directory: {self.output_dir}")
        if self.filename_filter:
            print(f"Filename filter: files starting with '{self.filename_filter}'")
        else:
            print("No filename filter applied")
        print("-" * 50)
        
        # Scrape the main page
        pdf_links = self.scrape_page(self.base_url)
        
        if not pdf_links:
            print("No PDF files found on the page.")
            return
        
        print(f"Found {len(pdf_links)} PDF files to process...")
        
        # Download each PDF
        for url, description in pdf_links:
            self.download_pdf(url, description)
        
        # Print summary
        print("-" * 50)
        print(f"Download complete!")
        print(f"Successfully downloaded: {len(self.downloaded_files)} files")
        print(f"Errors encountered: {len(self.errors)}")
        print(f"Files saved to: {self.output_dir}")
        
        if self.downloaded_files:
            print("\nDownloaded files:")
            for filename in self.downloaded_files:
                print(f"  - {filename}")
        
        if self.errors and self.verbose:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error}")


def main():
    parser = argparse.ArgumentParser(description='Download PDF files from a webpage')
    parser.add_argument('url', help='URL to scrape for PDF files')
    parser.add_argument('-f', '--filter', default='Ordinance', nargs='?', const='', 
                       help='Filename filter (files must start with this word). Use -f without value for no filter.')
    parser.add_argument('-o', '--output', help='Output directory (default: WebPDF_YY-MM-DD_HHMMSS)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Handle empty filter
    filename_filter = args.filter if args.filter else None
    
    # Ask for confirmation if no filter
    if filename_filter == '':
        filename_filter = None
        response = input("No filename filter specified. Download ALL PDF files? (y/N): ")
        if response.lower() != 'y':
            print("Aborted.")
            return
    
    try:
        downloader = PDFDownloader(
            base_url=args.url,
            filename_filter=filename_filter,
            output_dir=args.output,
            verbose=args.verbose
        )
        downloader.run()
        
    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
