# Le premier choix qui dépend de la situation : contre une patrouille on traverse, contre un poste on attend

*19/09/2026. Campagne `CHOIX-P2-TYPES-19-09`, 144 épisodes joués, 134 acceptés, 0 erreur SQF. Critères
pré-enregistrés : `menace/banc_seuil/CRITERES_P2_TYPES_19-09.md` (écrits par Fable avant le lancement). Lecture
unique : `menace/banc_seuil/lire_p2_types.py --sans-monde 11`. Statut : **ÉTABLI**.*

## Ce qui est mesuré

Vignette `d2a2`, de nuit. Deux options imposées à pile ou face : traverser tout de suite, ou attendre. Deux bras :
la menace de phase 2 est **une patrouille motorisée seule** (niveau 4) ou **un poste de contrôle seul** (niveau 5),
posés seuls. Issue primaire `phase_discrete` : fin de phase sans compromission, sans alarme, dix vivants.

| bras | traverser tout de suite | attendre | écart (attendre − tout de suite) |
|---|---|---|---|
| PATROUILLE motorisée | **0,936** | 0,714 | **−0,221** IC 95 % [−0,371 ; −0,071] |
| POSTE de contrôle | 0,781 | **0,929** | +0,148 IC 95 % [−0,048 ; +0,457] |

**Modulation (patrouille − poste) = −0,369, IC 95 % [−0,640 ; −0,126].** Elle exclut zéro, et les deux écarts sont de
signes opposés : le critère écrit d'avance classe ce choix **DÉPENDANT du type de menace, avec inversion**.

Modulation monde par monde : 4 : −0,50 · 5 : 0,00 · 6 : −0,70 · 7 : 0,00 · 8 : −0,13 · 9 : −1,00 · 12 : −0,25.
Cinq mondes sur sept vont dans le même sens, aucun ne va contre.

## Pourquoi c'est le premier

Six choix avaient été mesurés les 16, 17 et 18/09 : P1 et P2 indifférents, P3 et P4 et P5 dominés, P6 indifférent à la
limite. **Aucun ne dépendait de la situation.** Celui-ci est le premier, et il a fallu pour cela séparer les deux
types de menace au lieu de les mélanger (niveaux 4 et 5, 16e4b32) et réparer le balayage de la fenêtre
d'observation (réglage retenu avant la campagne : observation à 260 m, balayage réparé).

## L'hypothèse écrite d'avance est RÉFUTÉE, et c'est le meilleur cas

Les critères disaient : « PATROUILLE, attendre vaut mieux ; POSTE, attendre ne sert à rien → modulation POSITIVE ».
La modulation mesurée est **négative**. Le sens réel est l'inverse :

- **contre une patrouille qui roule, il faut traverser tout de suite** — elle revient, et attendre c'est l'attendre ;
- **contre un poste fixe, il faut attendre** — il ne bouge pas, et l'attente coûte moins que de traverser à l'aveugle.

L'effet est établi *et* la prédiction est tombée : c'est ce qui distingue une mesure d'une confirmation.

## Ce que ce verdict N'établit PAS

1. **La règle n'est pas encore jouable par l'agent.** Elle dépend du *type* de menace, or au moment du choix le
   détachement ne perçoit le véhicule que dans **7 épisodes sur 58**, et la menace n'est **jamais** connue du groupe
   (0 sur 118). L'Architecte ne peut pas encore s'en servir : il faudrait qu'il perçoive ce qui distingue les deux
   situations. C'est exactement l'objet du plan « menace visible » et de l'Oracle commandant.
2. **Un monde a été retiré**, le 11, par l'amendement 3 écrit d'avance (deux épisodes sans ligne de décision, le
   détachement étant compromis à 460 s avant de choisir). C'est le monde où la patrouille était **la plus
   dangereuse** : son retrait va dans le sens du résultat. Lecture sur 7 mondes, le minimum écrit est 6.
3. **La puissance est celle annoncée** : une modulation de moins de ~35 points n'aurait pas été établie. Celle-ci
   vaut 37 points — elle passe de justesse.
4. La mission jouée est une **copie** (`bancs/chacalp2`) : le résultat vaut pour le réglage inscrit dans les critères
   et devra être rejoué sur `bancs/chacal` si ce réglage est adopté.

## Descriptif utile pour la suite (aucune règle ajustée ici)

| au moment du choix | option | `phase_discrete` | n |
|---|---|---|---|
| menace non perçue | tout de suite | 0,935 | 46 |
| menace non perçue | attendre | 0,800 | 45 |
| menace perçue | tout de suite | 0,667 | 15 |
| menace perçue | attendre | 0,833 | 12 |

La perception varie d'un épisode à l'autre dans 5 mondes sur 7. Ces quatre cases suggèrent que **ce qui est perçu**
pourrait porter la même inversion que le type — mais avec 12 et 15 épisodes, c'est une piste, pas un résultat.

## Falsificateur

« Si la modulation n'est pas établie, le type de menace ne change pas la meilleure option, et le choix de la phase 2
ne sert pas encore à apprendre à décider selon la situation. » **Falsificateur non franchi : la modulation est
établie.** Le choix de la phase 2 sert.
