"""
Manager Accounting -> QuickBooks IIF Converter (Unified)

Reads the Manager bank transaction export (TSV) and produces clean QuickBooks
IIF import files for customer receipts and expense payments.

All known data-quality fixes are baked in so no post-processing scripts are
needed.

Usage:
    python manager_to_qb.py
"""

import re
import sys
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_FILE = Path(r"C:\Scripts\Manager2QB\FultonBankTransactions.tsv")
OUTPUT_DIR = Path(r"C:\Scripts\Manager2QB\quickbooks_import")
WARNINGS_FILE = Path(r"C:\Scripts\Manager2QB\Warnings.md")

BANK_ACCOUNT = "Fulton Bank"

# Manager em-dash character in latin-1
EM_DASH = "\x97"

# Manager account name  ->  QuickBooks account name
EXPENSE_ACCOUNT_MAP: dict[str, str] = {
    "Donations":                    "Charitable Contributions",
    "Insurance":                    "Insurance Expense",
    "Electricity":                  "Utilities:Electric-Main",
    "Real Estate Taxes":            "Taxes - Property",
    "Business Tax, NJ":             "Business Licenses and Permits",
    "Accounting fees":              "Professional Fees",
    "Fuel for tractors":            "Gasoline, Fuel and Oil",
    "Motor vehicle expenses":       "Tractor and Vehicle expenses",
    "Repairs and maintenance":      "Repairs and Maintenance",
    "Building Rental - Farm Labor": "Repairs and Maintenance",
    "Rodent control":               "Rodent Control",
    "Dumpsters/disposal":           "Miscellaneous Expense",
    "CitiCard (house CC)":          "Miscellaneous Expense",
    "Dues and Subscriptions":       "Dues and Subscriptions",
    "Motor vehicle expenses, Dumpsters/disposal":
                                    "Tractor and Vehicle expenses",
}

# Receipts whose Account field is NOT "Accounts receivable …" get mapped here
INCOME_ACCOUNT_MAP: dict[str, str] = {
    "Income from Morgan Stanley Investments": "Morgan Stanley",
    "Scrap Yard Income":                      "Uncategorized Income:Scrap Yard Proceeds",
}

# Suspense-account payments that can be recategorized by inspecting the memo
SUSPENSE_RECATEGORIZE: list[tuple[str, str]] = [
    ("PSEG",                "Utilities:Electric-Main"),
    ("Twp of Southampton",  "Taxes - Property"),
    ("Southampton",         "Taxes - Property"),
    ("Lowes",               "Repairs and Maintenance"),
]

# Accounts Payable entries — map the vendor portion to a QB expense account
AP_RECODE: dict[str, str] = {
    "Republic Bank":                        "Miscellaneous Expense",
    "Elan Financial Services (Fulton CC)":  "Miscellaneous Expense",
}

# Multi-account payment: when Manager lists several accounts separated by
# commas we need to know how to split the dollar amount.  Since the source
# data does not provide per-account amounts, we assign the full amount to
# the *first* recognised expense account.  This dict lets us override that
# for known combos where a better primary account exists.
MULTI_ACCOUNT_PRIMARY: dict[str, str] = {
    # key = frozenset of Manager account names joined with ", "
    "Repairs and maintenance, Fuel for tractors, Motor vehicle expenses":
        "Repairs and Maintenance",
    "Rodent control, Repairs and maintenance, Dues and Subscriptions":
        "Rodent Control",
    "Motor vehicle expenses, Dumpsters/disposal":
        "Tractor and Vehicle expenses",
    "Accounts payable " + EM_DASH + " Elan Financial Services (Fulton CC), Suspense":
        "Miscellaneous Expense",
}

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class InvoiceRef:
    """A reference to a specific Manager invoice within a receipt."""
    customer: str           # short-name
    invoice_num: str        # Manager invoice number
    invoice_date: str       # MM/DD/YYYY or empty

@dataclass
class ReceiptTxn:
    """A customer payment receipt deposited into the bank."""
    date: str               # MM/DD/YYYY
    amount: float
    customer: str           # QB customer short-name
    memo: str
    account: str            # "Accounts Receivable" or an income account
    docnum: str = ""
    invoice_refs: list[InvoiceRef] = None

    def __post_init__(self):
        if self.invoice_refs is None:
            self.invoice_refs = []

