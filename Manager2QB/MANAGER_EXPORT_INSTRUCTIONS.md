# Manager Export Instructions

## How to Export Data from Manager for QuickBooks Conversion

Since Manager doesn't have a direct "Export" function, we'll use the **Copy to Clipboard** feature from various reports and tabs.

---

## Step-by-Step Export Process

### 1. Chart of Accounts

1. In Manager, go to **Settings** → **Chart of Accounts**
2. You should see a list of all your accounts
3. Select all accounts (Ctrl+A)
4. Copy to clipboard (Ctrl+C)
5. Open Excel or Notepad
6. Paste (Ctrl+V)
7. Save as: `manager_chart_of_accounts.csv` or `.xlsx`

**What we need**:
- Account Name
- Account Type (Income, Expense, Asset, Liability, Equity)
- Account Code/Number (if any)
- Current Balance

---

### 2. Customers

1. In Manager, go to **Sales** → **Customers** tab
2. You should see a list of all customers
3. Select all (Ctrl+A) and Copy (Ctrl+C)
4. Paste into Excel/Notepad
5. Save as: `manager_customers.csv` or `.xlsx`

**What we need**:
- Customer Name
- Address
- Email
- Phone
- Any other contact details

---

### 3. Suppliers/Vendors

1. In Manager, go to **Purchases** → **Suppliers** tab
2. Select all (Ctrl+A) and Copy (Ctrl+C)
3. Paste into Excel/Notepad
4. Save as: `manager_suppliers.csv` or `.xlsx`

**What we need**:
- Supplier/Vendor Name
- Address
- Contact details

---

### 4. Items (Products/Services)

1. In Manager, go to **Settings** → **Invoice Items** (or **Inventory Items**)
2. Select all items and copy
3. Paste into Excel/Notepad
4. Save as: `manager_items.csv` or `.xlsx`

**What we need**:
- Item Name
- Description
- Price
- Income Account
- Item Type (Service, Inventory, etc.)

---

### 5. Bank Accounts

1. In Manager, go to **Bank Accounts** tab
2. List all bank accounts with their current balances
3. Copy and save as: `manager_bank_accounts.csv`

**What we need**:
- Bank Account Name
- Current Balance
- Account Type

---

### 6. Transactions (Most Important!)

#### Option A: General Ledger Report
1. Go to **Reports** → **General Ledger**
2. Set date range to cover all your Manager data period
3. Select all accounts or run for all
4. Copy the report
5. Save as: `manager_general_ledger.csv` or `.xlsx`

#### Option B: Transaction List
1. If Manager has a transaction list or journal entries view
2. Export all transactions with:
   - Date
   - Account(s)
   - Debit/Credit amounts
   - Description/Memo
   - Reference number

#### Option C: Account-by-Account
If the above don't work, for each major account:
1. Click on the account
2. View transactions
3. Copy transaction list
4. Save with account name

---

### 7. Trial Balance (For Opening Balances)

1. Go to **Reports** → **Trial Balance**
2. Set date to the **earliest date** you have data in Manager
3. Copy the report
4. Save as: `manager_trial_balance_opening.csv`

This will give us the opening balances for all accounts.

---

### 8. Summary Balance Sheet & P&L

1. **Balance Sheet**: Reports → Balance Sheet (as of latest date)
2. **Profit & Loss**: Reports → Profit and Loss Statement (for entire period)
3. Copy both and save

These help us verify our conversion is correct.

---

## Alternative: Screen Captures

If copy/paste doesn't work well:
1. Take screenshots of each report/list
2. Save them clearly labeled
3. I can help transcribe or we can manually enter key data

---

## What to Do Next

Once you have these files exported:
1. Save them all in: `C:\Scripts\Manager2QB\manager_manual_exports\`
2. Let me know which files you were able to export
3. I'll create conversion scripts to transform them into QuickBooks IIF format

---

## Priority Order

If you can only export some data, prioritize in this order:
1. **Chart of Accounts** - Essential
2. **Trial Balance** (opening balances) - Essential
3. **General Ledger / Transactions** - Most important for history
4. **Customers** - Important for invoices
5. **Suppliers** - Important for bills
6. **Items** - Important if you use them on invoices
7. **Bank Accounts** - Can be recreated in QB

---

## Notes

- Manager may allow you to select and copy data from most screens
- Excel is better than Notepad for preserving column structure
- Keep the original Manager file as backup
- Date format in Manager: Note what format you see (MM/DD/YYYY, etc.)
