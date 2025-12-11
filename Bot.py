import telebot
import os
from moviepy.editor import ImageClip, AudioFileClip
import shutil

# توکن رباتت رو از @BotFather بگیر و اینجا بذار
TOKEN = '8507871471:AAHIgNT4eeBQgkLLeXIjv86Ql0SCib7ffv8'
bot = telebot.TeleBot(TOKEN)

# پوشه موقت برای فایل‌ها
BASE_DIR = '/storage/emulated/0/Download/bot_files'
os.makedirs(BASE_DIR, exist_ok=True)

# دیکشنری برای نگهداری وضعیت کاربر (عکس منتظر آهنگ)
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام! اول یک عکس بفرست، بعد یک آهنگ (audio یا voice). من یک ویدیو با عکس ثابت و اون آهنگ می‌سازم و برات می‌فرستم.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    file_id = message.photo[-1].file_id  # بهترین کیفیت
    file = bot.get_file(file_id)
    downloaded_file = bot.download_file(file.file_path)
    
    image_path = os.path.join(BASE_DIR, f"{user_id}_image.jpg")
    with open(image_path, 'wb') as f:
        f.write(downloaded_file)
    
    user_data[user_id] = {'image': image_path}
    bot.reply_to(message, "عکس دریافت شد! حالا یک آهنگ (audio یا voice) بفرست.")

@bot.message_handler(content_types=['audio', 'voice'])
def handle_audio(message):
    user_id = message.from_user.id
    
    if user_id not in user_data or 'image' not in user_data[user_id]:
        bot.reply_to(message, "اول باید عکس بفرستی!")
        return
    
    # گرفتن فایل آهنگ
    if message.audio:
        file_id = message.audio.file_id
    elif message.voice:
        file_id = message.voice.file_id
    else:
        return
    
    file = bot.get_file(file_id)
    downloaded_file = bot.download_file(file.file_path)
    
    audio_path = os.path.join(BASE_DIR, f"{user_id}_audio.mp3")
    with open(audio_path, 'wb') as f:
        f.write(downloaded_file)
    
    image_path = user_data[user_id]['image']
    output_path = os.path.join(BASE_DIR, f"{user_id}_output.mp4")
    
    bot.reply_to(message, "در حال ساخت ویدیو... صبر کن (ممکنه چند ثانیه طول بکشه)")
    
    try:
        # ساخت ویدیو با moviepy
        audio_clip = AudioFileClip(audio_path)
        image_clip = ImageClip(image_path).set_duration(audio_clip.duration)
        video_clip = image_clip.set_audio(audio_clip)
        video_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
        
        # ارسال ویدیو
        with open(output_path, 'rb') as video:
            bot.send_video(message.chat.id, video, supports_streaming=True)
        
        bot.reply_to(message, "ویدیو آماده شد!")
        
    except Exception as e:
        bot.reply_to(message, f"خطا رخ داد: {str(e)}")
    
    finally:
        # پاک کردن فایل‌های موقت
        for path in [image_path, audio_path, output_path]:
            if os.path.exists(path):
                os.remove(path)
        if user_id in user_data:
            del user_data[user_id]

print("ربات در حال اجراست...")
bot.infinity_polling()
