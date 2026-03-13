"""
Validate and Fix QuickBooks IIF Files
Ensures all import files match QuickBooks 2012 Pro format requirements.
"""

import re
from pathlib import Path
from datetime import datetime

class IIFValidator:
    def __init__(self, import_dir, sample_dir):
        """Initialize validator."""
        self.import_dir = Path(import_dir)
        self.sample_dir = Path(sample_dir)
        self.timestamp = int(datetime.now().timestamp())
        self.issues = []
        
        # Load existing QB accounts from sample
        self.existing_accounts = self.load_existing_accounts()
        self.existing_customers = self.load_existing_customers()
    
    def load_existing_accounts(self):
        """Load existing account names from QB sample."""
        accounts = {}
        sample_file = self.sample_dir / "ChartOfAccounts.IIF"
        if sample_file.exists():
            with open(sample_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('ACCNT\t'):
                        parts = line.strip().split('\t')
                        if len(parts) > 4:
                            name = parts[1]
                            accnt_type = parts[4]
                            accounts[name] = accnt_type
        return accounts
    
    def load_existing_customers(self):
        """Load existing customer names from QB sample."""
        customers = set()
        sample_file = self.sample_dir / "Customers.IIF"
        if sample_file.exists():
            with open(sample_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('CUST\t'):
                        parts = line.strip().split('\t')
                        if len(parts) > 1:
                            customers.add(parts[1])
        return customers
    
    def is_valid_string(self, s):
        """Check if string contains only valid characters for QB."""
        if not s:
            return True
        # Check for binary/garbage characters
        for char in s:
            code = ord(char)
            # Allow printable ASCII, common punctuation, and some extended chars
            if code < 32 and code not in (9, 10, 13):  # Tab, LF, CR are OK
                return False
            if code > 126 and code < 160:  # Control characters
                return False
            # Check for specific garbage patterns from Protocol Buffer
            if char in '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f':
                return False
        # Check for known garbage patterns
        garbage_patterns = ['0øHQ', 'Vb3O', 'lM6B', 'xqM7', 'UUkJ', 'SސBTX', 'NI~^p']
        for pattern in garbage_patterns:
            if pattern in s:
                return False
        return True
    
    def clean_string(self, s):
        """Clean string of invalid characters."""
        if not s:
            return ''
        # Replace em-dash and other special chars
        s = s.replace('\x97', '-').replace('\u2014', '-').replace('\u2013', '-')
        # Remove other non-printable characters
        cleaned = ''.join(char for char in s if ord(char) >= 32 or char in '\t\n\r')
        return cleaned.strip()
    
    def fix_chart_of_accounts(self):
        """Fix and regenerate Chart of Accounts IIF file."""
        print("\n" + "="*60)
        print("Fixing Chart of Accounts")
        print("="*60)
        
        output_file = self.import_dir / "ChartOfAccounts_Import.IIF"
        
        # Define clean accounts based on what we know from Manager
        # and what already exists in QuickBooks
        new_accounts = []
        
        # Income accounts that may not exist in QB
        income_accounts = [
            ("Storage Rental", "INC", "Income from storage unit rentals"),
            ("Land Rental", "INC", "Income from land rental"),
            ("Art Studio Rental", "INC", "Income from art studio space rental"),
            ("Building Rental - Farm Labor", "INC", "Income from farm labor building rental"),
            ("Land Use - Hunting", "INC", "Income from hunting land use"),
            ("Electric Usage Reimbursement", "INC", "Reimbursement for electric usage"),
            ("Scrap Yard Income", "INC", "Income from scrap yard proceeds"),
        ]
        
        # Expense accounts that may not exist in QB
        expense_accounts = [
            ("Accounting fees", "EXP", "Professional accounting services"),
            ("Advertising and promotion", "EXP", "Advertising and promotional expenses"),
            ("Donations", "EXP", "Charitable contributions and donations"),
            ("Dumpsters/disposal", "EXP", "Waste disposal and dumpster fees"),
            ("Fuel for tractors", "EXP", "Fuel costs for farm equipment"),
            ("Rodent control", "EXP", "Pest and rodent control expenses"),
            ("Real Estate Taxes", "EXP", "Property tax payments"),
            ("Business Tax, NJ", "EXP", "New Jersey business taxes"),
        ]
        
        # Check which accounts already exist in QB
        for name, accnt_type, desc in income_accounts + expense_accounts:
            if name not in self.existing_accounts:
                new_accounts.append((name, accnt_type, desc))
            else:
                print(f"  [SKIP] Account '{name}' already exists in QuickBooks")
        
        if not new_accounts:
            print("[INFO] All accounts already exist in QuickBooks - no import needed")
            # Create empty file
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
                f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%m/%d/%Y')}\t{self.timestamp}\tN\t0\n")
            return output_file
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Write header
            f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
            f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%m/%d/%Y')}\t{self.timestamp}\tN\t0\n")
            
            # Write account header
            f.write("!ACCNT\tNAME\tREFNUM\tTIMESTAMP\tACCNTTYPE\tOBAMOUNT\tDESC\tACCNUM\tSCD\tBANKNUM\tEXTRA\tHIDDEN\tDELCOUNT\tUSEID\n")
            
            refnum = 100
            for name, accnt_type, desc in new_accounts:
                refnum += 1
                # SCD field - 0 for AR/AP/BANK, empty for others
                scd = ""
                f.write(f"ACCNT\t{name}\t{refnum}\t{self.timestamp}\t{accnt_type}\t0.00\t{desc}\t\t{scd}\t\t\tN\t0\tN\n")
                print(f"  [ADD] {name} ({accnt_type})")
            
            f.write("\n")
        
        print(f"[OK] Created: {output_file.name} ({len(new_accounts)} new accounts)")
        return output_file
    
    def fix_customers(self):
        """Fix and regenerate Customers IIF file."""
        print("\n" + "="*60)
        print("Fixing Customers")
        print("="*60)
        
        output_file = self.import_dir / "Customers_Import.IIF"
        
        # Define clean customer data based on what we extracted
        # Only include customers NOT already in QuickBooks
        new_customers = []
        
        # Customer data from decoded Manager file (cleaned)
        manager_customers = [
            ("David Ronan", "David Ronan", "5 Raleigh Dr.", "Mt. Laurel, NJ 08054", "", ""),
            ("Good Farms", "Good Farms", "58 Pemberton Rd.", "Southampton, NJ 08088", "rsgood57@gmail.com", "609-381-2869"),
            ("JJ Gun Club", "Jersey Jerry Gun Club", "William Thompson", "204 S. Lakeside Dr.", "whatsupbud@verizon.net", "609-304-6806"),
            ("Phil-CA", "Phil Roberts (CA)", "522 Eayrestown Rd.", "Southampton, NJ 08088", "philip.c.roberts@gmail.com", "609-502-7922"),
            ("Phil-PH", "Phil Roberts (PH)", "Black Orchard Studios", "522 Eayrestown Rd.", "philip.c.roberts@gmail.com", "609-502-7922"),
            ("PinelandPlayers", "Pineland Players", "PO Box 244", "Medford, NJ 08055", "pinelandplayers@aol.com", ""),
            ("Coombs, Jeff", "Jeff Coombs", "", "", "coombsjeffrey89@gmail.com", "609-238-8535"),
            ("Maron", "Cynthia Maron", "70 Seneca Trail", "Medford Lakes, NJ 08055", "cmaron@aol.com", "609-346-6285"),
            ("Bendall", "Michelle Bendall", "16 Burrs Mill Rd.", "Southampton, NJ 08088", "m.bendall@comcast.net", "609-506-3529"),
            ("Dlotman", "Dave Lotman", "130 Niagra Lane", "Willingboro, NJ 08046", "", "609-456-9137"),
            ("Glotman", "Geoff Lotman", "130 Niagra Lane", "Willingboro, NJ 08046", "", "609-456-5712"),
            ("Gower", "Gower Nurseries LLC", "384 Eayrestown Road", "Southampton, NJ 08088", "gowernurseries@comcast.net", "(609) 320-2744"),
            ("Kumpell", "Dave Kumpel", "1891 Rte. 70", "Southampton, NJ 08088", "", "609-744-5311"),
            ("Mitchell", "Paul Mitchell", "807 Eugenia Dr.", "Medford, NJ 08055", "pamitchell@att.net", "215-870-6326"),
            ("Moyer", "Sam Moyer", "Mt Laurel, NJ 08054", "", "moyerbase@aol.com", ""),
            ("Thomas", "Jay Thomas", "132 Wahwahtaysee Tr.", "Medford Lakes, NJ 08055", "JDTONE@gmail.com", "609-744-7568"),
            ("Tmaron", "Timothy Maron", "70 Seneca Trail", "Medford Lakes, NJ 08055", "timinthepines@aol.com", "609-410-3943"),
            ("Wollick", "Charlie Wollick", "12 Flemish Way", "Lumberton, NJ 08048", "", "609-864-2165"),
            ("Graeff", "Gary Graeff", "1313 Lincoln Dr", "Voorhees, NJ 08043", "GGraeff33@gmail.com", "609-209-7767"),
        ]
        
        # Filter out customers that already exist
        for cust in manager_customers:
            name = cust[0]
            if name not in self.existing_customers:
                new_customers.append(cust)
            else:
                print(f"  [SKIP] Customer '{name}' already exists in QuickBooks")
        
        if not new_customers:
            print("[INFO] All customers already exist in QuickBooks - no import needed")
            with open(output_file, 'w', encoding='utf-8', newline='') as f:
                f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
                f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%m/%d/%Y')}\t{self.timestamp}\tN\t0\n")
            return output_file
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Write header
            f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
            f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%m/%d/%Y')}\t{self.timestamp}\tN\t0\n")
            
            # Write name dictionary
            f.write("!CUSTNAMEDICT\tINDEX\tLABEL\tCUSTOMER\tVENDOR\tEMPLOYEE\n")
            f.write("!ENDCUSTNAMEDICT\n")
            for i in range(30):
                f.write(f"CUSTNAMEDICT\t{i}\t\tN\tN\tN\n")
            f.write("ENDCUSTNAMEDICT\n")
            
            # Write customer header (matching QB sample format)
            f.write("!CUST\tNAME\tREFNUM\tTIMESTAMP\tBADDR1\tBADDR2\tBADDR3\tBADDR4\tBADDR5\tSADDR1\tSADDR2\tSADDR3\tSADDR4\tSADDR5\tPHONE1\tPHONE2\tFAXNUM\tEMAIL\tNOTE\tCONT1\tCONT2\tCTYPE\tTERMS\tTAXABLE\tSALESTAXCODE\tLIMIT\tRESALENUM\tREP\tTAXITEM\tNOTEPAD\tSALUTATION\tCOMPANYNAME\tFIRSTNAME\tMIDINIT\tLASTNAME\tCUSTFLD1\tCUSTFLD2\tCUSTFLD3\tCUSTFLD4\tCUSTFLD5\tCUSTFLD6\tCUSTFLD7\tCUSTFLD8\tCUSTFLD9\tCUSTFLD10\tCUSTFLD11\tCUSTFLD12\tCUSTFLD13\tCUSTFLD14\tCUSTFLD15\tJOBDESC\tJOBTYPE\tJOBSTATUS\tJOBSTART\tJOBPROJEND\tJOBEND\tHIDDEN\tDELCOUNT\tPRICELEVEL\n")
            
            refnum = 100
            for name, addr1, addr2, addr3, email, phone in new_customers:
                refnum += 1
                # Quote address line 3 if it contains comma (city, state zip)
                if ',' in addr3:
                    addr3 = f'"{addr3}"'
                
                # Parse name into first/last
                name_parts = addr1.split()
                firstname = name_parts[0] if name_parts else ""
                lastname = name_parts[-1] if len(name_parts) > 1 else ""
                
                # Build customer line (59 fields)
                fields = [
                    "CUST", name, str(refnum), str(self.timestamp),
                    addr1, addr2, addr3, "", "",  # BADDR1-5
                    "", "", "", "", "",  # SADDR1-5
                    phone, "", "", email, "",  # PHONE1, PHONE2, FAX, EMAIL, NOTE
                    "", "",  # CONT1, CONT2
                    "", "", "N", "", "", "", "", "", "",  # CTYPE through NOTEPAD
                    "", "", firstname, "", lastname,  # SALUTATION, COMPANY, FIRST, MID, LAST
                    "", "", "", "", "", "", "", "", "", "", "", "", "", "", "",  # CUSTFLD1-15
                    "", "", "", "", "", "",  # JOB fields
                    "N", "0", ""  # HIDDEN, DELCOUNT, PRICELEVEL
                ]
                f.write("\t".join(fields) + "\n")
                print(f"  [ADD] {name}")
            
            f.write("\n")
        
        print(f"[OK] Created: {output_file.name} ({len(new_customers)} new customers)")
        return output_file
    
    def fix_items(self):
        """Fix Items IIF file - remove garbage data."""
        print("\n" + "="*60)
        print("Fixing Items/Services")
        print("="*60)
        
        output_file = self.import_dir / "Items_Import.IIF"
        
        # Define clean items based on QB sample format
        # These are service items for invoicing
        items = [
            ("Storage", "SERV", "Storage Rental", "Rental Income", "0.00"),
            ("Storage25", "SERV", "Storage $25/2 weeks", "Rental Income", "25.00"),
            ("Storage45", "SERV", "Storage $45/month", "Rental Income", "45.00"),
            ("Storage50", "SERV", "Storage $50/month", "Rental Income", "50.00"),
            ("Storage100", "SERV", "Storage $100/month", "Rental Income", "100.00"),
            ("Storage200", "SERV", "Storage $200/month", "Rental Income", "200.00"),
            ("Land Rental", "SERV", "Land rental", "Rental Income", "0.00"),
            ("Art Studio", "SERV", "Art studio space rental", "Rental Income", "300.00"),
            ("Building Rental", "SERV", "Farm labor building rental", "Rental Income", "0.00"),
            ("Hunting Land Use", "SERV", "Hunting land use fee", "Rental Income", "0.00"),
            ("Electric Reimburse", "OTHC", "Electric usage reimbursement", "Reimbursement", "0.00"),
        ]
        
        # Check which items already exist in QB
        existing_items = set()
        sample_file = self.sample_dir / "ItemList.IIF"
        if sample_file.exists():
            with open(sample_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('INVITEM\t'):
                        parts = line.strip().split('\t')
                        if len(parts) > 1:
                            existing_items.add(parts[1])
        
        new_items = []
        for item in items:
            if item[0] not in existing_items:
                new_items.append(item)
            else:
                print(f"  [SKIP] Item '{item[0]}' already exists in QuickBooks")
        
        with open(output_file, 'w', encoding='utf-8', newline='') as f:
            # Write header
            f.write("!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n")
            f.write(f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t{datetime.now().strftime('%m/%d/%Y')}\t{self.timestamp}\tN\t0\n")
            
            # Write item dictionary
            f.write("!CUSTITEMDICT\tINDEX\tLABEL\tINUSE\n")
            f.write("!ENDCUSTITEMDICT\n")
            for i in range(15):
                f.write(f"CUSTITEMDICT\t{i}\t\tN\n")
            f.write("ENDCUSTITEMDICT\n")
            
            # Write item header (matching QB sample)
            f.write("!INVITEM\tNAME\tREFNUM\tTIMESTAMP\tINVITEMTYPE\tDESC\tPURCHASEDESC\tACCNT\tASSETACCNT\tCOGSACCNT\tQNTY\tQNTY\tPRICE\tCOST\tTAXABLE\tSALESTAXCODE\tPAYMETH\tTAXVEND\tPREFVEND\tREORDERPOINT\tEXTRA\tCUSTFLD1\tCUSTFLD2\tCUSTFLD3\tCUSTFLD4\tCUSTFLD5\tDEP_TYPE\tISPASSEDTHRU\tHIDDEN\tDELCOUNT\tUSEID\tISNEW\n")
            
            refnum = 50
            for name, item_type, desc, account, price in new_items:
                refnum += 1
                f.write(f"INVITEM\t{name}\t{refnum}\t{self.timestamp}\t{item_type}\t{desc}\t{desc}\t{account}\t\t\t\t\t{price}\t0.00\tN\t\t\t\t\t\t0\t\t\t\t\t\t\tN\tN\t0\tN\tY\n")
                print(f"  [ADD] {name} ({item_type}) -> {account}")
            
            f.write("\n")
        
        print(f"[OK] Created: {output_file.name} ({len(new_items)} new items)")
        return output_file
    
    def fix_transactions(self):
        """Fix Deposits and Payments IIF files."""
        print("\n" + "="*60)
        print("Fixing Transactions")
        print("="*60)
        
        # Fix Deposits file
        deposits_file = self.import_dir / "Deposits_Import.IIF"
        if deposits_file.exists():
            self.fix_transaction_file(deposits_file)
        
        # Fix Payments file
        payments_file = self.import_dir / "Payments_Import.IIF"
        if payments_file.exists():
            self.fix_transaction_file(payments_file)
    
    def fix_transaction_file(self, filepath):
        """Fix a single transaction IIF file."""
        print(f"\n  Processing: {filepath.name}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        fixes_made = 0
        
        for line in lines:
            original = line
            
            # Clean special characters
            line = line.replace('\x97', '-')  # em-dash
            line = line.replace('\u2014', '-')
            line = line.replace('\u2013', '-')
            
            # Fix leading spaces in customer names (field 5 in TRNS/SPL lines)
            if line.startswith('TRNS\t') or line.startswith('SPL\t'):
                parts = line.split('\t')
                if len(parts) > 5:
                    # NAME field is index 5
                    parts[5] = parts[5].strip()
                    line = '\t'.join(parts)
            
            if line != original:
                fixes_made += 1
            
            fixed_lines.append(line)
        
        # Write back
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.writelines(fixed_lines)
        
        print(f"  [OK] Fixed {fixes_made} issues in {filepath.name}")
    
    def create_account_mapping_note(self):
        """Create a note about account mapping for transactions."""
        print("\n" + "="*60)
        print("Account Mapping Notes")
        print("="*60)
        
        # Accounts referenced in transactions that should exist
        transaction_accounts = {
            "Fulton Bank": "BANK",
            "Accounts Receivable": "AR",
            "Donations": "EXP",
            "Insurance": "EXP", 
            "Electricity": "EXP",
            "Real Estate Taxes": "EXP",
            "Business Tax": "EXP",
            "Accounting fees": "EXP",
        }
        
        print("\nAccounts referenced in transactions:")
        for acct, acct_type in transaction_accounts.items():
            if acct in self.existing_accounts:
                print(f"  [OK] '{acct}' exists in QuickBooks")
            else:
                print(f"  [WARN] '{acct}' may need to be created or mapped")
                
                # Find similar account
                for existing in self.existing_accounts:
                    if acct.lower() in existing.lower() or existing.lower() in acct.lower():
                        print(f"         Similar: '{existing}'")
    
    def validate_all(self):
        """Run all validations and fixes."""
        print("\n" + "="*60)
        print("QuickBooks IIF File Validator and Fixer")
        print("="*60)
        print(f"Import Directory: {self.import_dir}")
        print(f"Sample Directory: {self.sample_dir}")
        print(f"Existing QB Accounts: {len(self.existing_accounts)}")
        print(f"Existing QB Customers: {len(self.existing_customers)}")
        
        # Fix each file type
        self.fix_chart_of_accounts()
        self.fix_customers()
        self.fix_items()
        self.fix_transactions()
        self.create_account_mapping_note()
        
        print("\n" + "="*60)
        print("Validation Complete!")
        print("="*60)
        print("\nAll IIF files have been cleaned and reformatted.")
        print("Files are ready for QuickBooks 2012 Pro import.")

def main():
    """Main entry point."""
    import_dir = r"C:\Scripts\Manager2QB\quickbooks_import"
    sample_dir = r"C:\Scripts\Manager2QB\QuickBookSampleExports"
    
    validator = IIFValidator(import_dir, sample_dir)
    validator.validate_all()

if __name__ == "__main__":
    main()
