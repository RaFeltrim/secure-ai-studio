#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ SECURE AI STUDIO - Immutable Audit Log System
Cryptographically signed audit trail for all content generations

Features:
- Immutable log entries with cryptographic hashing
- Digital signatures for tamper detection
- Blockchain-like chain validation
- Comprehensive activity tracking
- Compliance-ready audit reports
"""

import os
import json
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, PublicFormat
import sqlite3

@dataclass
class AuditEntry:
    """Immutable audit log entry"""
    timestamp: str
    event_type: str
    user_id: str
    session_id: str
    content_id: str
    action_details: Dict[str, Any]
    system_state: Dict[str, Any]
    previous_hash: str
    entry_hash: str = ""
    signature: str = ""

class ImmutableAuditLog:
    """
    Immutable audit log with cryptographic integrity
    """
    
    def __init__(self, log_directory: str = "logs/audit", db_name: str = "audit_log.db"):
        """Initialize audit log system"""
        self.log_directory = Path(log_directory)
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.log_directory / db_name
        self.logger = self._setup_logging()
        
        # Initialize database
        self._initialize_database()
        
        # Generate signing keys
        self._setup_signing_keys()
        
        # Get genesis hash
        self.genesis_hash = self._get_genesis_hash()
        
        self.logger.info("📜 Immutable Audit Log initialized")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup audit logging"""
        logger = logging.getLogger('AuditLog')
        logger.setLevel(logging.INFO)
        
        handler = logging.FileHandler(self.log_directory / "audit_system.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _initialize_database(self):
        """Initialize SQLite database for audit entries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create audit log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                user_id TEXT NOT NULL,
                session_id TEXT NOT NULL,
                content_id TEXT NOT NULL,
                action_details TEXT NOT NULL,
                system_state TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                entry_hash TEXT NOT NULL,
                signature TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_audit_timestamp 
            ON audit_entries(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_audit_user 
            ON audit_entries(user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_audit_content 
            ON audit_entries(content_id)
        ''')
        
        conn.commit()
        conn.close()
    
    def _setup_signing_keys(self):
        """Setup RSA key pair for signing audit entries"""
        keys_dir = self.log_directory / "keys"
        keys_dir.mkdir(exist_ok=True)
        
        private_key_path = keys_dir / "audit_private_key.pem"
        public_key_path = keys_dir / "audit_public_key.pem"
        
        # Generate keys if they don't exist
        if not private_key_path.exists():
            self.logger.info("🔑 Generating audit signing keys...")
            
            # Generate RSA key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            public_key = private_key.public_key()
            
            # Save private key
            with open(private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=Encoding.PEM,
                    format=PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Save public key
            with open(public_key_path, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=Encoding.PEM,
                    format=PublicFormat.SubjectPublicKeyInfo
                ))
            
            self.logger.info("✅ Audit signing keys generated and stored")
        
        # Load keys
        with open(private_key_path, 'rb') as f:
            self.private_key = serialization.load_pem_private_key(
                f.read(), password=None
            )
        
        with open(public_key_path, 'rb') as f:
            self.public_key = serialization.load_pem_public_key(f.read())
    
    def _get_genesis_hash(self) -> str:
        """Get or create genesis hash for blockchain"""
        genesis_file = self.log_directory / "genesis.hash"
        
        if genesis_file.exists():
            with open(genesis_file, 'r') as f:
                return f.read().strip()
        else:
            # Create genesis entry
            genesis_data = {
                'timestamp': datetime.now().isoformat(),
                'event_type': 'GENESIS',
                'system_version': '1.0.0',
                'initialization_parameters': {}
            }
            
            genesis_hash = self._calculate_hash(genesis_data)
            
            with open(genesis_file, 'w') as f:
                f.write(genesis_hash)
            
            self.logger.info(f"🔗 Genesis hash created: {genesis_hash}")
            return genesis_hash
    
    def log_event(self, event_type: str, user_id: str, session_id: str,
                  content_id: str, action_details: Dict[str, Any],
                  system_state: Dict[str, Any] = None) -> str:
        """Log an audit event with cryptographic integrity"""
        try:
            # Get previous entry hash
            previous_hash = self._get_latest_hash()
            
            # Create audit entry
            entry = AuditEntry(
                timestamp=datetime.now().isoformat(),
                event_type=event_type,
                user_id=user_id,
                session_id=session_id,
                content_id=content_id,
                action_details=action_details,
                system_state=system_state or {},
                previous_hash=previous_hash
            )
            
            # Calculate entry hash
            entry_dict = asdict(entry)
            entry_dict.pop('entry_hash')  # Remove hash field for calculation
            entry_dict.pop('signature')   # Remove signature field for calculation
            
            entry.entry_hash = self._calculate_hash(entry_dict)
            
            # Create digital signature
            entry.signature = self._sign_entry(entry_dict)
            
            # Store in database
            self._store_entry(entry)
            
            # Write to file log
            self._write_file_log(entry)
            
            self.logger.info(f"✅ Audit entry logged: {event_type} for {content_id}")
            return entry.entry_hash
            
        except Exception as e:
            self.logger.error(f"❌ Failed to log audit entry: {e}")
            raise
    
    def _get_latest_hash(self) -> str:
        """Get hash of the latest audit entry"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT entry_hash FROM audit_entries 
            ORDER BY id DESC LIMIT 1
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else self.genesis_hash
    
    def _calculate_hash(self, data: Any) -> str:
        """Calculate SHA-256 hash of data"""
        data_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _sign_entry(self, entry_dict: Dict) -> str:
        """Create digital signature for entry"""
        entry_str = json.dumps(entry_dict, sort_keys=True, default=str)
        entry_bytes = entry_str.encode()
        
        signature = self.private_key.sign(
            entry_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        
        return signature.hex()
    
    def _store_entry(self, entry: AuditEntry):
        """Store entry in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO audit_entries 
            (timestamp, event_type, user_id, session_id, content_id, 
             action_details, system_state, previous_hash, entry_hash, signature)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            entry.timestamp,
            entry.event_type,
            entry.user_id,
            entry.session_id,
            entry.content_id,
            json.dumps(entry.action_details),
            json.dumps(entry.system_state),
            entry.previous_hash,
            entry.entry_hash,
            entry.signature
        ))
        
        conn.commit()
        conn.close()
    
    def _write_file_log(self, entry: AuditEntry):
        """Write entry to file log"""
        log_file = self.log_directory / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        
        entry_dict = asdict(entry)
        log_entry = {
            'log_timestamp': datetime.now().isoformat(),
            'entry': entry_dict
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry, default=str) + '\n')
    
    def verify_chain_integrity(self) -> Dict[str, Any]:
        """Verify the integrity of the entire audit chain"""
        self.logger.info("🔍 Verifying audit chain integrity...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all entries ordered by ID
        cursor.execute('''
            SELECT id, timestamp, event_type, user_id, content_id, 
                   action_details, system_state, previous_hash, entry_hash, signature
            FROM audit_entries 
            ORDER BY id ASC
        ''')
        
        entries = cursor.fetchall()
        conn.close()
        
        # Start with genesis hash
        expected_previous_hash = self.genesis_hash
        invalid_entries = []
        valid_entries = 0
        
        for entry in entries:
            (entry_id, timestamp, event_type, user_id, content_id,
             action_details, system_state, previous_hash, entry_hash, signature) = entry
            
            # Check previous hash linkage
            if previous_hash != expected_previous_hash:
                invalid_entries.append({
                    'id': entry_id,
                    'issue': 'Hash chain broken',
                    'expected_previous': expected_previous_hash,
                    'actual_previous': previous_hash
                })
            
            # Verify entry hash
            entry_data = {
                'timestamp': timestamp,
                'event_type': event_type,
                'user_id': user_id,
                'session_id': '',  # Not retrieved in this query
                'content_id': content_id,
                'action_details': json.loads(action_details),
                'system_state': json.loads(system_state),
                'previous_hash': previous_hash
            }
            
            calculated_hash = self._calculate_hash(entry_data)
            if calculated_hash != entry_hash:
                invalid_entries.append({
                    'id': entry_id,
                    'issue': 'Entry hash mismatch',
                    'calculated': calculated_hash,
                    'stored': entry_hash
                })
            
            # Verify digital signature
            try:
                entry_bytes = json.dumps(entry_data, sort_keys=True, default=str).encode()
                signature_bytes = bytes.fromhex(signature)
                
                self.public_key.verify(
                    signature_bytes,
                    entry_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH
                    ),
                    hashes.SHA256()
                )
            except Exception:
                invalid_entries.append({
                    'id': entry_id,
                    'issue': 'Signature verification failed'
                })
            
            if not any(ie['id'] == entry_id for ie in invalid_entries):
                valid_entries += 1
            
            expected_previous_hash = entry_hash
        
        result = {
            'total_entries': len(entries),
            'valid_entries': valid_entries,
            'invalid_entries': len(invalid_entries),
            'integrity_status': 'VALID' if len(invalid_entries) == 0 else 'COMPROMISED',
            'invalid_details': invalid_entries,
            'verification_timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"✅ Chain verification completed: {result['integrity_status']}")
        return result
    
    def get_audit_trail(self, content_id: str = None, user_id: str = None,
                       start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Retrieve audit trail with optional filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query with filters
        query = '''
            SELECT timestamp, event_type, user_id, session_id, content_id,
                   action_details, system_state, previous_hash, entry_hash
            FROM audit_entries WHERE 1=1
        '''
        
        params = []
        
        if content_id:
            query += ' AND content_id = ?'
            params.append(content_id)
        
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)
        
        query += ' ORDER BY timestamp ASC'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Convert to dictionary format
        trail = []
        for row in results:
            trail.append({
                'timestamp': row[0],
                'event_type': row[1],
                'user_id': row[2],
                'session_id': row[3],
                'content_id': row[4],
                'action_details': json.loads(row[5]),
                'system_state': json.loads(row[6]),
                'previous_hash': row[7],
                'entry_hash': row[8]
            })
        
        return trail
    
    def generate_compliance_report(self, period_days: int = 30) -> Dict[str, Any]:
        """Generate compliance report for specified period"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get statistics
        cursor.execute('''
            SELECT 
                COUNT(*) as total_events,
                COUNT(DISTINCT user_id) as unique_users,
                COUNT(DISTINCT content_id) as unique_content,
                MIN(timestamp) as first_event,
                MAX(timestamp) as last_event
            FROM audit_entries 
            WHERE timestamp >= ? AND timestamp <= ?
        ''', (start_date.isoformat(), end_date.isoformat()))
        
        stats = cursor.fetchone()
        
        # Get event type breakdown
        cursor.execute('''
            SELECT event_type, COUNT(*) as count
            FROM audit_entries 
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY event_type
            ORDER BY count DESC
        ''', (start_date.isoformat(), end_date.isoformat()))
        
        event_breakdown = cursor.fetchall()
        
        # Get user activity
        cursor.execute('''
            SELECT user_id, COUNT(*) as event_count
            FROM audit_entries 
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY user_id
            ORDER BY event_count DESC
            LIMIT 10
        ''', (start_date.isoformat(), end_date.isoformat()))
        
        user_activity = cursor.fetchall()
        
        conn.close()
        
        report = {
            'report_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': period_days
            },
            'summary_statistics': {
                'total_events': stats[0],
                'unique_users': stats[1],
                'unique_content': stats[2],
                'first_event': stats[3],
                'last_event': stats[4]
            },
            'event_type_breakdown': [
                {'event_type': row[0], 'count': row[1]} 
                for row in event_breakdown
            ],
            'top_users': [
                {'user_id': row[0], 'event_count': row[1]} 
                for row in user_activity
            ],
            'chain_integrity': self.verify_chain_integrity(),
            'generated_at': datetime.now().isoformat()
        }
        
        return report

class AuditEventTypes:
    """Standard audit event types"""
    
    # Content Generation Events
    CONTENT_GENERATED = "CONTENT_GENERATED"
    CONTENT_MODIFIED = "CONTENT_MODIFIED"
    CONTENT_DELETED = "CONTENT_DELETED"
    CONTENT_EXPORTED = "CONTENT_EXPORTED"
    
    # Security Events
    LOGIN_ATTEMPT = "LOGIN_ATTEMPT"
    ACCESS_GRANTED = "ACCESS_GRANTED"
    ACCESS_DENIED = "ACCESS_DENIED"
    SECURITY_ALERT = "SECURITY_ALERT"
    
    # System Events
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
    CONFIGURATION_CHANGE = "CONFIGURATION_CHANGE"
    MAINTENANCE_PERFORMED = "MAINTENANCE_PERFORMED"

# Example usage
def main():
    """Demo audit log functionality"""
    print("📜 IMMUTABLE AUDIT LOG DEMO")
    print("=" * 35)
    
    # Initialize audit log
    audit_log = ImmutableAuditLog()
    
    try:
        # Log various events
        print("📝 Logging sample events...")
        
        # Content generation event
        content_event = audit_log.log_event(
            event_type=AuditEventTypes.CONTENT_GENERATED,
            user_id="user_123",
            session_id="session_456",
            content_id="content_789",
            action_details={
                'content_type': 'image',
                'prompt': 'Landscape painting',
                'dimensions': [1024, 1024],
                'format': 'PNG'
            },
            system_state={
                'memory_usage': '4.2GB',
                'cpu_usage': '75%',
                'active_models': ['stable_diffusion']
            }
        )
        print(f"✅ Content event logged: {content_event[:16]}...")
        
        # Security event
        security_event = audit_log.log_event(
            event_type=AuditEventTypes.ACCESS_GRANTED,
            user_id="admin_user",
            session_id="admin_session",
            content_id="system_config",
            action_details={
                'access_type': 'configuration_read',
                'ip_address': '192.168.1.100',
                'user_agent': 'Mozilla/5.0...'
            }
        )
        print(f"✅ Security event logged: {security_event[:16]}...")
        
        # Verify chain integrity
        print("\n🔍 Verifying chain integrity...")
        integrity_result = audit_log.verify_chain_integrity()
        print(f"Chain Status: {integrity_result['integrity_status']}")
        print(f"Valid Entries: {integrity_result['valid_entries']}")
        print(f"Invalid Entries: {integrity_result['invalid_entries']}")
        
        # Generate compliance report
        print("\n📊 Generating compliance report...")
        report = audit_log.generate_compliance_report(period_days=1)
        
        print(f"Total Events: {report['summary_statistics']['total_events']}")
        print(f"Unique Users: {report['summary_statistics']['unique_users']}")
        print(f"Chain Integrity: {report['chain_integrity']['integrity_status']}")
        
        # Retrieve audit trail
        print("\n📋 Retrieving audit trail...")
        trail = audit_log.get_audit_trail(content_id="content_789")
        print(f"Events for content_789: {len(trail)}")
        
        for event in trail:
            print(f"  - {event['timestamp']}: {event['event_type']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    from datetime import timedelta
    success = main()
    exit(0 if success else 1)