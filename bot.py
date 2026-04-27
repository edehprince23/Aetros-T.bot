from dotenv import load_dotenv
import os
import time
import threading
import requests
import pandas as pd

from flask import Flask
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

# Convert chat_id to int (IMPORTANT FIX)
CHAT_ID = int(CHAT_ID)

bot = Bot(token=TELEGRAM_TOKEN)

# =========================
# PAIRS (40+)
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
    df["ema_9"] = df["close"].ewm(span=9).mean()
    df["ema_21"] = df["close"].ewm(span=21).mean()

    delta = df["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = -delta.clip(upper=0).rolling(14).mean()

    rs = gain / loss
    df["rsi"] = 100 - (100 / (1 + rs))

    return df

# =========================
# SIGNAL LOGIC (REAL)
# =========================
def check_signal(df):
    last = df.iloc[-1]

    # Trend
    if last["ema_9"] > last["ema_21"]:
        trend = "UP"
    elif last["ema_9"] < last["ema_21"]:
        trend = "DOWN"
    else:
        return None, 0

    # RSI filter
    if trend == "UP" and last["rsi"] < 65:
        return "BUY", 75

    if trend == "DOWN" and last["rsi"] > 35:
        return "SELL", 75

    return None, 0

# =========================
# BINANCE DATA
# =========================
def get_crypto_data(pair):
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=5m&limit=100"
    data = requests.get(url).json()

    df = pd.DataFrame(data, columns
