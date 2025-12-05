"""
Ensemble Models Module

Provides ensemble learning capabilities:
- Multiple model types (XGBoost, Random Forest, LightGBM, CatBoost)
- Voting classifier (soft voting)
- Stacking classifier with meta-learner
- Model performance comparison
- Individual and ensemble predictions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from sklearn.ensemble import VotingClassifier, StackingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score, TimeSeriesSplit
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import joblib
from pathlib import Path
from datetime import datetime

from xgboost import XGBClassifier

try:
    from lightgbm import LGBMClassifier
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("⚠️ LightGBM not available. Install with: pip install lightgbm")

try:
    from catboost import CatBoostClassifier
    CATBOOST_AVAILABLE = True
except ImportError:
    CATBOOST_AVAILABLE = False
    print("⚠️ CatBoost not available. Install with: pip install catboost")


class EnsembleTrainer:
    """
    Train and manage ensemble of ML models
    """
    
    def __init__(
        self,
        use_xgboost: bool = True,
        use_random_forest: bool = True,
        use_lightgbm: bool = True,
        use_catboost: bool = True,
        random_state: int = 42
    ):
        """
        Initialize ensemble trainer
        
        Args:
            use_xgboost: Include XGBoost model
            use_random_forest: Include Random Forest model
            use_lightgbm: Include LightGBM model
            use_catboost: Include CatBoost model
            random_state: Random seed
        """
        self.use_xgboost = use_xgboost
        self.use_random_forest = use_random_forest
        self.use_lightgbm = use_lightgbm and LIGHTGBM_AVAILABLE
        self.use_catboost = use_catboost and CATBOOST_AVAILABLE
        self.random_state = random_state
        
        self.models = {}
        self.voting_ensemble = None
        self.stacking_ensemble = None
        self.performance = {}
    
    def create_base_models(self, tuned_params: Optional[Dict[str, Dict]] = None) -> Dict:
        """
        Create base models for ensemble
        
        Args:
            tuned_params: Optional dict of tuned parameters for each model
            
        Returns:
            Dict of model instances
        """
        models = {}
        
        if tuned_params is None:
            tuned_params = {}
        
        # XGBoost
        if self.use_xgboost:
            xgb_params = tuned_params.get('xgboost', {
                'n_estimators': 100,
                'max_depth': 5,
                'learning_rate': 0.1,
                'random_state': self.random_state,
                'eval_metric': 'logloss'
            })
            models['xgboost'] = XGBClassifier(**xgb_params)
        
        # Random Forest
        if self.use_random_forest:
            rf_params = tuned_params.get('random_forest', {
                'n_estimators': 100,
                'max_depth': 10,
                'random_state': self.random_state
            })
            models['random_forest'] = RandomForestClassifier(**rf_params)
        
        # LightGBM
        if self.use_lightgbm:
            lgbm_params = tuned_params.get('lightgbm', {
                'n_estimators': 100,
                'max_depth': 5,
                'learning_rate': 0.1,
                'random_state': self.random_state,
                'verbose': -1
            })
            models['lightgbm'] = LGBMClassifier(**lgbm_params)
        
        # CatBoost
        if self.use_catboost:
            cb_params = tuned_params.get('catboost', {
                'iterations': 100,
                'depth': 5,
                'learning_rate': 0.1,
                'random_state': self.random_state,
                'verbose': False
            })
            models['catboost'] = CatBoostClassifier(**cb_params)
        
        return models
    
    def train_individual_models(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        tuned_params: Optional[Dict[str, Dict]] = None
    ) -> Dict[str, Dict]:
        """
        Train individual models and evaluate performance
        
        Args:
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            tuned_params: Optional tuned parameters
            
        Returns:
            Dict of model performance metrics
        """
        print("\n🤖 Training Individual Models")
        print("=" * 60)
        
        self.models = self.create_base_models(tuned_params)
        performance = {}
        
        for name, model in self.models.items():
            print(f"\n📊 Training {name.upper()}...")
            
            # Train
            model.fit(X_train, y_train)
            
            # Predict
            y_pred_train = model.predict(X_train)
            y_pred_test = model.predict(X_test)
            y_proba_test = model.predict_proba(X_test)[:, 1]
            
            # Metrics
            train_acc = accuracy_score(y_train, y_pred_train)
            test_acc = accuracy_score(y_test, y_pred_test)
            precision = precision_score(y_test, y_pred_test)
            recall = recall_score(y_test, y_pred_test)
            f1 = f1_score(y_test, y_pred_test)
            
            performance[name] = {
                'train_accuracy': train_acc,
                'test_accuracy': test_acc,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'predictions': y_pred_test,
                'probabilities': y_proba_test
            }
            
            print(f"  Train Acc: {train_acc:.4f}")
            print(f"  Test Acc:  {test_acc:.4f}")
            print(f"  Precision: {precision:.4f}")
            print(f"  Recall:    {recall:.4f}")
            print(f"  F1 Score:  {f1:.4f}")
        
        self.performance = performance
        return performance
    
    def create_voting_ensemble(self, use_weights: bool = True) -> VotingClassifier:
        """
        Create voting classifier ensemble with optional performance-based weights
        
        Args:
            use_weights: Use performance-based weights instead of uniform
        
        Returns:
            VotingClassifier instance
        """
        if not self.models:
            raise ValueError("No models trained. Call train_individual_models first.")
        
        # Create list of (name, model) tuples
        estimators = [(name, model) for name, model in self.models.items()]
        
        # Calculate weights based on performance
        weights = None
        if use_weights and self.performance:
            # Weight = (accuracy - baseline) / (1 - baseline)
            # Baseline is random guess (0.5)
            baseline = 0.5
            weights = []
            for name, _ in estimators:
                if name in self.performance:
                    acc = self.performance[name]['test_accuracy']
                    weight = max(0.1, (acc - baseline) / (1 - baseline))  # Minimum weight of 0.1
                    weights.append(weight)
                else:
                    weights.append(1.0)
            
            print(f"  Weighted voting: {dict(zip([n for n, _ in estimators], weights))}")
        
        # Soft voting (uses predicted probabilities)
        voting = VotingClassifier(
            estimators=estimators,
            voting='soft',
            weights=weights
        )
        
        return voting
    
    def create_stacking_ensemble(
        self,
        meta_learner: Optional[Any] = None
    ) -> StackingClassifier:
        """
        Create stacking classifier ensemble
        
        Args:
            meta_learner: Optional meta-learner (default: LogisticRegression)
            
        Returns:
            StackingClassifier instance
        """
        if not self.models:
            raise ValueError("No models trained. Call train_individual_models first.")
        
        # Create list of (name, model) tuples
        estimators = [(name, model) for name, model in self.models.items()]
        
        # Default meta-learner
        if meta_learner is None:
            meta_learner = LogisticRegression(random_state=self.random_state)
        
        # Stacking with cross-validation
        stacking = StackingClassifier(
            estimators=estimators,
            final_estimator=meta_learner,
            cv=5
        )
        
        return stacking
    
    def train_ensembles(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        use_calibration: bool = True
    ) -> Dict[str, Dict]:
        """
        Train voting and stacking ensembles with optional probability calibration
        
        Args:
            X_train: Training features
            y_train: Training target
            X_test: Test features
            y_test: Test target
            use_calibration: Apply probability calibration
            
        Returns:
            Dict of ensemble performance metrics
        """
        print("\n🎯 Training Ensemble Models")
        print("=" * 60)
        
        ensemble_performance = {}
        
        # Voting Ensemble
        print("\n📊 Training Voting Ensemble...")
        self.voting_ensemble = self.create_voting_ensemble(use_weights=True)
        self.voting_ensemble.fit(X_train, y_train)
        
        # Apply calibration if requested
        if use_calibration:
            from sklearn.calibration import CalibratedClassifierCV
            print("  Calibrating probabilities...")
            self.voting_ensemble = CalibratedClassifierCV(
                self.voting_ensemble, 
                method='sigmoid', 
                cv=3
            )
            self.voting_ensemble.fit(X_train, y_train)
        
        y_pred_vote = self.voting_ensemble.predict(X_test)
        y_proba_vote = self.voting_ensemble.predict_proba(X_test)[:, 1]
        
        ensemble_performance['voting'] = {
            'test_accuracy': accuracy_score(y_test, y_pred_vote),
            'precision': precision_score(y_test, y_pred_vote),
            'recall': recall_score(y_test, y_pred_vote),
            'f1_score': f1_score(y_test, y_pred_vote),
            'predictions': y_pred_vote,
            'probabilities': y_proba_vote
        }
        
        print(f"  Test Acc:  {ensemble_performance['voting']['test_accuracy']:.4f}")
        print(f"  F1 Score:  {ensemble_performance['voting']['f1_score']:.4f}")
        
        # Stacking Ensemble
        print("\n📊 Training Stacking Ensemble...")
        self.stacking_ensemble = self.create_stacking_ensemble()
        self.stacking_ensemble.fit(X_train, y_train)
        
        # Apply calibration if requested
        if use_calibration:
            from sklearn.calibration import CalibratedClassifierCV
            print("  Calibrating probabilities...")
            self.stacking_ensemble = CalibratedClassifierCV(
                self.stacking_ensemble, 
                method='sigmoid', 
                cv=3
            )
            self.stacking_ensemble.fit(X_train, y_train)
        
        y_pred_stack = self.stacking_ensemble.predict(X_test)
        y_proba_stack = self.stacking_ensemble.predict_proba(X_test)[:, 1]
        
        ensemble_performance['stacking'] = {
            'test_accuracy': accuracy_score(y_test, y_pred_stack),
            'precision': precision_score(y_test, y_pred_stack),
            'recall': recall_score(y_test, y_pred_stack),
            'f1_score': f1_score(y_test, y_pred_stack),
            'predictions': y_pred_stack,
            'probabilities': y_proba_stack
        }
        
        print(f"  Test Acc:  {ensemble_performance['stacking']['test_accuracy']:.4f}")
        print(f"  F1 Score:  {ensemble_performance['stacking']['f1_score']:.4f}")
        
        return ensemble_performance
    
    def compare_models(self) -> pd.DataFrame:
        """
        Compare performance of all models
        
        Returns:
            DataFrame with comparison metrics
        """
        if not self.performance:
            raise ValueError("No models trained yet")
        
        # Combine individual and ensemble performance
        all_performance = {**self.performance}
        
        # Create comparison DataFrame
        comparison = []
        for name, metrics in all_performance.items():
            comparison.append({
                'Model': name,
                'Test Accuracy': metrics['test_accuracy'],
                'Precision': metrics['precision'],
                'Recall': metrics['recall'],
                'F1 Score': metrics['f1_score']
            })
        
        df = pd.DataFrame(comparison)
        df = df.sort_values('Test Accuracy', ascending=False)
        
        return df
    
    def get_best_model(self) -> Tuple[str, Any, float]:
        """
        Get the best performing model
        
        Returns:
            (model_name, model_instance, accuracy)
        """
        if not self.performance:
            raise ValueError("No models trained yet")
        
        # Find best model by test accuracy
        best_name = max(self.performance, key=lambda x: self.performance[x]['test_accuracy'])
        best_acc = self.performance[best_name]['test_accuracy']
        
        # Get model instance
        if best_name in self.models:
            best_model = self.models[best_name]
        elif best_name == 'voting':
            best_model = self.voting_ensemble
        elif best_name == 'stacking':
            best_model = self.stacking_ensemble
        else:
            best_model = None
        
        return best_name, best_model, best_acc
    
    def save_ensemble(
        self,
        symbol: str,
        interval: str,
        feature_names: List[str],
        output_dir: str = "ml/models"
    ):
        """
        Save all trained models
        
        Args:
            symbol: Crypto symbol
            interval: Timeframe
            feature_names: List of feature names
            output_dir: Output directory
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get best model
        best_name, best_model, best_acc = self.get_best_model()
        
        # Save ensemble data
        ensemble_data = {
            'models': self.models,
            'voting_ensemble': self.voting_ensemble,
            'stacking_ensemble': self.stacking_ensemble,
            'performance': self.performance,
            'best_model_name': best_name,
            'best_accuracy': best_acc,
            'feature_names': feature_names,
            'symbol': symbol,
            'interval': interval,
            'trained_at': timestamp
        }
        
        # Save ensemble
        ensemble_path = output_path / f'ensemble_{symbol}_{interval}_{timestamp}.pkl'
        joblib.dump(ensemble_data, ensemble_path)
        print(f"\n💾 Ensemble saved: {ensemble_path}")
        
        # Save as latest
        latest_path = output_path / f'ensemble_{symbol}_{interval}_latest.pkl'
        joblib.dump(ensemble_data, latest_path)
        print(f"💾 Latest ensemble: {latest_path}")
        
        # Also save best model separately
        best_model_data = {
            'model': best_model,
            'model_type': best_name,
            'feature_names': feature_names,
            'symbol': symbol,
            'interval': interval,
            'test_accuracy': best_acc,
            'trained_at': timestamp
        }
        
        best_path = output_path / f'best_{symbol}_{interval}_latest.pkl'
        joblib.dump(best_model_data, best_path)
        print(f"💾 Best model ({best_name}): {best_path}")


