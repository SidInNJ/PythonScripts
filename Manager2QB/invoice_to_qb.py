"""
Invoice-to-QuickBooks IIF Converter with GUI
=============================================
Reads the Manager Accounting sales-invoice TSV export, presents a GUI
for selecting which invoices to import, and generates a QuickBooks-
importable IIF file with INVOICE transaction type.

Usage:
    python invoice_to_qb.py

Mapping file:  invoice_item_map.json  (edit to adjust item/account mappings)
Input file:    SalesInvooices          (Manager TSV export)
Output:        quickbooks_import/Invoices_Import.IIF
"""

from __future__ import annotations

import csv
import json
import re
import sys
import tkinter as tk
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
INVOICE_TSV = BASE_DIR / "SalesInvooices"
MAP_FILE = BASE_DIR / "invoice_item_map.json"
OUTPUT_DIR = BASE_DIR / "quickbooks_import"
OUTPUT_IIF = OUTPUT_DIR / "Invoices_Import.IIF"

# ---------------------------------------------------------------------------
# IIF constants
# ---------------------------------------------------------------------------
IIF_HDR = (
    "!HDR\tPROD\tVER\tREL\tIIFVER\tDATE\tTIME\tACCNTNT\tACCNTNTSPLITTIME\n"
    "HDR\tQuickBooks Pro\tVersion 22.0D\tRelease R16P\t1\t"
    f"{datetime.now():%Y-%m-%d}\t{int(datetime.now().timestamp())}\tN\t0\n"
)
TRNS_HDR = "!TRNS\tTRNSID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM\tMEMO\tCLEAR\tTOPRINT\tADDR1\tADDR2\tADDR3\tADDR4\tADDR5\n"
SPL_HDR = "!SPL\tSPLID\tTRNSTYPE\tDATE\tACCNT\tNAME\tCLASS\tAMOUNT\tDOCNUM\tMEMO\tCLEAR\tQNTY\tPRICE\tINVITEM\tTAXABLE\n"
ENDTRNS_HDR = "!ENDTRNS\n"

# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class InvoiceLine:
    """One line item on an invoice."""
    description: str
    qty: float
    unit_price: float
    amount: float          # qty * unit_price (or explicit CurrencyAmount)
    manager_acct_guid: str
    qb_account: str = ""   # resolved from mapping
    qb_item: str = ""      # resolved from mapping


@dataclass
class Invoice:
    """A parsed Manager sales invoice."""
    issue_date: str        # MM/DD/YYYY as in the TSV
    due_date: str
    reference: str         # invoice number
    customer: str
    description: str       # header-level description
    lines: list[InvoiceLine] = field(default_factory=list)

    @property
    def total(self) -> float:
        return sum(ln.amount for ln in self.lines)

    @property
    def line_count(self) -> int:
        return len(self.lines)


# ---------------------------------------------------------------------------
# Mapping helpers
# ---------------------------------------------------------------------------

