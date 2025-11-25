import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report
import joblib
from datetime import datetime
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from indicators.signals import get_binance_data
from ml.features import create_features, create_target, select_features, prepare_data_for_training

def fetch_training_data(symbol="BTCUSDT", interval="1h", limit=1000):
    """Fetch historical data for training"""
    print(f"📥 Récupération des données pour {symbol}...")
    df = get_binance_data(symbol, interval, limit)
    
    if df.empty:
        raise ValueError("Impossible de récupérer les données")
    
    print(f"✅ {len(df)} périodes récupérées")
    return df

def train_model(symbol="BTCUSDT", interval="1h", test_size=0.2):
    """
    Train XGBoost model on historical data
    
    Args:
        symbol: Crypto symbol to train on
        interval: Timeframe
        test_size: Proportion of data for testing
        
    Returns:
        Trained model, metrics, feature importance
    """
    print(f"\n🤖 Entraînement du modèle pour {symbol}")
    print("=" * 50)
    
    # Fetch data
    df = fetch_training_data(symbol, interval, limit=1000)
    
    # Add indicators (same as in signals.py)
    import ta
    df['rsi'] = ta.momentum.rsi(df['close'], window=14)
    df['ema20'] = ta.trend.ema_indicator(df['close'], window=20)
    df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['macd'] = ta.trend.macd_diff(df['close'])
    
    # Prepare data
    print("\n📊 Préparation des features...")
    X, y, feature_names = prepare_data_for_training(df, horizon=1)
    
    print(f"Features créées: {len(feature_names)}")
    print(f"Échantillons: {len(X)}")
    print(f"Distribution cible: UP={y.sum()} ({y.mean()*100:.1f}%), DOWN={len(y)-y.sum()} ({(1-y.mean())*100:.1f}%)")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, shuffle=False  # Don't shuffle time series
    )
    
    print(f"\nTrain: {len(X_train)}, Test: {len(X_test)}")
    
    # Train model
    print("\n🔧 Entraînement XGBoost...")
    model = XGBClassifier(
        n_estimators=100,
        max_depth=5,
        learning_rate=0.1,
        random_state=42,
        eval_metric='logloss'
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    print("\n📈 Évaluation du modèle...")
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    train_acc = accuracy_score(y_train, y_pred_train)
    test_acc = accuracy_score(y_test, y_pred_test)
    
    print(f"\nAccuracy Train: {train_acc:.3f}")
    print(f"Accuracy Test: {test_acc:.3f}")
    
    print("\n📊 Métriques Test:")
    print(classification_report(y_test, y_pred_test, target_names=['DOWN', 'UP']))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🔝 Top 10 Features:")
    print(feature_importance.head(10).to_string(index=False))
    
    # Cross-validation
    print("\n🔄 Cross-validation (5-fold)...")
    cv_scores = cross_val_score(model, X, y, cv=5, scoring='accuracy')
    print(f"CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std():.3f})")
    
    # Save model
    model_dir = os.path.join(os.path.dirname(__file__), 'models')
    os.makedirs(model_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_path = os.path.join(model_dir, f'xgboost_{symbol}_{interval}_{timestamp}.pkl')
    
    # Save model and metadata
    model_data = {
        'model': model,
        'feature_names': feature_names,
        'symbol': symbol,
        'interval': interval,
        'train_accuracy': train_acc,
        'test_accuracy': test_acc,
        'cv_accuracy': cv_scores.mean(),
        'trained_at': timestamp
    }
    
    joblib.dump(model_data, model_path)
    print(f"\n💾 Modèle sauvegardé: {model_path}")
    
    # Also save as "latest" for easy loading
    latest_path = os.path.join(model_dir, f'xgboost_{symbol}_{interval}_latest.pkl')
    joblib.dump(model_data, latest_path)
    print(f"💾 Copie latest: {latest_path}")
    
    return model, feature_importance, {
        'train_accuracy': train_acc,
        'test_accuracy': test_acc,
        'cv_accuracy': cv_scores.mean()
    }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Train ML models for crypto trading')
    parser.add_argument('--symbol', type=str, default=None, help='Crypto symbol (e.g., BTCUSDT)')
    parser.add_argument('--interval', type=str, default='1h', help='Timeframe (e.g., 1h, 4h)')
    parser.add_argument('--tune', action='store_true', help='Enable hyperparameter tuning')
    parser.add_argument('--tuning-method', type=str, default='random', 
                       choices=['grid', 'random', 'optuna'], help='Tuning method')
    parser.add_argument('--ensemble', action='store_true', help='Train ensemble models')
    parser.add_argument('--sentiment', action='store_true', help='Include sentiment features')
    
    args = parser.parse_args()
    
    # Determine symbols to train
    if args.symbol:
        symbols = [args.symbol]
    else:
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    
    for symbol in symbols:
        try:
            print(f"\n{'='*60}")
            print(f"TRAINING: {symbol}")
            print(f"{'='*60}")
            
            # Fetch data
            df = fetch_training_data(symbol, args.interval, limit=1000)
            
            # Add indicators
            import ta
            df['rsi'] = ta.momentum.rsi(df['close'], window=14)
            df['ema20'] = ta.trend.ema_indicator(df['close'], window=20)
            df['ema50'] = ta.trend.ema_indicator(df['close'], window=50)
            df['macd'] = ta.trend.macd_diff(df['close'])
            
            # Add sentiment features if requested
            if args.sentiment:
                try:
                    from ml.sentiment_features import add_sentiment_features, get_crypto_name
                    from config import settings
                    
                    if settings.sentiment_enabled:
                        crypto_name = get_crypto_name(symbol)
                        df = add_sentiment_features(df, symbol, crypto_name=crypto_name)
                        print("✅ Sentiment features added")
                except Exception as e:
                    print(f"⚠️ Could not add sentiment features: {e}")
            
            # Prepare data
            print("\n📊 Preparing features...")
            X, y, feature_names = prepare_data_for_training(df, horizon=1)
            
            # Split data
            from sklearn.model_selection import train_test_split
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, shuffle=False
            )
            
            # Hyperparameter tuning
            tuned_params = None
            if args.tune:
                print(f"\n🔧 Starting hyperparameter tuning ({args.tuning_method})...")
                from ml.hyperparameter_tuning import HyperparameterTuner
                
                tuner = HyperparameterTuner(
                    model_type='xgboost',
                    tuning_method=args.tuning_method,
                    n_trials=50
                )
                
                best_model, best_params, results = tuner.tune(X_train, y_train)
                tuner.save_tuning_results(best_params, results, symbol, args.interval)
                
                tuned_params = {'xgboost': best_params}
                print(f"✅ Tuning complete. Best score: {results['best_score']:.4f}")
            
            # Ensemble training
            if args.ensemble:
                print("\n🎯 Training ensemble models...")
                from ml.ensemble import EnsembleTrainer
                
                ensemble_trainer = EnsembleTrainer(
                    use_xgboost=True,
                    use_random_forest=True,
                    use_lightgbm=True,
                    use_catboost=True
                )
                
                # Train individual models
                performance = ensemble_trainer.train_individual_models(
                    X_train, y_train, X_test, y_test, tuned_params
                )
                
                # Train ensembles
                ensemble_perf = ensemble_trainer.train_ensembles(
                    X_train, y_train, X_test, y_test
                )
                
                # Update performance with ensemble results
                performance.update(ensemble_perf)
                ensemble_trainer.performance = performance
                
                # Compare models
                print("\n📊 Model Comparison:")
                comparison = ensemble_trainer.compare_models()
                print(comparison.to_string(index=False))
                
                # Save ensemble
                ensemble_trainer.save_ensemble(symbol, args.interval, feature_names)
                
                best_name, best_model, best_acc = ensemble_trainer.get_best_model()
                print(f"\n✅ {symbol} - Best Model: {best_name} (Accuracy: {best_acc:.4f})")
                
            else:
                # Train single XGBoost model (original behavior)
                model, importance, metrics = train_model(symbol, interval=args.interval)
                print(f"\n✅ {symbol} - Accuracy: {metrics['test_accuracy']:.3f}")
            
        except Exception as e:
            print(f"\n❌ Error for {symbol}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\n" + "="*60)
    print("✅ Training complete!")
    print("="*60)
