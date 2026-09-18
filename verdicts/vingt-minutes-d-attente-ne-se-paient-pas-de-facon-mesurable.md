# Vingt minutes d'attente ne se paient pas de façon mesurable : ce monde n'a pas d'horloge

*18/09/2026. Campagne `PRIX-DU-TEMPS-V2-18-09`, 48 épisodes, 48 acceptés, 0 erreur SQF. Critères pré-enregistrés :
`menace/CRITERES_PRIX_DU_TEMPS.md` (+ amendement 1). Lecture unique : `menace/lire_prix_du_temps.py`. Statut :
**OUVERT** — le critère écrit d'avance rend INDÉCIS.*

## La question

La forme proposée par Fable, `Δ = α − β·ln(τ) + γ·s`, repose sur `τ` = surcoût en temps / temps restant. Elle n'a de
sens que si le temps a un prix. Or la mission n'a **aucune échéance** : le succès est « 3 charges et 60 %
d'exfiltrés », sans terme de temps. On impose donc une attente de 0, 600 ou 1200 s avant la phase 5, hors de tout
plafond de phase, et on regarde si la réussite baisse.

## L'instrument, contrôlé avant d'être cru

| contrôle, écrit avant les épisodes | mesuré | verdict |
|---|---|---|
| dérive pendant l'attente ≤ 30 m dans 95 % des épisodes | 100 %, maximum **3 m** | ✅ |
| assaut à sa place au début de la phase 5, ≥ 80 % par bras | **100 %** dans les trois bras | ✅ |
| abandons `ARTICULATION_ROMPUE` < 20 % par bras | **0 %** partout | ✅ |

La version 1 de ce test avait échoué à ces trois contrôles sans le savoir (voir plus bas).

## Le résultat

| attente | mission réussie (3 charges **et** ≥ 6 exfiltrés) | 3 charges | ≥ 6 exfiltrés | durée | alarme | compromis |
|---|---|---|---|---|---|---|
| 0 s | 0,625 | 0,688 | 0,750 | 1169 s | 1,00 | 1,00 |
| 600 s | 0,562 | 0,688 | 0,750 | 1888 s | 0,88 | 1,00 |
| 1200 s | 0,500 | 0,688 | 0,625 | 2375 s | 1,00 | 1,00 |

Écarts appariés par monde, bootstrap sur les 8 mondes, graine 20260918 :
- 600 s − 0 s : **−0,062** IC 95 % [−0,500 ; +0,375]
- 1200 s − 0 s : **−0,125** IC 95 % [−0,500 ; +0,188]

**Critère écrit d'avance : INDÉCIS.** Ni « le temps a un prix » (l'IC n'exclut pas zéro), ni « le temps est gratuit »
(l'IC déborde largement ±10 points).

## Ce que le mécanisme dit, et qui vaut plus que le chiffre

1. **Les charges posées sont identiques aux trois niveaux : 0,688 partout.** Attendre vingt minutes ne change
   strictement rien à l'assaut lui-même.
2. **L'alarme et la compromission sont déjà au plafond** (1,00, sauf 0,88 d'alarme à 600 s) au début de la phase 5,
   dans tous les bras. Le canal par lequel le temps pourrait punir — un monde qui se réveille — est saturé avant que
   l'attente commence. C'est la même forme de faute que le témoin au plafond en P1 et P2.
3. S'il reste un coût, il est **en aval, sur l'exfiltration** (0,750 → 0,625), et il n'est pas établi.

## Ce que trancher coûterait

Pour établir un effet de 12 points il faut ≈ 3,9/0,125² ≈ 250 épisodes par bras, soit **750 épisodes** (~1,5 jour de
ferme). Doubler les répétitions, comme le prévoyait le critère, donnerait un IC d'environ ±0,24 : toujours pas de
quoi trancher. **Recommandation : ne pas acheter cette précision.** La saisine de Fable pointait exactement ce
défaut : ce monde n'a pas d'horloge. Lui en donner une — aube, fenêtre d'extraction, renfort au bout de N minutes —
est moins cher et plus informatif que de mesurer plus finement un effet quasi nul. Décision de Younes.

## La version 1, déclarée nulle

`PRIX-DU-TEMPS-18-09` donnait 62 % de 3 charges à 0 s, **6 % à 600 s**, 62 % à 1200 s. Un creux non monotone : un
artefact. Privés d'ordre pendant l'attente, six à sept hommes reprenaient leur mouvement précédent, marchaient
**818 m** puis revenaient ; à 600 s l'assaut était à 327–672 m de sa place et la mission renonçait 14 fois sur 16,
avec alarme 0, compromis 0 et 10 vivants sur 10. Et l'issue primaire d'alors, `exfil_reussie`, **récompensait
l'abandon** : 88 % à 600 s parce que le détachement rentrait sans combattre. Correctif b68c2c7 : figer pendant
l'attente, rendre la main ensuite, journaliser la dérive, compter les charges dans l'issue.

## Falsificateur

« Si une attente de 20 minutes ne fait pas baisser la réussite de plus de 10 points, alors le temps n'a pas de prix
mesurable dans ce monde, et aucune règle ne peut y apprendre à l'économiser. »

Le point mesuré est −12,5 points, mais son IC va de −50 à +19 : **le falsificateur n'est ni franchi ni écarté.** Le
verdict reste OUVERT, et ce qui est établi est plus étroit : *attendre vingt minutes ne change pas le nombre de
charges posées, et le monde est déjà en alerte avant que l'attente commence.*
