"""
Parser factory - routes to appropriate bank parser
"""
from typing import Dict
from .palus_parser import PalusParser
from .hdfc_parser import HDFCParser


class ParserFactory:
    """Factory to create and route to appropriate bank parser"""

    @staticmethod
    def detect_bank(text: str) -> str:
        """
        Detect which bank the statement belongs to
        Returns: 'PALUS', 'HDFC', or 'GENERIC'
        """
        text_upper = text.upper()

        if 'PALUS SAHAKARI' in text_upper:
            return 'PALUS'
        elif 'HDFC BANK' in text_upper or 'HDFC' in text_upper:
            return 'HDFC'
        else:
            return 'GENERIC'

    @staticmethod
    def get_parser(bank: str, text: str):
        """Get the appropriate parser for the bank"""
        if bank == 'PALUS':
            return PalusParser(text)
        elif bank == 'HDFC':
            return HDFCParser(text)
        else:
            # Generic parser - use Palus as default for now
            return PalusParser(text)

    @staticmethod
    def parse(text: str) -> Dict:
        """
        Main parsing method - auto-detects bank and parses
        Returns: Dict with 'success', 'transactions', 'confidence', and 'bank'
        """
        print(f"[ParserFactory] Received text of length: {len(text)}")
        
        bank = ParserFactory.detect_bank(text)
        print(f"[ParserFactory] Detected bank: {bank}")
        
        parser = ParserFactory.get_parser(bank, text)
        result = parser.parse()
        
        # Convert parser result format to expected API format
        # Parser returns: {'rows': [...], 'confidence': ...}
        # API expects: {'success': bool, 'transactions': [...], 'confidence': ..., 'bank': ...}
        
        transactions = result.get('rows', [])
        
        return {
            'success': True,
            'transactions': transactions,
            'confidence': result.get('confidence', 0),
            'bank': bank
        }