@dataclass
class PaymentTxn:
    """An expense payment (check / EFT) from the bank."""
    date: str
    amount: float           # positive
    expense_account: str    # QB expense account
    memo: str
    docnum: str = ""

@dataclass
class Warning:
    line_num: int
    raw_line: str
    message: str

# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

def clean_amount(amount_str: str) -> float:
    """Parse a Manager amount string like '$ 5,491.00' or '- $ 75.00'."""
    if not amount_str or not amount_str.strip():
        return 0.0
    s = amount_str.replace("$", "").replace(",", "").replace(" ", "").strip()
    if not s:
        return 0.0
    return float(s)


def parse_date(date_str: str) -> str:
    """Return MM/DD/YYYY or empty string."""
    if not date_str or not date_str.strip():
        return ""
    try:
        dt = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return dt.strftime("%m/%d/%Y")
    except ValueError:
        return date_str.strip()


def extract_customer_from_ar(account_field: str) -> str:
    """
    Extract the QB customer short-name from a Manager AR account string.

    Examples:
        "Accounts receivable — Glotman - Geoff Glotman — 1877 — 03/01/2025"
            -> "Glotman"
        "Accounts receivable — Phil-CA - Phil-CA — 1858 — 01/01/2025"
            -> "Phil-CA"
        "Accounts receivable — Kevin Dolan"
            -> "Kevin Dolan"
        "Accounts receivable — Coombs, Jeff - Coombs, Jeff"
            -> "Coombs, Jeff"
    """
    # Strip the "Accounts receivable — " prefix
    ar_prefix = "Accounts receivable" + " " + EM_DASH + " "
    if ar_prefix not in account_field:
        return ""

    remainder = account_field.split(ar_prefix, 1)[1]

    # The first segment (before any " — <digits>") is "ShortName - FullName"
    # or just "ShortName" when there are no invoice refs.
    # Split on the em-dash that precedes a digit (invoice number).
    parts = re.split(r"\s*" + EM_DASH + r"\s*(?=\d)", remainder, maxsplit=1)
    name_part = parts[0].strip()

    # If there are multiple AR entries separated by ", Accounts receivable …"
    # just use the first one.
    if ", Accounts receivable" in name_part:
        name_part = name_part.split(", Accounts receivable")[0].strip()
    if ", Customer Prepayments" in name_part:
        name_part = name_part.split(", Customer Prepayments")[0].strip()

    # "ShortName - FullName" -> take ShortName
    if " - " in name_part:
        short = name_part.split(" - ", 1)[0].strip()
        return short

    # No dash — the whole thing is the name (e.g. "Kevin Dolan")
    return name_part.strip()


def extract_invoice_refs(account_field: str) -> list[InvoiceRef]:
    """
    Parse all invoice references from a Manager AR account string.

    The Account field may contain one or more comma-separated AR entries:
        "Accounts receivable — Glotman - Geoff Glotman — 1877 — 03/01/2025,
         Accounts receivable — Glotman - Geoff Glotman — 1868 — 02/01/2025"

    Returns a list of InvoiceRef with customer short-name, invoice number,
    and invoice date for each entry.
    """
    refs: list[InvoiceRef] = []

    # Split on ", " followed by "Accounts receivable" or "Customer Prepayments"
    ar_entries = re.split(
        r",\s*(?=Accounts receivable|Customer Prepayments)", account_field)

    for entry in ar_entries:
        entry = entry.strip()
        if entry.startswith("Customer Prepayments"):
            refs.append(InvoiceRef(customer="", invoice_num="PREPAY", invoice_date=""))
            continue
        if "Accounts receivable" not in entry:
            continue

        # Split on em-dash: [0]="Accounts receivable", [1]="Short - Full",
        #                    [2]=invoice_num, [3]=invoice_date
        em_parts = [p.strip() for p in entry.split(EM_DASH) if p.strip()]
        customer = ""
        inv_num = ""
        inv_date = ""

        if len(em_parts) > 1:
            name_part = em_parts[1]
            customer = name_part.split(" - ", 1)[0].strip()
        if len(em_parts) > 2:
            inv_num = em_parts[2].strip()
        if len(em_parts) > 3:
            inv_date = em_parts[3].strip()

        if customer or inv_num:
            refs.append(InvoiceRef(customer=customer, invoice_num=inv_num,
                                   invoice_date=inv_date))

    return refs


