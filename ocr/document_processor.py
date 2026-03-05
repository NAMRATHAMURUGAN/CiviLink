"""
OCR Document Processing Module
Uses Tesseract for extracting text from government documents
"""

import pytesseract
import cv2
import numpy as np
from PIL import Image
import logging
import os
import tempfile
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import json

load_dotenv()

# Set Tesseract path
pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_CMD_PATH", "tesseract")

@dataclass
class OCRResult:
    extracted_text: str
    confidence: float
    detected_fields: Dict[str, str]
    document_type: Optional[str] = None
    processing_time: float = 0.0
    image_quality: Optional[str] = None

@dataclass
class FieldExtraction:
    field_name: str
    value: str
    confidence: float
    bbox: Optional[Tuple[int, int, int, int]] = None

class DocumentProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Document type patterns
        self.document_patterns = {
            "aadhaar_card": {
                "keywords": ["aadhaar", "आधार", "ஆதார்", "unique identification", "uidai"],
                "fields": {
                    "aadhaar_number": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
                    "name": r"Name\s*[:\-]?\s*([A-Za-z\s]+)",
                    "date_of_birth": r"DOB\s*[:\-]?\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
                    "gender": r"Gender\s*[:\-]?\s*(Male|Female|Other)",
                    "address": r"Address\s*[:\-]?\s*([\s\S]{10,200})"
                }
            },
            "death_certificate": {
                "keywords": ["death certificate", "death", "मृत्यु प्रमाण पत्र", "மரண சான்றிதழ்"],
                "fields": {
                    "deceased_name": r"Name\s*[:\-]?\s*([A-Za-z\s]+)",
                    "death_date": r"Date of Death\s*[:\-]?\s*(\d{2}[/\-]\d{2}[/\-]\d{4})",
                    "place_of_death": r"Place of Death\s*[:\-]?\s*([A-Za-z\s]+)"
                }
            },
            "bank_passbook": {
                "keywords": ["passbook", "bank", "account", "खाता", "வங்கி"],
                "fields": {
                    "account_number": r"Account\s*No\.?\s*[:\-]?\s*(\d{9,18})",
                    "bank_name": r"([A-Za-z\s]+Bank)",
                    "ifsc_code": r"IFSC\s*[:\-]?\s*([A-Z]{4}0[A-Z0-9]{6})",
                    "branch_name": r"Branch\s*[:\-]?\s*([A-Za-z\s]+)"
                }
            }
        }
    
    def process_document(self, image_data: bytes, document_type_hint: Optional[str] = None) -> OCRResult:
        """
        Process document image and extract text and fields
        
        Args:
            image_data: Raw image bytes
            document_type_hint: Optional hint about document type
            
        Returns:
            OCRResult with extracted information
        """
        import time
        start_time = time.time()
        
        try:
            # Preprocess image
            processed_image = self._preprocess_image(image_data)
            
            # Detect document type
            doc_type = self._detect_document_type(processed_image, document_type_hint)
            
            # Extract text using Tesseract
            extracted_text = self._extract_text(processed_image)
            
            # Calculate confidence
            confidence = self._calculate_ocr_confidence(processed_image, extracted_text)
            
            # Extract specific fields
            detected_fields = self._extract_fields(extracted_text, doc_type)
            
            # Assess image quality
            image_quality = self._assess_image_quality(processed_image)
            
            processing_time = time.time() - start_time
            
            self.logger.info(f"Document processed in {processing_time:.2f}s, type: {doc_type}, confidence: {confidence:.2f}")
            
            return OCRResult(
                extracted_text=extracted_text,
                confidence=confidence,
                detected_fields=detected_fields,
                document_type=doc_type,
                processing_time=processing_time,
                image_quality=image_quality
            )
            
        except Exception as e:
            self.logger.error(f"Document processing failed: {str(e)}")
            return OCRResult(
                extracted_text="",
                confidence=0.0,
                detected_fields={},
                processing_time=time.time() - start_time
            )
    
    def _preprocess_image(self, image_data: bytes) -> np.ndarray:
        """Preprocess image for better OCR results"""
        try:
            # Convert bytes to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                raise ValueError("Could not decode image")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Noise removal
            kernel = np.ones((1, 1), np.uint8)
            processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Deskew if needed
            processed = self._deskew_image(processed)
            
            return processed
            
        except Exception as e:
            self.logger.error(f"Image preprocessing failed: {str(e)}")
            # Return original image as fallback
            nparr = np.frombuffer(image_data, np.uint8)
            return cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    
    def _deskew_image(self, image: np.ndarray) -> np.ndarray:
        """Deskew image to improve OCR accuracy"""
        try:
            # Find contours
            contours, _ = cv2.findContours(image, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contours = sorted(contours, key=cv2.contourArea, reverse=True)
            
            # Get largest contour
            if contours:
                largest_contour = contours[0]
                
                # Get minimum area rectangle
                rect = cv2.minAreaRect(largest_contour)
                angle = rect[-1]
                
                # Correct angle
                if angle < -45:
                    angle = -(90 + angle)
                else:
                    angle = -angle
                
                # Rotate image
                (h, w) = image.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                rotated = cv2.warpAffine(image, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
                
                return rotated
            
            return image
            
        except Exception as e:
            self.logger.error(f"Deskewing failed: {str(e)}")
            return image
    
    def _extract_text(self, image: np.ndarray) -> str:
        """Extract text using Tesseract OCR"""
        try:
            # Configure Tesseract for better results
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz:-/ '
            
            text = pytesseract.image_to_string(image, config=custom_config)
            return text.strip()
            
        except Exception as e:
            self.logger.error(f"Text extraction failed: {str(e)}")
            return ""
    
    def _calculate_ocr_confidence(self, image: np.ndarray, extracted_text: str) -> float:
        """Calculate OCR confidence score"""
        try:
            # Get Tesseract confidence data
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            
            if data['conf']:
                # Calculate average confidence for detected text
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    return avg_confidence / 100.0
            
            # Fallback: confidence based on text length and patterns
            if len(extracted_text) > 50:
                # Check for common patterns
                if re.search(r"\b\d{12}\b", extracted_text):  # Aadhaar pattern
                    return 0.8
                elif re.search(r"\b[A-Z]{4}0[A-Z0-9]{6}\b", extracted_text):  # IFSC pattern
                    return 0.7
            
            return 0.5  # Default moderate confidence
            
        except Exception as e:
            self.logger.error(f"Confidence calculation failed: {str(e)}")
            return 0.5
    
    def _detect_document_type(self, image: np.ndarray, hint: Optional[str] = None) -> str:
        """Detect document type from extracted text"""
        try:
            # Extract text for analysis
            text = self._extract_text(image).lower()
            
            # If hint provided, check if it matches
            if hint and hint in self.document_patterns:
                pattern_keywords = self.document_patterns[hint]["keywords"]
                if any(keyword.lower() in text for keyword in pattern_keywords):
                    return hint
            
            # Check each document type
            for doc_type, patterns in self.document_patterns.items():
                keywords = patterns["keywords"]
                matches = sum(1 for keyword in keywords if keyword.lower() in text)
                if matches >= 2:  # Need at least 2 keyword matches
                    return doc_type
            
            return "unknown"
            
        except Exception as e:
            self.logger.error(f"Document type detection failed: {str(e)}")
            return "unknown"
    
    def _extract_fields(self, text: str, document_type: str) -> Dict[str, str]:
        """Extract specific fields based on document type"""
        try:
            if document_type not in self.document_patterns:
                return {}
            
            fields_config = self.document_patterns[document_type]["fields"]
            extracted_fields = {}
            
            for field_name, pattern in fields_config.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                    extracted_fields[field_name] = value.strip()
            
            return extracted_fields
            
        except Exception as e:
            self.logger.error(f"Field extraction failed: {str(e)}")
            return {}
    
    def _assess_image_quality(self, image: np.ndarray) -> str:
        """Assess image quality for OCR suitability"""
        try:
            # Calculate sharpness (Laplacian variance)
            gray = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image
            gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate brightness
            brightness = np.mean(gray)
            
            # Assess quality
            if sharpness > 100 and 50 < brightness < 200:
                return "excellent"
            elif sharpness > 50 and 30 < brightness < 220:
                return "good"
            elif sharpness > 20:
                return "fair"
            else:
                return "poor"
                
        except Exception as e:
            self.logger.error(f"Quality assessment failed: {str(e)}")
            return "unknown"
    
    def validate_extraction(self, ocr_result: OCRResult, expected_fields: List[str]) -> Tuple[bool, List[str]]:
        """Validate OCR extraction against expected fields"""
        try:
            missing_fields = []
            extracted_fields = ocr_result.detected_fields
            
            for field in expected_fields:
                if field not in extracted_fields or not extracted_fields[field]:
                    missing_fields.append(field)
            
            is_valid = len(missing_fields) == 0 and ocr_result.confidence > 0.6
            
            return is_valid, missing_fields
            
        except Exception as e:
            self.logger.error(f"Validation failed: {str(e)}")
            return False, expected_fields
    
    def get_extraction_summary(self, ocr_result: OCRResult) -> str:
        """Generate human-readable summary of extraction results"""
        try:
            summary_lines = [
                f"Document Type: {ocr_result.document_type or 'Unknown'}",
                f"Confidence: {ocr_result.confidence:.1%}",
                f"Image Quality: {ocr_result.image_quality or 'Unknown'}",
                f"Processing Time: {ocr_result.processing_time:.2f}s",
                "",
                "Extracted Information:"
            ]
            
            for field_name, value in ocr_result.detected_fields.items():
                summary_lines.append(f"  {field_name.replace('_', ' ').title()}: {value}")
            
            if not ocr_result.detected_fields:
                summary_lines.append("  No specific fields detected")
            
            return "\\n".join(summary_lines)
            
        except Exception as e:
            self.logger.error(f"Summary generation failed: {str(e)}")
            return "Error generating summary"

class DocumentValidator:
    """Validates extracted document information"""
    
    @staticmethod
    def validate_aadhaar(aadhaar_number: str) -> bool:
        """Validate Aadhaar number format"""
        # Remove spaces and check if exactly 12 digits
        clean_number = aadhaar_number.replace(" ", "")
        return len(clean_number) == 12 and clean_number.isdigit()
    
    @staticmethod
    def validate_ifsc(ifsc_code: str) -> bool:
        """Validate IFSC code format"""
        pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
        return bool(re.match(pattern, ifsc_code.upper()))
    
    @staticmethod
    def validate_bank_account(account_number: str) -> bool:
        """Validate bank account number format"""
        clean_number = account_number.replace(" ", "").replace("-", "")
        return 9 <= len(clean_number) <= 18 and clean_number.isdigit()
    
    @staticmethod
    def validate_date(date_str: str) -> bool:
        """Validate date format (DD/MM/YYYY or DD-MM-YYYY)"""
        patterns = [
            r'^\d{2}\/\d{2}\/\d{4}$',
            r'^\d{2}-\d{2}-\d{4}$'
        ]
        return any(re.match(pattern, date_str) for pattern in patterns)
