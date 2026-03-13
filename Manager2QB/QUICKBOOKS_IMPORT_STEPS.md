# QuickBooks 2012 Pro Import Steps

## Overview
Import transaction data from Manager Accounting (Dec 2024 - Dec 2025) into QuickBooks.

---

## Pre-Import Checklist
- [ ] Backup your QuickBooks company file before starting
- [ ] All files are in: `C:\Scripts\Manager2QB\quickbooks_import\`

---

## STEP 1: Import New Customer (Optional)
**File:** `Customers_Import.IIF`  
**Contains:** 1 new customer - "Coombs, Jeff"

**To Import:**
1. In QuickBooks: **File > Utilities > Import > IIF Files**
2. Navigate to `C:\Scripts\Manager2QB\quickbooks_import\`
3. Select `Customers_Import.IIF`
4. Click **Open**

**Skip if:** Customer "Coombs, Jeff" already exists or you'll add manually.

---

## STEP 2: Import New Items (Optional)
**File:** `Items_Import.IIF`  
**Contains:** 4 new service items
- Storage25 ($25/2 weeks)
- Storage100 ($100/month)
- Hunting Land Use
- Electric Reimburse

**To Import:**
1. **File > Utilities > Import > IIF Files**
2. Select `Items_Import.IIF`
3. Click **Open**

**Skip if:** These items already exist or you don't need them for invoicing.

---

## STEP 3: Import Deposits (Receipts)
**File:** `Deposits_Import.IIF`  
**Contains:** 92 deposit transactions (customer payments received)

**To Import:**
1. **File > Utilities > Import > IIF Files**
2. Select `Deposits_Import.IIF`
3. Click **Open**

**What it does:**
- Deposits money into **Fulton Bank**
- Credits **Accounts Receivable** for each customer

---

## STEP 4: Import Payments (Checks/Expenses)
**File:** `Payments_Import.IIF`  
**Contains:** 44 payment transactions (expenses paid)

**To Import:**
1. **File > Utilities > Import > IIF Files**
2. Select `Payments_Import.IIF`
3. Click **Open**

**What it does:**
- Withdraws money from **Fulton Bank**
- Debits expense accounts (Insurance, Utilities, Taxes, etc.)

---

## DO NOT IMPORT

### ❌ ChartOfAccounts_Import.IIF
**Reason:** All needed accounts already exist in QuickBooks with correct names. Importing this would create duplicate accounts.

### ❌ Vendors_Import.IIF  
**Reason:** Empty template file. Add vendors manually if needed.

---

## Post-Import Steps

### 1. Verify Transaction Count
In QuickBooks, run a **Transaction Detail by Account** report for Fulton Bank:
- Filter dates: 12/01/2024 to 12/31/2025
- Should show ~136 transactions (92 deposits + 44 payments)

### 2. Review Uncategorized Expenses
Some transactions were imported to **Uncategorized Expenses** because the original Manager categories didn't map cleanly. Review and recategorize:
- Several PSEG payments in Aug-Nov 2025
- Lowes CC payments
- Southampton Township payment (Nov 2025 - likely property taxes)

### 3. Reconcile Fulton Bank
After import, reconcile the Fulton Bank account with your bank statement.

---

## Manual Tasks Required

1. **Review "Uncategorized Expenses"** - About 9 transactions need recategorization
2. **Add Vendors** - If you want vendor names on checks, add them manually in QuickBooks
3. **Verify Customer Matches** - Deposits reference customer short names (Glotman, Wollick, etc.) - verify they match your QB customer list

---

## Troubleshooting

### "Account not found" error
The transaction references an account that doesn't exist in QuickBooks. Check spelling matches exactly.

### Duplicate transactions
If you've already entered some transactions manually, you may get duplicates. Delete the manual entries or skip importing that file.

### Import order matters
Import Customers before Deposits (so customer references work).

---

## Summary

| Step | File | Action |
|------|------|--------|
| 1 | Customers_Import.IIF | Optional - 1 customer |
| 2 | Items_Import.IIF | Optional - 4 items |
| 3 | Deposits_Import.IIF | **IMPORT** - 92 receipts |
| 4 | Payments_Import.IIF | **IMPORT** - 44 payments |
| - | ChartOfAccounts_Import.IIF | SKIP - accounts exist |
| - | Vendors_Import.IIF | SKIP - empty |

**Total new transactions:** 136
