import telebot
import os
from moviepy.editor import ImageClip, AudioFileClip
from flask import Flask, request
import threading

TOKEN = os.environ.get('BOT_TOKEN')  # توکن رو در env variables بگذار
bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

BASE_DIR = '/tmp/bot_files'  # در Render فایل سیستم موقت هست
os.makedirs(BASE_DIR, exist_ok=True)

user_data = {}

# هندلرها (همون قبلی)
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام! اول یک عکس بفرست، بعد یک آهنگ (audio یا voice).")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    user_id = message.from_user.id
    file_id = message.photo[-1].file_id
    file = bot.get_file(file_id)
    downloaded_file = bot.download_file(file.file_path)
    
    image_path = os.path.join(BASE_DIR, f"{user_id}_image.jpg")
    with open(image_path, 'wb') as f:
        f.write(downloaded_file)
    
    user_data[user_id] = {'image': image_path}
    bot.reply_to(message, "عکس دریافت شد! حالا آهنگ بفرست.")

@bot.message_handler(content_types=['audio', 'voice'])
def handle_audio(message):
    user_id = message.from_user.id
    
    if user_id not in user_data or 'image' not in user_data[user_id]:
        bot.reply_to(message, "اول عکس بفرست!")
        return
    
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
    
    bot.reply_to(message, "در حال ساخت ویدیو...")
    
    try:
        audio_clip = AudioFileClip(audio_path)
        image_clip = ImageClip(image_path).set_duration(audio_clip.duration)
        video_clip = image_clip.set_audio(audio_clip)
        video_clip.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
        
        with open(output_path, 'rb') as video:
            bot.send_video(message.chat.id, video, supports_streaming=True)
        
        bot.reply_to(message, "ویدیو آماده شد!")
    
    except Exception as e:
        bot.reply_to(message, f"خطا: {str(e)}")
    
    finally:
        for path in [image_path, audio_path, output_path]:
            if os.path.exists(path):
                os.remove(path)
        if user_id in user_data:
            del user_data[user_id]

# روت اصلی برای health check Render
@app.route('/')
def index():
    return "ربات فعاله!"

# وب هوک
@app.route('/' + TOKEN, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

if __name__ == "__main__":
    # ست کردن وب هوک (در یک ترد جدا)
    bot.remove_webhook()
    bot.set_webhook(url=f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}/{TOKEN}")
    
    # ران کردن Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
