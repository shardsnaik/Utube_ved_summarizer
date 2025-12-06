"""
YouTube Video Summarizer - Offline Processing
Main application file with CLI interface
"""

import os
import argparse
import logging
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from src.vedio_downloader import YouTubeDownloader
from src.SST_transcribe import OfflineTranscriber
from src.summarizer_model import OfflineSummarizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoSummarizer:
    """Main orchestrator for the video summarization pipeline"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.downloader = YouTubeDownloader(output_dir=str(self.output_dir / "audio"))
        self.transcriber = OfflineTranscriber()
        self.summarizer = OfflineSummarizer()
        
    def process_video(self, url: str, max_duration: Optional[int] = None) -> dict:
        """
        Complete pipeline: download -> transcribe -> summarize
        
        Args:
            url: YouTube video URL
            max_duration: Maximum video duration in seconds (None for no limit)
            
        Returns:
            Dictionary containing all results
        """
        results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'audio_path': None,
            'transcript': None,
            'summary': None,
            'errors': []
        }
        
        try:
            # Step 1: Download audio
            logger.info(f"Downloading audio from: {url}")
            audio_info = self.downloader.download(url, max_duration=max_duration)
            results['audio_path'] = audio_info['path']
            results['video_title'] = audio_info['title']
            results['duration'] = audio_info['duration']
            logger.info(f"Audio downloaded: {audio_info['title']} ({audio_info['duration']}s)")
            
            # Step 2: Transcribe audio
            logger.info("Transcribing audio...")
            transcript = self.transcriber.transcribe(audio_info['path'])
            results['transcript'] = transcript
            logger.info(f"Transcription complete: {len(transcript)} characters")
            # displaying the transcripts texts
            transcrib_text = self.output_dir / 'transcrib_text_.txt'
            with open(transcrib_text, 'w', encoding='utf-8') as d:
                d.write(str(results['transcript']))
        
            
            # Step 3: Summarize transcript
            logger.info("Generating summary...")
            summary = self.summarizer.summarize(transcript)
            results['summary'] = summary
            logger.info(f"Summary generated: {len(summary)} characters")
            
            # Save results
            self._save_results(results)
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            results['errors'].append(str(e))
            raise
            
        return results
    
    def _save_results(self, results: dict):
        """Save results to JSON and text files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON
        json_path = self.output_dir / f"results_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"Results saved to: {json_path}")
        
        # Save readable summary
        if results.get('summary'):
            summary_path = self.output_dir / f"summary_{timestamp}.txt"
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(f"Video: {results.get('video_title', 'Unknown')}\n")
                f.write(f"URL: {results['url']}\n")
                f.write(f"Duration: {results.get('duration', 'Unknown')}s\n")
                f.write(f"Processed: {results['timestamp']}\n")
                f.write("\n" + "="*80 + "\n")
                f.write("SUMMARY\n")
                f.write("="*80 + "\n\n")
                f.write(results['summary'])
            logger.info(f"Summary saved to: {summary_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Offline YouTube Video Summarizer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
  python main.py "https://youtu.be/VIDEO_ID" --max-duration 600
  python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --output results
        """
    )
    
    parser.add_argument(
        'url',
        type=str,
        help='YouTube video URL'
    )
    
    parser.add_argument(
        '--max-duration',
        type=int,
        default=None,
        help='Maximum video duration in seconds (default: no limit)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='output',
        help='Output directory (default: output)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize summarizer
        summarizer = VideoSummarizer(output_dir=args.output)
        
        # Process video
        print(f"\n{'='*80}")
        print("Offline YouTube Video Summarizer")
        print(f"{'='*80}\n")
        
        results = summarizer.process_video(args.url, max_duration=args.max_duration)

        # Display results
        print(f"\n{'='*80}")
        print("RESULTS")
        print(f"{'='*80}\n")
        print(f"Video: {results.get('video_title', 'Unknown')}")
        print(f"Duration: {results.get('duration', 'Unknown')}s")
        print(f"\nSUMMARY:\n")
        print(results['summary'])
        print(f"\n{'='*80}\n")
        print(f"✓ Complete! Results saved to: {args.output}/")
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        return 1
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"\n✗ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())