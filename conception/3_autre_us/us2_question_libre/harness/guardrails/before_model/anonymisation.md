# Avant chaque appel au modèle

**Anonymise ce qui part vers le modèle** — la question et tout contenu de
page ramené par un outil (URL, capture d'écran).

À chaque appel, pas juste au début : un outil peut ramener du contenu en
cours de route.

Pourquoi systématique : aucun de nos fournisseurs (Azure, Infomaniak,
Ollama) n'est notre propre infrastructure — le contenu sort toujours vers
un tiers, quel que soit l'environnement.

Reste ouvert : quoi anonymiser précisément, et comment sur une image.
