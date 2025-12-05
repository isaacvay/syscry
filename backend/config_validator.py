"""
Configuration validation and startup checks
"""
import sys
from config import settings
from logger import logger


def validate_required_settings():
    """
    Validate that required environment variables are set
    Raises ValueError if critical settings are missing
    """
    errors = []
    warnings = []
    
    # Critical settings (app won't work without these)
    # Note: API keys are optional for basic functionality
    
    # Optional but recommended settings
    if not settings.telegram_bot_token:
        warnings.append("TELEGRAM_BOT_TOKEN not set - Telegram alerts will be disabled")
    
    if not settings.telegram_chat_id:
        warnings.append("TELEGRAM_CHAT_ID not set - Telegram alerts will be disabled")
    
    # Sentiment analysis APIs (all optional)
    sentiment_apis = 0
    if settings.twitter_bearer_token:
        sentiment_apis += 1
    else:
        warnings.append("TWITTER_BEARER_TOKEN not set - Twitter sentiment disabled")
    
    if settings.reddit_client_id and settings.reddit_client_secret:
        sentiment_apis += 1
    else:
        warnings.append("REDDIT_CLIENT_ID/SECRET not set - Reddit sentiment disabled")
    
    if settings.news_api_key:
        sentiment_apis += 1
    else:
        warnings.append("NEWS_API_KEY not set - News sentiment disabled")
    
    if sentiment_apis == 0:
        warnings.append("No sentiment analysis APIs configured - sentiment features disabled")
    
    # Log warnings
    if warnings:
        logger.warning("Configuration warnings:")
        for warning in warnings:
            logger.warning(f"  ⚠️  {warning}")
    
    # Raise errors if any critical settings missing
    if errors:
        logger.error("Configuration errors:")
        for error in errors:
            logger.error(f"  ❌ {error}")
        raise ValueError("Missing required configuration. Check .env file and backend/.env.example")
    
    # Log success
    logger.info("✅ Configuration validation passed")
    if sentiment_apis > 0:
        logger.info(f"✅ Sentiment analysis enabled with {sentiment_apis} API(s)")
    
    return True


def print_startup_info():
    """Print startup configuration info"""
    logger.info("=" * 60)
    logger.info("🚀 Crypto AI Backend Starting")
    logger.info("=" * 60)
    logger.info(f"Frontend URL: {settings.frontend_url}")
    logger.info(f"Database: {settings.database_url}")
    logger.info(f"Default Cryptos: {', '.join(settings.default_cryptos)}")
    logger.info(f"Ensemble Models: {settings.use_ensemble}")
    logger.info(f"Sentiment Analysis: {settings.sentiment_enabled}")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Can be run standalone to validate configuration
    try:
        validate_required_settings()
        print_startup_info()
        print("\n✅ Configuration is valid!")
    except ValueError as e:
        print(f"\n❌ Configuration error: {e}")
        sys.exit(1)
