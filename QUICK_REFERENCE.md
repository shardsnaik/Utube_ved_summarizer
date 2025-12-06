# Quick Reference Card

One-page cheat sheet for the YouTube Video Summarizer.

## 🚀 Quick Start (30 seconds)

```bash
# 1. Install
pip install -r requirements.txt

# 2. Download models
python setup.py

# 3. Run (choose one)
python app.py    # Web UI (recommended)
python main.py "URL"     # Command line
```

---

## 🎨 Three Ways to Run

| Command | Access | Best For |
|---------|--------|----------|
| `python app.py` | `127.0.0.1:7860` | 👥 Interactive use |
| `python main.py "URL"` | Terminal | 🤖 Automation |

---

## 📝 Common Commands

### CLI Usage
```bash
# Basic
python main.py "https://youtube.com/watch?v=VIDEO_ID"

# With options
python main.py "URL" --max-duration 600 --output results

# Help
python main.py --help
```

### Gradio Usage
```bash
# Start server
python app.py

# Access in browser
http://127.0.0.1:7860

# Public link (temporary)
# Edit gradio_app.py: share=True
```


## 🔧 Configuration


**Options:**

**Whisper Models:**
- `tiny` - Fast, 70% accuracy
- `base` - Balanced (default)
- `small` - Better accuracy
- `medium` - High accuracy
- `large` - Best accuracy

**Summarization Models:**
- `Mistral 7B Instruct` (4-bit quantized)
- `LLaMA 3 8B Instruct` (4-bit)
- `Phi-3 Mini (3B)` → insanely fast, still good quality


### Output Directory
```bash
# CLI
python main.py "URL" --output my_results

# Or edit main.py line 16
summarizer = VideoSummarizer(output_dir="custom_path")
```

---

## 📊 Performance Benchmarks

### Processing Times (5-minute video)

| Hardware | Tiny | Base | Small | Medium |
|----------|------|------|-------|--------|
| **GPU (RTX 3060)** | 15s | 30s | 1m | 2m |
| **CPU (i7)** | 2m | 5m | 15m | 30m |

### Model Sizes

| Model | Download Size | RAM Usage |
|-------|--------------|-----------|
| Whisper tiny | 150 MB | 1 GB |
| Whisper base | 300 MB | 1 GB |
| Whisper small | 500 MB | 2 GB |
| BART large | 1.6 GB | 3 GB |

---


### Issue: "CUDA out of memory"
```bash
# Solution 1: Use smaller model
# Edit transcriber initialization:
transcriber = OfflineTranscriber(model_size='tiny')

# Solution 2: Force CPU
transcriber = OfflineTranscriber(device='cpu')

# Solution 3: Shorter videos
python main.py "URL" --max-duration 300
```

### Issue: "Port already in use"
```bash
# Gradio (default 7860)
lsof -i :7860
kill -9 PID

# Flask (default 5000)
lsof -i :5000
kill -9 PID

# Or change port in code
demo.launch(server_port=8080)
```

### Issue: Models not downloading
```bash
# Set proxy (if needed)
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=http://proxy:port

# Manual download
python -c "import whisper; whisper.load_model('base')"
```

---

## 📁 File Locations

### Output Files
```
output/
├── audio/
│   └── VIDEO_ID.wav           # Downloaded audio
├── results_TIMESTAMP.json     # Complete results
└── summary_TIMESTAMP.txt      # Readable summary
```

### Model Cache
```
~/.cache/huggingface/          # BART models
~/.cache/torch/                # PyTorch
~/.cache/whisper/              # Whisper models
```

### Logs
```
# In terminal (stdout)
# Or redirect to file:
python main.py "URL" > log.txt 2>&1
```

---

## 🎯 Example Videos (for testing)

| Video | Duration | Link | Good For |
|-------|----------|------|----------|
| 3Blue1Brown | 3m | `aircAruvnKk` | Educational |
| TED-Ed | 5m | Search TED-Ed | Clear audio |
| Interview | 10m | Your choice | Long content |

**Note:** Use the video ID or full URL

---

## 💡 Pro Tips

### Speed Up Processing
```bash
# 1. Use GPU (10-50x faster)
# 2. Use smaller models
# 3. Limit video duration
python main.py "URL" --max-duration 300

# 4. Process multiple videos in parallel
python main.py "URL1" & python main.py "URL2" &
```

### Save Disk Space
```bash
# Delete old audio files
rm output/audio/*.wav

# Keep models cached (don't delete ~/.cache/)
```

### Batch Processing
```bash
# Create video list
cat > videos.txt << EOF
https://youtube.com/watch?v=ID1
https://youtube.com/watch?v=ID2
EOF

# Process all
while read url; do
    python main.py "$url"
done < videos.txt
```

### Monitor GPU Usage
```bash
# Watch GPU in real-time
watch -n 1 nvidia-smi

# Or
nvidia-smi -l 1
```

---

## 🔐 Security Notes

### Safe Practices
- ✅ Use on private networks only
- ✅ Don't expose ports to internet without auth
- ✅ Keep models updated
- ✅ Use HTTPS in production

### Public Sharing (Gradio)
```python
# Temporary public link (72 hours)
demo.launch(share=True)

# With authentication
demo.launch(auth=("user", "pass"))
```

---

## 📱 Mobile Access

### On Same WiFi
```bash
# Find your IP
ifconfig | grep "inet "    # Mac/Linux
ipconfig                   # Windows

# Access from mobile
http://192.168.x.x:7860    # Gradio
http://192.168.x.x:5000    # Flask
```

---

## 🆘 Getting Help

### Check Logs
```bash
# Verbose mode
python main.py "URL" --verbose

# System test
python test_system.py

# Check specific component
python -c "from src.transcriber import OfflineTranscriber; print('OK')"
```

### Common Issues & Solutions

| Problem | Solution |
|---------|----------|
| Slow on CPU | Expected, use GPU or smaller model |
| Out of memory | Use smaller model or shorter video |
| Download fails | Check internet, try different video |
| Port in use | Change port or kill process |
| Models not found | Run `python setup.py` |

---

## 📚 Documentation

| File | Purpose |
|------|---------|
| `README.md` | Full documentation |
| `QUICKSTART.md` | 5-minute setup guide |

---

## ⌨️ Keyboard Shortcuts (Gradio)

| Key | Action |
|-----|--------|
| Tab | Navigate fields |
| Enter | Submit form |
| Ctrl+C | Stop server (terminal) |

---

## 🔄 Update Commands

```bash
# Update packages
pip install --upgrade -r requirements.txt

# Re-download models (if needed)
python setup.py

# Clear cache (if problems)
rm -rf ~/.cache/huggingface/
rm -rf ~/.cache/whisper/
```