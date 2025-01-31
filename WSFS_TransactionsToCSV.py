#!/usr/bin/env python3
import sys
import os
import pdfplumber
import pandas as pd
from pathlib import Path
from typing import List, Dict

def extract_data_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extract transaction data from the PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        List[Dict]: List of transactions with date, number, description, etc.
    """
    transactions = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extract text and split into lines
                text = page.extract_text()
                lines = text.split('\n')
                
                # Skip header lines
                start_idx = 0
                for i, line in enumerate(lines):
                    if 'Date' in line and 'Number' in line and 'Description' in line:
                        start_idx = i + 1
                        break
                
                # Process transaction lines
                for line in lines[start_idx:]:
                    # Skip empty lines and headers
                    if not line.strip() or 'Date' in line and 'Number' in line:
                        continue
                        
                    # Split line into components
                    parts = line.split()
                    
                    # Parse date
                    if not parts[0][0].isdigit():
                        continue
                    
                    # Parse and format date
                    date = parts[0]
                    try:
                        if '/' in date:  # Handle dates with separators
                            mm, dd, yy = date.split('/')
                            # Clean any non-digits
                            mm = ''.join(c for c in mm if c.isdigit())
                            dd = ''.join(c for c in dd if c.isdigit())
                            yy = ''.join(c for c in yy if c.isdigit())
                            
                            if len(yy) == 2:
                                yyyy = '20' + yy
                            else:
                                yyyy = yy
                        else:
                            # Remove any other separators
                            date_clean = ''.join(c for c in date if c.isdigit())
                            
                            if len(date_clean) == 8:  # MMDDYYYY
                                mm = date_clean[:2]
                                dd = date_clean[2:4]
                                yyyy = date_clean[4:]
                            elif len(date_clean) == 6:  # MMDDYY
                                mm = date_clean[:2]
                                dd = date_clean[2:4]
                                yy = date_clean[4:]
                                yyyy = '20' + yy
                            else:
                                print(f"Warning: Unexpected date format: {date}")
                                continue
                            
                        # Validate month and day
                        mm_int = int(mm)
                        dd_int = int(dd)
                        if not (1 <= mm_int <= 12 and 1 <= dd_int <= 31):
                            print(f"Warning: Invalid date values: {mm}/{dd}/{yyyy}")
                            continue
                            
                        date = f"{mm}/{dd}/{yyyy}"
                    except ValueError as e:
                        print(f"Warning: Could not parse date '{date}': {e}")
                        continue
                    
                    # Check if there's a check number
                    current_idx = 1
                    check_number = ''
                    if len(parts) > 1 and parts[current_idx].isdigit():
                        check_number = parts[current_idx]
                        current_idx += 1
                    
                    # Find withdrawal/deposit amounts
                    withdrawal = ''
                    deposit = ''
                    balance = parts[-1]
                    
                    # Look for amounts from the end
                    amount_idx = -2  # Start before balance
                    while abs(amount_idx) <= len(parts):
                        try:
                            float(parts[amount_idx].replace(',', ''))
                            if not withdrawal:
                                withdrawal = parts[amount_idx]
                            elif not deposit:
                                deposit = withdrawal
                                withdrawal = ''
                            break
                        except (ValueError, IndexError):
                            amount_idx -= 1
                    
                    # Get description (everything between check number/date and amounts)
                    desc_end = amount_idx if abs(amount_idx) < len(parts) else -1
                    description = ' '.join(parts[current_idx:desc_end])
                    
                    transaction = {
                        'Date': date,
                        'Number': check_number,
                        'Description': description,
                        'Withdrawals': withdrawal,
                        'Deposits': deposit,
                        'Balance': balance
                    }
                    
                    transactions.append(transaction)
        
        return transactions
    
    except Exception as e:
        print(f"Error processing file: {e}")
        return []

def find_pdf_files() -> List[str]:
    """
    Find all PDF files in the current directory.
    
    Returns:
        List[str]: List of PDF filenames
    """
    return [f for f in os.listdir() if f.lower().endswith('.pdf')]

def main():
    # Get input filename
    if len(sys.argv) > 1:
        pdf_file = sys.argv[1]
    else:
        # Look for PDF files in current directory
        pdf_files = find_pdf_files()
        
        if not pdf_files:
            pdf_file = input("Enter the PDF filename: ")
        else:
            print("Found PDF files:")
            for i, file in enumerate(pdf_files, 1):
                print(f"{i}. {file}")
            choice = int(input("Select a file number: "))
            pdf_file = pdf_files[choice - 1]
    
    # Check if file exists
    if not os.path.exists(pdf_file):
        print(f"Error: File '{pdf_file}' not found")
        sys.exit(1)
    
    # Extract data from PDF
    transactions = extract_data_from_pdf(pdf_file)
    
    if not transactions:
        print("No transactions found or error processing file")
        sys.exit(1)
    
    # Convert to DataFrame and sort by date
    df = pd.DataFrame(transactions)
    # Convert dates to datetime objects with explicit format
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    
    # Convert amount columns to numeric, removing any commas
    df['Withdrawals'] = pd.to_numeric(df['Withdrawals'].str.replace(',', ''), errors='coerce')
    df['Deposits'] = pd.to_numeric(df['Deposits'].str.replace(',', ''), errors='coerce')
    
    # Sort by Description first, then by Date ascending
    df = df.sort_values(['Description', 'Date'], ascending=[True, True])
    
    # Function to get the first meaningful words (e.g., "ELECTRONIC PAYMENT")
    def get_key_words(description):
        words = description.split()
        if len(words) >= 2:
            return ' '.join(words[:2])
        return description

    # Calculate both exact and partial matches
    summary_data = []
    processed_descriptions = set()
    
    # First pass: Find exact matches
    for desc, group in df.groupby('Description'):
        if len(group) > 1:  # Only group if multiple transactions
            withdrawals_sum = group['Withdrawals'].sum()
            deposits_sum = group['Deposits'].sum()
            count = len(group)
            
            summary_data.append({
                'Date': '',
                'Number': '',
                'Description': f"TOTAL for exact matches: {desc} ({count} transactions)",
                'Withdrawals': withdrawals_sum if withdrawals_sum > 0 else '',
                'Deposits': deposits_sum if deposits_sum > 0 else '',
                'Balance': '',
                'Sort_Order': 1  # For sorting summaries
            })
            processed_descriptions.update(group.index)
    
    # Second pass: Find partial matches among remaining transactions
    remaining_df = df.loc[~df.index.isin(processed_descriptions)]
    
    partial_groups = remaining_df.groupby(remaining_df['Description'].apply(get_key_words))
    
    for key_words, group in partial_groups:
        if len(group) > 1:  # Only group if multiple transactions
            withdrawals_sum = group['Withdrawals'].sum()
            deposits_sum = group['Deposits'].sum()
            count = len(group)
            
            summary_data.append({
                'Date': '',
                'Number': '',
                'Description': f"TOTAL for partial matches: {key_words}... ({count} transactions)",
                'Withdrawals': withdrawals_sum if withdrawals_sum > 0 else '',
                'Deposits': deposits_sum if deposits_sum > 0 else '',
                'Balance': '',
                'Sort_Order': 2  # For sorting summaries
            })
            processed_descriptions.update(group.index)
    
    if summary_data:
        # Create summary DataFrame and sort by Sort_Order
        summary_df = pd.DataFrame(summary_data)
        summary_df = summary_df.sort_values('Sort_Order')
        summary_df = summary_df.drop('Sort_Order', axis=1)
        
        # Add a blank row between data and summary
        blank_row = pd.DataFrame([{
            'Date': '',
            'Number': '',
            'Description': '',
            'Withdrawals': '',
            'Deposits': '',
            'Balance': ''
        }])
        
        # Combine main data, blank row, and summary
        final_df = pd.concat([df, blank_row, summary_df], ignore_index=True)
    else:
        final_df = df
    
    # Create output filename
    output_file = str(Path(pdf_file).with_suffix('.csv'))
    
    # Save to CSV
    final_df.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    # Print summary to console if exists
    if summary_data:
        print("\nSummary Totals:")
        for summary in summary_data:
            print(f"\n{summary['Description']}")
            if summary['Withdrawals']:
                print(f"  Total Withdrawals: ${summary['Withdrawals']:,.2f}")
            if summary['Deposits']:
                print(f"  Total Deposits: ${summary['Deposits']:,.2f}")
    else:
        print("\nNo groups found for summarization.")
    print(f"Data saved to {output_file}")

if __name__ == "__main__":
    main()
