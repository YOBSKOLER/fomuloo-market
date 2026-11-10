# Changelog

Les changements notables de l'API sont documentés ici. Le versionnement des routes suit
`/api/vN`; les chemins historiques sans préfixe restent temporairement disponibles mais
ne sont pas exposés dans le schéma OpenAPI.

## [2.0.0] - 2026-11-10

### Ajouté

- Contrats versionnés pour toutes les opérations de contacts sous `/api/v1` et `/api/v2`.
- OpenAPI/Swagger documente explicitement les deux versions; accès sur `/docs` et JSON
  sur `/openapi.json`.
- Les réponses v2 ajoutent le champ calculé `nom_complet`; les réponses v1 restent
  compatibles avec le contrat initial.
- Documentation de formation S3 et tests de contrat des versions.

### Compatibilité

- Les routes historiques `/contacts...` sont conservées provisoirement en alias cachés du
  schéma OpenAPI. Les nouveaux clients doivent utiliser `/api/v1` ou `/api/v2`.

## [1.0.0] - 2026-11-05

### Ajouter

- API Contacts CRUD avec recherche, pagination, validation email, groupe et UUID.
- Routes initiales sans préfixe de version.
