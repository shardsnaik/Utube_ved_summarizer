"""
YouTube Video Summarizer - Beautiful Flask App
Complete one-page application with modern design
Run with: python flask_app.py
"""

from flask import Flask, render_template_string, request, jsonify, session
import logging
from pathlib import Path
import json
from datetime import datetime
import threading
import uuid

# Use YOUR actual imports
from src.vedio_downloader import YouTubeDownloader
from src.SST_transcribe import OfflineTranscriber
from src.summarizer_model import OfflineSummarizer

# Setup
app = Flask(__name__)
app.secret_key = 'youtube-summarizer-secret-key-change-this'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# ✅ Available SST (Whisper) Models


# ✅ Lazy-load model registry
AVAILABLE_SST_MODELS = ["tiny", "base", "small", "medium"]
AVAILABLE_SUMMARIZER_MODELS = ["phi", "Mistral-7B"]

# ✅ Runtime caches (empty at startup)
transcribers = {}
summarizers = {}

# ✅ Thread locks to prevent double-loading
sst_lock = threading.Lock()
summarizer_lock = threading.Lock()

output_dir = Path("output")

# Store processing jobs
jobs = {}

# Beautiful HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video Summarizer</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        :root {
            --primary: #667eea;
            --secondary: #764ba2;
            --success: #10b981;
            --error: #ef4444;
            --warning: #f59e0b;
            --bg: #0f172a;
            --surface: #1e293b;
            --text: #f1f5f9;
            --text-muted: #94a3b8;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.6;
        }

        /* Animated background */
        .bg-animation {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.15;
            background: 
                radial-gradient(circle at 20% 50%, var(--primary) 0%, transparent 50%),
                radial-gradient(circle at 80% 50%, var(--secondary) 0%, transparent 50%);
            animation: pulse 15s ease-in-out infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 0.15; }
            50% { opacity: 0.25; }
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        /* Header */
        .header {
            text-align: center;
            padding: 3rem 0;
            margin-bottom: 3rem;
        }

        .header h1 {
            font-size: 3rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 1rem;
            animation: slideDown 0.6s ease;
        }

        .header p {
            font-size: 1.2rem;
            color: var(--text-muted);
            animation: slideDown 0.8s ease;
        }

        @keyframes slideDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        /* Card */
        .card {
            background: var(--surface);
            border-radius: 20px;
            padding: 2.5rem;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
            animation: fadeIn 1s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }

        /* Input Group */
        .input-group {
            margin-bottom: 1.5rem;
        }

        .input-group label {
            display: block;
            margin-bottom: 0.5rem;
            color: var(--text);
            font-weight: 600;
            font-size: 0.95rem;
        }

        .input-group input,
        .input-group select {
            width: 100%;
            padding: 1rem;
            background: rgba(255, 255, 255, 0.05);
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            color: var(--text);
            font-size: 1rem;
            transition: all 0.3s ease;
        }

        .input-group input:focus,
        .input-group select:focus {
            outline: none;
            border-color: var(--primary);
            background: rgba(255, 255, 255, 0.08);
            box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.1);
        }

        /* Button */
        .btn {
            width: 100%;
            padding: 1.2rem;
            background: linear-gradient(135deg, var(--primary), var(--secondary));
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn:disabled {
            background: linear-gradient(135deg, #4b5563, #6b7280);
            cursor: not-allowed;
            transform: none;
        }

        .btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.2);
            transition: left 0.5s ease;
        }

        .btn:hover::before {
            left: 100%;
        }
        .select-opt{
        color:black;

        }

        /* Status Box */
        .status-box {
            margin-top: 2rem;
            padding: 1.5rem;
            border-radius: 12px;
            display: none;
            animation: slideUp 0.5s ease;
        }

        @keyframes slideUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .status-box.show {
            display: block;
        }

        .status-box.processing {
            background: rgba(245, 158, 11, 0.1);
            border: 2px solid var(--warning);
        }

        .status-box.success {
            background: rgba(16, 185, 129, 0.1);
            border: 2px solid var(--success);
        }

        .status-box.error {
            background: rgba(239, 68, 68, 0.1);
            border: 2px solid var(--error);
        }

        /* Progress Bar */
        .progress-bar {
            width: 100%;
            height: 6px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
            overflow: hidden;
            margin: 1rem 0;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--secondary));
            width: 0%;
            transition: width 0.3s ease;
            animation: shimmer 2s infinite;
        }

        @keyframes shimmer {
            0% { opacity: 0.8; }
            50% { opacity: 1; }
            100% { opacity: 0.8; }
        }

        /* Results Section */
        .results {
            margin-top: 2rem;
            display: none;
        }

        .results.show {
            display: block;
            animation: fadeIn 0.5s ease;
        }

        .result-tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }

        .tab-btn {
            padding: 1rem 1.5rem;
            background: transparent;
            border: none;
            color: var(--text-muted);
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
            font-size: 0.95rem;
            font-weight: 600;
        }

        .tab-btn:hover {
            color: var(--text);
        }

        .tab-btn.active {
            color: var(--primary);
            border-bottom-color: var(--primary);
        }

        .tab-content {
            display: none;
            padding: 1.5rem;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            max-height: 500px;
            overflow-y: auto;
        }

        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }

        .tab-content h3 {
            color: var(--primary);
            margin-bottom: 1rem;
        }

        .tab-content p {
            margin-bottom: 0.5rem;
            line-height: 1.8;
        }

        /* Spinner */
        .spinner {
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid var(--primary);
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 1rem auto;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Scrollbar */
        .tab-content::-webkit-scrollbar {
            width: 8px;
        }

        .tab-content::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 4px;
        }

        .tab-content::-webkit-scrollbar-thumb {
            background: var(--primary);
            border-radius: 4px;
        }

        /* Info Badge */
        .info-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            background: rgba(102, 126, 234, 0.2);
            color: var(--primary);
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.5rem;
        }

        /* Footer */
        .footer {
            text-align: center;
            padding: 2rem 0;
            color: var(--text-muted);
            font-size: 0.9rem;
        }

        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 2rem;
            }

            .card {
                padding: 1.5rem;
            }

            .result-tabs {
                flex-wrap: wrap;
            }

            .tab-btn {
                flex: 1 1 auto;
                padding: 0.75rem 1rem;
            }
        }
    </style>
