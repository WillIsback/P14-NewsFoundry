# NewsFoundry

Outil de revue de presse automatique par IA.

**Frontend :** [https://news-foundry-lime.vercel.app/](https://news-foundry-lime.vercel.app/)
**Backend :** [https://p14-newsfoundry-production.up.railway.app](https://p14-newsfoundry-production.up.railway.app)
**Documentation :** [https://willisback.github.io/P14-NewsFoundry/](https://willisback.github.io/P14-NewsFoundry/)

## Documentation

La documentation technique (Starlight + TypeDoc) est disponible en ligne : **[https://willisback.github.io/P14-NewsFoundry/](https://willisback.github.io/P14-NewsFoundry/)**

Elle est auto-générée depuis les JSDoc/TSDoc du frontend et déployée sur GitHub Pages à chaque push sur `main`.

La documentation Markdown du projet se trouve dans le dossier [`docs/`](docs/index.md).

| Document | Description |
|----------|-------------|
| [Documentation complète](docs/index.md) | Index et table des matières |
| [Architecture](docs/architecture.md) | Structure du projet, flux de données |
| [Choix techniques](docs/technical-choices.md) | Justification de la stack et des librairies |
| [API](docs/api.md) | Points d'API, codes de statut, erreurs |
| [Authentification](docs/authentication.md) | JWT, sessions, isolation des données |
| [Prompts](docs/prompts.md) | Ingénierie des prompts LLM |
| [Tests](docs/testing.md) | Stratégie de test et CI/CD |
| [Gestion d'erreurs](docs/error-handling.md) | Erreurs backend, frontend, LLM, API |
| [Déploiement](docs/deployment.md) | Vercel, Railway, CI/CD |
| [Performance](docs/performance.md) | Optimisations et recommandations |

## Prérequis

- Docker
- Python 3.13
- uv
- Node.js 22.19

## Installation

1. Cloner le repository
2. Démarrer le backend avec les instructions du fichier `backend/README.md`
3. Démarrer le frontend avec les instructions du fichier `frontend/README.md`
