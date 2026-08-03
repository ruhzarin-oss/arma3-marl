# CRITÈRES FIGÉS — CONFIRMATION DU TÉMOIN VENTILÉ, SUR GRAINES NEUVES

Figés **avant** ce run, **après** avoir vu le run 7,8,9. C'est dit ici pour que personne
n'en fasse une prédiction qu'elle n'est pas.

## Le défaut d'instrument, décrit sans regarder le résultat

`initiative()` retient, pour chaque défenseur, **l'attaquant le plus proche**. Or la
doctrine « crochet » place deux hommes sur quatre en **fixation frontale** : par
construction, ce sont eux les plus proches. Le témoin observait donc les fixeurs et
appelait ça le mécanisme du contournement.

Ce défaut se démontre en lisant le code, sans connaître le résultat. C'est ce qui rend sa
correction légitime.

## Ce que le run 7,8,9 a donné (déjà vu — donc à confirmer, pas à croire)

| | initiative attaquant | engagements |
|---|---|---|
| crochet, fixeurs | 25,4 % | 3018 |
| crochet, flanqueurs | **61,5 %** | 1822 |
| frontal (doctrine entière) | 36,0 % | — |

Contrôle arithmétique : (0,254×3018 + 0,615×1822) / 4840 = **39,0 %**, l'ancien agrégé au
dixième. La décomposition est fidèle.

## Ce qui est testé ici, sur graines 21, 22, 23

Les seuils ne bougent pas. Ce sont ceux de `CRITERES_REVERDICT_ARC_OUVRANT.md`
(0606073790cc9c14) :

1. **crochet, FLANQUEURS ≥ 60 %** — le contournement prend l'initiative.
2. **frontal ≤ 35 %** — de face, le défenseur la garde.
3. **fixeurs nettement sous les flanqueurs** (écart ≥ 20 points) — c'est le mécanisme
   lui-même, pas un niveau : dans la MÊME doctrine, au MÊME instant, la face et le flanc
   doivent se comporter à l'opposé.
4. **Contre-épreuve** : cône dur dans la bande 22,2 % / 40,4 % ±5 pt
   (`CRITERES_REFERENCE_ARC3.md`, 5bbb7f957f0319e8).

## Ce qui invalide

- Flanqueurs sous 60 % → le 61,5 % était un effet de graine, on ne conclut rien.
- Moins de 500 engagements flanqueurs → échantillon trop mince.
- Contre-épreuve hors bande → le harnais a bougé.

## Interdit

Retoucher un seuil parce qu'il est manqué d'un point. Le frontal à 36 % contre 35 % **reste
un échec** s'il se reproduit — on le dira, et l'écart deviendra l'objet d'étude.
