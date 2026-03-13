#!/usr/bin/env python3
"""
Debug script to examine why 2023+ ordinances aren't being downloaded
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote, unquote

def construct_pdf_url(href, base_url):
    """Same logic as in the main script"""
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

def should_download_file(filename, filename_filter="Ordinance"):
    """Check if file should be downloaded based on filter"""
    if not filename_filter:
        return True
    return filename.lower().startswith(filename_filter.lower())

url = "https://www.southamptonnj.org/government/meetings/ordinance_lists.php"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

response = session.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

print("Analyzing all PDF links by year:")
print("=" * 60)

# Group by year
years = {}
all_links = []

for link in soup.find_all('a', href=True):
    href = link['href']
    if 'pdf' in href.lower():
        link_text = link.get_text(strip=True)
        full_url = construct_pdf_url(href, url)
        
        # Extract year from href
        year = None
        if '/2020/' in href:
            year = '2020'
        elif '/2021/' in href:
            year = '2021'
        elif '/2022/' in href:
            year = '2022'
        elif '/2023/' in href:
            year = '2023'
        elif '/2024/' in href:
            year = '2024'
        elif '/2025/' in href:
            year = '2025'
        else:
            year = 'Unknown'
        
        if year not in years:
            years[year] = []
        
        # Check if it passes the filter
        passes_filter = should_download_file(link_text)
        
        years[year].append({
            'href': href,
            'text': link_text,
            'url': full_url,
            'passes_filter': passes_filter
        })
        
        all_links.append({
            'year': year,
            'href': href,
            'text': link_text,
            'url': full_url,
            'passes_filter': passes_filter
        })

# Print summary by year
for year in sorted(years.keys()):
    links = years[year]
    passed_filter = [l for l in links if l['passes_filter']]
    print(f"\n{year}: {len(links)} total PDFs, {len(passed_filter)} pass filter")
    
    if len(passed_filter) > 0:
        print("  Filtered links:")
        for link in passed_filter[:5]:  # Show first 5
            print(f"    - {link['text']} -> {link['url']}")
        if len(passed_filter) > 5:
            print(f"    ... and {len(passed_filter) - 5} more")
    
    failed_filter = [l for l in links if not l['passes_filter']]
    if len(failed_filter) > 0:
        print(f"  Failed filter ({len(failed_filter)}):")
        for link in failed_filter[:3]:  # Show first 3
            print(f"    - {link['text']} (doesn't start with 'Ordinance')")
        if len(failed_filter) > 3:
            print(f"    ... and {len(failed_filter) - 3} more")

print(f"\nTotal PDF links found: {len(all_links)}")
print(f"Total that pass 'Ordinance' filter: {len([l for l in all_links if l['passes_filter']])}")

# Test a few 2023+ URLs to see if they're accessible
print("\n" + "=" * 60)
print("Testing accessibility of 2023+ URLs:")

test_years = ['2023', '2024', '2025']
for year in test_years:
    if year in years:
        links = [l for l in years[year] if l['passes_filter']]
        if links:
            test_url = links[0]['url']
            print(f"\nTesting {year}: {test_url}")
            try:
                test_response = session.head(test_url, timeout=10)
                print(f"  Status: {test_response.status_code}")
                if test_response.status_code == 200:
                    print(f"  Content-Type: {test_response.headers.get('content-type', 'Unknown')}")
                    print(f"  Content-Length: {test_response.headers.get('content-length', 'Unknown')}")
            except Exception as e:
                print(f"  Error: {str(e)}")
        else:
            print(f"\n{year}: No links found that pass filter")
    else:
        print(f"\n{year}: No links found for this year")
