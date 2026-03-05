# CiviLink - EmpowerAbility Government Assistant

An accessibility-first, privacy-focused government services assistant operating on WhatsApp that helps citizens complete complex government applications through structured, conversational guidance.

## 🧠 System Overview

CiviLink leverages advanced AI technologies to provide an inclusive and empathetic government services experience:

- **🤖 GPT-4 LLM**: Advanced intent detection and multilingual understanding
- **🎤 Whisper**: Speech-to-text for voice message processing  
- **👁️ Tesseract OCR**: Document processing and information extraction
- **🌍 Multilingual Support**: English, Tamil, Hindi with automatic detection
- **🔒 Privacy-First**: Consent-based data processing with automatic deletion
- **📱 WhatsApp Integration**: Native WhatsApp Business API integration

## ✨ Key Features

### Accessibility First
- **One Question at a Time**: Never overwhelms users with multiple requests
- **Adaptive Assistance**: Detects confusion and simplifies language automatically
- **Empathetic Responses**: Caring, supportive tone throughout the conversation
- **Voice Support**: Process voice messages for users who prefer speaking

### Privacy by Design
- **Explicit Consent**: Always asks permission before processing personal data
- **Data Minimization**: Collects only necessary information
- **Automatic Deletion**: Voice data (7 days), Documents (30 days), Personal info (30 days)
- **Encryption**: All sensitive data encrypted at rest
- **Audit Logging**: Complete privacy audit trail

### Multilingual Intelligence
- **Automatic Detection**: Detects user language from message patterns
- **Native Responses**: Generates responses in detected language
- **Cultural Context**: Understands regional variations and cultural nuances
- **Cross-Language Support**: Seamlessly switches between English, Tamil, Hindi

### Smart Document Processing
- **OCR Extraction**: Extracts text from Aadhaar cards, certificates, bank documents
- **Field Validation**: Validates Aadhaar numbers, IFSC codes, dates automatically
- **Quality Assessment**: Evaluates image quality and provides feedback
- **Privacy Safe**: Deletes documents immediately after processing

## 🏛️ Supported Services

### Widow Pension Scheme
- Complete application assistance
- Document verification (Aadhaar, death certificate, bank details)
- Eligibility checking
- Form submission with confirmation

### Scholarship Applications  
- Multiple scholarship schemes support
- Educational document processing
- Income certificate verification
- Application tracking

### Certificate Applications
- Birth certificates
- Death certificates  
- Marriage certificates
- Residence certificates

*(Extensible framework for adding more government services)*

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Tesseract OCR installed
- OpenAI API key
- WhatsApp Business API access

### Installation

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd CiviLink
   python setup.py
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys:
   # OPENAI_API_KEY=your_openai_key
   # WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
   # WHATSAPP_PHONE_NUMBER_ID=your_phone_id
   ```

3. **Start the Server**
   ```bash
   python app.py
   ```

4. **Configure WhatsApp Webhook**
   - Set webhook URL: `https://your-domain.com/webhook/whatsapp`
   - Verify webhook with token from `.env`
   - Test message processing

## 🏗️ Architecture

```
CiviLink/
├── core/                    # Core assistant logic
│   ├── assistant.py         # Main assistant with LLM integration
│   ├── llm_intent_detector.py # GPT-4 powered intent detection
│   └── whisper_stt.py       # Whisper speech-to-text
├── workflows/               # Government service workflows
│   ├── base_workflow.py     # Base workflow template
│   └── widow_pension_workflow.py # Widow pension workflow
├── multilingual/            # Multilingual support
│   └── multilingual_llm.py  # LLM-powered multilingual responses
├── ocr/                     # Document processing
│   └── document_processor.py # Tesseract OCR with validation
├── privacy/                 # Privacy & consent framework
│   └── consent_manager.py   # GDPR-style consent management
├── whatsapp/                # WhatsApp integration
│   └── webhook_handler.py   # WhatsApp Business API handler
└── app.py                   # Main Flask application
```

