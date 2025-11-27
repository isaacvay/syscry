"""
Sentiment Analysis Module

Provides multi-source sentiment analysis:
- Twitter/X sentiment scraping
- Reddit sentiment analysis
- News sentiment analysis
- Sentiment scoring and aggregation
- Caching to avoid rate limits
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Optional imports with graceful degradation
try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False
    print("⚠️ Tweepy not available. Install with: pip install tweepy")

try:
    import praw
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False
    print("⚠️ PRAW not available. Install with: pip install praw")

try:
    from newsapi import NewsApiClient
    NEWS_API_AVAILABLE = True
except ImportError:
    NEWS_API_AVAILABLE = False
    print("⚠️ NewsAPI not available. Install with: pip install newsapi-python")


class SentimentAnalyzer:
    """
    Multi-source sentiment analysis for crypto markets
    """
    
    def __init__(
        self,
        twitter_bearer_token: Optional[str] = None,
        reddit_client_id: Optional[str] = None,
        reddit_client_secret: Optional[str] = None,
        reddit_user_agent: Optional[str] = None,
        news_api_key: Optional[str] = None,
        cache_ttl: int = 3600  # 1 hour cache
    ):
        """
        Initialize sentiment analyzer
        
        Args:
            twitter_bearer_token: Twitter API bearer token
            reddit_client_id: Reddit API client ID
            reddit_client_secret: Reddit API client secret
            reddit_user_agent: Reddit API user agent
            news_api_key: News API key
            cache_ttl: Cache time-to-live in seconds
        """
        self.cache_ttl = cache_ttl
        self._cache = {}
        
        # Initialize VADER sentiment analyzer
        self.vader = SentimentIntensityAnalyzer()
        
        # Initialize Twitter client
        self.twitter_client = None
        if TWITTER_AVAILABLE and twitter_bearer_token:
            try:
                self.twitter_client = tweepy.Client(bearer_token=twitter_bearer_token)
                print("✅ Twitter API initialized")
            except Exception as e:
                print(f"⚠️ Twitter API initialization failed: {e}")
        
        # Initialize Reddit client (DISABLED - no API access)
        self.reddit_client = None
        # Reddit API disabled by user request
        print("ℹ️ Reddit API disabled (no API access)")
        
        # Initialize News API client
        self.news_client = None
        if NEWS_API_AVAILABLE and news_api_key:
            try:
                self.news_client = NewsApiClient(api_key=news_api_key)
                print("✅ News API initialized")
            except Exception as e:
                print(f"⚠️ News API initialization failed: {e}")
    
    def _get_cache_key(self, source: str, symbol: str) -> str:
        """Generate cache key"""
        return f"{source}_{symbol}_{datetime.now().strftime('%Y%m%d_%H')}"
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if valid"""
        if cache_key in self._cache:
            cached_data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        return None
    
    def _set_cache(self, cache_key: str, data: Dict):
        """Set data in cache"""
        self._cache[cache_key] = (data, time.time())
    
    def analyze_text_sentiment(self, text: str) -> Dict[str, float]:
        """
        Analyze sentiment of a single text using multiple methods
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict with sentiment scores
        """
        # VADER sentiment (good for social media)
        vader_scores = self.vader.polarity_scores(text)
        
        # TextBlob sentiment
        blob = TextBlob(text)
        textblob_polarity = blob.sentiment.polarity
        textblob_subjectivity = blob.sentiment.subjectivity
        
        # Combined score (average of VADER compound and TextBlob polarity)
        combined_score = (vader_scores['compound'] + textblob_polarity) / 2
        
        return {
            'vader_compound': vader_scores['compound'],
            'vader_positive': vader_scores['pos'],
            'vader_negative': vader_scores['neg'],
            'vader_neutral': vader_scores['neu'],
            'textblob_polarity': textblob_polarity,
            'textblob_subjectivity': textblob_subjectivity,
            'combined_score': combined_score
        }
    
    def get_twitter_sentiment(
        self,
        symbol: str,
        max_tweets: int = 100
    ) -> Optional[Dict]:
        """
        Get Twitter sentiment for a crypto symbol
        
        Args:
            symbol: Crypto symbol (e.g., BTC, ETH)
            max_tweets: Maximum tweets to analyze
            
        Returns:
            Dict with sentiment metrics or None
        """
        if not self.twitter_client:
            return None
        
        # Check cache
        cache_key = self._get_cache_key('twitter', symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Search for tweets
            query = f"${symbol} OR #{symbol} -is:retweet lang:en"
            tweets = self.twitter_client.search_recent_tweets(
                query=query,
                max_results=min(max_tweets, 100),
                tweet_fields=['created_at', 'public_metrics']
            )
            
            if not tweets.data:
                return None
            
            # Analyze sentiment of each tweet
            sentiments = []
            for tweet in tweets.data:
                sentiment = self.analyze_text_sentiment(tweet.text)
                sentiments.append(sentiment['combined_score'])
            
            # Aggregate metrics
            result = {
                'source': 'twitter',
                'symbol': symbol,
                'count': len(sentiments),
                'avg_sentiment': np.mean(sentiments),
                'sentiment_std': np.std(sentiments),
                'positive_ratio': sum(1 for s in sentiments if s > 0.1) / len(sentiments),
                'negative_ratio': sum(1 for s in sentiments if s < -0.1) / len(sentiments),
                'neutral_ratio': sum(1 for s in sentiments if -0.1 <= s <= 0.1) / len(sentiments),
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            self._set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"⚠️ Twitter sentiment error: {e}")
            return None
    
    def get_reddit_sentiment(
        self,
        symbol: str,
        subreddits: List[str] = ['cryptocurrency', 'CryptoMarkets', 'Bitcoin'],
        max_posts: int = 50
    ) -> Optional[Dict]:
        """
        Get Reddit sentiment for a crypto symbol
        
        Args:
            symbol: Crypto symbol
            subreddits: List of subreddits to search
            max_posts: Maximum posts to analyze
            
        Returns:
            Dict with sentiment metrics or None
        """
        if not self.reddit_client:
            return None
        
        # Check cache
        cache_key = self._get_cache_key('reddit', symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            sentiments = []
            
            for subreddit_name in subreddits:
                subreddit = self.reddit_client.subreddit(subreddit_name)
                
                # Search for posts
                for post in subreddit.search(symbol, limit=max_posts // len(subreddits)):
                    # Analyze title and selftext
                    text = f"{post.title} {post.selftext}"
                    sentiment = self.analyze_text_sentiment(text)
                    sentiments.append(sentiment['combined_score'])
                    
                    # Also analyze top comments
                    post.comments.replace_more(limit=0)
                    for comment in post.comments[:3]:  # Top 3 comments
                        if hasattr(comment, 'body'):
                            comment_sentiment = self.analyze_text_sentiment(comment.body)
                            sentiments.append(comment_sentiment['combined_score'])
            
            if not sentiments:
                return None
            
            # Aggregate metrics
            result = {
                'source': 'reddit',
                'symbol': symbol,
                'count': len(sentiments),
                'avg_sentiment': np.mean(sentiments),
                'sentiment_std': np.std(sentiments),
                'positive_ratio': sum(1 for s in sentiments if s > 0.1) / len(sentiments),
                'negative_ratio': sum(1 for s in sentiments if s < -0.1) / len(sentiments),
                'neutral_ratio': sum(1 for s in sentiments if -0.1 <= s <= 0.1) / len(sentiments),
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            self._set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"⚠️ Reddit sentiment error: {e}")
            return None
    
    def get_news_sentiment(
        self,
        symbol: str,
        crypto_name: Optional[str] = None,
        max_articles: int = 50
    ) -> Optional[Dict]:
        """
        Get news sentiment for a crypto symbol
        
        Args:
            symbol: Crypto symbol (e.g., BTC)
            crypto_name: Full crypto name (e.g., Bitcoin)
            max_articles: Maximum articles to analyze
            
        Returns:
            Dict with sentiment metrics or None
        """
        if not self.news_client:
            return None
        
        # Check cache
        cache_key = self._get_cache_key('news', symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            # Build query
            if crypto_name:
                query = f"{crypto_name} OR {symbol}"
            else:
                query = symbol
            
            # Get articles from last 7 days
            from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            
            articles = self.news_client.get_everything(
                q=query,
                from_param=from_date,
                language='en',
                sort_by='relevancy',
                page_size=min(max_articles, 100)
            )
            
            if not articles['articles']:
                return None
            
            # Analyze sentiment
            sentiments = []
            for article in articles['articles']:
                text = f"{article['title']} {article.get('description', '')}"
                sentiment = self.analyze_text_sentiment(text)
                sentiments.append(sentiment['combined_score'])
            
            # Aggregate metrics
            result = {
                'source': 'news',
                'symbol': symbol,
                'count': len(sentiments),
                'avg_sentiment': np.mean(sentiments),
                'sentiment_std': np.std(sentiments),
                'positive_ratio': sum(1 for s in sentiments if s > 0.1) / len(sentiments),
                'negative_ratio': sum(1 for s in sentiments if s < -0.1) / len(sentiments),
                'neutral_ratio': sum(1 for s in sentiments if -0.1 <= s <= 0.1) / len(sentiments),
                'timestamp': datetime.now().isoformat()
            }
            
            # Cache result
            self._set_cache(cache_key, result)
            
            return result
            
        except Exception as e:
            print(f"⚠️ News sentiment error: {e}")
            return None
    
    def get_aggregated_sentiment(
        self,
        symbol: str,
        crypto_name: Optional[str] = None
    ) -> Dict:
        """
        Get aggregated sentiment from all available sources
        
        Args:
            symbol: Crypto symbol
            crypto_name: Full crypto name for news search
            
        Returns:
            Dict with aggregated sentiment metrics
        """
        sentiments = {}
        
        # Get sentiment from each source
        twitter_sentiment = self.get_twitter_sentiment(symbol)
        if twitter_sentiment:
            sentiments['twitter'] = twitter_sentiment
        
        reddit_sentiment = self.get_reddit_sentiment(symbol)
        if reddit_sentiment:
            sentiments['reddit'] = reddit_sentiment
        
        news_sentiment = self.get_news_sentiment(symbol, crypto_name)
        if news_sentiment:
            sentiments['news'] = news_sentiment
        
        # Aggregate if we have any data
        if sentiments:
            # Weighted average (news has higher weight)
            weights = {'twitter': 0.3, 'reddit': 0.3, 'news': 0.4}
            
            weighted_sentiment = 0
            total_weight = 0
            
            for source, data in sentiments.items():
                weight = weights.get(source, 0.33)
                weighted_sentiment += data['avg_sentiment'] * weight
                total_weight += weight
            
            if total_weight > 0:
                final_sentiment = weighted_sentiment / total_weight
            else:
                final_sentiment = 0
            
            return {
                'symbol': symbol,
                'aggregated_sentiment': final_sentiment,
                'sources': sentiments,
                'source_count': len(sentiments),
                'timestamp': datetime.now().isoformat()
            }
        else:
            # No sentiment data available
            return {
                'symbol': symbol,
                'aggregated_sentiment': 0.0,
                'sources': {},
                'source_count': 0,
                'timestamp': datetime.now().isoformat()
            }


def create_sentiment_analyzer(config: Optional[Dict] = None) -> SentimentAnalyzer:
    """
    Factory function to create SentimentAnalyzer
    
    Args:
        config: Configuration dict with API keys
        
    Returns:
        SentimentAnalyzer instance
    """
    if config is None:
        config = {}
    
    return SentimentAnalyzer(
        twitter_bearer_token=config.get('twitter_bearer_token'),
        reddit_client_id=config.get('reddit_client_id'),
        reddit_client_secret=config.get('reddit_client_secret'),
        reddit_user_agent=config.get('reddit_user_agent', 'CryptoSentimentBot/1.0'),
        news_api_key=config.get('news_api_key'),
        cache_ttl=config.get('cache_ttl', 3600)
    )
