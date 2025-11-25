"""
Unit tests for market predictor module
"""

import pytest
import pandas as pd
import numpy as np
from ml.market_predictor import MarketPredictor, Signal, create_market_predictor


def test_market_predictor_initialization():
    """Test MarketPredictor initialization"""
    predictor = MarketPredictor()
    assert predictor.min_confidence == 0.55
    assert predictor.max_leverage == 10.0
    assert predictor.min_leverage == 1.0


def test_predict_signal_strong_buy():
    """Test strong buy signal generation"""
    predictor = MarketPredictor()
    
    signal = predictor.predict_signal(
        probability=0.75,
        rsi=35,
        price=100,
        ema20=95,
        volatility=0.02
    )
    
    assert signal == Signal.STRONG_BUY


def test_predict_signal_strong_sell():
    """Test strong sell signal generation"""
    predictor = MarketPredictor()
    
    signal = predictor.predict_signal(
        probability=0.25,
        rsi=65,
        price=100,
        ema20=105,
        volatility=0.02
    )
    
    assert signal == Signal.STRONG_SELL


def test_predict_signal_hold():
    """Test hold signal generation"""
    predictor = MarketPredictor()
    
    signal = predictor.predict_signal(
        probability=0.5,
        rsi=50,
        price=100,
        ema20=100,
        volatility=0.02
    )
    
    assert signal == Signal.HOLD


def test_calculate_leverage():
    """Test leverage calculation"""
    predictor = MarketPredictor()
    
    # High confidence, low volatility should give higher leverage
    leverage = predictor.calculate_leverage(
        probability=0.8,
        volatility=0.01,
        signal=Signal.STRONG_BUY
    )
    
    assert leverage > 1.0
    assert leverage <= predictor.max_leverage


def test_calculate_position_size():
    """Test position sizing calculation"""
    predictor = MarketPredictor()
    
    result = predictor.calculate_position_size(
        account_balance=10000,
        entry_price=100,
        stop_loss_price=95,
        leverage=2.0
    )
    
    assert 'position_size' in result
    assert 'quantity' in result
    assert 'risk_amount' in result
    assert result['risk_amount'] <= 10000 * predictor.risk_per_trade


def test_calculate_kelly_criterion():
    """Test Kelly Criterion calculation"""
    predictor = MarketPredictor()
    
    kelly = predictor.calculate_kelly_criterion(
        win_rate=0.6,
        avg_win=1.5,
        avg_loss=1.0
    )
    
    assert kelly >= 0
    assert kelly <= 0.1  # Capped at 10%


def test_calculate_stop_loss_take_profit():
    """Test stop-loss and take-profit calculation"""
    predictor = MarketPredictor()
    
    result = predictor.calculate_stop_loss_take_profit(
        entry_price=100,
        signal=Signal.BUY,
        atr=2.0,
        risk_reward_ratio=2.0
    )
    
    assert 'stop_loss' in result
    assert 'take_profit' in result
    assert result['stop_loss'] < 100  # Stop-loss below entry for buy
    assert result['take_profit'] > 100  # Take-profit above entry for buy


def test_generate_prediction():
    """Test comprehensive prediction generation"""
    predictor = MarketPredictor()
    
    indicators = {
        'rsi': 45,
        'ema20': 95,
        'atr': 2.0,
        'volatility': 0.02
    }
    
    prediction = predictor.generate_prediction(
        probability=0.65,
        price=100,
        indicators=indicators,
        account_balance=10000
    )
    
    assert 'signal' in prediction
    assert 'probability' in prediction
    assert 'confidence' in prediction
    assert 'leverage' in prediction
    assert 'stop_loss' in prediction
    assert 'take_profit' in prediction


def test_sentiment_integration():
    """Test sentiment score integration"""
    predictor = MarketPredictor()
    
    # Positive sentiment should boost probability
    signal_with_sentiment = predictor.predict_signal(
        probability=0.55,
        rsi=45,
        price=100,
        ema20=95,
        volatility=0.02,
        sentiment=0.5  # Positive sentiment
    )
    
    signal_without_sentiment = predictor.predict_signal(
        probability=0.55,
        rsi=45,
        price=100,
        ema20=95,
        volatility=0.02,
        sentiment=None
    )
    
    # With positive sentiment, more likely to get buy signal
    assert signal_with_sentiment in [Signal.BUY, Signal.STRONG_BUY, Signal.HOLD]


def test_create_market_predictor_factory():
    """Test factory function"""
    config = {
        'max_leverage': 5.0,
        'risk_per_trade': 0.01
    }
    
    predictor = create_market_predictor(config)
    
    assert predictor.max_leverage == 5.0
    assert predictor.risk_per_trade == 0.01