</head>
<body>
    <div class="bg-animation"></div>
    
    <div class="container">
        <div class="header">
            <h1>🎥 YouTube Video Summarizer</h1>
            <p>Offline AI-Powered Transcription & Summarization</p>
        </div>
        <div class="input-group">
    <label for="sstModel">Speech-to-Text Model</label>
    <select id="sstModel">
        <option value="tiny">Tiny (Fastest)</option>
        <option value="base">Base</option>
        <option value="small">Small</option>
        <option value="medium" selected>Medium (Best)</option>
    </select>
</div>

<div class="input-group">
    <label for="summarizerModel">Summarization Model</label>
    <div >
    <select id="summarizerModel" class='select-opt'>
        <option value="phi" selected>Phi</option>
        <option value="Mistral-7B">Mistral-7B</option>
    </select>
    </div>
</div>

        <div class="card">
            <form id="processForm">
                <div class="input-group">
                    <label for="url">YouTube URL</label>
                    <input 
                        type="text" 
                        id="url" 
                        name="url" 
                        placeholder="https://www.youtube.com/watch?v=..."
                        required
                    >
                </div>
                

                <div class="input-group">
                    <label for="maxDuration">Max Duration (seconds) - Optional</label>
                    <input 
                        type="number" 
                        id="maxDuration" 
                        name="maxDuration" 
                        placeholder="Leave empty for no limit"
                    >
                </div>

                <div class="input-group">
                    <label for="summaryLength">Summary Length</label>
                    <select id="summaryLength" name="summaryLength">
                        <option value="1000">Short (50-100 words)</option>
                        <option value="5500" selected>Medium (100-200 words)</option>
                        <option value="10000">Long (200-400 words)</option>
                    </select>
                </div>

                <button type="submit" class="btn" id="submitBtn">
                    🚀 Process Video
                </button>
            </form>

            <div id="statusBox" class="status-box">
                <div id="statusMessage"></div>
                <div class="progress-bar">
                    <div id="progressFill" class="progress-fill"></div>
                </div>
                <div id="spinner" class="spinner" style="display:none;"></div>
            </div>

            <div id="results" class="results">
                <div class="result-tabs">
                    <button class="tab-btn active" onclick="showTab('info')">📹 Video Info</button>
                    <button class="tab-btn" onclick="showTab('transcript')">📝 Transcript</button>
                    <button class="tab-btn" onclick="showTab('summary')">✨ Summary</button>
                </div>

                <div id="infoTab" class="tab-content active"></div>
                <div id="transcriptTab" class="tab-content"></div>
                <div id="summaryTab" class="tab-content"></div>
            </div>
        </div>

        <div class="footer">
            Built with ❤️ using Flask, Whisper & Phi-4 | All processing happens offline
        </div>
    </div>

    <script>
        let pollInterval;

        function showTab(tabName) {
            // Remove active class from all buttons and contents
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

            // Add active class to selected tab
            event.target.classList.add('active');
            document.getElementById(tabName + 'Tab').classList.add('active');
        }

        document.getElementById('processForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const url = document.getElementById('url').value;
            const maxDuration = document.getElementById('maxDuration').value;
            const summaryLength = document.getElementById('summaryLength').value;

            const submitBtn = document.getElementById('submitBtn');
            const statusBox = document.getElementById('statusBox');
            const statusMessage = document.getElementById('statusMessage');
            const spinner = document.getElementById('spinner');
            const results = document.getElementById('results');

            // Reset UI
            submitBtn.disabled = true;
            statusBox.className = 'status-box show processing';
            statusMessage.textContent = 'Starting...';
            spinner.style.display = 'block';
            results.classList.remove('show');
            document.getElementById('progressFill').style.width = '0%';

            try {
                // Start processing
                const response = await fetch('/process', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        url, 
                        max_duration: maxDuration || null,
                        summary_length: summaryLength
                    })
                });

                const data = await response.json();

                if (data.status === 'started') {
                    const jobId = data.job_id;
                    pollStatus(jobId);
                } else {
                    throw new Error(data.error || 'Failed to start processing');
                }
            } catch (error) {
                statusBox.className = 'status-box show error';
                statusMessage.textContent = '❌ Error: ' + error.message;
                spinner.style.display = 'none';
                submitBtn.disabled = false;
            }
        });

        async function pollStatus(jobId) {
            pollInterval = setInterval(async () => {
                try {
                    const response = await fetch(`/status/${jobId}`);
                    const data = await response.json();

                    const statusMessage = document.getElementById('statusMessage');
                    const progressFill = document.getElementById('progressFill');
                    const spinner = document.getElementById('spinner');
                    const statusBox = document.getElementById('statusBox');
                    const submitBtn = document.getElementById('submitBtn');
                    const results = document.getElementById('results');

                    if (data.status === 'processing') {
                        statusMessage.textContent = data.message;
                        progressFill.style.width = data.progress + '%';
                    } else if (data.status === 'completed') {
                        clearInterval(pollInterval);
                        statusBox.className = 'status-box show success';
                        statusMessage.textContent = '✅ Processing complete!';
                        spinner.style.display = 'none';
                        progressFill.style.width = '100%';

                        // Show results
                        displayResults(data.result);
                        results.classList.add('show');
                        submitBtn.disabled = false;
                    } else if (data.status === 'error') {
                        clearInterval(pollInterval);
                        statusBox.className = 'status-box show error';
                        statusMessage.textContent = '❌ Error: ' + data.error;
                        spinner.style.display = 'none';
                        submitBtn.disabled = false;
                    }
                } catch (error) {
                    console.error('Polling error:', error);
                }
            }, 1000);
        }

        function displayResults(result) {
            // Video Info
            const infoTab = document.getElementById('infoTab');
            infoTab.innerHTML = `
                <h3>Video Information</h3>
                <p><strong>Title:</strong> ${result.video_title}</p>
                <p><strong>Duration:</strong> ${result.duration} seconds (${Math.floor(result.duration / 60)} min ${result.duration % 60} sec)</p>
                <p><strong>Transcript Length:</strong> <span class="info-badge">${result.transcript.length} characters</span></p>
            `;

            // Transcript
            const transcriptTab = document.getElementById('transcriptTab');
            transcriptTab.innerHTML = `
                <h3>Full Transcript</h3>
                <p>${result.transcript}</p>
            `;

            // Summary
            const summaryTab = document.getElementById('summaryTab');
            summaryTab.innerHTML = `
                <h3>Generated Summary</h3>
                <p><span class="info-badge">${result.summary.split(' ').length} words</span></p>
                <p>${result.summary}</p>
            `;
        }
    </script>
