import os
import asyncio
from telegram import Bot
from telegram.error import TelegramError

BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN')

async def send_file_to_user(chat_id, filepath, filename):
    """Send downloaded file to user"""
    bot = Bot(token=BOT_TOKEN)
    try:
        with open(filepath, 'rb') as f:
            if filename.endswith('.mp3'):
                await bot.send_audio(chat_id=chat_id, audio=f)
            else:
                await bot.send_video(chat_id=chat_id, video=f)
        return True
    except TelegramError as e:
        print(f"Error sending file: {e}")
        return False

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 3:
        chat_id = sys.argv[1]
        filepath = sys.argv[2]
        filename = sys.argv[3]
        asyncio.run(send_file_to_user(chat_id, filepath, filename))
