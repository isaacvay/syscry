import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional

from logger_enhanced import logger, log_exception, performance_log
from exceptions import ModelNotFoundError, PredictionError
from dependency_manager import dependency_manager

# Global model cache
_model_cache = {}

def load_model(symbol="BTCUSDT", interval="1h", use_ensemble=True):
    """
    Load trained model from disk (ensemble or single model) with enhanced error handling
    
    Args:
        symbol: Crypto symbol
        interval: Timeframe
        use_ensemble: Try to load ensemble first
        
    Returns:
        Model data dict or None if not found
        
    Raises:
        ModelNotFoundError: If model file is not found
    """
    cache_key = f"{symbol}_{interval}_{'ensemble' if use_ensemble else 'single'}"
    
    # Check cache first
    if cache_key in _model_cache:
        logger.debug(f"Model cache hit: {cache_key}")
        return _model_cache[cache_key]
    
    # Model directory is at backend/ml/models (parent of model directory)
    model_dir = Path(__file__).parent.parent / 'ml' / 'models'
    
    # Try to load ensemble first if requested
    if use_ensemble:
        ensemble_path = model_dir / f'ensemble_{symbol}_{interval}_latest.pkl'
        if ensemble_path.exists():
            try:
                with performance_log("model_loading", model_type="ensemble", symbol=symbol):
                    model_data = joblib.load(ensemble_path)
                    _model_cache[cache_key] = model_data
                    logger.info(f"✅ Ensemble loaded: {symbol} {interval} "
                              f"(Best: {model_data.get('best_model_name', 'unknown')}, "
                              f"Accuracy: {model_data.get('best_accuracy', 0):.3f})")
                    return model_data
            except Exception as e:
                log_exception(e, {"model_path": str(ensemble_path)}, "Ensemble model loading")
    
    # Fallback to single model
    model_path = model_dir / f'xgboost_{symbol}_{interval}_latest.pkl'
    
    if model_path.exists():
        try:
            with performance_log("model_loading", model_type="single", symbol=symbol):
                model_data = joblib.load(model_path)
                _model_cache[cache_key] = model_data
                logger.info(f"✅ Model loaded: {symbol} {interval} "
                          f"(Accuracy: {model_data.get('test_accuracy', 0):.3f})")
                return model_data
        except Exception as e:
            log_exception(e, {"model_path": str(model_path)}, "Single model loading")
            return None
    else:
        logger.warning(f"⚠️ Model not found: {model_path}")
        return None

def predict_direction(df: pd.DataFrame, symbol="BTCUSDT", interval="1h", 
                     use_ensemble=True) -> float:
    """
    Predicts the probability of price going UP in the next timeframe with enhanced error handling.
    Returns a float between 0.0 and 1.0.
    
    Uses trained model (ensemble or single) if available, otherwise falls back to heuristic.
    
    Args:
        df: DataFrame with OHLCV and indicators
        symbol: Crypto symbol (for model selection)
        interval: Timeframe (for model selection)
        use_ensemble: Try to use ensemble model
        
    Returns:
        Probability of price increase (0.0 to 1.0)
        
    Raises:
        PredictionError: If prediction fails critically
    """
    try:
        # Try to load model
        model_data = load_model(symbol, interval, use_ensemble)
        
        if model_data is not None:
            # Use ML model
            try:
                if not dependency_manager.is_feature_available("ml_prediction"):
                    logger.warning("ML prediction dependencies not available, using heuristic")
                    return _enhanced_fallback_heuristic(df, symbol)
                
                from ml.features import create_features
                
                # Check if this is an ensemble
                is_ensemble = 'voting_ensemble' in model_data
                
                if is_ensemble:
                    # Use ensemble prediction
                    from ml.ensemble import predict_with_ensemble
                    
                    # Prepare features
                    df_features = create_features(df.copy())
                    
                    # Drop 'target' column if it exists in the DataFrame
                    if 'target' in df_features.columns:
                        df_features = df_features.drop(columns=['target'])
                    
                    feature_names = model_data['feature_names']
                    
                    # Filter out target if present in saved feature names
                    feature_names = [f for f in feature_names if f != 'target']
                    
                    # Handle missing features BEFORE selection
                    for col in feature_names:
                        if col not in df_features.columns:
                            df_features[col] = 0
                    
                    # Select only the features the model expects        
                    X = df_features[feature_names].iloc[[-1]]
                    
                    # Predict with ensemble
                    result = predict_with_ensemble(model_data, X)
                    prob = result['probability']
                    
                else:
                    # Single model prediction
                    df_features = create_features(df.copy())
                    
                    # Drop 'target' column if it exists in the DataFrame
                    if 'target' in df_features.columns:
                        df_features = df_features.drop(columns=['target'])
                    
                    feature_names = model_data['feature_names']
                    
                    # Filter out target if present in saved feature names
                    feature_names = [f for f in feature_names if f != 'target']
                    
                    # Handle missing features BEFORE selection
                    for col in feature_names:
                        if col not in df_features.columns:
                            df_features[col] = 0
                    
                    # Get last row features
                    X = df_features[feature_names].iloc[[-1]]
                    
                    # Predict probability
                    model = model_data['model']
                    prob = model.predict_proba(X)[0][1]  # Probability of class 1 (UP)
                
                # Validate probability
                if not (0 <= prob <= 1):
                    logger.warning(f"Invalid probability {prob} for {symbol}, clamping to valid range")
                    prob = max(0.0, min(1.0, prob))
                
                return float(prob)
                
            except Exception as e:
                log_exception(e, {"symbol": symbol, "interval": interval}, "ML prediction")
                logger.warning(f"Falling back to heuristic prediction for {symbol}")
                return _enhanced_fallback_heuristic(df, symbol)
        
        # If no model found, log warning and use heuristic
        if model_data is None:
            logger.warning(f"No ML model found for {symbol} {interval}, using heuristic prediction")
        
        return _enhanced_fallback_heuristic(df, symbol)
        
    except Exception as e:
        log_exception(e, {"symbol": symbol, "interval": interval}, "Prediction direction")
        # Last resort fallback
        return 0.5


