# Telegram Bot Scripts

Ce dossier contient deux scripts Telegram :

## 1. `telegram_bot.py` - Bot Interactif (Recommandé)

Bot avec commandes interactives pour une utilisation personnelle.

### Commandes disponibles :
- `/start` - Message de bienvenue
- `/signal BTC` - Obtenir le signal pour une crypto
- `/watch BTC ETH SOL` - Ajouter des cryptos à votre watchlist
- `/unwatch BTC` - Retirer une crypto
- `/list` - Voir votre watchlist avec signaux actuels

### Lancement :
```bash
python backend/bot/telegram_bot.py
```

### Configuration :
Ajoutez votre token dans `backend/.env` :
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

---

## 2. `bot.py` - Alertes Automatiques

Script d'alertes automatiques qui envoie des notifications périodiques.

### Fonctionnalités :
- Surveille plusieurs cryptos simultanément
- Filtre intelligent : envoie uniquement BUY/SELL (pas NEUTRE)
- Intervalle configurable (défaut: 5 minutes)

### Lancement :
```bash
python backend/bot/bot.py
```

### Configuration :
Ajoutez dans `backend/.env` :
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

---

## Comment obtenir un Bot Token ?

1. Parlez à [@BotFather](https://t.me/botfather) sur Telegram
2. Envoyez `/newbot`
3. Suivez les instructions
4. Copiez le token fourni

## Comment obtenir votre Chat ID ?

1. Parlez à [@userinfobot](https://t.me/userinfobot)
2. Il vous donnera votre Chat ID
