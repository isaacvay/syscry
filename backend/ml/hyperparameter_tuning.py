"""
Hyperparameter Tuning Module

Provides automated hyperparameter optimization using:
- GridSearchCV (exhaustive search)
- RandomizedSearchCV (random sampling)
- Optuna (Bayesian optimization)

Supports multiple model types: XGBoost, Random Forest, LightGBM, CatBoost
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional, Any
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, TimeSeriesSplit
from sklearn.metrics import accuracy_score, f1_score, make_scorer
import joblib
import json
from pathlib import Path
from datetime import datetime

try:
    import optuna
    from optuna.samplers import TPESampler
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    print("⚠️ Optuna not installed. Install with: pip install optuna")

from xgboost import XGBClassifier

try:
    from lightgbm import LGBMClassifier
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False

try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False

from sklearn.ensemble import RandomForestClassifier


class HyperparameterTuner:
    """
    Automated hyperparameter tuning for ML models
    """
    
    def __init__(
        self,
        model_type: str = "xgboost",
        tuning_method: str = "random",
        n_trials: int = 50,
        cv_splits: int = 5,
        random_state: int = 42
    ):
        """
        Initialize hyperparameter tuner
        
        Args:
            model_type: Type of model (xgboost, lightgbm, catboost, random_forest)
            tuning_method: Tuning method (grid, random, optuna)
            n_trials: Number of trials for random/optuna
            cv_splits: Number of cross-validation splits
            random_state: Random seed
        """
        self.model_type = model_type.lower()
        self.tuning_method = tuning_method.lower()
        self.n_trials = n_trials
        self.cv_splits = cv_splits
        self.random_state = random_state
        
        # Validate model type
        if self.model_type == "lightgbm" and not LIGHTGBM_AVAILABLE:
            raise ValueError("LightGBM not installed")
        if self.model_type == "catboost" and not CATBOOST_AVAILABLE:
            raise ValueError("CatBoost not installed")
        if self.tuning_method == "optuna" and not OPTUNA_AVAILABLE:
            raise ValueError("Optuna not installed")
    
    def get_param_space(self) -> Dict[str, Any]:
        """
        Get parameter space for the model type
        
        Returns:
            Dict with parameter ranges
        """
        if self.model_type == "xgboost":
            return {
                'n_estimators': [50, 100, 200, 300],
                'max_depth': [3, 5, 7, 9],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'min_child_weight': [1, 3, 5],
                'subsample': [0.6, 0.8, 1.0],
                'colsample_bytree': [0.6, 0.8, 1.0],
                'gamma': [0, 0.1, 0.2],
                'reg_alpha': [0, 0.1, 1],
                'reg_lambda': [1, 1.5, 2]
            }
        
        elif self.model_type == "lightgbm":
            return {
                'n_estimators': [50, 100, 200, 300],
                'max_depth': [3, 5, 7, 9, -1],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'num_leaves': [15, 31, 63, 127],
                'min_child_samples': [10, 20, 30],
                'subsample': [0.6, 0.8, 1.0],
                'colsample_bytree': [0.6, 0.8, 1.0],
                'reg_alpha': [0, 0.1, 1],
                'reg_lambda': [0, 0.1, 1]
            }
        
        elif self.model_type == "catboost":
            return {
                'iterations': [50, 100, 200, 300],
                'depth': [3, 5, 7, 9],
                'learning_rate': [0.01, 0.05, 0.1, 0.2],
                'l2_leaf_reg': [1, 3, 5, 7],
                'border_count': [32, 64, 128],
                'bagging_temperature': [0, 0.5, 1.0]
            }
        
        elif self.model_type == "random_forest":
            return {
                'n_estimators': [50, 100, 200, 300],
                'max_depth': [5, 10, 15, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'max_features': ['sqrt', 'log2', None],
                'bootstrap': [True, False]
            }
        
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
    
    def get_optuna_param_space(self, trial) -> Dict[str, Any]:
        """
        Get parameter space for Optuna optimization
        
        Args:
            trial: Optuna trial object
            
        Returns:
            Dict with suggested parameters
        """
        if self.model_type == "xgboost":
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 9),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 7),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'gamma': trial.suggest_float('gamma', 0, 0.5),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 2),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 2)
            }
        
        elif self.model_type == "lightgbm":
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 3, 9),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'num_leaves': trial.suggest_int('num_leaves', 15, 127),
                'min_child_samples': trial.suggest_int('min_child_samples', 5, 50),
                'subsample': trial.suggest_float('subsample', 0.6, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
                'reg_alpha': trial.suggest_float('reg_alpha', 0, 2),
                'reg_lambda': trial.suggest_float('reg_lambda', 0, 2)
            }
        
        elif self.model_type == "catboost":
            return {
                'iterations': trial.suggest_int('iterations', 50, 300),
                'depth': trial.suggest_int('depth', 3, 9),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'l2_leaf_reg': trial.suggest_int('l2_leaf_reg', 1, 10),
                'border_count': trial.suggest_categorical('border_count', [32, 64, 128]),
                'bagging_temperature': trial.suggest_float('bagging_temperature', 0, 1)
            }
        
        elif self.model_type == "random_forest":
            return {
                'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                'max_depth': trial.suggest_int('max_depth', 5, 30),
                'min_samples_split': trial.suggest_int('min_samples_split', 2, 20),
                'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 10),
                'max_features': trial.suggest_categorical('max_features', ['sqrt', 'log2'])
            }
    
    def create_model(self, params: Optional[Dict] = None):
        """
        Create model instance with given parameters
        
        Args:
            params: Model parameters
            
        Returns:
            Model instance
        """
        if params is None:
            params = {}
        
        if self.model_type == "xgboost":
            return XGBClassifier(
                random_state=self.random_state,
                eval_metric='logloss',
                **params
            )
        
        elif self.model_type == "lightgbm":
            return LGBMClassifier(
                random_state=self.random_state,
                verbose=-1,
                **params
            )
        
        elif self.model_type == "catboost":
            return CatBoostClassifier(
                random_state=self.random_state,
                verbose=False,
                **params
            )
        
        elif self.model_type == "random_forest":
            return RandomForestClassifier(
                random_state=self.random_state,
                **params
            )
    
    def tune_grid_search(
        self,
        X: pd.DataFrame,
        y: pd.Series
    ) -> Tuple[Any, Dict, Dict]:
        """
        Tune hyperparameters using GridSearchCV
        
        Args:
            X: Features
            y: Target
            
        Returns:
            best_model, best_params, results
        """
        print(f"\n🔍 Grid Search for {self.model_type.upper()}")
        print("=" * 50)
        
        # Create base model
        model = self.create_model()
        
        # Get parameter space
        param_grid = self.get_param_space()
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=self.cv_splits)
        
        # Grid search
        grid_search = GridSearchCV(
            model,
            param_grid,
            cv=tscv,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1
        )
        
        grid_search.fit(X, y)
        
        print(f"\n✅ Best Score: {grid_search.best_score_:.4f}")
        print(f"Best Parameters: {grid_search.best_params_}")
        
        results = {
            'best_score': grid_search.best_score_,
            'cv_results': grid_search.cv_results_,
            'tuning_method': 'grid_search'
        }
        
        return grid_search.best_estimator_, grid_search.best_params_, results
    
    def tune_random_search(
        self,
        X: pd.DataFrame,
        y: pd.Series
    ) -> Tuple[Any, Dict, Dict]:
        """
        Tune hyperparameters using RandomizedSearchCV
        
        Args:
            X: Features
            y: Target
            
        Returns:
            best_model, best_params, results
        """
        print(f"\n🎲 Randomized Search for {self.model_type.upper()}")
        print("=" * 50)
        
        # Create base model
        model = self.create_model()
        
        # Get parameter space
        param_distributions = self.get_param_space()
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=self.cv_splits)
        
        # Random search
        random_search = RandomizedSearchCV(
            model,
            param_distributions,
            n_iter=self.n_trials,
            cv=tscv,
            scoring='accuracy',
            n_jobs=-1,
            verbose=1,
            random_state=self.random_state
        )
        
        random_search.fit(X, y)
        
        print(f"\n✅ Best Score: {random_search.best_score_:.4f}")
        print(f"Best Parameters: {random_search.best_params_}")
        
        results = {
            'best_score': random_search.best_score_,
            'cv_results': random_search.cv_results_,
            'tuning_method': 'random_search'
        }
        
        return random_search.best_estimator_, random_search.best_params_, results
    
    def tune_optuna(
        self,
        X: pd.DataFrame,
        y: pd.Series
    ) -> Tuple[Any, Dict, Dict]:
        """
        Tune hyperparameters using Optuna
        
        Args:
            X: Features
            y: Target
            
        Returns:
            best_model, best_params, results
        """
        print(f"\n🎯 Optuna Optimization for {self.model_type.upper()}")
        print("=" * 50)
        
        # Time series cross-validation
        tscv = TimeSeriesSplit(n_splits=self.cv_splits)
        
        def objective(trial):
            # Get parameters
            params = self.get_optuna_param_space(trial)
            
            # Create model
            model = self.create_model(params)
            
            # Cross-validation scores
            scores = []
            for train_idx, val_idx in tscv.split(X):
                X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
                y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
                
                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)
                score = accuracy_score(y_val, y_pred)
                scores.append(score)
            
            return np.mean(scores)
        
        # Create study
        study = optuna.create_study(
            direction='maximize',
            sampler=TPESampler(seed=self.random_state)
        )
        
        # Optimize
        study.optimize(objective, n_trials=self.n_trials, show_progress_bar=True)
        
        print(f"\n✅ Best Score: {study.best_value:.4f}")
        print(f"Best Parameters: {study.best_params}")
        
        # Train final model with best params
        best_model = self.create_model(study.best_params)
        best_model.fit(X, y)
        
        results = {
            'best_score': study.best_value,
            'study': study,
            'tuning_method': 'optuna'
        }
        
        return best_model, study.best_params, results
    
    def tune(
        self,
        X: pd.DataFrame,
        y: pd.Series
    ) -> Tuple[Any, Dict, Dict]:
        """
        Tune hyperparameters using selected method
        
        Args:
            X: Features
            y: Target
            
        Returns:
            best_model, best_params, results
        """
        if self.tuning_method == "grid":
            return self.tune_grid_search(X, y)
        elif self.tuning_method == "random":
            return self.tune_random_search(X, y)
        elif self.tuning_method == "optuna":
            return self.tune_optuna(X, y)
        else:
            raise ValueError(f"Unknown tuning method: {self.tuning_method}")
    
    def save_tuning_results(
        self,
        best_params: Dict,
        results: Dict,
        symbol: str,
        interval: str,
        output_dir: str = "ml/tuning_results"
    ):
        """
        Save tuning results to disk
        
        Args:
            best_params: Best parameters found
            results: Tuning results
            symbol: Crypto symbol
            interval: Timeframe
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.model_type}_{symbol}_{interval}_{self.tuning_method}_{timestamp}.json"
        
        save_data = {
            'model_type': self.model_type,
            'tuning_method': self.tuning_method,
            'symbol': symbol,
            'interval': interval,
            'best_params': best_params,
            'best_score': results['best_score'],
            'timestamp': timestamp
        }
        
        filepath = output_path / filename
        with open(filepath, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"\n💾 Tuning results saved: {filepath}")
        
        # Also save as latest
        latest_file = output_path / f"{self.model_type}_{symbol}_{interval}_latest.json"
        with open(latest_file, 'w') as f:
            json.dump(save_data, f, indent=2)


def load_best_params(
    model_type: str,
    symbol: str,
    interval: str,
    tuning_dir: str = "ml/tuning_results"
) -> Optional[Dict]:
    """
    Load best parameters from previous tuning
    
    Args:
        model_type: Model type
        symbol: Crypto symbol
        interval: Timeframe
        tuning_dir: Tuning results directory
        
    Returns:
        Best parameters dict or None
    """
    tuning_path = Path(tuning_dir)
    latest_file = tuning_path / f"{model_type}_{symbol}_{interval}_latest.json"
    
    if latest_file.exists():
        with open(latest_file, 'r') as f:
            data = json.load(f)
            print(f"✅ Loaded tuned parameters for {model_type} ({data['tuning_method']})")
            return data['best_params']
    
    return None
