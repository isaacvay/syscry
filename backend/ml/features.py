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
    
    # Price-based features
    df['returns'] = df['close'].pct_change()
    df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
    
    # Lagged returns
    for lag in [1, 2, 3, 5, 10]:
        df[f'returns_lag_{lag}'] = df['returns'].shift(lag)
    
    # Volume features
    df['volume_change'] = df['volume'].pct_change()
    df['volume_ma_ratio'] = df['volume'] / df['volume'].rolling(20).mean()
    
    # Price momentum
    df['momentum_1h'] = df['close'] / df['close'].shift(1) - 1
    df['momentum_4h'] = df['close'] / df['close'].shift(4) - 1
    df['momentum_24h'] = df['close'] / df['close'].shift(24) - 1
    
    # Volatility (using rolling std)
    df['volatility_10'] = df['returns'].rolling(10).std()
    df['volatility_20'] = df['returns'].rolling(20).std()
    
    # Technical Indicators (already calculated in signals.py, but we add more)
    if 'rsi' not in df.columns:
        df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    
    if 'macd' not in df.columns:
        df['macd'] = ta.trend.macd_diff(df['close'])
    
    # Additional indicators
    df['rsi_6'] = ta.momentum.rsi(df['close'], window=6)
    df['rsi_24'] = ta.momentum.rsi(df['close'], window=24)
    
    # Bollinger Bands
    bollinger = ta.volatility.BollingerBands(df['close'])
    df['bb_high'] = bollinger.bollinger_hband()
    df['bb_low'] = bollinger.bollinger_lband()
    df['bb_width'] = (df['bb_high'] - df['bb_low']) / df['close']
    df['bb_position'] = (df['close'] - df['bb_low']) / (df['bb_high'] - df['bb_low'])
    
    # ATR (Average True Range) - Volatility indicator
    df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'])
    df['atr_ratio'] = df['atr'] / df['close']
    
    # Stochastic Oscillator
    stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
    df['stoch_k'] = stoch.stoch()
    df['stoch_d'] = stoch.stoch_signal()
    
    # EMA crossovers
    if 'ema20' in df.columns and 'ema50' in df.columns:
        df['ema_cross'] = (df['ema20'] > df['ema50']).astype(int)
    
    # Price position relative to EMAs
    if 'ema20' in df.columns:
        df['price_to_ema20'] = (df['close'] - df['ema20']) / df['ema20']
    if 'ema50' in df.columns:
        df['price_to_ema50'] = (df['close'] - df['ema50']) / df['ema50']
    
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
                    'bb_high', 'bb_low']
    
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
