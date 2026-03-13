"""
Manager Transaction to QuickBooks IIF Converter
Converts Manager bank transactions to QuickBooks IIF format.
"""

import pandas as pd
import re
from pathlib import Path
from datetime import datetime

class TransactionConverter:
    def __init__(self, input_file, output_dir):
        """Initialize converter."""
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.timestamp = int(datetime.now().timestamp())
        self.trns_id_counter = 1
    
    def get_next_trns_id(self):
        """Get next transaction ID."""
        self.trns_id_counter += 1
        return self.trns_id_counter
    
    def clean_amount(self, amount_str):
        """Clean amount string and return float."""
        if pd.isna(amount_str):
            return 0.0
        
        # Remove $, commas, and spaces
        amount_str = str(amount_str).replace('$', '').replace(',', '').replace(' ', '').strip()
        
        # Handle negative amounts
        if amount_str.startswith('-'):
            return -float(amount_str[1:])
        else:
            return float(amount_str)
    
    def parse_date(self, date_str):
        """Parse date string to MM/DD/YYYY format."""
        if pd.isna(date_str):
            return ''
        
        try:
            # Manager format appears to be MM/DD/YYYY
            dt = datetime.strptime(str(date_str).strip(), '%m/%d/%Y')
            return dt.strftime('%m/%d/%Y')
        except:
            return str(date_str).strip()
    
    def extract_customer_name(self, account_str):
        """Extract customer name from account string."""
        if pd.isna(account_str):
            return ''
        
        # Pattern: "Accounts receivable  CustomerName - Full Name  Invoice#  Date"
        # Extract the part between "receivable" and the invoice number
        match = re.search(r'receivable\s+([^0-9]+?)\s+\d', str(account_str))
        if match:
            customer = match.group(1).strip()
            # Remove trailing dash and extra name
            customer = re.sub(r'\s*-\s*.*$', '', customer)
            return customer.strip()
        
        return ''
    
    def extract_account_name(self, account_str):
        """Extract account name from account string."""
        if pd.isna(account_str):
            return ''
        
        # If it's accounts receivable, return that
        if 'receivable' in str(account_str).lower():
            return 'Accounts Receivable'
        
        # Otherwise, take the first part before any numbers or special chars
        account = str(account_str).strip()
        # Take everything before the first number or special pattern
        match = re.match(r'^([A-Za-z\s]+)', account)
        if match:
            return match.group(1).strip()
        
        return account
    
    def convert_to_iif(self):
        """Convert transactions to QuickBooks IIF format."""
        print("\n" + "="*60)
        print("Converting Transactions to QuickBooks IIF")
        print("="*60)
        
        # Read the TSV file
        try:
            df = pd.read_csv(self.input_file, sep='\t', encoding='latin-1')
            print(f"[OK] Loaded {len(df)} rows from {self.input_file.name}")
        except Exception as e:
            print(f"[ERROR] Failed to read file: {e}")
            return None
        
        # Filter out the starting balance row and empty rows
        df = df[df['Transaction'].notna()]
        df = df[~df['Transaction'].str.contains('Starting balance', na=False)]
        
        print(f"[OK] Processing {len(df)} transactions (excluding starting balance)")
        
        # Separate receipts and payments
        receipts = df[df['Transaction'].str.contains('Receipt', na=False)]
        payments = df[df['Transaction'].str.contains('Payment', na=False)]
        
        print(f"[OK] Found {len(receipts)} receipts and {len(payments)} payments")
        
        # Create separate IIF files for different transaction types
        self.create_deposits_iif(receipts)
        self.create_checks_iif(payments)
        
        print("\n[OK] Conversion complete!")
    
    def create_deposits_iif(self, receipts_df):
        """Create IIF file for deposits/receipts."""
        if len(receipts_df) == 0:
            print("[INFO] No receipts to convert")
            return
        
        output_file = self.output_dir / "Deposits_Import.IIF"
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Write IIF header
            f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
            f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%Y-%m-%d')}\t{self.timestamp}\tN\t0\n")
            
            # Write transaction header
            # TRNS = Transaction header, SPL = Split line
            f.write("!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM\tMEMO\tCLEAR\tTOPRINT\tADDR1\tADDR2\tADDR3\tADDR4\tADDR5\n")
            f.write("!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM\tMEMO\tCLEAR\tQNTY\tPRICE\tINVITEM\tTAXABLE\n")
            f.write("!ENDTRNS\n")
            
            # Process each receipt
            for idx, row in receipts_df.iterrows():
                date = self.parse_date(row['Date'])
                amount = self.clean_amount(row['Amount'])
                description = str(row['Description']) if pd.notna(row['Description']) else ''
                customer = self.extract_customer_name(row['Account'])
                
                # Extract receipt number
                receipt_match = re.search(r'Receipt\s+(\d+)', str(row['Transaction']))
                docnum = receipt_match.group(1) if receipt_match else ''
                
                trns_id = self.get_next_trns_id()
                
                # TRNS line - Deposit to bank account
                f.write(f"TRNS\t{trns_id}\tDEPOSIT\t{date}\tFulton Bank\t{customer}\t\t{amount:.2f}\t{docnum}\t{description}\tN\tN\t\t\t\t\t\n")
                
                # SPL line - From Accounts Receivable
                f.write(f"SPL\t{trns_id}\tDEPOSIT\t{date}\tAccounts Receivable\t{customer}\t\t-{amount:.2f}\t{docnum}\t{description}\tN\t\t\t\tN\n")
                
                f.write("ENDTRNS\n")
            
            f.write("\n")
        
        print(f"[OK] Created: {output_file.name} ({len(receipts_df)} deposits)")
        return output_file
    
    def create_checks_iif(self, payments_df):
        """Create IIF file for checks/payments."""
        if len(payments_df) == 0:
            print("[INFO] No payments to convert")
            return
        
        output_file = self.output_dir / "Payments_Import.IIF"
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Write IIF header
            f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
            f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%Y-%m-%d')}\t{self.timestamp}\tN\t0\n")
            
            # Write transaction header
            f.write("!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM\tMEMO\tCLEAR\tTOPRINT\tADDR1\tADDR2\tADDR3\tADDR4\tADDR5\n")
            f.write("!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM\tMEMO\tCLEAR\tQNTY\tPRICE\tINVITEM\tTAXABLE\n")
            f.write("!ENDTRNS\n")
            
            # Process each payment
            for idx, row in payments_df.iterrows():
                date = self.parse_date(row['Date'])
                amount = abs(self.clean_amount(row['Amount']))  # Make positive
                description = str(row['Description']) if pd.notna(row['Description']) else ''
                account = self.extract_account_name(row['Account'])
                
                # Try to extract payee from description
                payee = ''
                if description:
                    # Pattern: "description  Payee Name"
                    parts = description.split('  ')
                    if len(parts) > 1:
                        payee = parts[-1].strip()
                
                trns_id = self.get_next_trns_id()
                
                # TRNS line - Payment from bank account (negative)
                f.write(f"TRNS\t{trns_id}\tCHECK\t{date}\tFulton Bank\t{payee}\t\t-{amount:.2f}\t\t{description}\tN\tN\t\t\t\t\t\n")
                
                # SPL line - To expense account (positive)
                f.write(f"SPL\t{trns_id}\tCHECK\t{date}\t{account}\t{payee}\t\t{amount:.2f}\t\t{description}\tN\t\t\t\tN\n")
                
                f.write("ENDTRNS\n")
            
            f.write("\n")
        
        print(f"[OK] Created: {output_file.name} ({len(payments_df)} payments)")
        return output_file

def main():
    """Main entry point."""
    input_file = r"C:\Scripts\Manager2QB\FultonBankTransactions.tsv"
    output_dir = r"C:\Scripts\Manager2QB\quickbooks_import"
    
    print("\n" + "="*60)
    print("Manager Transaction Converter")
    print("="*60)
    print(f"Input: {input_file}")
    print(f"Output: {output_dir}")
    
    converter = TransactionConverter(input_file, output_dir)
    converter.convert_to_iif()
    
    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    print("1. Import Deposits_Import.IIF into QuickBooks")
    print("   (File > Utilities > Import > IIF Files)")
    print("2. Import Payments_Import.IIF into QuickBooks")
    print("3. Verify transactions in QuickBooks")
    print("4. Reconcile Fulton Bank account")
    print("\nNote: Starting balance of $39,023.18 should be entered")
    print("as the opening balance for Fulton Bank account in QuickBooks")

if __name__ == "__main__":
    main()