def map_expense_account(manager_account: str, memo: str) -> str:
    """Map a Manager expense account name to a QuickBooks account name."""
    acct = manager_account.strip()

    # Suspense recategorization based on memo (check before direct lookup
    # so that memo-based keywords can override the generic fallback)
    if acct == "Suspense":
        for keyword, qb_acct in SUSPENSE_RECATEGORIZE:
            if keyword.lower() in memo.lower():
                return qb_acct
        return "Uncategorized Expenses"

    # Direct lookup (handles single accounts AND known multi-account
    # combos like "Business Tax, NJ" or "Motor vehicle expenses, Dumpsters/disposal")
    if acct in EXPENSE_ACCOUNT_MAP:
        return EXPENSE_ACCOUNT_MAP[acct]

    # Check multi-account override
    if acct in MULTI_ACCOUNT_PRIMARY:
        return MULTI_ACCOUNT_PRIMARY[acct]

    # Check if it's an AP entry: "Accounts payable — VendorName"
    if acct.startswith("Accounts payable"):
        for vendor_key, qb_acct in AP_RECODE.items():
            if vendor_key in acct:
                return qb_acct
        # Fallback for unknown AP
        return "Miscellaneous Expense"

    # Multi-account: "acct1, acct2, acct3"
    if ", " in acct:
        sub_accounts = [s.strip() for s in acct.split(",")]
        for sub in sub_accounts:
            mapped = EXPENSE_ACCOUNT_MAP.get(sub)
            if mapped:
                return mapped
        # Fallback
        return "Uncategorized Expenses"

    # Fallback
    return "Uncategorized Expenses"


def clean_memo(description: str) -> str:
    """Clean the memo/description field for IIF output."""
    if not description:
        return ""
    # Replace em-dash with regular dash
    s = description.replace(EM_DASH, "-")
    # Remove non-printable characters
    s = "".join(c for c in s if c.isprintable() or c in "\t")
    return s.strip()


def extract_docnum(transaction_field: str) -> str:
    """Extract document/check number from the Transaction field."""
    if not transaction_field:
        return ""
    # "Receipt — 4358" or "Payment — 187" or "Payment — bp"
    match = re.search(EM_DASH + r"\s*(.+)$", transaction_field)
    if match:
        val = match.group(1).strip()
        # Only return if it looks like a useful reference
        if val and val.lower() not in ("", "bp", "eft"):
            return val
    return ""


# ---------------------------------------------------------------------------
# Main conversion
# ---------------------------------------------------------------------------

