"""
Quick test script for sentiment analysis
"""
import sys
import os

# Fix UTF-8 encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.sentiment_analyzer import create_sentiment_analyzer
from config import settings

print("Testing Sentiment Analysis")
print("=" * 60)

# Create analyzer
config = {
    'twitter_bearer_token': settings.twitter_bearer_token,
    'news_api_key': settings.news_api_key,
    'cache_ttl': 3600
}

analyzer = create_sentiment_analyzer(config)

# Test for BTC
print("\n📊 Testing BTC Sentiment...")
sentiment = analyzer.get_aggregated_sentiment('BTC', 'Bitcoin')

print(f"\nResults:")
print(f"  Aggregated Sentiment: {sentiment['aggregated_sentiment']:.3f}")
print(f"  Sources Available: {sentiment['source_count']}")
print(f"  Sources: {list(sentiment['sources'].keys())}")

if sentiment['sources']:
    for source, data in sentiment['sources'].items():
        print(f"\n  {source.upper()}:")
        print(f"    Avg Sentiment: {data['avg_sentiment']:.3f}")
        print(f"    Sample Count: {data['count']}")
        print(f"    Positive: {data['positive_ratio']:.1%}")
        print(f"    Negative: {data['negative_ratio']:.1%}")

print("\n✅ Sentiment test complete!")
