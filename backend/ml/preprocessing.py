"""
Data Preprocessing Module

Provides robust data preprocessing for ML models:
- Outlier detection and handling
- Feature scaling (robust, standard, minmax)
- Feature selection based on importance
- Missing value handling
"""

import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.preprocessing import RobustScaler, StandardScaler, MinMaxScaler
from sklearn.feature_selection import SelectKBest, mutual_info_classif
from scipy import stats


class DataPreprocessor:
    """
    Comprehensive data preprocessing for ML models
    """
    
    def __init__(
        self,
        scaling_method: str = "robust",
        outlier_method: str = "iqr",
        outlier_threshold: float = 3.0,
        feature_selection_enabled: bool = True,
        max_features: Optional[int] = None
    ):
        """
        Initialize preprocessor
        
        Args:
            scaling_method: 'robust', 'standard', or 'minmax'
            outlier_method: 'iqr', 'zscore', or 'none'
            outlier_threshold: Threshold for outlier detection
            feature_selection_enabled: Enable automatic feature selection
            max_features: Maximum number of features to keep
        """
        self.scaling_method = scaling_method
        self.outlier_method = outlier_method
        self.outlier_threshold = outlier_threshold
        self.feature_selection_enabled = feature_selection_enabled
        self.max_features = max_features
        
        # Initialize scaler
        if scaling_method == "robust":
            self.scaler = RobustScaler()
        elif scaling_method == "standard":
            self.scaler = StandardScaler()
        elif scaling_method == "minmax":
            self.scaler = MinMaxScaler()
        else:
            raise ValueError(f"Unknown scaling method: {scaling_method}")
        
        self.selected_features = None
        self.feature_scores = None
    
    def detect_outliers_iqr(
        self, 
        df: pd.DataFrame, 
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Detect outliers using IQR method
        
        Args:
            df: Input DataFrame
            columns: Columns to check (None = all numeric)
            
        Returns:
            Boolean DataFrame indicating outliers
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        outliers = pd.DataFrame(False, index=df.index, columns=columns)
        
        for col in columns:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            
            lower_bound = Q1 - self.outlier_threshold * IQR
            upper_bound = Q3 + self.outlier_threshold * IQR
            
            outliers[col] = (df[col] < lower_bound) | (df[col] > upper_bound)
        
        return outliers
    
    def detect_outliers_zscore(
        self, 
        df: pd.DataFrame, 
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Detect outliers using Z-score method
        
        Args:
            df: Input DataFrame
            columns: Columns to check (None = all numeric)
            
        Returns:
            Boolean DataFrame indicating outliers
        """
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        outliers = pd.DataFrame(False, index=df.index, columns=columns)
        
        for col in columns:
            z_scores = np.abs(stats.zscore(df[col].fillna(df[col].median())))
            outliers[col] = z_scores > self.outlier_threshold
        
        return outliers
    
    def handle_outliers(
        self, 
        df: pd.DataFrame, 
        method: str = "clip",
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Handle outliers in DataFrame
        
        Args:
            df: Input DataFrame
            method: 'clip', 'remove', or 'winsorize'
            columns: Columns to process
            
        Returns:
            DataFrame with outliers handled
        """
        df = df.copy()
        
        if self.outlier_method == "none":
            return df
        
        # Detect outliers
        if self.outlier_method == "iqr":
            outliers = self.detect_outliers_iqr(df, columns)
        elif self.outlier_method == "zscore":
            outliers = self.detect_outliers_zscore(df, columns)
        else:
            return df
        
        if columns is None:
            columns = outliers.columns.tolist()
        
        # Handle outliers
        for col in columns:
            if method == "clip":
                # Clip to percentiles
                lower = df[col].quantile(0.01)
                upper = df[col].quantile(0.99)
                df[col] = df[col].clip(lower, upper)
            
            elif method == "remove":
                # Mark rows with outliers for removal
                df.loc[outliers[col], col] = np.nan
            
            elif method == "winsorize":
                # Winsorize (replace with percentile values)
                lower = df[col].quantile(0.05)
                upper = df[col].quantile(0.95)
                df.loc[df[col] < lower, col] = lower
                df.loc[df[col] > upper, col] = upper
        
        return df
    
    def handle_missing_values(
        self, 
        df: pd.DataFrame,
        strategy: str = "forward_fill"
    ) -> pd.DataFrame:
        """
        Handle missing values
        
        Args:
            df: Input DataFrame
            strategy: 'forward_fill', 'backward_fill', 'mean', 'median', 'interpolate'
            
        Returns:
            DataFrame with missing values handled
        """
        df = df.copy()
        
        if strategy == "forward_fill":
            df = df.fillna(method='ffill')
        elif strategy == "backward_fill":
            df = df.fillna(method='bfill')
        elif strategy == "mean":
            df = df.fillna(df.mean())
        elif strategy == "median":
            df = df.fillna(df.median())
        elif strategy == "interpolate":
            df = df.interpolate(method='linear')
        
        # Fill any remaining NaN with 0
        df = df.fillna(0)
        
        return df
    
    def select_features(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        method: str = "mutual_info",
        k: Optional[int] = None
    ) -> List[str]:
        """
        Select most important features
        
        Args:
            X: Features DataFrame
            y: Target Series
            method: 'mutual_info', 'correlation', or 'variance'
            k: Number of features to select (None = use max_features)
            
        Returns:
            List of selected feature names
        """
        if k is None:
            k = self.max_features if self.max_features else len(X.columns)
        
        k = min(k, len(X.columns))
        
        if method == "mutual_info":
            # Mutual information
            selector = SelectKBest(mutual_info_classif, k=k)
            selector.fit(X, y)
            
            # Get scores
            scores = pd.DataFrame({
                'feature': X.columns,
                'score': selector.scores_
            }).sort_values('score', ascending=False)
            
            self.feature_scores = scores
            selected = scores.head(k)['feature'].tolist()
        
        elif method == "correlation":
            # Correlation with target
            correlations = X.corrwith(y).abs().sort_values(ascending=False)
            selected = correlations.head(k).index.tolist()
            
            self.feature_scores = pd.DataFrame({
                'feature': correlations.index,
                'score': correlations.values
            })
        
        elif method == "variance":
            # Variance threshold
            variances = X.var().sort_values(ascending=False)
            selected = variances.head(k).index.tolist()
            
            self.feature_scores = pd.DataFrame({
                'feature': variances.index,
                'score': variances.values
            })
        
        else:
            selected = X.columns.tolist()
        
        self.selected_features = selected
        return selected
    
    def fit_transform(
        self,
        X: pd.DataFrame,
        y: Optional[pd.Series] = None
    ) -> pd.DataFrame:
        """
        Fit and transform features
        
        Args:
            X: Features DataFrame
            y: Optional target for feature selection
            
        Returns:
            Transformed DataFrame
        """
        X = X.copy()
        
        # Handle missing values
        X = self.handle_missing_values(X, strategy="forward_fill")
        
        # Handle outliers
        X = self.handle_outliers(X, method="clip")
        
        # Feature selection
        if self.feature_selection_enabled and y is not None:
            selected_features = self.select_features(X, y, method="mutual_info")
            X = X[selected_features]
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        X = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
        
        return X
    
    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Transform features using fitted scaler
        
        Args:
            X: Features DataFrame
            
        Returns:
            Transformed DataFrame
        """
        X = X.copy()
        
        # Handle missing values
        X = self.handle_missing_values(X, strategy="forward_fill")
        
        # Handle outliers
        X = self.handle_outliers(X, method="clip")
        
        # Use selected features if available
        if self.selected_features is not None:
            # Add missing features with 0
            for col in self.selected_features:
                if col not in X.columns:
                    X[col] = 0
            X = X[self.selected_features]
        
        # Scale features
        X_scaled = self.scaler.transform(X)
        X = pd.DataFrame(X_scaled, columns=X.columns, index=X.index)
        
        return X


def create_preprocessor(config: dict) -> DataPreprocessor:
    """
    Create preprocessor from config
    
    Args:
        config: Configuration dict
        
    Returns:
        DataPreprocessor instance
    """
    return DataPreprocessor(
        scaling_method=config.get('feature_scaling_method', 'robust'),
        outlier_method=config.get('outlier_method', 'iqr'),
        outlier_threshold=config.get('outlier_threshold', 3.0),
        feature_selection_enabled=config.get('feature_selection_enabled', True),
        max_features=config.get('max_features', None)
    )
