"""
Flask backend for Document Reader - Pure Python implementation
Handles PDF upload, text extraction, OCR, parsing, and Excel generation

Converted from JavaScript Node.js backend to Python Flask
"""
import os
import json
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, List, Any
from bson.objectid import ObjectId

from flask import Flask, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from flask_pymongo import PyMongo
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_cors import CORS
import dotenv

# Import custom modules
from utils.pdf_extractor import extract_pdf_text
from utils.excel_exporter import export_to_excel
from utils.comparison_engine import compare_documents
from parsers.factory import ParserFactory
from models import User

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
dotenv.load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['MONGO_URI'] = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/document_reader')
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024))  # 50 MB
ALLOWED_EXTENSIONS = {'pdf'}

# Initialize extensions
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
CORS(app, supports_credentials=True, origins=['http://localhost:5173'])

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.find_by_id(mongo, user_id)


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def process_pdf(pdf_path: str) -> Tuple[dict, int]:
    """
    Process a PDF file: extract text, parse, and generate Excel
    Returns: (response_dict, http_status_code)
    """
    try:
        # Step 1: Extract text from PDF
        logger.info(f"Step 1: Extracting text from {pdf_path}")
        text, extraction_method = extract_pdf_text(pdf_path)

        if not text or len(text.strip()) < 50:
            logger.error("No text extracted from PDF")
            return {
                'success': False,
                'error': 'No text extracted from PDF. File may be empty or corrupted.'
            }, 400

        logger.info(f"Extracted {len(text)} characters using {extraction_method}")

        # Step 2: Parse text
        logger.info("Step 2: Parsing extracted text")
        parse_result = ParserFactory.parse(text)

        if not parse_result['success']:
            logger.warning(f"Parsing failed: {parse_result.get('error')}")
            return {
                'success': False,
                'error': f"Parsing failed: {parse_result.get('error', 'Unknown error')}"
            }, 400

        transactions = parse_result.get('transactions', [])
        bank = parse_result.get('bank', 'Unknown Bank')
        confidence = parse_result.get('confidence', 0)

        logger.info(f"Parsed {len(transactions)} transactions from {bank} (confidence: {confidence:.2f})")

        # Step 3: Generate Excel
        logger.info("Step 3: Generating Excel file")

        # Transactions are already dicts from parser
        # Just need to rename keys for Excel exporter
        transaction_dicts = []
        for txn in transactions:
            transaction_dicts.append({
                'date': txn.get('date', ''),
                'description': txn.get('description', ''),
                'debit amt': txn.get('debit', ''),
                'credit amt': txn.get('credit', ''),
                'balance': txn.get('balance', '')
            })

        excel_bytes = export_to_excel(transaction_dicts, bank=bank)

        logger.info("Excel file generated successfully")

        return {
            'success': True,
            'bank': bank,
            'confidence': confidence,
            'transaction_count': len(transactions),
            'extraction_method': extraction_method,
            'timestamp': datetime.now().isoformat()
        }, 200

    except Exception as e:
        logger.error(f"Error processing PDF: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }, 500


# ==================== HEALTH CHECK ====================

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Document Reader Backend',
        'timestamp': datetime.now().isoformat()
    }), 200


# ==================== AUTHENTICATION ====================

