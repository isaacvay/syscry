"""
Telegram Alert Service
Background service that sends trading signals to Telegram.
Runs automatically when backend starts.
"""
import threading
import time
from typing import Optional, List, Dict

from config import settings
from logger import logger

# Global state
_alert_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


class TelegramAlertService:
    """Background service for sending Telegram alerts"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval_minutes = 5  # Check every 5 minutes
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
    
    def start(self):
        """Start the Telegram alert service"""
        global _alert_thread, _stop_event
        
        # Check if Telegram is configured
        if not self.bot_token or not self.chat_id:
            logger.warning("⚠️ Telegram not configured - alerts disabled")
            logger.warning("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env to enable")
            return
        
        if self.is_running:
            logger.warning("Telegram alert service already running")
            return
        
        _stop_event.clear()
        _alert_thread = threading.Thread(target=self._run_loop, daemon=True)
        _alert_thread.start()
        self.is_running = True
        logger.info(f"🔔 Telegram alerts started (interval: {self.check_interval_minutes}min)")
        
        # Create default sessions if none exist
        self._ensure_default_sessions()
    
    def _ensure_default_sessions(self):
        """Create default trading sessions if none exist"""
        try:
            from services.trading_service import get_all_sessions, create_session
            
            sessions = get_all_sessions()
            if len(sessions) == 0:
                # Create Normal session
                create_session(
                    name="Session Normal",
                    strategy_name="Normal",
                    initial_balance=10000.0,
                    symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
                    strategy_config={
                        "risk_per_trade": 0.02,
                        "stop_loss": 0.03,
                        "take_profit": 0.06,
                        "max_positions": 4,
                        "trailing_stop": True
                    }
                )
                logger.info("✅ Created 'Session Normal'")
                
                # Create High Gain session
                create_session(
                    name="Session High Gain",
                    strategy_name="High Gain",
                    initial_balance=10000.0,
                    symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT"],
                    strategy_config={
                        "risk_per_trade": 0.04,
                        "stop_loss": 0.05,
                        "take_profit": 0.15,
                        "max_positions": 8,
                        "trailing_stop": False
                    }
                )
                logger.info("✅ Created 'Session High Gain'")
        except Exception as e:
            logger.error(f"Error creating default sessions: {e}")
    
    def stop(self):
        """Stop the Telegram alert service"""
        global _stop_event
        _stop_event.set()
        self.is_running = False
        logger.info("🔔 Telegram alert service stopped")
    
    def _run_loop(self):
        """Main loop that checks signals and sends alerts"""
        import requests
        from services.signal_service import generate_signal_service
        
        symbols = settings.default_cryptos
        
        while not _stop_event.is_set():
            try:
                self._check_and_send_alerts(symbols)
            except Exception as e:
                logger.error(f"Error in Telegram alert loop: {e}")
            
            # Wait for next check
            for _ in range(self.check_interval_minutes * 60):
                if _stop_event.is_set():
                    break
                time.sleep(1)
    
    def _check_and_send_alerts(self, symbols):
        """Check signals and send alerts for both strategies"""
        from services.signal_service import generate_signal_service
        
        signals = []
        for symbol in symbols:
            try:
                signal_data = generate_signal_service(symbol, "1h")
                if "error" not in signal_data:
                    signals.append(signal_data)
            except Exception as e:
                logger.debug(f"Error getting signal for {symbol}: {e}")
        
        # Classify signals by strategy
        normal_signals = []  # High confluence (strong signals only)
        high_gain_signals = []  # Lower confluence (more signals)
        
        for s in signals:
            signal_type = s.get("signal", "NEUTRE")
            confidence = s.get("confidence", 0)
            
            if signal_type == "NEUTRE":
                continue
            
            # High Gain: accepts all BUY/SELL signals with conf > 0.5
            if confidence >= 0.5:
                high_gain_signals.append(s)
            
            # Normal: only strong signals with conf > 0.65
            if confidence >= 0.65 or "STRONG" in signal_type:
                normal_signals.append(s)
        
        # Send alerts if any signals
        if normal_signals or high_gain_signals:
            self._send_dual_strategy_alert(normal_signals, high_gain_signals)
        else:
            logger.debug("✓ No important signals")
    
    def _send_dual_strategy_alert(self, normal_signals: List[Dict], high_gain_signals: List[Dict]):
        """Send Telegram alert with both strategies"""
        import requests
        
        msg_parts = ["🔔 **Signaux Détectés**\n"]
        
        # Normal Strategy Signals
        if normal_signals:
            msg_parts.append("📊 **NORMAL** (signaux confirmés):")
            for s in normal_signals:
                emoji = "🟢" if "BUY" in s.get("signal", "") else "🔴"
                msg_parts.append(
                    f"  {emoji} {s['symbol']} - {s['signal']} "
                    f"({int(s['confidence']*100)}%) - ${s['price']:.2f}"
                )
            msg_parts.append("")
        
        # High Gain Strategy Signals  
        if high_gain_signals:
            msg_parts.append("🚀 **HIGH GAIN** (plus de trades):")
            for s in high_gain_signals:
                emoji = "🟢" if "BUY" in s.get("signal", "") else "🔴"
                conf_icon = "💪" if s['confidence'] >= 0.65 else "⚡"
                msg_parts.append(
                    f"  {emoji}{conf_icon} {s['symbol']} - {s['signal']} "
                    f"({int(s['confidence']*100)}%) - ${s['price']:.2f}"
                )
        
        # Summary
        msg_parts.append(f"\n📈 Normal: {len(normal_signals)} | High Gain: {len(high_gain_signals)}")
        
        message = "\n".join(msg_parts)
        
        # Send to Telegram
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            response = requests.post(
                url, 
                data={"chat_id": self.chat_id, "text": message},
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"📤 Telegram alert sent: Normal={len(normal_signals)}, HighGain={len(high_gain_signals)}")
            else:
                logger.error(f"Telegram API error: {response.status_code}")
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")


# Global instance
telegram_alert_service = TelegramAlertService()
