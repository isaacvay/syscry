"""
Sentiment Features Module

Integrates sentiment analysis into ML feature pipeline
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
from ml.sentiment_analyzer import SentimentAnalyzer, create_sentiment_analyzer


def add_sentiment_features(
    df: pd.DataFrame,
    symbol: str,
    sentiment_analyzer: Optional[SentimentAnalyzer] = None,
    crypto_name: Optional[str] = None
) -> pd.DataFrame:
    """
    Add sentiment features to DataFrame
    
    Args:
        df: DataFrame with OHLCV data
        symbol: Crypto symbol
        sentiment_analyzer: Optional SentimentAnalyzer instance
        crypto_name: Full crypto name for news search
        
    Returns:
        DataFrame with sentiment features added
    """
    df = df.copy()
    
    # Create analyzer if not provided
    if sentiment_analyzer is None:
        # Will use default config (may not have API keys)
        sentiment_analyzer = create_sentiment_analyzer()
    
    # Get aggregated sentiment
    sentiment_data = sentiment_analyzer.get_aggregated_sentiment(symbol, crypto_name)
    
    # Add sentiment score as a constant column
    # (In production, you might want to fetch historical sentiment)
    df['sentiment_score'] = sentiment_data['aggregated_sentiment']
    df['sentiment_source_count'] = sentiment_data['source_count']
    
    # Add individual source sentiments if available
    sources = sentiment_data.get('sources', {})
    
    if 'twitter' in sources:
        df['twitter_sentiment'] = sources['twitter']['avg_sentiment']
        df['twitter_positive_ratio'] = sources['twitter']['positive_ratio']
    else:
        df['twitter_sentiment'] = 0.0
        df['twitter_positive_ratio'] = 0.5
    
    if 'reddit' in sources:
        df['reddit_sentiment'] = sources['reddit']['avg_sentiment']
        df['reddit_positive_ratio'] = sources['reddit']['positive_ratio']
    else:
        df['reddit_sentiment'] = 0.0
        df['reddit_positive_ratio'] = 0.5
    
    if 'news' in sources:
        df['news_sentiment'] = sources['news']['avg_sentiment']
        df['news_positive_ratio'] = sources['news']['positive_ratio']
    else:
        df['news_sentiment'] = 0.0
        df['news_positive_ratio'] = 0.5
    
    return df


def get_sentiment_features_list() -> list:
    """
    Get list of sentiment feature column names
    
    Returns:
        List of feature names
    """
    return [
        'sentiment_score',
        'sentiment_source_count',
        'twitter_sentiment',
        'twitter_positive_ratio',
        'reddit_sentiment',
        'reddit_positive_ratio',
        'news_sentiment',
        'news_positive_ratio'
    ]


def create_sentiment_indicator(
    sentiment_score: float,
    threshold_positive: float = 0.2,
    threshold_negative: float = -0.2
) -> str:
    """
    Create categorical sentiment indicator
    
    Args:
        sentiment_score: Aggregated sentiment score
        threshold_positive: Threshold for positive sentiment
        threshold_negative: Threshold for negative sentiment
        
    Returns:
        Sentiment category: 'POSITIVE', 'NEGATIVE', or 'NEUTRAL'
    """
    if sentiment_score > threshold_positive:
        return 'POSITIVE'
    elif sentiment_score < threshold_negative:
        return 'NEGATIVE'
    else:
        return 'NEUTRAL'


# Crypto name mapping for news search
CRYPTO_NAMES = {
    'BTC': 'Bitcoin',
    'BTCUSDT': 'Bitcoin',
    'ETH': 'Ethereum',
    'ETHUSDT': 'Ethereum',
    'SOL': 'Solana',
    'SOLUSDT': 'Solana',
    'BNB': 'Binance Coin',
    'BNBUSDT': 'Binance Coin',
    'ADA': 'Cardano',
    'ADAUSDT': 'Cardano',
    'XRP': 'Ripple',
    'XRPUSDT': 'Ripple',
    'DOT': 'Polkadot',
    'DOTUSDT': 'Polkadot',
    'DOGE': 'Dogecoin',
    'DOGEUSDT': 'Dogecoin'
}


def get_crypto_name(symbol: str) -> Optional[str]:
    """
    Get full crypto name from symbol
    
    Args:
        symbol: Crypto symbol
        
    Returns:
        Full crypto name or None
    """
    return CRYPTO_NAMES.get(symbol.upper())
