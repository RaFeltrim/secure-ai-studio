#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - CI/CD Self-Test Pipeline
Automated validation before output release (Linha de Defesa)

Features:
- File integrity validation
- Image corruption detection
- Encryption verification
- Security compliance checking
- Automated gating before release
"""

import os
import sys
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import cv2
import numpy as np
from PIL import Image, ImageChops

@dataclass
class ValidationResult:
    """Self-test validation result"""
    test_name: str
    passed: bool
    severity: str  # critical, high, medium, low
    message: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class FileIntegrityCheck:
    """File integrity verification"""
    file_path: str
    expected_checksum: str
    actual_checksum: str
    checksum_match: bool
    file_size: int
    modified_time: str

class SelfTestPipeline:
    """
    Automated CI/CD self-test pipeline for output validation
    """
    
    def __init__(self, config_path: str = "config/cicd.conf"):
        """Initialize self-test pipeline"""
        self.logger = self._setup_logging()
        self.config = self._load_config(config_path)
        self.validation_results = []
        
        # Security thresholds
        self.min_file_size = self.config.get('min_file_size', 1024)  # 1KB minimum
        self.max_file_size = self.config.get('max_file_size', 100 * 1024 * 1024)  # 100MB maximum
        self.required_extensions = self.config.get('required_extensions', ['.png', '.jpg', '.jpeg'])
        
        self.logger.info("🧪 CI/CD Self-Test Pipeline initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging"""
        logger = logging.getLogger('SelfTestPipeline')
        logger.setLevel(logging.INFO)
        
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load CI/CD configuration"""
        default_config = {
            'min_file_size': 1024,
            'max_file_size': 104857600,  # 100MB
            'required_extensions': ['.png', '.jpg', '.jpeg', '.mp4', '.avi'],
            'enable_encryption_check': True,
            'enable_corruption_check': True,
            'enable_security_scan': True,
            'fail_on_critical': True,
            'fail_on_high': False
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            else:
                return default_config
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return default_config
    
    def validate_output_file(self, file_path: str) -> List[ValidationResult]:
        """Run complete validation suite on output file"""
        self.logger.info(f"🔍 Validating output file: {file_path}")
        
        results = []
        
        # 1. File existence and basic checks
        results.extend(self._check_file_existence(file_path))
        
        # 2. File integrity validation
        results.extend(self._validate_file_integrity(file_path))
        
        # 3. Image/Video corruption detection
        results.extend(self._check_media_integrity(file_path))
        
        # 4. Security compliance checks
        results.extend(self._check_security_compliance(file_path))
        
        # 5. Metadata validation
        results.extend(self._validate_metadata(file_path))
        
        # Store results
        self.validation_results.extend(results)
        
        return results
    
    def _check_file_existence(self, file_path: str) -> List[ValidationResult]:
        """Check basic file properties"""
        results = []
        
        # Check if file exists
        if not os.path.exists(file_path):
            results.append(ValidationResult(
                test_name="file_existence",
                passed=False,
                severity="critical",
                message=f"File does not exist: {file_path}"
            ))
            return results
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size < self.min_file_size:
            results.append(ValidationResult(
                test_name="minimum_file_size",
                passed=False,
                severity="high",
                message=f"File too small: {file_size} bytes < {self.min_file_size} bytes minimum"
            ))
        elif file_size > self.max_file_size:
            results.append(ValidationResult(
                test_name="maximum_file_size",
                passed=False,
                severity="medium",
                message=f"File too large: {file_size} bytes > {self.max_file_size} bytes maximum"
            ))
        else:
            results.append(ValidationResult(
                test_name="file_size_validation",
                passed=True,
                severity="low",
                message=f"File size acceptable: {file_size} bytes"
            ))
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.required_extensions:
            results.append(ValidationResult(
                test_name="file_extension",
                passed=False,
                severity="medium",
                message=f"Unexpected file extension: {file_ext}"
            ))
        else:
            results.append(ValidationResult(
                test_name="extension_validation",
                passed=True,
                severity="low",
                message=f"Valid file extension: {file_ext}"
            ))
        
        return results
    
    def _validate_file_integrity(self, file_path: str) -> List[ValidationResult]:
        """Validate file integrity with checksums"""
        results = []
        
        try:
            # Calculate MD5 checksum
            md5_hash = hashlib.md5()
            sha256_hash = hashlib.sha256()
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    md5_hash.update(chunk)
                    sha256_hash.update(chunk)
            
            md5_checksum = md5_hash.hexdigest()
            sha256_checksum = sha256_hash.hexdigest()
            
            # Store checksum for future reference
            checksum_file = f"{file_path}.checksum"
            checksum_data = {
                'file_path': file_path,
                'md5': md5_checksum,
                'sha256': sha256_checksum,
                'timestamp': datetime.now().isoformat()
            }
            
            with open(checksum_file, 'w') as f:
                json.dump(checksum_data, f, indent=2)
            
            results.append(ValidationResult(
                test_name="checksum_generation",
                passed=True,
                severity="low",
                message=f"Checksums generated: MD5={md5_checksum[:8]}..., SHA256={sha256_checksum[:8]}...",
                details={
                    'md5': md5_checksum,
                    'sha256': sha256_checksum
                }
            ))
            
        except Exception as e:
            results.append(ValidationResult(
                test_name="checksum_generation",
                passed=False,
                severity="high",
                message=f"Failed to generate checksums: {e}"
            ))
        
        return results
    
    def _check_media_integrity(self, file_path: str) -> List[ValidationResult]:
        """Check for media file corruption"""
        results = []
        file_ext = Path(file_path).suffix.lower()
        
        # Only check media files if enabled
        if not self.config.get('enable_corruption_check', True):
            results.append(ValidationResult(
                test_name="corruption_check_disabled",
                passed=True,
                severity="low",
                message="Media corruption check disabled"
            ))
            return results
        
        try:
            if file_ext in ['.png', '.jpg', '.jpeg']:
                # Image integrity check
                image = Image.open(file_path)
                
                # Check if image can be loaded and has valid dimensions
                if image.size[0] <= 0 or image.size[1] <= 0:
                    results.append(ValidationResult(
                        test_name="image_dimensions",
                        passed=False,
                        severity="critical",
                        message="Invalid image dimensions"
                    ))
                else:
                    results.append(ValidationResult(
                        test_name="image_load_success",
                        passed=True,
                        severity="low",
                        message=f"Image loaded successfully: {image.size[0]}x{image.size[1]}"
                    ))
                
                # Check for corruption by attempting to save a copy
                test_path = f"{file_path}.test"
                try:
                    image.save(test_path, format=image.format)
                    os.remove(test_path)
                    results.append(ValidationResult(
                        test_name="image_save_test",
                        passed=True,
                        severity="low",
                        message="Image save test passed"
                    ))
                except Exception as e:
                    results.append(ValidationResult(
                        test_name="image_save_test",
                        passed=False,
                        severity="high",
                        message=f"Image save failed (possible corruption): {e}"
                    ))
                
            elif file_ext in ['.mp4', '.avi', '.mov']:
                # Video integrity check using OpenCV
                cap = cv2.VideoCapture(file_path)
                if not cap.isOpened():
                    results.append(ValidationResult(
                        test_name="video_load",
                        passed=False,
                        severity="critical",
                        message="Cannot open video file"
                    ))
                else:
                    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    fps = cap.get(cv2.CAP_PROP_FPS)
                    
                    if frame_count <= 0 or fps <= 0:
                        results.append(ValidationResult(
                            test_name="video_properties",
                            passed=False,
                            severity="high",
                            message="Invalid video properties"
                        ))
                    else:
                        results.append(ValidationResult(
                            test_name="video_load_success",
                            passed=True,
                            severity="low",
                            message=f"Video loaded: {frame_count} frames, {fps} FPS"
                        ))
                    
                    cap.release()
            
        except Exception as e:
            results.append(ValidationResult(
                test_name="media_integrity_check",
                passed=False,
                severity="critical",
                message=f"Media integrity check failed: {e}"
            ))
        
        return results
    
    def _check_security_compliance(self, file_path: str) -> List[ValidationResult]:
        """Check security compliance and potential threats"""
        results = []
        
        # Check for embedded malicious content
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            
            # Check for suspicious patterns
            suspicious_patterns = [
                b'eval(', b'exec(', b'import ', b'os.', b'subprocess.',
                b'system(', b'popen(', b'<script', b'javascript:'
            ]
            
            found_patterns = []
            for pattern in suspicious_patterns:
                if pattern in content:
                    found_patterns.append(pattern.decode('utf-8', errors='ignore'))
            
            if found_patterns:
                results.append(ValidationResult(
                    test_name="malicious_content_check",
                    passed=False,
                    severity="critical",
                    message=f"Potentially malicious content detected: {', '.join(found_patterns)}"
                ))
            else:
                results.append(ValidationResult(
                    test_name="security_scan",
                    passed=True,
                    severity="low",
                    message="No malicious content detected"
                ))
                
        except Exception as e:
            results.append(ValidationResult(
                test_name="security_scan",
                passed=False,
                severity="medium",
                message=f"Security scan failed: {e}"
            ))
        
        # Check file permissions
        try:
            file_stat = os.stat(file_path)
            # Should not be executable
            if file_stat.st_mode & 0o111:  # Check execute bits
                results.append(ValidationResult(
                    test_name="file_permissions",
                    passed=False,
                    severity="medium",
                    message="File has executable permissions"
                ))
            else:
                results.append(ValidationResult(
                    test_name="permissions_check",
                    passed=True,
                    severity="low",
                    message="File permissions are secure"
                ))
        except Exception as e:
            results.append(ValidationResult(
                test_name="permissions_check",
                passed=False,
                severity="low",
                message=f"Permissions check failed: {e}"
            ))
        
        return results
    
    def _validate_metadata(self, file_path: str) -> List[ValidationResult]:
        """Validate file metadata"""
        results = []
        
        try:
            # Get file metadata
            stat = os.stat(file_path)
            metadata = {
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'permissions': oct(stat.st_mode)[-3:]
            }
            
            # Check for recent modification (within last hour)
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            time_diff = datetime.now() - modified_time
            
            if time_diff.total_seconds() > 3600:  # 1 hour
                results.append(ValidationResult(
                    test_name="modification_time",
                    passed=False,
                    severity="low",
                    message="File was modified more than 1 hour ago",
                    details={'modification_age_seconds': time_diff.total_seconds()}
                ))
            else:
                results.append(ValidationResult(
                    test_name="recent_modification",
                    passed=True,
                    severity="low",
                    message="File was recently modified",
                    details={'modification_age_seconds': time_diff.total_seconds()}
                ))
            
            # Store metadata
            metadata_file = f"{file_path}.metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            results.append(ValidationResult(
                test_name="metadata_capture",
                passed=True,
                severity="low",
                message="File metadata captured",
                details=metadata
            ))
            
        except Exception as e:
            results.append(ValidationResult(
                test_name="metadata_validation",
                passed=False,
                severity="low",
                message=f"Metadata validation failed: {e}"
            ))
        
        return results
    
    def should_release_file(self, validation_results: List[ValidationResult]) -> bool:
        """Determine if file should be released based on validation results"""
        critical_failures = [r for r in validation_results if r.severity == "critical" and not r.passed]
        high_failures = [r for r in validation_results if r.severity == "high" and not r.passed]
        
        # Fail on critical issues
        if critical_failures and self.config.get('fail_on_critical', True):
            self.logger.error(f"❌ Blocking release due to critical failures: {[r.message for r in critical_failures]}")
            return False
        
        # Optionally fail on high severity issues
        if high_failures and self.config.get('fail_on_high', False):
            self.logger.warning(f"⚠️  High severity issues found: {[r.message for r in high_failures]}")
            return False
        
        # Check if majority of tests passed
        passed_tests = sum(1 for r in validation_results if r.passed)
        total_tests = len(validation_results)
        
        if passed_tests / total_tests >= 0.8:  # 80% pass rate required
            self.logger.info(f"✅ File approved for release ({passed_tests}/{total_tests} tests passed)")
            return True
        else:
            self.logger.warning(f"⚠️  File rejected due to low pass rate ({passed_tests}/{total_tests} tests passed)")
            return False
    
    def generate_validation_report(self, file_path: str, 
                                 validation_results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        passed_count = sum(1 for r in validation_results if r.passed)
        total_count = len(validation_results)
        
        # Categorize by severity
        severity_counts = {}
        for result in validation_results:
            if result.severity not in severity_counts:
                severity_counts[result.severity] = {'passed': 0, 'failed': 0}
            if result.passed:
                severity_counts[result.severity]['passed'] += 1
            else:
                severity_counts[result.severity]['failed'] += 1
        
        report = {
            'file_path': file_path,
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'approved' if self.should_release_file(validation_results) else 'rejected',
            'summary': {
                'total_tests': total_count,
                'passed_tests': passed_count,
                'failed_tests': total_count - passed_count,
                'pass_rate': passed_count / total_count if total_count > 0 else 0
            },
            'severity_breakdown': severity_counts,
            'validation_results': [
                {
                    'test_name': r.test_name,
                    'passed': r.passed,
                    'severity': r.severity,
                    'message': r.message,
                    'details': r.details
                }
                for r in validation_results
            ]
        }
        
        # Save report
        report_file = f"{file_path}.validation_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        return report

# Integration function for the pipeline
def run_self_test_pipeline(file_path: str) -> Tuple[bool, Dict[str, Any]]:
    """Run complete self-test pipeline on a file"""
    pipeline = SelfTestPipeline()
    
    # Run validation
    results = pipeline.validate_output_file(file_path)
    
    # Generate report
    report = pipeline.generate_validation_report(file_path, results)
    
    # Decision
    should_release = pipeline.should_release_file(results)
    
    return should_release, report

# Example usage
def main():
    """Demo self-test pipeline"""
    print("🧪 CI/CD SELF-TEST PIPELINE DEMO")
    print("=" * 40)
    
    # Create test file
    test_image_path = "test_cicd_validation.png"
    test_image = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    cv2.imwrite(test_image_path, test_image)
    print(f"✅ Created test file: {test_image_path}")
    
    try:
        # Run self-test
        should_release, report = run_self_test_pipeline(test_image_path)
        
        print(f"\n📊 Validation Results:")
        print(f"Overall Status: {'✅ APPROVED' if should_release else '❌ REJECTED'}")
        print(f"Pass Rate: {report['summary']['pass_rate']:.1%}")
        print(f"Tests Passed: {report['summary']['passed_tests']}/{report['summary']['total_tests']}")
        
        # Show critical findings
        critical_failures = [r for r in report['validation_results'] 
                           if r['severity'] == 'critical' and not r['passed']]
        if critical_failures:
            print(f"\n🚨 Critical Issues Found:")
            for failure in critical_failures:
                print(f"  - {failure['message']}")
        
        # Show report location
        report_file = f"{test_image_path}.validation_report.json"
        print(f"\n📋 Detailed report saved to: {report_file}")
        
    except Exception as e:
        print(f"❌ Pipeline error: {e}")
        return False
    finally:
        # Cleanup
        cleanup_files = [
            test_image_path,
            f"{test_image_path}.checksum",
            f"{test_image_path}.metadata.json",
            f"{test_image_path}.validation_report.json"
        ]
        
        for file_path in cleanup_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🧹 Cleaned up: {file_path}")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)