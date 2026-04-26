def check_signal(df):
    last = df.iloc[-1]

    score = 0
    direction = None

    # =========================
    # TREND (STRONG FILTER)
    # =========================
    if last["ema50"] > last["ema200"]:
        trend = "UP"
        score += 20
    elif last["ema50"] < last["ema200"]:
        trend = "DOWN"
        score += 20
    else:
        return None, 0

    # =========================
    # RSI
    # =========================
    if trend == "UP" and 40 < last["rsi"] < 70:
        score += 15
        direction = "BUY"

    elif trend == "DOWN" and 30 < last["rsi"] < 60:
        score += 15
        direction = "SELL"

    # =========================
    # EMA MOMENTUM
    # =========================
    if trend == "UP" and last["ema9"] > last["ema21"]:
        score += 15
    elif trend == "DOWN" and last["ema9"] < last["ema21"]:
        score += 15

    # =========================
    # MACD CONFIRMATION
    # =========================
    if trend == "UP" and last["macd"] > last["signal"]:
        score += 20
    elif trend == "DOWN" and last["macd"] < last["signal"]:
        score += 20

    # =========================
    # VOLUME FILTER
    # =========================
    if last["volume"] > last["volume_avg"]:
        score += 10

    # =========================
    # FINAL DECISION
    # =========================
    if score >= 70:
        return direction, score

    return None, score
