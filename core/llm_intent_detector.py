"""
LLM-based Intent Detection
Uses GPT-4 for advanced intent detection and multilingual understanding
"""

import openai
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import os
from dotenv import load_dotenv

load_dotenv()

class IntentType(Enum):
    WIDOW_PENSION = "widow_pension"
    SCHOLARSHIP = "scholarship"
    CERTIFICATE_APPLICATION = "certificate_application"
    GENERAL_INQUIRY = "general_inquiry"
    DOCUMENT_UPLOAD = "document_upload"
    AUTHENTICATION = "authentication"
    UNKNOWN = "unknown"

class AssistanceLevel(Enum):
    NORMAL = "normal"
    SIMPLIFIED = "simplified"
    EXPLANATION = "explanation"
    CONFUSED = "confused"

@dataclass
class IntentResult:
    intent: IntentType
    confidence: float
    language: str
    assistance_level: AssistanceLevel
    entities: Dict[str, str]
    emotional_state: Optional[str] = None

class LLMIntentDetector:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.logger = logging.getLogger(__name__)
        
        self.system_prompt = """You are CiviLink, an AI assistant for government services. Your task is to analyze user messages and detect:

1. **Intent**: What government service the user needs
2. **Language**: The language the user is speaking (en, ta, hi)
3. **Assistance Level**: Whether user needs normal, simplified, or detailed explanations
4. **Entities**: Key information like names, numbers, dates
5. **Emotional State**: Whether user seems confused, frustrated, confident, etc.

Supported intents:
- widow_pension: Widow pension applications
- scholarship: Scholarship applications  
- certificate_application: Birth/death/marriage certificates
- general_inquiry: General questions about services
- document_upload: User wants to upload documents
- authentication: Login/verification related
- unknown: Cannot determine intent

Assistance levels:
- normal: User understands well
- simplified: User needs simpler language
- explanation: User wants detailed explanations
- confused: User seems lost or overwhelmed

Respond in JSON format:
{
    "intent": "intent_name",
    "confidence": 0.95,
    "language": "en",
    "assistance_level": "normal",
    "entities": {"name": "John Doe", "aadhaar": "123456789012"},
    "emotional_state": "confident"
}

Be empathetic and accessibility-focused in your analysis."""

    def detect_intent(self, message: str, user_context: Optional[Dict] = None) -> IntentResult:
        """Detect intent using GPT-4"""
        try:
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Analyze this message: '{message}'"}
            ]
            
            if user_context:
                context_msg = f"User context: {json.dumps(user_context, indent=2)}"
                messages.append({"role": "system", "content": context_msg})
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON response
            try:
                result_data = json.loads(result_text)
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                result_data = self._fallback_parse(result_text)
            
            return IntentResult(
                intent=IntentType(result_data.get("intent", "unknown")),
                confidence=float(result_data.get("confidence", 0.5)),
                language=result_data.get("language", "en"),
                assistance_level=AssistanceLevel(result_data.get("assistance_level", "normal")),
                entities=result_data.get("entities", {}),
                emotional_state=result_data.get("emotional_state")
            )
            
        except Exception as e:
            self.logger.error(f"LLM intent detection failed: {str(e)}")
            return self._fallback_intent_detection(message)
    
    def _fallback_parse(self, response_text: str) -> Dict:
        """Fallback parsing if JSON fails"""
        # Simple keyword-based fallback
        response_lower = response_text.lower()
        
        intent = "unknown"
        if "widow" in response_lower or "pension" in response_lower:
            intent = "widow_pension"
        elif "scholarship" in response_lower or "education" in response_lower:
            intent = "scholarship"
        elif "certificate" in response_lower:
            intent = "certificate_application"
        elif "document" in response_lower or "upload" in response_lower:
            intent = "document_upload"
        elif "login" in response_lower or "verify" in response_lower:
            intent = "authentication"
        else:
            intent = "general_inquiry"
        
        language = "en"
        if any(word in response_lower for word in ["தமிழ்", "தமிழர்", "வணக்கம்"]):
            language = "ta"
        elif any(word in response_lower for word in ["हिंदी", "नमस्ते", "भारत"]):
            language = "hi"
        
        assistance_level = "normal"
        if any(word in response_lower for word in ["confused", "difficult", "don't understand"]):
            assistance_level = "simplified"
        elif "explain" in response_lower:
            assistance_level = "explanation"
        
        return {
            "intent": intent,
            "confidence": 0.6,
            "language": language,
            "assistance_level": assistance_level,
            "entities": {},
            "emotional_state": "neutral"
        }
    
    def _fallback_intent_detection(self, message: str) -> IntentResult:
        """Simple rule-based fallback"""
        message_lower = message.lower()
        
        intent = IntentType.UNKNOWN
        if "widow" in message_lower and "pension" in message_lower:
            intent = IntentType.WIDOW_PENSION
        elif "scholarship" in message_lower or "education" in message_lower:
            intent = IntentType.SCHOLARSHIP
        elif "certificate" in message_lower:
            intent = IntentType.CERTIFICATE_APPLICATION
        
        return IntentResult(
            intent=intent,
            confidence=0.4,
            language="en",
            assistance_level=AssistanceLevel.NORMAL,
            entities={}
        )
    
    def generate_response_suggestion(self, intent_result: IntentResult, message: str) -> str:
        """Generate appropriate response based on intent and emotional state"""
        try:
            prompt = f"""Based on this analysis:
Intent: {intent_result.intent.value}
Language: {intent_result.language}
Assistance Level: {intent_result.assistance_level.value}
Emotional State: {intent_result.emotional_state}
User message: "{message}"

Generate an empathetic, accessible response in {intent_result.language} that:
1. Acknowledges their emotional state
2. Uses appropriate complexity level
3. Guides them to the next step
4. Maintains CiviLink's caring tone

Keep it concise and supportive."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are CiviLink, an empathetic government services assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {str(e)}")
            return self._get_fallback_response(intent_result)
    
    def _get_fallback_response(self, intent_result: IntentResult) -> str:
        """Fallback response generation"""
        responses = {
            "en": {
                IntentType.WIDOW_PENSION: "I can help you with the widow pension application. Let's start step by step.",
                IntentType.SCHOLARSHIP: "I'd be happy to help you with scholarship applications.",
                IntentType.UNKNOWN: "I'm here to help. Could you tell me which government service you need assistance with?"
            },
            "ta": {
                IntentType.WIDOW_PENSION: "நான் உங்களுக்கு விதவை ஓயவூதிய விண்ணப்பத்தில் உதவ முடியும். படிப்படியாக தொடர்வோம்.",
                IntentType.SCHOLARSHIP: "உங்களுக்கு கல்வி உதவித்தொகை விண்ணப்பங்களில் உதவ மகிழும்.",
                IntentType.UNKNOWN: "நான் உதவ இங்கு இருக்கிறேன். நீங்கள் எந்த அரசு சேவையில் உதவி தேவை என்று சொல்ல முடியுமா?"
            },
            "hi": {
                IntentType.WIDOW_PENSION: "मैं आपकी विधवा पेंशन आवेदन में मदद कर सकता हूं। चलिए चरण दर चरण शुरू करते हैं।",
                IntentType.SCHOLARSHIP: "मैं छात्रवृत्ति आवेदनों में आपकी सहायता करने में प्रसन्न हूं।",
                IntentType.UNKNOWN: "मैं मदद करने के लिए यहां हूं। क्या आप बता सकते हैं कि आपको किस सरकारी सेवा में सहायता की आवश्यकता है?"
            }
        }
        
        lang_responses = responses.get(intent_result.language, responses["en"])
        return lang_responses.get(intent_result.intent, lang_responses[IntentType.UNKNOWN])
