# Formuloo Market

**Parcours** : Formuloo Backend  
**Niveau** : N3 — Licence  
**Branche de livraison** : ta branche `prenom-nom`

## Convention de branchement — OBLIGATOIRE

```bash
git clone https://gitlab.formuloo.com/formuloo-backend/formuloo-market.git
git checkout develop
git pull origin develop
git checkout -b prenom-nom   # ex: jean-dupont, sans accents, minuscules
```

Pour chaque feature ou tâche, crée une sous-branche :
```bash
git checkout -b prenom-nom/feature/nom-feature
# ... travail ...
git checkout prenom-nom
git merge prenom-nom/feature/nom-feature
git push origin prenom-nom
```

**Ta branche `prenom-nom` est ta branche de livraison — c'est ce qui sera évalué.**  
Ne jamais pousser directement sur `develop` ou `main`.

## Livrable de formation S2 — Django REST Framework

Le projet inclut une API d'exercice de gestion de contacts dans l'app `contacts` :
CRUD authentifié par JWT, isolation des données par utilisateur, validation via
serializer DRF et tests API. Les notes, commandes de démarrage et le lien avec le
mini-projet sont dans [docs/formation-django-drf.md](docs/formation-django-drf.md).

SQLite est configuré par défaut pour le démarrage local. Les variables de configuration
PostgreSQL sont documentées dans les notes de formation. Le pipeline GitLab exécute
les contrôles Django, vérifie l'état des migrations et lance les tests pytest avec
rapport de couverture.

Les notes du ticket T3 sur la validation DRF, le format d'erreur API et les protections
de sécurité de base sont dans [docs/formation-validation-erreurs-securite.md](docs/formation-validation-erreurs-securite.md).
Les routes d'inscription, de profil et les rôles JWT du ticket T2 sont documentés dans
[docs/formation-postgresql-jwt.md](docs/formation-postgresql-jwt.md).

La suite pytest, le rapport pytest-cov, le pipeline GitLab CI et leur réinvestissement
dans le mini-projet Contacts sont documentés dans
[docs/formation-tests-api-ci.md](docs/formation-tests-api-ci.md).
