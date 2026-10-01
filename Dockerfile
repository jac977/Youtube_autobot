FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir google-genai requests pytube

CMD ["python", "main.py"]
