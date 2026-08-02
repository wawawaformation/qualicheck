# Documents jury — livrets à remettre

Contrairement au reste de `docs/jury/` (`veille/`, `decisions/`), qui pointe
vers les preuves sans les recopier, ce dossier contient les **livrets
finaux** à remettre au jury pour chaque épreuve (E1 à E5,
`conception/referentiel_competences.md`) : ils synthétisent par nature ce qui
est dispersé ailleurs (code, specs, décisions, `docs/jury/E1_bloc1_criteres_performance.xlsx`...)
en un document de restitution autonome.

## Organisation

- `working/` : brouillons, rédaction en cours ; `working/config/` : templates
  LaTeX propres à ces livrets.
- `epreuvres/E{1..5}/` : un dossier par épreuve, source Markdown + export PDF
  (convention `markdown-pandoc` du projet — mêmes en-têtes pandoc que
  `conception/conception.md`/`referentiel_competences.md`).

**5 livrables au total, pas 6.** Confirmé par la référente certification
(Helena, 2026-07-29) : *« Les livrables attendus par le jury sont au nombre
de 5. Si un même projet est utilisé pour les 5 livrables, le contexte est à
présenter une seule fois au début du premier livrable. »* Le contexte projet
(QualiCheck, référentiel Opquast, personas) ouvre donc directement E1 (§
« Présentation du projet »), condensé pour laisser la place au reste du
budget de pages. Les livrets E2 à E5 n'y reviennent pas ; une phrase de
renvoi vers E1 suffit.

Un montage antérieur avait isolé ce contenu dans un « Livret 0 » séparé.
Abandonné : ce n'est pas ce que le jury attend (`commun/` supprimé le
2026-07-29).

## Pages de garde

Une seule page de garde, définie dans `working/config/jury-livret.tex` :
remplace `\maketitle`, construite depuis le Front Matter Pandoc
(`title`/`subtitle`/`author`/`date`), centrée, encadrée de filets. Commune
aux 5 livrets.

**Devise optionnelle par livret** (ex. « Garbage in, garbage out » pour E1,
pertinente pour un livret sur les données, pas pour les autres). Le
mécanisme `\devise` est vide par défaut dans le template commun ; un livret
qui veut sa propre devise passe un second fichier `--include-in-header`
(ex. `epreuvres/E1/devise.tex`, une seule ligne `\def\devise{...}`) après le
template principal. Le YAML `header-includes:` du `.md` ne fonctionne pas
de façon fiable combiné à `--include-in-header` sur cette version de
Pandoc (testé le 2026-07-29) : la devise disparaissait silencieusement.

## Style de rédaction

Prose destinée à être lue par le jury : pas de tiret cadratin (—), pas de
tournure qui « sonne IA » (incises systématiques, symétries trop nettes).
Préférer un point, une virgule, des deux-points, ou restructurer la phrase.

## Génération du PDF

**Toujours lancer `pandoc` depuis la racine du dépôt.** Les chemins d'image
dans les fichiers Markdown (ex. les annexes `conception/annexes/*.png`) sont
écrits relatifs à la racine, pas au dossier du fichier `.md` — Pandoc résout
les images relatives au répertoire d'où la commande est lancée, pas à
l'emplacement du fichier source (piège rencontré et vérifié en pratique le
2026-07-29).

```bash
pandoc docs/jury/documents_jury/epreuvres/E1/E1.md \
  --pdf-engine=xelatex \
  --include-in-header=docs/jury/documents_jury/working/config/jury-livret.tex \
  --include-in-header=docs/jury/documents_jury/epreuvres/E1/devise.tex \
  --toc --number-sections \
  -o docs/jury/documents_jury/epreuvres/E1/E1.pdf
```

Pour un livret sans devise propre (E2 à E5), omettre le second
`--include-in-header`.

Validé par compilation réelle (`./tmp/jury_livret_test/`, 2026-07-29).

## Budget de pages par épreuve (`conception/certif_deroule.md`)

| Épreuve | Bloc / compétences | Pages | Oral | Évaluation |
| --- | --- | --- | --- | --- |
| E1 | Bloc 1, C1 à C5 | 2 à 5 | 15 min | Rapport + soutenance orale |
| E2 | C6-C8 (veille, service IA) | 15 à 20 | 15 min | Rapport + soutenance orale |
| E3 | C9-C13 (API modèle IA) | 15 à 20 | 20 min | Rapport + soutenance avec démonstration |
| E4 | C14-C19 (analyse du besoin, appli) | 15 à 20 | 20 min | Rapport + soutenance avec démonstration |
| E5 | C20-C21 (monitorage + incident) | 2 à 5 | 10 min | Documentation + soutenance orale |

Structure non imposée par le référentiel, mais conseillée dans l'ordre des
compétences (C1 → C5 pour E1, etc.).

## Règle

Comme pour `docs/jury/decisions/`, un livret n'est finalisé (`epreuvres/`)
que lorsque le contenu source qu'il synthétise existe déjà réellement, pas
de rédaction anticipée sur un chantier non terminé.
