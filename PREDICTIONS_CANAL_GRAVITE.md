# PRÉDICTIONS — LE CANAL AVEC GRAVITÉ. Écrites AVANT la mesure.

**19/08/2026, 20 h 15.** Younes a tranché : **branche 1 — rendre la gravité au canal.**
Avant de changer quoi que ce soit en production, le nouveau canal est **mesuré sur les
mêmes lieux, dans le même passage**, en bras apparié contre l'ancien.

- **ancien canal** (`normal`) : `setVelocity [0, vy, 0]` — la verticale est annulée
- **nouveau canal** (`gravite`) : `setVelocity [0, vy, (velocity _u)#2]` — la verticale est
  **préservée**, forme employée par `squad_deploy*.py` et les théâtres LEVIATHAN

Mêmes 12 lieux (graine 19), même sonde, même monde, même passage. Bras appariés.

## LES QUATRE PRÉDICTIONS, CHIFFRÉES

| n° | grandeur | prédiction | valeur actuelle (ancien canal) |
|---|---|---|---|
| **P1** | part au sol, **en descente** | **> 50 %** | 0-3 % |
| **P2** | distance médiane, **en descente** | **< 20 m** | 24,6 m |
| **P3** | distance médiane, **en montée** | **inchangée, dans [11 ; 16] m** | 13,8 m |
| **P4** | hauteur max médiane, **en descente** | **< 2,0 m** | 6,9 m |

**P3 est la prédiction qui engage le mécanisme** : en montée la verticale relue vaut déjà
0,0 m/s — le contrôleur d'animation la mange. Lui rendre la gravité ne doit donc **rien**
changer. Si la montée bouge, le mécanisme est mal compris.

## CE QUE J'ATTENDS QUALITATIVEMENT ⟨prédiction de Fable, 19/08⟩

**Les décollages ne disparaîtront pas** — c'est le terrain qui les déclenche, pas notre
code. Ils deviendront des **sautillements courts** : fraction de vol faible, hauteur faible,
et la distance en descente se rapprochera de celle en montée.

## LE FALSIFICATEUR DE LA BRANCHE ELLE-MÊME

> **Si en descente la distance reste ≥ 23 m avec une part au sol < 10 %, alors rendre la
> gravité ne corrige rien** : le problème ne serait pas dans notre remise à zéro mais
> ailleurs, et la branche 1 devrait être rejouée avant d'être adoptée.

## L'ORDRE, ET POURQUOI

1. Ces prédictions (ce fichier, committé).
2. La **mesure appariée** — ancien et nouveau canal, mêmes lieux, même passage.
3. **Seulement ensuite** : le changement en production (`arma_couture.py`, socle).
4. **Seulement ensuite** : le critère neuf du placeur, dérivé de la capacité du canal retenu.

⚠️ On ne change pas le canal puis on regarde : ce serait mesurer après avoir choisi.
