# Formation S3 — Documentation Swagger et versioning d'API

## Ressources

Cette synthèse accompagne les ressources du ticket et ne prétend pas prouver leur suivi :

- [Swagger / OpenAPI](https://swagger.io/docs/)
- [Fireship](https://www.youtube.com/c/Fireship)
- [OpenAPI avec FastAPI](https://fastapi.tiangolo.com/features/#automatic-docs)

## Notes structurées

- OpenAPI est une description machine-readable du contrat HTTP : chemins, méthodes,
  paramètres, corps, schémas de réponse et codes d'état.
- Swagger UI rend le contrat navigable et permet d'essayer les requêtes. FastAPI expose
  Swagger UI sur `/docs`, ReDoc sur `/redoc` et le document OpenAPI JSON sur `/openapi.json`.
- Documenter les modèles Pydantic et les retours des endpoints rend les exemples et les
  erreurs de validation visibles aux consommateurs.
- Une version d'API explicite dans le chemin (`/api/v1`, `/api/v2`) permet de faire
  coexister deux contrats. Ne pas modifier le sens ou supprimer un champ de v1 si un
  client le consomme; publier une version nouvelle pour une modification incompatible.
- Un changelog consigne les versions, les changements, leur compatibilité et les étapes
  de migration. La version d'application OpenAPI et les versions dans les chemins sont
  documentées ensemble mais répondent à deux questions différentes.

## Exercice pratique livré

L'API Contacts FastAPI documente ses routes dans Swagger UI et expose deux contrats :

- `v1` : contrat stable de l'API Contacts d'origine, publié sous `/api/v1`;
- `v2` : mêmes opérations et mêmes données métier, avec le champ calculé
  `nom_complet` ajouté aux réponses, sous `/api/v2`.

Les anciens chemins `/contacts...` restent temporairement disponibles pour ne pas casser
les essais précédents; ils sont cachés du document OpenAPI afin de diriger les nouveaux
clients vers des chemins versionnés. Ils seront retirés après migration des consommateurs,
avec annonce dans le changelog.

Swagger est accessible sur `http://127.0.0.1:8000/docs`. Le document contractuel est sur
`http://127.0.0.1:8000/openapi.json`. La référence de version et l'historique sont dans
`CHANGELOG.md`.

### Vérifier

```powershell
python -m pytest tests/test_api_versioning.py tests/test_contacts_api.py
```

Les tests contrôlent le contenu OpenAPI, les réponses v1/v2 et l'alias transitoire.

## Réinvestissement dans le mini-projet « API Authentifiée : Gestionnaire de Tâches avec JWT »

- Publier les tâches sous un préfixe versionné (`/api/v1/tasks`) et documenter les
  opérations de création, liste, détail, mise à jour et suppression.
- Décrire explicitement dans OpenAPI le bearer JWT, les réponses `401` et `403`, les
  modèles Pydantic et les erreurs métier.
- Garder le contrat v1 stable; faire évoluer les champs ou règles incompatibles en v2,
  ajouter des tests de contrat pour les deux versions et inscrire chaque changement au
  changelog.
- N'ajouter les tokens, secrets ou données personnelles réels ni aux exemples Swagger,
  ni aux captures de démo.

## Suivi de formation

Les notes et l'exercice technique sont présents dans le dépôt. Le suivi réel des
ressources, le point tuteur/pair et la publication externe restent à confirmer par le
stagiaire.

## S3 « Documentation Swagger & versioning API », puis la correction effectuée lors de la dernière vérification

## 1. Ajout du versioning de l’API

Dans contacts/main.py, les routes sont accessibles avec deux préfixes :

/api/v1 conserve le contrat précédent de l’API Contacts.
/api/v2 propose une version enrichie des réponses.
La v2 ajoute le champ calculé nom_complet aux réponses de contact. Le calcul est défini dans contacts/models.py, et les schémas de réponse de la v2 sont dans contacts/schemas.py. Ce champ est calculé à partir du nom et du prénom : il ne nécessite pas de nouvelle colonne en base de données.

Les anciennes routes sans préfixe, comme /contacts, sont conservées comme alias de compatibilité. Elles restent utilisables, mais sont cachées dans la documentation OpenAPI pour mettre en avant les routes versionnées.

## 2. Mise à jour de la documentation et du changelog

README.md a été complété pour présenter Swagger, le versioning et les routes de l’API.
CHANGELOG.md décrit les évolutions des versions 1.0.0 et 2.0.0.
docs/formation-swagger-versioning.md contient une synthèse de formation, l’exercice pratique et une explication de la réutilisation de cette compétence dans le futur gestionnaire de tâches avec JWT.
La documentation OpenAPI annonce la version 2.0.0 et décrit les chemins v1 et v2. Les chemins historiques sans préfixe n’y sont pas affichés.

## 3. Ajout de tests de versioning et correction d’un test existant

Le fichier tests/test_api_versioning.py contient six tests portant notamment sur la présence des routes versionnées dans OpenAPI, les réponses v1/v2 et le maintien des anciens chemins.

Dans tests/test_contacts_api.py, les assertions OpenAPI ont été adaptées aux nouveaux chemins. J’ai aussi corrigé un test qui vérifie la réponse lorsqu’on demande un contact inconnu : il attendait par erreur le message de doublon d’e-mail. Il vérifie maintenant le bon message, « Contact introuvable. »

## 4. Vérifications effectuées

Après cette correction, la suite complète a été relancée :

44 tests réussis
96 % de couverture totale
git diff --check : aucune erreur d’espacement signalée
alembic check avait précédemment confirmé qu’aucune migration de base de données n’était nécessaire pour le champ calculé nom_complet.
Un avertissement de dépréciation lié à httpx et TestClient apparaît encore, mais il ne fait pas échouer les tests.
