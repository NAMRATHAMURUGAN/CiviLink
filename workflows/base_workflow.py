"""
Base Workflow Template
Defines the structure for all government service workflows
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

class FieldType(Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    AADHAAR = "aadhaar"
    BANK_ACCOUNT = "bank_account"
    ADDRESS = "address"
    DOCUMENT = "document"
    EMAIL = "email"
    PHONE = "phone"

@dataclass
class FieldDefinition:
    name: str
    field_type: FieldType
    required: bool = True
    validation_pattern: Optional[str] = None
    help_text: Optional[str] = None
    example: Optional[str] = None
    multilingual_help: Optional[Dict[str, str]] = None

@dataclass
class DocumentRequirement:
    name: str
    description: str
    ocr_fields: List[str]
    required: bool = True
    multilingual_description: Optional[Dict[str, str]] = None

class BaseWorkflow(ABC):
    def __init__(self):
        self.name = self.__class__.__name__
        self.fields = self.define_fields()
        self.documents = self.define_documents()
        self.validation_rules = self.define_validation_rules()
        self.submission_endpoint = self.define_submission_endpoint()
    
    @abstractmethod
    def define_fields(self) -> List[FieldDefinition]:
        """Define the fields required for this workflow"""
        pass
    
    @abstractmethod
    def define_documents(self) -> List[DocumentRequirement]:
        """Define the documents required for this workflow"""
        pass
    
    @abstractmethod
    def define_validation_rules(self) -> Dict[str, Any]:
        """Define validation rules for the workflow"""
        pass
    
    @abstractmethod
    def define_submission_endpoint(self) -> str:
        """Define the submission endpoint for this workflow"""
        pass
    
    @abstractmethod
    def get_workflow_description(self, language: str = "en") -> str:
        """Get a description of this workflow in the specified language"""
        pass
    
    def get_next_missing_field(self, collected_fields: Dict[str, Any]) -> Optional[FieldDefinition]:
        """Get the next required field that hasn't been collected yet"""
        for field in self.fields:
            if field.required and field.name not in collected_fields:
                return field
        return None
    
    def validate_field(self, field_name: str, value: str) -> tuple[bool, Optional[str]]:
        """Validate a field value"""
        if field_name not in [f.name for f in self.fields]:
            return False, "Unknown field"
        
        field = next(f for f in self.fields if f.name == field_name)
        
        # Basic validation based on field type
        if field.field_type == FieldType.AADHAAR:
            if not re.match(r'^\d{12}$', value.replace(' ', '')):
                return False, "Aadhaar number must be 12 digits"
        
        elif field.field_type == FieldType.EMAIL:
            if not re.match(r'^[^@]+@[^@]+\.[^@]+$', value):
                return False, "Please enter a valid email address"
        
        elif field.field_type == FieldType.PHONE:
            if not re.match(r'^\d{10}$', value.replace('-', '').replace(' ', '')):
                return False, "Phone number must be 10 digits"
        
        elif field.field_type == FieldType.BANK_ACCOUNT:
            if not re.match(r'^\d{9,18}$', value.replace(' ', '')):
                return False, "Bank account number must be 9-18 digits"
        
        # Custom validation pattern
        if field.validation_pattern:
            if not re.match(field.validation_pattern, value):
                return False, f"Invalid format for {field.name}"
        
        return True, None
    
    def get_field_question(self, field: FieldDefinition, language: str = "en", assistance_mode: str = "normal") -> str:
        """Generate a question for collecting a field"""
        if assistance_mode == "simplified":
            return self._get_simplified_question(field, language)
        
        questions = {
            "en": {
                FieldType.TEXT: f"Please provide your {field.name.replace('_', ' ')}",
                FieldType.NUMBER: f"Please enter your {field.name.replace('_', ' ')}",
                FieldType.DATE: f"Please provide your {field.name.replace('_', ' ')} (DD/MM/YYYY)",
                FieldType.AADHAAR: "Please provide your 12-digit Aadhaar number",
                FieldType.BANK_ACCOUNT: "Please provide your bank account number",
                FieldType.ADDRESS: "Please provide your residential address",
                FieldType.DOCUMENT: f"Please upload your {field.name.replace('_', ' ')}",
                FieldType.EMAIL: "Please provide your email address",
                FieldType.PHONE: "Please provide your 10-digit phone number"
            },
            "ta": {
                FieldType.TEXT: f"உங்கள் {field.name.replace('_', ' ')} தெரிவிக்கவும்",
                FieldType.NUMBER: f"உங்கள் {field.name.replace('_', ' ')} உள்ளிடவும்",
                FieldType.DATE: f"உங்கள் {field.name.replace('_', ' ')} தெரிவிக்கவும் (நாள்/மாதம்/ஆண்டு)",
                FieldType.AADHAAR: "உங்கள் 12-இலக்க ஆதார் எண்ணை தெரிவிக்கவும்",
                FieldType.BANK_ACCOUNT: "உங்கள் வங்கி கணக்கு எண்ணை தெரிவிக்கவும்",
                FieldType.ADDRESS: "உங்கள் வீட்டு முகவரியை தெரிவிக்கவும்",
                FieldType.DOCUMENT: f"உங்கள் {field.name.replace('_', ' ')} பதிவேற்றவும்",
                FieldType.EMAIL: "உங்கள் மின்னஞ்சல் முகவரியை தெரிவிக்கவும்",
                FieldType.PHONE: "உங்கள் 10-இலக்க தொலைபேசி எண்ணை தெரிவிக்கவும்"
            },
            "hi": {
                FieldType.TEXT: f"कृपया अपना {field.name.replace('_', ' ')} प्रदान करें",
                FieldType.NUMBER: f"कृपया अपना {field.name.replace('_', ' ')} दर्ज करें",
                FieldType.DATE: f"कृपया अपना {field.name.replace('_', ' ')} प्रदान करें (दिन/महीना/वर्ष)",
                FieldType.AADHAAR: "कृपया अपना 12-अंकीय आधार नंबर प्रदान करें",
                FieldType.BANK_ACCOUNT: "कृपया अपना बैंक खाता नंबर प्रदान करें",
                FieldType.ADDRESS: "कृपया अपना पता प्रदान करें",
                FieldType.DOCUMENT: f"कृपया अपना {field.name.replace('_', ' ')} अपलोड करें",
                FieldType.EMAIL: "कृपया अपना ईमेल पता प्रदान करें",
                FieldType.PHONE: "कृपया अपना 10-अंकीय फोन नंबर प्रदान करें"
            }
        }
        
        base_question = questions.get(language, questions["en"]).get(field.field_type, f"Please provide {field.name}")
        
        if field.example:
            if language == "en":
                base_question += f"\nExample: {field.example}"
            elif language == "ta":
                base_question += f"\nஉதாரணம்: {field.example}"
            elif language == "hi":
                base_question += f"\nउदाहरण: {field.example}"
        
        if field.help_text:
            if language == "en":
                base_question += f"\n{field.help_text}"
            elif field.multilingual_help and language in field.multilingual_help:
                base_question += f"\n{field.multilingual_help[language]}"
        
        return base_question
    
    def _get_simplified_question(self, field: FieldDefinition, language: str) -> str:
        """Get simplified version of the question"""
        simplifications = {
            "en": {
                "Please provide your": "Please tell me",
                "Please enter your": "Please tell me",
                "residential address": "home address",
                "Aadhaar number": "Aadhaar card number"
            },
            "ta": {
                "உங்கள்": "உங்கள்",
                "தெரிவிக்கவும்": "சொல்லுங்கள்",
                "வீட்டு முகவரியை": "வீட்டு முகவரி"
            },
            "hi": {
                "आपका": "आपका",
                "प्रदान करें": "बताएं",
                "पता": "घर का पता"
            }
        }
        
        question = self.get_field_question(field, language, "normal")
        
        for complex_term, simple_term in simplifications.get(language, {}).items():
            question = question.replace(complex_term, simple_term)
        
        return question
    
    def is_complete(self, collected_fields: Dict[str, Any]) -> bool:
        """Check if all required fields have been collected"""
        for field in self.fields:
            if field.required and field.name not in collected_fields:
                return False
        return True
    
    def get_summary(self, collected_fields: Dict[str, Any], language: str = "en") -> str:
        """Generate a summary of collected information for confirmation"""
        summaries = {
            "en": "Please review your details:\n",
            "ta": "உங்கள் விவரங்களை மதிப்பாய்க்கவும்:\n",
            "hi": "कृपया अपना विवरण देखें:\n"
        }
        
        summary = summaries.get(language, summaries["en"])
        
        for field in self.fields:
            if field.name in collected_fields:
                field_name_display = field.name.replace('_', ' ').title()
                summary += f"{field_name_display}: {collected_fields[field.name]}\n"
        
        return summary
