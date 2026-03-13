# Manager to QuickBooks Conversion - Analysis & Plan

## Date: 2026-01-29

---

## Phase 1 Complete: Database Exploration

### Manager Database Structure

**Source File**: `Roberts Orchards LLC (2026-01-29-1559).manager`

**Database Format**: SQLite 3 with Protocol Buffer encoded data

**Tables Found**:
- **Blobs** (0 rows) - Binary large objects storage
- **Blobs2** (0 rows) - Alternative blob storage
- **Changes** (985 rows) - Transaction history/audit log
- **Emails** (15 rows) - Email records
- **Images** (2 rows) - Image attachments
- **Objects** (486 rows) - **PRIMARY DATA TABLE** containing all accounting entities

### Key Finding: Objects Table

The `Objects` table contains ALL accounting data encoded in Protocol Buffer format:
- Chart of Accounts (Income, Expense accounts visible in sample)
- Customers (e.g., "David Ronan", "Good Farms", "JJ Gun Club", "Phil-CA", "Phil-PH")
- Bank Accounts (e.g., "Fulton Bank", "Live Oak Bank", "Morgan Stanley")
- Items/Services (e.g., "Land Rental", "Storage Rental")
- Invoices and transactions

**ContentType** field appears to be a GUID identifying the object type.

---

## QuickBooks Target Format Analysis

### IIF File Structure

QuickBooks IIF (Intuit Interchange Format) is a tab-delimited text format:

**Header Structure**:
```
!HDR	PROD	VER	REL	IIFVER	DATE	TIME	ACCNTNT	ACCNTNTSPLITTIME
HDR	QuickBooks Pro	Version 22.0D	Release R16P	1	2026-01-29	[timestamp]	N	0
```

### 1. Chart of Accounts (ChartOfAccounts.IIF)

**Format**:
```
!ACCNT	NAME	REFNUM	TIMESTAMP	ACCNTTYPE	OBAMOUNT	DESC	ACCNUM	SCD	BANKNUM	EXTRA	HIDDEN	DELCOUNT	USEID
ACCNT	[Name]	[RefNum]	[Timestamp]	[Type]	[OpeningBalance]	[Description]	[AccountNumber]	[SCD]	[BankNum]	[Extra]	N	0	N
```

**Account Types**:
- BANK - Bank accounts
- AR - Accounts Receivable
- AP - Accounts Payable
- OCASSET - Other Current Asset
- FIXASSET - Fixed Asset
- CCARD - Credit Card
- EQUITY - Equity accounts
- INC - Income
- COGS - Cost of Goods Sold
- EXP - Expense
- EXINC - Other Income
- EXEXP - Other Expense

**Key Fields**:
- NAME: Account name
- ACCNTTYPE: Account type (see above)
- OBAMOUNT: Opening balance (quoted if contains comma)
- DESC: Description
- ACCNUM: Account number
- EXTRA: Special flags (INVENTORYASSET, UNDEPOSIT, OPENBAL, RETEARNINGS, COGS, UNCATINC, UNCATEXP)

### 2. Customers (Customers.IIF)

**Format**:
```
!CUST	NAME	REFNUM	TIMESTAMP	BADDR1	BADDR2	BADDR3	BADDR4	BADDR5	...	EMAIL	...	COMPANYNAME	FIRSTNAME	MIDINIT	LASTNAME	...
CUST	[Name]	[RefNum]	[Timestamp]	[Address1]	[Address2]	[City,State,Zip]	...	[Email]	...	[Company]	[First]	[MI]	[Last]	...
```

**Key Fields**:
- NAME: Customer ID/short name
- BADDR1-5: Billing address lines
- PHONE1, PHONE2: Phone numbers
- EMAIL: Email address
- COMPANYNAME, FIRSTNAME, LASTNAME: Name components

### 3. Vendors (Vendors.IIF)

**Format**:
```
!VEND	NAME	REFNUM	TIMESTAMP	PRINTAS	ADDR1	ADDR2	ADDR3	ADDR4	ADDR5	...	COMPANYNAME	FIRSTNAME	MIDINIT	LASTNAME	...
VEND	[Name]	[RefNum]	[Timestamp]	[PrintAs]	[Address1]	[Address2]	[City,State,Zip]	...	[Company]	[First]	[MI]	[Last]	...
```

**Similar structure to Customers**

### 4. Items/Products (ItemList.IIF)

**Format**:
```
!INVITEM	NAME	REFNUM	TIMESTAMP	INVITEMTYPE	DESC	PURCHASEDESC	ACCNT	...	PRICE	COST	TAXABLE	...
INVITEM	[Name]	[RefNum]	[Timestamp]	[Type]	[Description]	[PurchaseDesc]	[IncomeAccount]	...	[Price]	[Cost]	[N/Y]	...
```

