import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime

def backtest_strategy(
    signals_df: pd.DataFrame,
    initial_capital: float = 10000,
    position_size: float = 0.1,  # 10% of capital per trade
    fee: float = 0.001  # 0.1% trading fee
) -> Dict:
    """
    Backtest a trading strategy based on historical signals
    
    Args:
        signals_df: DataFrame with columns: timestamp, signal, price, confidence
        initial_capital: Starting capital in USD
        position_size: Fraction of capital to use per trade (0-1)
        fee: Trading fee as decimal (0.001 = 0.1%)
        
    Returns:
        Dict with backtest results: profit, win_rate, trades, etc.
    """
    capital = initial_capital
    position = 0  # Current position (0 = no position, >0 = long)
    entry_price = 0
    trades = []
    
    for idx, row in signals_df.iterrows():
        signal = row['signal']
        price = row['price']
        confidence = row.get('confidence', 0.5)
        
        # Entry logic
        if position == 0 and signal in ['BUY', 'BUY (Trend)']:
            # Open long position
            trade_amount = capital * position_size
            position = (trade_amount * (1 - fee)) / price
            entry_price = price
            capital -= trade_amount
            
            trades.append({
                'type': 'BUY',
                'price': price,
                'amount': position,
                'timestamp': row.get('timestamp', idx),
                'confidence': confidence
            })
            
        # Exit logic
        elif position > 0 and signal in ['SELL', 'SELL (Trend)']:
            # Close long position
            exit_value = position * price * (1 - fee)
            profit = exit_value - (entry_price * position)
            capital += exit_value
            
            trades.append({
                'type': 'SELL',
                'price': price,
                'amount': position,
                'profit': profit,
                'timestamp': row.get('timestamp', idx),
                'confidence': confidence
            })
            
            position = 0
            entry_price = 0
    
    # Close any open position at last price
    if position > 0:
        last_price = signals_df.iloc[-1]['price']
        exit_value = position * last_price * (1 - fee)
        profit = exit_value - (entry_price * position)
        capital += exit_value
        
        trades.append({
            'type': 'SELL (FORCED)',
            'price': last_price,
            'amount': position,
            'profit': profit,
            'timestamp': signals_df.iloc[-1].get('timestamp', len(signals_df)-1)
        })
    
    # Calculate metrics
    total_trades = len([t for t in trades if t['type'] in ['SELL', 'SELL (FORCED)']])
    winning_trades = len([t for t in trades if t.get('profit', 0) > 0])
    losing_trades = len([t for t in trades if t.get('profit', 0) < 0])
    
    total_profit = capital - initial_capital
    roi = (total_profit / initial_capital) * 100
    win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
    
    avg_win = np.mean([t['profit'] for t in trades if t.get('profit', 0) > 0]) if winning_trades > 0 else 0
    avg_loss = np.mean([t['profit'] for t in trades if t.get('profit', 0) < 0]) if losing_trades > 0 else 0
    
    return {
        'initial_capital': initial_capital,
        'final_capital': capital,
        'total_profit': total_profit,
        'roi': roi,
        'total_trades': total_trades,
        'winning_trades': winning_trades,
        'losing_trades': losing_trades,
        'win_rate': win_rate,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else 0,
        'trades': trades
    }

def simulate_trading(symbol: str = "BTCUSDT", days: int = 30) -> Dict:
    """
    Simulate trading for a given symbol over a period
    
    Args:
        symbol: Crypto symbol
        days: Number of days to simulate
        
    Returns:
        Backtest results
    """
    from indicators.signals import get_binance_data, generate_signal
    
    # Fetch historical data
    limit = days * 24  # Assuming 1h timeframe
    df = get_binance_data(symbol, "1h", limit=limit)
    
    if df.empty:
        return {"error": "Could not fetch data"}
    
    # Generate signals for each candle
    signals_data = []
    for i in range(len(df) - 50):  # Need history for indicators
        subset = df.iloc[:i+50]
        try:
            signal_result = generate_signal(symbol, "1h")
            signals_data.append({
                'timestamp': df.iloc[i+49]['timestamp'],
                'signal': signal_result.get('signal', 'NEUTRE'),
                'price': df.iloc[i+49]['close'],
                'confidence': signal_result.get('confidence', 0.5)
            })
        except:
            continue
    
    signals_df = pd.DataFrame(signals_data)
    
    # Run backtest
    results = backtest_strategy(signals_df)
    results['symbol'] = symbol
    results['period_days'] = days
    
    return results
