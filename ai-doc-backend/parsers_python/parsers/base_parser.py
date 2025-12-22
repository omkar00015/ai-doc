"""
Base parser class for all bank statement parsers
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import re


@dataclass
class Transaction:
    """Transaction data structure"""
    date: str
    description: str
    debit: Optional[float] = None
    credit: Optional[float] = None
    balance: Optional[float] = None
    bank: str = ""

    def to_dict(self):
        """Convert to dictionary"""
        return asdict(self)


class BaseParser(ABC):
    """Base class for bank statement parsers"""

    def __init__(self, text: str):
        self.text = text
        self.lines = self._prepare_lines(text)
        self.transactions: List[Transaction] = []

    def _prepare_lines(self, text: str) -> List[str]:
        """Prepare text lines by cleaning and filtering"""
        lines = text.split('\n')
        return [
            ' '.join(line.split())  # Normalize whitespace
            for line in lines
            if line.strip()
        ]

    @abstractmethod
    def parse(self) -> Dict:
        """Parse transactions from text - must be implemented by subclasses"""
        pass

    def _extract_numbers(self, text: str) -> List[Dict]:
        """
        Extract all numbers from text with metadata
        Returns list of dicts with 'value' and 'has_decimal' keys
        """
        # Match numbers with optional commas and decimals
        pattern = r'\d+(?:[.,]\d+)*(?:[.,]\d{2})?'
        matches = re.findall(pattern, text)

        numbers = []
        for match in matches:
            has_decimal = '.' in match or ',' in match
            # Remove separators and convert to float
            numeric_value = float(match.replace(',', '').replace('.', '', match.count('.') - 1) if '.' in match else match.replace(',', ''))
            numbers.append({
                'original': match,
                'value': numeric_value,
                'has_decimal': has_decimal
            })

        return [n for n in numbers if n['value'] > 0]

    def _normalize_amount(self, value: float, has_decimal: bool) -> float:
        """Normalize amount - fix missing decimals due to OCR"""
        if value > 1000000 and not has_decimal:
            # Likely missing decimals, divide by 100
            return round(value / 100, 2)
        return round(value, 2)

    def _extract_description(self, text: str, bank: str = "") -> str:
        """
        Extract and clean description from text
        Remove dates, numbers, special chars, and bank-specific artifacts
        """
        # Remove dates
        text = re.sub(r'\d{1,2}-[A-Za-z]{3}-\d{4}', ' ', text)
        # Remove numbers
        text = re.sub(r'\d+(?:[.,]\d+)*(?:[.,]\d{2})?', ' ', text)
        # Remove special characters
        text = re.sub(r'[^a-zA-Z0-9\s\-\/]', ' ', text)

        # Remove common OCR artifacts and bank codes
        artifacts = [
            r'\b(neft|rtgs|axis|hdfc|icic|bsy|mos|seo|ref|con|obit|bot|moo|ww|cr|dr)\b',
            r'\b(byteam|bytm|byosh|bycsh|iftm|ftms|tms|tio|ttio|totz|moi|axi|ani|uxs)\b',
            r'\b(spo|poi|com|cri|nop|nbfc|paid|recvd|recd)\b',
        ]

        for artifact in artifacts:
            text = re.sub(artifact, ' ', text, flags=re.IGNORECASE)

        # Remove very short words (likely OCR noise)
        text = re.sub(r'\b[a-z]{1,2}\b', ' ', text, flags=re.IGNORECASE)

        # Normalize whitespace
        text = ' '.join(text.split())
        return text.strip()[:80]

    def _get_transaction_type(self, text: str) -> tuple:
        """
        Determine if transaction is debit or credit
        Returns (debit, credit) where one will be None
        """
        text_upper = text.upper()

        if re.search(r'\b(BY|CR|CREDIT)\b', text_upper):
            return (None, True)  # Credit transaction
        elif re.search(r'\b(TO|DR|DEBIT)\b', text_upper):
            return (True, False)  # Debit transaction
        else:
            return (None, True)  # Default to credit
