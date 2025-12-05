# 🚀 Guide de Démarrage - Crypto AI System

## Installation

### Prérequis
- Node.js 18+ et pnpm
- Python 3.9+
- Git

### 1. Cloner et Installer

```bash
# Cloner le repository
git clone <repo-url>
cd syscry

# Installer les dépendances frontend
pnpm install

# Installer les dépendances backend
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# ou: source .venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

### 2. Configuration des Variables d'Environnement

#### Frontend
```bash
# Copier le template
cp .env.example .env.local

# Éditer .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

#### Backend
```bash
cd backend

# Copier le template
cp .env.example .env

# Éditer .env avec vos clés API
# Voir backend/.env.example pour la liste complète
```

**⚠️ Important**: Les clés API suivantes sont **optionnelles** mais recommandées:
- `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID` - Pour les alertes
- `NEWS_API_KEY` - Pour l'analyse de sentiment (gratuit sur newsapi.org)
- `TWITTER_BEARER_TOKEN` - Pour Twitter sentiment (optionnel)
- `REDDIT_CLIENT_ID/SECRET` - Pour Reddit sentiment (optionnel)

### 3. Démarrer l'Application

#### Terminal 1 - Backend
```bash
cd backend
.venv\Scripts\activate  # Windows
uvicorn main:app --reload
```

Le backend sera disponible sur http://localhost:8000

#### Terminal 2 - Frontend
```bash
pnpm dev
```

Le frontend sera disponible sur http://localhost:3000

## Tests

### Frontend
```bash
# Lancer les tests
pnpm test

# Mode watch
pnpm test:watch

# Coverage
pnpm test:coverage
```

### Backend
```bash
cd backend
pytest tests/ -v --cov=.
```

## Vérification de la Configuration

```bash
# Vérifier la configuration backend
cd backend
python config_validator.py
```

## Problèmes Courants

### "Configuration validation failed"
- Vérifiez que votre fichier `.env` existe dans le dossier `backend/`
- Consultez `backend/.env.example` pour les variables requises

### "WebSocket connection failed"
- Assurez-vous que le backend est démarré
- Vérifiez que `NEXT_PUBLIC_WS_URL` pointe vers le bon port

### Tests échouent
- Installez les dépendances: `pnpm install`
- Vérifiez que Jest est configuré: `pnpm test --version`

## Documentation

- **API**: http://localhost:8000/docs (Swagger)
- **Analyse Complète**: Voir `project_analysis.md`
- **Plan d'Implémentation**: Voir `implementation_plan.md`

## Support

Pour toute question, consultez la documentation ou ouvrez une issue.
