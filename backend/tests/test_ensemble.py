"""
Unit tests for ensemble models
"""

import pytest
import pandas as pd
import numpy as np
from sklearn.datasets import make_classification
from ml.ensemble import EnsembleTrainer, load_ensemble, predict_with_ensemble


@pytest.fixture
def sample_data():
    """Create sample classification data"""
    X, y = make_classification(
        n_samples=200,
        n_features=10,
        n_informative=5,
        n_redundant=2,
        random_state=42
    )
    
    X = pd.DataFrame(X, columns=[f'feature_{i}' for i in range(10)])
    y = pd.Series(y)
    
    # Split into train/test
    split_idx = int(len(X) * 0.8)
    X_train = X.iloc[:split_idx]
    X_test = X.iloc[split_idx:]
    y_train = y.iloc[:split_idx]
    y_test = y.iloc[split_idx:]
    
    return X_train, X_test, y_train, y_test


def test_ensemble_trainer_initialization():
    """Test EnsembleTrainer initialization"""
    trainer = EnsembleTrainer()
    assert trainer.use_xgboost == True
    assert trainer.use_random_forest == True


def test_create_base_models():
    """Test base model creation"""
    trainer = EnsembleTrainer()
    models = trainer.create_base_models()
    
    assert 'xgboost' in models
    assert 'random_forest' in models


def test_train_individual_models(sample_data):
    """Test training individual models"""
    X_train, X_test, y_train, y_test = sample_data
    
    trainer = EnsembleTrainer(
        use_xgboost=True,
        use_random_forest=True,
        use_lightgbm=False,  # Skip for speed
        use_catboost=False   # Skip for speed
    )
    
    performance = trainer.train_individual_models(
        X_train, y_train, X_test, y_test
    )
    
    assert 'xgboost' in performance
    assert 'random_forest' in performance
    assert performance['xgboost']['test_accuracy'] > 0


def test_create_voting_ensemble(sample_data):
    """Test voting ensemble creation"""
    X_train, X_test, y_train, y_test = sample_data
    
    trainer = EnsembleTrainer(
        use_xgboost=True,
        use_random_forest=True,
        use_lightgbm=False,
        use_catboost=False
    )
    
    trainer.train_individual_models(X_train, y_train, X_test, y_test)
    voting = trainer.create_voting_ensemble()
    
    assert voting is not None
    assert len(voting.estimators) == 2  # XGBoost + Random Forest


def test_create_stacking_ensemble(sample_data):
    """Test stacking ensemble creation"""
    X_train, X_test, y_train, y_test = sample_data
    
    trainer = EnsembleTrainer(
        use_xgboost=True,
        use_random_forest=True,
        use_lightgbm=False,
        use_catboost=False
    )
    
    trainer.train_individual_models(X_train, y_train, X_test, y_test)
    stacking = trainer.create_stacking_ensemble()
    
    assert stacking is not None
    assert len(stacking.estimators) == 2


def test_train_ensembles(sample_data):
    """Test ensemble training"""
    X_train, X_test, y_train, y_test = sample_data
    
    trainer = EnsembleTrainer(
        use_xgboost=True,
        use_random_forest=True,
        use_lightgbm=False,
        use_catboost=False
    )
    
    trainer.train_individual_models(X_train, y_train, X_test, y_test)
    ensemble_perf = trainer.train_ensembles(X_train, y_train, X_test, y_test)
    
    assert 'voting' in ensemble_perf
    assert 'stacking' in ensemble_perf
    assert ensemble_perf['voting']['test_accuracy'] > 0


def test_compare_models(sample_data):
    """Test model comparison"""
    X_train, X_test, y_train, y_test = sample_data
    
    trainer = EnsembleTrainer(
        use_xgboost=True,
        use_random_forest=True,
        use_lightgbm=False,
        use_catboost=False
    )
    
    trainer.train_individual_models(X_train, y_train, X_test, y_test)
    comparison = trainer.compare_models()
    
    assert isinstance(comparison, pd.DataFrame)
    assert 'Model' in comparison.columns
    assert 'Test Accuracy' in comparison.columns
    assert len(comparison) >= 2


def test_get_best_model(sample_data):
    """Test getting best model"""
    X_train, X_test, y_train, y_test = sample_data
    
    trainer = EnsembleTrainer(
        use_xgboost=True,
        use_random_forest=True,
        use_lightgbm=False,
        use_catboost=False
    )
    
    trainer.train_individual_models(X_train, y_train, X_test, y_test)
    best_name, best_model, best_acc = trainer.get_best_model()
    
    assert best_name in ['xgboost', 'random_forest']
    assert best_model is not None
    assert best_acc > 0


def test_predict_with_ensemble_function(sample_data):
    """Test prediction with ensemble"""
    X_train, X_test, y_train, y_test = sample_data
    
    trainer = EnsembleTrainer(
        use_xgboost=True,
        use_random_forest=True,
        use_lightgbm=False,
        use_catboost=False
    )
    
    trainer.train_individual_models(X_train, y_train, X_test, y_test)
    ensemble_perf = trainer.train_ensembles(X_train, y_train, X_test, y_test)
    trainer.performance.update(ensemble_perf)
    
    # Create ensemble data structure
    best_name, best_model, best_acc = trainer.get_best_model()
    ensemble_data = {
        'models': trainer.models,
        'voting_ensemble': trainer.voting_ensemble,
        'stacking_ensemble': trainer.stacking_ensemble,
        'best_model_name': best_name,
        'best_accuracy': best_acc
    }
    
    # Make prediction
    X_sample = X_test.iloc[[0]]
    result = predict_with_ensemble(ensemble_data, X_sample, return_individual=True)
    
    assert 'prediction' in result
    assert 'probability' in result
    assert 'model_used' in result
    assert 'individual_predictions' in result
