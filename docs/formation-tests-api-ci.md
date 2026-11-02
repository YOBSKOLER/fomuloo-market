# Formation S2 — Tests API et intégration continue

## Objectifs et ressources

Cette synthèse accompagne les documentations citées dans le ticket T4. Elle ne prétend
pas prouver que les ressources externes ont été suivies :

- [pytest-django](https://pytest-django.readthedocs.io/)
- [Tests Django REST Framework](https://www.django-rest-framework.org/api-guide/testing/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [GitLab CI/CD](https://docs.gitlab.com/ee/ci/)

## Notes structurées

### Tests unitaires et tests d'intégration

- Un test unitaire isole une fonction ou une règle métier; un test d'intégration vérifie
  plusieurs composants ensemble. Un test API DRF exerce le routage, la vue, les
  permissions, le serializer et la base de test via le client HTTP DRF.
- `APITestCase` fournit assertions et client API dans une classe unittest. `APIClient`
  permet les requêtes HTTP en tests pytest fonctionnels; `force_authenticate()` est
  pratique pour isoler les permissions, tandis qu'un vrai JWT vérifie aussi le flux
  d'authentification.
- `pytest-django` prépare Django et la base de test. L'accès ORM depuis un test pytest
  nécessite `@pytest.mark.django_db` ou la fixture `db`.
- Les tests doivent être indépendants, déterministes et vérifier le comportement visible
  (statut HTTP, enveloppe JSON, données persistées, permissions), pas seulement appeler
  des fonctions internes.
- Paramétrer les cas d'entrée semblables évite la duplication tout en produisant un
  résultat de test par cas. Les noms de test doivent décrire le comportement attendu.

### Couverture de code

- `pytest-cov` exécute les tests avec Coverage.py et rapporte les lignes couvertes ou non.
- Le fichier `.coveragerc` exclut les modules de test et les migrations du calcul afin
  que le pourcentage représente le code applicatif.
- Le pourcentage indique quels chemins de code les tests ont exercés; il ne prouve pas
  à lui seul la qualité des assertions. Couvrir les cas de succès, erreurs, règles de
  permission et limites métier reste essentiel.
- Le rapport XML Cobertura est destiné à GitLab; le rapport HTML facilite l'inspection
  locale des lignes manquantes.

### Intégration continue GitLab

- `.gitlab-ci.yml` déclare une image, des étapes et des jobs. À chaque pipeline, le job
  de test installe les dépendances, vérifie la configuration et les migrations, puis
  exécute toute la suite pytest avec couverture.
- Un job échoué bloque l'étape et rend l'erreur visible avant intégration. Le rapport
  Cobertura et le rapport HTML sont conservés comme artefacts, même si les tests
  échouent.
- Les données de test sont éphémères; aucune base de production ni secret réel ne doit
  être nécessaire au job.

## Exercice pratique réalisé : tester l'API Contacts

La suite fonctionnelle `contacts/test_pytest_api.py` utilise pytest-django et
`rest_framework.test.APIClient`. Elle comprend plus de vingt cas couvrant notamment :

- accès anonyme et authentifié, liste filtrée par propriétaire et rôle gestionnaire;
- création avec propriétaire déterminé côté serveur, lecture, mise à jour et suppression;
- données requises/facultatives, email invalide ou dupliqué, champs en lecture seule;
- inscription, validation de mot de passe, profil, émission et renouvellement JWT.

Les tests existants de `contacts/tests.py` utilisent également `APITestCase` et restent
inclus dans la découverte pytest configurée par `pytest.ini`.

### Exécuter localement

Installer les dépendances de développement puis lancer les tests et créer les rapports :

```powershell
.\env\Scripts\python.exe -m pip install -r requirements-dev.txt
.\env\Scripts\python.exe -m pytest --cov=contacts --cov-report=term-missing --cov-report=xml:coverage.xml --cov-report=html:htmlcov
```

Le rapport lisible en terminal est affiché immédiatement. `coverage.xml` est au format
Cobertura; le rapport détaillé s'ouvre dans `htmlcov/index.html`.

### Vérification en CI

Le job `api-tests` du pipeline GitLab lance `manage.py check`, vérifie l'absence de
migrations non enregistrées et exécute la suite pytest avec couverture. GitLab reçoit
le pourcentage de couverture et les rapports Cobertura/HTML comme artefacts du job.

## Réinvestissement dans le mini-projet « API REST : Gestionnaire de Contacts »

- Pour chaque route CRUD, garder des tests de succès et de validation, puis vérifier les
  règles d'accès entre deux comptes afin qu'un contact ne soit jamais exposé à un autre
  membre.
- Ajouter des tests aux nouveaux champs et règles métiers (format email/téléphone,
  recherche, pagination ou catégories), y compris les erreurs attendues et les limites.
- Garder des fixtures de données réutilisables, mais créer les objets dans chaque test
  afin que les tests n'échangent pas d'état.
- Faire exécuter la suite et les migrations par la CI sur chaque changement; demander une
  relecture si un changement de permission modifie la frontière d'accès.
- Le même schéma s'applique aux futures apps Formuloo Market : tests ciblés de modèles
  et serializers, tests d'intégration des endpoints, puis suite complète en CI.

## Definition of Done et suivi

- La suite pytest inclut les tests API `APITestCase` préexistants et plus de vingt cas
  pytest fonctionnels.
- Les commandes de test produisent des rapports terminal, XML Cobertura et HTML.
- Le pipeline GitLab exécute les contrôles Django, les migrations et pytest-cov.
- Les notes font le lien avec le mini-projet Contacts.
- La lecture effective des ressources, le point tuteur/pair et le dépôt dans un espace
  externe restent à confirmer par le stagiaire.
