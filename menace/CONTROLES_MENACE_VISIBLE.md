# Contrôles pré-enregistrés — menace visible

*17/09/2026, vers 16 h. Plan `plans/plan-menace-visible.md` (4cd083e, 8bc624d), validé par Younes : fenêtre de 90 s,
ordre P2, P1, P4, connaissance du groupe (`targetKnowledge`). Patch `menace/patch_mission_menace.py`, essayé à blanc dans
les deux ordres (avant et après le patch EvoGP). Écrit et commité avant l'application du patch et avant tout épisode.
Lecture unique : `menace/lire_controles.py`.*

## Les jobs (`menace/jobs_controles.py`)

Campagne CONTROLE-MENACE-VISIBLE-17-09. Les gabarits sont les jobs des campagnes de la nuit (mêmes vignettes). Tous les
jobs ont une fenêtre de 90 s, sauf ORIGINE.

| contrôle | vignette | réglage | mondes × répétitions | épisodes |
|---|---|---|---|---|
| ORIGINE | P2 (`d2a2`, traverser tout de suite) | fenêtre 0, menace P2 niveau 3 | 2 × 1 | 2 |
| POSITIF | P2 | groupe inerte à 150 m devant, aucune autre menace | (4, 5) et (6, 7) × 2 | 8 |
| NÉGATIF | P2 | groupe inerte à 1500 m derrière | idem | 8 |
| NUL | P2 | aucune menace | idem | 8 |
| P2_TYPE1 / P2_TYPE2 | P2 | patrouille motorisée seule / poste de contrôle seul | idem | 8 + 8 |
| P1_TYPE1 / P1_TYPE2 | P1 (`d1a1`, partir) | guetteur seul / patrouille seule | idem | 8 + 8 |
| P4_TYPE1 / P4_TYPE2 | P4 (`d3 obs0 a4`, direct) | patrouille de mise en place seule / poste d'écoute seul | idem | 8 + 8 |

Total : 19 jobs, 74 épisodes.

## Critères

| contrôle | attendu |
|---|---|
| POSITIF | `menaces_connues` > 0 en fin de fenêtre dans au moins 80 % des épisodes acceptés |
| NÉGATIF | `menaces_vues` = 0 en fin de fenêtre dans au moins 95 % |
| NUL | `menaces_vues`, `menaces_connues`, `verite_menaces` et `menaces_connues` au choix, tous à 0, dans 100 % |
| ORIGINE | aucune fenêtre ouverte, 0 erreur SQF ; `phase`, `point`, `options`, `choix` et `decideur` identiques aux épisodes CHOIX-P2 équivalents (traverser tout de suite, menace 3, mondes 4 et 5) |
| GLOBAL | 0 erreur SQF sur les 74 épisodes, marqueur de décision version 3 partout |
| **VARIANCE** (descriptif) | part des épisodes où la menace est connue au moment du choix, par phase et par type, **entre 30 et 70 %** |

**Décision écrite avant**
- Si POSITIF, NÉGATIF, NUL, ORIGINE ou GLOBAL échoue, le patch est corrigé et les contrôles sont rejoués. Aucune
  campagne ne part.
- Si une case de VARIANCE sort de la plage, c'est rapporté à Younes avant la campagne de cette phase, sans rien
  changer seul (la fenêtre est fixée à 90 s).
- Cohérence : l'écart entre `distance_menace` (position crue) et `verite_distance_menace` est imprimé épisode par
  épisode, sans seuil.
