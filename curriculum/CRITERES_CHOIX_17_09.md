# Critères pré-enregistrés — les choix des vignettes 1, 2, 3, 4 et 6

*17/09/2026, nuit. Écrit et commité AVANT le lancement des campagnes, pendant la fumée FUMEE-CHOIX-17-09.
Plan : `plans/plan-choix-par-vignette.md` (d148974), ordre validé par Younes (« applique le plan en autonomie, toutes
les phases »). Mission : commit 307f68a. dbt : befe8a6 (`vignette_choix`, tests `tag:decision`). Lecture :
`C:\hmt\dbt\outils\lire_choix.py <CAMPAGNE>`, une seule fois par campagne, après sa fin.*

## La question, pour chaque choix

La situation (menace de niveau 3 sur la phase, contre le témoin sans menace) change-t-elle la meilleure option ?

## Dispositif commun

- 2 options × 2 bras (TÉMOIN `menace_pK=0`, MENACE `menace_pK=3`) × 8 mondes (graines 4, 5, 6, 7, 8, 9, 11, 12 :
  8 sites distincts) × R répétitions ; graine de situation 1 ; palier 4, socle 1, sans réserve.
- ~~Un job par (bras, option, monde)~~ **Amendement avant lancement (02:35)** : le contrôle avant run refuse un job d'une
  seule graine à moins de 5 répétitions. Un job porte donc **une paire de mondes** (4-5, 6-7, 8-9, 11-12), chaque monde
  avec ses R répétitions : 16 jobs par campagne, 80 au total. Chaque case garde 8 mondes × R épisodes ; les 4 cases
  d'une paire partent ensemble. Aucun épisode n'avait été lancé.
- Ordre de la file : P2, P1, P4, P3, P6 ; instances 1-8 et 10-13 en rotation ; 12 serveurs au plus.
- La fumée FUMEE-CHOIX-17-09 doit avoir tenu toutes ses attentes, sinon rien ne part.

## Les cinq campagnes

| campagne | vignette | point | option 1 → option 2 | issue primaire | R | épisodes | hypothèse écrite avant |
|---|---|---|---|---|---|---|---|
| CHOIX-P2-17-09 | `d2a2` | TRAVERSEE | tout de suite (1) → attendre la patrouille (2) | `phase_discrete` (fin de phase 2 sans compromission, sans alarme, 10 vivants) | 4 | 128 | témoin : indifférent ; menace : attendre vaut mieux → modulation **positive** |
| CHOIX-P1-17-09 | `d1a1` | INSERTION_ATTENTE | partir (1) → se terrer 3 min (2) | `phase_discrete` (phase 1) | 4 | 128 | témoin : indifférent ; menace : se terrer vaut mieux → modulation **positive** |
| CHOIX-P4-17-09 | `d3 obs0 a4` | ITINERAIRE | direct (1) → détour 350 m (2) | `mise_en_place_propre` (phase 4 ATTEINT, sans compromission ni alarme) | 4 | 128 | témoin : direct au moins aussi bon ; menace sur l'axe : détour meilleur → modulation **positive** |
| CHOIX-P3-17-09 | `d3 obs1 a3` | OBS_DUREE | 2 min (120) → 8 min (480) | `observation_utile` (au moins un défenseur localisé, fin de phase 3 sans compromission ni alarme) | 3 | 96 | témoin : 8 min meilleur ; patrouille de crête : 8 min expose → modulation **négative** |
| CHOIX-P6-17-09 | `d4a6` (délai du porteur 45 s) | EXFIL_ALLURE | prudent (0) → rapide (1) | `exfil_reussie` (au moins 6 exfiltrés) | 3 | 96 | témoin : rapide meilleur ; patrouille sur la sortie et blessé : prudent meilleur → modulation **négative** |

Total : 576 épisodes, estimés à 8 à 9 heures sur 12 serveurs.

## Écarts au plan, écrits ici

- **Phase 6** : le plan prévoyait « extraction principale ou de secours ». La mission n'a **pas de second point
  d'extraction** (le seul autre, la zone de poser, est à 4,4 km). Le choix devient l'allure du repli, levier `exfil`
  existant et vérifié (EXFIL-13-09-BIS).
