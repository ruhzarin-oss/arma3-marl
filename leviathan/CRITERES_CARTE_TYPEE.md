# CRITÈRES — CARTE TYPÉE PAR EFFET + LECTEUR SPATIAL

Figés le 27/07/2026, **avant** le run de nuit.

## Ce qu'on teste, et la question ouverte qu'on tranche

Deux choses en une seule expérience, parce qu'elles se confondent si on les sépare mal.

**(1) La carte typée par EFFET.** Cinq canaux, K×K autour de chaque agent. Typés par ce
qu'ils FONT, pas par ce qu'ils SONT :

| canal | effet | source |
|---|---|---|
| 1 | **bloque le mouvement** | hauteur du bâti plein (`_solidhR`) |
| 2 | **bloque le tir et la vue** | bâti plein **+ bas couvert** (`_lowhR`) — un muret arrête la balle sans arrêter l'homme |
| 3 | **ennemi connu ou soupçonné** | `FogCarte.threat` — croyance **qui vieillit**, jamais la vérité terrain |
| 4 | **prix du danger** | probabilité de se faire toucher dans cette cellule, LOS et arc compris |
| 5 | **l'objectif** | proximité de l'objectif |

Le canal 3 est le seul qui parle de l'ennemi, et il est **brouillé et vieillissant** par
construction : `FogCarte` ne rafraîchit une cellule que si un attaquant vivant la voit
(LOS + portée), et l'oublie ensuite avec une constante de temps. **Aucun canal ne contient
la position vraie d'un défenseur.**

**(2) La question ouverte : l'architecture est-elle le levier ?**
Les deux bras reçoivent **exactement le même tenseur d'observation**. Seul le RÉSEAU change.

- **DENSE** : la carte aplatie (5·K·K nombres) entre dans le perceptron actuel.
- **CONV** : le même vecteur, mais le réseau **re-plie** les 5·K·K en (5, K, K) et les lit
  avec un convolutif avant de rejoindre la même tête.

C'est le seul protocole qui isole l'architecture : mêmes données, mêmes graines, même PPO,
même budget de rondes. Si le dense suit, **l'architecture n'était pas le levier** — et on
arrête de chercher de ce côté.

## Le banc et le juge

Banc **figé** (`DURETE_FIGEE.md`, empreinte 0eeae9efcdd67572) : **A = 4, D = 8**,
R_spawn = 170, max_steps = 60, `def_line`, `def_rand`, `secure_only`, courbe mesurée et
les trois conversions (3,28 s/pas — 1,15 tir/pas — 0,233 dégât/impact).

**Juge : PRISE-À-PERTES = prise ÷ pertes par prise.** Rien d'autre ne décide.
3 graines, mêmes graines pour les deux bras, évaluation sur une graine **différente** de
l'entraînement.

## Seuils, écrits avant

- **CONTRE-ÉPREUVE (obligatoire)** : les deux repères scriptés doivent reproduire le banc
  figé, à ±8 points : **frontal ≈ 19,3 %** de prise, **crochet ≈ 74,7 %**.
  S'ils dérivent, **on ne conclut rien** — l'env a bougé.
- **LA CARTE PAIE** : le meilleur des deux bras carte dépasse le témoin `arc seul`
  d'au moins **+15 %** de prise-à-pertes.
- **L'ARCHITECTURE EST LE LEVIER** : `CONV` dépasse `DENSE` d'au moins **+15 %** de
  prise-à-pertes, moyenné sur les 3 graines.
- **L'ARCHITECTURE N'EST PAS LE LEVIER** : |CONV − DENSE| < 8 % de prise-à-pertes.
  C'est un résultat, pas un échec : il ferme une piste.
- **ZONE GRISE** : entre 8 % et 15 % → non concluant, il faut plus de graines. Écrit
  d'avance pour ne pas être tenté d'appeler 10 % une victoire.

## Sentinelles (logguées, sans seuil)
- exposition par mètre corrigée ;
- distance du détour ;
- part du temps passé dans l'angle mort du défenseur le plus proche ;
- **fraîcheur moyenne du canal 3** : si elle est proche de 1, la carte n'est pas brouillée
  et le canal est en train de fuir la vérité terrain. C'est le garde-fou de l'honnêteté du
  canal ennemi.

## Interdits
1. Changer K, l'empan, ou la constante d'oubli de `FogCarte` après avoir vu les chiffres.
2. Nourrir un canal avec la position vraie d'un défenseur, sous quelque forme que ce soit.
3. Comparer à des chiffres mesurés à 4 défenseurs : ils sont incomparables.
