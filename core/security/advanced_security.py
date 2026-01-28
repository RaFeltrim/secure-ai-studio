#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Advanced Security Layer
Professional security implementation with OpenCV watermarking and AES-256 encryption

Features:
- Advanced OpenCV-based watermarking
- AES-256 file encryption
- Metadata embedding
- Digital signature verification
- File integrity checking
"""

import os
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import hashlib
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import secrets

@dataclass
class WatermarkConfig:
    """Watermark configuration settings"""
    opacity: float = 0.7
    position: str = "bottom_right"  # top_left, top_right, bottom_left, bottom_right, center
    scale_factor: float = 0.15  # Relative to image size
    rotation_angle: int = 0
    blend_mode: str = "overlay"  # overlay, multiply, screen

@dataclass
class EncryptionConfig:
    """Encryption configuration settings"""
    algorithm: str = "AES-256-GCM"
    key_derivation_iterations: int = 100000
    salt_length: int = 16

class AdvancedWatermarkEngine:
    """
    Professional OpenCV-based watermarking engine
    """
    
    def __init__(self, config: Optional[WatermarkConfig] = None):
        """Initialize watermark engine"""
        self.config = config or WatermarkConfig()
        self.logger = logging.getLogger('WatermarkEngine')
        
        # Pre-load watermark templates
        self.watermark_templates = self._load_watermark_templates()
        
    def _load_watermark_templates(self) -> Dict[str, np.ndarray]:
        """Load watermark templates"""
        templates = {}
        
        # Create default text watermark
        templates['default'] = self._create_text_watermark(
            "CONFIDENTIAL - SECURE AI STUDIO", 
            (255, 255, 255), 
            32
        )
        
        # Create logo-style watermark
        templates['logo'] = self._create_logo_watermark()
        
        # Create pattern watermark
        templates['pattern'] = self._create_pattern_watermark()
        
        return templates
    
    def _create_text_watermark(self, text: str, color: Tuple[int, int, int], 
                             font_size: int) -> np.ndarray:
        """Create text-based watermark using OpenCV"""
        # Create image for text
        img = np.zeros((100, 800, 3), dtype=np.uint8)
        
        # Use OpenCV.putText for text rendering
        font = cv2.FONT_HERSHEY_SIMPLEX
        thickness = 2
        
        # Get text size
        (text_width, text_height), baseline = cv2.getTextSize(
            text, font, font_size/20, thickness
        )
        
        # Center text
        x = (img.shape[1] - text_width) // 2
        y = (img.shape[0] + text_height) // 2
        
        # Draw text
        cv2.putText(img, text, (x, y), font, font_size/20, color, thickness)
        
        return img
    
    def _create_logo_watermark(self) -> np.ndarray:
        """Create logo-style watermark"""
        # Create circular logo watermark
        size = 200
        img = np.zeros((size, size, 3), dtype=np.uint8)
        
        # Draw circle
        center = (size//2, size//2)
        radius = size//3
        cv2.circle(img, center, radius, (255, 255, 255), -1)
        
        # Draw inner circle
        cv2.circle(img, center, radius//2, (0, 0, 0), -1)
        
        # Add text
        cv2.putText(img, "AI", center, cv2.FONT_HERSHEY_SIMPLEX, 
                   1, (255, 255, 255), 2, cv2.LINE_AA)
        
        return img
    
    def _create_pattern_watermark(self) -> np.ndarray:
        """Create pattern-based watermark"""
        size = 300
        img = np.zeros((size, size, 3), dtype=np.uint8)
        
        # Create diagonal pattern
        for i in range(0, size, 20):
            cv2.line(img, (0, i), (i, 0), (128, 128, 128), 1)
            cv2.line(img, (i, size), (size, i), (128, 128, 128), 1)
        
        return img
    
    def apply_watermark(self, image_path: str, output_path: str = None,
                       watermark_type: str = "default",
                       config: Optional[WatermarkConfig] = None) -> str:
        """Apply watermark to image"""
        config = config or self.config
        
        try:
            # Load image using OpenCV
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Get watermark template
            if watermark_type not in self.watermark_templates:
                watermark_type = "default"
            
            watermark = self.watermark_templates[watermark_type].copy()
            
            # Resize watermark based on image size
            img_height, img_width = img.shape[:2]
            wm_height, wm_width = watermark.shape[:2]
            
            # Calculate new watermark size
            scale = min(
                img_width * config.scale_factor / wm_width,
                img_height * config.scale_factor / wm_height
            )
            
            new_wm_width = int(wm_width * scale)
            new_wm_height = int(wm_height * scale)
            
            # Resize watermark
            watermark_resized = cv2.resize(
                watermark, (new_wm_width, new_wm_height),
                interpolation=cv2.INTER_AREA
            )
            
            # Apply transparency
            watermark_alpha = np.ones((new_wm_height, new_wm_width, 1)) * config.opacity
            watermark_bgr = watermark_resized[:, :, :3]
            
            # Position watermark
            x, y = self._calculate_position(
                img_width, img_height, new_wm_width, new_wm_height, config.position
            )
            
            # Apply watermark using blending
            result = self._blend_watermark(
                img, watermark_bgr, watermark_alpha, x, y, config.blend_mode
            )
            
            # Rotate if needed
            if config.rotation_angle != 0:
                result = self._rotate_image(result, config.rotation_angle)
            
            # Save result
            if output_path is None:
                path_obj = Path(image_path)
                output_path = str(path_obj.parent / f"watermarked_{path_obj.name}")
            
            cv2.imwrite(output_path, result)
            
            self.logger.info(f"✅ Watermark applied to {image_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ Watermark application failed: {e}")
            raise
    
    def _calculate_position(self, img_width: int, img_height: int,
                          wm_width: int, wm_height: int, position: str) -> Tuple[int, int]:
        """Calculate watermark position"""
        positions = {
            "top_left": (20, 20),
            "top_right": (img_width - wm_width - 20, 20),
            "bottom_left": (20, img_height - wm_height - 20),
            "bottom_right": (img_width - wm_width - 20, img_height - wm_height - 20),
            "center": ((img_width - wm_width) // 2, (img_height - wm_height) // 2)
        }
        
        return positions.get(position, positions["bottom_right"])
    
    def _blend_watermark(self, img: np.ndarray, watermark: np.ndarray,
                        alpha: np.ndarray, x: int, y: int, blend_mode: str) -> np.ndarray:
        """Blend watermark with image using specified mode"""
        img_copy = img.copy()
        wm_height, wm_width = watermark.shape[:2]
        
        # Extract region of interest
        roi = img_copy[y:y+wm_height, x:x+wm_width]
        
        if blend_mode == "overlay":
            # Alpha blending
            blended = (alpha * watermark + (1 - alpha) * roi).astype(np.uint8)
        elif blend_mode == "multiply":
            # Multiply blending
            blended = ((watermark.astype(np.float32) * roi.astype(np.float32)) / 255).astype(np.uint8)
        elif blend_mode == "screen":
            # Screen blending
            blended = (255 - ((255 - watermark.astype(np.float32)) * 
                             (255 - roi.astype(np.float32)) / 255)).astype(np.uint8)
        else:
            # Default overlay
            blended = (alpha * watermark + (1 - alpha) * roi).astype(np.uint8)
        
        # Place blended watermark back
        img_copy[y:y+wm_height, x:x+wm_width] = blended
        
        return img_copy
    
    def _rotate_image(self, img: np.ndarray, angle: int) -> np.ndarray:
        """Rotate image by specified angle"""
        center = tuple(np.array(img.shape[1::-1]) / 2)
        rot_mat = cv2.getRotationMatrix2D(center, angle, 1.0)
        return cv2.warpAffine(img, rot_mat, img.shape[1::-1], flags=cv2.INTER_LINEAR)

class AES256FileEncryptor:
    """
    AES-256 file encryption system
    """
    
    def __init__(self, config: Optional[EncryptionConfig] = None):
        """Initialize encryptor"""
        self.config = config or EncryptionConfig()
        self.logger = logging.getLogger('FileEncryptor')
    
    def encrypt_file(self, file_path: str, password: str, output_path: str = None) -> str:
        """Encrypt file using AES-256-GCM"""
        try:
            # Read file content
            with open(file_path, 'rb') as f:
                data = f.read()
            
            # Generate salt and derive key
            salt = secrets.token_bytes(self.config.salt_length)
            key = self._derive_key(password, salt)
            
            # Generate nonce
            nonce = secrets.token_bytes(12)  # GCM standard nonce size
            
            # Encrypt data
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce))
            encryptor = cipher.encryptor()
            ciphertext = encryptor.update(data) + encryptor.finalize()
            
            # Get authentication tag
            tag = encryptor.tag
            
            # Create encrypted file structure
            encrypted_data = {
                'salt': salt.hex(),
                'nonce': nonce.hex(),
                'tag': tag.hex(),
                'ciphertext': ciphertext.hex(),
                'original_filename': Path(file_path).name,
                'encryption_date': datetime.now().isoformat()
            }
            
            # Save encrypted file
            if output_path is None:
                path_obj = Path(file_path)
                output_path = str(path_obj.parent / f"{path_obj.stem}.encrypted")
            
            with open(output_path, 'w') as f:
                json.dump(encrypted_data, f, indent=2)
            
            self.logger.info(f"✅ File encrypted: {file_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ File encryption failed: {e}")
            raise
    
    def decrypt_file(self, encrypted_path: str, password: str, output_path: str = None) -> str:
        """Decrypt AES-256-GCM encrypted file"""
        try:
            # Read encrypted data
            with open(encrypted_path, 'r') as f:
                encrypted_data = json.load(f)
            
            # Extract components
            salt = bytes.fromhex(encrypted_data['salt'])
            nonce = bytes.fromhex(encrypted_data['nonce'])
            tag = bytes.fromhex(encrypted_data['tag'])
            ciphertext = bytes.fromhex(encrypted_data['ciphertext'])
            
            # Derive key
            key = self._derive_key(password, salt)
            
            # Decrypt data
            cipher = Cipher(algorithms.AES(key), modes.GCM(nonce, tag))
            decryptor = cipher.decryptor()
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            # Save decrypted file
            if output_path is None:
                original_name = encrypted_data['original_filename']
                path_obj = Path(encrypted_path)
                output_path = str(path_obj.parent / f"decrypted_{original_name}")
            
            with open(output_path, 'wb') as f:
                f.write(plaintext)
            
            self.logger.info(f"✅ File decrypted: {encrypted_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"❌ File decryption failed: {e}")
            raise
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password"""
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=salt,
            iterations=self.config.key_derivation_iterations,
        )
        return kdf.derive(password.encode())

