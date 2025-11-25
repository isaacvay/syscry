import pytest
from indicators.signals import generate_signal

def test_generate_signal_basic():
    """Test basic signal generation"""
    result = generate_signal("BTCUSDT", "1h")
    
    # Check structure
    assert "signal" in result
    assert "confidence" in result
    assert "price" in result
    assert "indicators" in result
    assert "chart_data" in result
    
    # Check signal values
    assert result["signal"] in ["BUY", "SELL", "NEUTRE", "BUY (Trend)", "SELL (Trend)"]
    assert 0 <= result["confidence"] <= 1
    assert result["price"] > 0
    
def test_generate_signal_indicators():
    """Test that all indicators are present"""
    result = generate_signal("ETHUSDT", "1h")
    
    indicators = result["indicators"]
    assert "rsi" in indicators
    assert "ema20" in indicators
    assert "ema50" in indicators
    assert "macd" in indicators
    assert "atr" in indicators
    assert "stoch_k" in indicators
    assert "stoch_d" in indicators
    assert "adx" in indicators
    
    # Check RSI bounds
    assert 0 <= indicators["rsi"] <= 100
    
def test_generate_signal_chart_data():
    """Test chart data format"""
    result = generate_signal("SOLUSDT", "1h")
    
    chart_data = result["chart_data"]
    assert len(chart_data) > 0
    
    # Check first candle structure
    candle = chart_data[0]
    assert "time" in candle
    assert "open" in candle
    assert "high" in candle
    assert "low" in candle
    assert "close" in candle
    
    # Check OHLC logic
    assert candle["high"] >= candle["low"]
    assert candle["high"] >= candle["open"]
    assert candle["high"] >= candle["close"]
    assert candle["low"] <= candle["open"]
    assert candle["low"] <= candle["close"]

def test_generate_signal_invalid_symbol():
    """Test with invalid symbol"""
    result = generate_signal("INVALID", "1h")
    # Should return error or handle gracefully
    assert "error" in result or "signal" in result
