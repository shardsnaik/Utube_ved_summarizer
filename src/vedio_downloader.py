"""
YouTube Audio Downloader Module
Uses yt-dlp for robust video downloading
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict
import yt_dlp

logger = logging.getLogger(__name__)


class YouTubeDownloader:
    """Handles downloading audio from YouTube videos"""
    
    def __init__(self, output_dir: str = "audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def download(self, url: str, max_duration: Optional[int] = None) -> Dict[str, any]:
        """
        Download audio from YouTube video
        
        Args:
            url: YouTube video URL
            max_duration: Maximum video duration in seconds (None for no limit)
            
        Returns:
            Dictionary with download information
            
        Raises:
            ValueError: If video is too long or URL is invalid
            Exception: For download errors
        """
        # Validate URL
        if not self._is_valid_youtube_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")
        
        # Configure yt-dlp options
        output_template = str(self.output_dir / '%(id)s.%(ext)s')
        
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # First, get video info without downloading
                logger.info("Fetching video information...")
                info = ydl.extract_info(url, download=False)
                
                if info is None:
                    raise ValueError("Could not extract video information")
                
                # Check duration
                duration = info.get('duration', 0)
                if max_duration and duration > max_duration:
                    raise ValueError(
                        f"Video duration ({duration}s) exceeds maximum "
                        f"allowed duration ({max_duration}s)"
                    )
                
                video_id = info.get('id')
                title = info.get('title', 'Unknown')
                
                logger.info(f"Video: {title}")
                logger.info(f"Duration: {duration}s")
                
                # Check if already downloaded
                audio_path = self.output_dir / f"{video_id}.wav"
                if audio_path.exists():
                    logger.info(f"Audio already exists: {audio_path}")
                else:
                    # Download the audio
                    logger.info("Downloading audio...")
                    ydl.download([url])
                    logger.info("Download complete")
                
                return {
                    'path': str(audio_path),
                    'title': title,
                    'duration': duration,
                    'video_id': video_id
                }
                
        except yt_dlp.utils.DownloadError as e:
            logger.error(f"Download error: {str(e)}")
            raise Exception(f"Failed to download video: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise
    
    @staticmethod
    def _is_valid_youtube_url(url: str) -> bool:
        """Check if URL is a valid YouTube URL"""
        youtube_domains = [
            'youtube.com',
            'youtu.be',
            'www.youtube.com',
            'm.youtube.com'
        ]
        return any(domain in url.lower() for domain in youtube_domains)
    
    def cleanup(self, keep_latest: int = 5):
        """
        Clean up old audio files, keeping only the most recent ones
        
        Args:
            keep_latest: Number of most recent files to keep
        """
        audio_files = sorted(
            self.output_dir.glob('*.wav'),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for audio_file in audio_files[keep_latest:]:
            try:
                audio_file.unlink()
                logger.info(f"Removed old audio file: {audio_file}")
            except Exception as e:
                logger.warning(f"Could not remove {audio_file}: {e}")