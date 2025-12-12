FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# فقط این خط مهم هست (اسم فایل واقعی رو کپی می‌کنه)
COPY Bot.py bot.py

EXPOSE 8000

# این خط رو قبلاً درست کردیم
CMD gunicorn --bind 0.0.0.0:$PORT bot:app