# Formation S2 — PostgreSQL et authentification JWT

> Note historique de formation. L'API du mini-projet Contacts est actuellement publique,
> selon le périmètre FastAPI de la fiche; le JWT ci-dessous décrit l'exercice antérieur.

## Objectifs et ressources

Cette synthèse accompagne les ressources du ticket T2 ; elle ne prétend pas prouver
que les cours externes ont été suivis :

- [OpenClassrooms — Implémentez vos bases de données relationnelles avec SQL](https://openclassrooms.com/fr/courses/6971126-implementez-vos-bases-de-donnees-relationnelles-avec-sql)
- [Documentation Django — Modèles et bases de données](https://docs.djangoproject.com/fr/5.0/topics/db/)
- [Documentation SimpleJWT](https://django-rest-framework-simplejwt.readthedocs.io/)

## Notes structurées

### PostgreSQL et ORM Django

- Les modèles décrivent les tables ; les migrations versionnent la structure et
  permettent de faire évoluer le schéma entre environnements.
- L'ORM paramètre les valeurs des requêtes. Préférer `QuerySet`, relations et
  contraintes Django à la concaténation de SQL.
- Une contrainte unique garantit l'intégrité même si deux requêtes concurrentes
  passent la validation applicative.
- SQLite sert de base locale par défaut. PostgreSQL est sélectionnable par
  `DB_ENGINE=postgresql` et les variables `POSTGRES_DB`, `POSTGRES_USER`,
  `POSTGRES_PASSWORD`, `POSTGRES_HOST` et `POSTGRES_PORT`.
- Garder identifiants de base et secrets dans l'environnement, pas dans Git. Appliquer
  les migrations explicitement dans chaque environnement et sauvegarder les données
  avant toute évolution destructive.

### Cycle JWT et sécurité des comptes

- L'inscription valide le nom d'utilisateur, l'email et le mot de passe, compare la
  confirmation, puis utilise `set_password()` pour enregistrer un hash.
- La connexion `POST /api/token/` vérifie les identifiants et remet un access token et
  un refresh token. Le rôle serveur est inclus dans la claim `role`.
- `POST /api/token/refresh/` échange un refresh token valide contre un nouvel access
  token. Les jetons doivent être transmis via l'en-tête
  `Authorization: Bearer <access>`.
- `GET /api/auth/me/` retourne le profil et le rôle courant.
- L'inscription ne permet jamais de choisir `is_staff` ni un groupe : un compte créé
  reçoit le rôle `member`. Les administrateurs ajoutent les gestionnaires au groupe
  `contact_managers` via l'admin Django ; les comptes `is_staff` sont également traités
  comme gestionnaires.
- Les permissions DRF vérifient l'utilisateur authentifié et autorisent l'accès global
  aux contacts seulement aux gestionnaires. Les membres voient uniquement leurs propres
  contacts. Ne jamais faire confiance à une claim ou un champ de rôle fourni par le client.

## Exercice pratique livré

Routes :

| Méthode | Route | Accès |
| --- | --- | --- |
| `POST` | `/api/auth/register/` | Public, crée un compte membre |
| `POST` | `/api/token/` | Public, connexion et émission de jetons |
| `POST` | `/api/token/refresh/` | Public avec refresh token valide |
| `GET` | `/api/auth/me/` | Authentifié, profil et rôle |
| `GET`, `POST` | `/api/contacts/` | Authentifié ; filtrage selon rôle |
| `GET`, `PUT`, `PATCH`, `DELETE` | `/api/contacts/{id}/` | Propriétaire ou gestionnaire |

Après inscription, se connecter à `/api/token/` et utiliser l'access token pour les
routes privées. Pour créer un compte gestionnaire dans un environnement de formation,
créer un superutilisateur ou ajouter le compte au groupe `contact_managers` dans
`/admin/`; ne pas exposer cette opération à l'inscription publique.

Vérification locale :

```powershell
.\env\Scripts\python.exe manage.py migrate
.\env\Scripts\python.exe manage.py test contacts
```

Le pilote PostgreSQL `psycopg` est déclaré dans `requirements.txt`. L'API et les tests
fonctionnent également en SQLite sans serveur externe.

## Réinvestissement dans Contacts et Formuloo Market

- Conserver PostgreSQL comme base de données des environnements partagés ; valider les
  migrations en CI et tester les contraintes sur la base de production ciblée.
- Réutiliser les flows d'inscription, connexion, renouvellement et profil pour les
  nouveaux domaines applicatifs.
- Garder la création des rôles et privilèges réservée à l'administration ; appliquer
  les permissions DRF au niveau des vues et filtrer aussi les querysets.
- Pour chaque nouveau rôle, documenter explicitement ses actions autorisées et écrire
  des tests d'accès permis et refusé.

## Definition of Done et suivi

- PostgreSQL configurable et pilote déclaré ; SQLite garde un démarrage autonome.
- Inscription, connexion et renouvellement JWT disponibles.
- Rôles `member` et `contact_manager` attribués et vérifiés côté serveur.
- Tests couvrant inscription, hash du mot de passe, JWT/refresh et accès gestionnaire.
- Les ressources effectivement suivies, le point tuteur/pair et le dépôt dans l'espace
  d'équipe restent à confirmer par le stagiaire.