</body>
</html>
"""



def process_video_background(job_id, url, max_duration, summary_length, sst_model, summarizer_model):
    try:
        jobs[job_id]['status'] = 'processing'
        jobs[job_id]['message'] = 'Downloading audio...'
        jobs[job_id]['progress'] = 10

        audio_info = downloader.download(url, max_duration=max_duration)

        jobs[job_id]['message'] = f'Loading SST model: {sst_model}'
        jobs[job_id]['progress'] = 25
        transcriber = get_transcriber(sst_model)

        jobs[job_id]['message'] = f'Transcribing using {sst_model} model...'
        jobs[job_id]['progress'] = 50
        transcript = transcriber.transcribe(audio_info['path'])

        jobs[job_id]['message'] = f'Loading summarizer: {summarizer_model}'
        jobs[job_id]['progress'] = 65
        summarizer = get_summarizer(summarizer_model, summary_length)

        jobs[job_id]['message'] = f'Generating summary using {summarizer_model} model...'
        jobs[job_id]['progress'] = 85
        summary = summarizer.summarize(transcript)

        results = {
            'url': url,
            'timestamp': datetime.now().isoformat(),
            'video_title': audio_info['title'],
            'duration': audio_info['duration'],
            'sst_model': sst_model,
            'summarizer_model': summarizer_model,
            'transcript': transcript,
            'summary': summary
        }

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = output_dir / f"results_{timestamp}.json"

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        jobs[job_id]['status'] = 'completed'
        jobs[job_id]['progress'] = 100
        jobs[job_id]['result'] = results

    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)



@app.route('/')
def index():
    """Serve the main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process():
    data = request.json

    url = data.get('url')
    max_duration = data.get('max_duration')
    summary_length = int(data.get('summary_length', 5500))

    sst_model = data.get('sst_model', 'medium')
    summarizer_model = data.get('summarizer_model', 'phi')

    if not url:
        return jsonify({'status': 'error', 'error': 'No URL provided'}), 400

    if sst_model not in AVAILABLE_SST_MODELS:
        return jsonify({'status': 'error', 'error': 'Invalid SST model'}), 400

    if summarizer_model not in AVAILABLE_SUMMARIZER_MODELS:
        return jsonify({'status': 'error', 'error': 'Invalid summarizer model'}), 400

    if max_duration:
        try:
            max_duration = int(max_duration)
        except:
            max_duration = None

    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        'status': 'starting',
        'message': 'Initializing...',
        'progress': 0
    }

    thread = threading.Thread(
        target=process_video_background,
        args=(job_id, url, max_duration, summary_length, sst_model, summarizer_model)
    )
    thread.daemon = True
    thread.start()

    return jsonify({'status': 'started', 'job_id': job_id})