@app.route('/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()

        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400

        # Check if user already exists
        existing_user = User.find_by_email(mongo, email)
        if existing_user:
            return jsonify({'message': 'Email already registered'}), 400

        # Create new user
        user = User.create_user(mongo, email, password, name)
        login_user(user)

        logger.info(f"New user registered: {email}")
        return jsonify({
            'message': 'Registration successful',
            'user': user.to_dict()
        }), 201

    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        return jsonify({'message': 'Registration failed'}), 500


@app.route('/auth/login', methods=['POST'])
def login():
    """Login user"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'message': 'Email and password are required'}), 400

        # Find user
        user = User.find_by_email(mongo, email)
        
        if not user:
            logger.warning(f"Login failed: User not found for email {email}")
            return jsonify({'message': 'Invalid email or password'}), 401
            
        if not user.check_password(password):
            logger.warning(f"Login failed: Invalid password for email {email}")
            return jsonify({'message': 'Invalid email or password'}), 401

        # Login user
        login_user(user)
        logger.info(f"User logged in successfully: {email}")

        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        logger.error(f"Login exception for {email}: {str(e)}", exc_info=True)
        return jsonify({'message': f'Login failed: {str(e)}'}), 500


@app.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """Logout user"""
    try:
        logout_user()
        return jsonify({'message': 'Logout successful'}), 200
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        return jsonify({'message': 'Logout failed'}), 500


@app.route('/api/me', methods=['GET'])
def get_current_user():
    """Get current logged-in user"""
    if current_user.is_authenticated:
        return jsonify({'user': current_user.to_dict()}), 200
    return jsonify({'user': None}), 401


# ==================== FILE UPLOAD & PROCESSING ====================

@app.route('/upload', methods=['POST'])
@login_required
def upload_file():
    """
    Upload PDF and process it
    Returns: JSON with parsing results
    """
    logger.info("Received upload request")

    # Check if file is present
    if 'file' not in request.files:
        logger.error("No file part in request")
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']

    if file.filename == '':
        logger.error("No file selected")
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        logger.error(f"Invalid file type: {file.filename}")
        return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400

    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)

        logger.info(f"Saving file to: {file_path}")
        file.save(file_path)

        # Process the PDF
        response, status = process_pdf(file_path)

        if status == 200:
            # Generate Excel and return it
            try:
                text, _ = extract_pdf_text(file_path)
                parse_result = ParserFactory.parse(text)

                transactions = parse_result.get('transactions', [])
                bank = parse_result.get('bank', 'Unknown Bank')

                transaction_dicts = [
                    {
                        'date': txn.get('date', ''),
                        'description': txn.get('description', ''),
                        'debit amt': txn.get('debit', ''),
                        'credit amt': txn.get('credit', ''),
                        'balance': txn.get('balance', '')
                    }
                    for txn in transactions
                ]

                excel_bytes = export_to_excel(transaction_dicts, bank=bank)

                # Save Excel file
                excel_filename = f"{timestamp}_{filename.replace('.pdf', '.xlsx')}"
                excel_path = os.path.join(app.config['UPLOAD_FOLDER'], excel_filename)

                with open(excel_path, 'wb') as f:
                    f.write(excel_bytes)

                logger.info(f"Excel file saved: {excel_path}")

                # Save document metadata to MongoDB
                document_doc = {
                    'user_id': ObjectId(current_user.id),
                    'filename': unique_filename,
                    'original_name': filename,
                    'excel_filename': excel_filename,
                    'upload_date': datetime.utcnow(),
                    'status': 'completed',
                    'transaction_count': len(transactions),
                    'bank': bank,
                    'confidence': parse_result.get('confidence', 0)
                }
                mongo.db.documents.insert_one(document_doc)
                logger.info(f"Document metadata saved to MongoDB for user {current_user.email}")

                # Return both JSON response and Excel file download in separate endpoints
                response['excel_file'] = excel_filename
                response['pdf_file'] = unique_filename

                return jsonify(response), 200

            except Exception as e:
                logger.error(f"Error generating Excel: {e}")
                response['warning'] = "Parsing succeeded but Excel generation failed"
                return jsonify(response), 200

        else:
            return jsonify(response), status

    except RequestEntityTooLarge:
        logger.error("File size exceeds limit")
        return jsonify({'success': False, 'error': 'File size exceeds limit (max 50 MB)'}), 413

    except Exception as e:
        logger.error(f"Upload error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'}), 500

    finally:
        # Optionally cleanup temp file
        if os.path.exists(file_path):
            try:
                # Keep file for now, can be cleanup up later
                pass
            except Exception as e:
                logger.warning(f"Could not cleanup file: {e}")


# ==================== DOCUMENT MANAGEMENT ====================

@app.route('/api/documents', methods=['GET'])
@login_required
def list_user_documents():
    """List all documents for the current user"""
    try:
        documents = list(mongo.db.documents.find(
            {'user_id': ObjectId(current_user.id)}
        ).sort('upload_date', -1))
        
        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            doc['_id'] = str(doc['_id'])
            doc['user_id'] = str(doc['user_id'])
            doc['upload_date'] = doc['upload_date'].isoformat() if doc.get('upload_date') else None
        
        return jsonify({'documents': documents}), 200
    
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        return jsonify({'error': 'Failed to list documents'}), 500


# ==================== DOWNLOAD ENDPOINTS ====================

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename: str):
    """Download a processed file (PDF or Excel)"""
    logger.info(f"Download request for: {filename}")

    # Validate filename (prevent directory traversal)
    filename = secure_filename(filename)

    if not filename:
        return jsonify({'error': 'Invalid filename'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Check if file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return jsonify({'error': 'File not found'}), 404

    # Determine MIME type
    if filename.endswith('.xlsx'):
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif filename.endswith('.pdf'):
        mimetype = 'application/pdf'
    else:
        mimetype = 'application/octet-stream'

    logger.info(f"Sending file: {file_path}")
    return send_file(file_path, mimetype=mimetype, as_attachment=True, download_name=filename)


# ==================== PARSING ENDPOINTS (For backwards compatibility) ====================

@app.route('/parse', methods=['POST'])
def parse():
    """
    Parse OCR text directly
    Expects: {"text": "..."}
    Returns: {"success": bool, "bank": str, "confidence": float, "rows": [...], ...}
    """
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text or len(text) < 50:
            return jsonify({
                'success': False,
                'error': 'Text too short for parsing'
            }), 400

        result = ParserFactory.parse(text)

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Parse error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/parse-json', methods=['POST'])
def parse_json():
    """
    Parse OCR text and return structured JSON
    Expects: {"text": "..."}
    Returns: {"success": bool, "bank": str, "transactions": [...], ...}
    """
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text or len(text) < 50:
            return jsonify({
                'success': False,
                'error': 'Text too short for parsing'
            }), 400

        result = ParserFactory.parse(text)

        # Transactions are already dicts from parser, no conversion needed
        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Parse JSON error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== DOCUMENT COMPARISON ====================

@app.route('/compare', methods=['POST'])
@login_required
def compare_files():
    """
    Compare two PDF documents using AI embeddings.
    Expects: multipart form with 'file_a' and 'file_b' PDF uploads.
    Returns: JSON with detailed comparison results including matches,
             modifications, and missing sections.
    """
    logger.info("Received document comparison request")

    # Validate both files are present
    if 'file_a' not in request.files or 'file_b' not in request.files:
        return jsonify({
            'success': False,
            'error': 'Two PDF files are required (file_a and file_b)'
        }), 400

    file_a = request.files['file_a']
    file_b = request.files['file_b']

    if file_a.filename == '' or file_b.filename == '':
        return jsonify({'success': False, 'error': 'Both files must be selected'}), 400

    if not allowed_file(file_a.filename) or not allowed_file(file_b.filename):
        return jsonify({'success': False, 'error': 'Only PDF files are allowed'}), 400

    file_path_a = None
    file_path_b = None

    try:
        # Save both files
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        name_a = secure_filename(file_a.filename)
        unique_a = f"{timestamp}_cmp_a_{name_a}"
        file_path_a = os.path.join(app.config['UPLOAD_FOLDER'], unique_a)
        file_a.save(file_path_a)

        name_b = secure_filename(file_b.filename)
        unique_b = f"{timestamp}_cmp_b_{name_b}"
        file_path_b = os.path.join(app.config['UPLOAD_FOLDER'], unique_b)
        file_b.save(file_path_b)

        logger.info(f"Saved comparison files: {unique_a}, {unique_b}")

        # Extract text from both PDFs
        text_a, method_a = extract_pdf_text(file_path_a)
        text_b, method_b = extract_pdf_text(file_path_b)

        if not text_a or len(text_a.strip()) < 10:
            return jsonify({
                'success': False,
                'error': f'Could not extract text from {name_a}. File may be empty or corrupted.'
            }), 400

        if not text_b or len(text_b.strip()) < 10:
            return jsonify({
                'success': False,
                'error': f'Could not extract text from {name_b}. File may be empty or corrupted.'
            }), 400

        logger.info(
            f"Extracted text - A: {len(text_a)} chars ({method_a}), "
            f"B: {len(text_b)} chars ({method_b})"
        )

        # Run comparison engine
        result = compare_documents(
            text_a=text_a,
            text_b=text_b,
            name_a=file_a.filename,
            name_b=file_b.filename,
        )

        # Save comparison to MongoDB
        comparison_doc = {
            'user_id': ObjectId(current_user.id),
            'document_a': file_a.filename,
            'document_b': file_b.filename,
            'file_a': unique_a,
            'file_b': unique_b,
            'extraction_method_a': method_a,
            'extraction_method_b': method_b,
            'summary': result.get('summary', {}),
            'embedding_method': result.get('embedding_method', 'unknown'),
            'processing_time': result.get('processing_time_seconds', 0),
            'created_at': datetime.utcnow(),
        }
        inserted = mongo.db.comparisons.insert_one(comparison_doc)
        result['comparison_id'] = str(inserted.inserted_id)

        logger.info(f"Comparison saved with ID: {result['comparison_id']}")
        return jsonify(result), 200

    except RequestEntityTooLarge:
        return jsonify({'success': False, 'error': 'File size exceeds limit (max 50 MB)'}), 413

    except Exception as e:
        logger.error(f"Comparison error: {e}", exc_info=True)
        return jsonify({'success': False, 'error': f'Comparison failed: {str(e)}'}), 500


@app.route('/api/comparisons', methods=['GET'])
@login_required
def list_comparisons():
    """List all comparisons for the current user."""
    try:
        comparisons = list(mongo.db.comparisons.find(
            {'user_id': ObjectId(current_user.id)}
        ).sort('created_at', -1))

        for comp in comparisons:
            comp['_id'] = str(comp['_id'])
            comp['user_id'] = str(comp['user_id'])
            comp['created_at'] = comp['created_at'].isoformat() if comp.get('created_at') else None

        return jsonify({'comparisons': comparisons}), 200

    except Exception as e:
        logger.error(f"Error listing comparisons: {e}", exc_info=True)
        return jsonify({'error': 'Failed to list comparisons'}), 500


@app.route('/api/comparisons/<comparison_id>', methods=['GET'])
@login_required
def get_comparison(comparison_id: str):
    """Get a specific comparison result by ID."""
    try:
        comp = mongo.db.comparisons.find_one({
            '_id': ObjectId(comparison_id),
            'user_id': ObjectId(current_user.id),
        })

        if not comp:
            return jsonify({'error': 'Comparison not found'}), 404

        comp['_id'] = str(comp['_id'])
        comp['user_id'] = str(comp['user_id'])
        comp['created_at'] = comp['created_at'].isoformat() if comp.get('created_at') else None

        return jsonify(comp), 200

    except Exception as e:
        logger.error(f"Error fetching comparison: {e}", exc_info=True)
        return jsonify({'error': 'Failed to fetch comparison'}), 500


# ==================== ERROR HANDLERS ====================

@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle file size limit errors"""
    return jsonify({'error': 'File size exceeds limit (max 50 MB)'}), 413


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal error: {error}")
    return jsonify({'error': 'Internal server error'}), 500


# ==================== STARTUP ====================

if __name__ == '__main__':
    logger.info("Starting Document Reader Backend Server")
    logger.info(f"Upload folder: {UPLOAD_FOLDER}")
    logger.info(f"Max file size: {MAX_FILE_SIZE / (1024 * 1024):.1f} MB")

    # Run Flask app
    app.run(
        host='0.0.0.0',
        port=5001,
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
