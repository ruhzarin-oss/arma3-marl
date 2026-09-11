# Catalogue des episodes CHACAL

Genere par `outils/catalogue.py` le 2026-09-11 11:44. **Ne pas editer a la main** : il est
regenere apres chaque run (file3.sh) et chaque nuit (sauver.sh).

- **143 episodes**, lus depuis 196 journaux (13 sans ligne FINI ignores).
- Un episode = une ligne ; `episodes.csv` pour un tableur, `episodes.jsonl` pour un programme.
- Le journal complet de chaque episode est dans la colonne `source` ; ses tables (etat de chaque homme
  toutes les ~2 s, perception, evenements, phases) sont a cote, dans `extrait/`.

## Ce qui fait foi
`version_jouee` est deduite des leviers ecrits dans la ligne `CHACAL|FINI` de l episode, pas du nom
du dossier. `coherent = 0` signale un episode dont le job et le jeu different ; `contamine = 1`, un
dossier partage (incident du 11/09). `copies` compte les exemplaires identiques retrouves.

## Colonnes utiles
- `issue`, `cause` : le verdict de la mission ; `charges`/`sur` : charges posees sur objectifs.
- `ph1`..`ph6` : issue et instant de fin de chaque phase (`ATTEINT@4778.87`).
- `t_compromis`, `phase_au_compromis`, `cause_compromis` : quand, dans quelle phase, et pourquoi le detachement est repere.
- `charges_detail` : objectif par objectif, POSEE ou la cause du manque ; `porteur_temps` : secondes du porteur.
- `morts_fs`, `roles_morts` : nos pertes et leurs roles ; `pertes_est` : defenseurs tues.
- `tirs_appui_avant` / `tirs_appui_total` : coups de l appui avant le premier pas de l assaut / sur toute la phase.
- `porte_lecture` : ACCEPTE si les instruments de l episode se sont prouves (canari, pas continus...).

## Campagnes (episodes, dont charges completes)
| campagne | version jouee | episodes | charges completes |
|---|---|---|---|
| G8-FABLE-11-09 | V1 | 2 | 1 |
| G8-FABLE-11-09 | V2 | 10 | 4 |
| G8-FABLE-11-09 | V3 | 1 | 0 |
| G8-FABLE-11-09 | V4 | 10 | 3 |
| G8-FABLE-11-09 | V5 | 4 | 1 |
| G8-FABLE-11-09 | V6 | 10 | 5 |
| G8-FABLE-11-09 | V7 | 1 | 0 |
| G8-FABLE-11-09 | V8 | 2 | 1 |
| G8-FABLE-11-09 | V9 | 1 | 0 |
