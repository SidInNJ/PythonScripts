"""
Manager Accounting Backup Explorer
Extracts all tables from a Manager backup file (SQLite database) and exports to CSV/Excel files.
Also generates comprehensive markdown documentation of the database structure.
"""

import sqlite3
import pandas as pd
import os
from pathlib import Path
from datetime import datetime
import json

class ManagerExplorer:
    def __init__(self, backup_file_path, output_dir=None):
        """
        Initialize the Manager Explorer.
        
        Args:
            backup_file_path: Path to the Manager backup file (.manager file)
            output_dir: Directory to save exported files (defaults to same directory as backup)
        """
        self.backup_file = Path(backup_file_path)
        
        if not self.backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file_path}")
        
        if output_dir is None:
            self.output_dir = self.backup_file.parent / "manager_exports"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(exist_ok=True)
        self.conn = None
        self.tables_info = {}
        
    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(str(self.backup_file))
            print(f"[OK] Connected to: {self.backup_file.name}")
        except sqlite3.Error as e:
            raise Exception(f"Failed to connect to database: {e}")
    
    def get_all_tables(self):
        """Get list of all tables in the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"[OK] Found {len(tables)} tables")
        return tables
    
    def get_table_schema(self, table_name):
        """Get schema information for a specific table."""
        cursor = self.conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        schema = []
        for col in columns:
            schema.append({
                'column_id': col[0],
                'name': col[1],
                'type': col[2],
                'not_null': bool(col[3]),
                'default_value': col[4],
                'primary_key': bool(col[5])
            })
        
        return schema
    
    def get_table_row_count(self, table_name):
        """Get the number of rows in a table."""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        return cursor.fetchone()[0]
    
    def get_sample_data(self, table_name, limit=5):
        """Get sample rows from a table."""
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT {limit};", self.conn)
            return df
        except Exception as e:
            print(f"  Warning: Could not read sample data from {table_name}: {e}")
            return None
    
    def export_table_to_csv(self, table_name):
        """Export a table to CSV file."""
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name};", self.conn)
            csv_path = self.output_dir / f"{table_name}.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"  [OK] Exported to CSV: {table_name}.csv ({len(df)} rows)")
            return csv_path, len(df)
        except Exception as e:
            print(f"  [ERROR] Failed to export {table_name} to CSV: {e}")
            return None, 0
    
    def export_table_to_excel(self, table_name):
        """Export a table to Excel file."""
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name};", self.conn)
            excel_path = self.output_dir / f"{table_name}.xlsx"
            df.to_excel(excel_path, index=False, engine='openpyxl')
            print(f"  [OK] Exported to Excel: {table_name}.xlsx ({len(df)} rows)")
            return excel_path, len(df)
        except Exception as e:
            print(f"  [ERROR] Failed to export {table_name} to Excel: {e}")
            return None, 0
    
    def analyze_table(self, table_name):
        """Analyze a table and gather all information."""
        print(f"\nAnalyzing table: {table_name}")
        
        schema = self.get_table_schema(table_name)
        row_count = self.get_table_row_count(table_name)
        sample_data = self.get_sample_data(table_name)
        
        csv_path, csv_rows = self.export_table_to_csv(table_name)
        excel_path, excel_rows = self.export_table_to_excel(table_name)
        
        self.tables_info[table_name] = {
            'schema': schema,
            'row_count': row_count,
            'sample_data': sample_data,
            'csv_path': csv_path,
            'excel_path': excel_path
        }
    
    def generate_markdown_documentation(self):
        """Generate comprehensive markdown documentation."""
        md_path = self.output_dir / "MANAGER_DATABASE_DOCUMENTATION.md"
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write("# Manager Accounting Database Documentation\n\n")
            f.write(f"**Source File**: `{self.backup_file.name}`\n\n")
            f.write(f"**Export Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Total Tables**: {len(self.tables_info)}\n\n")
            
            f.write("---\n\n")
            f.write("## Table of Contents\n\n")
            for table_name in sorted(self.tables_info.keys()):
                f.write(f"- [{table_name}](#{table_name.lower()})\n")
            
            f.write("\n---\n\n")
            f.write("## Tables Overview\n\n")
            f.write("| Table Name | Row Count | Columns |\n")
            f.write("|------------|-----------|----------|\n")
            
            for table_name in sorted(self.tables_info.keys()):
                info = self.tables_info[table_name]
                col_count = len(info['schema'])
                f.write(f"| {table_name} | {info['row_count']:,} | {col_count} |\n")
            
            f.write("\n---\n\n")
            f.write("## Detailed Table Information\n\n")
            
            for table_name in sorted(self.tables_info.keys()):
                info = self.tables_info[table_name]
                f.write(f"### {table_name}\n\n")
                f.write(f"**Row Count**: {info['row_count']:,}\n\n")
                
                f.write("**Schema**:\n\n")
                f.write("| Column | Type | Not Null | Default | Primary Key |\n")
                f.write("|--------|------|----------|---------|-------------|\n")
                
                for col in info['schema']:
                    not_null = "Yes" if col['not_null'] else ""
                    pk = "Yes" if col['primary_key'] else ""
                    default = str(col['default_value']) if col['default_value'] is not None else ""
                    f.write(f"| {col['name']} | {col['type']} | {not_null} | {default} | {pk} |\n")
                
                f.write("\n**Exported Files**:\n")
                f.write(f"- CSV: `{table_name}.csv`\n")
                f.write(f"- Excel: `{table_name}.xlsx`\n\n")
                
                if info['sample_data'] is not None and len(info['sample_data']) > 0:
                    f.write("**Sample Data** (first 5 rows):\n\n")
                    f.write("```\n")
                    f.write(info['sample_data'].to_string(index=False))
                    f.write("\n```\n\n")
                else:
                    f.write("**Sample Data**: No data available\n\n")
                
                f.write("---\n\n")
            
            f.write("## Notes for QuickBooks Conversion\n\n")
            f.write("### Key Tables to Review:\n\n")
            f.write("- **Chart of Accounts**: Look for tables containing account names, types, and balances\n")
            f.write("- **Customers**: Customer/client information\n")
            f.write("- **Vendors**: Supplier/vendor information\n")
            f.write("- **Items/Products**: Inventory or service items\n")
            f.write("- **Transactions**: Journal entries, invoices, bills, payments\n")
            f.write("- **Opening Balances**: Initial account balances (typically from earliest transaction dates)\n\n")
            
            f.write("### Opening Balances Strategy:\n\n")
            f.write("1. Identify the earliest transaction date in the Manager data\n")
            f.write("2. Calculate opening balances for all accounts as of that date\n")
            f.write("3. Create opening balance journal entry in QuickBooks\n")
            f.write("4. Import all subsequent transactions\n\n")
            
            f.write("### Import Order Recommendation:\n\n")
            f.write("1. Chart of Accounts\n")
            f.write("2. Customers\n")
            f.write("3. Vendors\n")
            f.write("4. Items/Products\n")
            f.write("5. Opening Balances (as journal entry)\n")
            f.write("6. Transactions (chronologically)\n\n")
        
        print(f"\n[OK] Documentation generated: {md_path.name}")
        return md_path
    
    def export_all(self):
        """Main method to export all tables and generate documentation."""
        print(f"\n{'='*60}")
        print("Manager Accounting Backup Explorer")
        print(f"{'='*60}")
        
        self.connect()
        tables = self.get_all_tables()
        
        print(f"\nExporting to: {self.output_dir}")
        print(f"{'='*60}")
        
        for table in tables:
            self.analyze_table(table)
        
        print(f"\n{'='*60}")
        print("Generating Documentation")
        print(f"{'='*60}")
        
        doc_path = self.generate_markdown_documentation()
        
        print(f"\n{'='*60}")
        print("Export Complete!")
        print(f"{'='*60}")
        print(f"\nExported Files Location: {self.output_dir}")
        print(f"Documentation: {doc_path.name}")
        print(f"\nTotal Tables Exported: {len(self.tables_info)}")
        print(f"Total Rows Exported: {sum(info['row_count'] for info in self.tables_info.values()):,}")
        
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("\n[OK] Database connection closed")

def main():
    """Main entry point."""
    backup_file = r"C:\Scripts\Manager2QB\Roberts Orchards LLC (2026-01-29-1559).manager"
    
    print("\nManager Accounting Backup Explorer")
    print("=" * 60)
    
    try:
        explorer = ManagerExplorer(backup_file)
        explorer.export_all()
        explorer.close()
        
        print("\n[OK] All operations completed successfully!")
        print("\nNext Steps:")
        print("1. Review the MANAGER_DATABASE_DOCUMENTATION.md file")
        print("2. Examine the exported CSV/Excel files")
        print("3. Identify which tables map to QuickBooks entities")
        print("4. Proceed with conversion script development")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
