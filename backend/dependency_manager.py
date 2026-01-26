"""
Dependency Manager for Graceful Degradation
Handles missing optional dependencies and provides fallback mechanisms
"""

import importlib
import sys
from typing import Dict, List, Optional, Callable, Any
from logger import logger


class DependencyStatus:
    """Status of dependency validation"""
    
    def __init__(self):
        self.available: Dict[str, bool] = {}
        self.missing: List[str] = []
        self.errors: Dict[str, str] = {}
        self.fallbacks: Dict[str, Callable] = {}


class DependencyManager:
    """
    Manages optional dependencies with graceful degradation
    """
    
    def __init__(self):
        self.status = DependencyStatus()
        self._setup_fallbacks()
    
    def _setup_fallbacks(self):
        """Setup fallback functions for missing dependencies"""
        
        # Sentiment analysis fallback
        def sentiment_fallback(*args, **kwargs):
            logger.warning("Sentiment analysis unavailable - using neutral sentiment (0.0)")
            return {"sentiment_score": 0.0, "confidence": 0.0}
        
        # TextBlob fallback
        def textblob_fallback(*args, **kwargs):
            logger.warning("TextBlob unavailable - sentiment analysis disabled")
            return None
        
        self.status.fallbacks = {
            "textblob": textblob_fallback,
            "sentiment_analysis": sentiment_fallback,
            "twitter_api": lambda *args, **kwargs: {"tweets": [], "sentiment": 0.0},
            "reddit_api": lambda *args, **kwargs: {"posts": [], "sentiment": 0.0},
            "news_api": lambda *args, **kwargs: {"articles": [], "sentiment": 0.0}
        }
    
    def validate_dependencies(self) -> DependencyStatus:
        """
        Validate all optional dependencies
        
        Returns:
            DependencyStatus with validation results
        """
        dependencies = {
            "textblob": "textblob",
            "tweepy": "tweepy", 
            "praw": "praw",
            "newsapi": "newsapi-python",
            "requests": "requests",
            "pandas": "pandas",
            "numpy": "numpy",
            "ta": "ta",
            "joblib": "joblib",
            "sklearn": "scikit-learn"
        }
        
        for dep_name, package_name in dependencies.items():
            try:
                importlib.import_module(dep_name)
                self.status.available[dep_name] = True
                logger.debug(f"✅ Dependency available: {dep_name}")
            except ImportError as e:
                self.status.available[dep_name] = False
                self.status.missing.append(dep_name)
                self.status.errors[dep_name] = str(e)
                
                if dep_name in ["textblob", "tweepy", "praw", "newsapi"]:
                    # Optional dependencies
                    logger.warning(f"⚠️ Optional dependency missing: {dep_name}")
                    logger.info(f"💡 To install: pip install {package_name}")
                else:
                    # Critical dependencies
                    logger.error(f"❌ Critical dependency missing: {dep_name}")
                    logger.error(f"🚨 Please install: pip install {package_name}")
        
        # Log summary
        available_count = sum(self.status.available.values())
        total_count = len(dependencies)
        logger.info(f"📊 Dependencies: {available_count}/{total_count} available")
        
        if self.status.missing:
            logger.warning(f"⚠️ Missing dependencies: {', '.join(self.status.missing)}")
        
        return self.status
    
    def get_fallback_for_missing_dependency(self, dependency: str) -> Optional[Callable]:
        """
        Get fallback function for missing dependency
        
        Args:
            dependency: Name of the missing dependency
            
        Returns:
            Fallback function or None
        """
        return self.status.fallbacks.get(dependency)
    
    def is_feature_available(self, feature: str) -> bool:
        """
        Check if a feature is available based on dependencies
        
        Args:
            feature: Feature name to check
            
        Returns:
            True if feature is available
        """
        feature_deps = {
            "sentiment_analysis": ["textblob"],
            "twitter_sentiment": ["tweepy", "textblob"],
            "reddit_sentiment": ["praw", "textblob"],
            "news_sentiment": ["newsapi", "textblob"],
            "ml_prediction": ["pandas", "numpy", "sklearn", "joblib"],
            "technical_analysis": ["ta", "pandas", "numpy"]
        }
        
        if feature not in feature_deps:
            return True  # Unknown features are assumed available
        
        required_deps = feature_deps[feature]
        return all(self.status.available.get(dep, False) for dep in required_deps)
    
    def get_installation_instructions(self, dependency: str) -> str:
        """
        Get installation instructions for missing dependency
        
        Args:
            dependency: Name of the dependency
            
        Returns:
            Installation instruction string
        """
        instructions = {
            "textblob": "pip install textblob && python -m textblob.download_corpora",
            "tweepy": "pip install tweepy",
            "praw": "pip install praw",
            "newsapi": "pip install newsapi-python",
            "requests": "pip install requests",
            "pandas": "pip install pandas",
            "numpy": "pip install numpy",
            "ta": "pip install ta",
            "joblib": "pip install joblib",
            "sklearn": "pip install scikit-learn"
        }
        
        return instructions.get(dependency, f"pip install {dependency}")
    
    def safe_import(self, module_name: str, fallback_value: Any = None):
        """
        Safely import a module with fallback
        
        Args:
            module_name: Name of module to import
            fallback_value: Value to return if import fails
            
        Returns:
            Imported module or fallback value
        """
        try:
            return importlib.import_module(module_name)
        except ImportError:
            logger.warning(f"Module {module_name} not available, using fallback")
            return fallback_value
    
    def require_dependencies(self, dependencies: List[str]) -> bool:
        """
        Check if all required dependencies are available
        
        Args:
            dependencies: List of required dependency names
            
        Returns:
            True if all dependencies are available
            
        Raises:
            ImportError: If any required dependency is missing
        """
        missing = []
        for dep in dependencies:
            if not self.status.available.get(dep, False):
                missing.append(dep)
        
        if missing:
            instructions = [self.get_installation_instructions(dep) for dep in missing]
            error_msg = f"Missing required dependencies: {', '.join(missing)}\n"
            error_msg += "Install with:\n" + "\n".join(instructions)
            raise ImportError(error_msg)
        
        return True


# Global dependency manager instance
dependency_manager = DependencyManager()