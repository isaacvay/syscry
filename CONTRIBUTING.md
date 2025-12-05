# Contributing to Crypto AI System

Merci de votre intérêt pour contribuer au projet! Ce guide vous aidera à démarrer.

## 🚀 Quick Start

1. **Fork** le repository
2. **Clone** votre fork
3. **Créer** une branche pour votre feature
4. **Commiter** vos changements
5. **Pousser** vers votre fork
6. **Ouvrir** une Pull Request

## 📋 Prérequis

- Node.js 18+
- pnpm
- Python 3.9+
- Git

## 🔧 Setup Development

```bash
# Cloner le repo
git clone https://github.com/your-username/syscry.git
cd syscry

# Installer les dépendances
pnpm install

# Backend
cd backend
python -m venv .venv
source .venv/bin/activate  # ou .venv\Scripts\activate sur Windows
pip install -r requirements.txt

# Copier les fichiers d'environnement
cp .env.example .env.local
cp backend/.env.example backend/.env
```

## 🧪 Tests

Avant de soumettre une PR, assurez-vous que tous les tests passent:

```bash
# Frontend
pnpm test
pnpm test:coverage

# Backend
cd backend
pytest tests/ -v --cov=.

# Linter
pnpm lint

# Format
pnpm format:check
```

## 📝 Conventions de Code

### TypeScript/React
- Utiliser TypeScript strict
- Composants fonctionnels avec hooks
- Nommer les fichiers en PascalCase pour les composants
- Utiliser `React.memo` pour les composants lourds

### Python
- Suivre PEP 8
- Type hints obligatoires
- Docstrings pour toutes les fonctions publiques
- Maximum 88 caractères par ligne (Black)

### Commits
Suivre [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add new feature
fix: bug fix
docs: documentation changes
style: formatting, missing semi colons, etc
refactor: code refactoring
test: adding tests
chore: updating build tasks, etc
```

**Breaking changes**: Ajouter `BREAKING CHANGE:` dans le body du commit

## 🔀 Pull Requests

### Checklist
- [ ] Tests ajoutés/mis à jour
- [ ] Documentation mise à jour
- [ ] Code formaté (`pnpm format`)
- [ ] Linter passe (`pnpm lint`)
- [ ] Tests passent (`pnpm test`)
- [ ] Pas de secrets hardcodés
- [ ] PR description claire

### Taille
- Garder les PRs petites (< 500 lignes si possible)
- Une feature = une PR
- Séparer les refactorings des nouvelles features

### Review Process
1. CI/CD doit passer (tests, linter, security scan)
2. Au moins 1 review approuvée
3. Pas de conflits avec `main`
4. Coverage ne doit pas diminuer

## 🐛 Reporting Bugs

Utiliser les GitHub Issues avec le template:

```markdown
**Description**
Description claire du bug

**Steps to Reproduce**
1. Aller à '...'
2. Cliquer sur '...'
3. Voir l'erreur

**Expected Behavior**
Ce qui devrait se passer

**Actual Behavior**
Ce qui se passe réellement

**Environment**
- OS: [e.g. Windows 11]
- Node: [e.g. 18.17.0]
- Browser: [e.g. Chrome 120]
```

## 💡 Feature Requests

Ouvrir une issue avec:
- Description détaillée de la feature
- Use case / problème résolu
- Proposition d'implémentation (optionnel)

## 🏗️ Architecture

Consulter:
- `project_analysis.md` - Analyse complète
- `implementation_plan.md` - Plan d'implémentation
- `GETTING_STARTED.md` - Guide de démarrage

## 📚 Resources

- [Next.js Docs](https://nextjs.org/docs)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Testing Library](https://testing-library.com/react)
- [Jest Docs](https://jestjs.io/)

## ❓ Questions

- Ouvrir une Discussion sur GitHub
- Consulter la documentation existante
- Vérifier les issues fermées

## 📄 License

En contribuant, vous acceptez que vos contributions soient sous la même licence que le projet (MIT).

---

Merci de contribuer! 🎉
