import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from config import settings
import requests

# Import constants
try:
    from constants import (
        DEFAULT_API_TIMEOUT, TELEGRAM_API_TIMEOUT, TELEGRAM_ALERT_CHECK_INTERVAL,
        TELEGRAM_RETRY_ATTEMPTS, TELEGRAM_RETRY_DELAY, MAX_BACKTEST_DAYS,
        EMOJI_BUY, EMOJI_SELL, EMOJI_NEUTRAL, EMOJI_ALERT, EMOJI_SUCCESS, 
        EMOJI_ERROR, EMOJI_CHART
    )
except ImportError:
    # Fallback if constants not available
    DEFAULT_API_TIMEOUT = 10
    TELEGRAM_API_TIMEOUT = 10
    TELEGRAM_ALERT_CHECK_INTERVAL = 3600
    TELEGRAM_RETRY_ATTEMPTS = 3
    TELEGRAM_RETRY_DELAY = 2
    MAX_BACKTEST_DAYS = 90
    EMOJI_BUY = "🟢"
    EMOJI_SELL = "🔴"
    EMOJI_NEUTRAL = "⚪"
    EMOJI_ALERT = "🚨"
    EMOJI_SUCCESS = "✅"
    EMOJI_ERROR = "❌"
    EMOJI_CHART = "📊"

# Configuration - use environment variable with fallback
BOT_TOKEN = settings.telegram_bot_token
API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# User watchlists (in-memory, could be moved to database)
user_watchlists = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message"""
    welcome_msg = """
🤖 **Crypto AI Bot**

Bienvenue ! Je suis votre assistant de trading crypto.

**Commandes disponibles:**
/signal BTC - Obtenir le signal pour BTC
/watch BTC ETH - Ajouter des cryptos à votre watchlist
/unwatch BTC - Retirer une crypto de la watchlist
/list - Voir votre watchlist
/help - Afficher cette aide

Configurez vos alertes automatiques avec /settings
    """
    await update.message.reply_text(welcome_msg)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help"""
    await start(update, context)

async def signal_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get signal for a specific crypto"""
    if not context.args:
        await update.message.reply_text("❌ Usage: /signal BTC")
        return
    
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    
    try:
        response = requests.post(
            f"{API_URL}/get-signal",
            json={"symbol": symbol, "timeframe": "1h"},
            timeout=DEFAULT_API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "error" in data:
                await update.message.reply_text(f"❌ Erreur: {data['error']}")
                return
            
            emoji = EMOJI_NEUTRAL
            if "BUY" in data['signal']:
                emoji = EMOJI_BUY
            elif "SELL" in data['signal']:
                emoji = EMOJI_SELL
            
            msg = f"""
{emoji} **Signal: {data['symbol']}**
Timeframe: {data['timeframe']}
Signal: **{data['signal']}**
Confiance: {int(data['confidence'] * 100)}%
Prix: ${data['price']:.2f}

📊 **Indicateurs:**
RSI: {data['indicators']['rsi']:.2f}
MACD: {data['indicators']['macd']:.2f}
EMA20: {data['indicators']['ema20']:.2f}
EMA50: {data['indicators']['ema50']:.2f}
            """
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ Erreur lors de la récupération du signal")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")

async def watch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add cryptos to watchlist"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /watch BTC ETH SOL")
        return
    
    if user_id not in user_watchlists:
        user_watchlists[user_id] = set()
    
    added = []
    for symbol in context.args:
        symbol = symbol.upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"
        user_watchlists[user_id].add(symbol)
        added.append(symbol)
    
    await update.message.reply_text(f"✅ Ajouté à la watchlist: {', '.join(added)}")

async def unwatch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove crypto from watchlist"""
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text("❌ Usage: /unwatch BTC")
        return
    
    if user_id not in user_watchlists:
        await update.message.reply_text("❌ Votre watchlist est vide")
        return
    
    removed = []
    for symbol in context.args:
        symbol = symbol.upper()
        if not symbol.endswith("USDT"):
            symbol += "USDT"
        if symbol in user_watchlists[user_id]:
            user_watchlists[user_id].remove(symbol)
            removed.append(symbol)
    
    if removed:
        await update.message.reply_text(f"✅ Retiré de la watchlist: {', '.join(removed)}")
    else:
        await update.message.reply_text("❌ Aucune crypto trouvée dans votre watchlist")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's watchlist with current signals"""
    user_id = update.effective_user.id
    
    if user_id not in user_watchlists or not user_watchlists[user_id]:
        await update.message.reply_text("❌ Votre watchlist est vide. Utilisez /watch BTC ETH pour ajouter des cryptos.")
        return
    
    try:
        symbols = list(user_watchlists[user_id])
        response = requests.post(
            f"{API_URL}/signals/multi",
            json={"symbols": symbols, "timeframe": "1h"},
            timeout=DEFAULT_API_TIMEOUT * 1.5  # Longer timeout for multiple signals
        )
        
        if response.status_code == 200:
            data = response.json()
            signals = data.get("signals", [])
            
            msg = "📋 **Votre Watchlist:**\n\n"
            for signal in signals:
                if "error" in signal:
                    continue
                    
                emoji = EMOJI_NEUTRAL
                if "BUY" in signal['signal']:
                    emoji = EMOJI_BUY
                elif "SELL" in signal['signal']:
                    emoji = EMOJI_SELL
                
                msg += f"{emoji} **{signal['symbol']}** - {signal['signal']} ({int(signal['confidence']*100)}%)\n"
                msg += f"   Prix: ${signal['price']:.2f}\n\n"
            
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ Erreur lors de la récupération des signaux")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show performance statistics"""
    try:
        response = requests.get(
            f"{API_URL}/signals/history?limit=100",
            timeout=DEFAULT_API_TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            signals = data.get("signals", [])
            
            if not signals:
                await update.message.reply_text("❌ Aucun signal dans l'historique")
                return
            
            # Calculate stats
            buy_signals = len([s for s in signals if "BUY" in s['signal']])
            sell_signals = len([s for s in signals if "SELL" in s['signal']])
            neutral_signals = len([s for s in signals if s['signal'] == "NEUTRE"])
            
            avg_confidence = sum([s['confidence'] for s in signals]) / len(signals)
            
            msg = f"""
📊 **Statistiques (100 derniers signaux)**

Total: {len(signals)}
🟢 BUY: {buy_signals}
🔴 SELL: {sell_signals}
⚪ NEUTRE: {neutral_signals}

Confiance moyenne: {int(avg_confidence * 100)}%
            """
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ Erreur lors de la récupération des stats")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")

