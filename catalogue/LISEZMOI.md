# Catalogue des episodes CHACAL

Genere par `outils/catalogue.py` le 2026-09-16 05:01. **Ne pas editer a la main** : il est
regenere apres chaque run (file3.sh) et chaque nuit (sauver.sh).

- **1786 episodes**, lus depuis 2066 journaux (26 sans ligne FINI ignores).
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
| AZIMUT-PAR-GRAINE-14-09 | AZG-g7-120 | 5 | 2 |
| AZIMUT-PAR-GRAINE-14-09 | AZG-g7-240 | 5 | 4 |
| AZIMUT-PAR-GRAINE-14-09 | AZG-g7-300 | 6 | 4 |
| AZIMUT-PAR-GRAINE-14-09 | AZG-g7-60 | 5 | 4 |
| AZIMUT-PAR-GRAINE-14-09 | AZG-g8-120 | 4 | 4 |
| AZIMUT-PAR-GRAINE-14-09 | AZG-g8-180 | 4 | 2 |
| AZIMUT-PAR-GRAINE-14-09 | AZG-g8-240 | 5 | 1 |
| AZIMUT-PAR-GRAINE-14-09 | AZG-g8-60 | 6 | 6 |
| AZIMUT-VIGNETTE-13-09 | AZ-A-SCRIPT | 22 | 15 |
| AZIMUT-VIGNETTE-13-09 | AZ-B-HASARD | 23 | 14 |
| AZIMUT-VIGNETTE-13-09 | AZ-C-IMPOSE0 | 23 | 11 |
| BANC-APPUI-12-09 | BA-CLOUE | 8 | 0 |
| BANC-APPUI-12-09 | BA-LIBRE | 6 | 0 |
| CONFIRMATION-MISSION-15-09 | CONF-D180-g11-m1 | 6 | 3 |
| CONFIRMATION-MISSION-15-09 | CONF-D180-g11-m2 | 6 | 5 |
| CONFIRMATION-MISSION-15-09 | CONF-D180-g12-m1 | 6 | 3 |
| CONFIRMATION-MISSION-15-09 | CONF-D180-g12-m2 | 6 | 3 |
| CONFIRMATION-MISSION-15-09 | CONF-D180-g7-m1 | 6 | 5 |
| CONFIRMATION-MISSION-15-09 | CONF-D180-g7-m2 | 6 | 5 |
| CONFIRMATION-MISSION-15-09 | CONF-D180-g8-m1 | 6 | 4 |
| CONFIRMATION-MISSION-15-09 | CONF-D180-g8-m2 | 6 | 4 |
| CONFIRMATION-MISSION-15-09 | CONF-D45-g11-m1 | 6 | 1 |
| CONFIRMATION-MISSION-15-09 | CONF-D45-g11-m2 | 6 | 2 |
| CONFIRMATION-MISSION-15-09 | CONF-D45-g12-m1 | 6 | 3 |
| CONFIRMATION-MISSION-15-09 | CONF-D45-g12-m2 | 6 | 1 |
| CONFIRMATION-MISSION-15-09 | CONF-D45-g7-m1 | 6 | 4 |
| CONFIRMATION-MISSION-15-09 | CONF-D45-g7-m2 | 6 | 5 |
| CONFIRMATION-MISSION-15-09 | CONF-D45-g8-m1 | 6 | 4 |
| CONFIRMATION-MISSION-15-09 | CONF-D45-g8-m2 | 6 | 4 |
| CONTROLE-COUTURE-AZIMUT | COUTURE-CTRL | 1 | 0 |
| DELAI-PORTEUR-14-09 | DELAI180-g11-m1 | 12 | 8 |
| DELAI-PORTEUR-14-09 | DELAI180-g11-m2 | 12 | 9 |
| DELAI-PORTEUR-14-09 | DELAI180-g12-m1 | 12 | 8 |
| DELAI-PORTEUR-14-09 | DELAI180-g12-m2 | 12 | 9 |
| DELAI-PORTEUR-14-09 | DELAI180-g5-m1 | 12 | 7 |
| DELAI-PORTEUR-14-09 | DELAI180-g5-m2 | 12 | 10 |
| DELAI-PORTEUR-14-09 | DELAI180-g6-m1 | 12 | 8 |
| DELAI-PORTEUR-14-09 | DELAI180-g6-m2 | 10 | 6 |
| DELAI-PORTEUR-14-09 | DELAI180-g7-m1 | 12 | 8 |
| DELAI-PORTEUR-14-09 | DELAI180-g7-m2 | 9 | 9 |
| DELAI-PORTEUR-14-09 | DELAI180-g8-m1 | 10 | 6 |
| DELAI-PORTEUR-14-09 | DELAI180-g8-m2 | 13 | 12 |
| DELAI-PORTEUR-14-09 | DELAI180-g8-m2bis | 12 | 9 |
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
| GARDE-VALUES-15-09 | GARDE-VALUES-bis | 5 | 5 |
| GEOMETRIE-14-09 | GEO-CORPUS | 24 | 0 |
| GEOMETRIE-14-09 | GEO-JUGES | 8 | 0 |
| GEOMETRIE-LARGE-14-09 | GEOL | 139 | 0 |
| ORACLE-11-09 | OR | 17 | 7 |
| ORACLE-11-09 | REF-A | 12 | 4 |
| ORACLE-COMPLET-11-09 | ORC | 18 | 9 |
| ORACLE-COMPLET-11-09 | REF-A | 11 | 6 |
| PHASE1-CONTROLE-15-09 | P1-CTRL-g11 | 6 | 0 |
| PHASE1-CONTROLE-15-09 | P1-CTRL-g12 | 6 | 0 |
| PHASE1-CONTROLE-15-09 | P1-CTRL-g7 | 11 | 0 |
| PHASE1-CONTROLE-15-09 | P1-CTRL-g8 | 6 | 0 |
| PLACEUR-12-09 | PL-A | 10 | 0 |
| PLACEUR-12-09 | PL-B | 4 | 0 |
| PLACEUR-BALAYAGE-12-09 | PL4-A | 1 | 0 |
| PLACEUR-BALAYAGE-12-09 | PL4-B | 3 | 0 |
| PLACEUR-HAUTEUR-12-09 | PL3-A | 1 | 0 |
| PLACEUR-TEMOIN-12-09 | PL5-B | 1 | 0 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g11-m1 | 12 | 9 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g11-m2 | 12 | 6 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g12-m1 | 12 | 8 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g12-m2 | 12 | 7 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g5-m1 | 12 | 6 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g5-m2 | 12 | 7 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g6-m1 | 12 | 6 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g6-m2 | 12 | 8 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g7-m1 | 12 | 9 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g7-m2 | 11 | 9 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g8-m1 | 10 | 6 |
| PORTE-A-CONTRE-PORTE-B-14-09 | PORTE-A-g8-m2 | 11 | 6 |
| PORTE-B-CONTROLE-14-09 | CTRL-PORTE-B-g7 | 5 | 4 |
| PORTE-B-CONTROLE-14-09 | CTRL-PORTE-B-g8 | 5 | 3 |
| PORTE-HUIT-MONDES-15-09 | PORTE-A-g11 | 10 | 5 |
| PORTE-HUIT-MONDES-15-09 | PORTE-A-g12 | 10 | 7 |
| PORTE-HUIT-MONDES-15-09 | PORTE-A-g4 | 10 | 6 |
| PORTE-HUIT-MONDES-15-09 | PORTE-A-g5 | 15 | 8 |
| PORTE-HUIT-MONDES-15-09 | PORTE-A-g6 | 14 | 8 |
| PORTE-HUIT-MONDES-15-09 | PORTE-A-g7 | 14 | 12 |
| PORTE-HUIT-MONDES-15-09 | PORTE-A-g8 | 14 | 10 |
| PORTE-HUIT-MONDES-15-09 | PORTE-A-g9 | 10 | 6 |
| PORTE-HUIT-MONDES-15-09 | PORTE-B-g11 | 9 | 5 |
| PORTE-HUIT-MONDES-15-09 | PORTE-B-g12 | 10 | 8 |
| PORTE-HUIT-MONDES-15-09 | PORTE-B-g4 | 15 | 7 |
| PORTE-HUIT-MONDES-15-09 | PORTE-B-g5 | 14 | 12 |
| PORTE-HUIT-MONDES-15-09 | PORTE-B-g6 | 14 | 4 |
| PORTE-HUIT-MONDES-15-09 | PORTE-B-g7 | 11 | 4 |
| PORTE-HUIT-MONDES-15-09 | PORTE-B-g8 | 12 | 5 |
| PORTE-HUIT-MONDES-15-09 | PORTE-B-g9 | 10 | 6 |
| PORTE-RENSEIGNEE-15-09 | PORTE-A-g11 | 8 | 3 |
| PORTE-RENSEIGNEE-15-09 | PORTE-A-g12 | 4 | 3 |
| PORTE-RENSEIGNEE-15-09 | PORTE-A-g4 | 10 | 5 |
| PORTE-RENSEIGNEE-15-09 | PORTE-A-g5 | 10 | 4 |
| PORTE-RENSEIGNEE-15-09 | PORTE-A-g6 | 10 | 8 |
| PORTE-RENSEIGNEE-15-09 | PORTE-A-g7 | 9 | 5 |
| PORTE-RENSEIGNEE-15-09 | PORTE-A-g8 | 10 | 7 |
| PORTE-RENSEIGNEE-15-09 | PORTE-A-g9 | 4 | 2 |
| PORTE-RENSEIGNEE-15-09 | PORTE-B-g11 | 7 | 4 |
| PORTE-RENSEIGNEE-15-09 | PORTE-B-g12 | 6 | 5 |
| PORTE-RENSEIGNEE-15-09 | PORTE-B-g4 | 10 | 6 |
| PORTE-RENSEIGNEE-15-09 | PORTE-B-g5 | 10 | 9 |
| PORTE-RENSEIGNEE-15-09 | PORTE-B-g6 | 10 | 7 |
| PORTE-RENSEIGNEE-15-09 | PORTE-B-g7 | 10 | 5 |
| PORTE-RENSEIGNEE-15-09 | PORTE-B-g8 | 10 | 5 |
| PORTE-RENSEIGNEE-15-09 | PORTE-B-g9 | 5 | 3 |
| REFERENCE-JAMBES-13-09 | REF-JAMBES | 15 | 11 |
| REFERENCE-PROPRE-13-09 | REF-PROPRE | 144 | 87 |
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
