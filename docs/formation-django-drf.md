# Formation — Django et Django REST Framework

## Objectifs et ressources

Cette synthèse sert de support de révision pour le sprint S2. Elle accompagne les
ressources prescrites, mais ne constitue pas une preuve de suivi des cours :

- [OpenClassrooms — Débutez avec Django](https://openclassrooms.com/fr/courses/7172076-debutez-avec-le-framework-django)
- [OpenClassrooms — Allez plus loin avec Django](https://openclassrooms.com/fr/courses/7192426-allez-plus-loin-avec-le-framework-django)
- [Documentation officielle Django REST Framework](https://www.django-rest-framework.org/)

## Notes structurées

### Django

- Un projet regroupe la configuration et les points d'entrée (settings, ASGI/WSGI,
  routage racine). Une app regroupe un domaine métier et peut être réutilisée.
- `models.py` décrit les données et leurs contraintes ; les migrations versionnent
  l'évolution du schéma.
- `urls.py` associe des chemins à des vues. `include()` délègue le routage à une app.
- Les vues génériques réutilisent les comportements courants de lecture, création,
  mise à jour et suppression.
- L'ORM construit des requêtes paramétrées et gère les relations entre modèles.

### Django REST Framework

- Un serializer convertit les objets Django en représentations JSON et valide les
  données entrantes avant toute sauvegarde.
- Les vues génériques et mixins permettent d'implémenter un CRUD cohérent sans
  dupliquer les traitements HTTP.
- Les permissions déterminent qui peut appeler une vue ; les querysets filtrés
  déterminent quelles ressources un utilisateur peut réellement consulter ou modifier.
- `APITestCase` et `APIClient` vérifient les codes HTTP, les payloads, les validations
  et les règles d'accès.

### PostgreSQL, authentification et sécurité de base

- SQLite est pratique pour démarrer localement ; PostgreSQL est sélectionnable par
  variables d'environnement pour un environnement partagé ou de production.
- JWT sépare le jeton d'accès court du jeton de renouvellement. Les mots de passe
  restent gérés et hachés par le système d'authentification Django.
- Une API privée doit exiger une authentification et filtrer les données par
  propriétaire côté serveur. Ne jamais faire confiance à un identifiant de propriétaire
  fourni par le client.
- Les serializers rejettent les entrées invalides ; les contraintes en base protègent
  également l'intégrité en cas de requêtes concurrentes.
- En production : secret hors du dépôt, `DEBUG=false`, hôtes explicitement autorisés,
  HTTPS, politique CORS/CSRF adaptée au mode d'authentification et dépendances à jour.

## Exercice pratique réalisé : API de gestion de contacts

L'app `contacts` fournit une API JSON authentifiée :

| Méthode | Route | Résultat |
| --- | --- | --- |
| `POST` | `/api/token/` | Obtenir access/refresh avec username et password |
| `POST` | `/api/token/refresh/` | Renouveler un access token |
| `GET`, `POST` | `/api/contacts/` | Lister ses contacts ou en créer un |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/contacts/{id}/` | Lire/modifier/supprimer un de ses contacts |

### Lancer et vérifier

Depuis la racine du dépôt, installer les dépendances et initialiser la base :

```powershell
.\env\Scripts\python.exe -m pip install -r requirements.txt
.\env\Scripts\python.exe manage.py migrate
.\env\Scripts\python.exe manage.py createsuperuser
.\env\Scripts\python.exe manage.py test contacts
```

Démarrer le serveur avec `.\env\Scripts\python.exe manage.py runserver`. Créer un
jeton sur `/api/token/`, puis envoyer le jeton d'accès dans
`Authorization: Bearer <access>` pour appeler `/api/contacts/`.

Pour PostgreSQL, définir `DB_ENGINE=postgresql`, `POSTGRES_DB`, `POSTGRES_USER`,
`POSTGRES_PASSWORD`, `POSTGRES_HOST` et `POSTGRES_PORT` avant de lancer `migrate`.
SQLite reste le choix par défaut pour l'exercice local.
En production, définir également un `DJANGO_SECRET_KEY` aléatoire et confidentiel,
`DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS` avec les domaines attendus et, si
nécessaire, `EMAIL_BACKEND` vers un backend SMTP configuré. La configuration HTTPS
(redirection, cookies sécurisés et HSTS) doit correspondre au reverse proxy et au
domaine réellement déployés.

### Validation / résultat attendu

- Les tests couvrent le jeton JWT, l'accès anonyme refusé, le CRUD, l'email invalide,
  les doublons et l'isolation des contacts entre deux utilisateurs.
- Les données invalides retournent `400`; un objet appartenant à un autre compte
  retourne `404` plutôt que d'exposer son existence.

## Réinvestissement dans le mini-projet Contacts et Formuloo Market

- Réutiliser une app Django par domaine métier (`contacts`, puis éventuellement
  `accounts`, `orders` ou `catalog`) et inclure ses routes depuis le routeur principal.
- Remplacer le modèle d'exercice par les champs métiers validés en équipe et ajouter
  les relations nécessaires ; garder migrations et contraintes sous contrôle.
- Étendre les serializers pour la validation, sans accepter du client les champs
  d'identité ou de propriétaire qui doivent être déterminés côté serveur.
- Conserver des permissions et querysets filtrés par utilisateur, puis compléter les
  tests API à chaque règle métier.
- Utiliser PostgreSQL via configuration d'environnement dans les environnements
  partagés/CI et définir des secrets dans le gestionnaire de secrets, jamais dans Git.

## Definition of Done du livrable technique

- Architecture modulaire : projet `backend` et app métier `contacts`.
- Routage central et routes d'app séparés dans `urls.py`.
- Sérialisation/validation DRF dans `contacts/serializers.py`.
- CRUD réellement exécutable, JWT, choix de base PostgreSQL configurable et tests API.
- Le point rapide tuteur/pair et le dépôt effectif dans l'espace d'équipe restent à
  réaliser par le stagiaire.
