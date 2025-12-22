"""
Palus Sahakari Bank statement parser
"""
import re
from typing import Dict, List
from .base_parser import BaseParser, Transaction


class PalusParser(BaseParser):
    """Parser specifically for Palus Sahakari Bank statements"""

    def __init__(self, text: str):
        super().__init__(text)
        self.bank_name = "PALUS SAHAKARI"

    def parse(self) -> Dict:
        """
        Parse Palus Sahakari bank statement
        Returns dict with 'rows' (list of transactions) and 'confidence' score
        """
        print(f"[PalusParser] Input text length: {len(self.text)}")
        
        self.transactions = self._extract_transactions()
        
        confidence = self._calculate_confidence()
        print(f"[PalusParser] Extracted {len(self.transactions)} transactions with confidence {confidence}")

        return {
            'rows': [t.to_dict() for t in self.transactions],
            'confidence': confidence
        }

    def _extract_transactions(self) -> List[Transaction]:
        """Extract all transactions from the parsed lines"""
        transactions = []
        i = 0
        date_count = 0

        while i < len(self.lines):
            line = self.lines[i]

            # Look for lines containing a date
            date_match = re.search(r'(\d{1,2}-[A-Za-z]{3}-\d{4})', line)

            if not date_match:
                i += 1
                continue

            date = date_match.group(1)
            date_count += 1

            # Collect this line and next lines for context
            block_text = line
            j = i + 1

            # Collect up to 3 more lines
            for k in range(3):
                if j >= len(self.lines):
                    break

                next_line = self.lines[j]

                # Stop if next line starts with a date
                if re.search(r'\d{1,2}-[A-Za-z]{3}-\d{4}', next_line[:25]):
                    break

                block_text += " " + next_line
                j += 1

            # Extract transaction details
            txn = self._extract_transaction_details(date, block_text)

            if txn:
                transactions.append(txn)

            i = j

        print(f"[PalusParser] Dates found: {date_count}, Transactions extracted: {len(transactions)}")
        return transactions

    def _extract_transaction_details(self, date: str, block_text: str) -> Transaction:
        """Extract detailed transaction information from a block of text"""
        
        # Extract all numbers
        numbers = self._extract_numbers(block_text)

        if len(numbers) < 1:
            return None

        # Sort by value to find amount and balance
        sorted_nums = sorted(numbers, key=lambda x: x['value'], reverse=True)

        # Identify balance and amount
        balance = self._normalize_amount(sorted_nums[0]['value'], sorted_nums[0]['has_decimal'])

        amount = 0
        if len(sorted_nums) >= 2:
            amount = self._normalize_amount(sorted_nums[1]['value'], sorted_nums[1]['has_decimal'])
        elif len(sorted_nums) == 1 and balance > 10:
            amount = balance

        # Determine transaction type (debit/credit)
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
            description = "Transfer"

        # Skip invalid entries
        if (debit is None and credit is None) or amount < 0.01:
            return None

        if any(keyword in description.upper() for keyword in ['PRINTED', 'STATEMENT', 'ACCOUNT']):
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

        if count >= 50:
            return 0.98
        elif count >= 30:
            return 0.95
        elif count >= 20:
            return 0.90
        elif count >= 10:
            return 0.80
        elif count >= 5:
            return 0.60
        elif count > 0:
            return 0.40
        else:
            return 0.20
