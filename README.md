# S2 — API REST : Gestionnaire de Contacts

API REST de carnet d'adresses professionnel, réalisée avec FastAPI, Pydantic,
SQLAlchemy et Alembic. L'interface Swagger est disponible sur `/docs`.

## Prérequis et installation

Python 3.11 ou supérieur et une base SQLite locale ou PostgreSQL.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
alembic upgrade head
uvicorn contacts.main:app --reload
```

Le serveur écoute sur `http://127.0.0.1:8000`; Swagger UI se trouve à
`http://127.0.0.1:8000/docs`. Le fichier `.env` est local et ne doit pas être commité.
La valeur par défaut `DB_URL=sqlite:///./contacts.db` permet de démarrer sans serveur
externe.

Pour PostgreSQL, remplacer `DB_URL` dans `.env`, par exemple :

```dotenv
DB_URL=postgresql+psycopg://contacts_user:mot_de_passe@localhost:5432/contacts
```

Créer la base et son utilisateur PostgreSQL au préalable, puis exécuter
`alembic upgrade head`. Ne jamais placer un secret réel dans le dépôt.

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
| `created_at`, `updated_at` | datetime | Gérées par la base |

## Endpoints

Les erreurs de validation retournent `422`; ressource absente : `404`; email déjà
utilisé : `400`. Les entrées invalides sont refusées avant enregistrement.

| Méthode | Route | Description |
| --- | --- | --- |
| `POST` | `/contacts` | Créer un contact (`201`) |
| `GET` | `/contacts?page=1&limit=10` | Liste paginée |
| `GET` | `/contacts/search?q=ada` | Recherche nom, prénom, email ou groupe |
| `GET` | `/contacts/{id}` | Lire un contact |
| `PUT` | `/contacts/{id}` | Remplacer le contact |
| `PATCH` | `/contacts/{id}` | Modifier certains champs |
| `DELETE` | `/contacts/{id}` | Supprimer (`204`) |

Exemples cURL (PowerShell peut aussi utiliser `curl.exe`) :

```bash
curl -X POST http://127.0.0.1:8000/contacts \
  -H "Content-Type: application/json" \
  -d '{"nom":"Lovelace","prenom":"Ada","email":"ada@example.com","entreprise":"Analytical Engines","groupe":"CLIENT"}'

curl "http://127.0.0.1:8000/contacts?page=1&limit=10"
curl "http://127.0.0.1:8000/contacts/search?q=ada"
curl http://127.0.0.1:8000/contacts/UUID_DU_CONTACT

curl -X PUT http://127.0.0.1:8000/contacts/UUID_DU_CONTACT \
  -H "Content-Type: application/json" \
  -d '{"nom":"King","prenom":"Ada","email":"ada@example.com","groupe":"PARTENAIRE"}'

curl -X PATCH http://127.0.0.1:8000/contacts/UUID_DU_CONTACT \
  -H "Content-Type: application/json" \
  -d '{"telephone":"+33123456789"}'

curl -X DELETE http://127.0.0.1:8000/contacts/UUID_DU_CONTACT
```

## Tests et intégration continue

```powershell
python -m pytest --cov=contacts --cov-report=term-missing --cov-report=html
```

Les tests utilisent `pytest`, `httpx` et `FastAPI TestClient`, avec une base SQLite
temporaire. Le pipeline GitLab lance Alembic sur PostgreSQL puis les tests avec rapports
Cobertura XML et HTML.

## Migrations

```powershell
alembic upgrade head
alembic revision --autogenerate -m "description du changement"
alembic downgrade -1
```

Relire toujours une migration autogénérée avant de la committer.

## Historique des formations Django

Les documents `docs/formation-*.md` des tickets T1 à T4 gardent les notes des exercices
Django REST Framework antérieurs. Ils décrivent une formation distincte; l'API active du
mini-projet S2 est l'implémentation FastAPI décrite dans ce README.

La migration du prototype Django vers la stack FastAPI et son impact sur les tests sont
décrits dans [docs/mini-projet-fastapi.md](docs/mini-projet-fastapi.md).
