# Catalogue des episodes CHACAL

Genere par `outils/catalogue.py` le 2026-09-14 05:00. **Ne pas editer a la main** : il est
regenere apres chaque run (file3.sh) et chaque nuit (sauver.sh).

- **661 episodes**, lus depuis 907 journaux (22 sans ligne FINI ignores).
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
| ABLATION-12-09 | A0 | 19 | 10 |
| ABLATION-12-09 | A1 | 20 | 13 |
| ABLATION-12-09 | A2 | 18 | 8 |
| ABLATION-12-09 | A4 | 18 | 13 |
| ABLATION-12-09 | A8 | 16 | 11 |
| ALIZE-1 | AL1 | 19 | 6 |
| AZIMUT-VIGNETTE-13-09 | AZ-A-SCRIPT | 22 | 15 |
| AZIMUT-VIGNETTE-13-09 | AZ-B-HASARD | 23 | 14 |
| AZIMUT-VIGNETTE-13-09 | AZ-C-IMPOSE0 | 23 | 11 |
| BANC-APPUI-12-09 | BA-CLOUE | 8 | 0 |
| BANC-APPUI-12-09 | BA-LIBRE | 6 | 0 |
| CONTROLE-COUTURE-AZIMUT | COUTURE-CTRL | 1 | 0 |
| EXFIL-13-09 | EXF-A-REFERENCE | 1 | 0 |
| EXFIL-13-09 | EXF-B-AWARE | 2 | 0 |
| EXFIL-13-09 | EXF-C-BUDGET | 2 | 1 |
| EXFIL-13-09-BIS | EXF2-A-REFERENCE | 12 | 6 |
| EXFIL-13-09-BIS | EXF2-B-AWARE | 12 | 9 |
| EXFIL-13-09-BIS | EXF2-C-BUDGET | 12 | 9 |
| G8-FABLE-11-09 | V1 | 6 | 1 |
| G8-FABLE-11-09 | V2 | 10 | 4 |
| G8-FABLE-11-09 | V3 | 10 | 3 |
| G8-FABLE-11-09 | V4 | 10 | 3 |
| G8-FABLE-11-09 | V5 | 10 | 5 |
| G8-FABLE-11-09 | V6 | 10 | 5 |
| G8-FABLE-11-09 | V7 | 7 | 0 |
| G8-FABLE-11-09 | V8 | 6 | 3 |
| G8-FABLE-11-09 | V9 | 7 | 0 |
| ORACLE-11-09 | OR | 17 | 7 |
| ORACLE-11-09 | REF-A | 12 | 4 |
| ORACLE-COMPLET-11-09 | ORC | 18 | 9 |
| ORACLE-COMPLET-11-09 | REF-A | 11 | 6 |
| PLACEUR-12-09 | PL-A | 10 | 0 |
| PLACEUR-12-09 | PL-B | 4 | 0 |
| PLACEUR-BALAYAGE-12-09 | PL4-A | 1 | 0 |
| PLACEUR-BALAYAGE-12-09 | PL4-B | 3 | 0 |
| PLACEUR-HAUTEUR-12-09 | PL3-A | 1 | 0 |
| PLACEUR-TEMOIN-12-09 | PL5-B | 1 | 0 |
| S0-CONTROLE-POSITIF | S0 | 19 | 19 |
| SOCLE-CONFIRMATION-12-09 | B0 | 19 | 14 |
| SOCLE-CONFIRMATION-12-09 | B1c | 10 | 7 |
| SOCLE-CONFIRMATION-12-09 | MSOCLE | 6 | 3 |
| SONDE-12-09 | SONDE | 3 | 0 |
| TOURNOI-TACTIQUES-12-09 | B0 | 18 | 15 |
| TOURNOI-TACTIQUES-12-09 | B1 | 20 | 11 |
| TOURNOI-TACTIQUES-12-09 | B2 | 18 | 11 |
| TOURNOI-TACTIQUES-12-09 | B5 | 10 | 2 |
| TOURNOI-TACTIQUES-12-09 | REF | 10 | 1 |
| VICTOIRE-BOUT-EN-BOUT-12-09 | V6-PLEIN | 36 | 29 |
| VICTOIRE-BOUT-EN-BOUT-12-09 | V6-SONDE-DUREE | 2 | 1 |
