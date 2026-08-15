# Le limiteur est retiré — `setVelocity` est une impulsion, pas une consigne

Mesuré le 15/08/2026. Critères déposés avant dans `DEPOT_LIMITEUR.md` (`e0eba00`).

## La sonde à trois bras — les deux contrôles positifs passent

| bras | n | mètres par période de 3,28 s |
|---|---|---|
| **A — une seule émission** (le banc d'alors) | 10 | **2,58** |
| **B — réémission à 10 Hz** | 10 | **20,22** |
| **C — aucune émission** (contrôle nul) | 10 | **0,00** |

- **Contrôle 1** : le bras A reproduit la lenteur connue (2,58 m, le banc live en faisait 1,43
  sous le feu et sur terrain accidenté). La sonde mesure bien le banc.
- **Contrôle 2** : le bras C rend 0,00 m. Personne n'avance sans ordre.
- **La porte** (B > 10 m) est franchie largement : **20,22 m contre 19,7 attendus**
  à 6 m/s soutenus. `setVelocity` rend exactement la vitesse commandée — **à condition
  qu'on la réémette**.

## Après greffe, sur le gabarit d'action réel

**20,22 m par période**, FPS serveur 48,8. **Gain ×7,8 sur la sonde, ×14,1 sur ce que
faisait le banc live.**

Le jeton `HMT_NORDRE` coupe la boucle dès que l'ordre suivant arrive — sans lui, deux
boucles se disputeraient le même homme et la dernière émise gagnerait au hasard.

## Ce que le limiteur était vraiment

**Pas un accident : un arbitrage.** Le commentaire d'origine disait *« on tempère pour le
FPS »*, et une mesure ancienne du projet établit que `setVelocity` écroule les images par
seconde. Mais celui qui l'a posé a réglé une **vitesse** (6 m/s) en croyant que la commande
la tenait, alors qu'elle donne une impulsion. Le résultat n'était pas un corps tempéré,
c'était **un corps huit fois trop lent**.

## Le coût, honnêtement

48,8 FPS **à UN homme**. Le banc live en a quatre, la ferme jusqu'à quarante. **Non
extrapolable** — le FPS est désormais journalisé à chaque pas du banc, pour être mesuré
là où il compte plutôt qu'à côté.

## Ce qui n'est pas promis

Un corps réparé n'est pas un corps meilleur. Des hommes qui couvrent quatorze fois plus de
terrain peuvent simplement mourir plus vite ou plus loin. **`VERDICT_TRANSFERT.md` tient
tel quel** tant que les 20 épisodes n'ont pas été refaits — et ils pourront rendre 0.
