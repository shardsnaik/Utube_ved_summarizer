# YouTube Video Summarizer - Offline Processing

A fully offline + online (Gradio) system for downloading, transcribing, and summarizing YouTube videos using state-of-the-art AI models running entirely on your local machine.

## 🎯 Project Overview

This application provides an end-to-end pipeline that:
1. Downloads audio from any public YouTube video
2. Transcribes the audio to text using OpenAI's Whisper (running locally)
3. Generates a concise summary using Phi-4-mini or Mistral-7B models (running locally)
4. Outputs results in both JSON and human-readable formats

**Key Feature**: All AI processing happens completely offline after initial setup. No API keys, no cloud services, no internet required for the core functionality.

## 🏗️ Architecture & Design Choices

### System Components

```
┌─────────────────┐
│  YouTube URL    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│  YouTube Downloader (yt-dlp)    │
│  - Extracts audio track          │
│  - Converts to WAV format        │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Offline Transcriber (Whisper)  │
│  - Speech-to-Text conversion    │
│  - Multi-language support        │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│      Mistral-7b                 │
│  - Abstractive summarization    │
│  - Intelligent chunking          │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Results (JSON + Text)          │
└─────────────────────────────────┘
```

### Model Selection & Justification

#### 1. Speech-to-Text: OpenAI Whisper

**Why Whisper?**
- **State-of-the-art accuracy**: Consistently outperforms other open-source STT models
- **Multilingual support**: Handles 99 languages out of the box
- **Robust to audio quality**: Trained on diverse, noisy audio data
- **Multiple size options**: Scale from 39M (tiny) to 1.5B (large) parameters
- **Active maintenance**: Well-supported by OpenAI and community

**Model Size Trade-offs**:
- `tiny` (39M params): ~32x faster, 70% accuracy - good for quick tests
- `base` (74M params): ~16x faster, 80% accuracy - **recommended default**
- `small` (244M params): ~6x faster, 85% accuracy - best balance
- `medium` (769M params): ~2x faster, 90% accuracy - high accuracy
- `large` (1550M params): baseline speed, 95% accuracy - maximum accuracy

**Default Choice**: `medium` model provides the best speed/accuracy balance for most use cases.

#### 2. Summarization: Lightweight offline models

- **Mistral 7B Instruct (4-bit quantized)**

- **LLaMA 3 8B Instruct (4-bit)**

- **Phi-3 Mini (3B) → insanely fast, still good quality**

 **Best pick**:


Because:
- ✔ Extremely fast on CPU
- ✔ Good summarization quality
- ✔ Perfect for an offline pipeline

**Default Choice**: `Phi-3 Mini (3B) 4-bit quantized` for best quality summaries.

### Design Decisions & Trade-offs

#### 1. **Modular Architecture**
- **Decision**: Separate modules for downloading, transcribing, and summarizing
- **Rationale**: Allows independent testing, easier maintenance, and potential reuse
- **Trade-off**: Slightly more complex than a monolithic script, but much more maintainable

#### 2. **WAV Format for Audio**
- **Decision**: Convert all audio to WAV format
- **Rationale**: Uncompressed format ensures maximum quality for transcription
- **Trade-off**: Larger file sizes (~10MB per minute), but better accuracy

#### 3. **Chunk-based Processing**
- **Decision**: Split long transcripts into chunks for summarization
- **Rationale**: Models have input length limits (1024 tokens for BART)
- **Trade-off**: May lose some context between chunks, but handles videos of any length

#### 4. **Beam Search for Summarization**
- **Decision**: Use beam search with 4 beams by default
- **Rationale**: Better quality than greedy decoding without excessive computation
- **Trade-off**: 4x slower than greedy search, but significantly better results

#### 5. **CPU/GPU Auto-detection**
- **Decision**: Automatically use GPU if available, fall back to CPU
- **Rationale**: Maximize performance without requiring user configuration
- **Trade-off**: May need manual override in some edge cases

## 📋 Prerequisites

### System Requirements

- **Python**: 3.12
- **RAM**: 8GB minimum (16GB recommended for large models)
- **Storage**: 5GB for models + space for audio files
- **GPU**: Optional but recommended (10-50x speedup for transcription)


