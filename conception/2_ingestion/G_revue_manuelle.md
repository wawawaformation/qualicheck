# Revue manuelle des classifications LLM

> Spec d'incrément, courte : la plupart des décisions ont été prises en
> discussion directe avant rédaction, pas via un cycle de brainstorming complet.
> Indépendante du chantier 3 (ré-ingestion réelle) — n'affecte aucun champ lu ou
> écrit par le pipeline d'ingestion. À valider avant implémentation.
>
> Date : 2026-07-25

## 1. Problème

La revue manuelle des classifications `strategie_analyse` (celle qui a produit
`docs/problemes_rencontres/ingestion/3_recommandations_v4.md` pour la V3)
n'existe que sous forme d'un document Markdown statique, déconnecté des lignes
réelles de `regle`. Impossible de savoir, en base, si une règle donnée a été
revue, quand, et avec quel verdict — même angle mort que celui déjà résolu pour
la provenance LLM (spec E), mais côté validation humaine plutôt que génération
automatique.

## 2. Principe directeur

**Même famille que les colonnes de provenance de la spec E** (`llm_model`,
`prompt_version`, `created_at`, `updated_at`) : métadonnée de pipeline, pas
vocabulaire du domaine Opquast. Le test de nommage (spec E §7 : *un auditeur
qualité prononcerait-il ce mot en parlant de son métier ?*) tranche en anglais
ici — cette revue porte sur la qualité de l'enrichissement LLM en amont de
l'audit, pas sur l'audit web lui-même.

**Aucune écriture par le pipeline.** Ces colonnes ne sont renseignées que
manuellement (par David, via `psql` ou un futur outil), jamais par
`llm_client.py`, `stockage.py`, ou `EnrichedRule`. Une ré-ingestion future ne
les efface pas (aucun code ne les mentionne), mais ne les invalide pas non plus
automatiquement si la classification change — limite assumée, pas résolue ici
(cf. §5).

## 3. Décisions

| Point | Décision |
| --- | --- |
| Colonnes ajoutées | `reviewed_at` (DateTime, nullable), `review_status` (String, nullable, vocabulaire fermé), `review_note` (Text, nullable) |
| Vocabulaire de `review_status` | Fermé : `valide`, `a_revoir`, `invalide` — discipline portée par convention, pas de contrainte DB (cohérent avec `strategie_analyse`, qui n'a pas non plus de `CHECK` ou d'enum en base) |
| Rôle de `review_note` | Texte libre, pour noter ce qui cloche/pourrait être amélioré sur une règle donnée — matière première d'un futur script de réécriture ciblée (hors périmètre, §5), même logique que `constat.feedback_auditeur` pour la boucle US1/US2 |
| Renseignement | Manuel uniquement (`psql` pour l'instant). Aucun champ Pydantic (`EnrichedRule`) ni logique dans `stockage.py`/`llm_client.py` |
| Emplacement | Sur `regle` directement (pas de table séparée) — un review = un état courant par règle, pas un historique multi-valué à ce stade |

## 4. Modifications

### 4.1 `app/models/referentiel.py`

Ajout sur `Regle`, après `updated_at` :

```python
    reviewed_at = Column(DateTime, nullable=True)
    review_status = Column(String(16), nullable=True)
    review_note = Column(Text, nullable=True)
```

(`String(16)` suffit largement pour `valide`/`a_revoir`/`invalide` — le plus
long, `a_revoir`, fait 8 caractères.)

### 4.2 Migration Alembic `0010_*`

- `upgrade` : 3 `add_column`, toutes nullables.
- `downgrade` : 3 `drop_column`, symétrique.
- Aucune donnée existante à migrer — toutes les lignes actuelles passent à
  `NULL` sur les 3 colonnes (aucune règle n'a encore été revue selon ce
  nouveau schéma).

### 4.3 `conception/2_ingestion/MLD_qualicheck.md` et `conception/annexes/MLD_qualicheck.md`

Ajout des 3 colonnes dans le bloc `regle`, à la suite des colonnes de
provenance déjà documentées (spec E).

## 5. Hors périmètre (YAGNI)

- **Script de réécriture ciblée par LLM** (utilisant `review_note` comme
  contexte pour ré-enrichir uniquement les règles `a_revoir`/`invalide`) —
  reporté explicitement : construire ce script maintenant serait spéculatif,
  aucune règle n'ayant encore de vrai `review_note` à ce stade. À reprendre
  après le chantier 3 et un premier passage de revue manuelle réel.
- **Invalidation automatique d'une revue après ré-ingestion** — limite
  assumée (§2), non résolue. Si une classification change après une nouvelle
  ré-ingestion, `reviewed_at`/`review_status`/`review_note` restent en l'état
  jusqu'à ce qu'un humain les remette à jour.
- **Contrainte `CHECK` ou enum PostgreSQL sur `review_status`** — cohérent
  avec le choix déjà fait pour `strategie_analyse` (discipline de vocabulaire
  portée par convention, pas par la base).
- **Table d'historique des revues** — un seul état courant par règle suffit
  pour l'instant (§3).

## 6. Validation

1. Migration 0010 up/down OK, aucune donnée existante perdue sur les colonnes
   pré-existantes
2. Les 3 nouvelles colonnes existent, toutes nullables
3. `pytest`/`ruff` restent verts
4. `grep -rn "review_status\|review_note\|reviewed_at" app/ingestion/` ne
   retourne rien — confirme qu'aucun code du pipeline ne les touche (§2)
