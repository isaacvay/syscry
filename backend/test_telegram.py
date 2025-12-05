import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.bot import send_telegram_message

print("🧪 Test d'envoi Telegram...")
result = send_telegram_message("🔔 Test: Bot Telegram réactivé !")

if result:
    print("✅ Message envoyé avec succès!")
else:
    print("❌ Échec de l'envoi")
