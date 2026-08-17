# SURSIS OUVERTS PAR LA RÈGLE 19 ET PAR LA REVUE DU 17/08

## Par la règle 19 — mesuré dans UNE session

| acquis | dépôt | mention |
|---|---|---|
| le corps rend **12,2 m** par ordre | `CHARGE_FIDELITE_JAMBES.md` | **n = 1 session** |
| **62 %** des jambes du gymnase | idem | **n = 1 session** |
| « aucune primitive nettement mieux au sol » | `RETRACTATION_JAMBES.md` § CHOIX | **n = 1 session** |
| **44,8 %** de prise | `VERDICT_ARME.md` | + destin de session nommé |

**Ne sont PAS touchés** : les réfutations existentielles. « `setVelocity` ne déplace jamais
un homme posé » reste mort — une seule session où il marche 7/7 suffit à le tuer.

## Par la revue — `bissection_selection` violait la règle 18 PAR ARITHMÉTIQUE

`bissection_selection.py:218` mesure les hommes **touchés** (`HitPart`), donc **≤ 1,15 par
tireur et par pas**. Le seuil déposé était **« < 1,5 »** — **au-dessus du maximum de son
propre capteur**.

> **Une porte qui ne peut pas échouer n'a jamais jugé.**

Passent **SURSITAIRES** :
- **`cible_unique`** — le banc censé le réfuter ne le pouvait pas ;
- **et avec lui, LA DISPARITION DE L'AVANTAGE DU FLANC**, qui en découlait.

Levée conditionnée à un **capteur de VISÉE** — l'acte d'assignation, pas l'impact — contrôlé
règle 18 sur un cas passant et un cas échouant.

## Par la revue — le `clamp(min=1)` qui rendait la mort comme un succès

La revue doit rendre une **liste de sursis**, pas seulement des correctifs. **Chaque chiffre
déposé ayant traversé ce dénominateur est à nommer et à mettre en quarantaine.** Travail à
faire : remonter les dépôts qui citent une distance moyenne à l'objectif ou un taux d'arrivée
calculés sur une population qui rétrécit.

## Une victoire de procédure, à noter comme telle

La v1 du banc des jambes était **« muette » par un bug de parseur** — il ne reconnaissait pas
`bras=4_natif_domove`, donc le contrôle positif n'était **jamais** atteint. **Ne rien lire
d'un banc muet a empêché un parseur cassé de fabriquer des chiffres.** Le système a tenu là
où l'opérateur ne pouvait pas voir.
