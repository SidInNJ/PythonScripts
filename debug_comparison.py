#!/usr/bin/env python3
"""
Compare what the main script finds vs debug script
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, quote, unquote

def construct_pdf_url(href, base_url):
    """Same logic as in the main script"""
    if href.startswith(('http://', 'https://')):
        return href
    
    if href.startswith('/'):
        parsed_base = urlparse(base_url)
        return f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
    
    if 'southamptonnj.org' in base_url:
        if not href.startswith('/'):
            href = '/' + href
        constructed_url = f"https://cms9files.revize.com/southamptontwpnj{href}"
    else:
        constructed_url = urljoin(base_url, href)
    
    parsed = urlparse(constructed_url)
    encoded_path = quote(unquote(parsed.path), safe='/')
    constructed_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}"
    if parsed.query:
        constructed_url += f"?{parsed.query}"
    if parsed.fragment:
        constructed_url += f"#{parsed.fragment}"
    
    return constructed_url

def is_pdf_url(url):
    """Check if URL points to a PDF file"""
    return url.lower().endswith('.pdf') or 'pdf' in url.lower()

url = "https://www.southamptonnj.org/government/meetings/ordinance_lists.php"

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

response = session.get(url)
soup = BeautifulSoup(response.content, 'html.parser')

print("Main script logic - finding PDF links:")
print("=" * 50)

pdf_links = []
for link in soup.find_all('a', href=True):
    href = link['href']
    full_url = construct_pdf_url(href, base_url=url)
    
    if is_pdf_url(full_url):
        link_text = link.get_text(strip=True)
        pdf_links.append((full_url, link_text))
        
        # Check if it's 2023+
        if any(year in href for year in ['/2023/', '/2024/', '/2025/']):
            print(f"FOUND 2023+: {href} -> {full_url}")
            print(f"  Text: {link_text}")

print(f"\nTotal PDF links found by main script logic: {len(pdf_links)}")

# Count by year
years = {'2020': 0, '2021': 0, '2022': 0, '2023': 0, '2024': 0, '2025': 0}
for url_link, text in pdf_links:
    for year in years:
        if f'/{year}/' in url_link:
            years[year] += 1
            break

print("Year breakdown:")
for year, count in years.items():
    print(f"  {year}: {count}")

# Now let's check if there are any 2023+ links that don't pass is_pdf_url
print("\n" + "=" * 50)
print("Checking all links for 2023+ that might not pass is_pdf_url:")

for link in soup.find_all('a', href=True):
    href = link['href']
    if any(year in href for year in ['/2023/', '/2024/', '/2025/']):
        full_url = construct_pdf_url(href, base_url=url)
        link_text = link.get_text(strip=True)
        passes_pdf_check = is_pdf_url(full_url)
        
        print(f"2023+ Link: {href}")
        print(f"  Full URL: {full_url}")
        print(f"  Text: {link_text}")
        print(f"  Passes PDF check: {passes_pdf_check}")
        print()
