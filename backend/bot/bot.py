import time
import sys
import os

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from config import settings
from services.signal_service import generate_signal_service
from logger import logger

# ⚠️ Configuration via settings
BOT_TOKEN = settings.telegram_bot_token
CHAT_ID = settings.telegram_chat_id

def send_telegram_message(message):
    """Send message via Telegram API"""
    if not BOT_TOKEN or BOT_TOKEN == "":
        logger.warning("⚠️ Bot Token non configuré. Message non envoyé.")
        return False
    
    if not CHAT_ID or CHAT_ID == "":
        logger.warning("⚠️ Chat ID non configuré. Message non envoyé.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        response = requests.post(url, data={"chat_id": CHAT_ID, "text": message})
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Erreur envoi Telegram: {e}")
        return False

def start_alerts(symbols=None, timeframe="1h", interval_minutes=5):
    """
    Start monitoring and sending alerts
    """
    if symbols is None:
        symbols = settings.default_cryptos
    
    logger.info(f"🚀 Démarrage des alertes pour {len(symbols)} cryptos...")
    logger.info(f"Cryptos: {', '.join(symbols)}")
    logger.info(f"Intervalle: {interval_minutes} minutes")
    
    while True:
        try:
            # Generate signals internally
            signals = []
            for symbol in symbols:
                try:
                    s = generate_signal_service(symbol, timeframe)
                    if "error" not in s:
                        signals.append(s)
                except Exception as e:
                    logger.error(f"Error generating signal for {symbol}: {e}")
            
            # Filter: only send BUY/SELL signals (not NEUTRE)
            important_signals = [
                s for s in signals 
                if s["signal"] != "NEUTRE"
            ]
            
            if important_signals:
                # Group signals by type
                buy_signals = [s for s in important_signals if "BUY" in s["signal"]]
                sell_signals = [s for s in important_signals if "SELL" in s["signal"]]
                
                # Build message
                msg_parts = ["🔔 **Nouveaux Signaux Détectés**\n"]
                
                if buy_signals:
                    msg_parts.append("🟢 **ACHATS:**")
                    for s in buy_signals:
                        msg_parts.append(
                            f"  • {s['symbol']} - {s['signal']} "
                            f"({int(s['confidence']*100)}%) - ${s['price']:.2f}"
                        )
                    msg_parts.append("")
                
                if sell_signals:
                    msg_parts.append("🔴 **VENTES:**")
                    for s in sell_signals:
                        msg_parts.append(
                            f"  • {s['symbol']} - {s['signal']} "
                            f"({int(s['confidence']*100)}%) - ${s['price']:.2f}"
                        )
                
                message = "\n".join(msg_parts)
                logger.info(f"📤 Envoi alerte: {len(important_signals)} signaux")
                send_telegram_message(message)
            else:
                logger.info("✓ Aucun signal important (tous NEUTRE)")
                
        except Exception as e:
            logger.error(f"❌ Erreur boucle bot: {e}")

        # Wait before next check
        logger.info(f"⏳ Prochaine vérification dans {interval_minutes} minutes...")
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    start_alerts()
