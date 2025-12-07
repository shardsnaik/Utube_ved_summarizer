FROM python:3.11-slim

# 1) System setup
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# llama-cpp needs build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 2) Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3) Copy app code and model
COPY . .

# # If model is placed in /app/models/...
# ENV MODEL_PATH=/app/medgemma-4b-it-finnetunned-merged_new_for_cpu_q5_k_m.gguf
# # 4. (Optional but recommended) Create virtual env inside container
# RUN python -m venv /opt/venv
# ENV PATH="/opt/venv/bin:$PATH"

# EXPOSE 7860
EXPOSE 5000

# 4) Start FastAPI via uvicorn (App Runner will hit port 8000)
CMD ["python", "flask_app.py"]
