"""
Tests for config_validator module
"""
import pytest
import os
from unittest.mock import patch
from config_validator import validate_required_settings


class TestConfigValidator:
    """Test configuration validation"""
    
    def test_validation_passes_with_minimal_config(self):
        """Test that validation passes with minimal required config"""
        # Should not raise any errors
        try:
            validate_required_settings()
            assert True
        except ValueError:
            pytest.fail("Validation should pass with minimal config")
    
    @patch('config_validator.settings')
    def test_warns_on_missing_telegram_config(self, mock_settings, caplog):
        """Test warning when Telegram config is missing"""
        mock_settings.telegram_bot_token = ""
        mock_settings.telegram_chat_id = ""
        mock_settings.twitter_bearer_token = ""
        mock_settings.reddit_client_id = ""
        mock_settings.reddit_client_secret = ""
        mock_settings.news_api_key = ""
        
        validate_required_settings()
        
        # Should log warnings
        assert "TELEGRAM_BOT_TOKEN not set" in caplog.text
        assert "TELEGRAM_CHAT_ID not set" in caplog.text
    
    @patch('config_validator.settings')
    def test_warns_on_no_sentiment_apis(self, mock_settings, caplog):
        """Test warning when no sentiment APIs are configured"""
        mock_settings.telegram_bot_token = "test"
        mock_settings.telegram_chat_id = "test"
        mock_settings.twitter_bearer_token = ""
        mock_settings.reddit_client_id = ""
        mock_settings.reddit_client_secret = ""
        mock_settings.news_api_key = ""
        
        validate_required_settings()
        
        assert "No sentiment analysis APIs configured" in caplog.text
    
    @patch('config_validator.settings')
    def test_counts_sentiment_apis_correctly(self, mock_settings, caplog):
        """Test that sentiment APIs are counted correctly"""
        mock_settings.telegram_bot_token = "test"
        mock_settings.telegram_chat_id = "test"
        mock_settings.twitter_bearer_token = "test_token"
        mock_settings.reddit_client_id = "test_id"
        mock_settings.reddit_client_secret = "test_secret"
        mock_settings.news_api_key = "test_key"
        
        validate_required_settings()
        
        # Should have 3 APIs enabled
        assert "Sentiment analysis enabled with 3 API(s)" in caplog.text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
