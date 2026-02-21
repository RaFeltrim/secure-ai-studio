"""
Secure File Storage Utilities for secure-ai-studio
Implements the Level 3 security measures from the security plan:
- Pre-signed URLs for secure file transfer
- Automatic deletion policies
- Validation of file formats
"""

import os
import boto3
from datetime import datetime, timedelta
from typing import Optional, Tuple
from urllib.parse import urlparse
import mimetypes
from botocore.exceptions import ClientError
import secrets
import string


class SecureStorageManager:
    """
    Handles secure file uploads and management according to the security plan.
    Uses pre-signed URLs and automatic deletion policies to protect sensitive data.
    """
    
    def __init__(self):
        # Configuration from environment variables
        self.aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
        self.aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.s3_bucket_name = os.getenv('S3_BUCKET_NAME', 'secure-ai-studio-temp')
        self.region_name = os.getenv('AWS_REGION', 'us-east-1')
        
        # Initialize S3 client if credentials are available
        if self.aws_access_key_id and self.aws_secret_access_key:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
                region_name=self.region_name
            )
        else:
            # For demo purposes, we'll simulate the functionality
            self.s3_client = None
    
    def _generate_secure_filename(self, original_filename: str) -> str:
        """
        Generate a secure filename with random component to prevent enumeration.
        
        Args:
            original_filename: Original filename from user
            
        Returns:
            Secure filename with timestamp and random component
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        
        name, ext = os.path.splitext(original_filename)
        return f"{timestamp}_{random_suffix}{ext}"
    
    def _validate_file_type(self, filename: str) -> bool:
        """
        Validate that the file type is allowed for upload.
        
        Args:
            filename: Name of the file to validate
            
        Returns:
            True if file type is allowed, False otherwise
        """
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp', '.mp4', '.mov', '.avi'}
        _, ext = os.path.splitext(filename.lower())
        
        return ext in allowed_extensions
    
    def _validate_file_size(self, file_path: str, max_size_mb: int = 50) -> bool:
        """
        Validate that the file size is within acceptable limits.
        
        Args:
            file_path: Path to the file to validate
            max_size_mb: Maximum allowed file size in MB
            
        Returns:
            True if file size is acceptable, False otherwise
        """
        if not os.path.exists(file_path):
            return False
            
        file_size_bytes = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        
        return file_size_bytes <= max_size_bytes
    
    def upload_and_get_presigned_url(self, file_path: str, expiration_minutes: int = 30) -> Optional[str]:
        """
        Upload a file to secure storage and return a pre-signed URL.
        
        Args:
            file_path: Local path to the file to upload
            expiration_minutes: Number of minutes before the URL expires
            
        Returns:
            Pre-signed URL or None if upload failed
        """
        if not os.path.exists(file_path):
            print(f"[ERROR] File does not exist: {file_path}")
            return None
        
        # Validate file type and size
        filename = os.path.basename(file_path)
        if not self._validate_file_type(filename):
            print(f"[ERROR] Invalid file type: {filename}")
            return None
        
        if not self._validate_file_size(file_path):
            print(f"[ERROR] File too large: {filename}")
            return None
        
        # Generate secure filename
        secure_filename = self._generate_secure_filename(filename)
        
        if self.s3_client:
            # Upload to S3 in a real implementation
            try:
                self.s3_client.upload_file(
                    file_path, 
                    self.s3_bucket_name, 
                    secure_filename,
                    ExtraArgs={'ServerSideEncryption': 'AES256'}  # Enable encryption
                )
                
                # Generate pre-signed URL
                presigned_url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.s3_bucket_name, 'Key': secure_filename},
                    ExpiresIn=expiration_minutes * 60
                )
                
                # Schedule deletion after processing (in a real system, you'd use S3 lifecycle rules)
                print(f"[INFO] File uploaded securely as {secure_filename}. URL expires in {expiration_minutes} minutes.")
                return presigned_url
            except ClientError as e:
                print(f"[ERROR] Failed to upload file to S3: {str(e)}")
                return None
        else:
            # For demo purposes, simulate the process
            print(f"[DEMO] Would upload {file_path} securely as {secure_filename}")
            print(f"[DEMO] Would generate pre-signed URL with {expiration_minutes} minute expiry")
            # Return a simulated URL for demonstration
            return f"https://demo-storage.com/files/{secure_filename}?expires={expiration_minutes}min"
    
    def cleanup_expired_files(self, days_old: int = 1) -> int:
        """
        Clean up files older than specified days (simulate automatic lifecycle policy).
        
        Args:
            days_old: Files older than this many days will be deleted
            
        Returns:
            Number of files deleted
        """
        if not self.s3_client:
            print("[DEMO] Would clean up files older than {days_old} day(s)")
            return 0
        
        try:
            # List objects in the bucket
            response = self.s3_client.list_objects_v2(Bucket=self.s3_bucket_name)
            
            if 'Contents' not in response:
                return 0
            
            cutoff_date = datetime.now() - timedelta(days=days_old)
            deleted_count = 0
            
            for obj in response['Contents']:
                if obj['LastModified'] < cutoff_date:
                    self.s3_client.delete_object(Bucket=self.s3_bucket_name, Key=obj['Key'])
                    deleted_count += 1
                    
            print(f"[INFO] Cleaned up {deleted_count} expired files")
            return deleted_count
        except ClientError as e:
            print(f"[ERROR] Failed to clean up expired files: {str(e)}")
            return 0


def validate_provider_security(provider_name: str) -> dict:
    """
    Validate the security level of an AI provider based on the security plan.
    
    Args:
        provider_name: Name of the AI provider to validate
        
    Returns:
        Dictionary with security assessment
    """
    security_levels = {
        'google_vertex': {
            'level': 'Alto',
            'risk': '🟢',
            'recommendation': 'Recomendado',
            'justification': 'Permite Residência de Dados no Brasil (southamerica-east1). Oferece Zero Data Retention (ZDR) configurável.'
        },
        'adobe_firefly': {
            'level': 'Alto',
            'risk': '🟢',
            'recommendation': 'IP Seguro',
            'justification': 'Modelos treinados apenas em conteúdo licenciado/domínio público. Oferece Indenização de Propriedade Intelectual explícita.'
        },
        'openai': {
            'level': 'Médio',
            'risk': '🟡',
            'recommendation': 'Cuidado',
            'justification': 'Oferece Copyright Shield, mas não possui servidores no Brasil (apenas EUA/Europa).'
        },
        'luma': {
            'level': 'Moderado',
            'risk': '🟠',
            'recommendation': 'Risco Moderado',
            'justification': 'Infraestrutura global (AWS), mas sem garantia de residência de dados no Brasil.'
        },
        'kling': {
            'level': 'Crítico',
            'risk': '🔴',
            'recommendation': 'Evitar',
            'justification': 'Processamento na Ásia com ausência de clareza sobre conformidade LGPD.'
        }
    }
    
    provider_lower = provider_name.lower().replace(' ', '_')
    if provider_lower in security_levels:
        return security_levels[provider_lower]
    else:
        return {
            'level': 'Desconhecido',
            'risk': '❓',
            'recommendation': 'Verificar',
            'justification': 'Nível de segurança não documentado para este provedor.'
        }


def get_security_recommendation(is_sensitive_data: bool = False) -> str:
    """
    Get security recommendation based on data sensitivity.
    
    Args:
        is_sensitive_data: Whether the data being processed is sensitive
        
    Returns:
        Security recommendation string
    """
    if is_sensitive_data:
        return ("Para dados sensíveis, considere usar o Modo Local com modelos open-source "
                "como Flux (imagens) ou Wan2.2/LTX-Video (vídeos) hospedados em sua própria infraestrutura.")
    else:
        return ("Para dados menos sensíveis, provedores como Google Vertex AI com residência de dados no Brasil "
                "ou Adobe Firefly são opções seguras com boa qualidade de saída.")