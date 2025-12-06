# transcribe_q4_with_subprocess.py
import subprocess
import shlex
import sys
from pathlib import Path

MODEL_PATH = Path("models/ggml-small-q4_0.bin")   # change to your model file
AUDIO_PATH = Path("audio/input.wav")              # change to your audio file
WHISPER_BIN = Path("whisper.cpp/main")            # path to whisper.cpp executable (or main.exe on Windows)

if not MODEL_PATH.exists():
    print("Model file not found:", MODEL_PATH)
    sys.exit(1)
if not AUDIO_PATH.exists():
    print("Audio file not found:", AUDIO_PATH)
    sys.exit(1)
if not WHISPER_BIN.exists():
    print("whisper.cpp binary not found at", WHISPER_BIN)
    print("Build whisper.cpp (see https://github.com/ggerganov/whisper.cpp).")
    sys.exit(1)

# build the CLI command. -m model -f file -otxt prints plain text output
cmd = f"{WHISPER_BIN} -m {shlex.quote(str(MODEL_PATH))} -f {shlex.quote(str(AUDIO_PATH))} -otxt"

print("Running:", cmd)
proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)

if proc.returncode != 0:
    print("whisper.cpp failed:")
    print(proc.stderr)
    sys.exit(proc.returncode)

# whisper.cpp writes transcript to stdout or to output file (depending on flags).
print("Transcription result:\n")
print(proc.stdout)
