"""
Risk Management Module

Provides portfolio-level risk management:
- Portfolio risk calculation
- Maximum drawdown monitoring
- Volatility-adjusted leverage
- Position correlation analysis
- Risk limits enforcement
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Position:
    """Represents a trading position"""
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    leverage: float
    stop_loss: Optional[float] = None
    
    @property
    def value(self) -> float:
        """Current position value"""
        return self.quantity * self.current_price
    
    @property
    def pnl(self) -> float:
        """Profit/Loss"""
        return (self.current_price - self.entry_price) * self.quantity
    
    @property
    def pnl_percent(self) -> float:
        """Profit/Loss percentage"""
        return ((self.current_price - self.entry_price) / self.entry_price) * 100
    
    @property
    def leveraged_pnl(self) -> float:
        """Leveraged profit/loss"""
        return self.pnl * self.leverage


class RiskManager:
    """
    Portfolio risk management system
    """
    
    def __init__(
        self,
        max_portfolio_risk: float = 0.10,  # 10% max portfolio risk
        max_drawdown: float = 0.20,  # 20% max drawdown
        max_correlation: float = 0.7,  # Max correlation between positions
        max_leverage_portfolio: float = 3.0  # Max average portfolio leverage
    ):
        """
        Initialize risk manager
        
        Args:
            max_portfolio_risk: Maximum portfolio risk as fraction
            max_drawdown: Maximum allowed drawdown
            max_correlation: Maximum correlation between positions
            max_leverage_portfolio: Maximum average leverage across portfolio
        """
        self.max_portfolio_risk = max_portfolio_risk
        self.max_drawdown = max_drawdown
        self.max_correlation = max_correlation
        self.max_leverage_portfolio = max_leverage_portfolio
    
    def calculate_portfolio_risk(
        self,
        positions: List[Position],
        account_balance: float
    ) -> Dict[str, float]:
        """
        Calculate total portfolio risk
        
        Args:
            positions: List of current positions
            account_balance: Total account balance
            
        Returns:
            Dict with risk metrics
        """
        if not positions:
            return {
                'total_risk': 0.0,
                'total_exposure': 0.0,
                'average_leverage': 1.0,
                'position_count': 0
            }
        
        # Calculate total exposure
        total_exposure = sum(pos.value for pos in positions)
        
        # Calculate total risk (sum of potential losses to stop-loss)
        total_risk = 0.0
        for pos in positions:
            if pos.stop_loss:
                risk = abs(pos.entry_price - pos.stop_loss) * pos.quantity
                total_risk += risk
        
        # Average leverage
        avg_leverage = np.mean([pos.leverage for pos in positions])
        
        # Risk as percentage of balance
        risk_percent = total_risk / account_balance if account_balance > 0 else 0
        exposure_percent = total_exposure / account_balance if account_balance > 0 else 0
        
        return {
            'total_risk': round(total_risk, 2),
            'total_exposure': round(total_exposure, 2),
            'risk_percent': round(risk_percent, 4),
            'exposure_percent': round(exposure_percent, 4),
            'average_leverage': round(avg_leverage, 2),
            'position_count': len(positions)
        }
    
    def calculate_drawdown(
        self,
        equity_curve: List[float]
    ) -> Dict[str, float]:
        """
        Calculate drawdown metrics
        
        Args:
            equity_curve: List of account balance over time
            
        Returns:
            Dict with drawdown metrics
        """
        if not equity_curve or len(equity_curve) < 2:
            return {
                'current_drawdown': 0.0,
                'max_drawdown': 0.0,
                'peak_value': equity_curve[0] if equity_curve else 0
            }
        
        equity = np.array(equity_curve)
        
        # Calculate running maximum
        running_max = np.maximum.accumulate(equity)
        
        # Calculate drawdown
        drawdown = (equity - running_max) / running_max
        
        # Current and maximum drawdown
        current_dd = drawdown[-1]
        max_dd = drawdown.min()
        
        return {
            'current_drawdown': round(float(current_dd), 4),
            'max_drawdown': round(float(max_dd), 4),
            'peak_value': round(float(running_max[-1]), 2),
            'current_value': round(float(equity[-1]), 2)
        }
    
    def check_risk_limits(
        self,
        positions: List[Position],
        account_balance: float,
        equity_curve: Optional[List[float]] = None
    ) -> Dict[str, any]:
        """
        Check if portfolio is within risk limits
        
        Args:
            positions: Current positions
            account_balance: Account balance
            equity_curve: Optional equity curve for drawdown
            
        Returns:
            Dict with limit checks and warnings
        """
        warnings = []
        
        # Portfolio risk check
        portfolio_risk = self.calculate_portfolio_risk(positions, account_balance)
        
        if portfolio_risk['risk_percent'] > self.max_portfolio_risk:
            warnings.append(
                f"Portfolio risk ({portfolio_risk['risk_percent']:.1%}) exceeds "
                f"maximum ({self.max_portfolio_risk:.1%})"
            )
        
        if portfolio_risk['average_leverage'] > self.max_leverage_portfolio:
            warnings.append(
                f"Average leverage ({portfolio_risk['average_leverage']:.2f}x) exceeds "
                f"maximum ({self.max_leverage_portfolio:.2f}x)"
            )
        
        # Drawdown check
        drawdown_info = {}
        if equity_curve:
            drawdown_info = self.calculate_drawdown(equity_curve)
            if abs(drawdown_info['current_drawdown']) > self.max_drawdown:
                warnings.append(
                    f"Current drawdown ({drawdown_info['current_drawdown']:.1%}) exceeds "
                    f"maximum ({self.max_drawdown:.1%})"
                )
        
        return {
            'within_limits': len(warnings) == 0,
            'warnings': warnings,
            'portfolio_risk': portfolio_risk,
            'drawdown': drawdown_info
        }
    
    def adjust_leverage_for_volatility(
        self,
        base_leverage: float,
        current_volatility: float,
        avg_volatility: float = 0.02
    ) -> float:
        """
        Adjust leverage based on current volatility
        
        Higher volatility = lower leverage
        
        Args:
            base_leverage: Recommended leverage
            current_volatility: Current market volatility
            avg_volatility: Average/normal volatility
            
        Returns:
            Adjusted leverage
        """
        # Volatility ratio
        vol_ratio = current_volatility / avg_volatility
        
        # Reduce leverage if volatility is high
        if vol_ratio > 1.5:  # 50% above average
            adjustment = 0.6  # Reduce to 60%
        elif vol_ratio > 1.2:  # 20% above average
            adjustment = 0.8  # Reduce to 80%
        elif vol_ratio < 0.8:  # 20% below average
            adjustment = 1.1  # Increase to 110%
        else:
            adjustment = 1.0  # No change
        
        adjusted = base_leverage * adjustment
        return round(adjusted, 2)
    
    def calculate_position_correlation(
        self,
        price_data: Dict[str, pd.Series]
    ) -> pd.DataFrame:
        """
        Calculate correlation between positions
        
        Args:
            price_data: Dict mapping symbol to price series
            
        Returns:
            Correlation matrix
        """
        if len(price_data) < 2:
            return pd.DataFrame()
        
        # Create DataFrame from price series
        df = pd.DataFrame(price_data)
        
        # Calculate returns
        returns = df.pct_change().dropna()
        
        # Calculate correlation
        correlation = returns.corr()
        
        return correlation
    
    def check_correlation_risk(
        self,
        new_symbol: str,
        existing_symbols: List[str],
        price_data: Dict[str, pd.Series]
    ) -> Dict[str, any]:
        """
        Check if adding a new position would create correlation risk
        
        Args:
            new_symbol: Symbol to add
            existing_symbols: Existing position symbols
            price_data: Price data for all symbols
            
        Returns:
            Dict with correlation analysis
        """
        if not existing_symbols:
            return {
                'safe_to_add': True,
                'max_correlation': 0.0,
                'correlations': {}
            }
        
        # Calculate correlation matrix
        all_symbols = existing_symbols + [new_symbol]
        relevant_data = {s: price_data[s] for s in all_symbols if s in price_data}
        
        if len(relevant_data) < 2:
            return {
                'safe_to_add': True,
                'max_correlation': 0.0,
                'correlations': {}
            }
        
        corr_matrix = self.calculate_position_correlation(relevant_data)
        
        # Get correlations with new symbol
        if new_symbol in corr_matrix.columns:
            new_correlations = corr_matrix[new_symbol].drop(new_symbol).to_dict()
            max_corr = max(abs(v) for v in new_correlations.values()) if new_correlations else 0
        else:
            new_correlations = {}
            max_corr = 0
        
        safe_to_add = max_corr < self.max_correlation
        
        return {
            'safe_to_add': safe_to_add,
            'max_correlation': round(max_corr, 3),
            'correlations': {k: round(v, 3) for k, v in new_correlations.items()},
            'warning': None if safe_to_add else 
                f"High correlation ({max_corr:.1%}) with existing positions"
        }
    
    def get_recommended_position_size(
        self,
        account_balance: float,
        current_positions: List[Position],
        new_position_risk: float
    ) -> Optional[float]:
        """
        Get recommended position size considering portfolio risk
        
        Args:
            account_balance: Account balance
            current_positions: Existing positions
            new_position_risk: Risk of new position
            
        Returns:
            Recommended position size or None if too risky
        """
        # Calculate current portfolio risk
        portfolio_risk = self.calculate_portfolio_risk(current_positions, account_balance)
        current_risk = portfolio_risk['total_risk']
        
        # Available risk budget
        max_total_risk = account_balance * self.max_portfolio_risk
        available_risk = max_total_risk - current_risk
        
        if available_risk <= 0:
            return None  # No risk budget available
        
        # Recommended size based on available risk
        if new_position_risk > available_risk:
            # Scale down the position
            scale_factor = available_risk / new_position_risk
            return scale_factor
        else:
            return 1.0  # Full position is acceptable
