"""
Whisper Speech-to-Text Integration
Handles voice message transcription for WhatsApp audio
"""

import whisper
import logging
import os
import tempfile
from typing import Optional, Dict, Tuple
from dotenv import load_dotenv
import torch
import numpy as np
from pydub import AudioSegment
import io

load_dotenv()

class WhisperSTT:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model_name = os.getenv("WHISPER_MODEL", "base")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        try:
            self.model = whisper.load_model(self.model_name, device=self.device)
            self.logger.info(f"Whisper model '{self.model_name}' loaded on {self.device}")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {str(e)}")
            self.model = None
    
    def transcribe_audio(self, audio_data: bytes, audio_format: str = "ogg") -> Tuple[Optional[str], Optional[str]]:
        """
        Transcribe audio data to text
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Format of audio (ogg, mp3, wav, etc.)
            
        Returns:
            Tuple of (transcribed_text, detected_language)
        """
        if not self.model:
            self.logger.error("Whisper model not available")
            return None, None
        
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Convert to WAV if needed (Whisper works best with WAV)
                if audio_format != "wav":
                    wav_path = self._convert_to_wav(temp_file_path)
                    if not wav_path:
                        return None, None
                else:
                    wav_path = temp_file_path
                
                # Transcribe
                result = self.model.transcribe(
                    wav_path,
                    fp16=False if self.device == "cpu" else True,
                    language=None,  # Auto-detect language
                    task="transcribe"
                )
                
                text = result.get("text", "").strip()
                detected_language = result.get("language", "en")
                
                # Clean up temporary files
                os.unlink(temp_file_path)
                if wav_path != temp_file_path and os.path.exists(wav_path):
                    os.unlink(wav_path)
                
                self.logger.info(f"Transcribed {len(text)} characters, detected language: {detected_language}")
                return text, detected_language
                
            except Exception as e:
                self.logger.error(f"Transcription failed: {str(e)}")
                # Clean up on error
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                return None, None
                
        except Exception as e:
            self.logger.error(f"Audio processing failed: {str(e)}")
            return None, None
    
    def _convert_to_wav(self, input_path: str) -> Optional[str]:
        """Convert audio file to WAV format"""
        try:
            audio = AudioSegment.from_file(input_path)
            wav_path = input_path.replace(os.path.splitext(input_path)[1], ".wav")
            audio.export(wav_path, format="wav")
            return wav_path
        except Exception as e:
            self.logger.error(f"Audio conversion failed: {str(e)}")
            return None
    
    def detect_language(self, audio_data: bytes, audio_format: str = "ogg") -> Optional[str]:
        """
        Detect language from audio without full transcription
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Format of audio
            
        Returns:
            Detected language code (en, ta, hi, etc.)
        """
        if not self.model:
            return None
        
        try:
            text, detected_lang = self.transcribe_audio(audio_data, audio_format)
            return detected_lang
        except Exception as e:
            self.logger.error(f"Language detection failed: {str(e)}")
            return None
    
    def get_supported_formats(self) -> list:
        """Get list of supported audio formats"""
        return ["ogg", "mp3", "wav", "m4a", "flac", "aac"]
    
    def is_format_supported(self, audio_format: str) -> bool:
        """Check if audio format is supported"""
        return audio_format.lower() in self.get_supported_formats()
    
    def transcribe_with_confidence(self, audio_data: bytes, audio_format: str = "ogg") -> Dict:
        """
        Transcribe with confidence scores and additional metadata
        
        Returns:
            Dict with text, language, confidence, and metadata
        """
        text, language = self.transcribe_audio(audio_data, audio_format)
        
        if not text:
            return {
                "text": None,
                "language": None,
                "confidence": 0.0,
                "words": [],
                "duration": 0.0
            }
        
        # Calculate basic confidence metrics
        word_count = len(text.split())
        confidence = min(1.0, word_count / 10.0)  # Simple confidence based on word count
        
        return {
            "text": text,
            "language": language,
            "confidence": confidence,
            "word_count": word_count,
            "char_count": len(text),
            "detected_emotion": self._detect_emotion_from_text(text)
        }
    
    def _detect_emotion_from_text(self, text: str) -> str:
        """Simple emotion detection from transcribed text"""
        text_lower = text.lower()
        
        emotion_keywords = {
            "frustrated": ["frustrated", "angry", "upset", "annoyed", "mad"],
            "confused": ["confused", "don't understand", "unclear", "what do you mean"],
            "anxious": ["worried", "anxious", "nervous", "concerned"],
            "relieved": ["thank god", "finally", "relieved", "good"],
            "neutral": []  # Default
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        
        return "neutral"

class AudioProcessor:
    """Utility class for processing WhatsApp audio messages"""
    
    @staticmethod
    def extract_audio_from_whatsapp(media_data: bytes) -> Tuple[bytes, str]:
        """
        Extract audio data from WhatsApp media
        
        Args:
            media_data: Raw media data from WhatsApp
            
        Returns:
            Tuple of (audio_bytes, format)
        """
        try:
            # WhatsApp typically sends OGG format for voice messages
            # Try to detect format from file signature
            if media_data.startswith(b'OggS'):
                return media_data, "ogg"
            elif media_data.startswith(b'ID3') or media_data.startswith(b'\xff\xfb'):
                return media_data, "mp3"
            elif media_data.startswith(b'RIFF'):
                return media_data, "wav"
            else:
                # Default to OGG for WhatsApp voice messages
                return media_data, "ogg"
        except Exception as e:
            logging.error(f"Audio format detection failed: {str(e)}")
            return media_data, "ogg"
    
    @staticmethod
    def validate_audio_size(audio_data: bytes, max_size_mb: int = 25) -> bool:
        """Validate audio file size"""
        size_mb = len(audio_data) / (1024 * 1024)
        return size_mb <= max_size_mb
    
    @staticmethod
    def get_audio_duration(audio_data: bytes, audio_format: str) -> Optional[float]:
        """Get audio duration in seconds"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{audio_format}") as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                audio = AudioSegment.from_file(temp_file_path)
                duration_seconds = len(audio) / 1000.0
                os.unlink(temp_file_path)
                return duration_seconds
            except Exception as e:
                logging.error(f"Duration detection failed: {str(e)}")
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                return None
        except Exception as e:
            logging.error(f"Audio processing failed: {str(e)}")
            return None
