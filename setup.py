"""
CiviLink Setup Script
Automated setup for the EmpowerAbility Government Assistant
"""

import os
import subprocess
import sys
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print("✅ Python version check passed")

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        sys.exit(1)

def setup_environment():
    """Setup environment configuration"""
    print("🔧 Setting up environment...")
    
    # Create .env file if it doesn't exist
    env_file = Path(".env")
    if not env_file.exists():
        env_example = Path(".env.example")
        if env_example.exists():
            import shutil
            shutil.copy(env_example, env_file)
            print("✅ Created .env file from .env.example")
            print("⚠️  Please update .env file with your actual API keys and configuration")
        else:
            print("❌ .env.example file not found")
            sys.exit(1)
    else:
        print("✅ .env file already exists")

def check_tesseract():
    """Check if Tesseract OCR is installed"""
    print("🔍 Checking Tesseract OCR installation...")
    try:
        result = subprocess.run(["tesseract", "--version"], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ Tesseract OCR is installed")
        else:
            print("❌ Tesseract OCR not found")
            print("📖 Please install Tesseract OCR:")
            print("   Windows: https://github.com/UB-Mannheim/tesseract/wiki")
            print("   macOS: brew install tesseract")
            print("   Ubuntu: sudo apt install tesseract-ocr")
            sys.exit(1)
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ Tesseract OCR not found")
        print("📖 Please install Tesseract OCR:")
        print("   Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   macOS: brew install tesseract")
        print("   Ubuntu: sudo apt install tesseract-ocr")
        sys.exit(1)

def check_gpu():
    """Check if GPU is available for Whisper"""
    print("🔍 Checking GPU availability...")
    try:
        import torch
        if torch.cuda.is_available():
            print("✅ GPU detected - Whisper will use GPU acceleration")
        else:
            print("ℹ️  No GPU detected - Whisper will use CPU (slower but functional)")
    except ImportError:
        print("⚠️  PyTorch not installed yet")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = [
        "logs",
        "uploads", 
        "temp",
        "data",
        "tests/fixtures"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✅ Directories created")

def test_imports():
    """Test critical imports"""
    print("🧪 Testing critical imports...")
    
    try:
        import openai
        print("✅ OpenAI SDK imported")
    except ImportError:
        print("❌ OpenAI SDK import failed")
        sys.exit(1)
    
    try:
        import whisper
        print("✅ Whisper imported")
    except ImportError:
        print("❌ Whisper import failed")
        sys.exit(1)
    
    try:
        import pytesseract
        print("✅ Pytesseract imported")
    except ImportError:
        print("❌ Pytesseract import failed")
        sys.exit(1)
    
    try:
        import flask
        print("✅ Flask imported")
    except ImportError:
        print("❌ Flask import failed")
        sys.exit(1)

def generate_sample_config():
    """Generate sample configuration files"""
    print("📝 Generating sample configurations...")
    
    # Create sample workflow config
    workflow_config = {
        "widow_pension": {
            "enabled": True,
            "required_fields": ["full_name", "aadhaar_number", "date_of_birth"],
            "required_documents": ["aadhaar_card", "death_certificate"]
        },
        "scholarship": {
            "enabled": True,
            "required_fields": ["full_name", "aadhaar_number", "education_level"],
            "required_documents": ["aadhaar_card", "mark_sheet"]
        }
    }
    
    import json
    with open("config/workflows.json", "w") as f:
        json.dump(workflow_config, f, indent=2)
    
    print("✅ Sample workflow configuration created")

def main():
    """Main setup function"""
    print("🚀 CiviLink Setup Started")
    print("=" * 50)
    
    # Run setup steps
    check_python_version()
    install_dependencies()
    setup_environment()
    check_tesseract()
    check_gpu()
    create_directories()
    test_imports()
    generate_sample_config()
    
    print("=" * 50)
    print("🎉 CiviLink setup completed successfully!")
    print()
    print("📋 Next steps:")
    print("1. Update .env file with your API keys")
    print("2. Run 'python app.py' to start the server")
    print("3. Configure WhatsApp webhook in Meta Business Suite")
    print("4. Test with: curl http://localhost:5000/")
    print()
    print("📖 For more information, see README.md")

if __name__ == "__main__":
    main()