def convert(input_file: Path, output_dir: Path) -> list[Warning]:
    """Read the Manager TSV and produce IIF files.  Returns warnings."""
    output_dir.mkdir(exist_ok=True)
    warnings: list[Warning] = []

    # Read source file
    with open(input_file, "r", encoding="latin-1") as f:
        raw_lines = f.readlines()

    if len(raw_lines) < 2:
        warnings.append(Warning(0, "", "Input file is empty or has no data rows"))
        return warnings

    # Parse header
    header = raw_lines[0].strip().split("\t")
    # Expected: ['', '', 'Date', 'Transaction', 'Account', 'Description', 'Amount']
    # The first two columns are "Edit" and "View" links from the Manager UI.

    receipts: list[ReceiptTxn] = []
    payments: list[PaymentTxn] = []
    skipped_transfers: list[str] = []

    for line_num, raw_line in enumerate(raw_lines[1:], start=2):
        cols = raw_line.strip().split("\t")
        if len(cols) < 7:
            continue

        # Columns: Edit, View, Date, Transaction, Account, Description, Amount
        date_str = cols[2].strip()
        txn_type = cols[3].strip()
        account_field = cols[4].strip()
        description = cols[5].strip()
        amount_str = cols[6].strip() if len(cols) > 6 else ""

        date = parse_date(date_str)
        amount = clean_amount(amount_str)
        memo = clean_memo(description)

        # Skip zero-amount rows and the starting balance row
        if "Starting balance" in txn_type:
            continue
        if amount == 0.0:
            warnings.append(Warning(line_num, raw_line.strip(),
                                    "Skipped zero-amount transaction"))
            continue

        # --- Inter Account Transfer ---
        if "Inter Account Transfer" in txn_type:
            skipped_transfers.append(
                f"Line {line_num}: {date} | {memo} | ${abs(amount):,.2f}")
            continue

        # --- Receipts ---
        if "Receipt" in txn_type:
            docnum = extract_docnum(txn_type)

            if "Accounts receivable" in account_field:
                customer = extract_customer_from_ar(account_field)
                if not customer:
                    warnings.append(Warning(
                        line_num, raw_line.strip(),
                        f"Could not extract customer from AR: {account_field[:80]}"))
                    customer = "UNKNOWN"

                # Extract invoice references for payment application tracking
                inv_refs = extract_invoice_refs(account_field)

                # Use invoice number(s) as DOCNUM so they're visible in QB
                inv_nums = [r.invoice_num for r in inv_refs
                            if r.invoice_num and r.invoice_num != "PREPAY"]
                if inv_nums:
                    docnum = "/".join(inv_nums)

                receipts.append(ReceiptTxn(
                    date=date, amount=amount, customer=customer,
                    memo=memo, account="Accounts Receivable", docnum=docnum,
                    invoice_refs=inv_refs))
            else:
                # Non-AR receipt (Morgan Stanley, Scrap Yard, etc.)
                income_acct = INCOME_ACCOUNT_MAP.get(account_field)
                if not income_acct:
                    warnings.append(Warning(
                        line_num, raw_line.strip(),
                        f"Unknown receipt account: {account_field}"))
                    income_acct = "Uncategorized Income"
                receipts.append(ReceiptTxn(
                    date=date, amount=amount, customer="",
                    memo=memo, account=income_acct, docnum=docnum))
            continue

        # --- Payments ---
        if "Payment" in txn_type:
            docnum = extract_docnum(txn_type)
            expense_acct = map_expense_account(account_field, description)
            payments.append(PaymentTxn(
                date=date, amount=abs(amount),
                expense_account=expense_acct, memo=memo, docnum=docnum))
            continue

        # Unknown transaction type
        warnings.append(Warning(line_num, raw_line.strip(),
                                f"Unknown transaction type: {txn_type}"))

    # --- Write IIF files ---
    write_receipts_iif(output_dir / "Deposits_Import.IIF", receipts)
    write_payments_iif(output_dir / "Payments_Import.IIF", payments)

    # --- Payment application reference report ---
    write_payment_applications(output_dir / "Payment_Applications.md", receipts)

    # --- Skipped transfers ---
    if skipped_transfers:
        for t in skipped_transfers:
            warnings.append(Warning(0, t,
                                    "Inter-account transfer skipped (no QB equivalent)"))

    # --- Summary ---
    print(f"\n{'='*60}")
    print(f"Conversion Summary")
    print(f"{'='*60}")
    print(f"  Input file:       {input_file.name}")
    print(f"  Customer receipts: {len(receipts)}")
    print(f"  Expense payments:  {len(payments)}")
    print(f"  Warnings:          {len(warnings)}")
    print(f"  Output directory:  {output_dir}")
    print(f"{'='*60}")

    return warnings


# ---------------------------------------------------------------------------
# IIF writers
# ---------------------------------------------------------------------------

IIF_HEADER = (
    "!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n"
)
TRNS_HEADER = (
    "!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM"
    "\tMEMO\tCLEAR\tTOPRINT\tADDR1\tADDR2\tADDR3\tADDR4\tADDR5\n"
)
SPL_HEADER = (
    "!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM"
    "\tMEMO\tCLEAR\tQNTY\tPRICE\tINVITEM\tTAXABLE\n"
)
ENDTRNS_HEADER = "!ENDTRNS\n"


def iif_hdr_line() -> str:
    now = datetime.now()
    ts = int(now.timestamp())
    return (f"HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1"
            f"\t{now.strftime('%Y-%m-%d')}\t{ts}\tN\t0\n")


def write_receipts_iif(filepath: Path, receipts: list[ReceiptTxn]) -> None:
    """Write receipts as PAYMENT transactions to Undeposited Funds.

    All receipts land in Undeposited Funds so the user can group them
    into bank deposits via Banking > Record Deposits in QuickBooks.
    """
    trns_id = 1

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        f.write(IIF_HEADER)
        f.write(iif_hdr_line())
        f.write(TRNS_HEADER)
        f.write(SPL_HEADER)
        f.write(ENDTRNS_HEADER)

        for r in receipts:
            trns_id += 1

            # TRNS line: debit Undeposited Funds (positive amount)
            f.write(
                f"TRNS\t{trns_id}\tPAYMENT\t{r.date}\tUndeposited Funds"
                f"\t{r.customer}\t\t{r.amount:.2f}\t{r.docnum}"
                f"\t{r.memo}\tN\tN\t\t\t\t\t\n"
            )
            # SPL line: credit source account (negative amount)
            f.write(
                f"SPL\t{trns_id}\tPAYMENT\t{r.date}\t{r.account}"
                f"\t{r.customer}\t\t{-r.amount:.2f}\t{r.docnum}"
                f"\t{r.memo}\tN\t\t\t\tN\n"
            )
            f.write("ENDTRNS\n")

        f.write("\n")

    print(f"[OK] Created: {filepath.name}  ({len(receipts)} transactions)")


