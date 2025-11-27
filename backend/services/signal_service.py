import ta
import pandas as pd
from model.predict import predict_direction
from cache import cache
from config import settings
from logger import logger
from indicators.signals import get_binance_data

def generate_signal_service(symbol, timeframe):
    """
    Generate signal for a given symbol and timeframe.
    This logic is moved from indicators/signals.py to be reusable.
    """
    clean_symbol = symbol.replace("/", "").upper()
    
    # 1. Fetch Data
    df = get_binance_data(clean_symbol, timeframe)
    
    if df.empty:
        return {"error": "Could not fetch data"}

    # 2. Calculate Indicators
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["macd"] = ta.trend.macd_diff(df["close"])
    
    # Additional indicators
    df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)
    stoch = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"])
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()
    df["adx"] = ta.trend.adx(df["high"], df["low"], df["close"], window=14)
    
    # Add sentiment features if enabled
    if settings.sentiment_enabled:
        try:
            from ml.sentiment_features import add_sentiment_features, get_crypto_name
            crypto_name = get_crypto_name(clean_symbol)
            df = add_sentiment_features(df, clean_symbol, crypto_name=crypto_name)
        except Exception as e:
            logger.warning(f"Could not add sentiment features: {e}")
            # Add default sentiment features to match training
            df['sentiment_score'] = 0.0
            df['sentiment_source_count'] = 0
            df['twitter_sentiment'] = 0.0
            df['twitter_positive_ratio'] = 0.5
            df['reddit_sentiment'] = 0.0
            df['reddit_positive_ratio'] = 0.5
            df['news_sentiment'] = 0.0
            df['news_positive_ratio'] = 0.5

    last = df.iloc[-1]

    # 3. AI Prediction
    prob = predict_direction(df, symbol=clean_symbol, interval=timeframe)

    # 4. Signal Logic
    signal = "NEUTRE"
    
    # Get thresholds from settings (DB or Config)
    # Note: For now using config settings, but ideally should fetch from DB if we want dynamic thresholds
    rsi_oversold = settings.rsi_oversold
    rsi_overbought = settings.rsi_overbought
    confidence_threshold = settings.confidence_threshold

    # Strong Buy: High prob + Oversold RSI
    if prob > 0.60 and last["rsi"] < rsi_oversold: 
        signal = "BUY"
    # Strong Sell: Low prob + Overbought RSI
    elif prob < 0.40 and last["rsi"] > rsi_overbought:
        signal = "SELL"
    # Trend Following Buy
    elif prob > confidence_threshold and last["close"] > last["ema20"]:
        signal = "BUY (Trend)"
    # Trend Following Sell
    elif prob < (1 - confidence_threshold) and last["close"] < last["ema20"]:
        signal = "SELL (Trend)"

    # 5. Format Data
    chart_data = []
    for index, row in df.iterrows():
        chart_data.append({
            "time": int(row["timestamp"] / 1000), # Convert ms to seconds
            "open": row["open"],
            "high": row["high"],
            "low": row["low"],
            "close": row["close"]
        })

    return {
        "symbol": symbol,
        "timeframe": timeframe,
        "signal": signal,
        "confidence": round(float(prob), 2),
        "price": last["close"],
        "indicators": {
            "rsi": round(float(last["rsi"]), 2),
            "ema20": round(float(last["ema20"]), 2),
            "ema50": round(float(last["ema50"]), 2),
            "macd": round(float(last["macd"]), 2),
            "atr": round(float(last["atr"]), 2),
            "stoch_k": round(float(last["stoch_k"]), 2),
            "stoch_d": round(float(last["stoch_d"]), 2),
            "adx": round(float(last["adx"]), 2)
        },
        "chart_data": chart_data
    }
