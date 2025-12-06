"""
YouTube Video Summarizer - Gradio Interface (Compatible Version)
Beautiful, modern UI for video summarization
Run with: python gradio_app.py
"""

import gradio as gr
import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Optional, Tuple
import sys

from src.vedio_downloader import YouTubeDownloader
from src.SST_transcribe import OfflineTranscriber
from src.summarizer_model import OfflineSummarizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances (initialized on startup)
downloader = None
transcriber = None
summarizer = None





def process_video(
    url: str,
    max_duration: Optional[float],
    summary_length: str,
    progress=gr.Progress() if hasattr(gr, 'Progress') else None
) -> Tuple[str, str, str, str, str]:
    """
    Process a YouTube video through the complete pipeline
    
    Args:
        url: YouTube video URL
        max_duration: Maximum video duration in seconds
        summary_length: Length of summary (short/medium/long)
        progress: Gradio progress tracker (if available)
        
    Returns:
        Tuple of (status, video_info, transcript, summary, download_json)
    """
    global downloader, transcriber, summarizer
    
    # Check if models are initialized
    if downloader is None or transcriber is None or summarizer is None:
        return (
            "❌ Error: Models not initialized. Please restart the application.",
            "", "", "", ""
        )
    
    def update_progress(value, desc=""):
        if progress:
            try:
                progress(value, desc=desc)
            except:
                pass
    
    try:
        # Validate URL
        if not url or not url.strip():
            return (
                "❌ Error: Please enter a YouTube URL",
                "", "", "", ""
            )
        
        # Convert duration
        max_dur = int(max_duration) if max_duration else None
        
        # Step 1: Download
        update_progress(0.1, "📥 Downloading audio...")
        logger.info(f"Downloading from: {url}")
        
        try:
            audio_info = downloader.download(url, max_duration=max_dur)
        except ValueError as e:
            return (
                f"❌ Error: {str(e)}",
                "", "", "", ""
            )
        except Exception as e:
            return (
                f"❌ Download failed: {str(e)}",
                "", "", "", ""
            )
        
        video_info = f"""### 🎥 Video Information

**Title:** {audio_info['title']}  
**Duration:** {audio_info['duration']} seconds ({audio_info['duration']//60} min {audio_info['duration']%60} sec)  
**Video ID:** {audio_info['video_id']}
"""
        
        # Step 2: Transcribe
        update_progress(0.4, "🎤 Transcribing audio (this may take a few minutes)...")
        logger.info("Transcribing audio...")
        
        try:
            transcript = transcriber.transcribe(audio_info['path'])
            word_count = len(transcript.split())
            transcript_display = f"**Word Count:** {word_count} words\n\n**Transcript:**\n\n{transcript}"
        except Exception as e:
            return (
                f"❌ Transcription failed: {str(e)}",
                video_info, "", "", ""
            )
        
        # Step 3: Summarize
        update_progress(0.7, "✨ Generating summary...")
        logger.info("Generating summary...")
        
        # Set summary length
        length_map = {
            "Short (50-100 words)": (50, 100),
            "Medium (100-200 words)": (100, 200),
            "Long (200-400 words)": (200, 400)
        }
        min_len, max_len = length_map[summary_length]
        
        try:
            summary = summarizer.summarize(
                transcript,
                max_length=max_len,
                min_length=min_len
            )
            summary_word_count = len(summary.split())
            summary_display = f"**Summary Length:** {summary_word_count} words\n\n{summary}"
        except Exception as e:
            return (
                f"❌ Summarization failed: {str(e)}",
                video_info, transcript_display, "", ""
            )
        
        # Save results
        update_progress(0.9, "💾 Saving results...")
        results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'video_title': audio_info['title'],
            'duration': audio_info['duration'],
            'transcript': transcript,
            'summary': summary
        }
        
        # Save JSON
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_dir / f"results_{timestamp}.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        update_progress(1.0, "✅ Complete!")
        
        return (
            "✅ Processing complete!",
            video_info,
            transcript_display,
            summary_display,
            str(json_path)
        )
        
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        return (
            f"❌ Unexpected error: {str(e)}",
            "", "", "", ""
        )


