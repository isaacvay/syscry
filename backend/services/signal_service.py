import ta
import pandas as pd
from model.predict import predict_with_market_analysis
from cache import cache
from config import settings
from logger import logger
from indicators.signals import get_binance_data

def generate_signal_service(symbol, timeframe):
    """
    Generate signal for a given symbol and timeframe.
    Uses advanced market analysis logic from model.predict.
    """
    clean_symbol = symbol.replace("/", "").upper()
    
    # 1. Fetch Data
    df = get_binance_data(clean_symbol, timeframe)
    
    if df.empty:
        return {"error": "Could not fetch data"}

    # 2. Calculate Indicators (Basic ones for display/fallback)
    # Note: predict_with_market_analysis will calculate its own features, 
    # but we need these for the response payload
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["macd"] = ta.trend.macd_diff(df["close"])
    
    # Additional indicators for display
    df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)
    stoch = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"])
    df["stoch_k"] = stoch.stoch()
    df["stoch_d"] = stoch.stoch_signal()
    df["adx"] = ta.trend.adx(df["high"], df["low"], df["close"], window=14)
    
    # Add sentiment features if enabled
    sentiment_score = None
    if settings.sentiment_enabled:
        try:
            from ml.sentiment_features import add_sentiment_features, get_crypto_name
            crypto_name = get_crypto_name(clean_symbol)
            df = add_sentiment_features(df, clean_symbol, crypto_name=crypto_name)
            
            # Extract sentiment score for prediction
            if 'sentiment_score' in df.columns:
                sentiment_score = float(df['sentiment_score'].iloc[-1])
                
        except Exception as e:
            logger.warning(f"Could not add sentiment features: {e}")
            # Add default sentiment features to match training expectations if needed
            # But predict_with_market_analysis handles missing sentiment gracefully

    last = df.iloc[-1]

    # 3. AI Prediction & Signal Logic (Unified)
    try:
        prediction = predict_with_market_analysis(
            df=df, 
            symbol=clean_symbol, 
            interval=timeframe,
            sentiment_score=sentiment_score
        )
        
        signal = prediction['signal']
        confidence = prediction['probability'] # Use raw probability as confidence base
        
        # Map signal to display strings if needed, or keep Enum values
        # Frontend handles "BUY", "SELL", "STRONG_BUY", "STRONG_SELL"
        # The Enum returns uppercase strings which is perfect
        
    except Exception as e:
        logger.error(f"Error in market analysis: {e}")
        signal = "NEUTRE"
        confidence = 0.5

    # 5. Format Data
    chart_data = []
    # Optimize: Only take last 100 points for chart to reduce payload if needed
    # But usually full history in memory is small enough
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
        "confidence": round(float(confidence), 2),
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
