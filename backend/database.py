from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, OperationalError
from datetime import datetime
from config import settings
from logger import logger

# Import constants
try:
    from constants import DB_POOL_SIZE, DB_MAX_OVERFLOW, DB_POOL_PRE_PING
    from exceptions import DatabaseError, DatabaseConnectionError, DuplicateSignalError
except ImportError:
    DB_POOL_SIZE = 10
    DB_MAX_OVERFLOW = 20
    DB_POOL_PRE_PING = True
    
    class DatabaseError(Exception): pass
    class DatabaseConnectionError(Exception): pass
    class DuplicateSignalError(Exception): pass

Base = declarative_base()

class Signal(Base):
    __tablename__ = "signals"
    __table_args__ = (
        # Composite index for common queries (symbol + timestamp)
        # This speeds up queries like "get recent signals for BTC"
        {'extend_existing': True}
    )
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)  # Individual index for symbol-only queries
    timeframe = Column(String)
    signal = Column(String, index=True)  # Index for filtering by signal type
    confidence = Column(Float)
    price = Column(Float)
    rsi = Column(Float)
    ema20 = Column(Float)
    ema50 = Column(Float)
    macd = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)  # Individual index for time-based queries

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)


class TradingSession(Base):
    """Trading simulation session - persists even when browser is closed"""
    __tablename__ = "trading_sessions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String, default="Session")
    strategy_name = Column(String, default="Balanced")
    strategy_risk_per_trade = Column(Float, default=0.02)
    strategy_stop_loss = Column(Float, default=0.03)
    strategy_take_profit = Column(Float, default=0.06)
    strategy_max_positions = Column(Integer, default=5)
    strategy_trailing_stop = Column(Integer, default=1)  # 0 or 1
    symbols = Column(String, default="BTCUSDT,ETHUSDT,BNBUSDT")  # Comma-separated
    initial_balance = Column(Float, default=10000.0)
    current_balance = Column(Float, default=10000.0)
    is_active = Column(Integer, default=0)  # 0 or 1
    auto_trade = Column(Integer, default=0)  # 0 or 1
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionPosition(Base):
    """Open position in a trading session"""
    __tablename__ = "session_positions"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    symbol = Column(String, index=True)
    quantity = Column(Float)
    average_price = Column(Float)
    current_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    trailing_stop_price = Column(Float, nullable=True)
    pnl = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SessionTrade(Base):
    """Executed trade in a trading session"""
    __tablename__ = "session_trades"
    __table_args__ = {'extend_existing': True}
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    symbol = Column(String, index=True)
    trade_type = Column(String)  # BUY or SELL
    price = Column(Float)
    quantity = Column(Float)
    confidence = Column(Float)
    signal_reason = Column(String)  # BUY, SELL, STOP_LOSS, TAKE_PROFIT
    pnl = Column(Float, default=0.0)  # Only for SELL trades
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

# Create engine with connection pooling
try:
    engine = create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        pool_size=DB_POOL_SIZE,
        max_overflow=DB_MAX_OVERFLOW,
        pool_pre_ping=DB_POOL_PRE_PING,  # Verify connections before using
        echo=False  # Set to True for SQL debugging
    )
    logger.info(f"Database engine created with pool_size={DB_POOL_SIZE}, max_overflow={DB_MAX_OVERFLOW}")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise DatabaseConnectionError(f"Failed to create database engine: {e}")

# Create tables
Base.metadata.create_all(bind=engine)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_signal(signal_data: dict):
    """Save signal to database with error handling"""
    db = SessionLocal()
    try:
        signal = Signal(
            symbol=signal_data["symbol"],
            timeframe=signal_data["timeframe"],
            signal=signal_data["signal"],
            confidence=signal_data["confidence"],
            price=signal_data["price"],
            rsi=signal_data["indicators"]["rsi"],
            ema20=signal_data["indicators"]["ema20"],
            ema50=signal_data["indicators"]["ema50"],
            macd=signal_data["indicators"]["macd"]
        )
        db.add(signal)
        db.commit()
        db.refresh(signal)
        logger.debug(f"Saved signal for {signal_data['symbol']}: {signal_data['signal']}")
        return signal
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error saving signal: {e}")
        raise DuplicateSignalError(f"Signal already exists: {e}")
    except OperationalError as e:
        db.rollback()
        logger.error(f"Database operational error: {e}")
        raise DatabaseConnectionError(f"Database connection error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error saving signal: {e}")
        raise DatabaseError(f"Failed to save signal: {e}")
    finally:
        db.close()

def get_signal_history(symbol: str = None, limit: int = 100, offset: int = 0):
    """Get signal history from database with pagination and error handling"""
    db = SessionLocal()
    try:
        query = db.query(Signal)
        if symbol:
            query = query.filter(Signal.symbol == symbol)
        signals = query.order_by(Signal.timestamp.desc()).offset(offset).limit(limit).all()
        logger.debug(f"Retrieved {len(signals)} signals from history")
        return signals
    except OperationalError as e:
        logger.error(f"Database operational error retrieving history: {e}")
        raise DatabaseConnectionError(f"Database connection error: {e}")
    except Exception as e:
        logger.error(f"Error retrieving signal history: {e}")
        raise DatabaseError(f"Failed to retrieve signals: {e}")
    finally:
        db.close()

def get_settings_from_db():
    """Get all settings as a dict with error handling"""
    db = SessionLocal()
    try:
        settings_list = db.query(Settings).all()
        return {s.key: s.value for s in settings_list}
    except OperationalError as e:
        logger.error(f"Database operational error retrieving settings: {e}")
        raise DatabaseConnectionError(f"Database connection error: {e}")
    except Exception as e:
        logger.error(f"Error retrieving settings: {e}")
        raise DatabaseError(f"Failed to retrieve settings: {e}")
    finally:
        db.close()

def update_setting(key: str, value: str):
    """Update or create a setting with error handling"""
    db = SessionLocal()
    try:
        setting = db.query(Settings).filter(Settings.key == key).first()
        if not setting:
            setting = Settings(key=key, value=str(value))
            db.add(setting)
            logger.debug(f"Created new setting: {key}")
        else:
            setting.value = str(value)
            logger.debug(f"Updated setting: {key}")
        db.commit()
        return setting
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Integrity error updating setting {key}: {e}")
        raise DatabaseError(f"Failed to update setting: {e}")
    except OperationalError as e:
        db.rollback()
        logger.error(f"Database operational error updating setting: {e}")
        raise DatabaseConnectionError(f"Database connection error: {e}")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating setting {key}: {e}")
        raise DatabaseError(f"Failed to update setting: {e}")
    finally:
        db.close()
