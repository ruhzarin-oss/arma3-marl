# Critères du monde de poche de la phase 2 — écrits avant la première ligne de la poche

*22/09/2026. Étape 1 du plan de Fable (`poche/AVIS_FABLE_22_09.md`), validé par Younes. Tient compte de l'étape 0
(`poche/MECANIQUE_PHASE_2.md`, 8bd137a). Rien de ce fichier ne change après la première construction de la poche sans
un amendement daté, écrit avant la lecture qu'il touche.*

## Ce qu'est la poche

Un **proposeur**, pas un juge. Elle crible des situations de phase 2 et en envoie quelques-unes à Arma. Elle n'est
jamais crue sur un taux ; elle est jugée sur ce que ses propositions donnent dans Arma.

**Forme : deux courses** (conséquence de l'étape 0 — la compromission n'est pas une détection ennemie) :
1. **ils nous acquièrent et nous tirent dessus** (`COUP_RECU`, `FEU_PROCHE`) — noyau miroir et tir, mesurés à l'étape 2 ;
2. **nous les voyons en mode combat** (`ENNEMI_VU_EN_COMBAT`) — notre perception (mesurée) × la probabilité qu'ils
   soient en COMBAT au moment où nous les voyons (mesurée à l'étape 2).

Géométrie **cuite** depuis Arma monde par monde ; **liste blanche** de mécanismes ; calage ABC sur ≤ 10 scalaires ;
**ensemble de 32 mondes de poche** tirés du postérieur ; l'Oracle porté tel quel.

## Liste blanche initiale

Mesurés, admis : M1 définition de la compromission ; M2 structure de la phase ; M3 règle d'attente ; M4 durées ;
M5 réflexe de rupture ; M6 notre perception (moteur 900 m, vue 250-450 m de nuit).
À mesurer avant d'entrer (étape 2) : M7 leur perception de nous ; M8 le passage en COMBAT de la patrouille et du poste ;
M9 qui tire le premier. **Tout autre mécanisme est interdit** tant qu'un banc Arma ne l'a pas mesuré.

## Partition des mondes

- **A — calibrage** : graines 4 à 9 et 11 à 24 (déjà jouées).
- **B — jugement** : graines **0, 1, 2, 10, 25, 26, 27, 28, 29, 30, 31**, jamais jouées sur aucun banc CHACAL (la 3 est
  exclue : VOID `LAMBS_ABSENT`). Il en faut **au moins 8 valides**, dont **au moins 1 sans route** aux cases du
  couloir ; chacune recevra **au moins 40 épisodes Arma** (étape 2-3), joués sous les deux options.
- **B n'est jamais recalibré.** Aucune campagne n'utilise une graine de B hors du protocole de la poche ; l'Oracle
  autonome ne tire que dans A (`config.GRAINES`). Quand B est usé, on cuit des graines neuves.
- **Coupure temporelle** : les 480 paires de la confirmation de « toujours attendre » (itérations ≥ 12) restent
  **scellées** jusqu'à sa lecture ; elles ne servent ni au calage ni au plancher.

## Les nuls à battre, et leurs valeurs provisoires sur A

Un monde laissé de côté, Brier (`poche/nuls_A.txt`) :

| nul | définition | Brier sur A |
|---|---|---|
| N0 | constante | 0,1837 |
| N1 | taux du monde, appris sur la moitié de ses épisodes | 0,1678 |
| N2 | imagination actuelle de l'Oracle (logistiques L2) | 0,1837 |

Sur un monde neuf, l'imagination de l'Oracle ne fait pas mieux que la constante : sa force vient de la personnalité des
mondes qu'elle connaît.

## La marge

Écart-type d'un écart moyen apparié, mesuré sur 306 paires d'exploration (variance 0,286) : **0,085 à 40 paires,
0,072 à 55, 0,053 à 100, 0,024 à 480**. La poche **ne sera jamais certifiée sur des cellules à 5 points** ; seulement sur
des cellules à **≥ 15 points**. Le plancher Arma-contre-Arma (étape 2, mesure 2) fixera le désaccord admis :
**1,5 × ce plancher**, ni plus ni moins.

## Contrôles internes, à chaque construction — tout ou rien

1. patrouille amenée au contact → interception ≥ 95 % (Arma : 18/18) ;
2. détachement à 3 km → compromission ≤ 2 % (Arma : 0/18) ;
3. aucune menace → les deux options à ±1 point ;
4. budget 0 → aucun ordre, effet de l'Oracle nul ;
5. apport naturel de l'Oracle dans [+3 ; +20] points ;
6. noyaux conformes aux bancs (debout < 150 m connu en 3-11 s, jamais à 600 m ; moteur à 900 m, 0 faux positif) ;
7. port de l'Oracle : nourri des croyances journalisées d'Arma, ≥ 95 % des mêmes ordres ;
8. **nouveau (étape 0)** : part de « vu en combat » par type de menace dans l'intervalle Arma, et ≥ 60 % sans alarme.

## Les verdicts

- **V1 — l'écart agrégé** attendre − traverser sur B, dans l'intervalle Arma. Inversé → échec.
- **V2 — le niveau par monde neuf** : Spearman ≥ 0,6 entre taux prédit et taux Arma sur ≥ 8 mondes de B. S'il échoue,
  la poche ne sera crue que sur les écarts — écrit d'avance.
- **V3 — l'enrichissement prospectif**, le seul qui adopte (étape 4) : 4 cellules proposées par la poche (|écart| ≥ 15
  points, accord de signe ≥ 80 % de l'ensemble, ≥ 50 % sur |écart| ≥ 15) contre 4 cellules de l'imagination actuelle,
  entrelacées, **40 paires par cellule**, 320 paires. **Adoptée si** l'écart cumulé des cellules poche est ≥ 10 points
  dans le sens prédit (permutation des signes, unilatéral, α 0,05), **et** ≥ celui du témoin, **et** ≥ 3 signes sur 4.

## Arrêts

- Étape 3 : après 2 itérations de calage, Brier sur B > N2 ou V1 inversé → poche **rétrogradée** en outil de symétrie et
  de puissance.
- Étape 4 : écart cumulé < 5 points ou témoin ≥ poche → rétrogradée ; deux fois → retirée.
- Toujours : une proposition à écart > 30 points est suspecte par défaut (contrôle interne avant envoi) ; jamais deux
  cycles de poche sans passage par Arma ; une infirmation forte = diagnostic du mécanisme fautif avant toute nouvelle
  proposition dans cette région.

## Lecteur unique

`poche/lire_poche.py` : lit les prédictions de la poche sur les épisodes de B (`poche/predictions_B.csv` : épisode,
monde, option, p_compromis) et rend N0, N1, N2, V1, V2 en une fois. V3 a son propre lecteur, écrit avant l'étape 4.
