# Règles d'engagement : le moteur ne perçoit pas les civils, donc un agent en est aveugle

*Verdict du 13/09/2026. Labo MCP, terrain plat certifié [24100, 18900].*

## Pourquoi cette mesure

Un agent doit savoir ce qui lui est interdit, et la première interdiction est de tirer sur un
non-combattant. Avant d'écrire cette règle, il fallait savoir si la discrimination est **possible** :
un observateur peut-il distinguer un civil d'un soldat à la distance où il décide de tirer ?

## Ce qui est mesuré

Un observateur, un soldat et un civil, en terrain plat, ligne de vue libre, 50 à 400 m, jour et nuit.

| Canal | Soldat à 50 m, plein jour | Civil à 50 m, plein jour |
|---|---|---|
| `knowsAbout` (unité et camp) | **3,84** | **0,00** |
| `targetKnowledge`, connu par le groupe | oui | **non** |
| `nearTargets` | 0 entrée | 0 entrée |
| Armes portées | 2, une en main | **0, aucune** |

Le soldat n'est lui-même détecté qu'à 50 et 100 m (3,47 et 2,94 de jour ; 2,48 et 0,32 de nuit), jamais
au-delà de 100 m sur ce banc — cohérent avec la récolte du moteur, qui donne une détection médiane à
36 m de nuit.

## Le verdict

**Le moteur ne perçoit pas les civils du tout.** À cinquante mètres, en plein jour, ligne de vue libre,
le civil n'entre dans aucun canal de cible. Ce n'est pas une confusion entre civil et soldat : le civil
**n'existe pas** pour le système de perception.

**Conséquence pour l'agent.** Un agent dont la perception est bâtie sur ces canaux — ce qui est le cas
de tout ce que le projet a construit — est aveugle aux civils. Il ne peut pas les éviter puisqu'il ne
peut pas savoir qu'ils sont là. Et entraîné ainsi, il n'apprendra jamais qu'ils existent.

**Le seul signal discriminant trouvé est le port d'arme** : deux armes et une en main contre zéro.

## Ce qu'il faut en faire

1. **C'est à la mission de publier les non-combattants** à la perception de l'agent, puisque le moteur
   ne le fera pas. Avec un modèle de visibilité honnête : un non-combattant n'est perceptible que
   lorsqu'un humain pourrait le reconnaître comme tel, c'est-à-dire avec ligne de vue et à une distance
   où l'arme — ou son absence — est discernable.
2. **La sanction doit être dure.** Un civil tué rend l'épisode ÉCHEC, avec une cause propre. Une règle
   qui se négocie contre de la performance n'est pas une règle d'engagement, c'est une préférence.
3. **Et il faut peupler la mission.** Aujourd'hui CHACAL ne contient aucun civil : tout ce qui respire
   est hostile. La règle ne peut pas être testée dans un monde où elle ne peut pas être violée.

## Deux corrections d'instrument, à consigner

- **`nearTargets` ne rend rien sur ce serveur**, même avec une cible connue à 3,84. Ce n'est pas un
  canal de perception utilisable ici, contrairement à ce que laissait espérer la récolte du moteur.
- **`checkVisibility` vaut 0,55 vers une cible proche** parce que le rayon est occulté par le corps de
  la cible elle-même : la forme `[observateur, LOD]` n'ignore que l'observateur. La géométrie pure,
  qui ignore les deux, dit bien la ligne libre. Toute lecture passée de `checkVisibility` vers une
  unité est donc à relire avec cette réserve.

## Ce que ce verdict ne dit pas

- Un seul type de civil a été essayé (`C_man_1`).
- La perception a été lue **du côté du soldat régulier**. Un joueur, ou une unité avec des jumelles,
  pourrait voir autre chose.
- On n'a pas mesuré si l'IA **tire** sur un civil qui s'interpose : c'est la mesure suivante, et elle
  est différente de celle-ci.
