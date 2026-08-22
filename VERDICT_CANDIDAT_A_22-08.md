# CANDIDAT A — LA POLITIQUE EST AVEUGLE À LA PENTE, ET À TOUT LE RESTE

**22/08/2026.** Pré-inscription `PREINSCRIPTION_DEUX_CANDIDATS.md`, commit `82101f9`,
écrite **avant** toute mesure. Zéro pas d'entraînement : la politique `boucle_pol.pt` est
**rejouée** telle quelle. Monde imprimé par le gardien de paramètres (`move=14.0`,
`sec_par_pas=3.28`, `obs_sans_slope=False`, `relief_stratis=True`).

## Les deux prédictions passent

| graine | intact | brouillé | écart |
|---|---|---|---|
| 101 | 50,4 % | 50,0 % | 0,4 |
| 102 | 50,4 % | 49,6 % | 0,8 |
| 103 | 51,2 % | 52,0 % | −0,8 |

**Écart moyen 0,7 point** (seuil pré-inscrit : 3,0).
**A1 PASSE** · **A2 PASSE, 3 graines sur 3.**

> La pente est **permutée entre environnements**, jamais retirée : la dimension reste,
> l'information meurt. `assault_terrain.py:519` — la pente est la **colonne 5**.

## Le contrôle positif — sans lui, ce zéro ne vaut rien

Un instrument qui dit « rien n'a changé » doit prouver qu'il **sait dire le contraire**.
Le **même code** appliqué aux neuf colonnes de la base :

| colonne permutée | prise | chute |
|---|---|---|
| **apx** (ma position x) | 30,6 % | **20,1** |
| **dgx** (cap vers le but x) | 31,0 % | **19,7** |
| **apy** | 36,5 % | **14,2** |
| **dgy** | 39,5 % | **11,2** |
| alive | 52,3 % | −1,7 |
| **SLOPE** | 51,2 % | **−0,5** |
| dcover | 50,8 % | −0,1 |
| los (je suis vu) | 51,6 % | −0,9 |
| nd (défenseur le plus proche) | 51,8 % | −1,2 |

Témoin intact : **50,7 %**. Le brouilleur effondre quatre colonnes de 11 à 20 points et
laisse la pente à **−0,5**. **Il mord. Le zéro est un vrai zéro.**

## Le piège suivant, et comment il est levé

Une colonne inerte peut l'être pour deux raisons : on l'**ignore**, ou elle ne **varie pas**
— et alors la permuter est l'identité. Deux grandeurs qui ne se confondent pas :

| colonne | dispersion | décisions changées |
|---|---|---|
| apx / apy / dgx / dgy | 0,30 – 0,32 | **33 – 40 %** |
| **SLOPE** | **0,183** | **3,3 %** |
| los | 0,432 | 7,5 % |
| nd | (voir plus bas) | 1,6 % |
| dcover | **0,029** | 0,4 % |

**La pente varie autant que les colonnes qui décident** (0,183 contre 0,30) et ne déplace
que **3,3 %** des décisions, pour **0 point** de prise. **Elle est réellement ignorée.**

## Ce que ça dit vraiment — plus large que la question posée

**Cette politique est un NAVIGATEUR, pas un tacticien.** Elle lit **où elle est** et **où est
le but**. Les quatre canaux tactiques — pente, couvert, être vu, ennemi le plus proche —
pèsent ensemble moins que le bruit. Elle traverse un terrain ; elle ne le combat pas.

> C'est un mécanisme **plausible** de l'écart de 15,4 points : l'IA d'Arma, elle, réagit à
> ce qu'elle voit. **Plausible, non établi** — ce banc ne mesure que le gymnase.

## Conséquence directe sur la doctrine

> **Faire PAYER la pente ne servirait à rien tant que la politique ne la REGARDE pas.**

Le levier n'est pas dans la dynamique du monde : il est dans ce qui **récompense** la lecture
des canaux tactiques. Aucun réentraînement n'est décidé ici — c'est un arbitrage de Younes.

## ⚠️ Deux angles morts déclarés (règle 20)

1. **`dcover` n'a PAS été testé** : sa dispersion vaut **0,029**, cinquante fois moins que les
   autres. Le permuter ne fait presque rien **par construction**. Son inertie n'est **pas**
   une preuve d'aveuglement — l'instrument n'a pas pu la juger.
2. **`nd` est un canal EMPOISONNÉ.** `assault_terrain.py:_obs` calcule
   `min(dist²).clamp(max=1e17).sqrt()/S` : quand **tous les défenseurs sont morts**, la
   sentinelle vaut `1,581e+06` — mesuré, exactement la valeur prédite — et part dans un
   réseau dont les autres colonnes tiennent dans [−1, 1]. Présente à **23 pas sur 60**,
   **0,15 %** des entrées. ⚠️ **Portée limitée** : elle ne se déclenche qu'une fois le combat
   **déjà gagné**. C'est un défaut à corriger, **pas** un candidat pour les 15,4 points.

⭐ **Cliquet : une colonne inerte n'est une colonne ignorée que si elle VARIE.**
Sans la dispersion, j'aurais annoncé « la politique ignore le couvert » — alors que le
gymnase ne le lui montrait presque pas.