async def backtest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Run backtest for a symbol"""
    if not context.args:
        await update.message.reply_text("❌ Usage: /backtest BTC [days]\nExemple: /backtest BTC 30")
        return
    
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT"):
        symbol += "USDT"
    
    days = 30
    if len(context.args) > 1:
        try:
            days = int(context.args[1])
            if days > MAX_BACKTEST_DAYS:
                days = MAX_BACKTEST_DAYS
        except:
            pass
    
    await update.message.reply_text(f"⏳ Lancement du backtest pour {symbol} sur {days} jours...")
    
    try:
        response = requests.post(
            f"{API_URL}/backtest?symbol={symbol}&days={days}",
            timeout=60  # Backtest can take longer
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "error" in data:
                await update.message.reply_text(f"❌ Erreur: {data['error']}")
                return
            
            profit_emoji = "🟢" if data['total_profit'] > 0 else "🔴"
            
            msg = f"""
📈 **Backtest {data['symbol']}**
Période: {data['period_days']} jours

{profit_emoji} Profit: ${data['total_profit']:.2f}
ROI: {data['roi']:.2f}%

Trades: {data['total_trades']}
✅ Gagnants: {data['winning_trades']}
❌ Perdants: {data['losing_trades']}
Win Rate: {data['win_rate']:.1f}%

Gain moyen: ${data['avg_win']:.2f}
Perte moyenne: ${data['avg_loss']:.2f}
Profit Factor: {data['profit_factor']:.2f}
            """
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ Erreur lors du backtest")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur: {str(e)}")

# Store last known signal for each user+symbol to avoid spam
# Format: {user_id: {symbol: "BUY"}}
last_signals = {}

async def check_alerts(context: ContextTypes.DEFAULT_TYPE):
    """Background task to check for signals"""
    for user_id, symbols in user_watchlists.items():
        if not symbols:
            continue
            
        try:
            # Fetch signals for all symbols
            response = requests.post(
                f"{API_URL}/signals/multi",
                json={"symbols": list(symbols), "timeframe": "1h"},
                timeout=DEFAULT_API_TIMEOUT * 3  # Longer for background checks
            )
            
            if response.status_code == 200:
                data = response.json()
                signals = data.get("signals", [])
                
                for signal in signals:
                    symbol = signal['symbol']
                    current_signal = signal['signal']
                    
                    # Skip if error or neutral
                    if "error" in signal or current_signal == "NEUTRE":
                        continue
                        
                    # Check if signal changed
                    last_user_signals = last_signals.get(user_id, {})
                    last_signal = last_user_signals.get(symbol)
                    
                    if current_signal != last_signal:
                        # Send alert
                        emoji = EMOJI_BUY if "BUY" in current_signal else EMOJI_SELL
                        msg = f"{EMOJI_ALERT} **ALERTE {symbol}**\n\n{emoji} Nouveau signal: **{current_signal}**\nPrix: ${signal['price']:.2f}\nConfiance: {int(signal['confidence']*100)}%"
                        await context.bot.send_message(chat_id=user_id, text=msg)
                        
                        # Update last signal
                        if user_id not in last_signals:
                            last_signals[user_id] = {}
                        last_signals[user_id][symbol] = current_signal
                        
        except Exception as e:
            print(f"Error checking alerts for user {user_id}: {e}")

def main():
    """Start the bot"""
    if not BOT_TOKEN or BOT_TOKEN == "":
        print("❌ TELEGRAM_BOT_TOKEN non configuré dans .env")
        print("Veuillez configurer votre token Telegram dans backend/.env")
        return
    
    print("🚀 Démarrage du bot Telegram...")
    
    # Create application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("signal", signal_command))
    application.add_handler(CommandHandler("watch", watch_command))
    application.add_handler(CommandHandler("unwatch", unwatch_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("backtest", backtest_command))
    
    # Add background job for alerts (check every hour)
    if application.job_queue:
        application.job_queue.run_repeating(check_alerts, interval=TELEGRAM_ALERT_CHECK_INTERVAL, first=10)
        print(f"{EMOJI_SUCCESS} Système d'alertes automatiques activé (intervalle: {TELEGRAM_ALERT_CHECK_INTERVAL}s)")
    
    # Start the bot
    print("✅ Bot démarré ! Utilisez /start pour commencer.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
