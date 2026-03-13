#!/usr/bin/env python3
"""
Compare HTML content retrieved by main script vs debug script
"""

import requests
from bs4 import BeautifulSoup

def get_html_main_script_way():
    """Get HTML the way the main script does it"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    url = "https://www.southamptonnj.org/government/meetings/ordinance_lists.php"
    response = session.get(url, timeout=30)
    response.raise_for_status()
    
    return response.content

def get_html_debug_way():
    """Get HTML the way the debug script does it"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    url = "https://www.southamptonnj.org/government/meetings/ordinance_lists.php"
    response = session.get(url)
    
    return response.content

print("Comparing HTML content...")

html1 = get_html_main_script_way()
html2 = get_html_debug_way()

print(f"Main script HTML length: {len(html1)}")
print(f"Debug script HTML length: {len(html2)}")
print(f"HTML content identical: {html1 == html2}")

# Parse both and count 2023+ links
soup1 = BeautifulSoup(html1, 'html.parser')
soup2 = BeautifulSoup(html2, 'html.parser')

count_2023_plus_1 = 0
count_2023_plus_2 = 0

for link in soup1.find_all('a', href=True):
    href = link['href']
    if any(year in href for year in ['/2023/', '/2024/', '/2025/']):
        count_2023_plus_1 += 1

for link in soup2.find_all('a', href=True):
    href = link['href']
    if any(year in href for year in ['/2023/', '/2024/', '/2025/']):
        count_2023_plus_2 += 1

print(f"2023+ links found by main script method: {count_2023_plus_1}")
print(f"2023+ links found by debug script method: {count_2023_plus_2}")

# Show first few 2023+ links from each
print("\nFirst 3 2023+ links from main script method:")
count = 0
for link in soup1.find_all('a', href=True):
    href = link['href']
    if any(year in href for year in ['/2023/', '/2024/', '/2025/']):
        print(f"  {href} -> {link.get_text(strip=True)}")
        count += 1
        if count >= 3:
            break

print("\nFirst 3 2023+ links from debug script method:")
count = 0
for link in soup2.find_all('a', href=True):
    href = link['href']
    if any(year in href for year in ['/2023/', '/2024/', '/2025/']):
        print(f"  {href} -> {link.get_text(strip=True)}")
        count += 1
        if count >= 3:
            break

# Check if there are any differences in the HTML around 2023
if '2023' in html1.decode('utf-8', errors='ignore'):
    print("\n'2023' found in main script HTML")
else:
    print("\n'2023' NOT found in main script HTML")

if '2023' in html2.decode('utf-8', errors='ignore'):
    print("'2023' found in debug script HTML")
else:
    print("'2023' NOT found in debug script HTML")
