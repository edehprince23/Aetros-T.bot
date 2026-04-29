from dotenv import load_dotenv
import os
import time
import threading
import requests
import pandas as pd

from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# =========================
# LOAD ENV
# =========================
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY")

print("TOKEN:", TELEGRAM_TOKEN)
print("CHAT_ID:", CHAT_ID)

if not TELEGRAM_TOKEN or not CHAT_ID:
    raise ValueError("Missing TELEGRAM_TOKEN or CHAT_ID")

# VERY IMPORTANT FIX
CHAT_ID = int(CHAT_ID)

bot = Bot(token=TELEGRAM_TOKEN)

# =========================
# PAIRS
# =========================
CRYPTO_PAIRS = [
    "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","ADAUSDT","DOGEUSDT",
    "AVAXUSDT","MATICUSDT","LTCUSDT","LINKUSDT","DOTUSDT","TRXUSDT",
    "ATOMUSDT","NEARUSDT","FILUSDT","APTUSDT","ARBUSDT","OPUSDT","SANDUSDT",
    "AAVEUSDT","GALAUSDT","EGLDUSDT","FTMUSDT","ALGOUSDT"
]

FOREX_PAIRS = [
    "EURUSD","GBPUSD","USDJPY","AUDUSD","USDCAD",
    "USDCHF","NZDUSD","EURGBP","EURJPY","GBPJPY"
]

STOCKS = [
    "AAPL","TSLA","NVDA","AMZN","META","GOOGL","MSFT","NFLX"
]

# =========================
# INDICATORS
# =========================
def calculate_indicators(df):
    df["ema9"] = df["close"].ewm(span=9).mean()
    df["ema21"] = df["close"].ewm(span=21).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()

    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    return df

# =========================
# SIGNAL LOGIC
# =========================
def check_signal(df):
    last = df.iloc[-1]

    if last["ema9"] > last["ema21"] and last["rsi"] < 65:
        return "BUY", 75

    if last["ema9"] < last["ema21"] and last["rsi"] > 35:
        return "SELL", 75

    return None, 0

# =========================
# DATA FETCH
# =========================
def get_crypto_data(pair):
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=5m&limit=100"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns=[
        "time","open","high","low","close","volume",
        "ct","qav","nt","tbbav","tbqav","ignore"
    ])

    df["close"] = df["close"].astype(float)
    return df

def get_alpha_data(symbol, is_fx=False):
    if is_fx:
        base, quote = symbol[:3], symbol[3:]
        url = f"https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol={base}&to_symbol={quote}&interval=5min&apikey={ALPHA_VANTAGE_KEY}"
    else:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=5min&apikey={ALPHA_VANTAGE_KEY}"

    data = requests.get(url).json()

    try:
        key = list(data.keys())[1]
        ts = data[key]

        closes = [float(v["4. close"]) for v in ts.values()]
        df = pd.DataFrame({"close": closes[::-1]})
        return df
    except:
        return None

# =========================
# SEND MESSAGE
# =========================
def send_signal(market, pair, direction, score):
    try:
        msg = f"📊 {market}\n{pair}\n{direction} ({score}%)"
        bot.send_message(chat_id=CHAT_ID, text=msg)
    except Exception as e:
        print("Send error:", e)

# =========================
# LOOPS
# =========================
def run_crypto():
    while True:
        for pair in CRYPTO_PAIRS:
            try:
                df = get_crypto_data(pair)
                df = calculate_indicators(df)

                direction, score = check_signal(df)

                if direction:
                    send_signal("CRYPTO", pair, direction, score)

                time.sleep(1)

            except Exception as e:
                print("Crypto error:", e)

        time.sleep(20)

def run_forex():
    while True:
        for pair in FOREX_PAIRS:
            try:
                df = get_alpha_data(pair, True)

                if df is not None:
                    df = calculate_indicators(df)
                    direction, score = check_signal(df)

                    if direction:
                        send_signal("FOREX", pair, direction, score)

                time.sleep(12)

            except Exception as e:
                print("Forex error:", e)

def run_stocks():
    while True:
        for s in STOCKS:
            try:
                df = get_alpha_data(s)

                if df is not None:
                    df = calculate_indicators(df)
                    direction, score = check_signal(df)

                    if direction:
                        send_signal("STOCK", s, direction, score)

                time.sleep(12)

            except Exception as e:
                print("Stock error:", e)

# =========================
# TELEGRAM
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is LIVE!")

def run_telegram():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))

    print("Telegram running...")
    app.run_polling()

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    # background loops
    threading.Thread(target=run_crypto, daemon=True).start()
    threading.Thread(target=run_forex, daemon=True).start()
    threading.Thread(target=run_stocks, daemon=True).start()

    # TELEGRAM MUST RUN IN MAIN THREAD
    run_telegram()
