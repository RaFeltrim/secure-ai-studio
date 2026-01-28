#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Regression Visual Tests
Automated testing for watermark integrity and metadata verification

Features:
- Visual watermark detection and validation
- Metadata integrity checking
- Automated regression testing
- Image comparison algorithms
- Compliance verification
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import hashlib
import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import pytest
from skimage.metrics import structural_similarity as ssim
import warnings
warnings.filterwarnings("ignore")

@dataclass
class VisualTestResult:
    """Visual test result data structure"""
    test_name: str
    passed: bool
    confidence: float
    details: Dict[str, Any]
    execution_time: float
    timestamp: str

@dataclass
class WatermarkDetectionResult:
    """Watermark detection result"""
    detected: bool
    position: Optional[Tuple[int, int]]
    opacity: Optional[float]
    text_content: Optional[str]
    confidence: float

class VisualRegressionTester:
    """
    Automated visual regression testing system
    """
    
    def __init__(self, test_data_dir: str = "tests/visual_test_data"):
        """Initialize visual regression tester"""
        self.test_data_dir = Path(test_data_dir)
        self.test_data_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logging()
        
        # Reference images for comparison
        self.reference_images = {}
        self.baseline_metadata = {}
        
        self.logger.info("👁️ Visual Regression Tester initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('VisualRegression')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def create_reference_image(self, image_path: str, 
                             watermark_text: str = "CONFIDENTIAL",
                             metadata: Dict[str, Any] = None) -> str:
        """Create reference image with known watermark and metadata"""
        try:
            # Load original image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Apply standard watermark
            watermarked_img = self._apply_standard_watermark(img, watermark_text)
            
            # Add metadata
            metadata = metadata or {}
            metadata.update({
                'creation_tool': 'Secure AI Studio',
                'watermark_applied': True,
                'test_reference': True,
                'timestamp': datetime.now().isoformat()
            })
            
            # Save reference image
            reference_path = self.test_data_dir / f"reference_{Path(image_path).name}"
            cv2.imwrite(str(reference_path), watermarked_img)
            
            # Save metadata
            metadata_path = reference_path.with_suffix('.metadata.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Store hash for future comparison
            img_hash = self._calculate_image_hash(watermarked_img)
            self.reference_images[reference_path.name] = img_hash
            
            self.logger.info(f"✅ Reference image created: {reference_path}")
            return str(reference_path)
            
        except Exception as e:
            self.logger.error(f"❌ Reference image creation failed: {e}")
            raise
    
    def _apply_standard_watermark(self, img: np.ndarray, text: str) -> np.ndarray:
        """Apply standard watermark for reference images"""
        img_copy = img.copy()
        height, width = img.shape[:2]
        
        # Create watermark overlay
        watermark = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add text watermark
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = min(width, height) / 800
        thickness = max(1, int(font_scale * 2))
        
        # Calculate text size and position
        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_scale, thickness
        )
        
        x = width - text_width - 20
        y = height - 20
        
        # Draw text on watermark layer
        cv2.putText(watermark, text, (x, y), font, font_scale, (255, 255, 255), thickness)
        
        # Blend with original image (70% opacity)
        alpha = 0.7
        blended = cv2.addWeighted(img_copy, 1, watermark, alpha, 0)
        
        return blended
    
    def _calculate_image_hash(self, img: np.ndarray) -> str:
        """Calculate perceptual hash of image"""
        # Convert to grayscale
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Resize to standard size for comparison
        resized = cv2.resize(gray, (32, 32))
        
        # Calculate DCT
        dct = cv2.dct(np.float32(resized))
        
        # Extract top-left 8x8 coefficients
        dct_low_freq = dct[:8, :8]
        
        # Calculate median
        median = np.median(dct_low_freq)
        
        # Create hash
        hash_bits = (dct_low_freq > median).flatten()
        hash_str = ''.join(['1' if bit else '0' for bit in hash_bits])
        
        return hashlib.sha256(hash_str.encode()).hexdigest()
    
    def detect_watermark(self, image_path: str) -> WatermarkDetectionResult:
        """Detect and analyze watermark in image"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to different color spaces for analysis
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
            
            # Look for text-like patterns in brightness channel
            brightness = lab[:,:,0]
            
            # Apply edge detection
            edges = cv2.Canny(brightness, 50, 150)
            
            # Look for text regions using morphological operations
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 2))
            detected_text = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            
            # Find contours that might be text
            contours, _ = cv2.findContours(detected_text, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Analyze potential watermarks
            watermark_confidence = 0.0
            watermark_position = None
            watermark_text = None
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Filter by size and aspect ratio
                if w > 50 and h > 10 and w/h > 2:
                    # Check if this region has characteristics of watermark text
                    region_brightness = brightness[y:y+h, x:x+w]
                    contrast = np.std(region_brightness)
                    
                    if contrast > 20:  # High contrast suggests text
                        watermark_confidence = min(0.9, contrast / 50)
                        watermark_position = (x, y)
                        
                        # Try to read text (simplified OCR)
                        roi = img[y:y+h, x:x+w]
                        watermark_text = self._simple_ocr(roi)
                        break
            
            return WatermarkDetectionResult(
                detected=watermark_confidence > 0.3,
                position=watermark_position,
                opacity=None,  # Would need more sophisticated analysis
                text_content=watermark_text,
                confidence=watermark_confidence
            )
            
        except Exception as e:
            self.logger.error(f"❌ Watermark detection failed: {e}")
            return WatermarkDetectionResult(
                detected=False,
                position=None,
                opacity=None,
                text_content=None,
                confidence=0.0
            )
    
    def _simple_ocr(self, roi: np.ndarray) -> Optional[str]:
        """Simple OCR for watermark text detection"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            
            # Simple thresholding
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Look for common watermark text patterns
            text_patterns = [
                "CONFIDENTIAL", "SECURE", "COPYRIGHT", "PROTECTED",
                "DRAFT", "INTERNAL", "PRIVATE"
            ]
            
            # This is a simplified approach - in production, use proper OCR
            roi_text = pytesseract.image_to_string(thresh, config='--psm 8')
            
            for pattern in text_patterns:
                if pattern in roi_text.upper():
                    return pattern
            
            return roi_text.strip() if roi_text.strip() else None
            
        except Exception:
            return None
    
    def verify_watermark_integrity(self, image_path: str, 
                                 expected_text: str = None) -> VisualTestResult:
        """Verify watermark integrity in generated image"""
        start_time = time.time()
        
        try:
            # Detect watermark
            detection_result = self.detect_watermark(image_path)
            
            # Check if watermark is present
            has_watermark = detection_result.detected
            confidence = detection_result.confidence
            
            # Check text content if expected
            text_match = True
            if expected_text and detection_result.text_content:
                text_match = expected_text.upper() in detection_result.text_content.upper()
                if not text_match:
                    confidence *= 0.5  # Reduce confidence if text doesn't match
            
            passed = has_watermark and confidence > 0.5 and text_match
            
            execution_time = time.time() - start_time
            
            return VisualTestResult(
                test_name="watermark_integrity",
                passed=passed,
                confidence=confidence,
                details={
                    'watermark_detected': has_watermark,
                    'detected_text': detection_result.text_content,
                    'expected_text': expected_text,
                    'text_match': text_match,
                    'position': detection_result.position
                },
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return VisualTestResult(
                test_name="watermark_integrity",
                passed=False,
                confidence=0.0,
                details={'error': str(e)},
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )
    
    def verify_metadata_integrity(self, image_path: str) -> VisualTestResult:
        """Verify metadata integrity in image file"""
        start_time = time.time()
        
        try:
            # Load image with PIL to access metadata
            pil_img = Image.open(image_path)
            metadata = dict(pil_img.info)
            
            # Check for required metadata fields
            required_fields = [
                'Software', 'DateTime', 'Copyright'
            ]
            
            missing_fields = []
            present_fields = []
            
            for field in required_fields:
                if field in metadata:
                    present_fields.append(field)
                else:
                    missing_fields.append(field)
            
            # Check Secure AI Studio specific metadata
            has_secure_ai_metadata = any(
                'Secure AI' in str(value) or 'secure-ai' in str(value).lower()
                for value in metadata.values()
            )
            
            # Calculate confidence based on completeness
            total_checks = len(required_fields) + 1  # +1 for Secure AI metadata
            passed_checks = len(present_fields) + (1 if has_secure_ai_metadata else 0)
            confidence = passed_checks / total_checks
            
            passed = confidence >= 0.8  # 80% threshold
            
            execution_time = time.time() - start_time
            
            return VisualTestResult(
                test_name="metadata_integrity",
                passed=passed,
                confidence=confidence,
                details={
                    'present_fields': present_fields,
                    'missing_fields': missing_fields,
                    'has_secure_ai_metadata': has_secure_ai_metadata,
                    'total_metadata_fields': len(metadata)
                },
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return VisualTestResult(
                test_name="metadata_integrity",
                passed=False,
                confidence=0.0,
                details={'error': str(e)},
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )
    
    def compare_with_reference(self, test_image_path: str, 
                             reference_name: str) -> VisualTestResult:
        """Compare test image with reference image"""
        start_time = time.time()
        
        try:
            # Load images
            test_img = cv2.imread(test_image_path)
            reference_path = self.test_data_dir / reference_name
            
            if not reference_path.exists():
                raise FileNotFoundError(f"Reference image not found: {reference_name}")
            
            ref_img = cv2.imread(str(reference_path))
            
            # Resize images to same dimensions for comparison
            if test_img.shape != ref_img.shape:
                ref_img = cv2.resize(ref_img, (test_img.shape[1], test_img.shape[0]))
            
            # Calculate SSIM (Structural Similarity Index)
            gray_test = cv2.cvtColor(test_img, cv2.COLOR_BGR2GRAY)
            gray_ref = cv2.cvtColor(ref_img, cv2.COLOR_BGR2GRAY)
            
            similarity_score = ssim(gray_test, gray_ref)
            
            # Calculate MSE (Mean Squared Error)
            mse = np.mean((test_img.astype(float) - ref_img.astype(float)) ** 2)
            
            # Determine pass/fail based on thresholds
            similarity_threshold = 0.95  # 95% similarity required
            mse_threshold = 100  # Maximum allowed difference
            
            passed = similarity_score >= similarity_threshold and mse <= mse_threshold
            confidence = similarity_score
            
            execution_time = time.time() - start_time
            
            return VisualTestResult(
                test_name="reference_comparison",
                passed=passed,
                confidence=confidence,
                details={
                    'similarity_score': float(similarity_score),
                    'mse': float(mse),
                    'similarity_threshold': similarity_threshold,
                    'mse_threshold': mse_threshold
                },
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return VisualTestResult(
                test_name="reference_comparison",
                passed=False,
                confidence=0.0,
                details={'error': str(e)},
                execution_time=execution_time,
                timestamp=datetime.now().isoformat()
            )
    
    def run_complete_visual_test_suite(self, image_path: str, 
                                     reference_name: str = None,
                                     expected_watermark: str = "CONFIDENTIAL") -> List[VisualTestResult]:
        """Run complete visual test suite"""
        results = []
        
        # Test 1: Watermark integrity
        self.logger.info("🔍 Running watermark integrity test...")
        watermark_result = self.verify_watermark_integrity(image_path, expected_watermark)
        results.append(watermark_result)
        
        # Test 2: Metadata integrity
        self.logger.info("🔍 Running metadata integrity test...")
        metadata_result = self.verify_metadata_integrity(image_path)
        results.append(metadata_result)
        
        # Test 3: Reference comparison (if reference provided)
        if reference_name:
            self.logger.info("🔍 Running reference comparison test...")
            reference_result = self.compare_with_reference(image_path, reference_name)
            results.append(reference_result)
        
        # Overall summary
        passed_tests = sum(1 for result in results if result.passed)
        total_tests = len(results)
        overall_pass_rate = passed_tests / total_tests
        
        self.logger.info(f"📊 Visual test suite complete: {passed_tests}/{total_tests} tests passed")
        
        return results

# Pytest integration
class TestVisualRegression:
    """Pytest test class for visual regression testing"""
    
    @classmethod
    def setup_class(cls):
        """Setup test environment"""
        cls.tester = VisualRegressionTester()
        
        # Create test images
        cls.test_images = cls._create_test_images()
    
    @classmethod
    def _create_test_images(cls) -> Dict[str, str]:
        """Create test images for regression testing"""
        images = {}
        
        # Create base test image
        base_img = np.random.randint(50, 200, (512, 512, 3), dtype=np.uint8)
        base_path = "test_base_image.png"
        cv2.imwrite(base_path, base_img)
        images['base'] = base_path
        
        # Create properly watermarked image
        watermarked_img = cls.tester._apply_standard_watermark(base_img, "CONFIDENTIAL")
        watermarked_path = "test_watermarked_image.png"
        cv2.imwrite(watermarked_path, watermarked_img)
        images['watermarked'] = watermarked_path
        
        # Create reference image
        reference_path = cls.tester.create_reference_image(
            base_path,
            metadata={'test_case': 'regression_test'}
        )
        images['reference'] = reference_path
        
        return images
    
    def test_watermark_detection_positive(self):
        """Test that watermark is detected in watermarked image"""
        result = self.tester.verify_watermark_integrity(
            self.test_images['watermarked'],
            "CONFIDENTIAL"
        )
        
        assert result.passed, f"Watermark detection failed: {result.details}"
        assert result.confidence > 0.5, f"Low confidence: {result.confidence}"
    
    def test_watermark_detection_negative(self):
        """Test that watermark is not detected in base image"""
        result = self.tester.verify_watermark_integrity(
            self.test_images['base'],
            "CONFIDENTIAL"
        )
        
        # Should either fail to detect or have low confidence
        assert not result.passed or result.confidence < 0.3, "False positive watermark detection"
    
    def test_metadata_integrity(self):
        """Test metadata integrity verification"""
        result = self.tester.verify_metadata_integrity(self.test_images['watermarked'])
        assert result.passed, f"Metadata integrity check failed: {result.details}"
    
    def test_reference_comparison(self):
        """Test comparison with reference image"""
        result = self.tester.compare_with_reference(
            self.test_images['watermarked'],
            Path(self.test_images['reference']).name
        )
        
        assert result.passed, f"Reference comparison failed: {result.details}"

# Example usage
def main():
    """Demo visual regression testing"""
    print("👁️ VISUAL REGRESSION TEST DEMO")
    print("=" * 35)
    
    # Initialize tester
    tester = VisualRegressionTester()
    
    try:
        # Create test images
        print("🖼️ Creating test images...")
        
        # Base image
        base_img = np.random.randint(50, 200, (512, 512, 3), dtype=np.uint8)
        base_path = "demo_base_image.png"
        cv2.imwrite(base_path, base_img)
        
        # Watermarked image
        watermarked_img = tester._apply_standard_watermark(base_img, "CONFIDENTIAL")
        watermarked_path = "demo_watermarked_image.png"
        cv2.imwrite(watermarked_path, watermarked_img)
        
        # Create reference
        reference_path = tester.create_reference_image(
            base_path,
            metadata={'demo': True, 'purpose': 'testing'}
        )
        
        print(f"✅ Created test images")
        print(f"   Base: {base_path}")
        print(f"   Watermarked: {watermarked_path}")
        print(f"   Reference: {reference_path}")
        
        # Run test suite
        print("\n🧪 Running visual test suite...")
        results = tester.run_complete_visual_test_suite(
            watermarked_path,
            Path(reference_path).name,
            "CONFIDENTIAL"
        )
        
        # Display results
        print("\n📊 Test Results:")
        print("-" * 50)
        for result in results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} {result.test_name}")
            print(f"   Confidence: {result.confidence:.2f}")
            print(f"   Time: {result.execution_time:.3f}s")
            print(f"   Details: {result.details}")
            print()
        
        # Overall summary
        passed_count = sum(1 for r in results if r.passed)
        total_count = len(results)
        print(f"🎯 Summary: {passed_count}/{total_count} tests passed")
        
        # Cleanup
        for file_path in [base_path, watermarked_path]:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🧹 Cleaned up: {file_path}")
        
        return passed_count == total_count
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    import time
    try:
        import pytesseract
    except ImportError:
        print("⚠️  pytesseract not available, OCR functionality limited")
        pytesseract = None
    
    success = main()
    exit(0 if success else 1)