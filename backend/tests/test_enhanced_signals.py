"""
Tests for enhanced signal reliability improvements
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from services.signal_service import UnifiedSignalGenerator
from dependency_manager import DependencyManager
from exceptions import BinanceAPIError, DataQualityError, PredictionError
from indicators.signals import EnhancedDataFetcher


class TestUnifiedSignalGenerator:
    """Test the unified signal generator"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.generator = UnifiedSignalGenerator()
        
        # Create sample DataFrame
        self.sample_df = pd.DataFrame({
            'timestamp': [1640995200000, 1640998800000, 1641002400000],
            'open': [50000, 50100, 50200],
            'high': [50200, 50300, 50400],
            'low': [49900, 50000, 50100],
            'close': [50100, 50200, 50300],
            'volume': [1000, 1100, 1200]
        })
    
    def test_signal_generation_success(self):
        """Test successful signal generation"""
        with patch('services.signal_service.get_binance_data') as mock_data:
            mock_data.return_value = self.sample_df
            
            result = self.generator.generate_signal("BTCUSDT", "1h")
            
            assert "signal" in result
            assert "confidence" in result
            assert "price" in result
            assert "indicators" in result
            assert result["symbol"] == "BTCUSDT"
            assert result["timeframe"] == "1h"
    
    def test_signal_generation_with_empty_data(self):
        """Test signal generation with empty data"""
        with patch('services.signal_service.get_binance_data') as mock_data:
            mock_data.return_value = pd.DataFrame()
            
            result = self.generator.generate_signal("BTCUSDT", "1h")
            
            assert "error" in result
            assert result["error"] == "Could not fetch data"
    
    def test_fallback_signal_generation(self):
        """Test fallback signal generation when ML fails"""
        with patch('services.signal_service.get_binance_data') as mock_data:
            with patch('services.signal_service.predict_with_market_analysis') as mock_predict:
                mock_data.return_value = self.sample_df
                mock_predict.side_effect = Exception("ML prediction failed")
                
                result = self.generator.generate_signal("BTCUSDT", "1h")
                
                assert "signal" in result
                assert "confidence" in result
                # Should fallback to heuristic
                assert result["signal"] in ["BUY", "SELL", "HOLD"]
    
    def test_indicator_calculation_error_handling(self):
        """Test handling of indicator calculation errors"""
        # Create DataFrame with invalid data
        invalid_df = pd.DataFrame({
            'timestamp': [1640995200000],
            'open': [np.nan],
            'high': [np.nan],
            'low': [np.nan],
            'close': [np.nan],
            'volume': [np.nan]
        })
        
        with patch('services.signal_service.get_binance_data') as mock_data:
            mock_data.return_value = invalid_df
            
            result = self.generator.generate_signal("BTCUSDT", "1h")
            
            # Should handle gracefully and return result
            assert "signal" in result or "error" in result


class TestEnhancedDataFetcher:
    """Test the enhanced data fetcher"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.fetcher = EnhancedDataFetcher()
    
    def test_data_quality_validation(self):
        """Test data quality validation"""
        # Create DataFrame with quality issues
        df_with_issues = pd.DataFrame({
            'timestamp': [1640995200000, 1640998800000],
            'open': [50000, np.nan],  # NaN value
            'high': [50200, 50300],
            'low': [49900, 50000],
            'close': [50100, 50200],
            'volume': [1000, 1100]
        })
        
        # Should clean the data
        cleaned_df = self.fetcher.validate_data_quality(df_with_issues, "BTCUSDT")
        
        # NaN should be filled
        assert not cleaned_df.isnull().any().any()
    
    def test_invalid_price_data_rejection(self):
        """Test rejection of invalid price data"""
        # Create DataFrame with invalid prices
        df_invalid = pd.DataFrame({
            'timestamp': [1640995200000],
            'open': [-1],  # Invalid negative price
            'high': [50200],
            'low': [49900],
            'close': [50100],
            'volume': [1000]
        })
        
        with pytest.raises(DataQualityError):
            self.fetcher.validate_data_quality(df_invalid, "BTCUSDT")


class TestDependencyManager:
    """Test the dependency manager"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.manager = DependencyManager()
    
    def test_dependency_validation(self):
        """Test dependency validation"""
        status = self.manager.validate_dependencies()
        
        assert hasattr(status, 'available')
        assert hasattr(status, 'missing')
        assert isinstance(status.available, dict)
        assert isinstance(status.missing, list)
    
    def test_feature_availability_check(self):
        """Test feature availability checking"""
        # Test known features
        ml_available = self.manager.is_feature_available("ml_prediction")
        ta_available = self.manager.is_feature_available("technical_analysis")
        
        assert isinstance(ml_available, bool)
        assert isinstance(ta_available, bool)
    
    def test_fallback_function_retrieval(self):
        """Test fallback function retrieval"""
        fallback = self.manager.get_fallback_for_missing_dependency("textblob")
        
        if fallback:
            assert callable(fallback)
    
    def test_installation_instructions(self):
        """Test installation instruction generation"""
        instructions = self.manager.get_installation_instructions("textblob")
        
        assert isinstance(instructions, str)
        assert "pip install" in instructions


