"""
Manager Accounting Protocol Buffer Decoder
Decodes binary Protocol Buffer data from Manager backup files into readable formats.
"""

import sqlite3
import struct
import json
import re
from pathlib import Path
from collections import defaultdict
import pandas as pd

class ManagerProtobufDecoder:
    def __init__(self, backup_file_path):
        """Initialize the decoder with a Manager backup file."""
        self.backup_file = Path(backup_file_path)
        if not self.backup_file.exists():
            raise FileNotFoundError(f"Backup file not found: {backup_file_path}")
        
        self.conn = None
        self.objects = []
        self.objects_by_type = defaultdict(list)
        
    def connect(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(str(self.backup_file))
        print(f"[OK] Connected to: {self.backup_file.name}")
    
    def extract_string(self, data, start_pos=0):
        """
        Extract a string from protobuf data.
        Protobuf strings are encoded as: field_tag + length + string_bytes
        """
        strings = []
        pos = start_pos
        
        while pos < len(data):
            # Look for string field markers (wire type 2 = length-delimited)
            # Field tags are encoded as (field_number << 3) | wire_type
            # Wire type 2 is for strings
            if pos + 1 >= len(data):
                break
                
            tag = data[pos]
            wire_type = tag & 0x07
            
            if wire_type == 2:  # Length-delimited (strings, bytes, embedded messages)
                pos += 1
                if pos >= len(data):
                    break
                
                # Read length (varint encoding)
                length, bytes_read = self.read_varint(data, pos)
                pos += bytes_read
                
                if length > 0 and pos + length <= len(data):
                    try:
                        string_bytes = data[pos:pos + length]
                        # Try to decode as UTF-8
                        decoded = string_bytes.decode('utf-8', errors='ignore')
                        # Remove null bytes and control characters
                        decoded = ''.join(c for c in decoded if c.isprintable() or c in '\n\r\t')
                        decoded = decoded.strip()
                        # Only keep strings that look meaningful (printable characters)
                        if decoded and len(decoded) > 0:
                            strings.append(decoded)
                    except:
                        pass
                    pos += length
                else:
                    pos += 1
            else:
                pos += 1
        
        return strings
    
    def read_varint(self, data, pos):
        """Read a varint from the data at position pos."""
        result = 0
        shift = 0
        bytes_read = 0
        
        while pos < len(data) and bytes_read < 10:  # Varint max 10 bytes
            byte = data[pos]
            result |= (byte & 0x7F) << shift
            bytes_read += 1
            pos += 1
            
            if not (byte & 0x80):  # High bit not set, end of varint
                break
            shift += 7
        
        return result, bytes_read
    
    def extract_guids(self, data):
        """Extract GUID-like patterns from binary data."""
        # GUIDs in binary might be stored as 16 bytes
        guids = []
        
        # Also look for GUID strings in the extracted strings
        strings = self.extract_string(data)
        guid_pattern = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', re.IGNORECASE)
        
        for s in strings:
            matches = guid_pattern.findall(s)
            guids.extend(matches)
        
        return guids
    
    def extract_numbers(self, data):
        """Extract numeric values from protobuf data."""
        numbers = []
        pos = 0
        
        while pos < len(data):
            if pos + 1 >= len(data):
                break
            
            tag = data[pos]
            wire_type = tag & 0x07
            
            if wire_type == 0:  # Varint
                pos += 1
                value, bytes_read = self.read_varint(data, pos)
                if value > 0 and value < 1e15:  # Reasonable range
                    numbers.append(value)
                pos += bytes_read
            elif wire_type == 1:  # 64-bit fixed
                if pos + 9 <= len(data):
                    value = struct.unpack('<d', data[pos+1:pos+9])[0]
                    if abs(value) < 1e15:
                        numbers.append(value)
                pos += 9
            elif wire_type == 5:  # 32-bit fixed
                if pos + 5 <= len(data):
                    value = struct.unpack('<f', data[pos+1:pos+5])[0]
                    if abs(value) < 1e15:
                        numbers.append(value)
                pos += 5
            else:
                pos += 1
        
        return numbers
    
    def decode_object(self, key, content_type, content, timestamp):
        """Decode a single object from the Objects table."""
        if isinstance(content, str):
            content = content.encode('latin-1')
        
        strings = self.extract_string(content)
        numbers = self.extract_numbers(content)
        guids = self.extract_guids(content)
        
        obj = {
            'key': key,
            'content_type': content_type,
            'timestamp': timestamp,
            'strings': strings,
            'numbers': numbers,
            'guids': guids,
            'raw_content': content
        }
        
        return obj
    
    def load_objects(self):
        """Load and decode all objects from the database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT Key, ContentType, Content, Timestamp FROM Objects ORDER BY Timestamp;")
        
        rows = cursor.fetchall()
        print(f"[OK] Loading {len(rows)} objects...")
        
        for row in rows:
            key, content_type, content, timestamp = row
            obj = self.decode_object(key, content_type, content, timestamp)
            self.objects.append(obj)
            self.objects_by_type[content_type].append(obj)
        
        print(f"[OK] Decoded {len(self.objects)} objects")
        print(f"[OK] Found {len(self.objects_by_type)} unique content types")
    
    def identify_object_types(self):
        """Identify what each content type represents based on patterns."""
        type_analysis = {}
        
        for content_type, objs in self.objects_by_type.items():
            sample_strings = []
            for obj in objs[:5]:  # Sample first 5
                sample_strings.extend(obj['strings'][:10])  # First 10 strings from each
            
            analysis = {
                'count': len(objs),
                'sample_strings': sample_strings[:20],  # Keep first 20 strings
                'avg_string_count': sum(len(o['strings']) for o in objs) / len(objs) if objs else 0,
                'avg_number_count': sum(len(o['numbers']) for o in objs) / len(objs) if objs else 0
            }
            
            # Try to identify type based on patterns
            if any('Bank' in s for s in sample_strings):
                analysis['likely_type'] = 'Bank Account'
            elif any('@' in s for s in sample_strings):
                analysis['likely_type'] = 'Customer or Contact'
            elif any(s in ['Sales', 'Income', 'Expenses', 'Interest'] for s in sample_strings):
                analysis['likely_type'] = 'Chart of Account'
            elif any('Rental' in s or 'Storage' in s for s in sample_strings):
                analysis['likely_type'] = 'Item or Service'
            elif len(objs) == 1 and 'US Dollar' in ' '.join(sample_strings):
                analysis['likely_type'] = 'Currency Setting'
            elif len(objs) == 1 and any('MM/dd/yyyy' in s for s in sample_strings):
                analysis['likely_type'] = 'Date Format Setting'
            else:
                analysis['likely_type'] = 'Unknown'
            
            type_analysis[content_type] = analysis
        
        return type_analysis
    
    def export_by_type(self, output_dir):
        """Export decoded objects grouped by type."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        type_analysis = self.identify_object_types()
        
        # Create summary report
        summary_path = output_dir / "DECODED_OBJECTS_SUMMARY.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("# Manager Decoded Objects Summary\n\n")
            f.write(f"**Total Objects**: {len(self.objects)}\n\n")
            f.write(f"**Unique Content Types**: {len(self.objects_by_type)}\n\n")
            f.write("---\n\n")
            f.write("## Content Types Analysis\n\n")
            
            for content_type, analysis in sorted(type_analysis.items(), key=lambda x: x[1]['count'], reverse=True):
                f.write(f"### {content_type}\n\n")
                f.write(f"**Count**: {analysis['count']}\n\n")
                f.write(f"**Likely Type**: {analysis['likely_type']}\n\n")
                f.write(f"**Avg Strings per Object**: {analysis['avg_string_count']:.1f}\n\n")
                f.write(f"**Avg Numbers per Object**: {analysis['avg_number_count']:.1f}\n\n")
                
                if analysis['sample_strings']:
                    f.write("**Sample Strings**:\n")
                    for s in analysis['sample_strings'][:15]:
                        if s.strip():
                            f.write(f"- {s}\n")
                    f.write("\n")
                
                f.write("---\n\n")
        
        print(f"[OK] Summary written to: {summary_path.name}")
        
        # Export each type to CSV
        for content_type, objs in self.objects_by_type.items():
            analysis = type_analysis[content_type]
            safe_name = content_type[:8] if len(content_type) > 8 else content_type
            likely_type = analysis['likely_type'].replace(' ', '_')
            
            csv_path = output_dir / f"decoded_{likely_type}_{safe_name}.csv"
            
            # Create DataFrame
            rows = []
            for obj in objs:
                row = {
                    'key': obj['key'],
                    'content_type': obj['content_type'],
                    'timestamp': obj['timestamp'],
                    'all_strings': ' | '.join(obj['strings']),
                    'string_count': len(obj['strings']),
                    'number_count': len(obj['numbers'])
                }
                
                # Add individual string columns (up to 10)
                for i, s in enumerate(obj['strings'][:10]):
                    row[f'string_{i+1}'] = s
                
                # Add individual number columns (up to 5)
                for i, n in enumerate(obj['numbers'][:5]):
                    row[f'number_{i+1}'] = n
                
                rows.append(row)
            
            df = pd.DataFrame(rows)
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            print(f"[OK] Exported: {csv_path.name} ({len(objs)} objects)")
        
        return summary_path
    
    def export_structured_data(self, output_dir):
        """Export structured data for QuickBooks conversion."""
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        
        type_analysis = self.identify_object_types()
        
        # Extract Chart of Accounts
        accounts = []
        for content_type, analysis in type_analysis.items():
            if analysis['likely_type'] == 'Chart of Account':
                for obj in self.objects_by_type[content_type]:
                    if len(obj['strings']) > 0:
                        account = {
                            'key': obj['key'],
                            'name': obj['strings'][0] if obj['strings'] else '',
                            'all_data': ' | '.join(obj['strings'])
                        }
                        accounts.append(account)
        
        if accounts:
            df = pd.DataFrame(accounts)
            df.to_csv(output_dir / "chart_of_accounts_decoded.csv", index=False, encoding='utf-8-sig')
            print(f"[OK] Exported Chart of Accounts: {len(accounts)} accounts")
        
        # Extract Customers
        customers = []
        for content_type, analysis in type_analysis.items():
            if analysis['likely_type'] == 'Customer or Contact':
                for obj in self.objects_by_type[content_type]:
                    if len(obj['strings']) >= 2:
                        customer = {
                            'key': obj['key'],
                            'name': obj['strings'][0] if len(obj['strings']) > 0 else '',
                            'address': obj['strings'][1] if len(obj['strings']) > 1 else '',
                            'email': next((s for s in obj['strings'] if '@' in s), ''),
                            'all_data': ' | '.join(obj['strings'])
                        }
                        customers.append(customer)
        
        if customers:
            df = pd.DataFrame(customers)
            df.to_csv(output_dir / "customers_decoded.csv", index=False, encoding='utf-8-sig')
            print(f"[OK] Exported Customers: {len(customers)} customers")
        
        # Extract Bank Accounts
        banks = []
        for content_type, analysis in type_analysis.items():
            if analysis['likely_type'] == 'Bank Account':
                for obj in self.objects_by_type[content_type]:
                    if len(obj['strings']) > 0:
                        bank = {
                            'key': obj['key'],
                            'name': obj['strings'][0] if obj['strings'] else '',
                            'all_data': ' | '.join(obj['strings'])
                        }
                        banks.append(bank)
        
        if banks:
            df = pd.DataFrame(banks)
            df.to_csv(output_dir / "bank_accounts_decoded.csv", index=False, encoding='utf-8-sig')
            print(f"[OK] Exported Bank Accounts: {len(banks)} banks")
        
        # Extract Items/Services
        items = []
        for content_type, analysis in type_analysis.items():
            if analysis['likely_type'] == 'Item or Service':
                for obj in self.objects_by_type[content_type]:
                    if len(obj['strings']) > 0:
                        item = {
                            'key': obj['key'],
                            'name': obj['strings'][0] if obj['strings'] else '',
                            'description': obj['strings'][1] if len(obj['strings']) > 1 else '',
                            'all_data': ' | '.join(obj['strings'])
                        }
                        items.append(item)
        
        if items:
            df = pd.DataFrame(items)
            df.to_csv(output_dir / "items_services_decoded.csv", index=False, encoding='utf-8-sig')
            print(f"[OK] Exported Items/Services: {len(items)} items")
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("[OK] Database connection closed")

def main():
    """Main entry point."""
    backup_file = r"C:\Scripts\Manager2QB\Roberts Orchards LLC (2026-01-29-1559).manager"
    output_dir = r"C:\Scripts\Manager2QB\manager_decoded"
    
    print("\n" + "="*60)
    print("Manager Protocol Buffer Decoder")
    print("="*60)
    
    try:
        decoder = ManagerProtobufDecoder(backup_file)
        decoder.connect()
        decoder.load_objects()
        
        print("\n" + "="*60)
        print("Exporting Decoded Data")
        print("="*60 + "\n")
        
        summary_path = decoder.export_by_type(output_dir)
        
        print("\n" + "="*60)
        print("Exporting Structured Data for QuickBooks")
        print("="*60 + "\n")
        
        decoder.export_structured_data(output_dir)
        
        decoder.close()
        
        print("\n" + "="*60)
        print("Decoding Complete!")
        print("="*60)
        print(f"\nOutput Directory: {output_dir}")
        print(f"Summary: {summary_path.name}")
        print("\nNext Steps:")
        print("1. Review DECODED_OBJECTS_SUMMARY.md")
        print("2. Examine the decoded CSV files")
        print("3. Verify the structured data exports")
        print("4. Proceed with QuickBooks IIF conversion")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
