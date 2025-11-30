# API Disco2000

API FastAPI pour la gestion d'albums, artistes et labels, intégrée à Discogs.

## Fonctionnalités principales
- Ajout d'albums studio à partir d'un master Discogs
- Gestion des artistes et labels (unicité, récupération automatique)
- Association des artistes avec leur pays d'origine
- Endpoints REST pour consultation et insertion
- Filtrage des albums par artiste, date de début et date de fin
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

## Migrations de la base de données

Pour appliquer une migration SQL manuellement (par exemple pour ajouter le champ `country` aux artistes existants) :

```bash
python apply_migration.py sql/06-migration_artist_country.sql
```

## API Endpoints

### Artistes
- `GET /api/artists` - Liste tous les artistes avec leur pays (code ISO et nom)
- `GET /api/artists/search?q=beatles` - Recherche d'artistes par nom (recherche partielle)
- `GET /api/artists/{artist_id}` - Détails d'un artiste
- `PATCH /api/artists/{artist_id}` - Met à jour un artiste (nécessite authentification contributeur)
  ```json
  {
    "country": "FR"
  }
  ```
  Le pays doit être un code ISO 3166-1 alpha-2 valide (2 lettres) : FR, US, GB, DE, JP, etc.

### Pays
- `GET /api/countries` - Liste tous les codes pays ISO 3166-1 alpha-2 disponibles

### Albums
- `GET /api/albums` - Liste paginée des albums avec filtres optionnels :
  - `?page=1` - Numéro de page
  - `?page_size=20` - Nombre d'albums par page
  - `?artist=Beatles` - Filtre par nom d'artiste (recherche partielle)
  - `?year_from=1970` - Année de début (incluse)
  - `?year_to=1980` - Année de fin (incluse)

---

Pour toute question ou amélioration, ouvrez une issue ou contactez le repo.
