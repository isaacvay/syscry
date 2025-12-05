import pandas as pd
import numpy as np
import ta

def create_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create advanced features for ML model
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        DataFrame with additional features
    """
    df = df.copy()
    
    # ========== BASIC PRICE FEATURES ==========
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
    
    # Lagged returns
    for lag in [1, 2, 3, 5, 10]:
        df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
    
    # ========== MOMENTUM MULTI-SCALE ==========
    # Rate of Change (ROC) at different periods
    for period in [3, 7, 14, 21]:
        df[f'roc_{period}'] = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100
    
    # Price momentum
    df['momentum_1h'] = df['close'] / df['close'].shift(1) - 1
    df['momentum_4h'] = df['close'] / df['close'].shift(4) - 1
    df['momentum_24h'] = df['close'] / df['close'].shift(24) - 1
    
    # ========== ADVANCED VOLATILITY ==========
    # Standard volatility
    df['volatility_10'] = df['returns'].rolling(10).std()
    df['volatility_20'] = df['returns'].rolling(20).std()
    df['volatility_50'] = df['returns'].rolling(50).std()
    
    # Parkinson volatility (uses high-low range)
    df['parkinson_vol'] = np.sqrt(
        (1 / (4 * np.log(2))) * 
        ((np.log(df['high'] / df['low'])) ** 2).rolling(20).mean()
    )
    
    # Garman-Klass volatility (more accurate)
    df['gk_vol'] = np.sqrt(
        0.5 * ((np.log(df['high'] / df['low'])) ** 2).rolling(20).mean() -
        (2 * np.log(2) - 1) * ((np.log(df['close'] / df['open'])) ** 2).rolling(20).mean()
    )
    
    # ========== VOLUME FEATURES ==========
    df['volume_change'] = df['volume'].pct_change()
    df['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    
    # VWAP (Volume Weighted Average Price)
    df['vwap'] = (df['volume'] * (df['high'] + df['low'] + df['close']) / 3).cumsum() / df['volume'].cumsum()
    df['price_to_vwap'] = (df['close'] - df['vwap']) / df['vwap']
    
    # Volume momentum
    df['volume_momentum'] = df['volume'] / df['volume'].shift(5) - 1
    
    # Volume delta (buying vs selling pressure approximation)
    df['volume_delta'] = df['volume'] * np.sign(df['close'] - df['open'])
    df['volume_delta_ma'] = df['volume_delta'].rolling(10).mean()
    
    # ========== MARKET MICROSTRUCTURE ==========
    # High-Low spread
    df['hl_spread'] = (df['high'] - df['low']) / df['close']
    
    # Body to range ratio (candle body strength)
    df['body_range_ratio'] = abs(df['close'] - df['open']) / (df['high'] - df['low'] + 1e-10)
    
    # Upper and lower shadows
    df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / (df['high'] - df['low'] + 1e-10)
    df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / (df['high'] - df['low'] + 1e-10)
    
    # ========== CANDLESTICK PATTERNS ==========
    # Doji (small body)
    df['is_doji'] = (abs(df['close'] - df['open']) / (df['high'] - df['low'] + 1e-10) < 0.1).astype(int)
    
    # Hammer/Hanging Man (long lower shadow)
    df['is_hammer'] = ((df['lower_shadow'] > 0.6) & (df['upper_shadow'] < 0.1)).astype(int)
    
    # Bullish/Bearish engulfing
    df['bullish_engulfing'] = (
        (df['close'] > df['open']) & 
        (df['close'].shift(1) < df['open'].shift(1)) &
        (df['close'] > df['open'].shift(1)) &
        (df['open'] < df['close'].shift(1))
    ).astype(int)
    
    df['bearish_engulfing'] = (
        (df['close'] < df['open']) & 
        (df['close'].shift(1) > df['open'].shift(1)) &
        (df['close'] < df['open'].shift(1)) &
        (df['open'] > df['close'].shift(1))
    ).astype(int)
    
    # ========== TECHNICAL INDICATORS ==========
    if 'rsi' not in df.columns:
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    
    if 'macd' not in df.columns:
        df['macd'] = ta.trend.macd_diff(df['close'])
    
    # Additional RSI periods
    df['rsi_6'] = ta.momentum.rsi(df['close'], window=6)
    df['rsi_24'] = ta.momentum.rsi(df['close'], window=24)
    
    # RSI momentum
    df['rsi_momentum'] = df['rsi'] - df['rsi'].shift(5)
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['close'])
    df['bb_high'] = bollinger.bollinger_hband()
    df['bb_low'] = bollinger.bollinger_lband()
    df['bb_width'] = (df['bb_high'] - df['bb_low']) / df['close']
    df['bb_position'] = (df['close'] - df['bb_low']) / (df['bb_high'] - df['bb_low'])
    
    # ATR (Average True Range)
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
    df['atr_ratio'] = df['atr'] / df['close']
    
    # Stochastic Oscillator
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    
    # ADX (Average Directional Index) - Trend strength
    adx_indicator = ta.trend.ADXIndicator(df['high'], df['low'], df['close'])
    df['adx'] = adx_indicator.adx()
    df['adx_pos'] = adx_indicator.adx_pos()
    df['adx_neg'] = adx_indicator.adx_neg()
    
    # Aroon Indicator - Trend identification
    aroon = ta.trend.AroonIndicator(df['high'], df['low'])
    df['aroon_up'] = aroon.aroon_up()
    df['aroon_down'] = aroon.aroon_down()
    df['aroon_diff'] = df['aroon_up'] - df['aroon_down']
    
    # ========== EMA FEATURES ==========
    if 'ema20' in df.columns and 'ema50' in df.columns:
        df['ema_cross'] = (df['ema20'] > df['ema50']).astype(int)
        df['ema_distance'] = (df['ema20'] - df['ema50']) / df['ema50']
    
    # Price position relative to EMAs
    if 'ema20' in df.columns:
        df['price_to_ema20'] = (df['close'] - df['ema20']) / df['ema20']
    if 'ema50' in df.columns:
        df['price_to_ema50'] = (df['close'] - df['ema50']) / df['ema50']
    
    # ========== AUTOCORRELATION FEATURES ==========
    # Lag correlation to detect cycles
    for lag in [5, 10, 20]:
        df[f'autocorr_{lag}'] = df['returns'].rolling(50).apply(
            lambda x: x.autocorr(lag=lag) if len(x) >= lag + 1 else 0, 
            raw=False
        )
    
    return df

def create_target(df: pd.DataFrame, horizon: int = 1, threshold: float = 0.001) -> pd.Series:
    """
    Create target variable for classification
    
    Args:
        df: DataFrame with price data
        horizon: How many periods ahead to predict
        threshold: Minimum price change to consider as signal
        
    Returns:
        Series with target labels (1=UP, 0=DOWN)
    """
    future_returns = df['close'].shift(-horizon) / df['close'] - 1
    
    # Binary classification: 1 if price goes up by threshold, 0 otherwise
    target = (future_returns > threshold).astype(int)
    
    return target

def select_features(df: pd.DataFrame) -> list:
    """
    Select relevant features for model training
    
    Returns:
        List of feature column names
    """
    # Exclude non-feature columns
    exclude_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume', 
                    'bb_high', 'bb_low', 'target']
    
    # Only exclude columns that actually exist in the dataframe
    exclude_cols = [col for col in exclude_cols if col in df.columns]
    
    feature_cols = [col for col in df.columns if col not in exclude_cols]
    
    return feature_cols

def prepare_data_for_training(df: pd.DataFrame, horizon: int = 1):
    """
    Complete data preparation pipeline
    
    Args:
        df: Raw OHLCV DataFrame
        horizon: Prediction horizon
        
    Returns:
        X (features), y (target), feature_names
    """
    # Create features
    df = create_features(df)
    
    # Create target
    df['target'] = create_target(df, horizon=horizon)
    
    # Select features
    feature_cols = select_features(df)
    
    # Remove rows with NaN (from indicators and lags)
    df = df.dropna()
    
    X = df[feature_cols]
    y = df['target']
    
    return X, y, feature_cols
