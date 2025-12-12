# نسخه سبک و بدون مشکل
FROM python:3.11-slim

# برای کاهش مصرف RAM و جلوگیری از بافر
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# فقط ffmpeg نصب می‌کنیم (کافیه!)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# پوشه کاری
WORKDIR /app

# نصب پکیج‌های پایتون
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# کپی کد (حتماً اسم فایل bot.py با b کوچک باشه!)
COPY Bot.py .

# پورت (Render خودش $PORT می‌ده)
EXPOSE 8000

# اجرا
CMD ["gunicorn", "--bind", "0.0.0.0:$PORT", "bot:app"]