@app.route('/status/<job_id>')
def status(job_id):
    """Get job status"""
    if job_id not in jobs:
        return jsonify({'status': 'error', 'error': 'Job not found'}), 404
    
    return jsonify(jobs[job_id])


def main():
    """Initialize and run the Flask app"""
    global downloader, transcriber, summarizer, output_dir
    
    print("="*80)
    print("YouTube Video Summarizer - Flask App")
    print("="*80)
    print()
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize models
    print("Initializing AI models (this may take a moment)...")
    print()
    
    try:
        print("  [1/3] Loading YouTube downloader...")
        downloader = YouTubeDownloader(output_dir=str(output_dir / "audio"))
        print("        ✓ Downloader ready")
        
        # print("  [2/3] Preparing SST models...")
        # for key, model_size in AVAILABLE_SST_MODELS.items():
        #     transcribers[key] = OfflineTranscriber(model_size=model_size, device='cpu')
        #     print(f"        ✓ SST {model_size} loaded")
        
        # print("  [3/3] Preparing Summarizers...")
        # for key in AVAILABLE_SUMMARIZER_MODELS:
        #     summarizers[key] = OfflineSummarizer(model_name=key)
        #     print(f"        ✓ Summarizer {key} loaded")

        print()
        print("="*80)
        print("✅ All models loaded successfully!")
        print("="*80)
        print()
        
    except Exception as e:
        print(f"\n❌ Failed to initialize models: {e}")
        print("\nPlease ensure all models are downloaded.")
        return 1
    
    print("Starting Flask server...")
    print("="*80)
    print()
    print("Access the application at: http://localhost:5000")
    print("Press Ctrl+C to stop")
    print()
    
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)
    # app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)



def get_transcriber(model_name: str):
    if model_name not in AVAILABLE_SST_MODELS:
        raise ValueError("Invalid SST model")

    with sst_lock:
        if model_name not in transcribers:
            print(f"🔥 Loading SST model on-demand: {model_name}")
            transcribers[model_name] = OfflineTranscriber(model_size=model_name, device='cpu')
        return transcribers[model_name]


def get_summarizer(model_name: str, summary_length:int):
    if model_name not in AVAILABLE_SUMMARIZER_MODELS:
        raise ValueError("Invalid summarizer model")

    with summarizer_lock:
        if model_name not in summarizers:
            print(f"🔥 Loading Summarizer on-demand: {model_name}")
            summarizers[model_name] = OfflineSummarizer(model_path=model_name,max_context=summary_length)
        return summarizers[model_name]



if __name__ == "__main__":
    main()