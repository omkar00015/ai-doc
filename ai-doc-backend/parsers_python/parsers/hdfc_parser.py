"""
HDFC Bank statement parser
"""
import re
from typing import Dict, List
from .base_parser import BaseParser, Transaction


class HDFCParser(BaseParser):
    """Parser specifically for HDFC Bank statements"""

    def __init__(self, text: str):
        super().__init__(text)
        self.bank_name = "HDFC BANK"

    def parse(self) -> Dict:
        """
        Parse HDFC Bank statement
        Returns dict with 'rows' (list of transactions) and 'confidence' score
        """
        print(f"[HDFCParser] Input text length: {len(self.text)}")
        
        self.transactions = self._extract_transactions()
        
        confidence = self._calculate_confidence()
        print(f"[HDFCParser] Extracted {len(self.transactions)} transactions with confidence {confidence}")

        return {
            'rows': [t.to_dict() for t in self.transactions],
            'confidence': confidence
        }

    def _extract_transactions(self) -> List[Transaction]:
        """Extract all transactions from the parsed lines"""
        transactions = []
        i = 0

        while i < len(self.lines):
            line = self.lines[i]

            # Look for HDFC transaction pattern: DATE DESCRIPTION DEBIT CREDIT BALANCE
            # HDFC typically has cleaner format compared to Palus
            date_match = re.search(r'(\d{2}/\d{2}/\d{4})', line)

            if not date_match:
                i += 1
                continue

            date_str = date_match.group(1)
            
            # Convert DD/MM/YYYY to DD-MMM-YYYY format for consistency
            try:
                date_parts = date_str.split('/')
                day, month, year = date_parts[0], int(date_parts[1]), date_parts[2]
                
                # Convert month number to name
                month_names = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                              'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                month_name = month_names[month]
                date = f"{day}-{month_name}-{year}"
            except:
                date = date_str

            # Collect this line and next line if needed
            block_text = line
            j = i + 1

            if j < len(self.lines):
                next_line = self.lines[j]
                # If next line doesn't start with date, it's a continuation
                if not re.search(r'\d{2}/\d{2}/\d{4}', next_line[:20]):
                    block_text += " " + next_line
                    j += 1

            # Extract transaction details
            txn = self._extract_transaction_details(date, block_text)

            if txn:
                transactions.append(txn)

            i = j

        return transactions

    def _extract_transaction_details(self, date: str, block_text: str) -> Transaction:
        """Extract detailed transaction information from a block of text"""
        
        # Extract all numbers - HDFC format is cleaner with decimal points
        numbers = self._extract_numbers(block_text)

        if len(numbers) < 2:
            return None

        # HDFC format: DATE DESCRIPTION DEBIT CREDIT BALANCE
        # The last two numbers are usually credit and balance
        # or debit and balance
        sorted_nums = sorted(numbers, key=lambda x: x['value'], reverse=True)

        balance = self._normalize_amount(sorted_nums[0]['value'], sorted_nums[0]['has_decimal'])
        amount = self._normalize_amount(sorted_nums[1]['value'], sorted_nums[1]['has_decimal']) if len(sorted_nums) >= 2 else 0

        # Determine transaction type
        is_debit, is_credit = self._get_transaction_type(block_text)

        debit = None
        credit = None

        if is_credit:
            credit = amount if amount > 0 else None
        elif is_debit:
            debit = amount if amount > 0 else None

        # Extract and clean description
        description = self._extract_description(block_text, self.bank_name)

        # Validation
        if not description or len(description) < 2:
            description = "Transaction"

        # Skip invalid entries
        if (debit is None and credit is None) or amount < 0.01:
            return None

        if any(keyword in description.upper() for keyword in ['STATEMENT', 'ACCOUNT', 'DATE']):
            return None

        return Transaction(
            date=date,
            description=description,
            debit=debit,
            credit=credit,
            balance=balance if balance > 0 else None,
            bank=self.bank_name
        )

    def _calculate_confidence(self) -> float:
        """Calculate parsing confidence based on number of transactions"""
        count = len(self.transactions)

        if count >= 100:
            return 0.98
        elif count >= 50:
            return 0.95
        elif count >= 20:
            return 0.85
        elif count >= 10:
            return 0.70
        elif count > 0:
            return 0.40
        else:
            return 0.20