class TestErrorHandling:
    """Test enhanced error handling"""
    
    def test_binance_api_error_context(self):
        """Test BinanceAPIError with context"""
        error = BinanceAPIError(
            "API request failed",
            status_code=429,
            symbol="BTCUSDT",
            attempt=3
        )
        
        assert error.message == "API request failed"
        assert error.context["status_code"] == 429
        assert error.context["symbol"] == "BTCUSDT"
        assert error.context["attempt"] == 3
    
    def test_data_quality_error_context(self):
        """Test DataQualityError with context"""
        quality_issues = {"null_values": {"open": 5}}
        
        error = DataQualityError(
            "Data quality issues detected",
            symbol="ETHUSDT",
            quality_issues=quality_issues
        )
        
        assert error.context["symbol"] == "ETHUSDT"
        assert error.context["quality_issues"] == quality_issues
    
    def test_exception_to_dict_conversion(self):
        """Test exception to dictionary conversion"""
        error = PredictionError(
            "Prediction failed",
            symbol="BTCUSDT",
            prediction_type="ensemble"
        )
        
        error_dict = error.to_dict()
        
        assert error_dict["error_type"] == "PredictionError"
        assert error_dict["message"] == "Prediction failed"
        assert error_dict["context"]["symbol"] == "BTCUSDT"
        assert "timestamp" in error_dict


# Property-based tests (if hypothesis is available)
try:
    from hypothesis import given, strategies as st
    
    class TestSignalProperties:
        """Property-based tests for signal generation"""
        
        @given(
            prices=st.lists(st.floats(min_value=0.01, max_value=100000), min_size=50, max_size=100),
            volumes=st.lists(st.floats(min_value=0, max_value=1000000), min_size=50, max_size=100)
        )
        def test_signal_confidence_bounds(self, prices, volumes):
            """Property: Signal confidence should always be between 0 and 1"""
            # Create DataFrame from generated data
            df = pd.DataFrame({
                'timestamp': range(len(prices)),
                'open': prices,
                'high': [p * 1.01 for p in prices],
                'low': [p * 0.99 for p in prices],
                'close': prices,
                'volume': volumes[:len(prices)]
            })
            
            generator = UnifiedSignalGenerator()
            
            with patch('services.signal_service.get_binance_data') as mock_data:
                mock_data.return_value = df
                
                result = generator.generate_signal("BTCUSDT", "1h")
                
                if "confidence" in result:
                    assert 0.0 <= result["confidence"] <= 1.0
        
        @given(st.text(min_size=1, max_size=10))
        def test_signal_types_validity(self, symbol):
            """Property: Generated signals should be valid types"""
            valid_signals = {"BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL", "NEUTRE"}
            
            # Create minimal valid DataFrame
            df = pd.DataFrame({
                'timestamp': [1640995200000],
                'open': [50000],
                'high': [50100],
                'low': [49900],
                'close': [50000],
                'volume': [1000]
            })
            
            generator = UnifiedSignalGenerator()
            
            with patch('services.signal_service.get_binance_data') as mock_data:
                mock_data.return_value = df
                
                result = generator.generate_signal(symbol, "1h")
                
                if "signal" in result:
                    assert result["signal"] in valid_signals

except ImportError:
    # Hypothesis not available, skip property-based tests
    pass


if __name__ == "__main__":
    pytest.main([__file__])