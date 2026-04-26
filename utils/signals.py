def check_signal(df):
    last = df.iloc[-1]

    score = 0
    direction = None

    # RSI logic
    if last["rsi"] < 30:
        score += 40
        direction = "BUY"
    elif last["rsi"] > 70:
        score += 40
        direction = "SELL"

    # EMA trend
    if last["ema9"] > last["ema21"]:
        score += 30
    elif last["ema9"] < last["ema21"]:
        score += 30

    return direction, score
