# Débit du monde en boîtes — critère écrit AVANT la mesure
**14 septembre 2026.** Banc : `p2/banc_debit.py` (écrit le 15/08, **jamais lancé à l'échelle**).
Ce qui est mesuré : `vue_degagee` (boîtes orientées) contre `los_clear` (champ de hauteur),
à 4096 environnements × 3 agents, pour 185, 1000 et 5000 boîtes.

## La grandeur qui décide
Le **rapport au champ de hauteur**, à l'échelle réelle — parce que c'est exactement ce que le
candidat remplace, au même endroit de la boucle. Un coût absolu ne dit rien sans son remplacé.

| rapport mesuré | lecture |
|---|---|
| **≤ ×2** | échange direct : le monde 3D entre sans rien réorganiser |
| **×2 à ×10** | utilisable sous budget : moins de rayons, ou boîtes filtrées par proximité |
| **> ×10, ou mémoire insuffisante** | ce n'est plus un échange : il faut une structure d'accélération (grille, BVH), donc un autre chantier |

## Ce qui fait TOMBER la mesure avant tout chiffre
Le banc joue d'abord les 5 segments de référence contre la réponse d'Unreal, **jeu mixte**
(2 faux, 3 vrais). S'ils ne sortent pas à l'identique, il imprime `DEBIT_VERDICT=TOMBE` et ne
chronomètre rien. *Chronométrer un noyau faux ne mesure que la vitesse de l'erreur.*

## Ce que cette mesure NE dira PAS
- **12 288 rayons = UN rayon par agent.** Le gymnase en demande plus (l'exposition du corps en
  échantillonne des dizaines, la coque du projet en compte 12). Le chiffre rendu est donc un
  **plancher** : à 12 rayons par agent, il faut multiplier par ~12.
- Rien sur la **létalité** dans ce monde-là : accorder la courbe de toucher et la suppression sur
  des boîtes est un autre travail, non commencé.
- Rien sur le **chargement** de milliers de bâtiments réels : ici les boîtes sont le même bâtiment
  répliqué et décalé.
