from dotenv import load_dotenv
import os
import time
import threading
from flask import Flask
from telegram import Bot

from utils.data import get_candles
from utils.indicators import calculate_indicators
from utils.signals import check_signal

# Load env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

print("DEBUG TOKEN:", TELEGRAM_TOKEN)
print("DEBUG CHAT:", CHAT_ID)

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Missing TELEGRAM_TOKEN or CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# 🔥 MULTI-PAIR (UPGRADED)
PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
    "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
    "MATICUSDT", "LTCUSDT"
]

def send_signal(pair, direction, score):
    message = f"📊 SIGNAL\nPair: {pair}\nDirection: {direction}\nConfidence: {score}%"
    bot.send_message(chat_id=CHAT_ID, text=message)

def run():
    while True:
        try:
            for pair in PAIRS:
                df = get_candles(pair)
                df = calculate_indicators(df)

                direction, score = check_signal(df)

                if direction and score >= 75:
                    send_signal(pair, direction, score)

            time.sleep(60)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

# Railway server
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

if __name__ == "__main__":
    threading.Thread(target=run).start()
    app.run(host="0.0.0.0", port=5000)
