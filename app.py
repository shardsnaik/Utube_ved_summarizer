"""
YouTube Video Summarizer - Gradio Interface (Optimized)
Fast, efficient processing with model reuse
Run with: python gradio_app.py
"""

import gradio as gr
import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Optional, Tuple

# Import from your actual source files
from src.vedio_downloader import YouTubeDownloader
from src.SST_transcribe import OfflineTranscriber
from src.summarizer_model import OfflineSummarizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CRITICAL: Global instances - initialized once and reused
downloader = None
transcriber = None
summarizer = None
output_dir = Path("output")


def process_video(
    url: str,
    max_duration: Optional[float],
    summary_length: str
) -> Tuple[str, str, str, str, str]:
    """
    Process a YouTube video - EXACTLY like main.py does it
    """
    global downloader, transcriber, summarizer
    
    # Quick validation
    if not url or not url.strip():
        return "❌ Error: Please enter a YouTube URL", "", "", "", ""
    
    if downloader is None or transcriber is None or summarizer is None:
        return "❌ Error: Models not initialized. Please restart.", "", "", "", ""
    
    try:
        # Convert duration
        max_dur = int(max_duration) if max_duration else None
        
        # === EXACTLY THE SAME AS main.py ===
        
        # Step 1: Download
        logger.info(f"[1/3] Downloading: {url}")
        audio_info = downloader.download(url, max_duration=max_dur)
        
        video_info = f"""### 🎥 Video Information

**Title:** {audio_info['title']}  
**Duration:** {audio_info['duration']} seconds ({audio_info['duration']//60} min {audio_info['duration']%60} sec)  
**Video ID:** {audio_info['video_id']}
"""
        
        # Step 2: Transcribe
        logger.info(f"[2/3] Transcribing... (Duration: {audio_info['duration']}s)")
        transcript = transcriber.transcribe(audio_info['path'])
        word_count = len(transcript.split())
        transcript_display = f"**Word Count:** {word_count} words\n\n**Transcript:**\n\n{transcript}"
        logger.info(f"Transcription complete: {word_count} words")
        
        # Step 3: Summarize
        logger.info("[3/3] Generating summary...")
        
        # Set summary length
        length_map = {
            "Short (50-100 words)": (50, 100),
            "Medium (100-200 words)": (100, 200),
            "Long (200-400 words)": (200, 400)
        }
        min_len, max_len = length_map.get(summary_length, (100, 200))
        
        summary = summarizer.summarize(
            transcript,
            max_length=max_len,
            min_length=min_len
        )
        summary_word_count = len(summary.split())
        summary_display = f"**Summary Length:** {summary_word_count} words\n\n{summary}"
        logger.info(f"Summary complete: {summary_word_count} words")
        
        # Save results
        results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'video_title': audio_info['title'],
            'duration': audio_info['duration'],
            'transcript': transcript,
            'summary': summary
        }
        
        # Save JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_dir / f"results_{timestamp}.json"
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Complete! Saved to {json_path}")
        
        return (
            "✅ Processing complete!",
            video_info,
            transcript_display,
            summary_display,
            str(json_path)
        )
        
    except ValueError as e:
        return f"❌ Error: {str(e)}", "", "", "", ""
    except Exception as e:
        logger.error(f"Processing error: {e}", exc_info=True)
        return f"❌ Error: {str(e)}", "", "", "", ""