def _enhanced_fallback_heuristic(df: pd.DataFrame, symbol: str) -> float:
    """
    Enhanced fallback heuristic with better technical analysis
    
    Args:
        df: DataFrame with OHLCV and indicators
        symbol: Symbol for logging context
        
    Returns:
        Probability of price increase (0.0 to 1.0)
    """
    try:
        signals = []
        weights = []
        
        # Signal 1: EMA Trend (weight: 0.3)
        if 'ema20' in df.columns and len(df) > 0:
            last_close = df['close'].iloc[-1]
            last_ema = df['ema20'].iloc[-1]
            
            if pd.notna(last_close) and pd.notna(last_ema):
                if last_close > last_ema:
                    signals.append(0.6)  # Bullish
                    weights.append(0.3)
                else:
                    signals.append(0.4)  # Bearish
                    weights.append(0.3)
        
        # Signal 2: RSI (weight: 0.25) - Using updated thresholds
        if 'rsi' in df.columns and len(df) > 0:
            last_rsi = df['rsi'].iloc[-1]
            
            if pd.notna(last_rsi):
                if last_rsi < 30:  # Updated threshold
                    signals.append(0.65)  # Oversold - likely to go up
                    weights.append(0.25)
                elif last_rsi > 70:  # Updated threshold
                    signals.append(0.35)  # Overbought - likely to go down
                    weights.append(0.25)
                else:
                    signals.append(0.5)  # Neutral
                    weights.append(0.25)
        
        # Signal 3: MACD (weight: 0.25)
        if 'macd' in df.columns and len(df) > 0:
            last_macd = df['macd'].iloc[-1]
            
            if pd.notna(last_macd):
                if last_macd > 0:
                    signals.append(0.6)  # Bullish
                    weights.append(0.25)
                else:
                    signals.append(0.4)  # Bearish
                    weights.append(0.25)
        
        # Signal 4: Volume Trend (weight: 0.2)
        if 'volume' in df.columns and len(df) > 20:
            recent_volume = df['volume'].iloc[-5:].mean()
            avg_volume = df['volume'].iloc[-20:].mean()
            
            if pd.notna(recent_volume) and pd.notna(avg_volume) and avg_volume > 0:
                if recent_volume > avg_volume * 1.2:
                    # High volume - strengthen trend
                    if len(signals) > 0:
                        last_signal = signals[-1]
                        if last_signal > 0.5:
                            signals.append(0.6)
                        else:
                            signals.append(0.4)
                    else:
                        signals.append(0.5)
                    weights.append(0.2)
                else:
                    signals.append(0.5)  # Neutral
                    weights.append(0.2)
        
        # Calculate weighted average
        if signals and weights:
            prob = np.average(signals, weights=weights)
        else:
            prob = 0.5  # Default neutral
        
        # Add small random noise for variation
        import random
        noise = random.uniform(-0.03, 0.03)
        prob = prob + noise
        
        # Clamp between 0 and 1
        return max(0.0, min(1.0, prob))
        
    except Exception as e:
        log_exception(e, {"symbol": symbol}, "Fallback heuristic")
        return 0.5  # Ultimate fallback


def predict_with_market_analysis(
    df: pd.DataFrame,
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    account_balance: float = 10000.0,
    sentiment_score: Optional[float] = None
) -> Dict:
    """
    Generate comprehensive market prediction with risk analysis
    
    Args:
        df: DataFrame with OHLCV and indicators
        symbol: Crypto symbol
        interval: Timeframe
        account_balance: Account balance for position sizing
        sentiment_score: Optional sentiment score
        
    Returns:
        Dict with comprehensive prediction
    """
    from ml.market_predictor import create_market_predictor
    from config import settings
    
    # Get probability prediction
    probability = predict_direction(df, symbol, interval, use_ensemble=settings.use_ensemble)
    
    # Get current price and indicators
    last = df.iloc[-1]
    price = last['close']
    
    # Calculate volume ratio (current / average)
    volume_ratio = None
    if 'volume' in df.columns and len(df) > 20:
        avg_volume = df['volume'].iloc[-20:].mean()
        if avg_volume > 0:
            volume_ratio = float(last['volume'] / avg_volume)
    
    indicators = {
        'rsi': last.get('rsi', 50),
        'ema20': last.get('ema20', price),
        'atr': last.get('atr', price * 0.02),
        'volatility': df['close'].pct_change().std() if len(df) > 1 else 0.02,
        # New indicators for improved strategy
        'adx': last.get('adx'),
        'macd': last.get('macd'),
        'stoch_k': last.get('stoch_k'),
        'volume_ratio': volume_ratio
    }
    
    # Create market predictor
    predictor = create_market_predictor({
        'min_confidence': settings.confidence_threshold,
        'max_leverage': settings.max_leverage,
        'min_leverage': settings.min_leverage,
        'risk_per_trade': settings.risk_per_trade
    })
    
    # Generate comprehensive prediction
    prediction = predictor.generate_prediction(
        probability=probability,
        price=price,
        indicators=indicators,
        account_balance=account_balance,
        sentiment=sentiment_score
    )
    
    return prediction
