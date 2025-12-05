import os
import joblib
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional

# Global model cache
_model_cache = {}

def load_model(symbol="BTCUSDT", interval="1h", use_ensemble=True):
    """
    Load trained model from disk (ensemble or single model)
    
    Args:
        symbol: Crypto symbol
        interval: Timeframe
        use_ensemble: Try to load ensemble first
        
    Returns:
        Model data dict or None if not found
    """
    cache_key = f"{symbol}_{interval}_{'ensemble' if use_ensemble else 'single'}"
    
    # Check cache first
    if cache_key in _model_cache:
        return _model_cache[cache_key]
    
    # Model directory is at backend/ml/models (parent of model directory)
    model_dir = Path(__file__).parent.parent / 'ml' / 'models'
    
    # Try to load ensemble first if requested
    if use_ensemble:
        ensemble_path = model_dir / f'ensemble_{symbol}_{interval}_latest.pkl'
        if ensemble_path.exists():
            try:
                model_data = joblib.load(ensemble_path)
                _model_cache[cache_key] = model_data
                print(f"✅ Ensemble loaded: {symbol} {interval} "
                      f"(Best: {model_data['best_model_name']}, "
                      f"Accuracy: {model_data.get('best_accuracy', 0):.3f})")
                return model_data
            except Exception as e:
                print(f"⚠️ Error loading ensemble: {e}")
    
    # Fallback to single model
    model_path = model_dir / f'xgboost_{symbol}_{interval}_latest.pkl'
    
    if model_path.exists():
        try:
            model_data = joblib.load(model_path)
            _model_cache[cache_key] = model_data
            print(f"✅ Model loaded: {symbol} {interval} "
                  f"(Accuracy: {model_data.get('test_accuracy', 0):.3f})")
            return model_data
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return None
    else:
        print(f"⚠️ Model not found: {model_path}")
        return None

def predict_direction(df: pd.DataFrame, symbol="BTCUSDT", interval="1h", 
                     use_ensemble=True) -> float:
    """
    Predicts the probability of price going UP in the next timeframe.
    Returns a float between 0.0 and 1.0.
    
    Uses trained model (ensemble or single) if available, otherwise falls back to heuristic.
    
    Args:
        df: DataFrame with OHLCV and indicators
        symbol: Crypto symbol (for model selection)
        interval: Timeframe (for model selection)
        use_ensemble: Try to use ensemble model
        
    Returns:
        Probability of price increase (0.0 to 1.0)
    """
    # Try to load model
    model_data = load_model(symbol, interval, use_ensemble)
    
    if model_data is not None:
        # Use ML model
        try:
            from ml.features import create_features
            
            # Check if this is an ensemble
            is_ensemble = 'voting_ensemble' in model_data
            
            if is_ensemble:
                # Use ensemble prediction
                from ml.ensemble import predict_with_ensemble
                
                # Prepare features
                df_features = create_features(df.copy())
                feature_names = model_data['feature_names']
                
                # Filter out target if present
                feature_names = [f for f in feature_names if f != 'target']
                
                # Handle missing features BEFORE selection
                for col in feature_names:
                    if col not in df_features.columns:
                        df_features[col] = 0
                        
                X = df_features[feature_names].iloc[[-1]]
                
                # Predict with ensemble
                result = predict_with_ensemble(model_data, X)
                prob = result['probability']
                
            else:
                # Single model prediction
                df_features = create_features(df.copy())
                feature_names = model_data['feature_names']
                
                # Filter out target if present
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
            
            return float(prob)
            
        except Exception as e:
            from logger import logger
            logger.warning(f"⚠️ ML prediction error for {symbol} {interval}: {e}")
            logger.debug(f"Traceback:", exc_info=True)
            logger.warning(f"Falling back to heuristic prediction for {symbol}")
            # Fall through to heuristic
    
    # If no model found, log warning
    if model_data is None:
        from logger import logger
        logger.warning(f"No ML model found for {symbol} {interval}, using heuristic prediction")
    
    # ========== ENHANCED FALLBACK HEURISTIC ==========
    # Use multiple technical indicators for better fallback predictions
    
    signals = []
    weights = []
    
    # Signal 1: EMA Trend (weight: 0.3)
    if 'ema20' in df.columns:
        last_close = df['close'].iloc[-1]
        last_ema = df['ema20'].iloc[-1]
        
        if last_close > last_ema:
            signals.append(0.6)  # Bullish
            weights.append(0.3)
        else:
            signals.append(0.4)  # Bearish
            weights.append(0.3)
    
    # Signal 2: RSI (weight: 0.25)
    if 'rsi' in df.columns:
        last_rsi = df['rsi'].iloc[-1]
        
        if last_rsi < 30:
            signals.append(0.65)  # Oversold - likely to go up
            weights.append(0.25)
        elif last_rsi > 70:
            signals.append(0.35)  # Overbought - likely to go down
            weights.append(0.25)
        else:
            signals.append(0.5)  # Neutral
            weights.append(0.25)
    
    # Signal 3: MACD (weight: 0.25)
    if 'macd' in df.columns:
        last_macd = df['macd'].iloc[-1]
        
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
    
    indicators = {
        'rsi': last.get('rsi', 50),
        'ema20': last.get('ema20', price),
        'atr': last.get('atr', price * 0.02),
        'volatility': df['close'].pct_change().std() if len(df) > 1 else 0.02
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
