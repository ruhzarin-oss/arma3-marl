# RÉPÉTITION GÉNÉRALE — ce qu'une nuit d'Arma-dans-la-boucle rend réellement

*7 août 2026. Mesure, pas supposition. ⟨Fable : « la liturgie d'entrée »⟩*

**Fiches relues ⟨règle 10⟩** : `raid-env-arma-in-loop`, `arma-fps-wall-headless-clients`,
`pont-arma-meurt-en-service`, `bridge-scripting-gotchas`, `arma-50hz-eachframe`.

## Les trois chiffres demandés

| | mesuré | ce que le dossier craignait |
|---|---|---|
| **démarrage du serveur** | **34 s** | — |
| **une itération** (1 épisode collecté) | **≈ 4 min** | inconnu |
| **FPS serveur** | **44 à 48** | « le mur de FPS » |
| **pannes du pont** | **0** sur ~25 min | « le pont meurt en service » |

> **Ni le FPS ni le pont ne sont le goulot.** Les deux craintes du dossier ne se sont pas
> matérialisées sur cette durée. Le goulot est le **temps de jeu simulé** : 8 s par pas, et un
> épisode entier de 20 hommes sur 10 sous-objectifs.

## Ce que ça donne pour dimensionner

À 4 minutes l'épisode, **une nuit de 8 h rend ~120 épisodes**.

Or la porte déposée par Fable exige de savoir lire **5 points d'écart d'arrivée**, ce qui
demande de l'ordre de **800 accrochages par bras** en certification.

> **Le débit de ce banc-ci ne suffit pas** — mais il ne s'y transpose pas non plus : le banc de
> l'étage 1 est une **approche solo**, bien plus courte qu'un raid d'escouade à dix
> sous-objectifs. Le banc A2 sortait **300 accrochages en une nuit** avec des doctrines
> scriptées. C'est de cet ordre-là qu'il faut partir, pas de celui-ci.

**Ce qui se transpose vraiment de cette mesure** : le démarrage, la stabilité du pont, le FPS.
**Ce qui ne se transpose pas** : le débit d'épisodes.

## Le signal que je surveille, et que je ne verse pas

```
[it 0] tenus 0,0/10 · vivants 20,0/20
[it 1] tenus 0,0/10 · vivants 19,0/20
```

L'escouade **ne prend rien et ne perd personne**. À l'itération zéro c'est normal — la politique
part au hasard. Mais si ça persiste, c'est **le motif du plancher** : un banc où aucun bras ne
se distingue, comme le curriculum saturé du 06/08 et son miroir effondré du 07/08.

⟨règle de l'aiguille au butoir : le cadran à surveiller inclut la grandeur que le comportement
fait bouger. Ici c'est la prise. À 0/10 des deux côtés, l'aiguille ne bouge pas.⟩

**À vérifier avant tout dépôt du banc étage 1** : que les deux doctrines de référence y
atterrissent dans la bande 20-80 %, au point de fonctionnement du jugement.

## Ce que la répétition n'a pas mesuré, et qu'il faudra

- le débit du **banc étage 1 lui-même** — il n'existe pas encore ;
- la stabilité du pont **sur une nuit entière** — 25 minutes ne prouvent rien sur 8 heures, et
  la fiche dit « muet après 20-40 min » ;
- ce que coûte l'**alternance des deux bras** sur le même serveur.