def create_interface():
    """Create the Gradio interface"""
    
    # Header
    gr.Markdown("""
# 🎥 YouTube Video Summarizer
### Offline AI-Powered Transcription & Summarization
*Powered by Whisper & BART | 100% Offline Processing*

---

**ℹ️ How it works:** Downloads audio from YouTube, transcribes using Whisper, 
and generates a summary using BART. All processing happens offline.

**⚡ Performance:** Models are pre-loaded for fast processing!
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
**⚠️ Processing Time Estimates:**
- 5 min video: ~30s (GPU) / ~5 min (CPU)
- 15 min video: ~1 min (GPU) / ~15 min (CPU)

*Models are pre-loaded for optimal speed!*
""")
            
            process_btn = gr.Button("🚀 Process Video", variant="primary")
            
            status_output = gr.Textbox(
                label="Status",
                interactive=False,
                lines=2
            )
        
        with gr.Column(scale=1):
            gr.Markdown("""
## 💡 Quick Tips

**Best Practices:**
- Start with short videos (3-5 min)
- Models are already loaded - processing is fast!
- Check terminal for detailed progress

**Recommended Videos:**
- Educational content
- Interviews and podcasts
- Documentaries

**Why Fast?**
- ✅ Models pre-loaded at startup
- ✅ No re-initialization per request
- ✅ Efficient memory management
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
Complete results are automatically saved as JSON in the `output/` directory.
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
*All processing happens offline • Models pre-loaded for speed*
""")
    
    # Event handler - NO PROGRESS TRACKING (causes slowdown in old Gradio)
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
    """Main entry point - OPTIMIZED"""
    global downloader, transcriber, summarizer, output_dir
    
    print("="*80)
    print("YouTube Video Summarizer - Gradio Interface (OPTIMIZED)")
    print("="*80)
    print()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize models ONCE at startup
    print("Initializing AI models (one-time setup)...")
    print()
    
    try:
        print("  [1/3] Loading YouTube downloader...")
        downloader = YouTubeDownloader(output_dir=str(output_dir / "audio"))
        print("        ✓ Downloader ready")
        
        print("  [2/3] Loading Whisper (transcriber)...")
        print("        This may take a moment...")
        transcriber = OfflineTranscriber()
        print("        ✓ Whisper loaded")
        
        print("  [3/3] Loading BART (summarizer)...")
        print("        This may take a moment...")
        summarizer = OfflineSummarizer()
        print("        ✓ BART loaded")
        
        print()
        print("="*80)
        print("✅ All models loaded successfully!")
        print("="*80)
        print()
        print("PERFORMANCE NOTES:")
        print("  • Models are pre-loaded and cached in memory")
        print("  • Each request reuses the same model instances")
        print("  • No reinitialization overhead")
        print("  • Processing should be as fast as CLI mode")
        print()
        
    except Exception as e:
        print(f"\n❌ Failed to initialize models: {e}")
        print("\nPlease run 'python setup.py' first to download required models.")
        import traceback
        traceback.print_exc()
        return 1
    
    print("Starting Gradio interface...")
    print("="*80)
    print()
    
    # Create interface
    with gr.Blocks(title="YouTube Video Summarizer") as demo:
        create_interface()
    
    # Launch with optimized settings for your models
    demo.queue(
        
    )
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        inbrowser=True,
        quiet=False,
        max_threads=1  # Prevent threading issues
    )
    
    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        print("Models remain in memory until process ends.")
        exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit(1)


# # ============================================================
# # simplified verion 
# # ==========================================================


# import gradio as gr
# import logging
# from pathlib import Path
# import json
# from datetime import datetime
# from typing import Optional, Tuple
# import torch
# import time

# from src.vedio_downloader import YouTubeDownloader
# from src.SST_transcribe import OfflineTranscriber
# from src.summarizer_model import OfflineSummarizer

# # ---------------- LOGGING ---------------- #
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# # ---------------- DEVICE ---------------- #
# DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
# print(f"✅ Running on device: {DEVICE}")

# # ---------------- GLOBAL SINGLETON MODELS ---------------- #
# downloader = None
# transcriber = None
# summarizer = None


# def load_models():
#     """Load all models ONCE (critical for speed)"""
#     global downloader, transcriber, summarizer

#     if downloader is None:
#         print("📥 Loading Downloader...")
#         downloader = YouTubeDownloader(output_dir="output/audio")

#     if transcriber is None:
#         print("🎤 Loading Whisper...")
#         transcriber = OfflineTranscriber()

