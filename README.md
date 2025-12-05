# 🚀 Crypto AI System - Frontend Premium

Système de trading crypto avec IA et analyse en temps réel. Interface moderne et performante construite avec Next.js 16, React 19, et TailwindCSS 4.

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Next.js](https://img.shields.io/badge/Next.js-16.0-black)
![React](https://img.shields.io/badge/React-19.2-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue)

## ✨ Fonctionnalités

### 🎨 Design Premium
- **Palette vibrante**: Gradients cyan/violet/rose avec effets glassmorphism
- **Typographie professionnelle**: Inter (body) + JetBrains Mono (data)
- **Animations fluides**: Framer Motion pour toutes les interactions
- **Design system**: 400+ variables CSS pour cohérence totale

### 📊 Analyse Avancée
- **Signaux AI**: BUY/SELL/NEUTRAL avec niveau de confiance
- **Indicateurs techniques**: RSI, MACD, EMA20, EMA50, Bollinger Bands
- **Graphiques interactifs**: Candlestick, Line, Area avec zoom/pan
- **Market Heatmap**: Visualisation performance 24h

### ⚡ Temps Réel
- **WebSocket**: Connexion temps réel au backend (optionnel)
- **Auto-refresh**: Mise à jour automatique configurable
- **Notifications**: Toast pour nouveaux signaux
- **Status live**: Indicateur de connexion animé

### 🛠️ Outils Avancés
- **Backtest**: Simulation sur données historiques
- **Alertes**: Système d'alertes personnalisables
- **Watchlist**: Suivi multi-crypto avec badges
- **Grid Dashboard**: Vue multi-crypto en grille

## 🚀 Démarrage Rapide

### Prérequis
- Node.js 18+
- pnpm (recommandé) ou npm
- Backend Python FastAPI (voir `/backend`)

### Installation

```bash
# Cloner le repo
git clone <repo-url>
cd syscry

# Installer les dépendances
pnpm install

# Lancer le dev server
pnpm dev
```

L'application sera disponible sur [http://localhost:3000](http://localhost:3000)

### Backend

```bash
# Terminal séparé
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
uvicorn main:app --reload
```

Le backend sera sur [http://localhost:8000](http://localhost:8000)

## 📁 Structure du Projet

```
app/
├── components/
│   ├── ui/              # Composants UI réutilisables
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   ├── Badge.tsx
│   │   ├── Tooltip.tsx
│   │   └── Modal.tsx
│   ├── CryptoChart.tsx  # Graphique principal
│   ├── Watchlist.tsx    # Liste de suivi
│   ├── GridDashboard.tsx
│   ├── MarketHeatmap.tsx
│   ├── AlertManager.tsx
│   └── ConnectionStatus.tsx
├── hooks/
│   └── useWebSocket.ts  # Hook WebSocket
├── store/
│   └── useAppStore.ts   # State management Zustand
├── backtest/
│   └── page.tsx         # Page backtest
├── settings/
│   └── page.tsx         # Page paramètres
├── design-system.css    # Variables CSS
├── animations.ts        # Variants Framer Motion
├── globals.css
├── layout.tsx
├── page.tsx             # Dashboard principal
└── providers.tsx        # React Query provider
```

## 🎨 Composants UI

### Button
```tsx
import { Button } from './components/ui/Button';

<Button variant="primary" size="lg" isLoading={loading}>
  Action
</Button>

// Variants: primary, secondary, ghost, danger, success
// Sizes: sm, md, lg
```

### Card
```tsx
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/Card';

<Card variant="gradient" glow hover>
  <CardHeader>
    <CardTitle>Titre</CardTitle>
  </CardHeader>
  <CardContent>
    Contenu
  </CardContent>
</Card>

// Variants: default, glass, gradient
```

### Input
```tsx
import { Input } from './components/ui/Input';

<Input
  label="Email"
  type="email"
  error={errors.email}
  leftIcon={<Mail />}
/>
```

### Badge
```tsx
import { Badge } from './components/ui/Badge';

<Badge variant="success" dot>Live</Badge>

// Variants: default, success, danger, warning, info
```

### Tooltip
```tsx
import { Tooltip } from './components/ui/Tooltip';

<Tooltip content="Information utile" position="top">
  <Button>Hover me</Button>
</Tooltip>
```

### Modal
```tsx
import { Modal, ModalBody, ModalFooter } from './components/ui/Modal';

<Modal isOpen={isOpen} onClose={onClose} title="Titre">
  <ModalBody>
    Contenu
  </ModalBody>
  <ModalFooter>
    <Button onClick={onClose}>Fermer</Button>
  </ModalFooter>
</Modal>
```

## 🔧 Configuration

### Variables d'Environnement
Créer `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Personnalisation du Design

Modifier `app/design-system.css`:

```css
:root {
  --color-primary-500: hsl(190, 80%, 50%);
  --gradient-primary: linear-gradient(...);
  /* ... */
}
```

## 📊 Utilisation

### Vue Dashboard
- **Stats en temps réel**: Market value, signaux, confidence
- **Graphique principal**: Analyse technique complète
- **Watchlist**: Suivi de plusieurs cryptos
- **Signal history**: Historique des signaux

### Vue Grid
- **Multi-crypto**: 4 cryptos en parallèle
- **Stats individuelles**: Prix, signal, RSI, confidence
- **Mise à jour auto**: Refresh toutes les 30s

### Vue Advanced
- **Market Heatmap**: Performance 24h de toutes les cryptos
- **Alert Manager**: Gestion des alertes personnalisées
- **Grid Dashboard**: Vue multi-crypto

### Backtest
- **Simulation**: Testez vos stratégies
- **Historique**: Tous les trades simulés
- **Statistiques**: Win rate, profit total

### Settings
- **API Binance**: Configuration des clés
- **Préférences**: Crypto et timeframe par défaut
- **Telegram**: Alertes par bot

## 🎯 Fonctionnalités Avancées

### WebSocket Temps Réel
```tsx
import { useWebSocketSignals } from './hooks/useWebSocket';

const { signals, isConnected, connectionStatus } = useWebSocketSignals({
  enabled: true,
  onSignalUpdate: (signals) => {
    console.log('New signals:', signals);
  },
});
```

### State Management
```tsx
import { useAppStore } from './store/useAppStore';

const { alerts, addAlert, preferences, updatePreferences } = useAppStore();
```

### Animations
```tsx
import { motion } from 'framer-motion';
import { slideUp, staggerContainer } from './animations';

<motion.div {...slideUp}>
  <h1>Animé!</h1>
</motion.div>
```

## 🚀 Performance

### Optimisations Appliquées
- ✅ Code splitting automatique (Next.js)
- ✅ React Query pour cache et optimisation
- ✅ Lazy loading des composants
- ✅ Memoization (React.memo, useMemo)
- ✅ CSS variables (pas de styles inline)
- ✅ Font optimization (display: swap)
- ✅ **NOUVEAU**: GZIP compression sur API
- ✅ **NOUVEAU**: Retry logic avec exponential backoff
- ✅ **NOUVEAU**: Pagination pour historique
- ✅ **NOUVEAU**: Composants memoized (Watchlist)

### API Resilience
Le système utilise maintenant un client API robuste avec:
- **Retry automatique**: 3 tentatives avec exponential backoff
- **Timeout**: 30s par défaut
- **Error handling**: Gestion intelligente des erreurs réseau et serveur

```typescript
import { apiClient } from './utils/api';

// Utilisation simple
const data = await apiClient.get('/get-signal');

// Avec options personnalisées
const data = await apiClient.post('/get-signal', 
    { symbol: 'BTCUSDT', timeframe: '1h' },
    { timeout: 10000 },
    { maxRetries: 5 }
);
```

### Métriques Cibles
- **FCP**: < 1.5s
- **LCP**: < 2.5s
- **CLS**: < 0.1
- **TTI**: < 3.5s

## 🎨 Design Tokens

### Couleurs
```css
--color-primary-500: hsl(190, 80%, 50%)
--color-signal-buy: hsl(142, 76%, 50%)
--color-signal-sell: hsl(0, 84%, 60%)
```

### Spacing
```css
--space-4: 1rem      /* 16px */
--space-8: 2rem      /* 32px */
--space-12: 3rem     /* 48px */
```

### Typography
```css
--text-base: clamp(1rem, 0.9rem + 0.5vw, 1.125rem)
--text-2xl: clamp(1.5rem, 1.3rem + 1vw, 1.875rem)
```

## 📦 Technologies

### Core
- **Next.js 16**: Framework React avec App Router
- **React 19**: Bibliothèque UI
- **TypeScript 5**: Typage statique
- **TailwindCSS 4**: Utility-first CSS

### UI & Animations
- **Framer Motion 12**: Animations fluides
- **Lucide React**: Icons modernes
- **React Hot Toast**: Notifications

### Data & State
- **TanStack Query 5**: Cache et data fetching
- **Zustand 5**: State management
- **React Use WebSocket**: WebSocket client

### Charts
- **Lightweight Charts 5**: Graphiques financiers
- **Recharts 3**: Graphiques statistiques

## 🔜 Roadmap

### Phase 1 ✅ (Complété)
- [x] Design system premium
- [x] Composants UI réutilisables
- [x] Dashboard redesigné
- [x] WebSocket hook
- [x] State management

### Phase 2 🚧 (En cours)
- [ ] Portfolio tracker
- [ ] Advanced analytics
- [ ] Mobile app (React Native)
- [ ] Dark/Light mode toggle

### Phase 3 📋 (Planifié)
- [ ] PWA support
- [ ] Offline mode
- [ ] Push notifications
- [ ] Multi-language (i18n)

## 🤝 Contribution

Les contributions sont les bienvenues! Voir [CONTRIBUTING.md](CONTRIBUTING.md)

## 📄 License

MIT License - voir [LICENSE](LICENSE)

## 🙏 Remerciements

- **Next.js Team** pour le framework
- **Vercel** pour l'hébergement
- **TradingView** pour Lightweight Charts
- **Binance** pour l'API crypto

## 📞 Support

- 📧 Email: support@cryptoai.com
- 💬 Discord: [Join our server](https://discord.gg/cryptoai)
- 📖 Docs: [docs.cryptoai.com](https://docs.cryptoai.com)

---

**Made with ❤️ by the Crypto AI Team**
