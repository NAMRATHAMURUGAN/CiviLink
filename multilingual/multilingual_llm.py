"""
Multilingual LLM Support
Uses GPT-4 for high-quality multilingual understanding and response generation
"""

import openai
import logging
import json
import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class MultilingualResponse:
    text: str
    language: str
    confidence: float
    simplified_version: Optional[str] = None
    explanation_version: Optional[str] = None

class MultilingualLLM:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4")
        self.logger = logging.getLogger(__name__)
        
        self.supported_languages = {
            "en": {"name": "English", "direction": "ltr"},
            "ta": {"name": "Tamil", "direction": "ltr"}, 
            "hi": {"name": "Hindi", "direction": "ltr"}
        }
        
        self.system_prompt = """You are CiviLink, a multilingual government services assistant. Your role is to:

1. **Understand** the user's language and intent perfectly
2. **Respond** in the same language the user is speaking
3. **Adapt** complexity based on user's understanding level
4. **Maintain** empathy and accessibility in all languages
5. **Preserve** meaning - never loosely translate important terms

Guidelines:
- Use natural, conversational language
- Avoid overly formal or bureaucratic language
- For Tamil and Hindi, use commonly understood terms
- Keep sentences short and clear
- Maintain the same caring tone across all languages
- For government terms, use the official terminology in that language

Always respond in the detected user language."""

    def detect_language(self, text: str) -> Tuple[str, float]:
        """Detect language with confidence score"""
        try:
            messages = [
                {"role": "system", "content": "Detect the language of this text. Respond with only the language code: en, ta, or hi."},
                {"role": "user", "content": text}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=10
            )
            
            detected_lang = response.choices[0].message.content.strip().lower()
            
            # Validate language code
            if detected_lang not in self.supported_languages:
                detected_lang = "en"  # Default to English
            
            confidence = 0.9 if detected_lang != "en" else 0.8  # Higher confidence for non-English
            
            return detected_lang, confidence
            
        except Exception as e:
            self.logger.error(f"Language detection failed: {str(e)}")
            return self._fallback_language_detection(text)
    
    def _fallback_language_detection(self, text: str) -> Tuple[str, float]:
        """Fallback language detection using simple patterns"""
        text_lower = text.lower()
        
        # Tamil indicators
        tamil_indicators = [
            "தமிழ்", "வணக்கம்", "நன்றி", "எப்படி", "என்ன", "எங்கே", 
            "யார்", "எப்போது", "ஏன்", "எவ்வளவு", "உதவி", "சேவை"
        ]
        
        # Hindi indicators  
        hindi_indicators = [
            "हिंदी", "नमस्ते", "धन्यवाद", "कैसे", "क्या", "कहां", "कौन",
            "कब", "क्यों", "कितना", "मदद", "सेवा", "आवेदन"
        ]
        
        tamil_score = sum(1 for indicator in tamil_indicators if indicator in text_lower)
        hindi_score = sum(1 for indicator in hindi_indicators if indicator in text_lower)
        
        if tamil_score > hindi_score and tamil_score > 0:
            return "ta", 0.7
        elif hindi_score > 0:
            return "hi", 0.7
        else:
            return "en", 0.6
    
    def generate_response(
        self, 
        user_message: str, 
        intent: str, 
        language: str, 
        assistance_level: str = "normal",
        context: Optional[Dict] = None
    ) -> MultilingualResponse:
        """Generate contextually appropriate response in user's language"""
        
        try:
            # Build context-aware prompt
            context_info = ""
            if context:
                context_info = f"\\nContext: {json.dumps(context, indent=2)}"
            
            assistance_instruction = self._get_assistance_instruction(assistance_level, language)
            
            prompt = f"""User message: "{user_message}"
Detected intent: {intent}
Language: {language}
Assistance level: {assistance_level}{context_info}

{assistance_instruction}

Generate a response that:
1. Is in {self.supported_languages[language]['name']}
2. Matches the assistance level
3. Is empathetic and supportive
4. Guides the user to the next step
5. Maintains CiviLink's accessibility-first approach"""

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )
            
            main_response = response.choices[0].message.content.strip()
            
            # Generate simplified and explanation versions if needed
            simplified = None
            explanation = None
            
            if assistance_level in ["simplified", "explanation"]:
                simplified = self._generate_simplified_version(main_response, language)
            
            if assistance_level == "explanation":
                explanation = self._generate_explanation_version(main_response, intent, language)
            
            return MultilingualResponse(
                text=main_response,
                language=language,
                confidence=0.9,
                simplified_version=simplified,
                explanation_version=explanation
            )
            
        except Exception as e:
            self.logger.error(f"Response generation failed: {str(e)}")
            return self._get_fallback_response(intent, language, assistance_level)
    
    def _get_assistance_instruction(self, level: str, language: str) -> str:
        """Get specific instructions for assistance level"""
        instructions = {
            "normal": "Use clear, standard language. Be direct but empathetic.",
            "simplified": "Use very simple words. Short sentences. Avoid technical terms. Provide examples.",
            "explanation": "Provide detailed explanations. Break down complex concepts. Use analogies if helpful."
        }
        
        base_instruction = instructions.get(level, instructions["normal"])
        
        language_specific = {
            "ta": " Use natural Tamil that elderly people can easily understand.",
            "hi": " Use simple, clear Hindi that is commonly spoken.",
            "en": " Use clear, accessible English."
        }
        
        return base_instruction + language_specific.get(language, "")
    
    def _generate_simplified_version(self, original_response: str, language: str) -> str:
        """Generate a simplified version of the response"""
        try:
            prompt = f"""Simplify this response for someone who has difficulty understanding:
Original: "{original_response}"
Language: {language}

Make it:
- Much simpler
- Very short sentences
- Easy words only
- Step-by-step if possible"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You simplify complex text for accessibility."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Simplification failed: {str(e)}")
            return original_response
    
    def _generate_explanation_version(self, original_response: str, intent: str, language: str) -> str:
        """Generate a detailed explanation version"""
        try:
            prompt = f"""Provide a detailed explanation for this response:
