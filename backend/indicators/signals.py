import requests
import ta
import pandas as pd
import time
from model.predict import predict_direction, predict_with_market_analysis
from cache import cache
from config import settings
from logger import logger
from typing import Optional

# Import constants and exceptions
try:
    from constants import (
        BINANCE_API_TIMEOUT, MAX_RETRIES, RETRY_MIN_WAIT, RETRY_MAX_WAIT,
        MIN_DATA_POINTS, MIN_PRICE, MAX_PRICE, MIN_VOLUME,
        ERROR_BINANCE_API, ERROR_INSUFFICIENT_DATA
    )
    from exceptions import BinanceAPIError, InsufficientDataError, DataQualityError
except ImportError:
    # Fallback values
    BINANCE_API_TIMEOUT = 15
    MAX_RETRIES = 3
    RETRY_MIN_WAIT = 1
    RETRY_MAX_WAIT = 10
    MIN_DATA_POINTS = 50
    MIN_PRICE = 0.00000001
    MAX_PRICE = 1000000000
    MIN_VOLUME = 0
    ERROR_BINANCE_API = "Binance API error"
    ERROR_INSUFFICIENT_DATA = "Insufficient data for analysis"
    
    class BinanceAPIError(Exception): pass
    class InsufficientDataError(Exception): pass
    class DataQualityError(Exception): pass


def get_binance_data(symbol="BTCUSDT", interval="1h", limit=1000):
    """
    Fetch data from Binance API with retry logic and validation
    
    Args:
        symbol: Trading pair symbol
        interval: Timeframe (1h, 4h, 1d, etc.)
        limit: Number of candles to fetch
        
    Returns:
        DataFrame with OHLCV data
        
    Raises:
        BinanceAPIError: If API request fails after retries
        InsufficientDataError: If not enough data returned
        DataQualityError: If data quality is poor
    """
    # Check cache first
    cache_key = f"binance_data_{symbol}_{interval}_{limit}"
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        logger.debug(f"Cache hit for {symbol} {interval}")
        return cached_data
    
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    
    # Retry logic with exponential backoff
    last_exception = None
    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"Fetching Binance data for {symbol} (attempt {attempt + 1}/{MAX_RETRIES})")
            
            response = requests.get(url, timeout=BINANCE_API_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            # Validate response
            if not data or len(data) < MIN_DATA_POINTS:
                raise InsufficientDataError(
                    f"Insufficient data: got {len(data) if data else 0} candles, need at least {MIN_DATA_POINTS}"
                )
            
            # Parse data
            df = pd.DataFrame(data)
            # Binance returns: [Open time, Open, High, Low, Close, Volume, ...]
            df = df.iloc[:, :6]
            df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
            
            # Convert to numeric
            df["close"] = pd.to_numeric(df["close"], errors='coerce')
            df["high"] = pd.to_numeric(df["high"], errors='coerce')
            df["low"] = pd.to_numeric(df["low"], errors='coerce')
            df["open"] = pd.to_numeric(df["open"], errors='coerce')
            df["volume"] = pd.to_numeric(df["volume"], errors='coerce')
            df["timestamp"] = pd.to_numeric(df["timestamp"], errors='coerce')
            
            # Data quality validation
            if df.isnull().any().any():
                null_counts = df.isnull().sum()
                logger.warning(f"Data contains NaN values: {null_counts[null_counts > 0].to_dict()}")
                # Fill NaN with forward fill, then backward fill
                df = df.fillna(method='ffill').fillna(method='bfill')
                
                # If still has NaN, raise error
                if df.isnull().any().any():
                    raise DataQualityError(f"Data quality error: unable to fill NaN values for {symbol}")
            
            # Validate price ranges
            if (df['close'] < MIN_PRICE).any() or (df['close'] > MAX_PRICE).any():
                raise DataQualityError(f"Invalid price data for {symbol}: prices out of valid range")
            
            # Validate volume
            if (df['volume'] < MIN_VOLUME).any():
                raise DataQualityError(f"Invalid volume data for {symbol}")
            
            # Cache the result
            cache.set(cache_key, df, ttl=settings.cache_ttl)
            logger.info(f"Successfully fetched {len(df)} candles for {symbol} {interval}")
            
            return df
            
        except requests.exceptions.Timeout as e:
            last_exception = e
            logger.warning(f"Binance API timeout for {symbol} (attempt {attempt + 1}/{MAX_RETRIES})")
            
        except requests.exceptions.RequestException as e:
            last_exception = e
            logger.warning(f"Binance API request error for {symbol}: {e} (attempt {attempt + 1}/{MAX_RETRIES})")
            
        except (InsufficientDataError, DataQualityError) as e:
            # Don't retry for data quality issues
            logger.error(f"Data validation error for {symbol}: {e}")
            raise
            
        except Exception as e:
            last_exception = e
            logger.error(f"Unexpected error fetching data for {symbol}: {e}")
        
        # Exponential backoff before retry
        if attempt < MAX_RETRIES - 1:
            wait_time = min(RETRY_MIN_WAIT * (2 ** attempt), RETRY_MAX_WAIT)
            logger.debug(f"Waiting {wait_time}s before retry...")
            time.sleep(wait_time)
    
    # All retries failed
    error_msg = f"{ERROR_BINANCE_API}: {last_exception}"
    logger.error(error_msg)
    raise BinanceAPIError(error_msg)

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
    
    try:
        df = get_binance_data(clean_symbol, timeframe)
    except (BinanceAPIError, InsufficientDataError, DataQualityError) as e:
        logger.error(f"Failed to fetch data for {clean_symbol}: {e}")
        return {"error": str(e)}
    except Exception as e:
        logger.error(f"Unexpected error fetching data for {clean_symbol}: {e}")
        return {"error": "Could not fetch data"}
    
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
