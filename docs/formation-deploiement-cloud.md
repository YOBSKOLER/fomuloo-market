# Formation S3 — Déploiement cloud et variables d'environnement

## Objectifs et ressources

- [AWS Elastic Beanstalk](https://docs.aws.amazon.com/elasticbeanstalk/)
- [AWS App Runner](https://docs.aws.amazon.com/apprunner/)
- [AWS Elastic Beanstalk : variables d'environnement](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/environments-cfg-softwaresettings.html)
- [AWS Elastic Beanstalk : logs et CloudWatch](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/using-features.logging.html)

Le dépôt utilise Elastic Beanstalk, choisi dans le ticket précédent. Le code et les
vérifications sont préparés; le compte AWS, les environnements et les déploiements
effectifs restent à configurer et à réaliser.

## Notes structurées

- Une configuration diffère selon l'environnement (local, staging, production). Le code
  reste le même; les URL de base et paramètres opérationnels changent.
- Les valeurs de configuration sont injectées à l'exécution, pas inscrites dans le code.
  La configuration locale `.env` est ignorée par Git. Ne jamais commiter une clé, un mot
  de passe ni une URL de base contenant un secret.
- La staging sert à valider un déploiement proche de la production sans exposer les
  utilisateurs finaux. La production est mise à jour seulement après validation et
  approbation.
- Elastic Beanstalk héberge les instances de l'application. La base de données doit être
  persistante et indépendante, par exemple Amazon RDS PostgreSQL; le fichier SQLite local
  ne convient pas à plusieurs instances ou à un remplacement d'instance.
- Le rôle IAM GitHub OIDC évite d'enregistrer des clés AWS permanentes dans les secrets
  GitHub. Limiter sa confiance au dépôt et aux environnements autorisés.
- Les sondes de santé disent si le processus tourne (`/health/live`) et si la base peut
  accepter du trafic (`/health/ready`). Elles ne remplacent pas les logs, alarmes, tests
  métier ou une supervision 24/7.
- Les logs applicatifs et la santé Elastic Beanstalk sont consultables via le tableau de
  bord AWS. CloudWatch Logs permet de conserver et rechercher les logs; des alarmes sur
  erreurs HTTP, CPU ou santé peuvent être ajoutées selon les objectifs du service.

## Exercice livré dans le dépôt

### Contrôles de santé

- `GET /health/live` retourne `200 {"status":"ok"}` tant que l'application répond.
- `GET /health/ready` exécute `SELECT 1` sur la base et retourne le même résultat si la
  connexion fonctionne; sinon, l'API retourne `503` sans exposer les détails de connexion.
- Le workflow vérifie `/health/ready` après chaque déploiement staging ou production.
- Les tests correspondants sont dans `tests/test_deployment_health.py`.

### Pipeline staging / production

Le workflow `.github/workflows/ci-cd.yml` :

1. lance Ruff et pytest sur les push et pull requests;
2. déploie vers `staging` automatiquement après un push validé sur `main`;
3. permet de lancer `production` manuellement depuis **Actions > CI/CD > Run workflow**,
   en choisissant `production` et la branche `main`;
4. attend la réussite des tests, demande l'approbation de l'environnement GitHub
   `production` si des reviewers sont configurés, puis vérifie `/health/ready`.

Les versions staging et production doivent être des environnements Elastic Beanstalk
distincts. Configurez dans les paramètres de chaque environnement GitHub (`staging` et
`production`) les variables `AWS_REGION`, `EB_APPLICATION_NAME` et `EB_ENVIRONMENT_NAME`,
et le secret `AWS_ROLE_TO_ASSUME`. Les noms de variables sont les mêmes, mais leurs
valeurs peuvent différer par environnement.

Dans **Settings > Environments > production**, ajouter au moins un reviewer obligatoire
et limiter les branches de déploiement à `main`. Pour `staging`, autoriser uniquement
`main`. Les reviewers ne doivent pas être la personne qui déclenche le déploiement si
les règles de protection GitHub l'interdisent.

Le rôle IAM doit faire confiance à OIDC avec l'audience `sts.amazonaws.com` et un sujet
restreint à chaque environnement, sous la forme :

```text
repo:OWNER/REPOSITORY:environment:staging
repo:OWNER/REPOSITORY:environment:production
```

Il lui faut uniquement les permissions nécessaires pour obtenir le bucket d'artefacts
Elastic Beanstalk, téléverser le bundle vers ce bucket, créer une version et mettre à
jour l'environnement correspondant. Le rôle ne doit pas avoir accès aux environnements
non concernés.

### Préparer chaque environnement AWS

1. Créer une application et deux environnements Elastic Beanstalk distincts, staging et
   production, sur une plateforme Python Linux compatible.
2. Configurer un RDS PostgreSQL durable (idéalement séparé par environnement), le réseau,
   les règles de sécurité réseau et les sauvegardes.
3. Configurer `DB_URL` dans les propriétés d'environnement Elastic Beanstalk pour
   chaque environnement, avec un compte DB limité à la base correspondante. Restreindre
   fortement les permissions IAM et console sur ces propriétés; pour une gestion plus
   stricte, stocker le secret dans AWS Secrets Manager et organiser sa rotation.
4. Avant le premier trafic, appliquer `alembic upgrade head` contre la base ciblée depuis
   un poste ou une tâche d'administration sécurisée. Vérifier la connexion et les
   migrations d'abord sur staging. Le workflow ne lance pas encore Alembic sur les bases
   distantes.
5. Activer la santé améliorée Elastic Beanstalk et configurer le chemin de santé
   `/health/ready`. Activer le streaming des logs vers CloudWatch Logs, la rétention,
   ainsi que des alarmes adaptées (par exemple environnement dégradé et taux d'erreurs).
6. Vérifier le domaine HTTPS et les certificats avant de transmettre une URL aux
   utilisateurs. Le contrôle automatisé actuel utilise le CNAME Elastic Beanstalk en
   HTTP; configurez TLS/domaine HTTPS pour les accès réels.

Ne pas utiliser les données personnelles de production dans staging. Utiliser des
données synthétiques et des identifiants distincts.

## Procédure de déploiement

1. Ouvrir une pull request vers `main`; vérifier les jobs Lint et Tests.
2. Fusionner vers `main`; dans Actions, vérifier que le déploiement staging et la sonde
   de santé réussissent.
3. Tester le staging, consulter les logs et métriques CloudWatch, puis approuver la
   mise en production.
4. Dans **Actions > CI/CD > Run workflow**, sélectionner `main` et la cible `production`.
5. Après approbation, confirmer le succès du déploiement et du contrôle de santé; vérifier
   ensuite `/docs` et un parcours API fonctionnel.
6. En cas d'échec, consulter les logs du job GitHub et les événements/logs Elastic
   Beanstalk. Restaurer la version précédente via Elastic Beanstalk si nécessaire.

## Réinvestissement dans le mini-projet « API Authentifiée : Gestionnaire de Tâches avec JWT »

- Utiliser des environnements distincts et des bases séparées pour staging et production.
- Configurer `DB_URL`, `JWT_SECRET_KEY`, l'expiration des tokens et les origines CORS
  sans valeur secrète dans Git.
- Restreindre les permissions du rôle de déploiement et des comptes DB.
- Vérifier après déploiement l'authentification, les codes `401`/`403`, les migrations et
  les parcours CRUD avec des comptes de test.
- Surveiller les erreurs, latences et disponibilités; ne jamais journaliser les mots de
  passe, tokens JWT, en-têtes `Authorization` ou chaînes de connexion.

## Suivi et limites du livrable

Le code des sondes, les tests, le workflow à deux environnements et cette synthèse sont
préparés. La création AWS, la saisie des variables/secrets, l'approbation GitHub, les
tests sur staging/production, la consultation CloudWatch, le suivi des ressources et le
point tuteur/pair sont des opérations externes qui restent à effectuer.
