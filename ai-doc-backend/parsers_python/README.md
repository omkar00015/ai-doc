# Bank Statement Parser - Python Module

This is the Python-based parsing module for extracting transactions from bank statements. It handles the complex OCR text parsing logic that was previously in JavaScript.

## Directory Structure

```
parsers_python/
├── parsers/
│   ├── __init__.py           # Package initialization
│   ├── base_parser.py        # Base parser class
│   ├── palus_parser.py       # Palus Sahakari parser
│   ├── hdfc_parser.py        # HDFC Bank parser
│   └── factory.py            # Parser factory/router
├── app.py                     # Flask API server
├── test_parser.py            # Standalone test script
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Installation

### 1. Install Python Dependencies

```bash
cd parsers_python
pip install -r requirements.txt
```

### 2. Run the Flask API Server (Recommended)

```bash
python app.py
```

The server will start on `http://127.0.0.1:5001`

Alternatively, run in background:

```bash
# Windows
start python app.py

# Linux/Mac
python app.py &
```

## Usage

### Option 1: Via Flask API (Recommended)

The Node.js backend will automatically call the Flask API when parsing.

**Endpoint:** `POST http://127.0.0.1:5001/parse`

**Request:**
```json
{
  "text": "extracted OCR text here..."
}
```

**Response:**
```json
{
  "success": true,
  "rows": [
    {
      "date": "08-Apr-2025",
      "description": "Transfer to account",
      "debit": null,
      "credit": 258.50,
      "balance": 2672837.01,
      "bank": "PALUS SAHAKARI"
    }
  ],
  "confidence": 0.95,
  "bank": "PALUS",
  "count": 19
}
```

### Option 2: Standalone Testing

Test the parser with extracted text:

```bash
python test_parser.py < extracted_text.txt
```

Or with a text file:

```bash
python test_parser.py path/to/extracted_text.txt
```

## Parsers

### Palus Sahakari Parser (`PalusParser`)

Handles Palus Sahakari bank statements with features:
- Flexible date pattern matching (handles OCR corruption)
- Robust amount normalization (handles missing decimals)
- Smart transaction type detection (debit/credit)
- Aggressive text cleaning and artifact removal

**Key Features:**
- Handles heavy OCR corruption
- Extracts up to 3 context lines per transaction
- Auto-normalizes amounts > 1,000,000 by dividing by 100

### HDFC Bank Parser (`HDFCParser`)

Handles HDFC Bank statements with features:
- Cleaner date format (DD/MM/YYYY)
- Standard transaction structure
- Similar robustness to Palus parser

## How It Works

1. **Text Input:** Receives extracted OCR text from Node.js
2. **Bank Detection:** Automatically detects bank type from text
3. **Line Processing:** Splits text into lines and normalizes whitespace
4. **Date Extraction:** Finds transaction lines by date patterns
5. **Amount Extraction:** Extracts and normalizes numeric values
6. **Transaction Type Detection:** Determines debit/credit from keywords
7. **Description Cleaning:** Removes OCR artifacts and bank codes
8. **Validation:** Filters invalid transactions
9. **Output:** Returns structured transaction list with confidence score

## Architecture

### Base Parser Class

The `BaseParser` class provides:
- Common text processing methods
- Number extraction with metadata
- Amount normalization
- Description cleaning
- Transaction type detection

### Parser Factory

The `ParserFactory` class:
- Auto-detects bank type
- Routes to appropriate parser
- Provides main `parse()` method

## Configuration

### Adjust Logging

Edit `app.py` to change Flask logging:

```python
# Enable debug logging
log.setLevel(logging.DEBUG)

# Or set Flask debug mode
app.run(host='127.0.0.1', port=5001, debug=True)
```

### Add New Bank Parser

1. Create new file `parsers/newbank_parser.py`
2. Extend `BaseParser` class
3. Implement `parse()` and `_extract_transactions()` methods
4. Register in `ParserFactory.get_parser()`

## Testing

### Run Tests

```bash
python -m pytest test_parser.py
```

### Test with Sample Data

```python
from parsers.factory import ParserFactory

text = "... extracted OCR text ..."
result = ParserFactory.parse(text)
print(f"Found {len(result['rows'])} transactions")
```

## Troubleshooting

### Python not found

Make sure Python 3.8+ is installed and in PATH:

```bash
python --version
```

### Flask not found

Install Flask:

```bash
pip install -r requirements.txt
```

### Port 5001 already in use

Change the port in `app.py`:

```python
app.run(host='127.0.0.1', port=5002)  # Use different port
```

### No transactions extracted

Check:
1. Text contains valid dates in DD-MMM-YYYY format
2. Text contains numeric amounts
3. Bank detection is correct (check logs)
4. Run `test_parser.py` for debugging

## Performance

- **Average parsing time:** < 1 second per statement
- **Memory usage:** < 50MB
- **Concurrent requests:** Flask handles multiple requests

## Future Improvements

- [ ] Add more bank parsers (Axis, Kotak, etc.)
- [ ] Implement ML-based transaction classification
- [ ] Add OCR pre-processing filters
- [ ] Support for different statement formats
- [ ] Batch processing API
