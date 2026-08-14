# Dépôt — choix du site du banc live, critères écrits AVANT la mesure

Déposé le 14/08/2026. Le site actuel (1734, 5391) est une **plaine** : gradient médian
0,000 sur 60 points, 58,3 % de pentes rigoureusement nulles, là où Stratis au hasard rend
2,143 de médiane et le gymnase 0,368 de `slope`.

**Deux colonnes sur cinq sortaient de plage à cause du SITE, pas des capteurs.**

## Ce qu'on ne fait PAS

On ne retouche **ni `slope` ni `dcover`**. La sonde les a innocentés : sur 400 points de
Stratis tirés au hasard, `slope` rend 0,429 de médiane contre 0,368 au gymnase — les deux
distributions se recouvrent. Régler un capteur pour qu'il rende ce qui arrange, c'est la
faute déjà nommée dans le code : *« corriger le monde pour satisfaire un capteur qui ne
mesure pas la bonne chose »*, à l'envers.

On ne déplace pas non plus le décor comme on l'a fait de 200 m à 170 m. **On change de
site, et on le dit.**

## Le dispositif

80 objectifs candidats tirés sur Stratis (terre ferme, à plus de 300 m de la mer). Pour
chacun, 30 points dans le disque de 200 m — le disque que le banc emploie réellement
(défenseurs au centre, attaquants à 170 m).

## Les portes DURES, franchies ou le candidat est écarté

| grandeur | porte | pourquoi |
|---|---|---|
| médiane de `slope` sur le disque | **dans [0,20 ; 0,60]** | encadre les 0,368 du gymnase sans exiger de coïncider |
| part de pentes exactement nulles | **< 10 %** | le site actuel est à 58,3 % ; Stratis au hasard à 1,0 % |
| `dcover` jamais trouvé (seuil en service) | **< 25 %** | le site actuel est à 78,3 % — c'est ce qui produisait la constante 0,533 |

## La règle de choix, parmi les survivants

**Le candidat qui minimise `|médiane slope − 0,368|`.** Une seule grandeur départage, et
c'est celle que la sonde a innocentée. En cas d'égalité à 0,01 près, le plus petit
`dcover` jamais-trouvé l'emporte.

## Ce qui est déclaré d'avance comme NON résolu

`dcover` restera **décalé** : au seuil en service, Stratis au hasard rend 0,100 de médiane
quand le gymnase veut 0,035. Changer le site ne le corrigera pas. **Ce résidu se lira, il
ne se corrigera pas dans le même geste** — et surtout pas en ajustant le seuil après avoir
vu les sites, ce qui serait calibrer le capteur sur le résultat.

## Ce qui ferait échouer cette mesure

- Si **aucun** candidat ne franchit les trois portes : Stratis n'offre pas de site
  compatible et c'est le monde d'entraînement qu'il faut rapprocher, pas le site.
- Si **tous** les candidats les franchissent : les portes ne séparent rien et ne valent
  rien — il faudra les resserrer avant de choisir.

## Aveu porté au dossier

Mon critère précédent sur `dcover` (« baisse d'au moins 20 points depuis 19,1 ») était
**insatisfiable par arithmétique**, indépendamment des données. Un critère qui ne peut pas
passer est le miroir d'un contrôle qui ne peut pas échouer. Il n'a rendu aucun verdict et
n'a pas été réinterprété après coup.
