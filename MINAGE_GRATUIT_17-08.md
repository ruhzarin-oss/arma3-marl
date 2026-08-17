# MINAGE GRATUIT — RÉSULTAT NÉGATIF, ET IL ÉLIMINE

17/08/2026. **Zéro serveur démarré.** Relecture des journaux existants : 12 sessions de la
sonde d'unité + 35 de la nuit NATIF. Signatures écrites avant chaque croisement.

## Ce qui a été croisé, et ce que ça donne

### Le côté Python du pont — MUET
Les 12 journaux de session sont **identiques au mot près** : « serveur… », « échauffement »,
« scène », « réveil NATIF », « socle chargé ». **Aucune erreur, aucun silence, aucun compte.**

Ce n'est pas une preuve que le pont va bien : il ne journalisait presque rien avant la 1.2.
C'est une **absence de signal**, et elle est due à l'instrument, pas au monde.

### La télémétrie de naissance — AUCUNE SÉPARATION

| variable | vivantes | mortes | verdict |
|---|---|---|---|
| charge (`load`) | 0,82 – 1,91 (méd 1,32) | 0,21 – 2,09 (méd 1,23) | **chevauchent** |
| co-locataires | 0 – 1 | 0 – 1 | **chevauchent** |
| ordre de lancement | 3 – 11 | 1 – 12 | **chevauchent** |
| heure | 22:04 – 22:37 | 21:55 – 22:41 | **chevauchent** |

La session **morte** de plus faible charge (`0,21`) et la session **vivante** de plus forte
charge (`1,91`) sont aux deux extrêmes du mauvais côté. **La charge n'explique rien.**

### Le temps, sur 35 sessions de la nuit — PAS DE GROUPEMENT
```
VVVMVVMMMMMMVMMMVMMVMMVMVMMMMMMMMMV
```
15 séries observées contre **16,1 attendues sous indépendance**, `z = −0,43`. Les mortes ne
se suivent pas plus que le hasard ne le veut. Première moitié 10/17, seconde 14/18 :
**pas de dérive**.

## Ce que le négatif ÉLIMINE, et c'est le gain

Le destin de session **n'est expliqué par aucune variable extérieure relevée** : ni la charge
machine, ni le co-locataire, ni l'heure, ni l'ordre, ni le voisinage temporel.

> **La cause est INTERNE à la naissance du serveur.** Ce qui restait de « l'état de la
> machine à cette heure-là » dans l'espace de recherche tombe.

## Un fait stable, à travers deux protocoles et deux socles

| campagne | socle | protocole | mortes |
|---|---|---|---|
| nuit NATIF | 1.10.0 | 1 tirage / serveur | **24 / 35 = 68 %** |
| sonde d'unité | 1.13.0 | 6 tirages / serveur | **7 / 12 = 58 %** |

**Le taux ne bouge pas** quand le socle, le protocole et le nombre de tirages changent.
Le phénomène est **stationnaire** — il ne s'aggrave ni ne s'améliore, il est simplement là.

## Ce qui reste, et ce qu'il faut payer

Le minage gratuit est **épuisé**. Aucune variable déjà relevée ne sépare, et les journaux
serveur des sessions concernées ont été **écrasés** (`prevol.py` réinitialise son `.out` à
chaque lancement — défaut d'instrument à corriger avant la prochaine sonde).

Le prochain geste est **payé** : la sonde du pont prescrite par Fable — 12 sessions sous la
**1.2**, état du pont journalisé par session (bind, compteurs `ring` / `send` / `ligne`),
**signature écrite d'avance : chaque destin doit s'apparier à un état du pont**. Si les
compteurs ne séparent pas les destins, l'hypothèse meurt à bas prix.

⚠️ La 1.2 est un **instrument neuf** : empreinte neuve, porte pleine-chemin à rejouer, et
**interdiction de mélanger dans une même table des sessions d'ère 1.1 et d'ère 1.2**.