class DigitalSignatureManager:
    """
    Digital signature management for file integrity
    """
    
    def __init__(self):
        """Initialize signature manager"""
        self.logger = logging.getLogger('SignatureManager')
        self.private_key = None
        self.public_key = None
    
    def generate_key_pair(self) -> Tuple[bytes, bytes]:
        """Generate RSA key pair for signing"""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Get public key
            public_key = private_key.public_key()
            
            # Serialize keys
            private_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_pem = public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            
            self.private_key = private_key
            self.public_key = public_key
            
            self.logger.info("✅ RSA key pair generated")
            return private_pem, public_pem
            
        except Exception as e:
            self.logger.error(f"❌ Key generation failed: {e}")
            raise
    
    def sign_file(self, file_path: str, private_key_pem: bytes = None) -> str:
        """Create digital signature for file"""
        try:
            # Load private key if provided
            if private_key_pem:
                private_key = serialization.load_pem_private_key(
                    private_key_pem, password=None
                )
            else:
                private_key = self.private_key
            
            if not private_key:
                raise ValueError("No private key available for signing")
            
            # Read file and calculate hash
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            file_hash = hashlib.sha256(file_data).digest()
            
            # Create signature
            signature = private_key.sign(
                file_hash,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            # Save signature
            path_obj = Path(file_path)
            signature_path = str(path_obj.parent / f"{path_obj.stem}.sig")
            
            signature_data = {
                'signature': signature.hex(),
                'algorithm': 'SHA256-RSA-PSS',
                'timestamp': datetime.now().isoformat(),
                'filename': path_obj.name
            }
            
            with open(signature_path, 'w') as f:
                json.dump(signature_data, f, indent=2)
            
            self.logger.info(f"✅ File signed: {file_path}")
            return signature_path
            
        except Exception as e:
            self.logger.error(f"❌ File signing failed: {e}")
            raise
    
    def verify_signature(self, file_path: str, signature_path: str, 
                        public_key_pem: bytes = None) -> bool:
        """Verify digital signature"""
        try:
            # Load public key if provided
            if public_key_pem:
                public_key = serialization.load_pem_public_key(public_key_pem)
            else:
                public_key = self.public_key
            
            if not public_key:
                raise ValueError("No public key available for verification")
            
            # Read file and calculate hash
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            file_hash = hashlib.sha256(file_data).digest()
            
            # Read signature
            with open(signature_path, 'r') as f:
                signature_data = json.load(f)
            
            signature = bytes.fromhex(signature_data['signature'])
            
            # Verify signature
            try:
                public_key.verify(
                    signature,
                    file_hash,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
                self.logger.info(f"✅ Signature verified for {file_path}")
                return True
            except Exception:
                self.logger.warning(f"❌ Signature verification failed for {file_path}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Signature verification error: {e}")
            return False

class SecurityOrchestrator:
    """
    Main security orchestrator combining all security features
    """
    
    def __init__(self):
        """Initialize security orchestrator"""
        self.logger = logging.getLogger('SecurityOrchestrator')
        self.watermark_engine = AdvancedWatermarkEngine()
        self.encryptor = AES256FileEncryptor()
        self.signature_manager = DigitalSignatureManager()
        
        self.logger.info("🛡️ Security Orchestrator initialized")
    
    def secure_content_generation(self, image_path: str, 
                                security_options: Dict[str, Any] = None) -> Dict[str, str]:
        """Apply complete security suite to generated content"""
        security_options = security_options or {}
        result_paths = {}
        
        try:
            # Step 1: Apply watermark
            if security_options.get('apply_watermark', True):
                watermarked_path = self.watermark_engine.apply_watermark(
                    image_path,
                    watermark_type=security_options.get('watermark_type', 'default')
                )
                result_paths['watermarked'] = watermarked_path
                current_path = watermarked_path
            else:
                current_path = image_path
            
            # Step 2: Encrypt file
            if security_options.get('encrypt_file', False):
                password = security_options.get('encryption_password')
                if not password:
                    raise ValueError("Encryption password required")
                
                encrypted_path = self.encryptor.encrypt_file(current_path, password)
                result_paths['encrypted'] = encrypted_path
            
            # Step 3: Create digital signature
            if security_options.get('sign_file', True):
                signature_path = self.signature_manager.sign_file(current_path)
                result_paths['signature'] = signature_path
            
            self.logger.info(f"✅ Security processing completed for {image_path}")
            return result_paths
            
        except Exception as e:
            self.logger.error(f"❌ Security processing failed: {e}")
            raise

# Example usage
def main():
    """Demo security layer functionality"""
    print("🛡️ ADVANCED SECURITY LAYER DEMO")
    print("=" * 40)
    
    # Initialize security components
    orchestrator = SecurityOrchestrator()
    
    # Generate test image
    test_image_path = "test_security_image.png"
    img = np.random.randint(0, 255, (512, 512, 3), dtype=np.uint8)
    cv2.imwrite(test_image_path, img)
    print(f"✅ Created test image: {test_image_path}")
    
    try:
        # Apply security processing
        security_options = {
            'apply_watermark': True,
            'watermark_type': 'default',
            'encrypt_file': True,
            'encryption_password': 'secure_password_123',
            'sign_file': True
        }
        
        result = orchestrator.secure_content_generation(test_image_path, security_options)
        
        print(f"🔐 Security processing results:")
        for key, path in result.items():
            print(f"  {key}: {path}")
        
        # Verify signature
        if 'signature' in result:
            is_valid = orchestrator.signature_manager.verify_signature(
                result.get('watermarked', test_image_path),
                result['signature']
            )
            print(f"✅ Signature valid: {is_valid}")
        
        # Test decryption
        if 'encrypted' in result:
            decrypted_path = orchestrator.encryptor.decrypt_file(
                result['encrypted'], 
                'secure_password_123'
            )
            print(f"🔓 Decrypted file: {decrypted_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Cleanup test files
        test_files = [
            test_image_path,
            "watermarked_test_security_image.png",
            "test_security_image.encrypted",
            "test_security_image.sig",
            "decrypted_test_security_image.png"
        ]
        
        for file_path in test_files:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"🧹 Cleaned up: {file_path}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)