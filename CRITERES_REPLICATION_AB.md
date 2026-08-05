# Réplication de l A/B — règle d arrêt déposée AVANT toute lecture

*5 août 2026, 23h35. Le reboot (Secure Boot / pilote NVIDIA) a tué le run de la nuit.
Il redémarre à zéro. **Aucun score du nouveau journal n a été lu.***

## Ce qui change, et ce qui ne change pas

**Ne change pas : les critères.** Hiérarchie des métriques inchangée, celle déposée au
commit `f64ffae` (CRITERES_METRIQUES_AB.md) : primaire = TENUE, secondaires séparées,
jamais agrégées. Portée inchangée : charge 6, ratio 1,5-3,0.

**Change : le statut.** Le premier corpus (partie1 + partie2, 210 accrochages) a **déjà
rendu son verdict** : +17,3 pts sur la TENUE, p = 0,012, zéro écart sur l élimination,
synergie au plancher NON établie. Ce verdict est clos et ne se rejuge pas.

Le nouveau journal est donc une **RÉPLICATION INDÉPENDANTE**, pas une rallonge du premier.
Le mélanger au premier serait un cumul opportuniste : on regarderait jusqu à ce que le p
plaise.

## Règle d arrêt, déposée maintenant

On juge la réplication **une seule fois**, au premier de ces deux termes :

- le nouveau journal atteint **>= 150 accrochages clos** (comparable au premier corpus) ;
- ou il est **8h00** le 6 août.

Si à ce terme la TENUE compte **moins de 30 événements**, la primaire est illisible et on
le dit tel quel — aucun verdict n est prononcé sur la réplication.

## Ce qui la ferait échouer, écrit avant

La réplication **contredit** le premier corpus si l écart sur la TENUE est **< +6 points**
ou si son signe s inverse. Dans ce cas le +17,3 redevient une observation d un seul monde,
et c est CETTE phrase-là qui se verse au projet.

Le test au plancher (arr_plancher.py) est rejoué **à l identique**, sans retouche.
