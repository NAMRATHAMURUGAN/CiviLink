"""
WhatsApp Webhook Handler
Handles incoming WhatsApp messages and sends responses
"""

import logging
import json
import os
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from core.assistant import CiviLinkAssistant
from privacy.consent_manager import ConsentManager, ConsentType

load_dotenv()

@dataclass
class WhatsAppMessage:
    from_number: str
    message_id: str
    message_type: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None

class WhatsAppWebhookHandler:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.webhook_verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")
        
        self.base_url = f"https://graph.facebook.com/v18.0/{self.phone_number_id}"
        
    def verify_webhook(self, args: Dict[str, str]) -> tuple:
        """Verify WhatsApp webhook"""
        try:
            mode = args.get('hub.mode')
            token = args.get('hub.verify_token')
            challenge = args.get('hub.challenge')
            
            if mode and token:
                if mode == 'subscribe' and token == self.webhook_verify_token:
                    self.logger.info("Webhook verified successfully")
                    return int(challenge), 200
                else:
                    self.logger.warning("Webhook verification failed")
                    return "Verification token mismatch", 403
            else:
                return "Missing parameters", 400
                
        except Exception as e:
            self.logger.error(f"Webhook verification error: {str(e)}")
            return "Verification failed", 500
    
    def process_message(self, webhook_data: Dict[str, Any], 
                       assistant: CiviLinkAssistant, 
                       consent_manager: ConsentManager) -> Dict[str, Any]:
        """Process incoming WhatsApp message"""
        try:
            # Extract message from webhook data
            message = self._extract_message(webhook_data)
            if not message:
                return {"status": "no_message", "response": "No message found"}
            
            self.logger.info(f"Processing message from {message.from_number}: {message.content[:50]}...")
            
            # Process different message types
            if message.message_type == "text":
                response = self._handle_text_message(message, assistant, consent_manager)
            elif message.message_type == "audio":
                response = self._handle_voice_message(message, assistant, consent_manager)
            elif message.message_type == "image":
                response = self._handle_image_message(message, assistant, consent_manager)
            elif message.message_type == "document":
                response = self._handle_document_message(message, assistant, consent_manager)
            else:
                response = self._handle_unsupported_message(message)
            
            # Send response back to WhatsApp
            if response.get("response_text"):
                self._send_message(message.from_number, response["response_text"], response.get("message_type", "text"))
            
            return {
                "status": "processed",
                "message_id": message.message_id,
                "from": message.from_number,
                "response": response
            }
            
        except Exception as e:
            self.logger.error(f"Message processing error: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _extract_message(self, webhook_data: Dict[str, Any]) -> Optional[WhatsAppMessage]:
        """Extract message from WhatsApp webhook data"""
        try:
            # Navigate through WhatsApp webhook structure
            entry = webhook_data.get('entry', [])
            if not entry:
                return None
            
            changes = entry[0].get('changes', [])
            if not changes:
                return None
            
            messages = changes[0].get('value', {}).get('messages', [])
            if not messages:
                return None
            
            message_data = messages[0]
            
            # Extract basic message info
            from_number = message_data.get('from')
            message_id = message_data.get('id')
            timestamp = message_data.get('timestamp')
            
            # Determine message type and content
            message_type = None
            content = ""
            metadata = {}
            
            if 'text' in message_data:
                message_type = "text"
                content = message_data['text'].get('body', '')
            
            elif 'audio' in message_data:
                message_type = "audio"
                audio_data = message_data['audio']
                content = audio_data.get('id', '')  # Media ID for download
                metadata['media_id'] = content
                metadata['mime_type'] = audio_data.get('mime_type', 'audio/ogg')
            
            elif 'image' in message_data:
                message_type = "image"
                image_data = message_data['image']
                content = image_data.get('id', '')
                metadata['media_id'] = content
                metadata['mime_type'] = image_data.get('mime_type', 'image/jpeg')
                metadata['caption'] = image_data.get('caption', '')
            
            elif 'document' in message_data:
                message_type = "document"
                doc_data = message_data['document']
                content = doc_data.get('id', '')
                metadata['media_id'] = content
                metadata['mime_type'] = doc_data.get('mime_type', 'application/pdf')
                metadata['filename'] = doc_data.get('filename', 'document')
                metadata['caption'] = doc_data.get('caption', '')
            
            elif 'interactive' in message_data:
                message_type = "interactive"
                interactive_data = message_data['interactive']
                content = json.dumps(interactive_data)
                metadata['interactive_type'] = interactive_data.get('type')
            
            elif 'button' in message_data:
                message_type = "button"
                button_data = message_data['button']
                content = button_data.get('text', '')
                metadata['button_payload'] = button_data.get('payload')
            
            else:
                # Unknown message type
                message_type = "unknown"
                content = json.dumps(message_data)
            
            return WhatsAppMessage(
                from_number=from_number,
                message_id=message_id,
                message_type=message_type,
                content=content,
                timestamp=timestamp,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"Message extraction error: {str(e)}")
            return None
    
    def _handle_text_message(self, message: WhatsAppMessage, 
                            assistant: CiviLinkAssistant, 
                            consent_manager: ConsentManager) -> Dict[str, Any]:
        """Handle text message"""
        try:
            # Process through assistant
            result = assistant.process_message(message.from_number, message.content, "text")
            
            return {
                "response_text": result.get("response", ""),
                "message_type": "text",
                "session_state": result.get("session_state"),
                "simplified_response": result.get("simplified_response"),
                "explanation_response": result.get("explanation_response")
            }
            
        except Exception as e:
            self.logger.error(f"Text message handling error: {str(e)}")
            return {"response_text": "I'm having trouble understanding. Could you please try again?", "message_type": "text"}
    
    def _handle_voice_message(self, message: WhatsAppMessage, 
                           assistant: CiviLinkAssistant, 
                           consent_manager: ConsentManager) -> Dict[str, Any]:
        """Handle voice/audio message"""
        try:
            # Download audio file
            audio_data = self._download_media(message.metadata.get('media_id'))
            
            if not audio_data:
                return {"response_text": "I couldn't download your voice message. Please try again.", "message_type": "text"}
            
            # Process through assistant (will use Whisper)
            result = assistant.process_message(message.from_number, audio_data, "voice")
            
            return {
                "response_text": result.get("response", ""),
                "message_type": "text",
                "session_state": result.get("session_state"),
                "transcription": result.get("transcription")
            }
            
        except Exception as e:
            self.logger.error(f"Voice message handling error: {str(e)}")
            return {"response_text": "I had trouble processing your voice message. Please type your message instead.", "message_type": "text"}
    
    def _handle_image_message(self, message: WhatsAppMessage, 
                            assistant: CiviLinkAssistant, 
                            consent_manager: ConsentManager) -> Dict[str, Any]:
        """Handle image message (for document processing)"""
        try:
            # Download image
            image_data = self._download_media(message.metadata.get('media_id'))
            
            if not image_data:
                return {"response_text": "I couldn't download your image. Please try again.", "message_type": "text"}
            
            # Process with OCR
            from ocr.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            
            ocr_result = processor.process_document(image_data)
            
            # Generate response based on OCR results
            if ocr_result.confidence > 0.6 and ocr_result.detected_fields:
                response_text = f"I found the following information:\\n"
                for field, value in ocr_result.detected_fields.items():
                    response_text += f"• {field.replace('_', ' ').title()}: {value}\\n"
                response_text += "\\nIs this correct?"
            else:
                response_text = "I couldn't clearly read the document. Could you please upload a clearer image or type the information?"
            
            return {
                "response_text": response_text,
                "message_type": "text",
                "ocr_result": {
                    "confidence": ocr_result.confidence,
                    "document_type": ocr_result.document_type,
                    "detected_fields": ocr_result.detected_fields
                }
            }
            
        except Exception as e:
            self.logger.error(f"Image message handling error: {str(e)}")
            return {"response_text": "I had trouble processing your image. Please try again or type the information.", "message_type": "text"}
    
    def _handle_document_message(self, message: WhatsAppMessage, 
                               assistant: CiviLinkAssistant, 
                               consent_manager: ConsentManager) -> Dict[str, Any]:
        """Handle document message"""
        try:
            # Download document
            doc_data = self._download_media(message.metadata.get('media_id'))
            
            if not doc_data:
                return {"response_text": "I couldn't download your document. Please try again.", "message_type": "text"}
            
            # For now, treat similar to image processing
            # In production, would handle PDFs and other document formats
            response_text = f"I received your document: {message.metadata.get('filename', 'document')}. I'm currently processing images best. For PDFs, please take a screenshot of the important pages."
            
            return {
                "response_text": response_text,
                "message_type": "text"
            }
            
        except Exception as e:
            self.logger.error(f"Document message handling error: {str(e)}")
            return {"response_text": "I had trouble processing your document. Please try again.", "message_type": "text"}
    
    def _handle_unsupported_message(self, message: WhatsAppMessage) -> Dict[str, Any]:
        """Handle unsupported message types"""
        return {
            "response_text": "I can only understand text messages, voice notes, and images right now. Please type your message or upload an image of your document.",
            "message_type": "text"
        }
    
    def _download_media(self, media_id: str) -> Optional[bytes]:
        """Download media file from WhatsApp servers"""
        try:
            # Get media URL
            url = f"https://graph.facebook.com/v18.0/{media_id}"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            media_data = response.json()
            
            # Download actual media file
            download_url = media_data.get('url')
            if not download_url:
                return None
            
            media_response = requests.get(download_url, headers=headers)
            media_response.raise_for_status()
            
            return media_response.content
            
        except Exception as e:
            self.logger.error(f"Media download error: {str(e)}")
            return None
    
    def _send_message(self, to_number: str, message_text: str, message_type: str = "text") -> bool:
        """Send message via WhatsApp API"""
        try:
            url = f"{self.base_url}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": message_type,
                message_type: {
                    "body": message_text
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            self.logger.info(f"Message sent to {to_number}: {message_text[:50]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Message sending error: {str(e)}")
            return False
    
    def send_interactive_message(self, to_number: str, header_text: str, 
                                body_text: str, buttons: list) -> bool:
        """Send interactive message with buttons"""
        try:
            url = f"{self.base_url}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "header": {
                        "type": "text",
                        "text": header_text
                    },
                    "body": {
                        "text": body_text
                    },
                    "action": {
                        "buttons": buttons
                    }
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Interactive message sending error: {str(e)}")
            return False
    
    def send_template_message(self, to_number: str, template_name: str, 
                             components: list) -> bool:
        """Send template message"""
        try:
            url = f"{self.base_url}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en"},
                    "components": components
                }
            }
            
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Template message sending error: {str(e)}")
            return False
