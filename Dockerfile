FROM python:3.10-slim

# FFmpeg install kar rahe hain media merge karne ke liye
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY . /app

# Pipeline ki sabhi required libraries
RUN pip install --no-cache-dir requests gTTS google-api-python-client google-auth-oauthlib google-auth-httplib2

CMD ["python", "main.py"]
