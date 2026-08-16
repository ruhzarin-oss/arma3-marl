# DÉPÔT — LE CONTRÔLE POSITIF DU LIEN DRONE→SOLDAT NE CERTIFIE PAS

*16 août 2026, 21 h 50. 20 répétitions sur 20, aucune VOID, toutes dans le MÊME monde
(`socle 1.10.0-16082026`, empreinte transportée avec chaque répétition). Portes et seuils
déposés avant lancement dans `CONTROLE_POSITIF_DRONE.md`. **Tentative CONSOMMÉE.***

## LE RÉSULTAT

| bras | ont tiré | part | médiane 1ᵉʳ tir | savaient déjà à l'ouverture |
|---|---|---|---|---|
| **A0** — sans observateur | 3/20 | 15 % | 0,2 s | 3/20 |
| **A1** — observateur qui voit, tuyau coupé | 4/20 | 20 % | 0,1 s | 3/20 |
| **B** — `reveal` niveau 4 | **20/20** | 100 % | **2,9 s** | 1/20 |

> **P1 · le canal existe** — B ≥ 18/20 et médiane ≤ 8 s → **PASSE** (20/20, 2,9 s)
> **P2 · aveugle sans lui** — A0 ≤ 2/20 → **TOMBE** (3/20)

**P2 tombe d'UNE répétition.** Le seuil était écrit avant ; il ne se renégocie pas après.
Conformément au dépôt : *la SCÈNE est mal posée, et les trois bras sont sans objet.*

## LA CAUSE EST IDENTIFIÉE, ET ELLE EST DANS MON MONTAGE

Les trois répétitions fautives de A0 — n° 9, 13, 19 — portent toutes `saitgrp0 > 0`
(2,97 / 1,79 / 2,75) : **l'escouade savait déjà avant l'ouverture de la fenêtre**, et a tiré
en 0,1 à 2,5 s. Ce ne sont pas des détections pendant la mesure, ce sont des détections
pendant les **30 secondes d'attente** qui précèdent.

Or cette attente n'existe que pour une raison : laisser à l'observateur aérien le temps
d'acquérir (il atteint 4,0 en 15-25 s). Elle a été imposée aux trois bras pour l'équité —
correctement — mais elle **double l'exposition de l'escouade**, de 30 s à 60 s. Le témoin
paie une attente dont il n'a aucun besoin.

## CE QUI N'EST PAS LU, ET NE SERA PAS CITÉ

**A1 ne se lit pas.** Le dépôt l'interdit tant que P2 n'est pas franchie. On note seulement,
sans en rien conclure, que A1 (4/20) et A0 (3/20) sont à une répétition l'un de l'autre, et
que 3 des 4 tirs de A1 sont des répétitions où l'escouade savait déjà à l'ouverture. Une
seule — la n° 3 — a l'allure d'une fuite : un coup unique à 30,1 s, en toute fin de fenêtre.
**Ça ne vaut rien tant que la scène n'est pas réparée**, et c'est écrit ici pour ne pas être
redécouvert comme une nouveauté.

## CE QUI EST ACQUIS MALGRÉ TOUT

Ces trois faits ne dépendent pas de la porte P2 ; ils ont été mesurés séparément, en scène
pure, avec étalon d'infanterie :

1. **Dans Arma, un drone ne donne RIEN à l'IA.** AR-2 Darter : `knowsAbout` = 0 sur 4
   montages. MQ-4A Greyhawk : 0, y compris **cloué à 148 m juste au-dessus** de la cible
   (`dist2D` = 0). Le capteur d'un UAV alimente le terminal d'un opérateur humain, pas la
   base de connaissance des unités. **Un banc drone devra ÉCRIRE la perception du drone.**
2. **Un observateur aérien à équipage IA perçoit — mais seulement en oblique.** Posé à la
   verticale : 0 pendant 60 s. Lâché à 300 m et rentrant en oblique : 4,0 en 15 s.
3. **`reveal` fait tirer.** 20/20, premier coup à 2,9 s de médiane, sans aucun
   `forceWeaponFire`, escouade en mode `natif`. Le canal est réel et rapide.

## LA RÉPARATION PROPOSÉE — à déposer AVANT de la jouer

Découpler l'acquisition de l'observateur de l'exposition de l'escouade : poser d'abord
l'ennemi et l'observateur, lui laisser ses 30 s, **puis seulement poser l'escouade** et
ouvrir la fenêtre dans la foulée. L'exposition du témoin retombe de 60 s à 30 s sans rien
retirer à l'observateur, et les trois bras restent appariés. Ce n'est pas un assouplissement
du seuil : c'est le retrait d'un artefact que le seuil a correctement détecté.

⚠️ Cette réparation exige un **nouveau dépôt écrit avant lancement** et compte comme une
**seconde tentative**.

## UNE FAUTE DE MONDE RÉPARÉE EN COURS DE ROUTE, ET DÉCLARÉE

Les serveurs de cette sonde mouraient silencieusement toutes les ~5 min. Cause trouvée :
`nuit_natif.sh` et 15 autres scripts du dépôt font `pkill -f arma3server_x64`, qui tue
**tous** les serveurs Arma de la machine. Parade sans toucher au travail voisin : lancer
sous un lien dur nommé `arma3server_dr64`. Rendement passé de 1 lot sur 4 à **20 sur 20**.
Les 20 répétitions déposées ici sont toutes postérieures à cette réparation.
