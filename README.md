# FastHTML Boilerplate

Deploy your [FastAPI](https://fastapi.tiangolo.com/) project to Vercel with zero configuration.

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/vercel/vercel/tree/main/examples/fastapi&template=fastapi)

_Live Example: https://ai-sdk-preview-python-streaming.vercel.app/_

Visit the [FastAPI documentation](https://fastapi.tiangolo.com/) to learn more.

## Getting Started



## Installation des dépendances

Créez et activez l'environnement virtuel (une seule fois) :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Installez les dépendances (API et tests) :

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # si ce fichier existe, sinon installez pytest, httpx, python-dotenv, fastapi, pydantic
```

Ajoutez un fichier `.env` à la racine du projet avec votre token Discogs :

```
DISCOGS_TOKEN=VOTRE_TOKEN
```

## Running Locally



## Lancer le serveur en local

Démarrez le serveur de développement sur http://0.0.0.0:5001 :

```bash
source .venv/bin/activate
uvicorn main:app --reload --port 5001
```



Lorsque vous modifiez votre projet, le serveur se recharge automatiquement.

## Endpoint Discogs

Pour récupérer les informations d'un master Discogs :

```
GET /api/discogs/master/{master_id}
```

Réponse :
```json
{
	"artiste": "...",
	"titre": "...",
	"identifiants_discogs": {"master_id": 123, "main_release": 456},
	"genres": ["..."],
	"styles": ["..."],
	"annee": 2000,
	"label": [
		{"name": "Label Name", "id": 1, "catno": "ABC123"}
	],
	"pochette": "https://..."
}
```

## Lancer les tests

Les tests unitaires sont dans le dossier `tests/` :

```bash
pytest tests/
```

## Deploying to Vercel

Deploy your project to Vercel with the following command:

```bash
npm install -g vercel
vercel --prod
```

Or `git push` to your repostory with our [git integration](https://vercel.com/docs/deployments/git).

To view the source code for this template, [visit the example repository](https://github.com/vercel/vercel/tree/main/examples/fastapi).