- **Phases 1 et 2** : le plan situait l'inversion entre deux types de menace (patrouille contre guetteur, patrouille
  contre poste). Cette nuit, la comparaison est menace de niveau 3 (les deux types) contre témoin, comme le pilote.
- **Phase 2** : l'option « attendre » applique la règle de perception du script **sans** sa sortie
  PATROUILLE_ABSENTE, qui lisait l'état vrai du monde.

## Amendement 2 (03:58), avant toute lecture : remplacement des épisodes refusés par l'enregistreur

Dans CHOIX-P2-17-09, 4 épisodes du monde 9 ont été refusés, un par case, tous par un contrôle de l'enregistreur
(canari ou témoin : `canari_tir_journalise`, `temoin_vu_par_*`), jamais par une cause liée au choix. Aucun effet n'a été
lu. Règle ajoutée : **à la fin d'une campagne, si une case (monde, bras, option) a moins de R épisodes acceptés à cause de
refus de l'enregistreur, des épisodes de remplacement de cette case sont rejoués** (même monde, même bras, même option),
et la lecture attend leur fin. Le compte par case est fait sans lire aucune issue. Les portes Q1 à Q5 restent inchangées.

## Portes de qualité, avant toute lecture d'effet (sinon : lecture refusée)

| porte | critère |
|---|---|
| Q1 | au moins 90 % des épisodes prévus ACCEPTE |
| Q2 | zéro erreur SQF |
| Q3 | tests dbt à zéro sur la campagne : décision unique par point, choix conforme au job, choix joué conforme, choix forcé écrit, conséquence avant l'arrêt, zéro erreur SQF, situation conforme au job |
| Q4 | chaque case (monde, bras, option) a au moins max(2, R − 1) épisodes |
| Q5 | menaces de la phase posées dans tous les épisodes MENACE, aucune dans le TÉMOIN |

## Critères et classement

Moyennes par case ; écarts (option 2 − option 1) appariés par monde ; moyenne des 8 mondes à poids égaux ;
IC 95 % par 10 000 rééchantillonnages des mondes (graine 20260917).

- **Modulation** = écart MENACE − écart TÉMOIN.
- **DÉPENDANT de la situation** : IC de la modulation excluant 0 → le choix entre au curriculum et au gymnase v1.
- **DOMINÉ** : sinon, et l'IC de l'écart moyen des deux situations exclut 0 → une option vaut mieux partout.
- **INDIFFÉRENT** : ni l'un ni l'autre, à la précision du dispositif.
- Inversion (modulation établie et écarts de signes opposés) et sens conforme à l'hypothèse : rapportés, pas exigés.
- Issues secondaires : descriptives, sans décision.

## Puissance, écrite d'avance

Pour une issue binaire autour de 50 %, l'écart-type de la modulation moyenne vaut environ 2 × √(0,25/R) / √8 :
0,18 à R = 4 et 0,20 à R = 3. **Une modulation de moins de ~35 points (R = 4) ou ~40 points (R = 3) ne sera pas
établie.** Un résultat « indifférent » dira seulement que l'effet est plus petit que ça. Si une issue est presque
toujours 0 ou presque toujours 1, la précision est meilleure mais l'information plus pauvre : c'est rapporté.

## Falsificateur, pour chaque campagne

« Si la modulation n'est pas établie, la menace de la phase n'a pas changé la meilleure option à la précision de ce
dispositif, et ce choix ne sert pas encore à apprendre à décider selon la situation. »

## Fumée préalable (FUMEE-CHOIX-17-09, 10 jobs × 2 graines)

Pour chaque phase : option 1 sans menace, option 2 avec menace. Attentes écrites dans les jobs : zéro erreur,
ACCEPTE, marqueur version 2, une décision conforme au job, une preuve `choix_joue` du même choix, fin de phase
écrite, menaces seulement côté menace, mêmes sites que le 16/09, tests dbt `tag:decision` à zéro.
**Si une attente échoue, aucune campagne ne part.**
