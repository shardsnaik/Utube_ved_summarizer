

"""
Offline Text Summarization Module
Uses BART or T5 models for abstractive summarization
"""

import logging
from typing import Optional
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    pipeline
)

logger = logging.getLogger(__name__)


class OfflineSummarizer:
    """
    Handles offline text summarization using transformer models
    
    Model Selection Rationale:
    - Using facebook/bart-large-cnn as default
    - BART is specifically fine-tuned for summarization tasks
    - Produces abstractive summaries (not just extractive)
    - Completely offline after initial download
    - Good balance between quality and speed
    
    Alternative: google/flan-t5-base for shorter summaries
    """
    
    # Available models with their characteristics
    AVAILABLE_MODELS = {
        'bart-large-cnn': {
            'name': 'facebook/bart-large-cnn',
            'description': 'Best quality, slower (~1.6GB)',
            'max_input': 1024,
            'recommended': True
        },
        'bart-base': {
            'name': 'facebook/bart-base',
            'description': 'Faster, good quality (~500MB)',
            'max_input': 1024,
            'recommended': False
        },
        'flan-t5-base': {
            'name': 'google/flan-t5-base',
            'description': 'Fast, concise summaries (~900MB)',
            'max_input': 512,
            'recommended': False
        },
        'flan-t5-large': {
            'name': 'google/flan-t5-large',
            'description': 'High quality, larger model (~3GB)',
            'max_input': 512,
            'recommended': False
        }
    }
    
    def __init__(
        self,
        model_name: str = 'flan-t5-large',
        device: Optional[str] = None
    ):
        """
        Initialize summarizer with specified model
        
        Args:
            model_name: Model identifier from AVAILABLE_MODELS
            device: Device to run on ('cuda', 'cpu', or None for auto-detect)
        """
        if model_name not in self.AVAILABLE_MODELS:
            raise ValueError(
                f"Invalid model. Choose from: {list(self.AVAILABLE_MODELS.keys())}"
            )
        
        model_info = self.AVAILABLE_MODELS[model_name]
        self.model_id = model_info['name']
        self.max_input_length = model_info['max_input']
        
        # Auto-detect device
        if device is None:
            self.device = 0 if torch.cuda.is_available() else -1
        else:
            self.device = 0 if device == 'cuda' else -1
        
        device_name = 'CUDA' if self.device == 0 else 'CPU'
        logger.info(f"Initializing summarization model: {self.model_id}")
        logger.info(f"Using device: {device_name}")
        
        try:
            # Load model and create pipeline
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_id)
            
            self.summarizer = pipeline(
                "summarization",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device
            )
            
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
    
    def summarize(
        self,
        text: str,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        num_beams: int = 4
    ) -> str:
        """
        Summarize input text
        
        Args:
            text: Text to summarize
            max_length: Maximum summary length (None for auto)
            min_length: Minimum summary length (None for auto)
            num_beams: Number of beams for beam search (higher = better quality, slower)
            
        Returns:
            Summary text
        """
        if not text or len(text.strip()) == 0:
            raise ValueError("Input text is empty")
        
        logger.info(f"Summarizing text: {len(text)} characters")
        
        # Calculate appropriate summary length if not specified
        if max_length is None:
            # Aim for ~20% of original length, capped at reasonable limits
            max_length = min(max(len(text) // 5, 100), 500)
        
        if min_length is None:
            min_length = max(30, max_length // 4)
        
        try:
            # Handle long texts by chunking
            chunks = self._chunk_text(text)
            
            if len(chunks) == 1:
                # Single chunk - direct summarization
                summary = self._summarize_chunk(
                    chunks[0],
                    max_length=max_length,
                    min_length=min_length,
                    num_beams=num_beams
                )
            else:
                # Multiple chunks - summarize each then combine
                logger.info(f"Text split into {len(chunks)} chunks")
                chunk_summaries = []
                
                for i, chunk in enumerate(chunks, 1):
                    logger.info(f"Summarizing chunk {i}/{len(chunks)}")
                    chunk_summary = self._summarize_chunk(
                        chunk,
                        max_length=max_length // len(chunks),
                        min_length=min_length // len(chunks),
                        num_beams=num_beams
                    )
                    chunk_summaries.append(chunk_summary)
                
                # Combine chunk summaries
                combined = " ".join(chunk_summaries)
                
                # Final summarization if combined is still long
                if len(combined.split()) > max_length:
                    logger.info("Performing final summarization pass")
                    summary = self._summarize_chunk(
                        combined,
                        max_length=max_length,
                        min_length=min_length,
                        num_beams=num_beams
                    )
                else:
                    summary = combined
            
            logger.info(f"Summary generated: {len(summary)} characters")
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            raise Exception(f"Failed to generate summary: {str(e)}")
    
    def _summarize_chunk(
        self,
        text: str,
        max_length: int,
        min_length: int,
        num_beams: int
    ) -> str:
        """Summarize a single chunk of text"""
        result = self.summarizer(
            text,
            max_length=max_length,
            min_length=min_length,
            num_beams=num_beams,
            length_penalty=2.0,
            early_stopping=True,
            do_sample=False
        )
        
        return result[0]['summary_text']
    
    def _chunk_text(self, text: str, overlap: int = 50) -> list:
        """
        Split text into chunks that fit model's input size
        
        Args:
            text: Input text
            overlap: Number of words to overlap between chunks
            
        Returns:
            List of text chunks
        """
        words = text.split()
        
        # Calculate tokens (rough estimate: 1 word ≈ 1.3 tokens)
        estimated_tokens = len(words) * 1.3
        
        if estimated_tokens <= self.max_input_length:
            return [text]
        
        # Split into chunks
        chunk_size = int(self.max_input_length / 1.3) - overlap
        chunks = []
        
        for i in range(0, len(words), chunk_size):
            chunk_words = words[max(0, i - overlap):i + chunk_size]
            chunks.append(" ".join(chunk_words))
        
        return chunks
    
    @staticmethod
    def get_model_info():
        """Get information about available models"""
        info = []
        for key, model in OfflineSummarizer.AVAILABLE_MODELS.items():
            recommended = " [RECOMMENDED]" if model['recommended'] else ""
            info.append(f"{key}: {model['description']}{recommended}")
        return "\n".join(info)


def download_model(model_name: str = 'bart-large-cnn'):
    """
    Pre-download summarization model
    
    Args:
        model_name: Model identifier
    """
    if model_name not in OfflineSummarizer.AVAILABLE_MODELS:
        raise ValueError(f"Unknown model: {model_name}")
    
    model_id = OfflineSummarizer.AVAILABLE_MODELS[model_name]['name']
    logger.info(f"Downloading model: {model_id}")
    
    AutoTokenizer.from_pretrained(model_id)
    AutoModelForSeq2SeqLM.from_pretrained(model_id)
    
    logger.info("Model download complete")


if __name__ == "__main__":
    # Example usage and testing
    print("Available summarization models:")
    print(OfflineSummarizer.get_model_info())
    
    # Test model loading
    print("\nTesting model initialization...")
    summarizer = OfflineSummarizer()
    print("✓ Model loaded successfully")