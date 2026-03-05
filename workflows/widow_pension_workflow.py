"""
Widow Pension Workflow
Handles the application process for widow pension schemes
"""

from typing import Dict, List, Any
from .base_workflow import BaseWorkflow, FieldDefinition, DocumentRequirement, FieldType

class WidowPensionWorkflow(BaseWorkflow):
    def define_fields(self) -> List[FieldDefinition]:
        return [
            FieldDefinition(
                name="full_name",
                field_type=FieldType.TEXT,
                help_text="Enter your name as it appears on official documents",
                example="Rani Sharma",
                multilingual_help={
                    "ta": "அதிகாரப்பூர்வ ஆவணங்களில் காணப்படும் பெயரை உள்ளிடவும்",
                    "hi": "आधिकारिक दस्तावेजों में दिखाई देने वाला नाम दर्ज करें"
                }
            ),
            FieldDefinition(
                name="aadhaar_number",
                field_type=FieldType.AADHAAR,
                help_text="12-digit unique identification number",
                example="123456789012",
                multilingual_help={
                    "ta": "12-இலக்க தனித்துவ அடையாரம் எண்",
                    "hi": "12 अंकों की विशिष्ट पहचान संख्या"
                }
            ),
            FieldDefinition(
                name="date_of_birth",
                field_type=FieldType.DATE,
                help_text="Your date of birth as per records",
                example="15/08/1965",
                multilingual_help={
                    "ta": "பதிவுகளின்படி உங்கள் பிறந்த தேதி",
                    "hi": "रिकॉर्ड के अनुसार आपकी जन्म तिथि"
                }
            ),
            FieldDefinition(
                name="phone_number",
                field_type=FieldType.PHONE,
                help_text="10-digit mobile number for communication",
                example="9876543210",
                multilingual_help={
                    "ta": "தொடர்புக்கான 10-இலக்க மொபைல் எண்",
                    "hi": "संचार के लिए 10 अंकों का मोबाइल नंबर"
                }
            ),
            FieldDefinition(
                name="address",
                field_type=FieldType.ADDRESS,
                help_text="Complete residential address with PIN code",
                example="12 Gandhi Street, Chennai - 600001",
                multilingual_help={
                    "ta": "பின் குறியீடு உட்பட முழு குடியிருப்பு முகவரி",
                    "hi": "पिन कोड सहित पूरा आवासीय पता"
                }
            ),
            FieldDefinition(
                name="bank_account_number",
                field_type=FieldType.BANK_ACCOUNT,
                help_text="Bank account number for pension direct transfer",
                example="1234567890123456",
                multilingual_help={
                    "ta": "ஓயவூதியம் நேரடி பரிமாற்றத்திற்கான வங்கி கணக்கு எண்",
                    "hi": "पेंशन सीधे ट्रांसफर के लिए बैंक खाता नंबर"
                }
            ),
            FieldDefinition(
                name="bank_name",
                field_type=FieldType.TEXT,
                help_text="Name of your bank branch",
                example="State Bank of India, Main Branch",
                multilingual_help={
                    "ta": "உங்கள் வங்கி கிளையின் பெயர்",
                    "hi": "आपके बैंक शाखा का नाम"
                }
            ),
            FieldDefinition(
                name="ifsc_code",
                field_type=FieldType.TEXT,
                validation_pattern=r'^[A-Z]{4}0[A-Z0-9]{6}$',
                help_text="IFSC code of your bank branch",
                example="SBIN0001234",
                multilingual_help={
                    "ta": "உங்கள் வங்கி கிளையின் IFSC குறியீடு",
                    "hi": "आपके बैंक शाखा का IFSC कोड"
                }
            ),
            FieldDefinition(
                name="husband_death_date",
                field_type=FieldType.DATE,
                help_text="Date of death of your husband",
                example="01/01/2023",
                multilingual_help={
                    "ta": "உங்கள் கணவரின் மரண தேதி",
                    "hi": "आपके पति की मृत्यु तिथि"
                }
            ),
            FieldDefinition(
                name="annual_income",
                field_type=FieldType.NUMBER,
                help_text="Your annual family income in rupees",
                example="120000",
                multilingual_help={
                    "ta": "உங்கள் ஆண்டு குடும்ப வருமானம் ரூபாயில்",
                    "hi": "आपकी वार्षिक पारिवारिक आय रुपयों में"
                }
            )
        ]
    
    def define_documents(self) -> List[DocumentRequirement]:
        return [
            DocumentRequirement(
                name="aadhaar_card",
                description="Applicant's Aadhaar card",
                ocr_fields=["full_name", "aadhaar_number", "date_of_birth", "address"],
                multilingual_description={
                    "ta": "விண்ணப்பதாரரின் ஆதார் அட்டை",
                    "hi": "आवेदक का आधार कार्ड"
                }
            ),
            DocumentRequirement(
                name="death_certificate",
                description="Death certificate of husband",
                ocr_fields=["husband_death_date"],
                multilingual_description={
                    "ta": "கணவரின் மரண சான்றிதழ்",
                    "hi": "पति की मृत्यु प्रमाण पत्र"
                }
            ),
            DocumentRequirement(
                name="bank_passbook",
                description="First page of bank passbook",
                ocr_fields=["bank_account_number", "bank_name", "ifsc_code"],
                multilingual_description={
                    "ta": "வங்கி கடவுச்சீட்டின் முதல் பக்கம்",
                    "hi": "बैंक पासबुक का पहला पृष्ठ"
                }
            ),
            DocumentRequirement(
                name="income_certificate",
                description="Income certificate (if available)",
                ocr_fields=["annual_income"],
                required=False,
                multilingual_description={
                    "ta": "வருமானச் சான்றிதழ் (இருந்தால்)",
                    "hi": "आय प्रमाण पत्र (यदि उपलब्ध हो)"
                }
            )
        ]
    
    def define_validation_rules(self) -> Dict[str, Any]:
        return {
            "age_min": 18,
            "age_max": 80,
            "income_max": 300000,  # Maximum annual income for eligibility
            "required_documents": ["aadhaar_card", "death_certificate", "bank_passbook"],
            "eligibility_checks": {
                "widow_status": True,
                "income_limit": True,
                "residency": True
            }
        }
    
    def define_submission_endpoint(self) -> str:
        return "/api/widow-pension/submit"
    
    def get_workflow_description(self, language: str = "en") -> str:
        descriptions = {
            "en": "I'll help you apply for the Widow Pension Scheme. This pension provides financial assistance to widows who have lost their husband. We'll need to collect your personal details, documents, and bank information for processing.",
            "ta": "நான் உங்களுக்கு விதவை ஓயவூதியத் திட்டத்திற்கு விண்ணப்பிக்க உதவுவேன். இந்த ஓயவூதியம் தங்கள் கணவரை இழந்த விதவைகளுக்கு நிதி உதவியை வழங்குகிறது. செயலாக்கத்திற்கு உங்கள் தனிப்பட்ட விவரங்கள், ஆவணங்கள் மற்றும் வங்கி தகவல்களை நாங்கள் சேகரிக்க வேண்டும்.",
            "hi": "मैं आपकी विधवा पेंशन योजना के लिए आवेदन करने में मदद करूंगा। यह पेंशन उन विधवाओं को वित्तीय सहायता प्रदान करती है जिन्होंने अपने पति को खो दिया है। प्रसंस्करण के लिए हमें आपका व्यक्तिगत विवरण, दस्तावेज़ और बैंक जानकारी एकत्र करने की आवश्यकता होगी।"
        }
        return descriptions.get(language, descriptions["en"])
    
    def check_eligibility(self, collected_fields: Dict[str, Any]) -> tuple[bool, str]:
        """Check if the applicant is eligible for widow pension"""
        try:
            # Check age (simplified - would need proper date calculation)
            if "date_of_birth" in collected_fields:
                # This is a simplified check - in production, calculate actual age
                pass
            
            # Check income limit
            if "annual_income" in collected_fields:
                income = int(collected_fields["annual_income"])
                if income > self.validation_rules["income_max"]:
                    return False, "Annual income exceeds the eligibility limit of ₹3,00,000"
            
            # Check if widow status is confirmed (death certificate required)
            if "husband_death_date" not in collected_fields:
                return False, "Husband's death certificate is required for eligibility"
            
            return True, "Applicant appears eligible for widow pension"
            
        except Exception as e:
            return False, f"Error checking eligibility: {str(e)}"
