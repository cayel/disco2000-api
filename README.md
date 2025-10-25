# API Disco2000

API FastAPI pour la gestion d'albums, artistes et labels, intégrée à Discogs.

## Fonctionnalités principales
- Ajout d'albums studio à partir d'un master Discogs
- Gestion des artistes et labels (unicité, récupération automatique)
- Endpoints REST pour consultation et insertion
- Stockage des genres et styles en tableau (plusieurs valeurs par album)
- Tests unitaires robustes (pytest)
- Migration automatique des tables à chaque démarrage (via FastAPI lifespan)
- Configuration par fichier `.env` (token Discogs)

## Installation

Créez et activez l'environnement virtuel :
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Installez les dépendances :
```bash
pip install -r requirements.txt
```

Ajoutez un fichier `.env` à la racine :
```
DISCOGS_TOKEN=VOTRE_TOKEN
```

## Lancement du serveur

Démarrez l'API sur http://0.0.0.0:5001 :
```bash
uvicorn main:app --reload --port 5001
```

## Lancer les tests

Pour exécuter tous les tests asynchrones sans erreur d'event loop (FastAPI + SQLAlchemy async), utilise le plugin pytest-xdist :

```bash
pip install pytest-xdist
pytest -n auto tests
```

Chaque fichier de test sera lancé dans un processus séparé, ce qui garantit l'isolation des contextes asynchrones.

---

Pour toute question ou amélioration, ouvrez une issue ou contactez le repo.
