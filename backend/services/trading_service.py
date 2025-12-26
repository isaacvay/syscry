"""
Background Trading Service
Runs in the background to execute trades for active sessions even when browser is closed.
"""
import asyncio
import threading
from datetime import datetime
from typing import List, Dict, Optional
import uuid

from logger import logger

# Will be initialized after database is ready
_trading_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


class TradingService:
    """Service that manages background trading for all active sessions"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 30  # seconds
    
    def start(self):
        """Start the background trading service"""
        global _trading_thread, _stop_event
        
        if self.is_running:
            logger.warning("Trading service already running")
            return
        
        _stop_event.clear()
        _trading_thread = threading.Thread(target=self._run_loop, daemon=True)
        _trading_thread.start()
        self.is_running = True
        logger.info("🚀 Background trading service started")
    
    def stop(self):
        """Stop the background trading service"""
        global _stop_event
        _stop_event.set()
        self.is_running = False
        logger.info("🛑 Background trading service stopped")
    
    def _run_loop(self):
        """Main loop that checks and executes trades"""
        while not _stop_event.is_set():
            try:
                self._process_active_sessions()
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
            
            # Wait for next iteration
            _stop_event.wait(self.check_interval)
    
    def _process_active_sessions(self):
        """Process all active sessions with auto_trade enabled"""
        from database import SessionLocal, TradingSession, SessionPosition, SessionTrade
        
        db = SessionLocal()
        try:
            # Get all active sessions with auto_trade enabled
            sessions = db.query(TradingSession).filter(
                TradingSession.is_active == 1,
                TradingSession.auto_trade == 1
            ).all()
            
            if not sessions:
                return
            
            logger.debug(f"Processing {len(sessions)} active trading sessions")
            
            for session in sessions:
                try:
                    self._process_session(db, session)
                except Exception as e:
                    logger.error(f"Error processing session {session.id}: {e}")
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error in _process_active_sessions: {e}")
        finally:
            db.close()
    
    def _process_session(self, db, session):
        """Process a single trading session"""
        from database import SessionPosition, SessionTrade
        from services.signal_service import generate_signal_service
        
        symbols = session.symbols.split(",")
        positions = db.query(SessionPosition).filter(
            SessionPosition.session_id == session.id
        ).all()
        
        # Fetch signals for each symbol
        for symbol in symbols:
            try:
                signal_data = generate_signal_service(symbol.strip(), "1h")
                
                if "error" in signal_data:
                    continue
                
                current_price = signal_data.get("current_price", 0)
                signal = signal_data.get("signal", "NEUTRAL")
                confidence = signal_data.get("confidence", 0)
                
                # Find existing position
                position = next((p for p in positions if p.symbol == symbol.strip()), None)
                
                # Update position price if exists
                if position:
                    position.current_price = current_price
                    position.pnl = (current_price - position.average_price) * position.quantity
                    
                    # Update trailing stop if enabled
                    if session.strategy_trailing_stop and position.pnl > 0:
                        trailing_stop_price = current_price * (1 - session.strategy_stop_loss)
                        if not position.trailing_stop_price or trailing_stop_price > position.trailing_stop_price:
                            position.trailing_stop_price = trailing_stop_price
                    
                    # Check stop-loss
                    effective_stop = position.trailing_stop_price or position.stop_loss
                    if current_price <= effective_stop:
                        self._execute_sell(db, session, position, current_price, 1.0, "STOP_LOSS")
                        logger.info(f"🛑 Stop-loss triggered for {symbol} in session {session.name}")
                        continue
                    
                    # Check take-profit
                    if current_price >= position.take_profit:
                        self._execute_sell(db, session, position, current_price, 1.0, "TAKE_PROFIT")
                        logger.info(f"🎯 Take-profit reached for {symbol} in session {session.name}")
                        continue
                    
                    # Check for SELL signal
                    if signal == "SELL" and confidence >= 0.6:
                        self._execute_sell(db, session, position, current_price, confidence, "SELL")
                        logger.info(f"📉 Sell signal executed for {symbol} in session {session.name}")
                
                else:
                    # No position - check for BUY signal
                    if signal == "BUY" and confidence >= 0.6:
                        # Check max positions
                        if len(positions) < session.strategy_max_positions:
                            self._execute_buy(db, session, symbol.strip(), current_price, confidence)
                            logger.info(f"📈 Buy signal executed for {symbol} in session {session.name}")
                
            except Exception as e:
                logger.error(f"Error processing signal for {symbol}: {e}")
    
    def _execute_buy(self, db, session, symbol: str, price: float, confidence: float):
        """Execute a BUY trade"""
        from database import SessionPosition, SessionTrade
        
        risk_amount = session.current_balance * session.strategy_risk_per_trade
        quantity = risk_amount / price
        cost = quantity * price
        
        if cost > session.current_balance:
            return
        
        # Calculate stop-loss and take-profit
        stop_loss = price * (1 - session.strategy_stop_loss)
        take_profit = price * (1 + session.strategy_take_profit)
        
        # Deduct from balance
        session.current_balance -= cost
        
        # Create position
        position = SessionPosition(
            session_id=session.id,
            symbol=symbol,
            quantity=quantity,
            average_price=price,
            current_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            pnl=0.0
        )
        db.add(position)
        
        # Record trade
        trade = SessionTrade(
            session_id=session.id,
            symbol=symbol,
            trade_type="BUY",
            price=price,
            quantity=quantity,
            confidence=confidence,
            signal_reason="BUY",
            pnl=0.0
        )
        db.add(trade)
    
    def _execute_sell(self, db, session, position, price: float, confidence: float, reason: str):
        """Execute a SELL trade"""
        from database import SessionTrade
        
        revenue = position.quantity * price
        cost = position.average_price * position.quantity
        pnl = revenue - cost
        
        # Add to balance
        session.current_balance += revenue
        
        # Update stats
        session.total_trades += 1
        if pnl > 0:
            session.winning_trades += 1
        else:
            session.losing_trades += 1
        
        # Record trade
        trade = SessionTrade(
            session_id=session.id,
            symbol=position.symbol,
            trade_type="SELL",
            price=price,
            quantity=position.quantity,
            confidence=confidence,
            signal_reason=reason,
            pnl=pnl
        )
        db.add(trade)
        
        # Delete position
        db.delete(position)


# ============================================
# Session Management Functions
# ============================================

def create_session(
    name: str = "New Session",
    strategy_name: str = "Balanced",
    initial_balance: float = 10000.0,
    symbols: List[str] = None,
    strategy_config: Dict = None
) -> Dict:
    """Create a new trading session"""
    from database import SessionLocal, TradingSession
    
    if symbols is None:
        symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    
    if strategy_config is None:
        strategy_config = {
            "risk_per_trade": 0.02,
            "stop_loss": 0.03,
            "take_profit": 0.06,
            "max_positions": 5,
            "trailing_stop": True
        }
    
    session_id = str(uuid.uuid4())
    
    db = SessionLocal()
    try:
        session = TradingSession(
            id=session_id,
            name=name,
            strategy_name=strategy_name,
            strategy_risk_per_trade=strategy_config.get("risk_per_trade", 0.02),
            strategy_stop_loss=strategy_config.get("stop_loss", 0.03),
            strategy_take_profit=strategy_config.get("take_profit", 0.06),
            strategy_max_positions=strategy_config.get("max_positions", 5),
            strategy_trailing_stop=1 if strategy_config.get("trailing_stop", True) else 0,
            symbols=",".join(symbols),
            initial_balance=initial_balance,
            current_balance=initial_balance,
            is_active=0,
            auto_trade=0
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
        logger.info(f"Created trading session: {name} (ID: {session_id})")
        
        return session_to_dict(session)
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating session: {e}")
        raise
    finally:
        db.close()


def get_session(session_id: str) -> Optional[Dict]:
    """Get a trading session by ID"""
    from database import SessionLocal, TradingSession, SessionPosition, SessionTrade
    
    db = SessionLocal()
    try:
        session = db.query(TradingSession).filter(TradingSession.id == session_id).first()
        if not session:
            return None
        
        positions = db.query(SessionPosition).filter(SessionPosition.session_id == session_id).all()
        trades = db.query(SessionTrade).filter(SessionTrade.session_id == session_id).order_by(SessionTrade.timestamp.desc()).limit(50).all()
        
        result = session_to_dict(session)
        result["positions"] = [position_to_dict(p) for p in positions]
        result["trades"] = [trade_to_dict(t) for t in trades]
        
        return result
    finally:
        db.close()


def get_all_sessions() -> List[Dict]:
    """Get all trading sessions"""
    from database import SessionLocal, TradingSession, SessionPosition
    
    db = SessionLocal()
    try:
        sessions = db.query(TradingSession).order_by(TradingSession.created_at.desc()).all()
        result = []
        
        for session in sessions:
            positions = db.query(SessionPosition).filter(SessionPosition.session_id == session.id).all()
            total_value = session.current_balance + sum(p.quantity * p.current_price for p in positions)
            
            session_dict = session_to_dict(session)
            session_dict["total_value"] = total_value
            session_dict["position_count"] = len(positions)
            result.append(session_dict)
        
        return result
    finally:
        db.close()


def update_session(session_id: str, updates: Dict) -> Optional[Dict]:
    """Update a trading session"""
    from database import SessionLocal, TradingSession
    
    db = SessionLocal()
    try:
        session = db.query(TradingSession).filter(TradingSession.id == session_id).first()
        if not session:
            return None
        
        # Update allowed fields
        allowed_fields = [
            "name", "is_active", "auto_trade", "strategy_name",
            "strategy_risk_per_trade", "strategy_stop_loss", "strategy_take_profit",
            "strategy_max_positions", "strategy_trailing_stop", "symbols"
        ]
        
        for field in allowed_fields:
            if field in updates:
                value = updates[field]
                # Convert booleans to integers for SQLite
                if field in ["is_active", "auto_trade", "strategy_trailing_stop"]:
                    value = 1 if value else 0
                setattr(session, field, value)
        
        session.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(session)
        
        logger.info(f"Updated session {session_id}: {updates}")
        
        return session_to_dict(session)
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating session: {e}")
        raise
    finally:
        db.close()


def delete_session(session_id: str) -> bool:
    """Delete a trading session and all related data"""
    from database import SessionLocal, TradingSession, SessionPosition, SessionTrade
    
    db = SessionLocal()
    try:
        # Delete related records first
        db.query(SessionPosition).filter(SessionPosition.session_id == session_id).delete()
        db.query(SessionTrade).filter(SessionTrade.session_id == session_id).delete()
        
        # Delete session
        result = db.query(TradingSession).filter(TradingSession.id == session_id).delete()
        db.commit()
        
        if result:
            logger.info(f"Deleted session {session_id}")
        
        return result > 0
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting session: {e}")
        raise
    finally:
        db.close()


# ============================================
# Helper Functions
# ============================================

def session_to_dict(session) -> Dict:
    """Convert TradingSession to dictionary"""
    return {
        "id": session.id,
        "name": session.name,
        "strategy": {
            "name": session.strategy_name,
            "riskPerTrade": session.strategy_risk_per_trade,
            "stopLoss": session.strategy_stop_loss,
            "takeProfit": session.strategy_take_profit,
            "maxPositions": session.strategy_max_positions,
            "trailingStop": bool(session.strategy_trailing_stop)
        },
        "symbols": session.symbols.split(","),
        "initialBalance": session.initial_balance,
        "currentBalance": session.current_balance,
        "isActive": bool(session.is_active),
        "autoTrade": bool(session.auto_trade),
        "stats": {
            "totalTrades": session.total_trades,
            "winningTrades": session.winning_trades,
            "losingTrades": session.losing_trades,
            "winRate": (session.winning_trades / session.total_trades * 100) if session.total_trades > 0 else 0
        },
        "createdAt": session.created_at.isoformat() + "Z" if session.created_at else None,
        "updatedAt": session.updated_at.isoformat() + "Z" if session.updated_at else None
    }


def position_to_dict(position) -> Dict:
    """Convert SessionPosition to dictionary"""
    return {
        "id": position.id,
        "symbol": position.symbol,
        "quantity": position.quantity,
        "averagePrice": position.average_price,
        "currentPrice": position.current_price,
        "stopLoss": position.stop_loss,
        "takeProfit": position.take_profit,
        "trailingStopPrice": position.trailing_stop_price,
        "pnl": position.pnl,
        "createdAt": position.created_at.isoformat() + "Z" if position.created_at else None
    }


def trade_to_dict(trade) -> Dict:
    """Convert SessionTrade to dictionary"""
    return {
        "id": trade.id,
        "symbol": trade.symbol,
        "type": trade.trade_type,
        "price": trade.price,
        "quantity": trade.quantity,
        "confidence": trade.confidence,
        "signalReason": trade.signal_reason,
        "pnl": trade.pnl,
        "timestamp": trade.timestamp.isoformat() + "Z" if trade.timestamp else None
    }


# Global instance
trading_service = TradingService()
