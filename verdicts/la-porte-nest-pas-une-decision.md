# La porte n'est pas une décision, même quand on la voit

*Verdict du 16/09/2026. Campagne PORTE-RENSEIGNEE-15-09 : 160 épisodes, 8 mondes, 2 portes,
10 répétitions, `depart=3` `arret=5` `azimut=2` (imposé), `obs=1`. Environ 13 h de ferme.*

---

## Le contrôle positif, qui passe — donc c'est une mesure, pas une panne

| | |
|---|---|
| Épisodes exploitables | **155** sur 160 (4 nuls écartés sur trace, 1 sans ligne FINI) |
| `renseignement > 0` au moment du choix | **78 / 155 = 50 %** |
| `gardes` DIFFÉRENTS entre les deux ouvertures | **73 / 155 = 47 %** |
| Distribution du renseignement | 0 vue : 77 · 1 : 60 · 2 : 15 · **3 : 3** |
| Azimut joué conforme au mode IMPOSE | **155 / 155** |
| Ouverture demandée ATTEINTE | **153 / 155** |

C'est la première fois que la question est posée dans un monde où l'assaut sait quelque chose.
Les 243 épisodes précédents avaient `gardes|[0,0]` **dans 243 cas sur 243**.

---

## C1 — la porte change-t-elle l'issue ? NON

Sortie primaire enregistrée d'avance : **détruits 0..3**.

```
 monde |   porte A   |   porte B   |  ecart B-A
     4 | 2.25 ( 8)   | 2.40 (10)   |   +0.15
     5 | 2.30 (10)   | 2.80 (10)   |   +0.50
     6 | 2.60 (10)   | 2.50 (10)   |   -0.10
     7 | 2.14 ( 7)   | 2.10 (10)   |   -0.04
     8 | 2.20 (10)   | 2.50 (10)   |   +0.30
     9 | 2.60 (10)   | 1.90 (10)   |   -0.70
    11 | 2.40 (10)   | 2.10 (10)   |   -0.30
    12 | 2.50 (10)   | 2.20 (10)   |   -0.30
 ECART APPARIE sur 8 mondes : -0.062  IC 95 % [-0.305 ; +0.188]  signes 3/8  p=0.727
```

Lecture secondaire sur **charges 0..3** : +0.051, IC [−0.106 ; +0.219], signes 3/8, p=0.727.
**La conclusion ne dépend pas de la sortie choisie.**

### La puissance annoncée était au rendez-vous
L'écart-type des écarts par monde est 0,381 ; la demi-largeur de l'IC est **0,264 objet**. Le seuil
inscrit d'avance dans le job était 0,30. **Le plan pouvait voir l'effet qu'il cherchait, et ne l'a
pas vu.**

Nuance à porter honnêtement : la borne basse de l'IC est −0,305. Un avantage de 0,30 objet **en
faveur de la porte A** n'est donc pas exclu — il est exactement au bord. Mais les signes sont
partagés 3/8 : aucune direction ne se tient d'un monde à l'autre.

### Sensibilité : écarter les 4 épisodes refusés ne change rien
Quatre épisodes du monde 9 sont refusés par `lire.py` — porte d'instrument `canari_tir_journalise`,
qui contrôle la **capture des tirs**, pas l'issue. Sans eux : **−0,099**, IC [−0,418 ; +0,188],
signes 3/8. Même absence d'effet.

---

## C2 — la meilleure porte suit-elle ce que la crête a vu ? NON

```
 porte la MOINS gardee jouee : n=42   detruits moyen 2.45
 porte la PLUS  gardee jouee : n=31   detruits moyen 2.32
 ECART +0.130   IC 95 % [-0.319 ; +0.592]
```

Restreint aux épisodes où la crête a vu au moins **deux** défenseurs, l'écart **s'inverse**
(−0,19, n=13, IC ±1,0 — non informatif, mais certainement pas un renfort).

La concordance de signe **par monde** est 6/8 (p = 0,289). C'est une statistique choisie **après**
avoir vu la sortie primaire échouer : elle ne vaut rien comme preuve, et 6/8 est ce que le hasard
produit une fois sur trois. Elle est notée pour mémoire, pas pour appui.

---

## Le falsificateur, écrit dans le job avant la campagne

> « SI C1 ÉCHOUE ET C2 ÉCHOUE, la porte n'est pas une décision même quand elle est informée : la
> reconstruction du banc est alors justifiée par une mesure et non par une intuition. »

**Les deux échouent. Le falsificateur est franchi.**

---

## Ce que ça veut dire, et pourquoi c'était prévisible

Deux mesures indépendantes disent maintenant la même chose :

- `oracle-savoir-a-l-assaut.md` : **donner** la position des défenseurs ne fait pas gagner (8/18 contre 4/12) ;
- ce verdict : **voir** un défenseur et entrer par la porte qu'il ne garde pas ne fait pas gagner non plus.

L'explication la plus économique est géométrique, et elle était lisible dans le décor sans jouer un
seul épisode. L'enceinte fait **46 m de rayon**, les deux ouvertures sont à **92 m** l'une de
l'autre, et quatre défenseurs y tiennent garnison. Quelle que soit la porte, l'assaut se retrouve en
quelques secondes à l'intérieur d'un cercle où les quatre défenseurs le couvrent tous. **Les deux
options sont échangeables**, au sens du critère de symétrie du cahier des charges — et deux options
échangeables ne peuvent pas différer autrement que par hasard.

C'est la leçon la plus chère du verdict : **cette campagne aurait pu être évitée en lisant
`20_decor.sqf`.** Le test de symétrie coûte zéro épisode ; celui-ci a coûté 13 heures de ferme.

---

## Ce qui est décidé

1. **La couture de la porte est close.** On n'y branche pas d'officier, on n'y entraîne pas d'agent.
2. **La reconstruction est justifiée par une mesure.** Étape 0 du cahier des charges : faite, et sa
   réponse est non.
3. **Le prochain point de décision doit briser une symétrie.** Le cahier classe premier la
   **répartition de l'effectif** (assaut / bouchon) : l'asymétrie est déjà mesurée — 3 hommes sur 10
   tirent 31 coups sur 5753 et fournissent 46 % des exfiltrés — et son optimum doit basculer avec le
   délai de la QRF, qu'on contrôle. Prérequis : dégeler ce délai, aujourd'hui figé à 9999.
4. **Avant tout nouveau point de décision : lire le générateur et prouver que les options ne sont
   pas échangeables.** C'est désormais une porte obligatoire.

## Ce que ce verdict ne dit pas

- Il ne dit pas que la porte ne compterait pas dans une **enceinte plus grande** ou avec **plus de
  défenseurs**. Il dit qu'elle ne compte pas dans CELLE-CI, à 46 m de rayon et quatre défenseurs.
- Il ne dit rien de `arret=6` : l'exfiltration n'est pas jouée ici. 96 épisodes sur 155 sortent en
  `EXFIL_MANQUEE`, ce qui est la vignette assumée, pas un résultat.
- Il ne dit rien de la règle de choix elle-même : la porte était **imposée**. Savoir si le script
  sait choisir n'a plus d'objet maintenant que le choix ne paie pas.
