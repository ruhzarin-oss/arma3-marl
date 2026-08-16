# CONTRÔLE POSITIF DU LIEN DRONE→SOLDAT — TENTATIVE N° 2, déposée avant lancement

*16 août 2026. Tentative n° 1 : **ÉCHEC**, P2 tombée à 3/20 pour un seuil de ≤ 2/20. Elle
reste un échec au registre et ne sera jamais relue comme un passage (`DEPOT_CONTROLE_DRONE.md`).*

*⟨Fable, sur la réparation⟩ « Un réglage touche la porte ou relit la tentative échouée comme
un passage ; une réparation touche la scène et produit une prédiction falsifiable. »*

## CE QUI CHANGE, ET RIEN D'AUTRE

**Un seul changement de scène : l'attente de 30 s disparaît.**

Elle n'existait que pour laisser à l'observateur aérien le temps d'acquérir sa cible. Elle
était imposée aux trois bras par équité — correctement — mais elle **doublait l'exposition de
l'escouade**, de 30 s à 60 s. Les 3 répétitions qui ont fait tomber P2 portaient toutes un
témoin d'ouverture non nul : elles avaient détecté **pendant cette attente**, pas pendant la
mesure. Le témoin payait une dette qui n'était pas la sienne.

**Le bras A1 est retiré.** Il existait pour attraper une fuite native du **drone** vers le sol.
Or c'est déjà répondu, et par une mesure séparée : pour un drone, ce canal **n'existe pas**
(UAV `knowsAbout` = 0, y compris cloué à 148 m au-dessus de la cible). Tel que joué, A1
mesurait la fuite d'un **hélicoptère à équipage** — qui n'est pas l'objet. Sans observateur
aérien, plus aucune raison d'attendre : l'attente tombe à **5 s**, identiques pour les deux bras.

⛔ **Les seuils ne bougent pas.** P1 et P2 sont recopiés à l'identique.

## LE MONTAGE — deux bras APPARIÉS par scène

Origine `[4644, 5652]` sur Stratis, socle **figé 1.10.0** (`sha256 91269784…`), mods du juge.
Un azimut tiré par répétition, joué par les deux bras.

- Escouade : 4 × `B_Soldier_F`, mode **`natif`** — aucun `disableAI`, aucun tir forcé.
- Ennemi : 1 × `O_Soldier_F` à **300 m DERRIÈRE**, hors du cône. Inerte, indestructible, il ne
  tire jamais (compteur vérifié).
- Ligne de vue **≥ 0,5** vérifiée au moteur, 20 azimuts essayés.
- Attente **5 s**, fenêtre **30 s**, identiques dans les deux bras.

| bras | tuyau `reveal` | ce qu'il répond |
|------|----------------|-----------------|
| **A0** | coupé | l'escouade est-elle vraiment aveugle ? |
| **B**  | niveau 4, chaque seconde | le canal existe-t-il ? |

## LES PORTES — inchangées

> **P1 · le canal existe.** Bras B : **≥ 18/20** répétitions valides portent au moins un
> `Fired`, **et** médiane du temps au premier tir **≤ 8 s**.
>
> **P2 · aveugle sans lui.** Bras A0 : **≤ 2/20** répétitions valides portent un `Fired`.

## LA CONDITION DE VALIDITÉ — nouvelle, et déposée avant

> **Une répétition n'est VALIDE que si le témoin d'ouverture est nul dans les DEUX bras :
> `saitgrp0 < 1,5`. Sinon elle est VOID.**

Elle est licite parce qu'elle vérifie la **prémisse** du bras — l'escouade ignore l'ennemi
à t0 — et non son résultat. Une répétition où l'escouade savait déjà avant le début ne teste
rien : ni l'aveuglement, ni le canal.

⚠️ **Elle ne doit pas devenir une trappe à données.** Plafond inchangé : **plus de 4 VOID sur
20 et on ne lit pas.**

## LA PRÉDICTION FALSIFIABLE — c'est elle qui juge la réparation

> **Si la réparation est la bonne, le témoin d'ouverture est nul sur 20/20, dans les deux
> bras.** La tentative n° 1 en comptait 3 sur 20 en A0 et 1 sur 20 en B.

C'est vérifiable indépendamment des portes, et c'est ce qui distingue une réparation d'un
desserrage : si les VOID restent nombreux, la réparation a **échoué**, quoi que disent P1 et P2.

## CE QUI FERAIT ÉCHOUER — écrit avant

- **P1 tombe** → `reveal` n'est pas le canal, ou l'escouade ne peut pas tirer. Instrument mort.
- **P2 tombe ALORS QUE le témoin d'ouverture est nul partout** → ce ne sont plus les 30 s
  d'attente : **ce sont les LIEUX qui fuient**. On répare alors la géométrie — distance,
  choix des azimuts — **jamais le seuil**. Les azimuts 77 et 235 sont déjà suspects : ils ont
  fait tirer les deux bras dans la tentative n° 1.
- **Plus de 4 VOID** → la réparation a échoué, on ne lit pas.
- **L'ennemi tire** → répétition VOID, comptée et déclarée.

## CE QUE CE CONTRÔLE NE PROMET TOUJOURS PAS

Qu'un drone paie. Que le banc sache payer l'information — la porte oracle reste **à franchir
après**, et elle n'est pas dans ce dépôt.

## CE QUE LA MESURE DU DRONE A DÉJÀ CHANGÉ AU PROJET

Le moteur n'ayant **aucun canal drone→IA**, `reveal` ne sonde pas un mécanisme du monde :
**il EST la liaison drone, écrite à la main.** Le banc n'observe pas un drone simulé, il
implémente une hypothèse de liaison. Niveau, cadence et latence deviennent des **paramètres
de modèle** à justifier — et à calibrer sur l'étalon d'infanterie, qui donne le prix du
« voir » : **2,87 en 10 s à 300 m**.

⟨Fable⟩ *« Dans Arma, un drone est un décor plus un script. »*
