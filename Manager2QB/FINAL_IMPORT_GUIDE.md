# QuickBooks Import Guide - Complete Instructions

**Business**: Roberts Orchards LLC  
**Date**: January 29, 2026  
**Conversion**: Manager Accounting → QuickBooks Pro 2012

---

## ✓ All Files Ready for Import

All conversion scripts have been run successfully. Your QuickBooks import files are ready in:  
`C:\Scripts\Manager2QB\quickbooks_import\`

---

## Import Files Summary

| File | Records | Description |
|------|---------|-------------|
| **ChartOfAccounts_Import.IIF** | 36 accounts | Income, Expense, Bank accounts |
| **Customers_Import.IIF** | 120 customers | Customer names, addresses, emails |
| **Vendors_Import.IIF** | Empty | Template (add vendors manually) |
| **Items_Import.IIF** | 229 items | Service items for invoicing |
| **Deposits_Import.IIF** | 93 deposits | Customer payments to Fulton Bank |
| **Payments_Import.IIF** | 45 payments | Expenses from Fulton Bank |

**Total Transactions**: 138 (93 deposits + 45 payments)  
**Date Range**: December 18, 2024 - Present  
**Fulton Bank Starting Balance**: $39,023.18

---

## Step-by-Step Import Instructions

### STEP 1: Set Up Fulton Bank Account

**Before importing transactions**, you need the Fulton Bank account in QuickBooks.

**Option A: If Fulton Bank was already in QuickBooks**
- The account should already exist from when you left off
- Verify the balance matches $39,023.18 as of 12/18/2024
- If balance is different, you may need to adjust

**Option B: If Fulton Bank needs to be created**
1. In QuickBooks: Lists → Chart of Accounts
2. Click Account → New
3. Select: Bank
4. Account Name: Fulton Bank
5. Opening Balance: $39,023.18
6. As of: 12/17/2024 (day before first transaction)
7. Click OK

---

### STEP 2: Import Chart of Accounts

**File**: `ChartOfAccounts_Import.IIF`

**Steps**:
1. In QuickBooks: File → Utilities → Import → IIF Files
2. Navigate to: `C:\Scripts\Manager2QB\quickbooks_import\`
3. Select: `ChartOfAccounts_Import.IIF`
4. Click Open
5. QuickBooks will import the accounts

**What Gets Imported**:
- **Income Accounts**: Sales, Interest received, Land Rental, Storage Rental, Art Studio Rental, Building Rental - Farm Labor, Land Use - Hunting, Electric Usage Reimbursement, Scrap Yard Income, Income from Morgan Stanley Investments
- **Expense Accounts**: Accounting fees, Advertising and promotion, Bank charges, Computer equipment, Donations, Electricity, Entertainment, Legal fees, Motor vehicle expenses, Printing and stationery, Rent, Repairs and maintenance, Telephone, Insurance, Dues and Subscriptions, Dumpsters/disposal, CitiCard (house CC), Fuel for tractors, Rodent control, Business Tax NJ, Real Estate Taxes
- **Bank Accounts**: Live Oak Bank, Morgan Stanley (if not already existing)

**After Import**:
1. Go to Lists → Chart of Accounts
2. Review all imported accounts
3. Correct any account types if needed
4. Add account numbers if desired

---

### STEP 3: Import Customers

**File**: `Customers_Import.IIF`

**Steps**:
1. File → Utilities → Import → IIF Files
2. Select: `Customers_Import.IIF`
3. Click Open

**Key Customers Imported**:
- David Ronan
- Good Farms
- JJ Gun Club
- Phil-CA, Phil-PH
- PinelandPlayers
- Michelle Bendall
- Cynthia Maron
- David Dlotman
- Geoff Glotman
- Gower Nurseries
- And 110+ more

**After Import**:
1. Go to: Customers → Customer Center
2. Review customer list
3. Merge any duplicates (right-click → Merge)
4. Update any missing information

---

### STEP 4: Import Items/Services

**File**: `Items_Import.IIF`

**Steps**:
1. File → Utilities → Import → IIF Files
2. Select: `Items_Import.IIF`
3. Click Open

**What Gets Imported**:
- Storage rental items (various unit numbers: 1001, 1004, 1099, 1111, etc.)
- Land rental services
- Electric reimbursement items
- Building rental items

**After Import**:
1. Go to: Lists → Item List
2. Review items
3. Clean up duplicate items if needed
4. Set default prices for commonly used items

---

### STEP 5: Add Vendors (Manual)

**File**: `Vendors_Import.IIF` (empty template)

The Protocol Buffer decoder didn't extract vendor data cleanly. You'll need to add vendors manually.

**Common Vendors to Add** (based on your transactions):
- Klatzkin Accounting (Accountant)
- PSEG (Electric utility)
- American National (Insurance)
- State of NJ (Taxes)
- Twp of Southampton (Property taxes)
- Hampton Lakes Emergency Squad
- NJ Ag Society

**To Add Vendors**:
1. Vendors → Vendor Center
2. Click New Vendor
3. Enter name and details
4. Click OK

---

### STEP 6: Import Deposits (Customer Payments)

**File**: `Deposits_Import.IIF`

**Important**: Import this BEFORE Payments_Import.IIF

**Steps**:
1. File → Utilities → Import → IIF Files
2. Select: `Deposits_Import.IIF`
3. Click Open

**What Gets Imported**:
- 93 customer payments deposited to Fulton Bank
- Dates: 12/18/2024 through present
- Amounts range from $25 to $500
- All deposits reduce Accounts Receivable

**Sample Deposits**:
- 12/18/2024: Glotman - $100.00 (Storage)
- 12/28/2024: Wollick - $80.00 (Storage)
- 12/31/2024: Dlotman - $400.00 (Storage)
- 01/02/2025: Tmaron - $300.00 (Storage)

**After Import**:
1. Go to: Banking → Use Register → Fulton Bank
2. Verify deposits appear correctly
3. Check that Accounts Receivable decreased appropriately

---

### STEP 7: Import Payments (Expenses)

**File**: `Payments_Import.IIF`

**Steps**:
1. File → Utilities → Import → IIF Files
2. Select: `Payments_Import.IIF`
3. Click Open

**What Gets Imported**:
- 45 expense payments from Fulton Bank
- Dates: 01/02/2025 through present
- Various expense categories

**Sample Payments**:
- 01/02/2025: Donations - $75.00 (Hampton Lakes Emergency Squad)
- 01/02/2025: Donations - $50.00 (NJ Ag Society)
- 01/02/2025: Insurance - $85.26 (Trailer insurance)
- 01/09/2025: Insurance - $5,491.00 (Farm package)
- 01/31/2025: Electricity - $434.83 (PSEG Farm)
- 02/03/2025: Real Estate Taxes - $5,358.43 (Southampton Twp)
- 02/07/2025: Business Tax - $1,200.00 (State of NJ)
- 02/10/2025: Accounting fees - $3,450.00 (Klatzkin)

**After Import**:
1. Go to: Banking → Use Register → Fulton Bank
2. Verify all payments appear
3. Check expense accounts have correct amounts

---

### STEP 8: Verify & Reconcile

**Verify Fulton Bank Balance**:
1. Go to: Banking → Use Register → Fulton Bank
2. Check ending balance
3. Should match your current Fulton Bank statement

**Expected Calculation**:
```
Starting Balance (12/17/2024):     $39,023.18
+ Total Deposits:                  (sum of 93 deposits)
- Total Payments:                  (sum of 45 payments)
= Current Balance:                 (should match statement)
```

**Reconcile the Account**:
1. Banking → Reconcile
2. Select: Fulton Bank
3. Enter statement ending date and balance
4. Mark all cleared transactions
5. Reconcile should balance to $0.00 difference

---

## Troubleshooting

### Issue: "Account not found" error
**Solution**: Make sure you imported ChartOfAccounts_Import.IIF first

### Issue: "Customer not found" error  
**Solution**: Import Customers_Import.IIF before Deposits_Import.IIF

### Issue: Duplicate customers
**Solution**: In Customer Center, right-click duplicate → Merge Customers

### Issue: Wrong account types
**Solution**: Edit account in Chart of Accounts → change Account Type

### Issue: Transactions don't balance
**Solution**: 
- Verify Fulton Bank starting balance is $39,023.18
- Check that all deposits are positive, payments are negative
- Review transaction detail for any errors

---

## What's NOT Included

### Other Bank Accounts
- Live Oak Bank transactions (not exported from Manager)
- Morgan Stanley transactions (not exported from Manager)
- **Action**: Export these separately from Manager if needed

### Invoices
- The deposits represent payments received, not the original invoices
- **Action**: If you need invoice history, export from Manager

### Bills
- The payments represent checks written, not vendor bills
- **Action**: If you need bill history, export from Manager

### Other Transactions
- Journal entries
- Transfers between accounts
- Credit card transactions
- **Action**: Export from Manager if needed

---

## Next Steps After Import

1. **Verify all imports were successful**
   - Check Chart of Accounts
   - Check Customer list
   - Check Item list
   - Check Fulton Bank register

2. **Reconcile Fulton Bank**
   - Get latest bank statement
   - Reconcile in QuickBooks
   - Verify ending balance matches

3. **Continue with current transactions**
   - You're now caught up through the Manager period
   - Continue entering new transactions in QuickBooks
   - No need to use Manager anymore

4. **Export other accounts if needed**
   - If you need Live Oak Bank or Morgan Stanley transactions
   - Export from Manager and let me know
   - We can create additional import files

---

## Files Created

All files are in: `C:\Scripts\Manager2QB\`

### Scripts
- `manager_explorer.py` - Database explorer
- `manager_protobuf_decoder.py` - Binary data decoder
- `manager_to_quickbooks_converter.py` - IIF converter for master data
- `transaction_converter.py` - IIF converter for transactions
- `analyze_transactions.py` - Transaction file analyzer

### Import Files (Ready to Use)
- `quickbooks_import/ChartOfAccounts_Import.IIF`
- `quickbooks_import/Customers_Import.IIF`
- `quickbooks_import/Vendors_Import.IIF`
- `quickbooks_import/Items_Import.IIF`
- `quickbooks_import/Deposits_Import.IIF`
- `quickbooks_import/Payments_Import.IIF`

### Documentation
- `CONVERSION_SUMMARY.md` - Technical summary
- `ANALYSIS_AND_PLAN.md` - Technical analysis
- `MANAGER_EXPORT_INSTRUCTIONS.md` - Manual export guide
- `FINAL_IMPORT_GUIDE.md` - This file

---

## Support

If you encounter any issues during import:

1. **Check import order** - Must import in the sequence listed above
2. **Review error messages** - QuickBooks will show specific errors
3. **Check file format** - Files should be tab-delimited IIF format
4. **Verify QuickBooks version** - Tested with QB Pro 2012
5. **Contact me** with specific error messages if needed

---

## Success Checklist

- [ ] Fulton Bank account exists with correct starting balance
- [ ] Chart of Accounts imported (36 accounts)
- [ ] Customers imported (120 customers)
- [ ] Items imported (229 items)
- [ ] Vendors added manually (as needed)
- [ ] Deposits imported (93 transactions)
- [ ] Payments imported (45 transactions)
- [ ] Fulton Bank register shows all 138 transactions
- [ ] Fulton Bank reconciled successfully
- [ ] Ready to continue with current QuickBooks operations

---

**Congratulations!** You've successfully converted your Manager Accounting data to QuickBooks Pro 2012. You can now continue using QuickBooks for all your accounting needs.
