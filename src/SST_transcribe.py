"""
Offline Speech-to-Text Transcriber
Uses OpenAI's Whisper model running locally
"""

import logging
from pathlib import Path
import torch
import whisper
from typing import Optional
from config import AppConfig


logger = logging.getLogger(__name__)
configs = AppConfig().config

class OfflineTranscriber:
    """
    Handles offline speech-to-text transcription using Whisper
    
    Model Selection Rationale:
    - Whisper by OpenAI is chosen for its excellent accuracy and multilingual support
    - Completely offline after initial model download
    - Multiple model sizes available for different speed/accuracy tradeoffs
    - Well-maintained and widely used
    """
    
    # Model size options with tradeoffs
    MODEL_SIZES = {
        'tiny': 'Fastest, lowest accuracy (~1GB VRAM)',
        'base': 'Fast, decent accuracy (~1GB VRAM)',
        'small': 'Balanced speed and accuracy (~2GB VRAM)',
        'medium': 'Good accuracy, slower (~5GB VRAM)',
        'large': 'Best accuracy, slowest (~10GB VRAM)'
    }
    

    def __init__(self, model_size:Optional[str] = None, device:Optional[str]=None):
        """
        Initialize transcriber with specified model
        
        Args:
            model_size: Whisper model size ('tiny', 'base', 'small', 'medium', 'large')
            device: Device to run on ('cuda', 'cpu', or None for auto-detect)
        """
        # if model_size not in self.MODEL_SIZES:
        #     raise ValueError(
        #         f"Invalid model size. Choose from: {list(self.MODEL_SIZES.keys())}"
        #     )
        if model_size is None:
            self.model_size = configs.SST_model.sst_model_name
        else:
            self.model_size = model_size

        # Auto-detect device if not specified
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        logger.info(f"Initializing Whisper model: {self.model_size}")
        logger.info(f"Using device: {self.device}")
        
        # Load model
        try:
            self.model = whisper.load_model(self.model_size, device=self.device)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es'). None for auto-detect
            
        Returns:
            Transcribed text
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            Exception: For transcription errors
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Transcribing: {audio_path.name}")
        logger.info(f"File size: {audio_path.stat().st_size / (1024*1024):.2f} MB")
        
        try:
            # Transcribe with progress
            transcribe_options = {
                'language': language,
                'task': 'transcribe',
                'verbose': False,
            }
            
            result = self.model.transcribe(
                str(audio_path),
                **transcribe_options
            )
            
            transcript = result['text'].strip()
            
            # Log detected language if auto-detected
            if language is None and 'language' in result:
                detected_lang = result['language']
                logger.info(f"Detected language: {detected_lang}")
            
            logger.info(f"Transcription complete: {len(transcript)} characters")
            
            return transcript
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            raise Exception(f"Failed to transcribe audio: {str(e)}")
    
    def transcribe_with_timestamps(self, audio_path: str) -> list:
        """
        Transcribe with word-level timestamps
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            List of segments with timestamps and text
        """
        audio_path = Path(audio_path)
        
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        logger.info(f"Transcribing with timestamps: {audio_path.name}")
        
        try:
            result = self.model.transcribe(
                str(audio_path),
                word_timestamps=True,
                verbose=False
            )
            
            return result['segments']
            
        except Exception as e:
            logger.error(f"Transcription with timestamps failed: {str(e)}")
            raise Exception(f"Failed to transcribe with timestamps: {str(e)}")
    
    @staticmethod
    def get_model_info():
        """Get information about available models"""
        info = []
        for size, description in OfflineTranscriber.MODEL_SIZES.items():
            info.append(f"{size}: {description}")
        return "\n".join(info)


# Utility function for model download
def download_model(model_size: str = 'base'):
    """
    Pre-download Whisper model
    
    Args:
        model_size: Model size to download
    """
    logger.info(f"Downloading Whisper model: {model_size}")
    whisper.load_model(model_size)
    logger.info("Model download complete")


# if __name__ == "__main__":
#     # Example usage and testing
#     print("Available Whisper models:")
#     print(OfflineTranscriber.get_model_info())
    
#     # Test model loading
#     print("\nTesting model initialization...")
#     transcriber = OfflineTranscriber(model_size='base')
#     print("✓ Model loaded successfully")