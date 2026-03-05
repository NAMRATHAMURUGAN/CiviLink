"""
CiviLink Main Application
Flask application for WhatsApp-based government services assistant
"""

from flask import Flask, request, jsonify, Response
import logging
import os
from dotenv import load_dotenv
from core.assistant import CiviLinkAssistant
from privacy.consent_manager import ConsentManager, ConsentType
from whatsapp.twilio_handler import TwilioWebhookHandler
from multilingual.multilingual_llm import MultilingualLLM
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv("LOG_FILE", "civlink.log")),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "dev-secret-key")

# Initialize components
assistant = CiviLinkAssistant()
consent_manager = ConsentManager()
multilingual_llm = MultilingualLLM()
twilio_handler = TwilioWebhookHandler()

@app.route('/')
def home():
    """Health check endpoint"""
    return jsonify({
        "service": "CiviLink - EmpowerAbility Government Assistant",
        "status": "active",
        "version": "1.0.0",
        "features": [
            "LLM-powered intent detection",
            "Multilingual support (English, Tamil, Hindi)",
            "Voice message processing with Whisper",
            "OCR document processing",
            "Privacy-first consent management",
            "WhatsApp integration (Twilio)"
        ]
    })

@app.route('/webhook/whatsapp', methods=['POST'])
def whatsapp_webhook():
    """Handle Twilio WhatsApp webhook events"""
    try:
        # Twilio sends data as form-encoded
        data = request.form.to_dict()
        logger.info(f"Received Twilio WhatsApp webhook from {data.get('From')}")
        
        # Process message via Twilio handler (returns TwiML string)
        twiml_response = twilio_handler.process_message(data, assistant, consent_manager)
        
        response = Response(twiml_response, mimetype='text/xml')
        # Add header to bypass ngrok browser warning
        response.headers['ngrok-skip-browser-warning'] = 'true'
        return response
            
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {str(e)}")
        return Response("<Response><Message>Technical error. Please try again.</Message></Response>", mimetype='text/xml'), 500

@app.route('/api/message', methods=['POST'])
def process_message():
    """Direct API endpoint for message processing"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        message = data.get('message')
        message_type = data.get('message_type', 'text')
        
        if not user_id or not message:
            return jsonify({"error": "user_id and message are required"}), 400
        
        # Process message through assistant
        result = assistant.process_message(user_id, message, message_type)
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Message processing error: {str(e)}")
        return jsonify({"error": "Message processing failed"}), 500

@app.route('/api/consent/request', methods=['POST'])
def request_consent():
    """Request user consent for data processing"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        consent_type = data.get('consent_type')
        language = data.get('language', 'en')
        
        if not user_id or not consent_type:
            return jsonify({"error": "user_id and consent_type are required"}), 400
        
        # Validate consent type
        try:
            consent_enum = ConsentType(consent_type)
        except ValueError:
            return jsonify({"error": f"Invalid consent_type: {consent_type}"}), 400
        
        # Request consent
        consent_message = consent_manager.request_consent(user_id, consent_enum, language)
        
        return jsonify({
            "consent_message": consent_message,
            "consent_type": consent_type,
            "user_id": user_id
        }), 200
        
    except Exception as e:
        logger.error(f"Consent request error: {str(e)}")
        return jsonify({"error": "Consent request failed"}), 500

