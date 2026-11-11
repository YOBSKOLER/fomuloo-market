# S2 — API REST : Gestionnaire de Contacts

API REST de carnet d'adresses professionnel, réalisée avec FastAPI, Pydantic,
SQLAlchemy et Alembic. L'API est versionnée (`/api/v1` et `/api/v2`) et documentée par
OpenAPI/Swagger.

## Installation et démarrage

Prérequis : Python 3.11 ou supérieur et SQLite (local) ou PostgreSQL.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
alembic upgrade head
python -m uvicorn contacts.main:app --reload
```

L'API locale est à `http://127.0.0.1:8000`. Swagger UI est sur
`http://127.0.0.1:8000/docs`, ReDoc sur `/redoc` et le schéma OpenAPI JSON sur
`/openapi.json`. Le fichier `.env` est local et ne doit pas être commité. Par défaut,
`DB_URL=sqlite:///./contacts.db` permet de démarrer sans serveur externe.

Pour PostgreSQL, configurer `DB_URL` dans `.env`, créer au préalable la base et son
utilisateur, puis appliquer `alembic upgrade head`. Ne jamais commiter un vrai secret.

## Versions et contrat

- **v1 stable** : `http://127.0.0.1:8000/api/v1/contacts` et `/api/v1/contacts/search`.
  Les réponses conservent les champs historiques.
- **v2** : mêmes opérations sous `/api/v2`, avec `nom_complet` ajouté aux réponses.
- Les anciens chemins `/contacts...` restent des alias temporaires, absents du schéma
  Swagger; les nouveaux clients doivent utiliser une version explicite.

Voir le [changelog](CHANGELOG.md) et les [notes S3 sur Swagger et le versioning](docs/formation-swagger-versioning.md).

## Modèle Contact

| Champ | Type | Règle |
| --- | --- | --- |
| `id` | UUID | Clé primaire générée par l'API |
| `nom` | string | Obligatoire, 1–100 caractères |
| `prenom` | string | Facultatif |
| `email` | email | Obligatoire, valide et unique |
| `telephone` | string | Facultatif |
| `entreprise` | string | Facultatif |
| `groupe` | enum | `CLIENT`, `PARTENAIRE`, `FOURNISSEUR`, `AUTRE` |
| `notes` | text | Facultatif |
| `created_at`, `updated_at` | datetime | Générés par le serveur |

## Endpoints disponibles dans v1 et v2

| Méthode | Route suffix | Description |
| --- | --- | --- |
| `POST` | `/contacts` | Créer (`201`) |
| `GET` | `/contacts?page=1&limit=10` | Liste paginée |
| `GET` | `/contacts/search?q=ada` | Recherche nom, prénom, email ou groupe |
| `GET` | `/contacts/{id}` | Lire par UUID |
| `PUT` | `/contacts/{id}` | Remplacer le contact |
| `PATCH` | `/contacts/{id}` | Modifier certains champs |
| `DELETE` | `/contacts/{id}` | Supprimer (`204`) |

Préfixer chaque route par `/api/v1` ou `/api/v2`. Les erreurs de validation retournent
`422`, un contact absent `404`, un email déjà utilisé `400`, et une erreur imprévue `500`.

Exemple de création (remplacer `v1` par `v2` pour la nouvelle version) :

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/v1/contacts `
  -H "Content-Type: application/json" `
  -d '{"nom":"Lovelace","prenom":"Ada","email":"ada@example.com","entreprise":"Analytical Engines","groupe":"CLIENT"}'

curl.exe "http://127.0.0.1:8000/api/v1/contacts?page=1&limit=10"
curl.exe "http://127.0.0.1:8000/api/v2/contacts/search?q=ada"
```

Les essais interactifs, paramètres, schémas de requête et réponses sont aussi accessibles
sur `/docs`.

## Tests et intégration continue

```powershell
python -m pytest --cov=contacts --cov-report=term-missing --cov-report=html
ruff check --isolated --select E4,E7,E9,F contacts tests alembic
```

Les tests utilisent `pytest` et `FastAPI TestClient`, avec une base SQLite temporaire. Le
pipeline GitLab applique Alembic sur PostgreSQL, lance les tests et conserve les rapports
Cobertura XML/HTML. Le workflow GitHub Actions (`.github/workflows/ci-cd.yml`) lance Ruff
et pytest sur les push et pull requests; il déploie sur AWS Elastic Beanstalk uniquement
après un push réussi vers `main`. Voir les [notes de formation CI/CD](docs/formation-github-actions-ci-cd.md)
pour la configuration AWS requise.

Le remote Git courant est GitLab : GitHub Actions ne s'exécutera que si ce dépôt est
également publié sur GitHub. Le pipeline GitLab existant reste indépendant.

## Migrations Alembic

```powershell
alembic upgrade head
alembic revision --autogenerate -m "description du changement"
alembic downgrade -1
```

Relire chaque migration autogénérée avant de la committer.

## Historique des formations Django

Les documents `docs/formation-*.md` des tickets T1 à T4 gardent les notes des exercices
antérieurs en Django REST Framework. Ils ne décrivent pas la stack active du mini-projet;
voir la [note sur le portage FastAPI](docs/mini-projet-fastapi.md).
