"""
Unit tests for sentiment analysis
"""

import pytest
from ml.sentiment_analyzer import SentimentAnalyzer, create_sentiment_analyzer
from ml.sentiment_features import (
    get_sentiment_features_list,
    create_sentiment_indicator,
    get_crypto_name
)


def test_sentiment_analyzer_initialization():
    """Test SentimentAnalyzer initialization"""
    analyzer = SentimentAnalyzer()
    assert analyzer.cache_ttl == 3600
    assert analyzer.vader is not None


def test_analyze_text_sentiment():
    """Test text sentiment analysis"""
    analyzer = SentimentAnalyzer()
    
    # Positive text
    positive_result = analyzer.analyze_text_sentiment("Bitcoin is amazing! Great investment!")
    assert positive_result['combined_score'] > 0
    
    # Negative text
    negative_result = analyzer.analyze_text_sentiment("Bitcoin is terrible. Worst investment ever.")
    assert negative_result['combined_score'] < 0
    
    # Neutral text
    neutral_result = analyzer.analyze_text_sentiment("Bitcoin is a cryptocurrency.")
    assert abs(neutral_result['combined_score']) < 0.3


def test_get_aggregated_sentiment_no_apis():
    """Test aggregated sentiment without API keys"""
    analyzer = SentimentAnalyzer()
    
    result = analyzer.get_aggregated_sentiment('BTC')
    
    assert 'symbol' in result
    assert 'aggregated_sentiment' in result
    assert 'sources' in result
    assert 'source_count' in result


def test_create_sentiment_analyzer_factory():
    """Test factory function"""
    config = {
        'cache_ttl': 1800
    }
    
    analyzer = create_sentiment_analyzer(config)
    assert analyzer.cache_ttl == 1800


def test_get_sentiment_features_list():
    """Test sentiment features list"""
    features = get_sentiment_features_list()
    
    assert 'sentiment_score' in features
    assert 'twitter_sentiment' in features
    assert 'reddit_sentiment' in features
    assert 'news_sentiment' in features


def test_create_sentiment_indicator():
    """Test sentiment indicator creation"""
    # Positive
    assert create_sentiment_indicator(0.3) == 'POSITIVE'
    
    # Negative
    assert create_sentiment_indicator(-0.3) == 'NEGATIVE'
    
    # Neutral
    assert create_sentiment_indicator(0.1) == 'NEUTRAL'


def test_get_crypto_name():
    """Test crypto name mapping"""
    assert get_crypto_name('BTC') == 'Bitcoin'
    assert get_crypto_name('BTCUSDT') == 'Bitcoin'
    assert get_crypto_name('ETH') == 'Ethereum'
    assert get_crypto_name('ETHUSDT') == 'Ethereum'
    assert get_crypto_name('UNKNOWN') is None


def test_sentiment_caching():
    """Test sentiment caching mechanism"""
    analyzer = SentimentAnalyzer(cache_ttl=10)
    
    # First call
    result1 = analyzer.get_aggregated_sentiment('BTC')
    
    # Second call (should use cache)
    result2 = analyzer.get_aggregated_sentiment('BTC')
    
    # Results should be identical (from cache)
    assert result1['aggregated_sentiment'] == result2['aggregated_sentiment']
