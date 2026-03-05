"""
Error Handling and Empathy Module
Provides structured error messages and empathetic responses
"""

import random
import logging
from typing import Dict, List, Optional
from enum import Enum

class EmotionalState(Enum):
    CONFUSED = "confused"
    FRUSTRATED = "frustrated"
    HESITANT = "hesitant"
    NEUTRAL = "neutral"
    CONFIDENT = "confident"

class EmpathyManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.responses = {
            "en": {
                EmotionalState.CONFUSED: [
                    "It's okay. I'm here to help you.",
                    "I understand this might seem confusing. Let me make it simpler.",
                    "Don't worry, we can take this step by step."
                ],
                EmotionalState.FRUSTRATED: [
                    "I apologize if this is difficult. Let's try a different way.",
                    "I'm sorry for the trouble. I'll do my best to help you finish this.",
                    "Let's take a deep breath. We can go slowly."
                ],
                EmotionalState.HESITANT: [
                    "Take your time. There's no rush.",
                    "I'm here to help at your pace.",
                    "It's completely fine to go slowly. What part should we look at again?"
                ],
                "error_general": [
                    "I'm not sure I understood that. Could you please clarify?",
                    "There seems to be a technical issue. Let's try again.",
                    "I apologize for the confusion. Let me rephrase that."
                ]
            },
            "ta": {
                EmotionalState.CONFUSED: [
                    "பரவாயில்லை. நான் உங்களுக்கு உதவ இங்கே இருக்கிறேன்.",
                    "இது குழப்பமாகத் தோன்றலாம் என்று எனக்குப் புரிகிறது. இதை எளிதாக்குகிறேன்.",
                    "கவலைப்பட வேண்டாம், நாம் இதை படிப்படியாகச் செய்யலாம்."
                ],
                EmotionalState.FRUSTRATED: [
                    "இது கடினமாக இருந்தால் மன்னிக்கவும். வேறு வழியில் முயற்சிப்போம்.",
                    "சிரமத்திற்கு வருந்துகிறேன். இதை முடிக்க உங்களுக்கு உதவ என்னால் முடிந்த அனைத்தையும் செய்வேன்.",
                    "மெதுவாகச் செல்வோம், கவலைப்பட வேண்டாம்."
                ],
                "error_general": [
                    "நீங்கள் சொன்னது எனக்குப் புரியவில்லை. தயவுசெய்து விளக்க முடியுமா?",
                    "தொழில்நுட்ப சிக்கல் இருப்பது போல் தெரிகிறது. மீண்டும் முயற்சிப்போம்.",
                    "குழப்பத்திற்கு வருந்துகிறேன். நான் அதை வேறு விதமாகச் சொல்கிறேன்."
                ]
            },
            "hi": {
                EmotionalState.CONFUSED: [
                    "कोई बात नहीं। मैं यहाँ आपकी मदद के लिए हूँ।",
                    "मैं समझ सकता हूँ कि यह भ्रमित करने वाला लग सकता है। मैं इसे और सरल बना देता हूँ।",
                    "चिंता न करें, हम इसे चरण दर चरण कर सकते हैं।"
                ],
                EmotionalState.FRUSTRATED: [
                    "अगर यह कठिन है तो मैं क्षमा चाहता हूँ। चलिए एक अलग तरीका आज़माते हैं।",
                    "परेशानी के लिए खेद है। मैं इसे पूरा करने में आपकी मदद करने की पूरी कोशिश करूँगा।",
                    "गहरी सांस लें। हम धीरे-धीरे आगे बढ़ सकते हैं।"
                ],
                "error_general": [
                    "मुझे यकीन नहीं है कि मैं इसे समझ पाया। क्या आप कृपया स्पष्ट कर सकते हैं?",
                    "ऐसा लगता है कि कोई तकनीकी समस्या है। चलिए फिर से कोशिश करते हैं।",
                    "उलझन के लिए क्षमा करें। मैं इसे फिर से कहता हूँ।"
                ]
            }
        }

    def get_empathetic_response(self, state: EmotionalState, language: str = "en") -> str:
        """Get an empathetic response based on the user's emotional state."""
        lang_responses = self.responses.get(language, self.responses["en"])
        state_responses = lang_responses.get(state, lang_responses[EmotionalState.CONFUSED])
        return random.choice(state_responses)

    def get_error_message(self, error_type: str = "general", language: str = "en") -> str:
        """Get a user-friendly error message."""
        lang_responses = self.responses.get(language, self.responses["en"])
        error_key = f"error_{error_type}"
        error_responses = lang_responses.get(error_key, lang_responses["error_general"])
        return random.choice(error_responses)
