# Guide d'utilisation des codes pays

## Format normalisé : ISO 3166-1 alpha-2

Les codes pays suivent la norme internationale **ISO 3166-1 alpha-2**, qui utilise 2 lettres majuscules pour identifier chaque pays.

## Exemples de codes pays

| Code | Pays |
|------|------|
| FR   | France |
| US   | États-Unis |
| GB   | Royaume-Uni |
| DE   | Allemagne |
| ES   | Espagne |
| IT   | Italie |
| JP   | Japon |
| CA   | Canada |
| AU   | Australie |
| BR   | Brésil |

## Utilisation de l'API

### 1. Obtenir la liste complète des pays disponibles

```bash
curl http://localhost:5001/api/countries
```

Réponse :
```json
[
  {"code": "AD", "name": "Andorre"},
  {"code": "AE", "name": "Émirats Arabes Unis"},
  {"code": "AF", "name": "Afghanistan"},
  ...
  {"code": "FR", "name": "France"},
  ...
]
```

### 2. Mettre à jour le pays d'un artiste

```bash
curl -X PATCH http://localhost:5001/api/artists/123 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"country": "FR"}'
```

Réponse :
```json
{
  "id": 123,
  "name": "Daft Punk",
  "discogs_id": 1234,
  "country": "FR",
  "country_name": "France"
}
```

### 3. Récupérer un artiste avec son pays

```bash
curl http://localhost:5001/api/artists/123
```

Réponse :
```json
{
  "id": 123,
  "name": "Daft Punk",
  "discogs_id": 1234,
  "country": "FR",
  "country_name": "France"
}
```

### 4. Lister tous les artistes

```bash
curl http://localhost:5001/api/artists
```

Réponse :
```json
[
  {
    "id": 1,
    "name": "The Beatles",
    "discogs_id": 82730,
    "country": "GB",
    "country_name": "Royaume-Uni"
  },
  {
    "id": 2,
    "name": "Pink Floyd",
    "discogs_id": 45467,
    "country": "GB",
    "country_name": "Royaume-Uni"
  },
  {
    "id": 3,
    "name": "Nirvana",
    "discogs_id": 251,
    "country": "US",
    "country_name": "États-Unis"
  }
]
```

## Validation automatique

L'API valide automatiquement les codes pays :

### ✅ Codes valides
- `"FR"`, `"fr"`, `"  FR  "` → Normalisé en `"FR"`
- `"US"`, `"GB"`, `"DE"`, etc.
- `null` ou vide → Accepté (pays non renseigné)

### ❌ Codes invalides
- `"FRA"` → Erreur : doit faire 2 caractères
- `"XX"` → Erreur : code inexistant
- `"France"` → Erreur : doit être un code, pas un nom
- `"1"`, `"123"` → Erreur : doit être alphabétique

Message d'erreur :
```json
{
  "detail": [
    {
      "loc": ["body", "country"],
      "msg": "Code pays invalide : 'FRA'. Doit être un code ISO 3166-1 alpha-2 (ex: FR, US, GB)",
      "type": "value_error"
    }
  ]
}
```

## Avantages de cette normalisation

1. **Standard international** : Compatible avec toutes les APIs et bibliothèques
2. **Compact** : Seulement 2 caractères au lieu de noms longs
3. **Validation stricte** : Empêche les erreurs de saisie
4. **Multilingue** : Le code est universel, seul le nom change selon la langue
5. **Performance** : Index plus rapide qu'avec des chaînes longues
6. **Cohérence** : Un seul code par pays, pas d'ambiguïté

## Cas particuliers

- **Royaume-Uni** : `GB` (Great Britain), pas `UK`
- **Grèce** : `GR` (Greece)
- **Corée du Sud** : `KR` (Korea, Republic of)
- **Corée du Nord** : `KP` (Korea, People's Republic of)
