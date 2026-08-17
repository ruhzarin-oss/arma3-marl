# LECTURE DE TOUS LES PLACEURS — correctif n°6, zéro serveur

17/08/2026. Prescrit par Fable : *« le procès s'étend à tous les placeurs — lecture d'abord,
énumérer et lire coûte zéro serveur. »* Quatre trouvailles.

## 1 · LA SCÈNE DU BANC LIVE NE TESTE **RIEN**

```sqf
private _a = random 360; private _r = 10 + random 25;          // défenseurs
private _p = [(HMT_OBJ select 0) + _r * sin _a, ...];
private _az = random 360;                                       // attaquants
```

**Compté : 0 test dans `SCENE`.** Ni `surfaceIsWater`, ni `getTerrainHeightASL`, ni
`checkVisibility`, ni praticabilité. Les huit hommes de chaque épisode naissent **au pur
hasard** autour de l'objectif.

Ce n'est pas « mal choisir » — c'est **ne pas choisir**. Un attaquant peut naître dans un
rocher, contre un mur, sur un toit, et **rien ne le détecte**.

## 2 · LE PRÉVOL NE TESTE JAMAIS LE DÉPLACEMENT DES HOMMES **SERVIS**

Ce qu'il leur teste (lignes 222-242) : l'arme en main, les munitions, le mode déclaré.
**Rien d'autre.**

**T5 et T7 testent un TÉMOIN**, créé à part, placé par le placeur, à 250-370 m de la scène.
Les huit hommes qui vont réellement jouer l'épisode ne sont **jamais** éprouvés sur leur
capacité à se déplacer ni à tirer depuis **leur** position.

> **C'est le même défaut que celui qu'on vient de corriger, un cran plus haut : on teste
> ailleurs que là où ça compte.** Le placeur v2 garantit un bon lieu **pour le témoin**.
> Il ne garantit rien pour les hommes de l'épisode.

## 3 · LE BANC DES JAMBES NE TESTE QUE L'EAU

```sqf
private _px = _cx + (random 120) - 60;
if (surfaceIsWater [_px,_py]) then { _px = _cx; _py = _cy };
```

Positions tirées au hasard dans ±60 m, **seul l'eau est écartée**. Le 12,2 m a donc été
mesuré sur des positions **non filtrées**, dont certaines encombrées.

## 4 · ⚠️ UN ÉCART DE VITESSE QUE PERSONNE N'AVAIT VU

| mesure | mode de pilotage | distance | durée | vitesse |
|---|---|---|---|---|
| banc des jambes | `pilote` | 12,2 m | 3,28 s | **3,72 m/s** |
| placeur v2, lieux reçus | `statue` + `PATH` | 25 m | 4,0 s | **6,25 m/s** |

**Facteur 1,68.** Or le gymnase suppose **6 m/s** — que le placeur atteint et dépasse.

Deux explications possibles, **non départagées** :
- le **lieu** : le placeur ne mesure que sur des lieux qu'il vient de recevoir (biais de
  sélection assumé), le banc des jambes mesurait sur des positions non filtrées ;
- le **mode** : `pilote` coupe `AUTOCOMBAT` et `FSM`, `statue` coupe aussi `FSM` mais garde
  `PATH` explicitement rendu.

> **Conséquence pour le sursis** : le « **corps rend 62 % des jambes du gymnase** » ne mesure
> peut-être pas le corps — il mélange **la capacité du corps et la qualité du lieu**. Le sursis
> « n = 1 lieu » posé par Fable est donc **plus grave qu'annoncé** : ce n'est pas une question
> de taille d'échantillon, c'est une **grandeur composite**.
>
> La levée reste bon marché et devient prioritaire : **rejouer le banc des jambes sur des
> lieux REÇUS par le placeur v2**, et rendre la vitesse comme une distribution.

## Ce que la lecture NE dit pas

Elle ne mesure rien. L'écart ×1,68 rapproche deux chiffres obtenus dans des conditions
différentes — c'est un **motif d'enquête**, pas un résultat. Aucun sursis n'est levé ni
aggravé par ce document ; il désigne où mesurer.

## Ordre de priorité qui en découle

1. **La scène** — placement aléatoire non testé, et c'est là que jouent les vrais hommes.
2. **Le prévol** — étendre T5/T7 aux hommes servis, ou faire naître le témoin **dans la scène**.
3. **Le banc des jambes** — rejouer sur lieux reçus, ce qui lève ou confirme le 62 %.
