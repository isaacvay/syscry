"""
Market Prediction Module

Provides comprehensive market predictions including:
- Buy/Sell/Hold signals
- Leverage recommendations (1x-10x)
- Position sizing (Kelly Criterion)
- Stop-loss and take-profit levels
- Risk/reward analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
from enum import Enum


class Signal(Enum):
    """Trading signal types"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class MarketPredictor:
    """
    Advanced market prediction with risk management
    """
    
    def __init__(
        self,
        min_confidence: float = 0.55,
        max_leverage: float = 10.0,
        min_leverage: float = 1.0,
        risk_per_trade: float = 0.02  # 2% of capital per trade
    ):
        """
        Initialize market predictor
        
        Args:
            min_confidence: Minimum confidence for non-HOLD signals
            max_leverage: Maximum allowed leverage
            min_leverage: Minimum leverage (1x = no leverage)
            risk_per_trade: Maximum risk per trade as fraction of capital
        """
        self.min_confidence = min_confidence
        self.max_leverage = max_leverage
        self.min_leverage = min_leverage
        self.risk_per_trade = risk_per_trade
    
    def predict_signal(
        self,
        probability: float,
        rsi: float,
        price: float,
        ema20: float,
        volatility: float,
        sentiment: Optional[float] = None
    ) -> Signal:
        """
        Determine trading signal based on multiple factors
        
        Args:
            probability: ML model probability of price increase (0-1)
            rsi: RSI indicator value
            price: Current price
            ema20: 20-period EMA
            volatility: Price volatility measure
            sentiment: Optional sentiment score (-1 to +1)
            
        Returns:
            Signal enum value
        """
        # Adjust probability with sentiment if available
        adjusted_prob = probability
        if sentiment is not None:
            # Sentiment can shift probability by up to 0.1
            sentiment_adjustment = sentiment * 0.1
            adjusted_prob = np.clip(probability + sentiment_adjustment, 0, 1)
        
        # Strong signals require high confidence + technical confirmation
        if adjusted_prob > 0.70 and rsi < 40 and price > ema20:
            return Signal.STRONG_BUY
        elif adjusted_prob < 0.30 and rsi > 60 and price < ema20:
            return Signal.STRONG_SELL
        
        # Regular signals
        elif adjusted_prob > 0.60 and price > ema20:
            return Signal.BUY
        elif adjusted_prob < 0.40 and price < ema20:
            return Signal.SELL
        
        # Default to HOLD
        else:
            return Signal.HOLD
    
    def calculate_leverage(
        self,
        probability: float,
        volatility: float,
        signal: Signal
    ) -> float:
        """
        Calculate recommended leverage based on confidence and volatility
        
        Higher confidence + lower volatility = higher leverage
        
        Args:
            probability: ML model probability
            volatility: Price volatility (std dev of returns)
            signal: Trading signal
            
        Returns:
            Recommended leverage (1x to max_leverage)
        """
        # No leverage for HOLD
        if signal == Signal.HOLD:
            return 1.0
        
        # Calculate confidence (distance from 0.5)
        confidence = abs(probability - 0.5) * 2  # Scale to 0-1
        
        # Volatility penalty (higher volatility = lower leverage)
        # Normalize volatility to 0-1 range (assuming typical volatility < 0.1)
        volatility_factor = 1 - np.clip(volatility * 10, 0, 0.8)
        
        # Base leverage calculation
        base_leverage = 1 + (confidence * volatility_factor * (self.max_leverage - 1))
        
        # Strong signals get a boost
        if signal in [Signal.STRONG_BUY, Signal.STRONG_SELL]:
            base_leverage *= 1.2
        
        # Clamp to allowed range
        leverage = np.clip(base_leverage, self.min_leverage, self.max_leverage)
        
        return round(leverage, 2)
    
    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        leverage: float = 1.0
    ) -> Dict[str, float]:
        """
        Calculate position size using risk management
        
        Args:
            account_balance: Total account balance
            entry_price: Planned entry price
            stop_loss_price: Stop-loss price
            leverage: Leverage to use
            
        Returns:
            Dict with position_size, quantity, risk_amount
        """
        # Calculate risk per unit
        risk_per_unit = abs(entry_price - stop_loss_price)
        
        # Maximum risk amount (e.g., 2% of balance)
        max_risk = account_balance * self.risk_per_trade
        
        # Calculate position size
        # With leverage: can control larger position with same capital
        position_value = (max_risk / risk_per_unit) * entry_price
        position_value = min(position_value, account_balance * leverage)
        
        # Quantity to buy
        quantity = position_value / entry_price
        
        return {
            'position_size': round(position_value, 2),
            'quantity': round(quantity, 8),
            'risk_amount': round(max_risk, 2),
            'capital_required': round(position_value / leverage, 2)
        }
    
    def calculate_kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion
        
        Kelly % = W - [(1 - W) / R]
        where W = win rate, R = avg_win / avg_loss
        
        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade return
            avg_loss: Average losing trade return (positive number)
            
        Returns:
            Optimal fraction of capital to risk (0-1)
        """
        if avg_loss == 0 or win_rate == 0:
            return 0.0
        
        win_loss_ratio = avg_win / avg_loss
        kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        # Use fractional Kelly (0.25 to 0.5) for safety
        # Full Kelly can be too aggressive
        conservative_kelly = kelly * 0.25
        
        return max(0.0, min(conservative_kelly, 0.1))  # Cap at 10%
    
    def calculate_stop_loss_take_profit(
        self,
        entry_price: float,
        signal: Signal,
        atr: float,
        risk_reward_ratio: float = 2.0
    ) -> Dict[str, float]:
        """
        Calculate stop-loss and take-profit levels
        
        Uses ATR (Average True Range) for dynamic levels
        
        Args:
            entry_price: Entry price
            signal: Trading signal
            atr: Average True Range indicator
            risk_reward_ratio: Reward/Risk ratio (default 2:1)
            
        Returns:
            Dict with stop_loss, take_profit, risk_reward_ratio
        """
        # Use ATR for stop-loss distance
        # Strong signals: tighter stops (1.5x ATR)
        # Regular signals: wider stops (2x ATR)
        atr_multiplier = 1.5 if signal in [Signal.STRONG_BUY, Signal.STRONG_SELL] else 2.0
        stop_distance = atr * atr_multiplier
        
        if signal in [Signal.BUY, Signal.STRONG_BUY]:
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + (stop_distance * risk_reward_ratio)
        elif signal in [Signal.SELL, Signal.STRONG_SELL]:
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - (stop_distance * risk_reward_ratio)
        else:  # HOLD
            return {
                'stop_loss': None,
                'take_profit': None,
                'risk_reward_ratio': 0
            }
        
        return {
            'stop_loss': round(stop_loss, 2),
            'take_profit': round(take_profit, 2),
            'risk_reward_ratio': risk_reward_ratio,
            'stop_distance': round(stop_distance, 2)
        }
    
    def generate_prediction(
        self,
        probability: float,
        price: float,
        indicators: Dict[str, float],
        account_balance: float = 10000.0,
        sentiment: Optional[float] = None
    ) -> Dict:
        """
        Generate comprehensive market prediction
        
        Args:
            probability: ML model probability of price increase
            price: Current price
            indicators: Dict with rsi, ema20, atr, volatility
            account_balance: Account balance for position sizing
            sentiment: Optional sentiment score
            
        Returns:
            Complete prediction with signal, leverage, position sizing, etc.
        """
        # Extract indicators
        rsi = indicators.get('rsi', 50)
        ema20 = indicators.get('ema20', price)
        atr = indicators.get('atr', price * 0.02)  # Default 2% ATR
        volatility = indicators.get('volatility', 0.02)
        
        # Generate signal
        signal = self.predict_signal(
            probability, rsi, price, ema20, volatility, sentiment
        )
        
        # Calculate leverage
        leverage = self.calculate_leverage(probability, volatility, signal)
        
        # Calculate stop-loss and take-profit
        sl_tp = self.calculate_stop_loss_take_profit(
            price, signal, atr
        )
        
        # Calculate position sizing if not HOLD
        position_info = {}
        if signal != Signal.HOLD and sl_tp['stop_loss'] is not None:
            position_info = self.calculate_position_size(
                account_balance,
                price,
                sl_tp['stop_loss'],
                leverage
            )
        
        # Compile prediction
        prediction = {
            'signal': signal.value,
            'probability': round(probability, 4),
            'confidence': round(abs(probability - 0.5) * 2, 4),
            'leverage': leverage,
            'stop_loss': sl_tp['stop_loss'],
            'take_profit': sl_tp['take_profit'],
            'risk_reward_ratio': sl_tp['risk_reward_ratio'],
            'sentiment': sentiment,
            **position_info
        }
        
        return prediction


def create_market_predictor(config: Optional[Dict] = None) -> MarketPredictor:
    """
    Factory function to create MarketPredictor with config
    
    Args:
        config: Optional configuration dict
        
    Returns:
        MarketPredictor instance
    """
    if config is None:
        config = {}
    
    return MarketPredictor(
        min_confidence=config.get('min_confidence', 0.55),
        max_leverage=config.get('max_leverage', 10.0),
        min_leverage=config.get('min_leverage', 1.0),
        risk_per_trade=config.get('risk_per_trade', 0.02)
    )