Original: "{original_response}"
Intent: {intent}
Language: {language}

Add:
- Why this step is needed
- What happens next
- Helpful tips or warnings
- Background information if relevant"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You provide detailed, educational explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Explanation generation failed: {str(e)}")
            return original_response
    
    def _get_fallback_response(self, intent: str, language: str, assistance_level: str) -> MultilingualResponse:
        """Fallback response generation"""
        fallback_responses = {
            "en": {
                "widow_pension": "I can help you with widow pension. Let's go step by step.",
                "scholarship": "I can help you with scholarship applications.",
                "certificate_application": "I can help you with certificate applications.",
                "unknown": "I'm here to help. What government service do you need?"
            },
            "ta": {
                "widow_pension": "நான் உங்களுக்கு விதவை ஓயவூதியத்தில் உதவ முடியும். படிப்படியாக செல்வோம்.",
                "scholarship": "நான் உங்களுக்கு கல்வி உதவித்தொகை விண்ணப்பங்களில் உதவ முடியும்.",
                "certificate_application": "நான் உங்களுக்கு சான்றிதழ் விண்ணப்பங்களில் உதவ முடியும்.",
                "unknown": "நான் உதவ இங்கு இருக்கிறேன். நீங்கள் எந்த அரசு சேவை தேவை?"
            },
            "hi": {
                "widow_pension": "मैं आपकी विधवा पेंशन में मदद कर सकता हूं। चलिए धीरे-धीरे करते हैं।",
                "scholarship": "मैं आपकी छात्रवृत्ति आवेदनों में मदद कर सकता हूं।",
                "certificate_application": "मैं आपके प्रमाण पत्र आवेदनों में मदद कर सकता हूं।",
                "unknown": "मैं मदद करने के लिए यहां हूं। आपको कौन सी सरकारी सेवा चाहिए?"
            }
        }
        
        lang_responses = fallback_responses.get(language, fallback_responses["en"])
        response_text = lang_responses.get(intent, lang_responses["unknown"])
        
        return MultilingualResponse(
            text=response_text,
            language=language,
            confidence=0.5
        )
    
    def translate_text(self, text: str, target_language: str) -> Optional[str]:
        """Translate text to target language using LLM"""
        if target_language not in self.supported_languages:
            return None
        
        try:
            prompt = f"""Translate this text to {self.supported_languages[target_language]['name']}.
Keep the meaning exactly the same. Use natural, conversational language.
Text: "{text}" """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator specializing in government services."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=400
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Translation failed: {str(e)}")
            return None
    
    def validate_response_quality(self, response: str, language: str) -> Tuple[bool, str]:
        """Validate response quality and appropriateness"""
        try:
            prompt = f"""Review this {self.supported_languages[language]['name']} response for:
1. Clarity and simplicity
2. Empathy and tone
3. Accuracy for government services
4. Cultural appropriateness

Response: "{response}"

Respond with only: "GOOD" or "NEEDS_IMPROVEMENT" and a brief reason."""

            validation_response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a quality assurance specialist for government services."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            result = validation_response.choices[0].message.content.strip()
            
            if result.startswith("GOOD"):
                return True, "Response meets quality standards"
            else:
                return False, result.replace("NEEDS_IMPROVEMENT", "").strip()
                
        except Exception as e:
            self.logger.error(f"Quality validation failed: {str(e)}")
            return True, "Validation unavailable"
