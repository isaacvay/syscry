"""
Test API with ensemble predictions
"""
import requests
import json
import sys

# Fix UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

print("Testing Ensemble Predictions via API")
print("=" * 60)

# Test signal endpoint
url = "http://localhost:8000/get-signal"
data = {
    "symbol": "BTCUSDT",
    "timeframe": "1h"
}

print(f"\nTesting: POST {url}")
print(f"Payload: {json.dumps(data, indent=2)}")

try:
    response = requests.post(url, json=data, timeout=30)
    print(f"\nStatus: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("\nResponse:")
        print(json.dumps(result, indent=2))
        
        print("\n" + "=" * 60)
        print("Signal Summary:")
        print(f"  Symbol: {result.get('symbol')}")
        print(f"  Signal: {result.get('signal')}")
        print(f"  Confidence: {result.get('confidence')}")
        print(f"  Price: ${result.get('price'):,.2f}")
        print(f"  RSI: {result.get('indicators', {}).get('rsi')}")
        print("=" * 60)
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")