## 🚀 Setup and Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/shardsnaik/Utube_ved_summarizer.git
cd Utube_ved_summarizer
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
venv\Scripts\activate
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Note**: This will install PyTorch. If you have a GPU and want to use it:
```bash
# For CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Step 4: Download AI Models

Run the setup script to download required models:

```bash
python setup.py
```

This will:
1. Check your system configuration
2. Verify FFmpeg installation
3. Download Whisper model (you can choose size)
4. Download BART summarization model
5. Create necessary directories

**First-time setup takes 5-15 minutes** depending on your internet speed and chosen models.

### Directory Structure

After setup, your project should look like:

```
youtube-video-summarizer/
├── main.py               # Main CLI application
├── app.py                # Web interface (Gradio) ⭐ NEW
├── setup.py              # Setup and model download script
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── src/                  # Source code modules
│   ├── __init__.py
│   ├── vedio_downloader.py  # YouTube audio downloader
│   ├── SST_transcribe.py    # Whisper speech-to-text
│   └── summarizer_model.py  # BART summarization
├── output/              # Generated results
│   └── audio/           # Downloaded audio files
└── models/              # Cached AI models (auto-created)
```

## 💻 Usage

### Option 1: Gradio Web Interface (Recommended) 🎨

**Beautiful, modern web UI with real-time progress:**

```bash
python app.py
```

Then open your browser to `http://127.0.0.1:7860`

**Features**:
- 🎨 Beautiful gradient design
- 📊 Real-time progress tracking
- 📑 Tabbed results display
- 📱 Mobile responsive
- 🎯 Pre-loaded examples
- 💾 Easy export options


## 📚 Documentation

This project includes comprehensive documentation:

- **[README.md](README.md)** - Complete guide (you are here)
- **[DOCKER_GUIDE.md](DOCKER_GUIDE.md)** - Complete Docker deployment guide 🐳
- **[INTERFACE_COMPARISON.md](INTERFACE_COMPARISON.md)** - Compare CLI vs Web vs Docker
- **[PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)** - Architecture & design details
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - One-page cheat sheet 📄

---

### Option 2: Command Line Interface

**For automation and scripting:**

```bash
python main.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### Advanced Options

**CLI Options:**

```bash
# Limit video duration (e.g., 600 seconds = 10 minutes)
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --max-duration 600

# Custom output directory
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --output my_results

# Verbose logging (for debugging)
python main.py "https://www.youtube.com/watch?v=VIDEO_ID" --verbose
```

**Gradio Options:**
- Set max duration in the UI
- Choose summary length (Short/Medium/Long)
- View results in organized tabs
- Export as JSON automatically

### Full Command-Line Options

```bash
python main.py --help
```

**Arguments**:
- `url` (required): YouTube video URL
- `--max-duration SECONDS`: Skip videos longer than this (default: no limit)
- `--output DIR`: Output directory (default: `output`)
- `--verbose`: Enable detailed logging

### Example Session

**Using Gradio Interface (Recommended):**

```bash
$ python app.py

================================================================================
YouTube Video Summarizer - Gradio Interface
================================================================================

Initializing AI models (this may take a moment)...

✅ Models loaded successfully!

Starting Gradio interface...
================================================================================
Running on local URL:  http://127.0.0.1:7860
```

Then in your browser:
1. Paste YouTube URL
2. Set options (duration, summary length)
3. Click "Process Video"
4. View results in beautiful tabs

---

**Using CLI:**

```bash
$ python main.py "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

================================================================================
Offline YouTube Video Summarizer
================================================================================

[INFO] Downloading audio from: https://www.youtube.com/watch?v=dQw4w9WgXcQ
[INFO] Video: Never Gonna Give You Up
[INFO] Duration: 212s
[INFO] Audio downloaded successfully

[INFO] Transcribing audio...
[INFO] Using device: cuda
[INFO] Transcription complete: 1543 characters

[INFO] Generating summary...
[INFO] Summary generated: 287 characters

================================================================================
RESULTS
================================================================================
Video: Never Gonna Give You Up
Duration: 212s

SUMMARY:
The video features a music performance with lyrics about commitment and 
emotional honesty. The performer pledges unwavering loyalty and promises 
never to disappoint or abandon their partner, emphasizing reliability and 
dedication in the relationship.

================================================================================
✓ Complete! Results saved to: output/
```

### Output Files

The application generates:

1. **results_TIMESTAMP.json**: Complete results in JSON format
   ```json
   {
     "url": "...",
     "video_title": "...",
     "duration": 212,
     "transcript": "...",
     "summary": "...",
     "timestamp": "2024-01-15T10:30:00"
   }
   ```

2. **summary_TIMESTAMP.txt**: Human-readable summary
   ```
   Video: Never Gonna Give You Up
   URL: https://www.youtube.com/watch?v=...
   Duration: 212s
   Processed: 2024-01-15T10:30:00
   
   ================================================================================
   SUMMARY
   ================================================================================
   
   [Summary text here]
   ```

## 🔧 Configuration

### Changing AI Models

Edit the model initialization in `params.yaml`:

```python

  summarizer_model_path : 'models\microsoft_Phi-4-mini-instruct-Q4_K_L.gguf'
  summarizer_max_context: 10000
  gpu_layers: 0    
  max_words: 8000
  .....
  ..... 

