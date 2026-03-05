"""
Authentication and OTP Module
Handles user verification via Twilio SMS
"""

import random
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()

class AuthManager:
    def __init__(self, db_path: str = "civlink.db"):
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)
        else:
            self.client = None
            
        self._init_db()

    def _init_db(self):
        """Initialize OTP storage table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS otp_verification (
                user_id TEXT PRIMARY KEY,
                otp_code TEXT NOT NULL,
                expiry_time TIMESTAMP NOT NULL,
                verified BOOLEAN DEFAULT FALSE
            )
        ''')
        conn.commit()
        conn.close()

    def generate_otp(self, user_id: str) -> str:
        """Generate a 6-digit OTP and store it"""
        otp = str(random.randint(100000, 999999))
        expiry = datetime.now() + timedelta(minutes=10)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO otp_verification (user_id, otp_code, expiry_time, verified)
            VALUES (?, ?, ?, ?)
        ''', (user_id, otp, expiry, False))
        conn.commit()
        conn.close()
        
        return otp

    def send_otp(self, user_id: str, phone_number: str) -> bool:
        """Send OTP via Twilio WhatsApp/SMS"""
        if not self.client:
            self.logger.error("Twilio client not configured for OTP")
            return False
            
        otp = self.generate_otp(user_id)
        message_body = f"Your CiviLink verification code is: {otp}. It expires in 10 minutes."
        
        try:
            # Note: to_number must be in E.164 format (e.g., whatsapp:+1234567890)
            target = phone_number if phone_number.startswith('whatsapp:') else f"whatsapp:{phone_number}"
            self.client.messages.create(
                from_=f"whatsapp:{self.twilio_number}",
                body=message_body,
                to=target
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to send OTP: {str(e)}")
            return False

    def verify_otp(self, user_id: str, input_code: str) -> Tuple[bool, str]:
        """Verify the OTP provided by user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT otp_code, expiry_time, verified FROM otp_verification WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if not row:
            return False, "No OTP found for this user."
            
        stored_code, expiry_str, already_verified = row
        expiry_time = datetime.fromisoformat(expiry_str)
        
        if already_verified:
            return True, "User already verified."
            
        if datetime.now() > expiry_time:
            return False, "OTP has expired."
            
        if input_code == stored_code:
            cursor.execute('UPDATE otp_verification SET verified = TRUE WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
            return True, "Verification successful."
        
        conn.close()
        return False, "Invalid OTP code."

    def is_verified(self, user_id: str) -> bool:
        """Check if user is already verified"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT verified FROM otp_verification WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else False
