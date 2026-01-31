FROM python:3.11-slim

WORKDIR /app

# FFmpeg ইনস্টলেশন (যা কোয়ালিটি মার্জ করার জন্য দরকার)
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "600", "app:app"]
