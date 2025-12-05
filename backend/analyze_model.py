import joblib
from pathlib import Path
import pandas as pd
from config import settings

# Load the latest ensemble model for each symbol
model_dir = Path('ml/models')
symbols = settings.default_cryptos

print(f"\n{'='*80}")
print(f"GLOBAL MODEL PERFORMANCE SUMMARY")
print(f"{'='*80}\n")

summary_data = []

for symbol in symbols:
    latest = model_dir / f'ensemble_{symbol}_1h_latest.pkl'
    
    if not latest.exists():
        print(f"⚠️ No model found for {symbol}")
        continue
        
    try:
        data = joblib.load(latest)
        best_model = data['best_model_name']
        best_acc = data['best_accuracy']
        
        # Get stacking accuracy if available, otherwise best
        stacking_acc = 0
        if 'stacking' in data['performance']:
            stacking_acc = data['performance']['stacking']['test_accuracy']
            
        summary_data.append({
            'Symbol': symbol,
            'Best Model': best_model,
            'Best Accuracy': f"{best_acc:.4f}",
            'Stacking Acc': f"{stacking_acc:.4f}" if stacking_acc else "N/A"
        })
        
    except Exception as e:
        print(f"❌ Error loading {symbol}: {e}")

# Display summary table
if summary_data:
    df = pd.DataFrame(summary_data)
    print(df.to_string(index=False))
else:
    print("No models loaded successfully.")

print(f"\n{'='*80}")

