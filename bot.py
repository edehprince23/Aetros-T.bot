from dotenv import load_dotenv
import os
import time
import threading
import requests
from flask import Flask
from telegram import Bot

from utils.data import get_candles
from utils.indicators import calculate_indicators
from utils.signals import check_signal

# Load env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

print("DEBUG TOKEN:", TELEGRAM_TOKEN)
print("DEBUG CHAT:", CHAT_ID)
print("DEBUG ALPHA:", ALPHA_VANTAGE_KEY)

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Missing TELEGRAM_TOKEN or CHAT_ID")

bot = Bot(token=TELEGRAM_TOKEN)

# 🔥 CRYPTO (FAST LOOP)
CRYPTO_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT", "LTCUSDT",
    "LINKUSDT", "DOTUSDT", "TRXUSDT", "ATOMUSDT", "NEARUSDT",
    "FILUSDT", "APTUSDT", "ARBUSDT", "OPUSDT", "SANDUSDT"
]

# 💱 FOREX (SLOW LOOP - Alpha Vantage)
FOREX_PAIRS = ["EURUSD", "GBPUSD", "USDJPY"]

# 📊 STOCKS
STOCKS = ["AAPL", "TSLA", "NVDA"]

def send_signal(market, pair, direction, score):
    message = f"📊 {market} SIGNAL\nPair: {pair}\nDirection: {direction}\nConfidence: {score}%"
    bot.send_message(chat_id=CHAT_ID, text=message)

# =========================
# 🔥 CRYPTO LOOP (FAST)
# =========================
def run_crypto():
    while True:
        try:
            for pair in CRYPTO_PAIRS:
                df = get_candles(pair)
                df = calculate_indicators(df)

                direction, score = check_signal(df)

                if direction and score >= 75:
                    send_signal("CRYPTO", pair, direction, score)

                time.sleep(1)  # prevent rate limit

            time.sleep(30)

        except Exception as e:
            print("Crypto Error:", e)
            time.sleep(10)

# =========================
# 💱 FOREX LOOP (SLOW)
# =========================
def get_forex_data(pair):
    base = pair[:3]
    quote = pair[3:]

    url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={base}&to_symbol={quote}&interval=1min&apikey={ALPHA_VANTAGE_KEY}"
    data = requests.get(url).json()

    try:
        ts = data["Time Series FX (1min)"]
        latest = list(ts.values())[0]
        close = float(latest["4. close"])

        return close
    except:
        return None

def run_forex():
    while True:
        try:
            for pair in FOREX_PAIRS:
                price = get_forex_data(pair)

                if price:
                    # simple logic (placeholder)
                    if price % 2 > 1:
                        send_signal("FOREX", pair, "BUY", 70)
                    else:
                        send_signal("FOREX", pair, "SELL", 70)

                time.sleep(12)  # respect 5 req/min limit

        except Exception as e:
            print("Forex Error:", e)

# =========================
# 📊 STOCK LOOP (SLOW)
# =========================
def get_stock_data(symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey={ALPHA_VANTAGE_KEY}"
    data = requests.get(url).json()

    try:
        ts = data["Time Series (1min)"]
        latest = list(ts.values())[0]
        close = float(latest["4. close"])

        return close
    except:
        return None

def run_stocks():
    while True:
        try:
            for symbol in STOCKS:
                price = get_stock_data(symbol)

                if price:
                    if price % 2 > 1:
                        send_signal("STOCK", symbol, "BUY", 65)
                    else:
                        send_signal("STOCK", symbol, "SELL", 65)

                time.sleep(12)

        except Exception as e:
            print("Stock Error:", e)

# =========================
# 🌐 FLASK (RAILWAY)
# =========================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running (Crypto + Forex + Stocks)"

# =========================
# 🚀 START EVERYTHING
# =========================
if __name__ == "__main__":
    threading.Thread(target=run_crypto).start()
    threading.Thread(target=run_forex).start()
    threading.Thread(target=run_stocks).start()

    app.run(host="0.0.0.0", port=5000)
