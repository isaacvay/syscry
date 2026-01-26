import requests
import ta
import pandas as pd
import time
from model.predict import predict_direction, predict_with_market_analysis
from cache import cache
from config import settings
from logger import logger
from typing import Optional
from exceptions import CircuitBreaker, BinanceAPIError, InsufficientDataError, DataQualityError

# Import constants and exceptions
try:
    from constants import (
        BINANCE_API_TIMEOUT, MAX_RETRIES, RETRY_MIN_WAIT, RETRY_MAX_WAIT,
        MIN_DATA_POINTS, MIN_PRICE, MAX_PRICE, MIN_VOLUME,
        ERROR_BINANCE_API, ERROR_INSUFFICIENT_DATA
    )
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

# Global circuit breaker for Binance API
binance_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)
binance_circuit_breaker.service_name = "Binance API"


class EnhancedDataFetcher:
    """
    Enhanced data fetcher with retry logic, circuit breaker, and data validation
    """
    
    def __init__(self):
        self.circuit_breaker = binance_circuit_breaker
        self.base_url = "https://api.binance.com/api/v3"
    
    def fetch_market_data(self, symbol: str, interval: str, limit: int = 1000) -> pd.DataFrame:
        """
        Fetch market data with enhanced error handling and validation
        
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
        
        # Use circuit breaker for API calls
        try:
            df = self.circuit_breaker.call(self._fetch_from_api, symbol, interval, limit)
            
            # Validate and clean data
            df = self.validate_data_quality(df, symbol)
            
            # Cache the result
            cache.set(cache_key, df, ttl=settings.cache_ttl)
            logger.info(f"Successfully fetched {len(df)} candles for {symbol} {interval}")
            
            return df
            
        except Exception as e:
            # Try cache fallback if available
            if cached_data is not None:
                logger.warning(f"API failed, using stale cache for {symbol} {interval}")
                return cached_data
            raise
    
    def _fetch_from_api(self, symbol: str, interval: str, limit: int) -> pd.DataFrame:
        """
        Internal method to fetch data from Binance API with retry logic
        """
        url = f"{self.base_url}/klines?symbol={symbol}&interval={interval}&limit={limit}"
        
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
                        f"Insufficient data: got {len(data) if data else 0} candles, need at least {MIN_DATA_POINTS}",
                        required=MIN_DATA_POINTS,
                        received=len(data) if data else 0,
                        symbol=symbol
                    )
                
                # Parse data
                df = pd.DataFrame(data)
                # Binance returns: [Open time, Open, High, Low, Close, Volume, ...]
                df = df.iloc[:, :6]
                df.columns = ["timestamp", "open", "high", "low", "close", "volume"]
                
                # Convert to numeric
                numeric_columns = ["close", "high", "low", "open", "volume", "timestamp"]
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
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
        raise BinanceAPIError(
            f"Failed to fetch data after {MAX_RETRIES} attempts: {last_exception}",
            symbol=symbol,
            attempt=MAX_RETRIES
        )
    
    def validate_data_quality(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Validate and clean data quality
        
        Args:
            df: Raw DataFrame from API
            symbol: Symbol for error context
            
        Returns:
            Cleaned DataFrame
            
        Raises:
            DataQualityError: If data cannot be cleaned
        """
        quality_issues = {}
        
        # Check for NaN values
        if df.isnull().any().any():
            null_counts = df.isnull().sum()
            quality_issues["null_values"] = null_counts[null_counts > 0].to_dict()
            logger.warning(f"Data contains NaN values for {symbol}: {quality_issues['null_values']}")
            
            # Fill NaN with forward fill, then backward fill
            df = df.fillna(method='ffill').fillna(method='bfill')
            
            # If still has NaN, raise error
            if df.isnull().any().any():
                raise DataQualityError(
                    f"Unable to fill NaN values for {symbol}",
                    symbol=symbol,
                    quality_issues=quality_issues
                )
        
        # Validate price ranges
        price_columns = ['open', 'high', 'low', 'close']
        for col in price_columns:
            if col in df.columns:
                invalid_prices = (df[col] < MIN_PRICE) | (df[col] > MAX_PRICE)
                if invalid_prices.any():
                    quality_issues[f"invalid_{col}_prices"] = invalid_prices.sum()
        
        if quality_issues.get("invalid_close_prices", 0) > 0:
            raise DataQualityError(
                f"Invalid price data for {symbol}: prices out of valid range",
                symbol=symbol,
                quality_issues=quality_issues
            )
        
        # Validate volume
        if 'volume' in df.columns:
            invalid_volume = df['volume'] < MIN_VOLUME
            if invalid_volume.any():
                quality_issues["invalid_volume"] = invalid_volume.sum()
                logger.warning(f"Invalid volume data for {symbol}: {quality_issues['invalid_volume']} records")
        
        # Validate OHLC logic
        ohlc_issues = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        )
        
        if ohlc_issues.any():
            quality_issues["ohlc_logic_errors"] = ohlc_issues.sum()
            logger.warning(f"OHLC logic errors for {symbol}: {quality_issues['ohlc_logic_errors']} records")
        
        # Log quality summary
        if quality_issues:
            logger.info(f"Data quality issues resolved for {symbol}: {quality_issues}")
        
        return df


# Global enhanced data fetcher instance
enhanced_data_fetcher = EnhancedDataFetcher()


def get_binance_data(symbol="BTCUSDT", interval="1h", limit=1000):
    """
    Fetch data from Binance API with enhanced error handling
    
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
    return enhanced_data_fetcher.fetch_market_data(symbol, interval, limit)

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

    # Enhanced Signal Logic - NO NEUTRAL, always choose BUY or SELL
    if prob > 0.60 and last["rsi"] < settings.rsi_oversold: 
        signal = "BUY"
    elif prob < 0.40 and last["rsi"] > settings.rsi_overbought:
        signal = "SELL"
    elif prob > settings.confidence_threshold and last["close"] > last["ema20"]:
        signal = "BUY (Trend)"
    elif prob < (1 - settings.confidence_threshold) and last["close"] < last["ema20"]:
        signal = "SELL (Trend)"
    else:
        # Instead of NEUTRE, choose based on probability and trend
        if prob > 0.5:
            if last["close"] > last["ema20"]:
                signal = "BUY"
            else:
                signal = "BUY (Weak)"
        else:
            if last["close"] < last["ema20"]:
                signal = "SELL"
            else:
                signal = "SELL (Weak)"

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
