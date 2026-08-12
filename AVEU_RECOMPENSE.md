# AVEU — la récompense de la boucle est retouchée. 11/08.

*Mon dépôt disait : « la récompense doit être retouchée pour que ça marche → c'est un aveu, pas
un réglage ; il s'écrit au registre. » Le voici.*

## LE RÉSULTAT QUI L'A DÉCLENCHÉ

| | prise | mètres gagnés |
|---|---|---|
| appris | 18,6 % | **113,7** |
| frontal | 20,4 % | 117,0 |
| flanc | **42,3 %** | 100,1 |

G1 échoue contre les deux doctrines (−1,8 et **−23,7** points). G2 et G3 passent : le banc n'est
pas gagnable au hasard (0,7 %), et l'agent ne se terre pas — il gagne **plus** de mètres que la
meilleure doctrine. **Il a appris à avancer, pas à prendre.**

## DÉFAUT N°1 — L'ÉCHELLE : le guide payait plus que le but

`r = 1,0 × prise + 0,01 × mètre gagné`. À 114 mètres, le guide vaut **1,14** — **plus que le but
lui-même**. L'agent a optimisé exactement ce que je lui ai le plus payé. Il a appris
parfaitement la mauvaise chose.

## DÉFAUT N°2 — LE CLAMP : une récompense POMPABLE, et c'est le plus grave

J'avais écrit `(d_prec − d).clamp(min=0)` — « on ne compte que les mètres gagnés ». Conséquence
que je n'avais pas vue : **reculer est gratuit, avancer paie.** Un agent peut donc **pomper la
récompense en oscillant** — avancer un mètre, reculer, avancer — sans jamais progresser. Et le
terme ne **télescope plus** : sa somme ne vaut plus la distance parcourue, elle vaut la somme des
avancées, sans limite.

## LA CORRECTION, ET POURQUOI ELLE EST PRINCIPÉE ET NON UN RÉGLAGE

> **r = 1,0 × prise + 0,001 × (d_précédent − d), SIGNÉ.**

- **Signé** : c'est du façonnage par potentiel ⟨Ng, Harada & Russell 1999⟩ avec Φ = −k·distance.
  Un tel terme **télescope** — sa somme sur l'épisode vaut `k × (départ − arrivée)`, bornée — et
  il est **prouvé qu'il ne déplace pas la politique optimale**. Il guide sans pouvoir mentir.
  Le clamp cassait exactement cette propriété.
- **0,001** : le total du guide vaut alors `0,001 × 200 ≈ 0,2`, soit **un cinquième du but**.
  La règle déposée : **le guide ne vaut jamais plus du cinquième de ce qu'il guide.**

**Ce qui n'est PAS touché** : aucun terme d'exposition n'entre — le monde la sur-tarife de onze
fois. La monnaie reste **arriver**. La porte reste identique : G1 sur la borne contre les deux
doctrines, G2 contrôle nul, G3 anti-planque. **Aucun seuil n'est assoupli.**

⚠️ **Et si ça échoue encore, ce ne sera plus la récompense.** Un deuxième aveu sur la même
campagne voudrait dire que je façonne jusqu'à obtenir le résultat — et alors c'est le banc, ou
l'algorithme, qui se redépose, pas le tarif qui se rerègle.
