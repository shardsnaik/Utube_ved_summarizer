"""
Setup script to download all required models
Run this after installing requirements.txt
"""

import os
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_ffmpeg():
    """Check if ffmpeg is installed"""
    import shutil
    if shutil.which('ffmpeg') is None:
        logger.error("FFmpeg not found!")
        logger.error("Please install FFmpeg:")
        logger.error("  - Ubuntu/Debian: sudo apt-get install ffmpeg")
        logger.error("  - macOS: brew install ffmpeg")
        logger.error("  - Windows: Download from https://ffmpeg.org/download.html")
        return False
    logger.info("✓ FFmpeg is installed")
    return True


def download_whisper_model(model_size='base'):
    """Download Whisper model"""
    logger.info(f"Downloading Whisper model: {model_size}")
    try:
        import whisper
        whisper.load_model(model_size)
        logger.info(f"✓ Whisper model '{model_size}' downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to download Whisper model: {str(e)}")
        return False


def download_summarization_model(model_name='bart-large-cnn'):
    """Download summarization model"""
    logger.info(f"Downloading summarization model: {model_name}")
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        model_mapping = {
            'bart-large-cnn': 'facebook/bart-large-cnn',
            'bart-base': 'facebook/bart-base',
            'flan-t5-base': 'google/flan-t5-base',
            'flan-t5-large': 'google/flan-t5-large'
        }
        
        model_id = model_mapping.get(model_name, model_name)
        
        logger.info(f"Downloading tokenizer for {model_id}...")
        AutoTokenizer.from_pretrained(model_id)
        
        logger.info(f"Downloading model {model_id}...")
        AutoModelForSeq2SeqLM.from_pretrained(model_id)
        
        logger.info(f"✓ Summarization model '{model_name}' downloaded successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to download summarization model: {str(e)}")
        return False


def create_directory_structure():
    """Create necessary directories"""
    dirs = ['output', 'output/audio', 'src', 'models']
    for dir_name in dirs:
        Path(dir_name).mkdir(parents=True, exist_ok=True)
    logger.info("✓ Directory structure created")


def main():
    print("="*80)
    print("YouTube Video Summarizer - Setup")
    print("="*80)
    print()
    
    # Check Python version
    if sys.version_info < (3, 8):
        logger.error("Python 3.8 or higher is required")
        return 1
    logger.info(f"✓ Python version: {sys.version.split()[0]}")
    
    # Create directories
    logger.info("\n[1/4] Creating directory structure...")
    create_directory_structure()
    
    # Check FFmpeg
    logger.info("\n[2/4] Checking FFmpeg installation...")
    if not check_ffmpeg():
        logger.warning("Please install FFmpeg and run setup again")
        return 1
    
    # Download Whisper model
    logger.info("\n[3/4] Downloading Whisper model...")
    logger.info("Model sizes available: tiny, base, small, medium, large")
    logger.info("Default: base (good balance of speed and accuracy)")
    
    whisper_model = input("Enter Whisper model size [base]: ").strip() or 'base'
    if not download_whisper_model(whisper_model):
        logger.warning("Whisper model download failed")
        return 1
    
    # Download summarization model
    logger.info("\n[4/4] Downloading summarization model...")
    logger.info("Models available: bart-large-cnn, bart-base, flan-t5-base, flan-t5-large")
    logger.info("Default: bart-large-cnn (best quality)")
    
    summ_model = input("Enter summarization model [bart-large-cnn]: ").strip() or 'bart-large-cnn'
    if not download_summarization_model(summ_model):
        logger.warning("Summarization model download failed")
        return 1
    
    # Success
    print("\n" + "="*80)
    print("✓ Setup complete!")
    print("="*80)
    print("\nYou can now run the application:")
    print('  python main.py "https://www.youtube.com/watch?v=VIDEO_ID"')
    print("\nFor help:")
    print("  python main.py --help")
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user")
        exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {str(e)}", exc_info=True)
        exit(1)