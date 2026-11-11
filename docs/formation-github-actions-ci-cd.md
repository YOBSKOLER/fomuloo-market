# Formation S3 — GitHub Actions et pipeline CI/CD

## Ressources

- [Documentation GitHub Actions](https://docs.github.com/fr/actions)
- [GitHub Actions : Python](https://docs.github.com/fr/actions/automating-builds-and-tests/building-and-testing-python)
- [AWS Elastic Beanstalk : GitHub Actions](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/GettingStarted.DeployApp.html)

Ces notes et l'exercice sont préparés dans le dépôt. Ils ne prétendent pas confirmer
que les ressources ont déjà été suivies ni qu'un déploiement AWS a déjà été exécuté.

## Notes structurées

- Un workflow est un fichier YAML versionné sous `.github/workflows/`.
- Un événement (`push` ou `pull_request`) déclenche le workflow. Les jobs contiennent
  les étapes et peuvent s'exécuter en parallèle ou être liés avec `needs`.
- Les tests et le lint doivent réussir avant le job de déploiement. Ici, un push vers
  `main` déclenche le déploiement seulement si les deux jobs de vérification réussissent.
- Les tests s'exécutent avec pytest et publient un rapport de couverture téléchargeable
  comme artefact GitHub Actions.
- Le lint utilise Ruff avec les règles d'erreurs de syntaxe/structure `E4`, `E7`, `E9`
  et les problèmes de noms/imports `F`, définies explicitement pour garder le même
  résultat sur les postes locaux et dans le runner GitHub.
- Les informations de déploiement varient selon l'environnement. Les valeurs non
  sensibles sont des variables GitHub; l'identité AWS est fédérée via OIDC. Aucun
  identifiant AWS à longue durée n'est écrit dans le code ou les fichiers YAML.
- Un pipeline valide le code et automatise les étapes reproductibles; il ne remplace
  ni la revue de code, ni les tests de bout en bout, ni la configuration d'une base
  de données de production.

## Exercice livré

Le workflow `.github/workflows/ci-cd.yml` :

1. exécute Ruff sur le code applicatif, les tests et les migrations;
2. exécute les tests avec couverture;
3. conserve `coverage.xml` comme artefact;
4. après succès des deux vérifications, déploie sur AWS Elastic Beanstalk quand un
   commit est poussé sur `main`.

Le fichier `Procfile` démarre l'application ASGI avec Uvicorn sur le port 8000.
L'archive déployée contient l'application FastAPI, ses dépendances et les migrations
Alembic, mais pas les tests ni les fichiers locaux de base de données.

### Déclenchement et vérification

Sur GitHub, ouvrir **Actions**, sélectionner **CI/CD**, puis consulter les jobs `Lint`,
`Tests` et, pour un push vers `main`, `Deploy to AWS Elastic Beanstalk`. L'artefact
`coverage-report` est disponible dans les détails du workflow.

Pour tester le workflow sans déployer, ouvrir une pull request vers `main` : seuls
le lint et les tests s'exécutent. Un push ou une fusion sur `main` lance également
le job de déploiement.

## Configuration AWS requise avant le premier déploiement

Dans **Settings > Secrets and variables > Actions** du dépôt GitHub :

| Nom | Type | Contenu |
| --- | --- | --- |
| `AWS_ROLE_TO_ASSUME` | Secret | ARN du rôle IAM de déploiement autorisé par le fournisseur OIDC GitHub |
| `AWS_REGION` | Variable | Région AWS, par exemple `eu-west-3` |
| `EB_APPLICATION_NAME` | Variable | Nom de l'application Elastic Beanstalk déjà créée |
| `EB_ENVIRONMENT_NAME` | Variable | Nom de l'environnement Elastic Beanstalk déjà créé |

Le rôle IAM doit faire confiance au dépôt GitHub et autoriser uniquement les actions
Elastic Beanstalk/S3 nécessaires au dépôt d'une version et à la mise à jour de cet
environnement. Restreindre sa confiance à l'organisation et au dépôt concernés.

Créer au préalable l'application et l'environnement Elastic Beanstalk sur une plateforme
Python compatible, puis configurer une base durable (par exemple PostgreSQL géré) et la
variable d'environnement `DB_URL` dans l'environnement. **Ne pas utiliser SQLite comme
base de production** : son fichier local n'est pas une persistance fiable sur les
instances Elastic Beanstalk. Les identifiants de base doivent rester dans la
configuration sécurisée AWS, jamais dans le dépôt.

Le dépôt local a actuellement son remote `origin` sur GitLab. GitHub Actions ne se
déclenchera que si le code est aussi présent dans un dépôt GitHub. Le pipeline GitLab
existant reste distinct et n'est pas remplacé par ce workflow.

## Réinvestissement dans le mini-projet « API Authentifiée : Gestionnaire de Tâches avec JWT »

- Exécuter lint et tests API sur chaque pull request avant la fusion.
- Tester l'authentification JWT, les rôles/permissions, les codes `401`/`403`, les
  migrations et les parcours CRUD avant tout déploiement.
- N'autoriser le déploiement qu'après fusion vers la branche principale protégée.
- Stocker les clés JWT, la chaîne de connexion DB et les autres secrets dans le
  gestionnaire de secrets de la plateforme, jamais dans Git ou les logs du pipeline.
- Ajouter des tests de santé et un contrôle post-déploiement avant de considérer la
  mise en production terminée.

## Suivi de formation

Le workflow et l'exercice sont présents dans le dépôt. Le suivi réel des ressources,
la configuration AWS, le premier déploiement, le point tuteur/pair et la publication
dans l'espace d'équipe restent à confirmer par le stagiaire.
