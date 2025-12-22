"""
PDF extraction module using pdfplumber and pytesseract for OCR
"""

import os
import tempfile
from pathlib import Path
from typing import Tuple
import logging
import shutil

# Load environment variables from .env file
try:
    import dotenv
    # Load .env from the parsers_python directory
    env_path = Path(__file__).parent.parent / '.env'
    dotenv.load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, will use system environment variables

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import pytesseract
    from pdf2image import convert_from_path
    
    # Configure Tesseract path from environment variable
    tesseract_path = os.getenv("TESSERACT_PATH")
    if tesseract_path and os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        logging.getLogger(__name__).info(f"Configured Tesseract path: {tesseract_path}")
    else:
        logging.getLogger(__name__).warning(f"TESSERACT_PATH not set or invalid: {tesseract_path}")
    
except ImportError:
    pytesseract = None
    convert_from_path = None

try:
    from PIL import Image, ImageEnhance
except ImportError:
    Image = None
    ImageEnhance = None


logger = logging.getLogger(__name__)


def get_poppler_path() -> str | None:
    """
    Detect Poppler path (Windows-safe)
    Priority:
    1. POPPLER_PATH env variable
    2. Known Windows install locations
    """

    # 1️⃣ Environment variable
    env_path = os.getenv("POPPLER_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    # 2️⃣ Known install paths (your system included)
    known_paths = [
        Path("C:/poppler-25.12.0/Library/bin"),
        Path("C:/poppler/Library/bin"),
    ]

    for path in known_paths:
        if path.exists():
            return str(path)

    return None


class PDFExtractor:
    """Extract text from PDF files using text extraction and OCR"""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.temp_dir = None

    def extract_text(self) -> Tuple[str, str]:
        """
        Extract text from PDF
        Returns: (text, extraction_method)
        extraction_method: 'native' or 'ocr'
        """
        logger.info(f"Extracting text from: {self.pdf_path}")

        native_text = self._extract_native_text()

        if native_text and len(native_text.strip()) > 100:
            logger.info(f"Extracted {len(native_text)} chars using native method")
            return native_text, "native"

        logger.info("Native extraction insufficient, using OCR")

        try:
            ocr_text = self._extract_ocr_text()
            return ocr_text, "ocr"
        except Exception as e:
            logger.error(f"OCR failed completely: {e}")
            logger.info("Returning native extraction fallback")
            return native_text, "native"

    def _extract_native_text(self) -> str:
        """Extract text using pdfplumber (native PDF text)"""
        if not pdfplumber:
            logger.warning("pdfplumber not installed, skipping native extraction")
            return ""

        try:
            text = ""
            with pdfplumber.open(self.pdf_path) as pdf:
                logger.info(f"PDF has {len(pdf.pages)} pages")

                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text() or ""
                        text += page_text + "\n"
                        logger.debug(f"Page {page_num}: {len(page_text)} chars")
                    except Exception as e:
                        logger.error(f"Error extracting page {page_num}: {e}")

            return text

        except Exception as e:
            logger.error(f"Native extraction failed: {e}")
            return ""

    def _extract_ocr_text(self) -> str:
        """Extract text using OCR (pytesseract + pdf2image)"""

        if not convert_from_path or not pytesseract:
            raise ImportError("pytesseract and pdf2image are required for OCR")

        if not Image:
            raise ImportError("Pillow is required for OCR image processing")

        poppler_path = get_poppler_path()
        if not poppler_path:
            raise RuntimeError(
                "Poppler not found. Install Poppler and set POPPLER_PATH "
                "or ensure it exists in a known location."
            )

        logger.info(f"Using Poppler path: {poppler_path}")

        try:
            self.temp_dir = tempfile.mkdtemp(prefix="pdf_ocr_")
            logger.info(f"Using temp dir: {self.temp_dir}")

            logger.info("Converting PDF to images...")
            images = convert_from_path(
                self.pdf_path,
                dpi=300,
                poppler_path=poppler_path,
                output_folder=self.temp_dir
            )

            logger.info(f"Converted {len(images)} pages to images")

            full_text = ""

            for idx, image in enumerate(images, 1):
                try:
                    enhanced_image = self._enhance_image(image)

                    logger.info(f"Running OCR on page {idx}...")
                    text = pytesseract.image_to_string(
                        enhanced_image,
                        lang="eng"
                    )

                    full_text += text + "\n"
                    logger.debug(f"Page {idx}: {len(text)} chars extracted")

                except Exception as e:
                    logger.error(f"OCR failed for page {idx}: {e}")

            logger.info(f"Total OCR text extracted: {len(full_text)} chars")
            return full_text

        finally:
            self._cleanup_temp()

    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image for better OCR accuracy"""
        try:
            image = image.convert("L")

            image = ImageEnhance.Contrast(image).enhance(2.0)
            image = ImageEnhance.Sharpness(image).enhance(2.0)

            return image

        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image

    def _cleanup_temp(self):
        """Clean up temporary OCR files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.debug(f"Cleaned up temp dir: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup temp dir: {e}")


def extract_pdf_text(pdf_path: str) -> Tuple[str, str]:
    """
    Extract text from PDF file
    Returns:
        (text, method) -> method is 'native' or 'ocr'
    """
    extractor = PDFExtractor(pdf_path)
    return extractor.extract_text()
