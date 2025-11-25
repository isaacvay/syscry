import requests
import ta
import pandas as pd
from model.predict import predict_direction, predict_with_market_analysis
from cache import cache
from config import settings
from logger import logger
from typing import Optional

def get_binance_data(symbol="BTCUSDT", interval="1h", limit=1000):
    # Check cache first
    cache_key = f"binance_data_{symbol}_{interval}_{limit}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        # Binance returns: [Open time, Open, High, Low, Close, Volume, ...]
        df = df.iloc[:, :6]
        df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["open"] = df["open"].astype(float)
        df["volume"] = df["volume"].astype(float)
        
        # Cache the result
        cache.set(cache_key, df)
        
        return df
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {e}")
        return pd.DataFrame()

def generate_signal(symbol, timeframe, use_advanced_prediction=True, account_balance=None):
    """
    Generate trading signal with optional advanced prediction
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe for analysis
        use_advanced_prediction: Use market predictor with leverage/risk analysis
        account_balance: Account balance for position sizing
    """
    clean_symbol = symbol.replace("/", "").upper()
    
    df = get_binance_data(clean_symbol, timeframe)
    
    if df.empty:
        return {"error": "Could not fetch data"}

    # Calculate indicators
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

    last = df.iloc[-1]
    
    # Get sentiment if enabled
    sentiment_score = None
    if settings.sentiment_enabled:
        try:
            from ml.sentiment_analyzer import create_sentiment_analyzer
            from ml.sentiment_features import get_crypto_name
            
            sentiment_config = {
                'twitter_bearer_token': settings.twitter_bearer_token,
                'reddit_client_id': settings.reddit_client_id,
                'reddit_client_secret': settings.reddit_client_secret,
                'news_api_key': settings.news_api_key,
                'cache_ttl': settings.sentiment_cache_ttl
            }
            
            analyzer = create_sentiment_analyzer(sentiment_config)
            crypto_name = get_crypto_name(clean_symbol)
            sentiment_data = analyzer.get_aggregated_sentiment(clean_symbol, crypto_name)
            sentiment_score = sentiment_data['aggregated_sentiment']
        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            sentiment_score = None

    # Use advanced prediction if enabled
    if use_advanced_prediction:
        try:
            balance = account_balance or settings.default_account_balance
            prediction = predict_with_market_analysis(
                df, clean_symbol, timeframe, balance, sentiment_score
            )
            
            signal = prediction['signal']
            confidence = prediction['probability']
            
            # Format data for charts
            chart_data = []
            for index, row in df.iterrows():
                chart_data.append({
                    "time": int(row["timestamp"] / 1000),
                    "open": row["open"],
                    "high": row["high"],
                    "low": row["low"],
                    "close": row["close"]
                })
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "signal": signal,
                "confidence": round(float(confidence), 4),
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
                "chart_data": chart_data,
                # Advanced prediction fields
                "leverage": prediction.get('leverage'),
                "stop_loss": prediction.get('stop_loss'),
                "take_profit": prediction.get('take_profit'),
                "risk_reward_ratio": prediction.get('risk_reward_ratio'),
                "position_size": prediction.get('position_size'),
                "quantity": prediction.get('quantity'),
                "sentiment": sentiment_score
            }
        except Exception as e:
            logger.error(f"Advanced prediction failed: {e}, falling back to basic")
            # Fall through to basic prediction
    
    # Basic prediction (original logic)
    prob = predict_direction(df, symbol=clean_symbol, interval=timeframe)

    signal = "NEUTRE"
    
    # Signal Logic (using config settings)
    if prob > 0.60 and last["rsi"] < settings.rsi_oversold: 
        signal = "BUY"
    elif prob < 0.40 and last["rsi"] > settings.rsi_overbought:
        signal = "SELL"
    elif prob > settings.confidence_threshold and last["close"] > last["ema20"]:
        signal = "BUY (Trend)"
    elif prob < (1 - settings.confidence_threshold) and last["close"] < last["ema20"]:
        signal = "SELL (Trend)"

    # Format data for charts
    chart_data = []
    for index, row in df.iterrows():
        chart_data.append({
            "time": int(row["timestamp"] / 1000),
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
        "chart_data": chart_data,
        "sentiment": sentiment_score
    }
