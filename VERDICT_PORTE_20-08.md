# ✅ LA PORTE PASSE — les quatre lignes vertes ensemble

**20/08/2026, 12 h 28.** Socle **5.4.0-20082026**, commit de la porte `d51e506`,
tampons sur `52f40e2`. 60 tirages, 5 lots de 12, serveur neuf à chaque lot.

| | | |
|---|---|---|
| **LIGNE 1** · le canal de locomotion est-il vivant ? | **0 canal mort** sur **60** tirages mesurés (exigé ≥ 50) | ✓ |
| **LIGNE 2** · muets décomposés | 0 planté · 0 pont muet · 0 lent · 0 écarté | ✓ |
| **LIGNE 2bis** · rebut d'instrument | **0 sur 60** (seuil ≤ 3) | ✓ |
| **LIGNE 3** · regroupement par serveur | 12/12 · 12/12 · 12/12 · 12/12 · 11/12 — **X² = 4,07**, seuil 11,07 | ✓ |
| **LIGNE 4** · les cinq sabotages | tous **PASSE**, **même socle**, même commit | ✓ |

**59 verts sur 60.**

## CE QUE CETTE PORTE VAUT, ET CE QU'ELLE NE VAUT PAS

Elle certifie que **l'instrument fonctionne** : le canal de locomotion répond, le feu part,
le monde ne se tait pas, les cinq sabotages sont refusés comme ils doivent l'être, et rien
ne se regroupe par serveur. **Elle ne dit rien de la tactique.**

⚠️ C'est la première porte valide depuis le 18/08. Les précédentes tournaient avec un
**sélecteur qui triait sur la pente**, un critère infranchissable au sol, et une ligne de
journal qui écrivait `any`. Leur vert n'aurait rien voulu dire.

## L'UNIQUE ÉCHEC, ET IL N'EST JUGÉ PAR AUCUNE LIGNE

Lot 5, tirage 2 : **« T2 chargeur VIDE chez 1 hommes »**. Compté `AUTRE`.

C'est un **défaut réel du monde** — un homme né sans munitions — et **aucune des quatre
lignes ne le juge**. La ligne 1 ne regarde que le canal ; T2 a son propre acte et personne
ne borne son taux d'échec.

> ⚠️ **1 sur 60, soit 1,7 %.** Sous le plafond de rebut de la règle 19 (6 %) si on
> l'y rangeait — mais **on ne l'y range pas**, et c'est justement le problème : une
> grandeur que rien ne borne peut dériver sans jamais rougir.
> **À pré-inscrire : une ligne qui borne les échecs d'acte non identifiés.**

## LES FAUTES ATTRAPÉES EN JUGEANT

- **Le juge imprimait un ROUGE codé en dur** que rien ne calculait, juste sous le verdict
  qu'il calculait — vestige d'un état où la ligne 4 était une constante basculée à la main.
  ⚠️ **S'il avait dit VERTE, il aurait masqué un vrai rouge.** Même famille que la ligne
  `GESTE` qui écrivait `any` : *un instrument qui parle sans mesurer ment dans les deux sens.*
- **Le minuteur de lot était rond** (`timeout 1200`) et avait tronqué les cinq lots du 19/08
  à 5-7 tirages, en silence. Dérivé à **2400 s** (échauffement + pont + scène + 12 × la borne
  extérieure du prévol), et il **annonce** désormais s'il mord.
- **Le compteur du lot cherchait « T5 IMMOBILE »**, message disparu avec la fusion.

## L'ÉTAT

**Le banc sort de panne diagnostique.** Ce qui était bloqué depuis le 16/08 par des
instruments qui mentaient est débloqué. La file reprend : anneau par tirage, bloc C avec
son propre critère, NATIF ×2, puis la politique et la comparaison.

**Reste entier, et c'est à Younes** : le tempo du gymnase — 6 m/s enseignés contre
~3,75 rendus en montée. Voir `DOSSIER_DOCTRINE_TEMPO.md`.
