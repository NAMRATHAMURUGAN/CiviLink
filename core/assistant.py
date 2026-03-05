"""
CiviLink Core Assistant
Accessibility-first, privacy-focused government services assistant
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import re
import logging
from core.llm_intent_detector import LLMIntentDetector, IntentType, AssistanceLevel, IntentResult
from multilingual.multilingual_llm import MultilingualLLM, MultilingualResponse

class IntentType(Enum):
    WIDOW_PENSION = "widow_pension"
    SCHOLARSHIP = "scholarship"
    CERTIFICATE_APPLICATION = "certificate_application"
    UNKNOWN = "unknown"

class AssistanceMode(Enum):
    NORMAL = "normal"
    SIMPLIFIED = "simplified"
    EXPLANATION = "explanation"

@dataclass
class UserSession:
    user_id: str
    language: str = "en"
    assistance_mode: AssistanceMode = AssistanceMode.NORMAL
    consent_given: bool = False
    current_workflow: Optional[str] = None
    collected_fields: Dict[str, Any] = None
    current_step: int = 0
    needs_explanation: bool = False
    
    def __post_init__(self):
        if self.collected_fields is None:
            self.collected_fields = {}

class CiviLinkAssistant:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sessions: Dict[str, UserSession] = {}
        
        # Initialize LLM components
        self.intent_detector = LLMIntentDetector()
        self.multilingual_llm = MultilingualLLM()
        
        # Legacy patterns for fallback
        self.intent_patterns = self._load_intent_patterns()
        self.empathy_responses = self._load_empathy_responses()
        
    def _load_intent_patterns(self) -> Dict[IntentType, List[str]]:
        """Load patterns for intent detection"""
        return {
            IntentType.WIDOW_PENSION: [
                r'widow.*pension', r'pension.*widow', r'विधवा.*पेंशन', 
                r'விதவை.*ஓயவூதியம்', r'husband.*passed.*away'
            ],
            IntentType.SCHOLARSHIP: [
                r'scholarship', r'education.*grant', r'student.*aid',
                r'छात्रवृत्ति', r'கல்வி.*உதவி', r'study.*fund'
            ],
            IntentType.CERTIFICATE_APPLICATION: [
                r'certificate', r'birth.*certificate', r'death.*certificate',
                r'marriage.*certificate', r'प्रमाणपत्र', r'சான்றிதழ்'
            ]
        }
    
    def _load_empathy_responses(self) -> Dict[str, List[str]]:
        """Load empathetic response templates"""
        return {
            'confusion': [
                "It's okay. I'm here to help you.",
                "Don't worry. We can take this step by step.",
                "I understand this might seem confusing. Let me make it simpler."
            ],
            'hesitation': [
                "Take your time. There's no rush.",
                "It's completely fine to go slowly.",
                "I'm here to help at your pace."
            ],
            'error': [
                "I'm not sure I understood that. Could you please clarify?",
                "There seems to be a technical issue. Let's try again.",
                "I apologize for the confusion. Let me rephrase that."
            ]
        }
    
    def detect_intent(self, message: str, user_id: str) -> IntentResult:
        """Detect user intent using LLM with fallback to patterns"""
        try:
            # Get user context for better LLM understanding
            session = self.get_or_create_session(user_id)
            user_context = {
                "language": session.language,
                "assistance_mode": session.assistance_mode.value,
                "current_workflow": session.current_workflow,
                "consent_given": session.consent_given
            }
            
            # Use LLM for primary intent detection
            intent_result = self.intent_detector.detect_intent(message, user_context)
            
            # Update session with detected information
            session.language = intent_result.language
            if intent_result.assistance_level == AssistanceLevel.SIMPLIFIED:
                session.assistance_mode = AssistanceMode.SIMPLIFIED
            elif intent_result.assistance_level == AssistanceLevel.EXPLANATION:
                session.assistance_mode = AssistanceMode.EXPLANATION
            
            self.logger.info(f"LLM detected intent: {intent_result.intent.value} for user {user_id}")
            return intent_result
            
        except Exception as e:
            self.logger.error(f"LLM intent detection failed, using fallback: {str(e)}")
            # Fallback to pattern-based detection
            legacy_intent = self._fallback_intent_detection(message)
            return IntentResult(
                intent=legacy_intent,
                confidence=0.5,
                language="en",
                assistance_level=AssistanceLevel.NORMAL,
                entities={}
            )
    
    def _fallback_intent_detection(self, message: str) -> IntentType:
        """Fallback intent detection using regex patterns"""
        message_lower = message.lower()
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent_type
        
        return IntentType.UNKNOWN
    
    def detect_assistance_mode(self, message: str, session: UserSession) -> AssistanceMode:
        """Detect if user needs simplified assistance"""
        confusion_indicators = [
            "confused", "don't understand", "not clear", "difficult",
            "confused", "समझ नहीं आ रहा", "புரியவில்லை", "explain simple"
        ]
        
        elderly_indicators = [
            "elderly", "senior", "old age", "slow", "बूढ़ा", "வயதான"
        ]
        
        simplification_requests = [
            "explain simple", "make it simple", "easy words", 
            "simple language", "आसान भाषा", "எளிய மொழி"
        ]
        
        message_lower = message.lower()
        
        if any(indicator in message_lower for indicator in confusion_indicators + elderly_indicators + simplification_requests):
            return AssistanceMode.SIMPLIFIED
        
        if session.needs_explanation or "explain" in message_lower:
            return AssistanceMode.EXPLANATION
            
        return AssistanceMode.NORMAL
    
    def get_or_create_session(self, user_id: str) -> UserSession:
        """Get existing session or create new one"""
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession(user_id=user_id)
        return self.sessions[user_id]
    
    def format_response(self, message: str, session: UserSession) -> str:
        """Format response based on assistance mode and language"""
        if session.assistance_mode == AssistanceMode.SIMPLIFIED:
            message = self._simplify_language(message)
        
        # Add empathetic prefix if user seems confused
        if session.assistance_mode in [AssistanceMode.SIMPLIFIED, AssistanceMode.EXPLANATION]:
            empathy_prefix = "I'm here to help you. "
            message = empathy_prefix + message
        
        return message
    
    def _simplify_language(self, message: str) -> str:
        """Simplify complex language"""
        simplifications = {
            "Please provide": "Please tell me",
            "residential address": "home address",
            "authentication": "verification",
            "application": "form",
            "submit": "send",
            "process": "help you with"
        }
        
        for complex_term, simple_term in simplifications.items():
            message = message.replace(complex_term, simple_term)
        
        # Break into shorter sentences
        sentences = message.split('. ')
        if len(sentences) > 2:
            message = '. '.join(sentences[:2]) + '.'
        
        return message
    
    def get_empathetic_response(self, situation: str) -> str:
        """Get empathetic response for specific situations"""
        if situation in self.empathy_responses:
            import random
            return random.choice(self.empathy_responses[situation])
        return "I'm here to help you."
    
    def validate_consent(self, user_id: str) -> bool:
        """Check if user has given consent for processing"""
        session = self.get_or_create_session(user_id)
        return session.consent_given
    
    def request_consent(self, language: str = "en") -> str:
        """Request user consent for data processing"""
        consent_messages = {
            "en": "Do you consent to EmpowerAbility processing your personal information for application assistance?",
            "ta": "விண்ணப்ப உதவிக்கு உங்கள் தனிப்பட்ட தகவலை EmpowerAbility செயலாற்ற ஒப்புக்கொள்கிறீர்களா?",
            "hi": "क्या आप आवेदन सहायता के लिए EmpowerAbility द्वारा आपकी व्यक्तिगत जानकारी को संसाधित करने के लिए सहमत हैं?"
        }
        return consent_messages.get(language, consent_messages["en"])
    
    def get_next_question(self, session: UserSession) -> Optional[str]:
        """Get next question based on workflow and collected fields"""
        if not session.current_workflow:
            return None
        
        # This will be implemented when we create workflow templates
        return "What is your full name?"
    
    def process_message(self, user_id: str, message: Any, message_type: str = "text") -> Dict[str, Any]:
        """Main message processing pipeline with LLM integration"""
        session = self.get_or_create_session(user_id)
        
        # Handle voice messages (Whisper)
        if message_type in ["voice", "voice_url"]:
            from .whisper_stt import WhisperSTT
            whisper = WhisperSTT()
            
            audio_data = None
            if message_type == "voice_url":
                import requests
                response = requests.get(message)
                if response.status_code == 200:
                    audio_data = response.content
            else:
                audio_data = message

            if audio_data:
                transcribed_text, detected_lang = whisper.transcribe_audio(audio_data)
                if transcribed_text:
                    message = transcribed_text
                    if detected_lang:
                        session.language = detected_lang
                else:
                    return {
                        "response": self.format_response("I couldn't understand the audio. Could you please type your message?", session),
                        "session_state": "voice_processing_failed"
                    }
            else:
                return {
                    "response": self.format_response("I couldn't retrieve the audio message. Could you please try again?", session),
                    "session_state": "voice_retrieval_failed"
                }
        
        # Detect intent using LLM
        intent_result = self.detect_intent(message, user_id)
        
        # Check consent first
        if not session.consent_given:
            if "yes" in message.lower() or "agree" in message.lower() or "சம்மதம்" in message or "हाँ" in message:
                session.consent_given = True
                response = self.multilingual_llm.generate_response(
                    message=message,
                    intent="consent_given",
                    language=session.language,
                    assistance_level=session.assistance_mode.value
                )
                return {
                    "response": response.text,
                    "session_state": "consent_given",
                    "language": session.language
                }
            elif "no" in message.lower() or "disagree" in message.lower():
                response = self.multilingual_llm.generate_response(
                    message=message,
                    intent="consent_denied",
                    language=session.language,
                    assistance_level=session.assistance_mode.value
                )
                return {
                    "response": response.text,
                    "session_state": "consent_denied"
                }
            else:
                consent_msg = self.request_consent(session.language)
                return {
                    "response": consent_msg,
                    "session_state": "awaiting_consent"
                }
        
        # Handle workflow initialization or continuation
        if not session.current_workflow:
            if intent_result.intent == IntentType.UNKNOWN:
                response = self.multilingual_llm.generate_response(
                    message=message,
                    intent="intent_clarification",
                    language=session.language,
                    assistance_level=session.assistance_mode.value
                )
                return {
                    "response": response.text,
                    "session_state": "intent_clarification_needed"
                }
            else:
                session.current_workflow = intent_result.intent.value
                response = self.multilingual_llm.generate_response(
                    message=message,
                    intent=f"workflow_start_{intent_result.intent.value}",
                    language=session.language,
                    assistance_level=session.assistance_mode.value,
                    context={"workflow": intent_result.intent.value}
                )
                return {
                    "response": response.text,
                    "session_state": "workflow_initialized",
                    "current_workflow": session.current_workflow,
                    "next_question": self.get_next_question(session)
                }
        
        # Continue workflow
        next_question = self.get_next_question(session)
        if next_question:
            # Generate contextual response using LLM
            response = self.multilingual_llm.generate_response(
                message=message,
                intent="workflow_question",
                language=session.language,
                assistance_level=session.assistance_mode.value,
                context={
                    "workflow": session.current_workflow,
                    "current_step": session.current_step,
                    "next_question": next_question,
                    "collected_fields": session.collected_fields
                }
            )
            
            return {
                "response": response.text,
                "session_state": "workflow_in_progress",
                "simplified_response": response.simplified_version,
                "explanation_response": response.explanation_version
            }
        
        # Default ready state
        response = self.multilingual_llm.generate_response(
            message=message,
            intent="ready",
            language=session.language,
            assistance_level=session.assistance_mode.value
        )
        
        return {
            "response": response.text,
            "session_state": "ready"
        }
