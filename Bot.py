import telebot
import os
import subprocess
from flask import Flask, request
import telebot.types

# توکن از محیط
TOKEN = os.environ.get('BOT_TOKEN')
if not TOKEN:
    print("خطا: BOT_TOKEN تنظیم نشده!")
    exit(1)

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# پوشه موقت (در داکر قابل نوشتنه)
BASE_DIR = '/tmp'
user_data = {}

# پیام شروع
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام! 👋\nاول یک عکس بفرست، بعد یک آهنگ (audio یا voice)\nمن یک ویدیو با عکس ثابت + آهنگ می‌سازم و برات می‌فرستم.")

# دریافت عکس
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_path = f"{BASE_DIR}/{user_id}_image.jpg"
    with open(image_path, 'wb') as f:
        f.write(downloaded_file)

    user_data[user_id] = {'image': image_path}
    bot.reply_to(message, "عکس دریافت شد! حالا یک آهنگ بفرست 🎵")

# دریافت آهنگ و ساخت ویدیو
@bot.message_handler(content_types=['audio', 'voice'])
def handle_audio(message):
    user_id = message.from_user.id

    if user_id not in user_data:
        bot.reply_to(message, "اول باید عکس بفرستی!")
        return

    # دریافت فایل صوتی
    file_id = message.audio.file_id if message.audio else message.voice.file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    audio_path = f"{BASE_DIR}/{user_id}_audio.mp3"
    output_path = f"{BASE_DIR}/{user_id}_output.mp4"
    image_path = user_data[user_id]['image']

    with open(audio_path, 'wb') as f:
        f.write(downloaded_file)

    bot.reply_to(message, "در حال ساخت ویدیو... لطفاً صبر کن ⏳")

    try:
        # دستور ffmpeg (سریع، پایدار و بدون مشکل)
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-i', image_path,
            '-i', audio_path,
            '-c:v', 'libx264', '-tune', 'stillimage', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '192k',
            '-shortest', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2',
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            bot.reply_to(message, f"خطا در ffmpeg:\n{result.stderr[:500]}")
            return

        # ارسال ویدیو
        with open(output_path, 'rb') as video:
            bot.send_video(message.chat.id, video, supports_streaming=True, timeout=300)

        bot.reply_to(message, "ویدیو آماده شد!")

    except Exception as e:
        bot.reply_to(message, f"خطا: {str(e)}")

    finally:
        # پاک کردن فایل‌ها
        for path in [image_path, audio_path, output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
        user_data.pop(user_id, None)

# صفحه اصلی (برای keep-alive)
@app.route('/')
def home():
    return "ربات ویدیوساز فعاله!"

# وب‌هوک
@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Forbidden', 403

# تنظیم وب‌هوک موقع استارت (بدون before_first_request)
def setup_webhook():
    import time
    time.sleep(3)  # یه کم صبر می‌کنه تا Render دامنه رو بده
    bot.remove_webhook()
    hostname = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
    if hostname:
        url = f"https://{hostname}/{TOKEN}"
        try:
            bot.set_webhook(url=url)
            print(f"وب‌هوک با موفقیت تنظیم شد: {url}")
        except Exception as e:
            print(f"خطا در تنظیم وب‌هوک: {e}")
    else:
        print("RENDER_EXTERNAL_HOSTNAME پیدا نشد! وب‌هوک تنظیم نشد.")

# این تابع رو موقع استارت صدا می‌زنیم
setup_webhook()

# فقط برای هلث چک (Render این رو می‌بینه و sleep نمی‌کنه)
@app.route('/')
def home():
    return "ربات ویدیوساز فعاله!"

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

# این خط آخر باشه (gunicorn خودش اجرا می‌کنه، نیازی به if __name__ نیست)