#     if summarizer is None:
#         print("✨ Loading Summarizer...")
#         summarizer = OfflineSummarizer()

#     print("✅ All models loaded successfully")


# # ---------------- FAST BACKEND PIPELINE ---------------- #
# def process_video_fast(
#     url: str,
#     max_duration: Optional[float],
#     summary_length: str
# ) -> Tuple[str, str, str, str]:

#     try:
#         load_models()

#         if not url.strip():
#             return "❌ Please enter a valid URL", "", "", ""

#         max_dur = int(max_duration) if max_duration else None

#         # -------- Download -------- #
#         logger.info("Downloading audio...")
#         audio_info = downloader.download(url, max_duration=max_dur)

#         video_info = (
#             f"Title: {audio_info['title']}\n"
#             f"Duration: {audio_info['duration']} sec\n"
#             f"Video ID: {audio_info['video_id']}"
#         )

#         # -------- Transcribe -------- #
#         logger.info("Transcribing...")
#         transcript = transcriber.transcribe(audio_info["path"])

#         # ✅ HARD LIMIT transcript shown in UI (HUGE SPEED FIX)
#         transcript_preview = transcript[:4000] + "\n\n...[TRUNCATED]"

#         # -------- Summarize -------- #
#         length_map = {
#             "Short": (50, 100),
#             "Medium": (100, 200),
#             "Long": (200, 400)
#         }

#         min_len, max_len = length_map[summary_length]

#         logger.info("Summarizing...")
#         summary = summarizer.summarize(
#             transcript,
#             max_length=max_len,
#             min_length=min_len
#         )

#         # -------- Save to Disk (NON-BLOCKING UI) -------- #
#         output_dir = Path("output")
#         output_dir.mkdir(exist_ok=True)

#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         json_path = output_dir / f"results_{timestamp}.json"

#         with open(json_path, "w", encoding="utf-8") as f:
#             json.dump({
#                 "url": url,
#                 "title": audio_info["title"],
#                 "duration": audio_info["duration"],
#                 "transcript": transcript,
#                 "summary": summary,
#             }, f, indent=2, ensure_ascii=False)

#         return (
#             "✅ Completed Successfully",
#             video_info,
#             transcript_preview,
#             summary
#         )

#     except Exception as e:
#         logger.exception("Processing Failed")
#         return f"❌ Error: {str(e)}", "", "", ""


# # ---------------- UI (LIGHTWEIGHT & FAST) ---------------- #
# def create_ui():
#     gr.Markdown("# ⚡ Ultra-Fast YouTube Video Summarizer (Offline)")

#     with gr.Row():
#         with gr.Column():
#             url_input = gr.Textbox(label="YouTube URL")
#             max_duration = gr.Number(label="Max Duration (seconds)", value=300)

#             summary_length = gr.Radio(
#                 ["Short", "Medium", "Long"],
#                 value="Medium",
#                 label="Summary Length"
#             )

#             process_btn = gr.Button("🚀 Process", variant="primary")
#             status = gr.Textbox(label="Status", interactive=False)

#         with gr.Column():
#             video_info = gr.Textbox(label="Video Info", interactive=False)

#     transcript_output = gr.Textbox(
#         label="Transcript Preview (Auto-Truncated)",
#         lines=18
#     )

#     summary_output = gr.Textbox(
#         label="Final Summary",
#         lines=12
#     )

#     process_btn.click(
#         fn=process_video_fast,
#         inputs=[url_input, max_duration, summary_length],
#         outputs=[status, video_info, transcript_output, summary_output]
#     )


# # ---------------- MAIN ---------------- #
# def main():
#     load_models()  # ✅ Warm startup

#     with gr.Blocks(title="Fast YouTube Summarizer") as demo:
#         create_ui()

#     demo.queue().launch(
#         server_name="127.0.0.1",
#         server_port=7860,
#         share=False
#     )


# if __name__ == "__main__":
#     main()
