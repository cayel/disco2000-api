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

## Endpoints principaux

### Ajouter un album studio
```
POST /api/albums/studio?master_id={id_discogs}
```
- Retourne 201 si l'album est ajouté
- Retourne 409 si l'album existe déjà


### Supprimer un album
```
DELETE /api/albums/{album_id}
```
- Retourne 204 si l'album est supprimé
- Retourne 404 si l'album n'existe pas
  
### Récupérer les infos d'un master Discogs
```
GET /api/discogs/master/{master_id}
```


### Exemple de réponse (infos master Discogs)
```json
{
  "artiste": "...",
  "titre": "...",
  "identifiants_discogs": {"master_id": 123, "main_release": 456, "artist_id": 789},
  "genres": ["Rock", "Pop", "Electronic"],
  "styles": ["Indie", "Synthpop"],
  "annee": 2000,
  "label": [
    {"name": "Label Name", "id": 1, "catno": "ABC123"}
  ],
  "pochette": "https://..."
}
```

### Endpoint artistes
```
GET /api/artists
```
Réponse :
```json
[
  {"id": 1, "name": "Nom Artiste", "discogs_id": 789},
  ...
]
```

> Depuis octobre 2025, le champ `discogs_id` de l'artiste est bien renseigné lors de l'ajout d'un album à partir d'un master Discogs.


## Lancer les tests

Pour exécuter tous les tests asynchrones sans erreur d'event loop (FastAPI + SQLAlchemy async), utilise le plugin pytest-xdist :

```bash
pip install pytest-xdist
pytest -n auto tests
```

Chaque fichier de test sera lancé dans un processus séparé, ce qui garantit l'isolation des contextes asynchrones.

## Déploiement Vercel

```bash
npm install -g vercel
vercel --prod
```

---

Pour toute question ou amélioration, ouvrez une issue ou contactez le repo.
