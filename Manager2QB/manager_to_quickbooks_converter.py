"""
Manager to QuickBooks IIF Converter
Converts Manager accounting data to QuickBooks IIF format for import.
"""

import pandas as pd
import csv
from pathlib import Path
from datetime import datetime
import re

class ManagerToQBConverter:
    def __init__(self, input_dir, output_dir):
        """Initialize converter with input and output directories."""
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # QuickBooks account type mapping
        self.account_type_map = {
            'Bank': 'BANK',
            'Cash': 'BANK',
            'Accounts Receivable': 'AR',
            'Accounts Payable': 'AP',
            'Current Asset': 'OCASSET',
            'Fixed Asset': 'FIXASSET',
            'Other Asset': 'OASSET',
            'Credit Card': 'CCARD',
            'Current Liability': 'OCLIAB',
            'Long Term Liability': 'LTLIAB',
            'Equity': 'EQUITY',
            'Income': 'INC',
            'Cost of Sales': 'COGS',
            'Expense': 'EXP',
            'Other Income': 'EXINC',
            'Other Expense': 'EXEXP'
        }
        
        self.timestamp = int(datetime.now().timestamp())
        self.refnum_counter = 1000
    
    def get_next_refnum(self):
        """Get next reference number."""
        self.refnum_counter += 1
        return self.refnum_counter
    
    def clean_string(self, s):
        """Clean string for IIF format."""
        if pd.isna(s) or s is None:
            return ''
        s = str(s).strip()
        # Remove any remaining control characters
        s = ''.join(char for char in s if char.isprintable() or char in '\n\r\t')
        # Quote if contains special characters
        if '\t' in s or ',' in s or '"' in s:
            s = s.replace('"', '""')
            s = f'"{s}"'
        return s
    
    def write_iif_header(self, f, record_type, fields):
        """Write IIF header line."""
        f.write(f"!{record_type}\t" + "\t".join(fields) + "\n")
    
    def write_iif_record(self, f, record_type, values):
        """Write IIF data record."""
        cleaned_values = [self.clean_string(v) for v in values]
        f.write(f"{record_type}\t" + "\t".join(cleaned_values) + "\n")
    
    def convert_chart_of_accounts(self, input_file=None):
        """Convert Chart of Accounts to QuickBooks IIF format."""
        print("\n" + "="*60)
        print("Converting Chart of Accounts")
        print("="*60)
        
        # Try to load from decoded data first
        if input_file is None:
            decoded_file = self.input_dir / "bank_accounts_decoded.csv"
            if decoded_file.exists():
                input_file = decoded_file
        
        if input_file is None or not Path(input_file).exists():
            print("[WARNING] No Chart of Accounts file found")
            print("Please export from Manager and save as 'manager_chart_of_accounts.csv'")
            return None
        
        df = pd.read_csv(input_file)
        print(f"[OK] Loaded {len(df)} accounts from {Path(input_file).name}")
        
        output_file = self.output_dir / "ChartOfAccounts_Import.IIF"
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Write IIF header
            f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
            f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%Y-%m-%d')}\t{self.timestamp}\tN\t0\n")
            
            # Write account header
            fields = ["NAME", "REFNUM", "TIMESTAMP", "ACCNTTYPE", "OBAMOUNT", "DESC", 
                     "ACCNUM", "SCD", "BANKNUM", "EXTRA", "HIDDEN", "DELCOUNT", "USEID"]
            self.write_iif_header(f, "ACCNT", fields)
            
            # Process each account
            for idx, row in df.iterrows():
                name = row.get('name', '')
                if not name or len(name) < 2:
                    continue
                
                # Determine account type based on name patterns
                name_lower = name.lower()
                if any(word in name_lower for word in ['income', 'sales', 'revenue', 'rental']):
                    accnt_type = 'INC'
                elif any(word in name_lower for word in ['expense', 'cost', 'fee', 'charge', 'tax', 'insurance', 'repair', 'fuel', 'electric']):
                    accnt_type = 'EXP'
                elif 'bank' in name_lower or 'checking' in name_lower or 'savings' in name_lower:
                    accnt_type = 'BANK'
                elif 'receivable' in name_lower:
                    accnt_type = 'AR'
                elif 'payable' in name_lower:
                    accnt_type = 'AP'
                elif 'equity' in name_lower or 'capital' in name_lower or 'drawing' in name_lower:
                    accnt_type = 'EQUITY'
                elif 'asset' in name_lower:
                    accnt_type = 'OCASSET'
                elif 'liability' in name_lower or 'loan' in name_lower:
                    accnt_type = 'OCLIAB'
                elif 'credit card' in name_lower or 'citicard' in name_lower:
                    accnt_type = 'CCARD'
                else:
                    # Default based on common patterns
                    if name_lower.startswith(('interest', 'dividend', 'gain')):
                        accnt_type = 'EXINC'
                    else:
                        accnt_type = 'EXP'  # Default to expense
                
                refnum = self.get_next_refnum()
                timestamp = self.timestamp
                ob_amount = "0.00"  # Opening balance - will be set separately
                desc = name
                accnum = ""
                scd = "0" if accnt_type in ['BANK', 'AR', 'AP'] else ""
                banknum = ""
                extra = ""
                hidden = "N"
                delcount = "0"
                useid = "N"
                
                values = [name, refnum, timestamp, accnt_type, ob_amount, desc,
                         accnum, scd, banknum, extra, hidden, delcount, useid]
                self.write_iif_record(f, "ACCNT", values)
            
            f.write("\n")
        
        print(f"[OK] Created: {output_file.name}")
        print(f"[OK] Converted {len(df)} accounts")
        return output_file
    
    def convert_customers(self, input_file=None):
        """Convert Customers to QuickBooks IIF format."""
        print("\n" + "="*60)
        print("Converting Customers")
        print("="*60)
        
        # Try to load from decoded data
        if input_file is None:
            decoded_file = self.input_dir / "customers_decoded.csv"
            if decoded_file.exists():
                input_file = decoded_file
        
        if input_file is None or not Path(input_file).exists():
            print("[WARNING] No Customers file found")
            return None
        
        df = pd.read_csv(input_file)
        print(f"[OK] Loaded {len(df)} customers from {Path(input_file).name}")
        
        output_file = self.output_dir / "Customers_Import.IIF"
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Write IIF header
            f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
            f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%Y-%m-%d')}\t{self.timestamp}\tN\t0\n")
            
            # Write customer name dictionary (required by QB)
            f.write("!CUSTNAMEDICT\tINDEX\tLABEL\tCUSTOMER\tVENDOR\tEMPLOYEE\n")
            f.write("!ENDCUSTNAMEDICT\n")
            for i in range(30):
                f.write(f"CUSTNAMEDICT\t{i}\t\tN\tN\tN\n")
            f.write("ENDCUSTNAMEDICT\n")
            
            # Write customer header (simplified - key fields only)
            fields = ["NAME", "REFNUM", "TIMESTAMP", "BADDR1", "BADDR2", "BADDR3", 
                     "BADDR4", "BADDR5", "SADDR1", "SADDR2", "SADDR3", "SADDR4", "SADDR5",
                     "PHONE1", "PHONE2", "FAXNUM", "EMAIL", "NOTE", "CONT1", "CONT2",
                     "CTYPE", "TERMS", "TAXABLE", "SALESTAXCODE", "LIMIT", "RESALENUM",
                     "REP", "TAXITEM", "NOTEPAD", "SALUTATION", "COMPANYNAME", "FIRSTNAME",
                     "MIDINIT", "LASTNAME"] + ["CUSTFLD" + str(i) for i in range(1, 16)] + \
                    ["JOBDESC", "JOBTYPE", "JOBSTATUS", "JOBSTART", "JOBPROJEND", "JOBEND",
                     "HIDDEN", "DELCOUNT", "PRICELEVEL"]
            self.write_iif_header(f, "CUST", fields)
            
            # Process each customer
            for idx, row in df.iterrows():
                name = row.get('name', '')
                if not name or len(name) < 2:
                    continue
                
                # Parse address
                address = row.get('address', '')
                addr_parts = address.split(',') if address else []
                baddr1 = addr_parts[0].strip() if len(addr_parts) > 0 else ''
                baddr2 = addr_parts[1].strip() if len(addr_parts) > 1 else ''
                baddr3 = addr_parts[2].strip() if len(addr_parts) > 2 else ''
                baddr4 = ''
                baddr5 = ''
                
                email = row.get('email', '')
                phone1 = ''
                
                refnum = self.get_next_refnum()
                timestamp = self.timestamp
                
                # Build values list (must match fields order)
                values = [
                    name, refnum, timestamp,
                    baddr1, baddr2, baddr3, baddr4, baddr5,  # Billing address
                    '', '', '', '', '',  # Shipping address (empty)
                    phone1, '', '', email, '',  # Contact info
                    '', '',  # CONT1, CONT2
                    '', '', 'N', '', '', '',  # CTYPE, TERMS, TAXABLE, etc.
                    '', '', '', '',  # REP, TAXITEM, NOTEPAD, SALUTATION
                    name, '', '', ''  # COMPANYNAME, FIRSTNAME, MIDINIT, LASTNAME
                ]
                # Add 15 custom fields (empty)
                values.extend([''] * 15)
                # Add job fields
                values.extend(['', '', '', '', '', '', 'N', '0', ''])
                
                self.write_iif_record(f, "CUST", values)
            
            f.write("\n")
        
        print(f"[OK] Created: {output_file.name}")
        print(f"[OK] Converted {len(df)} customers")
        return output_file
    
    def convert_vendors(self, input_file=None):
        """Convert Vendors/Suppliers to QuickBooks IIF format."""
        print("\n" + "="*60)
        print("Converting Vendors")
        print("="*60)
        
        # For now, create empty vendor file as we don't have vendor data decoded
        output_file = self.output_dir / "Vendors_Import.IIF"
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
            f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%Y-%m-%d')}\t{self.timestamp}\tN\t0\n")
            f.write("!CUSTNAMEDICT\tINDEX\tLABEL\tCUSTOMER\tVENDOR\tEMPLOYEE\n")
            f.write("!ENDCUSTNAMEDICT\n")
            for i in range(30):
                f.write(f"CUSTNAMEDICT\t{i}\t\tN\tN\tN\n")
            f.write("ENDCUSTNAMEDICT\n")
            f.write("!VEND\tNAME\tREFNUM\tTIMESTAMP\tPRINTAS\tADDR1\tADDR2\tADDR3\tADDR4\tADDR5\n")
            f.write("\n")
        
        print(f"[OK] Created empty vendor file: {output_file.name}")
        print("[INFO] You can manually add vendors or export from Manager")
        return output_file
    
    def convert_items(self, input_file=None):
        """Convert Items/Services to QuickBooks IIF format."""
        print("\n" + "="*60)
        print("Converting Items/Services")
        print("="*60)
        
        # Try to load from decoded data
        if input_file is None:
            decoded_file = self.input_dir / "items_services_decoded.csv"
            if decoded_file.exists():
                input_file = decoded_file
        
        if input_file is None or not Path(input_file).exists():
            print("[WARNING] No Items file found")
            return None
        
        df = pd.read_csv(input_file)
        print(f"[OK] Loaded {len(df)} items from {Path(input_file).name}")
        
        output_file = self.output_dir / "Items_Import.IIF"
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Write IIF header
            f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
            f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%Y-%m-%d')}\t{self.timestamp}\tN\t0\n")
            
            # Write item dictionary
            f.write("!CUSTITEMDICT\tINDEX\tLABEL\tINUSE\n")
            f.write("!ENDCUSTITEMDICT\n")
            for i in range(15):
                f.write(f"CUSTITEMDICT\t{i}\t\tN\n")
            f.write("ENDCUSTITEMDICT\n")
            
            # Write item header
            fields = ["NAME", "REFNUM", "TIMESTAMP", "INVITEMTYPE", "DESC", "PURCHASEDESC",
                     "ACCNT", "ASSETACCNT", "COGSACCNT", "QNTY", "QNTY", "PRICE", "COST",
                     "TAXABLE", "SALESTAXCODE", "PAYMETH", "TAXVEND", "PREFVEND", "REORDERPOINT",
                     "EXTRA", "CUSTFLD1", "CUSTFLD2", "CUSTFLD3", "CUSTFLD4", "CUSTFLD5",
                     "DEP_TYPE", "ISPASSEDTHRU", "HIDDEN", "DELCOUNT", "USEID", "ISNEW"]
            self.write_iif_header(f, "INVITEM", fields)
            
            # Process each item
            for idx, row in df.iterrows():
                name = row.get('name', '')
                if not name or len(name) < 1 or name == '0':
                    continue
                
                desc = row.get('description', name)
                
                # Determine item type and income account
                name_lower = name.lower()
                if 'storage' in name_lower or 'rental' in name_lower:
                    item_type = 'SERV'
                    accnt = 'Rental Income'
                elif 'electric' in name_lower or 'reimburs' in name_lower:
                    item_type = 'OTHC'
                    accnt = 'Reimbursement'
                else:
                    item_type = 'SERV'
                    accnt = 'Income'
                
                refnum = self.get_next_refnum()
                timestamp = self.timestamp
                
                values = [
                    name, refnum, timestamp, item_type, desc, desc,
                    accnt, '', '',  # ACCNT, ASSETACCNT, COGSACCNT
                    '', '', '0.00', '0.00',  # QNTY, QNTY, PRICE, COST
                    'N', '', '', '', '', '',  # TAXABLE, SALESTAXCODE, etc.
                    '0', '', '', '', '', '',  # EXTRA, CUSTFLD1-5
                    '', 'N', 'N', '0', 'N', 'Y'  # DEP_TYPE, ISPASSEDTHRU, etc.
                ]
                
                self.write_iif_record(f, "INVITEM", values)
            
            f.write("\n")
        
        print(f"[OK] Created: {output_file.name}")
        print(f"[OK] Converted {len(df)} items")
        return output_file
    
    def create_opening_balance_template(self):
        """Create a template for entering opening balances."""
        print("\n" + "="*60)
        print("Creating Opening Balance Template")
        print("="*60)
        
        template_file = self.output_dir / "OPENING_BALANCES_TEMPLATE.txt"
        
        with open(template_file, 'w', encoding='utf-8') as f:
            f.write("OPENING BALANCES TEMPLATE\n")
            f.write("="*60 + "\n\n")
            f.write("Instructions:\n")
            f.write("1. Export Trial Balance from Manager as of the earliest date\n")
            f.write("2. Enter opening balances for each account below\n")
            f.write("3. Save this file and run the converter again\n\n")
            f.write("Format: AccountName | Debit | Credit\n")
            f.write("-"*60 + "\n\n")
            f.write("# Example:\n")
            f.write("# Fulton Bank | 39023.18 | 0.00\n")
            f.write("# Accounts Receivable | 17976.64 | 0.00\n")
            f.write("# Accounts Payable | 0.00 | 5000.00\n\n")
            f.write("# Enter your opening balances below:\n")
            f.write("-"*60 + "\n\n")
        
        print(f"[OK] Created: {template_file.name}")
        return template_file
    
    def convert_all(self):
        """Convert all available data."""
        print("\n" + "="*60)
        print("Manager to QuickBooks Converter")
        print("="*60)
        print(f"Input Directory: {self.input_dir}")
        print(f"Output Directory: {self.output_dir}")
        
        results = {}
        
        # Convert Chart of Accounts
        results['accounts'] = self.convert_chart_of_accounts()
        
        # Convert Customers
        results['customers'] = self.convert_customers()
        
        # Convert Vendors
        results['vendors'] = self.convert_vendors()
        
        # Convert Items
        results['items'] = self.convert_items()
        
        # Create opening balance template
        results['ob_template'] = self.create_opening_balance_template()
        
        print("\n" + "="*60)
        print("Conversion Complete!")
        print("="*60)
        print(f"\nOutput files in: {self.output_dir}")
        print("\nFiles created:")
        for key, filepath in results.items():
            if filepath:
                print(f"  - {Path(filepath).name}")
        
        print("\n" + "="*60)
        print("Next Steps:")
        print("="*60)
        print("1. Review the IIF files created")
        print("2. Import into QuickBooks in this order:")
        print("   a. ChartOfAccounts_Import.IIF")
        print("   b. Customers_Import.IIF")
        print("   c. Vendors_Import.IIF (add vendors manually if needed)")
        print("   d. Items_Import.IIF")
        print("3. Create opening balance journal entry in QuickBooks")
        print("4. For transactions, export General Ledger from Manager")
        print("   and we'll create a transaction import script")
        
        return results

def main():
    """Main entry point."""
    input_dir = r"C:\Scripts\Manager2QB\manager_decoded"
    output_dir = r"C:\Scripts\Manager2QB\quickbooks_import"
    
    converter = ManagerToQBConverter(input_dir, output_dir)
    converter.convert_all()

if __name__ == "__main__":
    main()