def create_interface():
    """Create the Gradio interface"""
    
    # Header
    header = gr.Markdown("""
# 🎥 YouTube Video Summarizer
### Offline AI-Powered Transcription & Summarization
*Powered by Whisper & BART | 100% Offline Processing*

---

**ℹ️ How it works:** This application downloads audio from YouTube, transcribes it using OpenAI's Whisper model, 
and generates a summary using Facebook's BART model. All processing happens completely offline on your machine.
""")
    
    # Input section
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("## 📝 Input Settings")
            
            url_input = gr.Textbox(
                label="YouTube URL",
                placeholder="https://www.youtube.com/watch?v=...",
                lines=1
            )
            
            with gr.Row():
                max_duration = gr.Number(
                    label="Max Duration (seconds)",
                    placeholder="Leave empty for no limit",
                    value=None
                )
                
                summary_length = gr.Radio(
                    label="Summary Length",
                    choices=[
                        "Short (50-100 words)",
                        "Medium (100-200 words)",
                        "Long (200-400 words)"
                    ],
                    value="Medium (100-200 words)"
                )
            
            gr.Markdown("""
**⚠️ Note:** Processing time depends on video length and your hardware. 
A 5-minute video takes ~30 seconds with GPU or ~5 minutes with CPU.
""")
            
            process_btn = gr.Button("🚀 Process Video", variant="primary")
            
            status_output = gr.Textbox(
                label="Status",
                interactive=False
            )
        
        with gr.Column(scale=1):
            gr.Markdown("""
## 💡 Quick Tips

**Best Practices:**
- Start with short videos (3-5 min) for testing
- Use max duration to limit processing time
- GPU processing is 10-50x faster than CPU

**Recommended Videos:**
- Educational content (TED talks, tutorials)
- Interviews and podcasts
- Documentaries

**Processing Time:**
- 5 min video: ~30s (GPU) / ~5 min (CPU)
- 15 min video: ~1 min (GPU) / ~15 min (CPU)
- 30 min video: ~2 min (GPU) / ~30 min (CPU)
""")
    
    # Output section
    gr.Markdown("## 📊 Results")
    
    with gr.Tab("📹 Video Info"):
        video_info_output = gr.Markdown(label="Video Information")
    
    with gr.Tab("📝 Transcript"):
        transcript_output = gr.Markdown(label="Full Transcript")
    
    with gr.Tab("✨ Summary"):
        summary_output = gr.Markdown(label="Generated Summary")
    
    with gr.Tab("💾 Export"):
        gr.Markdown("### Download Results")
        json_output = gr.Textbox(
            label="JSON File Path",
            interactive=False
        )
        gr.Markdown("""
The complete results are automatically saved as JSON in the `output/` directory.
You can find both JSON and text versions of your summaries there.
""")
    
    # Examples
    gr.Markdown("## 🎯 Try These Examples")
    gr.Examples(
        examples=[
            [
                "https://www.youtube.com/watch?v=aircAruvnKk",
                300,
                "Medium (100-200 words)"
            ],
            [
                "https://www.youtube.com/watch?v=R9OHn5ZF4Uo",
                600,
                "Short (50-100 words)"
            ],
        ],
        inputs=[url_input, max_duration, summary_length],
        label="Click to load example videos"
    )
    
    # Footer
    gr.Markdown("""
---
*Built with ❤️ using Gradio, Whisper, and BART*  
*All processing happens offline • No data leaves your machine*
""")
    
    # Event handlers
    process_btn.click(
        fn=process_video,
        inputs=[url_input, max_duration, summary_length],
        outputs=[
            status_output,
            video_info_output,
            transcript_output,
            summary_output,
            json_output
        ]
    )


def main():
    """Main entry point"""
    global downloader, transcriber, summarizer
    
    print("="*80)
    print("YouTube Video Summarizer - Gradio Interface")
    print("="*80)
    print()
    
    # Initialize models BEFORE creating interface
    print("Initializing AI models (this may take a moment)...")
    
    try:
        print("  - Loading YouTube downloader...")
        downloader = YouTubeDownloader(output_dir="output/audio")
        
        print("  - Loading Whisper (transcriber)...")
        transcriber = OfflineTranscriber()
        
        print("  - Loading BART (summarizer)...")
        summarizer = OfflineSummarizer()
        
        print("\n✅ All models loaded successfully!")
    except Exception as e:
        print(f"\n❌ Failed to initialize models: {e}")
        print("Please run 'python setup.py' first to download required models.")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\nStarting Gradio interface...")
    print("="*80)
    
    # Create interface with simple layout
    with gr.Blocks(title="YouTube Video Summarizer") as demo:
        create_interface()
    
    # Launch
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True
    )
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit(1)