## 🔧 Configuration

### OpenAI Integration
```python
# .env configuration
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4
WHISPER_MODEL=base
```

### WhatsApp Setup
1. Create Meta Business Account
2. Set up WhatsApp Business API
3. Configure webhook endpoint
4. Add phone number to Business Account

### OCR Configuration
```python
# Windows
TESSERACT_CMD_PATH="C:\\Program Files\\Tesseract-OCR\\tesseract.exe"

# Linux/macOS  
TESSERACT_CMD_PATH="/usr/bin/tesseract"
```

## 📱 Usage Examples

### Text Interaction
```
User: "I want widow pension"
CiviLink: "I can help you with widow pension. Do you consent to processing your information?"
User: "Yes"
CiviLink: "Thank you! Let's start with your full name."
```

### Voice Processing
```
User: [Voice message in Tamil]
CiviLink: [Transcribes using Whisper] "நான் உங்களுக்கு உதவ முடியும்..."
```

### Document Upload
```
User: [Uploads Aadhaar card image]
CiviLink: [OCR Processing] "I found: Name: Rani Sharma, Aadhaar: 1234... Is this correct?"
```

## 🔒 Privacy & Security

### Data Protection
- **Encryption**: All personal data encrypted using Fernet
- **Consent Management**: Granular consent for different data types
- **Retention Policies**: Automatic data deletion based on type
- **Audit Trail**: Complete logging of all data operations

### Compliance Features
- **GDPR Principles**: Data minimization, purpose limitation
- **Right to Withdraw**: Users can revoke consent anytime
- **Data Portability**: Users can request their data summary
- **Transparency**: Clear explanations of data usage

## 🧪 Testing

### Run Tests
```bash
python -m pytest tests/
```

### Test WhatsApp Integration
```bash
curl -X POST http://localhost:5000/api/message \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "hello"}'
```

### Test OCR Processing
```bash
curl -X POST http://localhost:5000/api/ocr/process \
  -F "document=@test_aadhaar.jpg" \
  -F "user_id=test"
```

## 📊 Monitoring & Analytics

### Health Checks
```bash
curl http://localhost:5000/api/health
```

### Privacy Summary
```bash
curl http://localhost:5000/api/privacy/summary/{user_id}
```

### Data Cleanup
```bash
curl -X POST http://localhost:5000/api/admin/cleanup
```

## 🌐 API Documentation

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/webhook/whatsapp` | POST/GET | WhatsApp webhook handler |
| `/api/message` | POST | Direct message processing |
| `/api/ocr/process` | POST | Document OCR processing |
| `/api/voice/transcribe` | POST | Voice message transcription |
| `/api/consent/request` | POST | Request user consent |
| `/api/privacy/summary/{user_id}` | GET | Get privacy summary |

### Response Format
```json
{
  "response": "I can help you with widow pension...",
  "session_state": "workflow_initialized",
  "language": "en",
  "simplified_response": "I help with pension...",
  "explanation_response": "Detailed explanation..."
}
```

## 🚀 Deployment

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

### Environment Variables
```bash
# Production
FLASK_ENV=production
LOG_LEVEL=INFO
PORT=5000

# Security
SECRET_KEY=your-production-secret
ENCRYPTION_KEY=your-encryption-key
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-service`
3. Add tests for new functionality
4. Ensure all tests pass: `python -m pytest`
5. Submit pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: Check README.md and inline code comments
- **Issues**: Report bugs via GitHub Issues
- **Security**: Report security concerns privately

## 🌟 Impact

CiviLink is designed to:
- **Reduce Digital Inequality**: Make government services accessible to all
- **Empower Citizens**: Provide clear guidance through complex processes  
- **Save Time**: Eliminate repeated visits to government offices
- **Increase Inclusion**: Support elderly, low-literacy, and rural populations
- **Protect Privacy**: Set new standards for data protection in government services

---

**Built with ❤️ for inclusive digital governance**
