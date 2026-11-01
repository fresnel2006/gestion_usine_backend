# API Gestion de l'usine

API REST FastAPI de l'application de gestion de l'usine (projet Agile TWIN 3 - ESATIC).
Base de données : PostgreSQL (locale ou Supabase).

## Lancer en local (Windows, PowerShell)

```
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # puis renseigner les valeurs
python seed_users.py
uvicorn app.main:app --reload
```

Documentation interactive : http://localhost:8000/docs

## Variables d'environnement

| Variable | Rôle |
|---|---|
| `DATABASE_URL` | Chaîne de connexion PostgreSQL (Supabase : Connect > Session pooler) |
| `JWT_SECRET` | Clé secrète de signature des jetons (longue chaîne aléatoire) |
| `JWT_EXPIRE_MINUTES` | Durée de validité d'un jeton, en minutes (480 par défaut) |
| `CORS_ORIGINS` | Adresses du frontend autorisées, séparées par des virgules |
| `SEUIL_STOCK_FAIBLE` | Seuil d'alerte de stock des pièces (5 par défaut) |

## Déploiement sur Render

1. Sur render.com : New > Blueprint, puis choisir ce dépôt (le fichier `render.yaml` est lu automatiquement).
2. Renseigner `DATABASE_URL` et `CORS_ORIGINS` (adresse Vercel du frontend).
3. Une fois le service en ligne, créer les comptes de test depuis un poste local
   pointant sur la même base : `python seed_users.py`.

Commande de démarrage pour un autre hébergeur :
`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Tests

```
python -m pytest
```

Les tests s'exécutent dans des transactions annulées : la base n'est pas modifiée.