def write_payments_iif(filepath: Path, payments: list[PaymentTxn]) -> None:
    """Write expense payments as CHECK transactions."""
    trns_id = 100  # Start at 100 to avoid ID collisions with receipts

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        f.write(IIF_HEADER)
        f.write(iif_hdr_line())
        f.write(TRNS_HEADER)
        f.write(SPL_HEADER)
        f.write(ENDTRNS_HEADER)

        for p in payments:
            trns_id += 1

            # TRNS line: credit bank account (negative amount)
            f.write(
                f"TRNS\t{trns_id}\tCHECK\t{p.date}\t{BANK_ACCOUNT}"
                f"\t\t\t{-p.amount:.2f}\t{p.docnum}"
                f"\t{p.memo}\tN\tN\t\t\t\t\t\n"
            )
            # SPL line: debit expense account (positive amount)
            f.write(
                f"SPL\t{trns_id}\tCHECK\t{p.date}\t{p.expense_account}"
                f"\t\t\t{p.amount:.2f}\t{p.docnum}"
                f"\t{p.memo}\tN\t\t\t\tN\n"
            )
            f.write("ENDTRNS\n")

        f.write("\n")

    print(f"[OK] Created: {filepath.name}  ({len(payments)} transactions)")


# ---------------------------------------------------------------------------
# Payment application reference report
# ---------------------------------------------------------------------------

def write_payment_applications(filepath: Path, receipts: list[ReceiptTxn]) -> None:
    """Generate a reference report showing which invoices each payment covers.

    QuickBooks IIF cannot specify payment-to-invoice application, so this
    report serves as a manual reference.  QB will auto-apply payments to the
    oldest open invoices; use this report to verify or correct applications.
    """
    # Only include AR receipts that have invoice references
    ar_receipts = [r for r in receipts if r.invoice_refs]

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Payment-to-Invoice Applications\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("QuickBooks IIF does not support specifying which invoice(s) a payment\n")
        f.write("applies to. QB will auto-apply to the oldest open invoice(s). Use this\n")
        f.write("report to verify or manually correct the applications.\n\n")
        f.write(f"**{len(ar_receipts)} customer receipt(s) with invoice references:**\n\n")
        f.write("---\n\n")

        for r in ar_receipts:
            inv_count = len(r.invoice_refs)
            tag = "" if inv_count == 1 else f" ({inv_count} invoices)"
            f.write(f"### {r.date} — {r.customer} — ${r.amount:,.2f}{tag}\n\n")
            f.write(f"- **Memo:** {r.memo}\n")
            f.write(f"- **DOCNUM (in IIF):** {r.docnum}\n")
            f.write(f"- **Applied to:**\n")
            for ref in r.invoice_refs:
                if ref.invoice_num == "PREPAY":
                    f.write(f"  - Customer Prepayment\n")
                elif ref.invoice_num:
                    date_str = f" dated {ref.invoice_date}" if ref.invoice_date else ""
                    f.write(f"  - Invoice #{ref.invoice_num}{date_str}\n")
                else:
                    f.write(f"  - (no invoice number — unapplied payment)\n")
            f.write("\n")

        # Summary table: count of single vs multi-invoice payments
        single = sum(1 for r in ar_receipts if len(r.invoice_refs) == 1)
        multi = sum(1 for r in ar_receipts if len(r.invoice_refs) > 1)
        no_inv = sum(1 for r in receipts
                     if r.account == "Accounts Receivable" and not r.invoice_refs)
        f.write("---\n\n")
        f.write("## Summary\n\n")
        f.write(f"| Category | Count |\n")
        f.write(f"|---|---|\n")
        f.write(f"| Single-invoice payments | {single} |\n")
        f.write(f"| Multi-invoice payments (review carefully) | {multi} |\n")
        f.write(f"| Payments without invoice refs | {no_inv} |\n")
        f.write(f"| Non-customer income (Morgan Stanley, etc.) | "
                f"{sum(1 for r in receipts if r.account != 'Accounts Receivable')} |\n")
        f.write(f"| **Total receipts** | **{len(receipts)}** |\n\n")
        f.write("**Note:** Multi-invoice payments need manual verification in QB's\n")
        f.write("\"Receive Payments\" window to ensure amounts are applied correctly.\n")

    print(f"[OK] Created: {filepath.name}  ({len(ar_receipts)} payment applications)")


