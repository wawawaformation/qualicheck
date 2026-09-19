# Tool `valider_marquage`

Sous-capacité de la stratégie **`statique`** (ex. règle 104, « appel
valide à une icône de favori », règle 214, « contrôle d'intégrité des
ressources tierces ») : validation syntaxique déterministe (HTML/CSS
conforme aux spécifications W3C), distincte de la simple lecture du
contenu (`lire_url`).

## Docstring

Valide la syntaxe HTML ou CSS d'une page par rapport aux spécifications
W3C, et retourne la liste des erreurs trouvées. À utiliser quand la
question porte sur la conformité du marquage lui-même (balises mal
fermées, attributs invalides, etc.), pas sur son contenu.

Pas encore implémenté — contrat de tool posé ici.

## Paramètres d'entrée

| Paramètre | Type | Obligatoire | Description |
|---|---|---|---|
| `url` | string | oui | Page à valider |

## Sortie

```json
{ "valide": false, "erreurs": ["ligne 42 : balise <div> non fermée"] }
```

ou, si la validation échoue (page inaccessible) :

```json
{ "erreur": "page inaccessible" }
```

- `valide: true` avec `erreurs: []` : marquage conforme.
