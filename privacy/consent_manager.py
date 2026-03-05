"""
Privacy and Consent Framework
Manages user consent, data protection, and privacy compliance
"""

import logging
import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from cryptography.fernet import Fernet
import sqlite3
from dotenv import load_dotenv

load_dotenv()

class ConsentType(Enum):
    DATA_PROCESSING = "data_processing"
    DOCUMENT_UPLOAD = "document_upload"
    VOICE_PROCESSING = "voice_processing"
    PERSONAL_INFO_COLLECTION = "personal_info_collection"
    GOVERNMENT_SUBMISSION = "government_submission"

class ConsentStatus(Enum):
    PENDING = "pending"
    GRANTED = "granted"
    DENIED = "denied"
    EXPIRED = "expired"
    REVOKED = "revoked"

@dataclass
class ConsentRecord:
    user_id: str
    consent_type: ConsentType
    status: ConsentStatus
    timestamp: datetime
    purpose: str
    data_retention_days: int = 30
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class PrivacySettings:
    data_minimization: bool = True
    automatic_deletion: bool = True
    encryption_enabled: bool = True
    audit_logging: bool = True
    consent_required: bool = True
    voice_data_retention_days: int = 7
    document_retention_days: int = 30

class ConsentManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.encryption_key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
        self.cipher = Fernet(self.encryption_key.encode())
        self.privacy_settings = PrivacySettings()
        
        # Initialize database
        self.db_path = os.getenv("DATABASE_URL", "sqlite:///civlink.db").replace("sqlite:///", "")
        self._init_database()
        
        # Consent messages in multiple languages
        self.consent_messages = self._load_consent_messages()
    
    def _init_database(self):
        """Initialize privacy database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create consent records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS consent_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    consent_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    data_retention_days INTEGER DEFAULT 30,
                    metadata TEXT,
                    UNIQUE(user_id, consent_type)
                )
            ''')
            
            # Create audit log table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS privacy_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT
                )
            ''')
            
            # Create data retention table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_retention (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    data_type TEXT NOT NULL,
                    data_hash TEXT NOT NULL,
                    expiry_date TEXT NOT NULL,
                    deleted BOOLEAN DEFAULT FALSE
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {str(e)}")
    
    def _load_consent_messages(self) -> Dict[str, Dict[str, str]]:
        """Load consent messages in multiple languages"""
        return {
            "data_processing": {
                "en": "Do you consent to EmpowerAbility processing your personal information for application assistance?",
                "ta": "விண்ணப்ப உதவிக்கு உங்கள் தனிப்பட்ட தகவலை EmpowerAbility செயலாற்ற ஒப்புக்கொள்கிறீர்களா?",
                "hi": "क्या आप आवेदन सहायता के लिए EmpowerAbility द्वारा आपकी व्यक्तिगत जानकारी को संसाधित करने के लिए सहमत हैं?"
            },
            "document_upload": {
                "en": "Do you consent to uploading and processing your documents for verification?",
                "ta": "சரிபார்ப்பிற்கு உங்கள் ஆவணங்களை பதிவேற்ற மற்றும் செயலாற்ற ஒப்புக்கொள்கிறீர்களா?",
                "hi": "क्या आप सत्यापन के लिए अपने दस्तावेज़ों को अपलोड और संसाधित करने के लिए सहमत हैं?"
            },
            "voice_processing": {
                "en": "Do you consent to voice message processing for transcription?",
                "ta": "உரை மாற்றத்திற்கான குரல் செய்தி செயலாக்கத்திற்கு ஒப்புக்கொள்கிறீர்களா?",
                "hi": "क्या आप ट्रांसक्रिप्शन के लिए वॉइस मैसेज प्रोसेसिंग के लिए सहमत हैं?"
            }
        }
    
    def request_consent(self, user_id: str, consent_type: ConsentType, language: str = "en") -> str:
        """Request user consent for specific data processing"""
        try:
            # Check if consent already exists
            existing_consent = self.get_consent_status(user_id, consent_type)
            if existing_consent and existing_consent.status == ConsentStatus.GRANTED:
                return "Consent already granted"
            
            # Get consent message
            consent_key = consent_type.value
            messages = self.consent_messages.get(consent_key, {})
            message = messages.get(language, messages.get("en", "Do you consent?"))
            
            # Log consent request
            self._log_privacy_event(user_id, "consent_requested", consent_type.value, {
                "language": language,
                "message": message
            })
            
            return message
            
        except Exception as e:
            self.logger.error(f"Consent request failed: {str(e)}")
            return "Error requesting consent"
    
    def record_consent(self, user_id: str, consent_type: ConsentType, response: str, 
                      language: str = "en", metadata: Optional[Dict] = None) -> bool:
        """Record user consent response"""
        try:
            # Determine consent status
            if response.lower() in ["yes", "agree", "consent", "சம்மதம்", "हाँ", "ok"]:
                status = ConsentStatus.GRANTED
            elif response.lower() in ["no", "disagree", "decline", "இல்லை", "नहीं"]:
                status = ConsentStatus.DENIED
            else:
                status = ConsentStatus.PENDING
            
            # Create consent record
            consent_record = ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                status=status,
                timestamp=datetime.now(),
                purpose=self._get_purpose_description(consent_type, language),
                data_retention_days=self._get_retention_days(consent_type),
                metadata=metadata or {}
            )
            
            # Save to database
            self._save_consent_record(consent_record)
            
            # Log consent response
            self._log_privacy_event(user_id, "consent_recorded", consent_type.value, {
                "status": status.value,
                "response": response,
                "language": language
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Consent recording failed: {str(e)}")
            return False
    
    def get_consent_status(self, user_id: str, consent_type: ConsentType) -> Optional[ConsentRecord]:
        """Get current consent status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_id, consent_type, status, timestamp, purpose, data_retention_days, metadata
                FROM consent_records
                WHERE user_id = ? AND consent_type = ?
                ORDER BY timestamp DESC
                LIMIT 1
            ''', (user_id, consent_type.value))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                metadata = json.loads(row[6]) if row[6] else {}
                return ConsentRecord(
                    user_id=row[0],
                    consent_type=ConsentType(row[1]),
                    status=ConsentStatus(row[2]),
                    timestamp=datetime.fromisoformat(row[3]),
                    purpose=row[4],
                    data_retention_days=row[5],
                    metadata=metadata
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Consent status retrieval failed: {str(e)}")
            return None
    
    def has_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """Check if user has granted valid consent"""
        consent = self.get_consent_status(user_id, consent_type)
        
        if not consent:
            return False
        
        # Check if consent is still valid
        if consent.status == ConsentStatus.GRANTED:
            expiry_date = consent.timestamp + timedelta(days=consent.data_retention_days)
            if datetime.now() < expiry_date:
                return True
            else:
                # Mark as expired
                self._update_consent_status(user_id, consent_type, ConsentStatus.EXPIRED)
                return False
        
        return False
    
    def revoke_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """Revoke user consent"""
        try:
            success = self._update_consent_status(user_id, consent_type, ConsentStatus.REVOKED)
            
            if success:
                self._log_privacy_event(user_id, "consent_revoked", consent_type.value)
                # Schedule data deletion for revoked consent
                self._schedule_data_deletion(user_id, consent_type)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Consent revocation failed: {str(e)}")
            return False
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            if self.privacy_settings.encryption_enabled:
                encrypted_data = self.cipher.encrypt(data.encode())
                return encrypted_data.decode()
            return data
        except Exception as e:
            self.logger.error(f"Data encryption failed: {str(e)}")
            return data
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            if self.privacy_settings.encryption_enabled:
                decrypted_data = self.cipher.decrypt(encrypted_data.encode())
                return decrypted_data.decode()
            return encrypted_data
        except Exception as e:
            self.logger.error(f"Data decryption failed: {str(e)}")
            return encrypted_data
    
    def store_data_with_retention(self, user_id: str, data_type: str, data: Any, 
                                retention_days: Optional[int] = None) -> str:
        """Store data with automatic retention policy"""
        try:
            # Generate data hash for tracking
            data_str = json.dumps(data) if isinstance(data, (dict, list)) else str(data)
            data_hash = hashlib.sha256(data_str.encode()).hexdigest()
            
            # Determine retention period
            if retention_days is None:
                retention_days = self._get_retention_days_by_type(data_type)
            
            expiry_date = datetime.now() + timedelta(days=retention_days)
            
            # Store in retention table
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO data_retention
                (user_id, data_type, data_hash, expiry_date, deleted)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, data_type, data_hash, expiry_date.isoformat(), False))
            
            conn.commit()
            conn.close()
            
            # Log data storage
            self._log_privacy_event(user_id, "data_stored", data_type, {
                "data_hash": data_hash,
                "expiry_date": expiry_date.isoformat(),
                "retention_days": retention_days
            })
            
            return data_hash
            
        except Exception as e:
            self.logger.error(f"Data storage with retention failed: {str(e)}")
            return ""
    
    def cleanup_expired_data(self) -> int:
        """Clean up expired data according to retention policies"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Find expired data
            cursor.execute('''
                UPDATE data_retention
                SET deleted = TRUE
                WHERE expiry_date < ? AND deleted = FALSE
            ''', (datetime.now().isoformat(),))
            
            expired_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up {expired_count} expired data records")
            return expired_count
            
        except Exception as e:
            self.logger.error(f"Data cleanup failed: {str(e)}")
            return 0
    
    def get_privacy_summary(self, user_id: str) -> Dict[str, Any]:
        """Get user's privacy and consent summary"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all consent records
            cursor.execute('''
                SELECT consent_type, status, timestamp, purpose
                FROM consent_records
                WHERE user_id = ?
            ''', (user_id,))
            
            consent_records = []
            for row in cursor.fetchall():
                consent_records.append({
                    "type": row[0],
                    "status": row[1],
                    "timestamp": row[2],
                    "purpose": row[3]
                })
            
            # Get stored data count
            cursor.execute('''
                SELECT data_type, COUNT(*) as count
                FROM data_retention
                WHERE user_id = ? AND deleted = FALSE
                GROUP BY data_type
            ''', (user_id,))
            
            stored_data = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                "user_id": user_id,
                "consent_records": consent_records,
                "stored_data": stored_data,
                "privacy_settings": asdict(self.privacy_settings),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Privacy summary generation failed: {str(e)}")
            return {}
    
    def _save_consent_record(self, consent_record: ConsentRecord):
        """Save consent record to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO consent_records
            (user_id, consent_type, status, timestamp, purpose, data_retention_days, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            consent_record.user_id,
            consent_record.consent_type.value,
            consent_record.status.value,
            consent_record.timestamp.isoformat(),
            consent_record.purpose,
            consent_record.data_retention_days,
            json.dumps(consent_record.metadata) if consent_record.metadata else None
        ))
        
        conn.commit()
        conn.close()
    
    def _update_consent_status(self, user_id: str, consent_type: ConsentType, 
                             new_status: ConsentStatus) -> bool:
        """Update consent status"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE consent_records
                SET status = ?, timestamp = ?
                WHERE user_id = ? AND consent_type = ?
            ''', (new_status.value, datetime.now().isoformat(), user_id, consent_type.value))
            
            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Consent status update failed: {str(e)}")
            return False
    
    def _log_privacy_event(self, user_id: str, action: str, data_type: str, 
                          details: Optional[Dict] = None):
        """Log privacy-related events"""
        if not self.privacy_settings.audit_logging:
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO privacy_audit_log
                (user_id, action, data_type, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                action,
                data_type,
                datetime.now().isoformat(),
                json.dumps(details) if details else None
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Privacy event logging failed: {str(e)}")
    
    def _get_purpose_description(self, consent_type: ConsentType, language: str) -> str:
        """Get purpose description for consent type"""
        purposes = {
            ConsentType.DATA_PROCESSING: {
                "en": "To process your application and provide assistance",
                "ta": "உங்கள் விண்ணப்பத்தை செயலாற்றி உதவி வழங்க",
                "hi": "आपके आवेदन को संसाधित करने और सहायता प्रदान करने के लिए"
            },
            ConsentType.DOCUMENT_UPLOAD: {
                "en": "To verify your identity and documents",
                "ta": "உங்கள் அடையாளத்தை மற்றும் ஆவணங்களை சரிபார்க்க",
                "hi": "आपकी पहचान और दस्तावेज़ों को सत्यापित करने के लिए"
            }
        }
        
        return purposes.get(consent_type, {}).get(language, purposes.get(consent_type, {}).get("en", ""))
    
    def _get_retention_days(self, consent_type: ConsentType) -> int:
        """Get data retention days for consent type"""
        retention_map = {
            ConsentType.DATA_PROCESSING: 30,
            ConsentType.DOCUMENT_UPLOAD: 30,
            ConsentType.VOICE_PROCESSING: 7,
            ConsentType.PERSONAL_INFO_COLLECTION: 30,
            ConsentType.GOVERNMENT_SUBMISSION: 365
        }
        return retention_map.get(consent_type, 30)
    
    def _get_retention_days_by_type(self, data_type: str) -> int:
        """Get retention days by data type"""
        if data_type == "voice":
            return self.privacy_settings.voice_data_retention_days
        elif data_type == "document":
            return self.privacy_settings.document_retention_days
        else:
            return 30
    
    def _schedule_data_deletion(self, user_id: str, consent_type: ConsentType):
        """Schedule data deletion when consent is revoked"""
        try:
            # Mark data for immediate deletion
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE data_retention
                SET expiry_date = ?
                WHERE user_id = ? AND data_type = ?
            ''', (datetime.now().isoformat(), user_id, consent_type.value))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Data deletion scheduling failed: {str(e)}")