def load_ensemble(
    symbol: str,
    interval: str,
    model_dir: str = "ml/models"
) -> Optional[Dict]:
    """
    Load trained ensemble
    
    Args:
        symbol: Crypto symbol
        interval: Timeframe
        model_dir: Model directory
        
    Returns:
        Ensemble data dict or None
    """
    model_path = Path(model_dir)
    ensemble_file = model_path / f'ensemble_{symbol}_{interval}_latest.pkl'
    
    if ensemble_file.exists():
        try:
            ensemble_data = joblib.load(ensemble_file)
            print(f"✅ Loaded ensemble for {symbol} {interval}")
            print(f"   Best model: {ensemble_data['best_model_name']} "
                  f"(Accuracy: {ensemble_data['best_accuracy']:.4f})")
            return ensemble_data
        except Exception as e:
            print(f"❌ Error loading ensemble: {e}")
            return None
    else:
        print(f"⚠️ Ensemble not found: {ensemble_file}")
        return None


def predict_with_ensemble(
    ensemble_data: Dict,
    X: pd.DataFrame,
    return_individual: bool = False
) -> Dict:
    """
    Make predictions using ensemble
    
    Args:
        ensemble_data: Loaded ensemble data
        X: Features for prediction
        return_individual: Return individual model predictions
        
    Returns:
        Dict with predictions
    """
    # Get best model
    best_name = ensemble_data['best_model_name']
    
    if best_name == 'voting':
        best_model = ensemble_data['voting_ensemble']
    elif best_name == 'stacking':
        best_model = ensemble_data['stacking_ensemble']
    else:
        best_model = ensemble_data['models'][best_name]
    
    # Make prediction
    prediction = best_model.predict(X)[0]
    probability = best_model.predict_proba(X)[0][1]
    
    result = {
        'prediction': int(prediction),
        'probability': float(probability),
        'model_used': best_name
    }
    
    # Individual predictions if requested
    if return_individual:
        individual = {}
        for name, model in ensemble_data['models'].items():
            pred = model.predict(X)[0]
            prob = model.predict_proba(X)[0][1]
            individual[name] = {
                'prediction': int(pred),
                'probability': float(prob)
            }
        result['individual_predictions'] = individual
    
    return result