**Item Types**:
- SERV - Service item
- PART - Inventory part
- OTHC - Other Charge

**Key Fields**:
- NAME: Item name
- INVITEMTYPE: Item type
- DESC: Sales description
- ACCNT: Income account
- PRICE: Default sales price
- COST: Default cost

---

## Conversion Strategy

### Challenge: Protocol Buffer Decoding

Manager stores data in Protocol Buffer format (binary). The data is NOT directly readable from CSV exports.

**Options**:
1. **Reverse engineer Protocol Buffer schema** - Complex, time-consuming
2. **Use Manager's export features** - If Manager has built-in export to Excel/CSV
3. **Parse the binary data directly** - Requires understanding Manager's specific protobuf schema
4. **Use Manager's API or CLI** - If available

### Recommended Approach

**QUESTION FOR USER**: Does Manager have built-in export functionality? 
- Can you export reports from Manager (Chart of Accounts, Customer List, Vendor List, etc.)?
- If yes, we should use Manager's native export and convert those files
- If no, we need to decode the Protocol Buffer data

### If Manager Has Export Features:

1. Export from Manager:
   - Chart of Accounts
   - Customer List
   - Vendor List
   - Item List
   - General Ledger or Transaction List
   - Trial Balance (for opening balances)

2. Convert Manager exports to QuickBooks IIF format

### If No Export Features Available:

We need to decode the Protocol Buffer data. From the sample data, I can see:
- Text strings are partially readable (e.g., "Interest received", "Sales", "Fulton Bank")
- Binary data contains GUIDs and encoded values
- Need to identify ContentType GUIDs for each entity type

---

## Opening Balances Strategy

### Approach:
1. Identify the earliest transaction date in Manager
2. Export Trial Balance from Manager as of that date (or calculate from transactions)
3. Create opening balance journal entry in QuickBooks
4. All account balances should be entered as of the start date
5. Then import all transactions chronologically

### QuickBooks Opening Balance Entry:
- Use "Opening Balance Equity" account as the offset
- Create journal entry with all account balances
- Date: Day before first transaction in Manager

---

## Import Order (Once Data is Converted)

1. **Chart of Accounts** - Must be first
2. **Customers** - Before invoices
3. **Vendors** - Before bills
4. **Items/Products** - Before transactions using items
5. **Opening Balances** - Journal entry with all account balances
6. **Transactions** - Import chronologically:
   - Journal Entries
   - Invoices
   - Bills
   - Payments
   - Deposits

---

## Next Steps

**AWAITING USER INPUT**:

1. **Can Manager export data natively?**
   - File → Export → Reports?
   - Any export functionality in Manager?

2. **If yes**: What formats are available? (Excel, CSV, PDF?)

3. **If no**: We'll need to decode the Protocol Buffer data programmatically

Once we know the answer, we can proceed with:
- Creating the appropriate conversion scripts
- Mapping Manager data to QuickBooks format
- Generating IIF files for import

---

## Files Created So Far

1. `manager_explorer.py` - SQLite database explorer
2. `requirements_manager_explorer.txt` - Python dependencies
3. `manager_exports/` - Directory with raw CSV/Excel exports
4. `manager_exports/MANAGER_DATABASE_DOCUMENTATION.md` - Database structure documentation
5. `ANALYSIS_AND_PLAN.md` - This file

---

## Technical Notes

### Manager ContentType GUIDs Observed:
- `26b9e4a5-ce10-4f30-94c7-23a1ca4428f9` - Appears to be Chart of Accounts entries
- `5770616c-0e01-46ca-a172-f7042275da6c` - Account groups (Income, Expenses)
- `f361339b-932a-4436-b56e-a337c1587c72` - Equity accounts
- `1408c33b-6284-4f50-9e31-48cbea21f3cf` - Bank accounts
- `ec37c11e-2b67-49c6-8a58-6eccb7dd75ee` - Customers
- `ad12b60b-23bf-4421-94df-8be79cef533e` - Invoices or recurring invoices
- `0c1000da-6cc3-4448-8245-6f1eeccab8d6` - Transactions or payments
- `7662b887-c8d8-486e-98fd-f9dbcd41c6dc` - Invoice line items

### QuickBooks IIF Requirements:
- Tab-delimited format
- Must include header rows with field names (prefixed with !)
- Quoted fields if they contain commas or special characters
- Specific field order must be maintained
- RefNum and Timestamp fields are important for updates
- Some fields have special values (N/Y for boolean, specific codes for types)