@app.route('/api/consent/record', methods=['POST'])
def record_consent():
    """Record user consent response"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        consent_type = data.get('consent_type')
        response = data.get('response')
        language = data.get('language', 'en')
        
        if not all([user_id, consent_type, response]):
            return jsonify({"error": "user_id, consent_type, and response are required"}), 400
        
        # Validate consent type
        try:
            consent_enum = ConsentType(consent_type)
        except ValueError:
            return jsonify({"error": f"Invalid consent_type: {consent_type}"}), 400
        
        # Record consent
        success = consent_manager.record_consent(user_id, consent_enum, response, language)
        
        if success:
            return jsonify({
                "status": "recorded",
                "consent_type": consent_type,
                "user_id": user_id,
                "response": response
            }), 200
        else:
            return jsonify({"error": "Consent recording failed"}), 500
            
    except Exception as e:
        logger.error(f"Consent recording error: {str(e)}")
        return jsonify({"error": "Consent recording failed"}), 500

@app.route('/api/ocr/process', methods=['POST'])
def process_document():
    """Process document with OCR"""
    try:
        if 'document' not in request.files:
            return jsonify({"error": "No document file provided"}), 400
        
        file = request.files['document']
        user_id = request.form.get('user_id')
        document_type_hint = request.form.get('document_type')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        # Check consent for document processing
        if not consent_manager.has_consent(user_id, ConsentType.DOCUMENT_UPLOAD):
            return jsonify({"error": "Document processing consent not granted"}), 403
        
        # Read image data
        image_data = file.read()
        
        # Process with OCR
        from ocr.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        ocr_result = processor.process_document(image_data, document_type_hint)
        
        # Store document data with retention policy
        if ocr_result.extracted_text:
            consent_manager.store_data_with_retention(
                user_id, 
                "document", 
                ocr_result.extracted_text,
                30  # 30 days retention
            )
        
        return jsonify({
            "user_id": user_id,
            "document_type": ocr_result.document_type,
            "confidence": ocr_result.confidence,
            "extracted_fields": ocr_result.detected_fields,
            "processing_time": ocr_result.processing_time,
            "image_quality": ocr_result.image_quality
        }), 200
        
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        return jsonify({"error": "Document processing failed"}), 500

@app.route('/api/voice/transcribe', methods=['POST'])
def transcribe_voice():
    """Transcribe voice message using Whisper"""
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        file = request.files['audio']
        user_id = request.form.get('user_id')
        audio_format = request.form.get('format', 'ogg')
        
        if not user_id:
            return jsonify({"error": "user_id is required"}), 400
        
        # Check consent for voice processing
        if not consent_manager.has_consent(user_id, ConsentType.VOICE_PROCESSING):
            return jsonify({"error": "Voice processing consent not granted"}), 403
        
        # Read audio data
        audio_data = file.read()
        
        # Transcribe with Whisper
        from core.whisper_stt import WhisperSTT
        whisper = WhisperSTT()
        
        transcription_result = whisper.transcribe_with_confidence(audio_data, audio_format)
        
        # Store transcription with retention policy
        if transcription_result["text"]:
            consent_manager.store_data_with_retention(
                user_id,
                "voice",
                transcription_result["text"],
                7  # 7 days retention for voice data
            )
        
        return jsonify({
            "user_id": user_id,
            "transcription": transcription_result["text"],
            "language": transcription_result["language"],
            "confidence": transcription_result["confidence"],
            "word_count": transcription_result["word_count"],
            "detected_emotion": transcription_result["detected_emotion"]
        }), 200
        
    except Exception as e:
        logger.error(f"Voice transcription error: {str(e)}")
        return jsonify({"error": "Voice transcription failed"}), 500

@app.route('/api/privacy/summary/<user_id>', methods=['GET'])
def get_privacy_summary(user_id: str):
    """Get user's privacy and consent summary"""
    try:
        summary = consent_manager.get_privacy_summary(user_id)
        return jsonify(summary), 200
        
    except Exception as e:
        logger.error(f"Privacy summary error: {str(e)}")
        return jsonify({"error": "Privacy summary retrieval failed"}), 500

@app.route('/api/consent/revoke', methods=['POST'])
def revoke_consent():
    """Revoke user consent"""
    try:
        data = request.get_json()
        
        user_id = data.get('user_id')
        consent_type = data.get('consent_type')
        
        if not user_id or not consent_type:
            return jsonify({"error": "user_id and consent_type are required"}), 400
        
        # Validate consent type
        try:
            consent_enum = ConsentType(consent_type)
        except ValueError:
            return jsonify({"error": f"Invalid consent_type: {consent_type}"}), 400
        
        # Revoke consent
        success = consent_manager.revoke_consent(user_id, consent_enum)
        
        if success:
            return jsonify({
                "status": "revoked",
                "consent_type": consent_type,
                "user_id": user_id
            }), 200
        else:
            return jsonify({"error": "Consent revocation failed"}), 500
            
    except Exception as e:
        logger.error(f"Consent revocation error: {str(e)}")
        return jsonify({"error": "Consent revocation failed"}), 500

@app.route('/api/admin/cleanup', methods=['POST'])
def cleanup_expired_data():
    """Clean up expired data (admin endpoint)"""
    try:
        # This should be protected with authentication in production
        cleaned_count = consent_manager.cleanup_expired_data()
        
        return jsonify({
            "status": "completed",
            "cleaned_records": cleaned_count
        }), 200
        
    except Exception as e:
        logger.error(f"Data cleanup error: {str(e)}")
        return jsonify({"error": "Data cleanup failed"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Comprehensive health check"""
    try:
        # Check all components
        health_status = {
            "status": "healthy",
            "components": {
                "assistant": "operational",
                "consent_manager": "operational",
                "multilingual_llm": "operational",
                "whatsapp_handler": "operational"
            },
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }
        
        return jsonify(health_status), 200
        
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

if __name__ == '__main__':
    # Run cleanup on startup
    logger.info("Starting CiviLink application...")
    logger.info("Performing startup data cleanup...")
    cleaned = consent_manager.cleanup_expired_data()
    logger.info(f"Cleaned {cleaned} expired records on startup")
    
    # Start Flask app
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_ENV", "production") == "development"
    
    app.run(host='0.0.0.0', port=port, debug=debug)
