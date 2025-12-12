# استفاده از ایمیج سبک پایتون
FROM python:3.11-slim

# نصب ffmpeg و ابزارهای لازم
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# پوشه کاری
WORKDIR /app

# کپی requirements و نصب پکیج‌ها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد
COPY Bot.py .

# پورت
EXPOSE 8000

# اجرا
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "bot:app"]