```


### Performance Benchmarks

Approximate processing times (on a typical laptop):

| Video Length | Model Size | CPU Time | GPU Time (CUDA) |
|--------------|-----------|----------|-----------------|
| 5 minutes    | base      | 10 min   | 30 sec          |
| 5 minutes    | small     | 25 min   | 1 min           |
| 10 minutes   | base      | 20 min   | 1 min           |
| 30 minutes   | base      | 60 min   | 3 min           |

*GPU times assume NVIDIA RTX 3060 or similar*

## 🧪 Testing

### Test with a Sample Video

```bash
# Short educational video (~3 minutes)
python main.py "https://www.youtube.com/watch?v=aircAruvnKk"

# TED talk (~18 minutes)
python main.py "https://www.youtube.com/watch?v=c0m6yaGlZh4" --max-duration 600
```


## 🎯 Design Choices and Justification

### 1. Speech-to-Text (Transcription) Model Selection

**Chosen Model: `OpenAI Whisper (Offline)`, size = configurable (Tiny → Large)**

**Why Whisper?**

I selected Whisper because it provides the best balance of accuracy, robustness, and offline capability among publicly available ASR (Automatic Speech Recognition) models. The core reasons:

**1. Offline & Secure** : Whisper runs entirely on-device with no network dependency, which is ideal for privacy-sensitive offline YouTube summarization.

**2. High Accuracy on Real-World Audio** : YouTube videos include noise, music, accents, and long-form speech. Whisper is known to be extremely robust under such variations.

**3. Multiple Model Sizes → Flexible Trade-offs** : Whisper provides:
- tiny: ultra-fast but lower accuracy
- base/small: real-time speed with good accuracy
- medium/large: highest accuracy for long YouTube lectures

This flexibility allowed me to choose a model based on available hardware.

**4. Stable + Widely Adopted** : Whisper is actively used in production systems and offers stable APIs, which reduces integration risk.

### 2. Summarization Model Selection

**Chosen Model: `Phi-4-Mini / Phi-3-Mini (Quantized GGUF)`**


**Why This LLM?**

**1. Quantized model → fast CPU execution** : Running on llama.cpp allows 4-bit quantization (Q4_K_M or Q4_K_L). This drastically reduces memory usage while keeping accuracy high.

**2. Small but high-quality model** : Phi models punch above their parameter size—they deliver high reasoning and summarization quality while being small enough to run offline.

**3. Large Context Window Support** : YouTube transcripts can be thousands of words long.
My summarizer supports hierarchical chunking → summarizing segments → combining them into a final structured summary.
(Logic shown in chunk_text, summarize_chunk, and summarize_final). 

**4. Deterministic Output** : The temperature is set to 0.2 for stable summarization, avoiding randomness.

**5. Integration Simplicity** : llama.cpp API made it easy to load quantized models in a single line:

```
self.llm = Llama(model_path=model_path, n_ctx=max_context)
```

## 🎯 Challenges Faced & Solutions

### Challenge 1: Memory Management with Long Videos
**Problem**: YouTube transcripts can exceed model context limits (4k–8k tokens). Directly sending a full transcript causes Context overflow, model truncation and ram spikes

**Solution**: Implemented intelligent chunking:
- Split transcripts into overlapping chunks
- Summarize each chunk independently
- Combine chunk summaries with final summarization pass
- Allows processing videos of any length

### Challenge 2: Model Loading on CPU (Slow Performance Initially)
**Problem**: Full models require 5-10GB download, slow for users.

**Solution**: 
- Provide multiple model size options
- Default to smaller but capable models
- Switched to quantized GGUF models (Q4_K_M, Q4_K_L).
- Reduced `gpu_layers` to 0 to ensure compatibility.
- Used `n_threads` for parallel CPU optimization.

### Challenge 3: Transcription Accuracy Variability
**Problem**: Some YouTube videos had background music, echo, or fast speakers.
Whisper tiny/base struggled with accuracy.....

**Solution**:
- Use Whisper's robust noise-handling
- Convert to uncompressed WAV for best quality
- upgraded to Whisper medium / large for difficult videos.(larger = more accurate)



## 🔒 Privacy & Security

- **Fully Offline**: After initial setup, no internet connection required
- **Local Processing**: All data stays on your machine
- **No Tracking**: No analytics or telemetry
- **Open Source**: Audit the code yourself
