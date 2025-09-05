import os
import logging
from typing import Optional
import tempfile
try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # Set debug level globally for example

class OCRProcessor:
    def __init__(self):
        self.ocr_engine = None

        # Initialize PaddleOCR safely, fallback to None if fails
        if PADDLEOCR_AVAILABLE:
            try:
                self.ocr_engine = PaddleOCR(
                    lang='en',
                    text_detection_model_name='PP-OCRv5_server_det',
                    text_recognition_model_name='PP-OCRv5_server_rec',
                    use_angle_cls=True,  # Optional angle classification
                    det_limit_side_len=8000  # Increase max side length to avoid internal resizing
                )
                logger.info("PaddleOCR initialized successfully")
            except Exception as e:
                logger.warning(f"PaddleOCR initialization failed: {e}. Falling back to Tesseract.")
                self.ocr_engine = None
        else:
            logger.warning("PaddleOCR not available. Using Tesseract as fallback.")

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Optional preprocessing: convert to grayscale, enhance contrast, resize, etc.
        Customize this function to improve OCR results on your images.
        """
        # Example: convert to grayscale (uncomment and modify as needed)
        # image = image.convert('L')
        # Example: resize if image is too small
        # w, h = image.size
        # if w < 1000:
        #     image = image.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
        return image

    def extract_text_from_image(self, image_path: str) -> Optional[str]:
        """Extract text from image file path using PaddleOCR or fallback to Tesseract"""
        try:
            # Preprocess image optionally
            img = Image.open(image_path)
            img = self._preprocess_image(img)
            # Save to temp file the preprocessed image for PaddleOCR predict()
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                img.save(tmp_file.name, format='PNG')
                preprocessed_path = tmp_file.name

            if self.ocr_engine:
                texts = self.ocr_engine.predict(input=preprocessed_path)
                logger.info(f"PaddleOCR raw output: {texts}")
                text_lines = []
                if texts:
                    for entry in texts:
                        # Use 'rec_texts' key for recognized text as per PaddleOCR output
                        if "rec_texts" in entry:
                            for text in entry["rec_texts"]:
                                if text.strip():
                                    text_lines.append(text)
                # Clean up temp file
                try:
                    os.unlink(preprocessed_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temp preprocessed image: {e}")

                if text_lines:
                    logger.info("PaddleOCR extraction succeeded")
                    print("paddle here")
                    return "\n".join(text_lines)

            # PaddleOCR not available or returned empty -> fallback to Tesseract
            logger.info("Falling back to Tesseract OCR")
            print("tesseract here")
            return self._tesseract_ocr(image_path)

        except Exception as e:
            logger.error(f"OCR error for {image_path}: {e}")
            return self._tesseract_ocr(image_path)

    def _tesseract_ocr(self, image_path: str) -> Optional[str]:
        """Fallback text extraction using Tesseract OCR"""
        try:
            text = pytesseract.image_to_string(Image.open(image_path))
            return text if text.strip() else None
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return None

    def process_pdf(self, pdf_path: str) -> Optional[str]:
        """Convert PDF to images and perform OCR on each page, returning combined text."""
        try:
            # Convert PDF to images at 300 dpi for good quality
            images = convert_from_path(pdf_path, dpi=300)
            all_text = []
            for i, image in enumerate(images):
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_img:
                    image.save(temp_img.name, 'PNG')
                    temp_img_path = temp_img.name

                try:
                    text = self.extract_text_from_image(temp_img_path)
                    if text:
                        all_text.append(f"--- Page {i+1} ---\n{text}")
                finally:
                    try:
                        os.unlink(temp_img_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete temp image file: {e}")
            return "\n\n".join(all_text) if all_text else None

        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return None

    def process_document(self, file_path: str) -> Optional[str]:
        """General document processor for image and PDF files, with logging."""
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        file_ext = os.path.splitext(file_path)[1].lower()
        logger.info(f"Processing document {file_path} with extension {file_ext}")

        if file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return self.extract_text_from_image(file_path)
        elif file_ext == '.pdf':
            return self.process_pdf(file_path)
        else:
            logger.error(f"Unsupported file format: {file_ext}")
            return None
