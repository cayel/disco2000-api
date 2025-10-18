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

Installez les dépendances :

```bash
pip install -r requirements.txt
```

## Running Locally


## Lancer le serveur en local

Démarrez le serveur de développement sur http://0.0.0.0:5001 :

```bash
source .venv/bin/activate
uvicorn main:app --reload --port 5001
```


Lorsque vous modifiez votre projet, le serveur se recharge automatiquement.

## Deploying to Vercel

Deploy your project to Vercel with the following command:

```bash
npm install -g vercel
vercel --prod
```

Or `git push` to your repostory with our [git integration](https://vercel.com/docs/deployments/git).

To view the source code for this template, [visit the example repository](https://github.com/vercel/vercel/tree/main/examples/fastapi).
