# Fiche psql — pour un habitué de MySQL

## Principe général

Les commandes psql commencent par `\` (backslash), pas par un mot-clé SQL. Elles ne sont **pas** du SQL — c'est le client `psql` qui les interprète localement, jamais envoyées au serveur.

Équivalent MySQL : le shell `mysql` a aussi des commandes courtes (`\s`, `\q`...) mais MySQL couvre surtout via des requêtes SQL (`SHOW TABLES`). PostgreSQL fait l'inverse : tout passe par `\`.

---

## Table de correspondance MySQL → psql

| MySQL | psql | Résultat |
|---|---|---|
| `SHOW DATABASES;` | `\l` | Liste les bases |
| `USE nom_base;` | `\c nom_base` | Change de base |
| `SHOW TABLES;` | `\dt` | Liste les tables |
| `DESCRIBE table;` | `\d table` | Structure d'une table (colonnes, types, contraintes) |
| `SHOW CREATE TABLE table;` | `\d+ table` | Structure détaillée (+ taille, commentaires) |
| `SHOW COLUMNS FROM table;` | `\d table` | Idem `DESCRIBE` |
| `SHOW INDEX FROM table;` | `\di` ou `\d table` (les index apparaissent en bas) | Liste les index |
| `exit` / `quit` | `\q` | Quitter psql |
| `SELECT USER();` | `\conninfo` | Infos de connexion (user, base, host) |
| — | `\du` | Liste les utilisateurs/rôles |
| — | `\dn` | Liste les schémas |
| — | `\df` | Liste les fonctions |
| — | `\x` | Bascule affichage horizontal ↔ vertical (très utile pour les lignes larges) |

---

## Commandes spécifiques QualiCheck (utiles pour ce projet)

```sql
-- Voir toutes les tables du référentiel Opquast + cœur métier
\dt

-- Structure de la table regle (colonnes, FK, contraintes UNIQUE/NOT NULL)
\d regle

-- Voir les contraintes en détail (UNIQUE, FK...)
\d+ regle

-- Compter les règles en base
SELECT COUNT(*) FROM regle;

-- Voir les 10 premières règles avec leur thème
SELECT r.numero, r.intitule, t.theme
FROM regle r
JOIN theme t ON r.theme_id = t.id
ORDER BY r.numero
LIMIT 10;

-- Vérifier l'extension pgvector est bien active
\dx

-- Voir l'index HNSW sur regle.embedding
\di regle*
```

---

## Astuces psql qui n'existent pas (ou différemment) en MySQL

- **`\x`** : bascule l'affichage vertical (une colonne par ligne) — très utile quand une table a beaucoup de colonnes larges (comme `regle` avec `guide_analyse` en `TEXT`). Tape `\x` une fois pour activer, encore une fois pour désactiver.
- **`\timing`** : affiche le temps d'exécution de chaque requête (équivalent MySQL : rien de natif, il faut `SET profiling = 1`).
- **Auto-complétion** : Tab fonctionne sur les noms de tables/colonnes, comme dans MySQL.
- **Historique** : flèches haut/bas, comme MySQL.
- **`\e`** : ouvre ton éditeur ($EDITOR) pour composer une requête longue, puis l'exécute à la fermeture — pas d'équivalent direct en MySQL CLI.

---

## Différence de syntaxe SQL à connaître (pas psql, mais PostgreSQL vs MySQL)

- **Guillemets** : MySQL tolère `"..."` pour les chaînes ; PostgreSQL réserve `"..."` aux identifiants (noms de colonnes/tables) et `'...'` pour les chaînes. `SELECT * FROM regle WHERE theme = "Contenus"` → erreur en PostgreSQL, il faut `'Contenus'`.
- **`LIMIT`** : identique dans les deux.
- **Auto-increment** : MySQL `AUTO_INCREMENT`, PostgreSQL `SERIAL` (déjà vu dans le MLD du projet).
- **Booléens** : PostgreSQL a un vrai type `BOOLEAN` (`true`/`false`), MySQL utilise souvent `TINYINT(1)`.

---

## Quitter proprement

```
\q
```

(pas `exit`, pas `quit` tout court — bien que `quit` fonctionne aussi comme alias dans les versions récentes)
