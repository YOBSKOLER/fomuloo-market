# Mini-projet S2 — Portage de Django REST vers FastAPI

## Décision de stack

La consigne du mini-projet demande FastAPI, Pydantic, SQLAlchemy et Alembic. L'API
Contacts active est donc portée de Django REST Framework vers cette stack. Les documents
`formation-django-drf.md`, `formation-postgresql-jwt.md`,
`formation-validation-erreurs-securite.md` et `formation-tests-api-ci.md` sont conservés
comme preuves/notes des exercices de formation T1–T4; ils ne décrivent pas la stack
active du mini-projet.

## Impact sur le projet

- **API/runtime :** les vues, serializers, modèles et URLs Django sont remplacés par
  FastAPI, schémas Pydantic et modèles SQLAlchemy.
- **Modèle de contacts :** le mini-projet emploie `nom`, `prenom`, `telephone`,
  `entreprise` et le groupe métier. Le prototype Django utilisait `first_name`,
  `last_name`, `phone`, un propriétaire et une authentification JWT.
- **Comportement :** l'API du mini-projet implémente CRUD, recherche et pagination,
  conforme à la fiche. L'authentification JWT et l'isolation par propriétaire, propres
  à l'exercice précédent, ne font pas partie des exigences de cette fiche.
- **Base et migrations :** les migrations Django ne servent plus à l'API mini-projet;
  Alembic crée la table `contacts`. SQLite est la valeur locale par défaut et `DB_URL`
  permet PostgreSQL.
- **Tests :** les anciennes suites Django (`contacts/tests.py` et
  `contacts/test_pytest_api.py`) ont été remplacées par des tests pytest qui utilisent
  `FastAPI TestClient` et une base SQLite temporaire. Ils vérifient routes, sérialisation,
  validation Pydantic, requêtes SQLAlchemy, contraintes, recherche, pagination et erreurs.
- **CI :** GitLab applique la migration Alembic sur PostgreSQL, exécute pytest et produit
  les rapports de couverture Cobertura/HTML.
- **Dépendances et démarrage :** Django/DRF sont remplacés par FastAPI, SQLAlchemy,
  Alembic et Uvicorn. L'application démarre avec `uvicorn contacts.main:app --reload`.

## Vérification

Depuis la racine du dépôt :

```powershell
python -m pip install -r requirements-dev.txt
alembic upgrade head
python -m pytest --cov=contacts --cov-report=term-missing
```

Le schéma SQLite local par défaut est créé par Alembic. Les tests utilisent une base
éphémère distincte et ne modifient pas cette base locale.