def load_mappings() -> dict:
    """Load the JSON mapping file."""
    with open(MAP_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_qb_item(desc: str, price: float, mappings: dict) -> str:
    """Determine the QB item name from description and price."""
    desc_map: dict = mappings.get("description_to_qb_item", {})
    price_map: dict = mappings.get("price_to_storage_item", {})

    # Exact match on description
    if desc in desc_map:
        item = desc_map[desc]
        # For generic "Storage" items, refine by price
        if item == "Storage" and str(int(price)) in price_map:
            return price_map[str(int(price))]
        return item

    # Partial / prefix match (handles varying demand-reimbursement dates)
    for pattern, item in desc_map.items():
        if desc.startswith(pattern):
            return item

    return ""


def resolve_qb_account(guid: str, mappings: dict) -> str:
    """Determine the QB income account from a Manager account GUID."""
    acct_map: dict = mappings.get("account_guid_to_qb_account", {})
    return acct_map.get(guid, "Uncategorized Income")


# ---------------------------------------------------------------------------
# TSV parser
# ---------------------------------------------------------------------------

def parse_invoices(tsv_path: Path, mappings: dict) -> list[Invoice]:
    """Parse the Manager sales-invoice TSV export into Invoice objects."""
    invoices: list[Invoice] = []

    with open(tsv_path, "r", encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader)

        # Build column index lookups
        def col(name: str) -> int | None:
            return header.index(name) if name in header else None

        ci_issue = col("IssueDate")
        ci_due = col("DueDate")
        ci_ref = col("Reference")
        ci_cust = col("Customer")
        ci_desc = col("Description")

        # Discover line-item column groups (Lines.1 .. Lines.6)
        line_groups: list[dict[str, int | None]] = []
        for n in range(1, 7):
            grp = {
                "desc": col(f"Lines.{n}.LineDescription"),
                "qty": col(f"Lines.{n}.Qty"),
                "price": col(f"Lines.{n}.SalesUnitPrice"),
                "amount": col(f"Lines.{n}.CurrencyAmount"),
                "acct": col(f"Lines.{n}.Account"),
            }
            line_groups.append(grp)

        for row in reader:
            def val(idx: int | None) -> str:
                if idx is None or idx >= len(row):
                    return ""
                return row[idx].strip()

            customer = val(ci_cust)
            # Skip the GUID customer row
            if re.match(r"^[0-9a-f]{8}-", customer):
                continue

            issue_date = val(ci_issue)
            due_date = val(ci_due)
            reference = val(ci_ref)
            description = val(ci_desc)

            lines: list[InvoiceLine] = []
            for grp in line_groups:
                desc_val = val(grp["desc"])
                qty_val = val(grp["qty"])
                price_val = val(grp["price"])
                amt_val = val(grp["amount"])
                acct_val = val(grp["acct"])

                # Skip empty line slots
                if not desc_val and not qty_val and not price_val:
                    continue

                qty = float(qty_val) if qty_val else 1.0
                price = float(price_val) if price_val else 0.0
                amount = float(amt_val) if amt_val else qty * price

                qb_account = resolve_qb_account(acct_val, mappings)
                qb_item = resolve_qb_item(desc_val, price, mappings)

                lines.append(InvoiceLine(
                    description=desc_val,
                    qty=qty,
                    unit_price=price,
                    amount=amount,
                    manager_acct_guid=acct_val,
                    qb_account=qb_account,
                    qb_item=qb_item,
                ))

            if lines:
                invoices.append(Invoice(
                    issue_date=issue_date,
                    due_date=due_date,
                    reference=reference,
                    customer=customer,
                    description=description,
                    lines=lines,
                ))

    return invoices


# ---------------------------------------------------------------------------
# IIF writer
# ---------------------------------------------------------------------------

def write_invoices_iif(filepath: Path, invoices: list[Invoice]) -> None:
    """Write selected invoices as INVOICE transactions in IIF format."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    trns_id = 0
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        f.write(IIF_HDR)
        f.write(TRNS_HDR)
        f.write(SPL_HDR)
        f.write(ENDTRNS_HDR)

        for inv in invoices:
            trns_id += 1
            total = inv.total

            # TRNS line: debit Accounts Receivable for the full amount
            docnum = f"M{inv.reference}" if inv.reference else ""
            f.write(
                f"TRNS\t{trns_id}\tINVOICE\t{inv.issue_date}"
                f"\tAccounts Receivable\t{inv.customer}\t\t{total:.2f}"
                f"\t{docnum}\t{inv.description}"
                f"\tN\tY\t\t\t\t\t\n"
            )

            # One SPL line per line item: credit the income account
            # Per Intuit sample: SPL amounts are negative, no NAME,
            # QNTY and PRICE are positive.
            for ln in inv.lines:
                memo = ln.description
                f.write(
                    f"SPL\t{trns_id}\tINVOICE\t{inv.issue_date}"
                    f"\t{ln.qb_account}\t\t\t{-ln.amount:.2f}"
                    f"\t\t{memo}"
                    f"\tN\t{ln.qty:.4g}\t{round(ln.unit_price, 5):.5f}"
                    f"\t{ln.qb_item}\tN\n"
                )

            f.write("ENDTRNS\n")

        f.write("\n")

    print(f"[OK] Created: {filepath.name}  ({len(invoices)} invoices)")


# ---------------------------------------------------------------------------
# GUI
# ---------------------------------------------------------------------------

class InvoiceSelectorApp:
    """Tkinter GUI for selecting invoices to export."""

    def __init__(self, root: tk.Tk, invoices: list[Invoice]):
        self.root = root
        self.all_invoices = invoices
        self.selected: set[int] = set()  # indices into all_invoices
        self.sort_col = "date"
        self.sort_reverse = True  # newest first by default

        self.root.title("Manager → QuickBooks Invoice Exporter")
        self.root.geometry("1100x650")
        self.root.minsize(900, 400)

        self._build_ui()
        self._populate_tree()

    # ---- UI construction ----

    def _build_ui(self):
        # Top frame: filter + buttons
        top = ttk.Frame(self.root, padding=8)
        top.pack(fill=tk.X)

        ttk.Label(top, text="Filter by customer:").pack(side=tk.LEFT)
        self.cust_var = tk.StringVar(value="(All)")
        customers = sorted(set(inv.customer for inv in self.all_invoices))
        self.cust_combo = ttk.Combobox(
            top, textvariable=self.cust_var,
            values=["(All)"] + customers, state="readonly", width=20)
        self.cust_combo.pack(side=tk.LEFT, padx=(4, 16))
        self.cust_combo.bind("<<ComboboxSelected>>", lambda e: self._populate_tree())

        ttk.Button(top, text="Select All Visible",
                   command=self._select_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="Deselect All",
                   command=self._deselect_all).pack(side=tk.LEFT, padx=2)

        # Status label (right side)
        self.status_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.status_var).pack(side=tk.RIGHT)

        # Treeview
        cols = ("sel", "date", "ref", "customer", "lines", "total",
                "due", "items", "description")
        col_widths = {
            "sel": 30, "date": 90, "ref": 60, "customer": 100,
            "lines": 45, "total": 85, "due": 90, "items": 180,
            "description": 250,
        }
        col_headings = {
            "sel": "\u2611", "date": "Date", "ref": "Inv #",
            "customer": "Customer", "lines": "Ln", "total": "Total",
            "due": "Due Date", "items": "QB Items",
            "description": "Description",
        }
        col_anchors = {
            "sel": tk.CENTER, "date": tk.CENTER, "ref": tk.CENTER,
            "customer": tk.W, "lines": tk.CENTER, "total": tk.E,
            "due": tk.CENTER, "items": tk.W, "description": tk.W,
        }

        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 4))

        self.tree = ttk.Treeview(
            tree_frame, columns=cols, show="headings", selectmode="extended")

        for c in cols:
            self.tree.heading(c, text=col_headings[c],
                              command=lambda _c=c: self._sort_by(_c))
            self.tree.column(c, width=col_widths.get(c, 100),
                             anchor=col_anchors.get(c, tk.W),
                             stretch=(c == "description"))

        vsb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL,
                             command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<ButtonRelease-1>", self._on_click)

        # Bottom frame: export button
        bot = ttk.Frame(self.root, padding=8)
        bot.pack(fill=tk.X)

        ttk.Button(bot, text="Export Selected to IIF",
                   command=self._export).pack(side=tk.RIGHT, padx=4)
        self.export_status = tk.StringVar(value="")
        ttk.Label(bot, textvariable=self.export_status).pack(side=tk.RIGHT)

    # ---- Data display ----

    def _visible_invoices(self) -> list[tuple[int, Invoice]]:
        """Return (original_index, invoice) for the current filter."""
        cust = self.cust_var.get()
        pairs = list(enumerate(self.all_invoices))
        if cust != "(All)":
            pairs = [(i, inv) for i, inv in pairs if inv.customer == cust]
        return pairs

    def _populate_tree(self):
        self.tree.delete(*self.tree.get_children())
        pairs = self._visible_invoices()

        # Sort
        key_map = {
            "date": lambda p: p[1].issue_date,
            "ref": lambda p: p[1].reference,
            "customer": lambda p: p[1].customer.lower(),
            "lines": lambda p: p[1].line_count,
            "total": lambda p: p[1].total,
            "due": lambda p: p[1].due_date,
            "sel": lambda p: (p[0] in self.selected),
        }
        key_fn = key_map.get(self.sort_col, key_map["date"])
        pairs.sort(key=key_fn, reverse=self.sort_reverse)

        for idx, inv in pairs:
            check = "\u2611" if idx in self.selected else "\u2610"
            items_str = ", ".join(
                dict.fromkeys(ln.qb_item for ln in inv.lines if ln.qb_item))
            ref_display = f"M{inv.reference}" if inv.reference else ""
            self.tree.insert("", tk.END, iid=str(idx), values=(
                check,
                inv.issue_date,
                ref_display,
                inv.customer,
                inv.line_count,
                f"${inv.total:,.2f}",
                inv.due_date,
                items_str,
                inv.description[:80],
            ))

        self._update_status()

    def _update_status(self):
        n = len(self.selected)
        total = sum(self.all_invoices[i].total for i in self.selected)
        self.status_var.set(f"{n} selected  |  ${total:,.2f}")

    # ---- Interaction ----

    def _on_click(self, event):
        region = self.tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col = self.tree.identify_column(event.x)
        item_id = self.tree.identify_row(event.y)
        if not item_id:
            return

        idx = int(item_id)
        # Toggle selection on any column click
        if idx in self.selected:
            self.selected.discard(idx)
        else:
            self.selected.add(idx)

        # Update just this row's checkbox
        inv = self.all_invoices[idx]
        check = "\u2611" if idx in self.selected else "\u2610"
        items_str = ", ".join(
            dict.fromkeys(ln.qb_item for ln in inv.lines if ln.qb_item))
        ref_display = f"M{inv.reference}" if inv.reference else ""
        self.tree.item(item_id, values=(
            check, inv.issue_date, ref_display, inv.customer,
            inv.line_count, f"${inv.total:,.2f}", inv.due_date,
            items_str, inv.description[:80],
        ))
        self._update_status()

    def _select_all(self):
        for idx, _ in self._visible_invoices():
            self.selected.add(idx)
        self._populate_tree()

    def _deselect_all(self):
        self.selected.clear()
        self._populate_tree()

    def _sort_by(self, col_name: str):
        if self.sort_col == col_name:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col_name
            self.sort_reverse = False
        self._populate_tree()

    # ---- Export ----

    def _export(self):
        if not self.selected:
            messagebox.showwarning("No Selection",
                                   "Please select at least one invoice.")
            return

        selected_invoices = [self.all_invoices[i]
                             for i in sorted(self.selected)]

        # Check for missing QB items
        missing = set()
        for inv in selected_invoices:
            for ln in inv.lines:
                if not ln.qb_item:
                    missing.add(f"Inv #{inv.reference}: \"{ln.description}\"")
        if missing:
            msg = ("These line items have no QB item mapping and will be "
                   "imported without an item name:\n\n"
                   + "\n".join(sorted(missing)[:15])
                   + "\n\nContinue anyway?")
            if not messagebox.askyesno("Missing Item Mappings", msg):
                return

        write_invoices_iif(OUTPUT_IIF, selected_invoices)
        self.export_status.set(
            f"Exported {len(selected_invoices)} invoices to {OUTPUT_IIF.name}")
        messagebox.showinfo(
            "Export Complete",
            f"Created {OUTPUT_IIF.name}\n"
            f"{len(selected_invoices)} invoices exported.\n\n"
            f"Import into QuickBooks:\n"
            f"  File > Utilities > Import > IIF Files\n\n"
            f"Note: Customers and Items must already exist in QB.")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    if not INVOICE_TSV.exists():
        print(f"ERROR: Invoice export not found: {INVOICE_TSV}")
        print("Export sales invoices from Manager as a TSV file first.")
        sys.exit(1)

    if not MAP_FILE.exists():
        print(f"ERROR: Mapping file not found: {MAP_FILE}")
        sys.exit(1)

    mappings = load_mappings()
    invoices = parse_invoices(INVOICE_TSV, mappings)
    print(f"Loaded {len(invoices)} invoices from {INVOICE_TSV.name}")

    if not invoices:
        print("No invoices found. Check the TSV file.")
        sys.exit(1)

    root = tk.Tk()
    InvoiceSelectorApp(root, invoices)
    root.mainloop()


if __name__ == "__main__":
    main()