# ---------------------------------------------------------------------------
# Warnings file
# ---------------------------------------------------------------------------

def write_warnings(filepath: Path, warnings: list[Warning]) -> None:
    """Write a Warnings.md file with all issues encountered."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# Conversion Warnings\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        if not warnings:
            f.write("No warnings. All transactions converted successfully.\n")
            return

        f.write(f"**{len(warnings)} warning(s) found:**\n\n")

        for w in warnings:
            f.write(f"- **{w.message}**\n")
            if w.raw_line:
                # Truncate very long lines
                display = w.raw_line[:150]
                if len(w.raw_line) > 150:
                    display += "..."
                f.write(f"  - `{display}`\n")
            f.write("\n")

    print(f"[OK] Created: {filepath.name}  ({len(warnings)} warnings)")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_output(output_dir: Path) -> list[str]:
    """Post-generation validation of IIF files."""
    issues: list[str] = []

    for iif_file in output_dir.glob("*_Import.IIF"):
        with open(iif_file, "r", encoding="utf-8") as f:
            lines = f.readlines()

        in_transaction = False
        for i, line in enumerate(lines, start=1):
            stripped = line.rstrip("\n\r")

            if stripped.startswith("TRNS\t"):
                in_transaction = True
                parts = stripped.split("\t")

                # Check: AR transactions must have a customer name
                if len(parts) > 4:
                    # SPL line check is more important, but TRNS should match
                    pass

            elif stripped.startswith("SPL\t"):
                parts = stripped.split("\t")
                if len(parts) > 5:
                    acct = parts[4]
                    name = parts[5]
                    if acct == "Accounts Receivable" and not name.strip():
                        issues.append(
                            f"{iif_file.name} line {i}: "
                            f"Accounts Receivable without customer name")
                    if acct == "Accounts Payable" and not name.strip():
                        issues.append(
                            f"{iif_file.name} line {i}: "
                            f"Accounts Payable without vendor name")

            elif stripped.startswith("ENDTRNS"):
                in_transaction = False

            # Check for em-dash or other non-ASCII that QB can't handle
            if EM_DASH in stripped:
                issues.append(
                    f"{iif_file.name} line {i}: "
                    f"Contains em-dash character (0x97)")

    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print(f"\n{'='*60}")
    print("Manager -> QuickBooks IIF Converter")
    print(f"{'='*60}")
    print(f"Input:  {INPUT_FILE}")
    print(f"Output: {OUTPUT_DIR}")

    if not INPUT_FILE.exists():
        print(f"\n[ERROR] Input file not found: {INPUT_FILE}")
        sys.exit(1)

    # Convert
    warnings = convert(INPUT_FILE, OUTPUT_DIR)

    # Validate
    print("\nValidating output files...")
    issues = validate_output(OUTPUT_DIR)
    if issues:
        print(f"\n[WARN] {len(issues)} validation issue(s):")
        for issue in issues:
            print(f"  - {issue}")
            warnings.append(Warning(0, "", issue))
    else:
        print("[OK] Validation passed — no issues found")

    # Write warnings
    write_warnings(WARNINGS_FILE, warnings)

    # Import instructions
    print(f"\n{'='*60}")
    print("Import into QuickBooks:")
    print(f"{'='*60}")
    print("1. File > Utilities > Import > IIF Files")
    print(f"2. Import: Deposits_Import.IIF  (customer receipts -> Undeposited Funds)")
    print(f"3. Import: Payments_Import.IIF  (expense payments)")
    print(f"4. Banking > Record Deposits -> select payments -> deposit to {BANK_ACCOUNT}")
    print(f"\nNote: Ensure all customers exist in QB before importing receipts.")
    print(f"Review Payment_Applications.md to verify invoice applications.")
    print(f"Check Warnings.md for any issues that need manual attention.")


if __name__ == "__main__":
    main()
