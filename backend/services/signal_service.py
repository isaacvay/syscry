import ta
import pandas as pd
import numpy as np
from model.predict import predict_with_market_analysis
from cache import cache
from config import settings
from logger import logger
from indicators.signals import get_binance_data
from dependency_manager import dependency_manager
from exceptions import PredictionError


class UnifiedSignalGenerator:
    """
    Unified signal generator with confluence scoring and dependency management
    """
    
    def __init__(self):
        self.dependency_status = dependency_manager.validate_dependencies()
    
    def generate_signal(self, symbol: str, timeframe: str) -> dict:
        """
        Generate signal with unified logic, dependency management and enhanced reliability
        
        Args:
            symbol: Trading symbol
            timeframe: Timeframe for analysis
            
        Returns:
            Enhanced signal data dictionary with reliability metrics
        """
        clean_symbol = symbol.replace("/", "").upper()
        
        try:
            # 1. Fetch Data with enhanced error handling
            df = get_binance_data(clean_symbol, timeframe)
            
            if df.empty:
                return {"error": "Could not fetch data"}

            # 2. Calculate Technical Indicators
            df = self._calculate_indicators(df)
            
            # 3. Validate Data Quality
            data_quality_score = self._validate_data_quality(df)
            if data_quality_score < 0.5:
                logger.warning(f"Low data quality for {clean_symbol}: {data_quality_score}")
            
            # 4. Handle Sentiment Analysis with Dependency Management
            sentiment_score = self._get_sentiment_score(clean_symbol)
            
            # 5. Generate ML Prediction with Error Handling
            ml_signal = None
            ml_confidence = None
            
            try:
                prediction = predict_with_market_analysis(
                    df=df, 
                    symbol=clean_symbol, 
                    interval=timeframe,
                    sentiment_score=sentiment_score
                )
                
                ml_signal = prediction['signal']
                ml_confidence = prediction['probability']
                
            except Exception as e:
                logger.error(f"ML prediction failed for {clean_symbol}: {e}")
                ml_signal = None
                ml_confidence = None
            
            # 6. Generate Fallback Signal
            fallback_signal, fallback_confidence = self._generate_fallback_signal(df)
            
            # 7. Combine Signals for Enhanced Reliability
            final_signal, final_confidence = self._combine_signals(
                ml_signal, ml_confidence, 
                fallback_signal, fallback_confidence,
                df, sentiment_score
            )
            
            # 8. Format Response with Enhanced Metrics
            return self._format_response(clean_symbol, timeframe, final_signal, final_confidence, df, sentiment_score)
            
        except Exception as e:
            logger.error(f"Signal generation failed for {symbol}: {e}")
            return {"error": f"Signal generation failed: {str(e)}"}
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators with error handling"""
        try:
            # Basic indicators for display/fallback
            df["rsi"] = ta.momentum.rsi(df["close"], window=14)
            df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
            df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
            df["macd"] = ta.trend.macd_diff(df["close"])
            
            # Additional indicators for improved analysis
            df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)
            stoch = ta.momentum.StochasticOscillator(df["high"], df["low"], df["close"])
            df["stoch_k"] = stoch.stoch()
            df["stoch_d"] = stoch.stoch_signal()
            df["adx"] = ta.trend.adx(df["high"], df["low"], df["close"], window=14)
            
            # Fill any remaining NaN values - use newer pandas methods
            df = df.ffill().bfill()
            
            return df
            
        except Exception as e:
            logger.error(f"Indicator calculation failed: {e}")
            # Return DataFrame with minimal indicators
            df["rsi"] = 50.0  # Neutral RSI
            df["ema20"] = df["close"]
            df["ema50"] = df["close"]
            df["macd"] = 0.0
            df["atr"] = df["close"] * 0.02
            df["stoch_k"] = 50.0
            df["stoch_d"] = 50.0
            df["adx"] = 25.0  # Neutral trend strength
            return df
    
    def _get_sentiment_score(self, symbol: str) -> float:
        """Get sentiment score with dependency management"""
        if not settings.sentiment_enabled:
            return 0.0
        
        if not dependency_manager.is_feature_available("sentiment_analysis"):
            logger.debug(f"Sentiment analysis not available for {symbol}")
            return 0.0
        
        try:
            # Try to get sentiment features
            if dependency_manager.status.available.get("textblob", False):
                from ml.sentiment_features import add_sentiment_features, get_crypto_name
                crypto_name = get_crypto_name(symbol)
                
                # Create dummy DataFrame for sentiment
                dummy_df = pd.DataFrame({"close": [1]})
                sentiment_df = add_sentiment_features(dummy_df, symbol, crypto_name=crypto_name)
                
                if 'sentiment_score' in sentiment_df.columns:
                    return float(sentiment_df['sentiment_score'].iloc[-1])
            
        except Exception as e:
            logger.warning(f"Sentiment analysis failed for {symbol}: {e}")
        
        return 0.0  # Default neutral sentiment
    
    def _generate_fallback_signal(self, df: pd.DataFrame) -> tuple:
        """Generate fallback signal using heuristic methods - BUY/SELL only"""
        try:
            last = df.iloc[-1]
            
            # Enhanced confluence scoring for more decisive signals
            buy_score = 0
            sell_score = 0
            
            # RSI contrarian signals (using updated thresholds) - weighted more heavily
            if last["rsi"] < settings.rsi_oversold:  # RSI < 30
                buy_score += 3  # Strong oversold signal
            elif last["rsi"] > settings.rsi_overbought:  # RSI > 70
                sell_score += 3  # Strong overbought signal
            elif last["rsi"] < 40:  # Moderately oversold
                buy_score += 1
            elif last["rsi"] > 60:  # Moderately overbought
                sell_score += 1
            
            # EMA trend - stronger weight for trend following
            if last["close"] > last["ema20"] and last["ema20"] > last["ema50"]:
                buy_score += 2  # Strong uptrend
            elif last["close"] < last["ema20"] and last["ema20"] < last["ema50"]:
                sell_score += 2  # Strong downtrend
            elif last["close"] > last["ema20"]:
                buy_score += 1  # Weak uptrend
            else:
                sell_score += 1  # Weak downtrend
            
            # MACD momentum
            if last["macd"] > 0:
                buy_score += 1
            else:
                sell_score += 1
            
            # ADX trend strength - only trade when trend is strong
            if last["adx"] > 25:  # Strong trend
                if buy_score > sell_score:
                    buy_score += 1
                else:
                    sell_score += 1
            
            # Determine signal - NO HOLD, always choose stronger side
            if buy_score > sell_score:
                signal = "BUY"
                # Higher confidence for stronger signals
                confidence = min(0.9, 0.5 + (buy_score - sell_score) * 0.1)
            else:
                signal = "SELL"
                # Higher confidence for stronger signals
                confidence = min(0.9, 0.5 + (sell_score - buy_score) * 0.1)
            
            return signal, confidence
            
        except Exception as e:
            logger.error(f"Fallback signal generation failed: {e}")
            # Even in error, return a signal based on simple RSI
            try:
                last = df.iloc[-1]
                if last["rsi"] < 50:
                    return "BUY", 0.5
                else:
                    return "SELL", 0.5
            except:
                return "BUY", 0.5  # Default fallback
    
    def _format_response(self, symbol: str, timeframe: str, signal: str, 
                        confidence: float, df: pd.DataFrame, sentiment_score: float) -> dict:
        """Format the final response with enhanced reliability metrics"""
        try:
            last = df.iloc[-1]
            
            # Calculate signal strength and reliability metrics
            signal_strength = self._calculate_signal_strength(df, signal, confidence)
            reliability_score = self._calculate_reliability_score(df, signal, confidence, sentiment_score)
            
            # Format chart data (last 100 points for performance)
            chart_data = []
            df_chart = df.tail(100)  # Only last 100 candles for frontend
            for index, row in df_chart.iterrows():
                chart_data.append({
                    "time": int(row["timestamp"] / 1000),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0))
                })
            
            # Enhanced signal classification
            signal_type = self._classify_signal_type(signal, confidence, signal_strength)
            
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "signal": signal,
                "signal_type": signal_type,
                "confidence": round(float(confidence), 3),
                "signal_strength": round(signal_strength, 3),
                "reliability_score": round(reliability_score, 3),
                "price": float(last["close"]),
                "timestamp": int(last["timestamp"]),
                "indicators": {
                    "rsi": round(float(last["rsi"]), 2),
                    "ema20": round(float(last["ema20"]), 2),
                    "ema50": round(float(last["ema50"]), 2),
                    "macd": round(float(last["macd"]), 4),
                    "atr": round(float(last["atr"]), 4),
                    "stoch_k": round(float(last["stoch_k"]), 2),
                    "stoch_d": round(float(last["stoch_d"]), 2),
                    "adx": round(float(last["adx"]), 2)
                },
                "market_conditions": {
                    "trend": self._determine_trend(df),
                    "volatility": self._calculate_volatility(df),
                    "volume_trend": self._analyze_volume_trend(df)
                },
                "risk_metrics": {
                    "stop_loss_suggestion": self._calculate_stop_loss(last, signal),
                    "take_profit_suggestion": self._calculate_take_profit(last, signal),
                    "risk_reward_ratio": self._calculate_risk_reward(last, signal)
                },
                "chart_data": chart_data,
                "sentiment": round(sentiment_score, 3) if sentiment_score else 0.0,
                "metadata": {
                    "data_points": len(df),
                    "analysis_time": pd.Timestamp.now().isoformat(),
                    "ml_model_used": dependency_manager.is_feature_available("ml_prediction"),
                    "sentiment_analysis_used": dependency_manager.is_feature_available("sentiment_analysis")
                }
            }
            
        except Exception as e:
            logger.error(f"Response formatting failed: {e}")
            return {"error": f"Response formatting failed: {str(e)}"}

    def _calculate_signal_strength(self, df: pd.DataFrame, signal: str, confidence: float) -> float:
        """Calculate signal strength based on multiple factors"""
        try:
            last = df.iloc[-1]
            strength = 0.0
            
            # Base strength from confidence
            strength += confidence * 0.4
            
            # RSI extremes add strength
            if last["rsi"] < 20 or last["rsi"] > 80:
                strength += 0.3
            elif last["rsi"] < 30 or last["rsi"] > 70:
                strength += 0.2
            
            # Trend alignment adds strength
            if signal == "BUY" and last["close"] > last["ema20"] > last["ema50"]:
                strength += 0.2
            elif signal == "SELL" and last["close"] < last["ema20"] < last["ema50"]:
                strength += 0.2
            
            # MACD confirmation
            if (signal == "BUY" and last["macd"] > 0) or (signal == "SELL" and last["macd"] < 0):
                strength += 0.1
            
            return min(1.0, strength)
            
        except Exception:
            return confidence * 0.5
    
    def _calculate_reliability_score(self, df: pd.DataFrame, signal: str, confidence: float, sentiment: float) -> float:
        """Calculate reliability score based on data quality and consistency"""
        try:
            reliability = 0.0
            
            # Data quality (more data = more reliable)
            data_quality = min(1.0, len(df) / 500)  # 500+ candles = full score
            reliability += data_quality * 0.3
            
            # Indicator consistency
            last = df.iloc[-1]
            consistency_score = 0.0
            
            # Check if multiple indicators agree
            buy_indicators = 0
            sell_indicators = 0
            
            if last["rsi"] < 50:
                buy_indicators += 1
            else:
                sell_indicators += 1
                
            if last["close"] > last["ema20"]:
                buy_indicators += 1
            else:
                sell_indicators += 1
                
            if last["macd"] > 0:
                buy_indicators += 1
            else:
                sell_indicators += 1
            
            # Higher consistency = higher reliability
            consistency_score = abs(buy_indicators - sell_indicators) / 3.0
            reliability += consistency_score * 0.4
            
            # Confidence contributes to reliability
            reliability += confidence * 0.3
            
            return min(1.0, reliability)
            
        except Exception:
            return confidence * 0.6
    
    def _validate_data_quality(self, df: pd.DataFrame) -> float:
        """Validate data quality and return quality score (0-1)"""
        try:
            quality_score = 1.0
            
            # Check data completeness
            if len(df) < 100:
                quality_score -= 0.3
            
            # Check for missing values
            missing_ratio = df.isnull().sum().sum() / (len(df) * len(df.columns))
            quality_score -= missing_ratio * 0.4
            
            # Check for price anomalies
            price_changes = df['close'].pct_change().abs()
            extreme_changes = (price_changes > 0.1).sum()  # >10% changes
            if extreme_changes > len(df) * 0.05:  # More than 5% extreme changes
                quality_score -= 0.2
            
            # Check volume consistency (if available)
            if 'volume' in df.columns:
                zero_volume = (df['volume'] == 0).sum()
                if zero_volume > len(df) * 0.1:  # More than 10% zero volume
                    quality_score -= 0.1
            
            return max(0.0, quality_score)
            
        except Exception:
            return 0.5  # Default moderate quality
    
    def _combine_signals(self, ml_signal: str, ml_confidence: float, 
                        fallback_signal: str, fallback_confidence: float,
                        df: pd.DataFrame, sentiment_score: float) -> tuple:
        """Combine ML and fallback signals for enhanced reliability"""
        try:
            # If ML signal is available and confident, use it
            if ml_signal and ml_confidence and ml_confidence > 0.6:
                # Check if fallback agrees
                if ml_signal == fallback_signal:
                    # Both agree - high confidence
                    combined_confidence = min(0.95, (ml_confidence + fallback_confidence) / 2 + 0.1)
                    return ml_signal, combined_confidence
                else:
                    # Disagreement - moderate confidence, prefer ML
                    combined_confidence = ml_confidence * 0.8
                    return ml_signal, combined_confidence
            
            # If ML signal is weak or unavailable, use enhanced fallback
            elif fallback_signal:
                # Add sentiment boost if available
                sentiment_boost = 0.0
                if sentiment_score:
                    if (fallback_signal == "BUY" and sentiment_score > 0.1) or \
                       (fallback_signal == "SELL" and sentiment_score < -0.1):
                        sentiment_boost = 0.1
                
                enhanced_confidence = min(0.9, fallback_confidence + sentiment_boost)
                return fallback_signal, enhanced_confidence
            
            # Last resort - use simple trend following
            else:
                last = df.iloc[-1]
                if last["close"] > last["ema20"]:
                    return "BUY", 0.4
                else:
                    return "SELL", 0.4
                    
        except Exception as e:
            logger.error(f"Signal combination failed: {e}")
            return fallback_signal or "BUY", fallback_confidence or 0.5
    
    def _classify_signal_type(self, signal: str, confidence: float, strength: float) -> str:
        """Classify signal type based on confidence and strength"""
        if confidence >= 0.8 and strength >= 0.8:
            return "TRÈS FORT"
        elif confidence >= 0.7 and strength >= 0.7:
            return "FORT"
        elif confidence >= 0.6 and strength >= 0.6:
            return "MODÉRÉ"
        elif confidence >= 0.5:
            return "FAIBLE"
        else:
            return "TRÈS FAIBLE"
    
    def _determine_trend(self, df: pd.DataFrame) -> str:
        """Determine market trend"""
        try:
            last = df.iloc[-1]
            if last["ema20"] > last["ema50"] and last["close"] > last["ema20"]:
                return "HAUSSIER"
            elif last["ema20"] < last["ema50"] and last["close"] < last["ema20"]:
                return "BAISSIER"
            else:
                return "LATÉRAL"
        except Exception:
            return "INDÉTERMINÉ"
    
    def _calculate_volatility(self, df: pd.DataFrame) -> str:
        """Calculate market volatility"""
        try:
            # Use ATR for volatility
            last_atr = df["atr"].iloc[-1]
            last_price = df["close"].iloc[-1]
            
            # Prevent division by zero
            if last_price == 0 or pd.isna(last_price) or pd.isna(last_atr):
                return "INDÉTERMINÉE"
                
            volatility_pct = (last_atr / last_price) * 100
            
            if volatility_pct > 3:
                return "TRÈS ÉLEVÉE"
            elif volatility_pct > 2:
                return "ÉLEVÉE"
            elif volatility_pct > 1:
                return "MODÉRÉE"
            else:
                return "FAIBLE"
        except Exception:
            return "INDÉTERMINÉE"
    
    def _analyze_volume_trend(self, df: pd.DataFrame) -> str:
        """Analyze volume trend"""
        try:
            if "volume" in df.columns:
                recent_volume = df["volume"].tail(10).mean()
                older_volume = df["volume"].tail(50).head(40).mean()
                
                # Prevent division by zero
                if older_volume == 0 or pd.isna(older_volume) or pd.isna(recent_volume):
                    return "INDÉTERMINÉ"
                
                if recent_volume > older_volume * 1.2:
                    return "EN HAUSSE"
                elif recent_volume < older_volume * 0.8:
                    return "EN BAISSE"
                else:
                    return "STABLE"
            else:
                return "NON DISPONIBLE"
        except Exception:
            return "INDÉTERMINÉ"
    
    def _calculate_stop_loss(self, last_candle: pd.Series, signal: str) -> float:
        """Calculate suggested stop loss"""
        try:
            atr = last_candle["atr"]
            price = last_candle["close"]
            
            if signal.startswith("BUY"):
                return round(price - (atr * 2), 4)
            else:  # SELL
                return round(price + (atr * 2), 4)
        except Exception:
            return None
    
    def _calculate_take_profit(self, last_candle: pd.Series, signal: str) -> float:
        """Calculate suggested take profit"""
        try:
            atr = last_candle["atr"]
            price = last_candle["close"]
            
            if signal.startswith("BUY"):
                return round(price + (atr * 3), 4)
            else:  # SELL
                return round(price - (atr * 3), 4)
        except Exception:
            return None
    
    def _calculate_risk_reward(self, last_candle: pd.Series, signal: str) -> float:
        """Calculate risk/reward ratio"""
        try:
            stop_loss = self._calculate_stop_loss(last_candle, signal)
            take_profit = self._calculate_take_profit(last_candle, signal)
            price = last_candle["close"]
            
            if stop_loss and take_profit and price:
                risk = abs(price - stop_loss)
                reward = abs(take_profit - price)
                
                # Prevent division by zero
                if risk == 0 or pd.isna(risk):
                    return 0
                    
                return round(reward / risk, 2)
            return 0
        except Exception:
            return 0


# Global unified signal generator
unified_signal_generator = UnifiedSignalGenerator()


def generate_signal_service(symbol, timeframe):
    """
    Generate signal for a given symbol and timeframe using unified generator
    """
    return unified_signal_generator.generate_signal(symbol, timeframe)