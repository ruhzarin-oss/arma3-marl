# VERDICT — L'ARC N'EST PAS RETENU

Tentative **unique**, pré-enregistrée dans `DEPOT_ARC_PREENREGISTRE.md`.
Mesurée le 14/08/2026. Journal intégral : `journaux/ARC_verdict_14-08.txt`,
sha256 `490ae6c56530180fe828211f…`. Intégrité vérifiée : 1 en-tête, 1 verdict,
1 bloc de porte, 3 bras, 0 itération dupliquée.

## Les trois bras — 800 itérations de 256 épisodes, 14 entrées, 10 actions

| bras | prise | mètres |
|---|---|---|
| **SANS** (référence) | **51,1 %** | **114,8** |
| **ARC** (+2 nombres : l'arc de tir) | 10,3 % | 70,3 |
| **BRUIT** (+2 nombres aléatoires — contrôle nul) | 4,3 % | 80,5 |

## La porte, lue sur la borne, appariée par graine

| | écart | borne | |
|---|---|---|---|
| ARC contre SANS | −40,8 pt | −43,4 | **TOMBE** — le dépôt exigeait ≥ +5 |
| BRUIT contre SANS | −46,8 pt | −49,6 | le **contrôle nul PASSE** : le bruit ne franchit pas le seuil |
| anti-planque | 70,3 m contre 114,8 m | | **TOMBE** |

## Ce que ça dit

**L'arc ne coûte pas zéro — il coûte 40,8 points.** Et il n'est que **6 points meilleur
que deux nombres tirés au hasard**. Il tombe aussi sur la porte anti-planque : l'agent
qui reçoit l'arc avance 70 m au lieu de 115. Lui donner l'arc lui apprend à se planquer,
pas à manœuvrer.

## Ce que ça NE dit PAS — réserve posée à la lecture

Les deux bras s'effondrent, l'arc comme le bruit. L'essai **ne sépare pas** :

- « l'arc ne porte aucune information exploitable », de
- « deux entrées de plus coûtent plus cher que 800 itérations ne peuvent rembourser ».

Le contrôle nul a fonctionné — il détecte que le bruit n'aide pas — mais il n'arbitre pas
cette alternative. Toute lecture future devra le dire.

## Ce que ça renverse

Le résultat `agent-percoit-pas-manoeuvre` (« l'agent est aveugle à l'arc ; +2 nombres →
exposition −28 % ») a été mesuré dans **l'ancienne sandbox**, avant le monde de fidélité.
Dans le monde mesuré, les deux mêmes nombres coûtent 40,8 points de prise.
**Ce résultat est retiré** et rejoint le registre des sursitaires.

## Statut

**Consommé.** Le dépôt fixait une tentative unique et un seuil de 5 points ; le bras a
rendu −40,8. On ne rejoue pas, on ne retouche pas, on n'ajoute pas une treizième idée à
la perception — **c'est l'algorithme qui se redépose.**

⚠️ **Aucun verdict de mission.** Le monde est le nôtre ; Arma tranchera.

## Note de cohérence interne

Le bras SANS rend **51,1 % de prise**, exactement le chiffre de la boucle fermée. Les
deux mesures sont indépendantes et concordent. Ce chiffre reste **non citable comme
transféré** tant que le banc live n'a pas rejoué avec le contrat réparé ⟨Fable⟩.
