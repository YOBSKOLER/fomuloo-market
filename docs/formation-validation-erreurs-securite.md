# Formation S2 — Validation, erreurs et sécurité de base

## Objectifs et ressources

Cette synthèse accompagne les ressources du ticket T3 ; elle ne prétend pas prouver
que les cours externes ont été suivis :

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Sécurité Django](https://docs.djangoproject.com/fr/5.0/topics/security/)
- [Serializers DRF](https://www.django-rest-framework.org/api-guide/serializers/)

## Notes structurées

### Validation des entrées avec les serializers DRF

- Un serializer vérifie le type, le format, les champs obligatoires et les règles
  métier avant que la vue ne sauvegarde les données.
- Utiliser `validate_<field>()` pour une règle sur un champ et `validate()` pour une
  règle portant sur plusieurs champs.
- Les données du client ne doivent pas décider du propriétaire ou des champs internes :
  le propriétaire du contact est défini dans `perform_create()` à partir de l'utilisateur
  authentifié.
- Une validation retourne une réponse `400 Bad Request`; les contraintes de base de
  données restent nécessaires pour protéger l'intégrité, notamment contre les courses
  concurrentes.

### Gestion des erreurs

- Le gestionnaire central configuré dans `REST_FRAMEWORK["EXCEPTION_HANDLER"]` transforme
  les exceptions prises en charge par DRF en une enveloppe JSON stable.
- Exemple de validation : `{"error":{"code":"validation_error","message":"Les données
  fournies sont invalides.","details":{"email":["Saisissez une adresse e-mail valide."]}}}`.
- Les erreurs d'authentification, permissions et ressources absentes suivent le même
  format, tout en gardant leurs codes HTTP usuels (`401`, `403`, `404`).
- Les erreurs inattendues ne sont pas masquées par le gestionnaire : elles sont laissées
  à la gestion standard Django/DRF et ne doivent pas exposer de trace en production
  (`DEBUG=false`).

### Protections et limites

- `SecurityMiddleware`, `CsrfViewMiddleware` et `XFrameOptionsMiddleware` sont activés.
  Les headers `nosniff`, `Referrer-Policy` et `X-Frame-Options: DENY` sont également
  configurés.
- Le middleware CSRF protège les vues utilisant l'authentification par cookies/sessions
  et l'administration Django. Cette API utilise JWT dans l'en-tête
  `Authorization: Bearer ...`; ne pas stocker ce jeton dans un cookie automatiquement
  envoyé par le navigateur sans protection CSRF adaptée.
- Les requêtes ORM utilisées ici passent par les paramètres de l'ORM, et non par du SQL
  construit par concaténation. Ne jamais interpoler des valeurs client dans du SQL brut.
- Une API JSON ne doit pas interpréter une valeur utilisateur comme du HTML. Le backend
  ne prétend pas « nettoyer » toutes les chaînes contre XSS : l'interface cliente doit
  encoder le texte au moment de l'affichage et éviter toute insertion HTML non sûre.
- En production, utiliser HTTPS, secrets d'environnement, `DEBUG=false` et des hôtes
  autorisés. Activer redirection HTTPS et HSTS uniquement lorsque le domaine et le
  reverse proxy sont correctement configurés.

## Exercice pratique et résultat

Sur l'API Contacts, l'exercice vérifie les emails invalides et doublons, l'enveloppe
d'erreur `400`, l'authentification obligatoire, les headers de sécurité et le traitement
par l'ORM d'une chaîne contenant une syntaxe ressemblant à du SQL. Les tests vérifient
que cette chaîne reste une valeur texte et que la table reste présente.

Commandes de vérification depuis la racine :

```powershell
.\env\Scripts\python.exe manage.py check
.\env\Scripts\python.exe manage.py test contacts
```

## Réinvestissement dans le mini-projet Contacts / Formuloo Market

- Implémenter les règles de validation dans les serializers et les contraintes dans les
  modèles/migrations.
- Conserver l'affectation serveur du propriétaire et les querysets limités à l'utilisateur.
- Utiliser le format centralisé d'erreur pour que les clients API traitent uniformément
  les erreurs de validation, authentification et absence de ressource.
- Tester les entrées invalides, les accès entre comptes et les headers à chaque évolution.
- Pour chaque nouvel endpoint, choisir explicitement l'authentification et vérifier si
  elle repose sur un mécanisme cookie nécessitant CSRF.

## Definition of Done et suivi

- Serializer DRF : validation d'email et doublons conservés, cas invalides testés.
- Gestionnaire d'exception : format d'erreur centralisé et couvert par les tests.
- Protections Django : middlewares existants confirmés, headers de base configurés et testés.
- Notes liées au mini-projet produites dans ce dépôt.
- Le suivi effectif des ressources, le point tuteur/pair et le dépôt dans l'espace équipe
  restent à confirmer par le stagiaire.
