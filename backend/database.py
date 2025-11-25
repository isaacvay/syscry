from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import settings

Base = declarative_base()

class Signal(Base):
    __tablename__ = "signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True)
    timeframe = Column(String)
    signal = Column(String)
    confidence = Column(Float)
    price = Column(Float)
    rsi = Column(Float)
    ema20 = Column(Float)
    ema50 = Column(Float)
    macd = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    value = Column(String)

# Create engine
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

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
    """Save signal to database"""
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
        return signal
    finally:
        db.close()

def get_signal_history(symbol: str = None, limit: int = 100):
    """Get signal history from database"""
    db = SessionLocal()
    try:
        query = db.query(Signal)
        if symbol:
            query = query.filter(Signal.symbol == symbol)
        signals = query.order_by(Signal.timestamp.desc()).limit(limit).all()
        return signals
    finally:
        db.close()

def get_settings_from_db():
    """Get all settings as a dict"""
    db = SessionLocal()
    try:
        settings_list = db.query(Settings).all()
        return {s.key: s.value for s in settings_list}
    finally:
        db.close()

def update_setting(key: str, value: str):
    """Update or create a setting"""
    db = SessionLocal()
    try:
        setting = db.query(Settings).filter(Settings.key == key).first()
        if not setting:
            setting = Settings(key=key, value=str(value))
            db.add(setting)
        else:
            setting.value = str(value)
        db.commit()
        return setting
    finally:
        db.close()
