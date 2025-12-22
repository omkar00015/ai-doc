"""
Standalone script to test the parser locally
Usage: python test_parser.py < extracted_text.txt
or: python test_parser.py path/to/statement.pdf
"""
import sys
import json
from parsers.factory import ParserFactory


def test_with_text(text):
    """Test parser with raw text"""
    print("=" * 60)
    print("TESTING PARSER WITH TEXT")
    print("=" * 60)
    
    result = ParserFactory.parse(text)
    
    print(f"\nBank Detected: {result.get('bank')}")
    print(f"Transactions Found: {len(result.get('rows', []))}")
    print(f"Confidence: {result.get('confidence')}")
    
    print("\n" + "=" * 60)
    print("FIRST 10 TRANSACTIONS")
    print("=" * 60)
    
    for i, txn in enumerate(result.get('rows', [])[:10], 1):
        print(f"\n[{i}] {txn['date']} | {txn['description'][:40]}")
        print(f"    Debit: {txn['debit']} | Credit: {txn['credit']} | Balance: {txn['balance']}")
    
    print("\n" + "=" * 60)
    print(f"TOTAL TRANSACTIONS: {len(result.get('rows', []))}")
    print("=" * 60)
    
    return result


if __name__ == '__main__':
    if len(sys.argv) > 1:
        # Read from file
        filepath = sys.argv[1]
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                text = f.read()
            test_with_text(text)
        except FileNotFoundError:
            print(f"Error: File '{filepath}' not found")
            sys.exit(1)
    else:
        # Read from stdin
        print("Reading text from stdin (Ctrl+D to end)...")
        text = sys.stdin.read()
        test_with_text(text)
