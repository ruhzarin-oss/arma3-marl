# Dépôt — ESSAI A : l'ordre fait-il quelque chose ?

Déposé le 14/08/2026, **avant toute mesure**. Décidé par Fable après quatre campagnes
sans verdict.

## La question

Le bras natif ne tire que sur le terrain 0 (347 coups contre 0-4 sur les cinq autres),
alors que **90 ordres partent sur chacun des six terrains**. Deux lectures possibles :

- **(i)** l'ordre marche sur le terrain 0 et le moteur le refuse ailleurs ;
- **(ii)** l'ordre ne marche nulle part, et le terrain 0 tire par **contact spontané** —
  auquel cas **mon bras natif n'a jamais existé** et le banc n'a jamais testé la
  suppression, sur aucun terrain, dans aucune campagne.

## Le dispositif

Terrain 0 seulement. Deux bras alternés, 3 répétitions chacun, **même monde, même
session** :

- **bras 2** — natif, ordre `commandSuppressiveFire` réémis toutes les 4 s (à l'identique)
- **bras 3** — **NOUVEAU** : préparation strictement identique au bras 2 (armé, munitions
  regarnies par `HMT_DOTER`, `setCombatMode "RED"`, révélation des victimes), **et aucun
  ordre n'est émis**. La seule différence entre les deux bras est l'ordre.

## Contrôle positif de l'instrument ⟨Fable, clause 1 du 14/08⟩

**Le bras 2 doit retirer plus de 100 coups sur le terrain 0.** C'est le phénomène connu
massif (347 mesurés). S'il ne le fait pas, l'instrument n'a pas reproduit ce qu'il doit
voir : **le run est NUL et ne se lit pas.** Aucune lecture du bras 3 n'est admissible
sans ce préalable.

## Les trois lectures, déposées avant

| coups du bras 3 (sans ordre) | lecture |
|---|---|
| **> 100** | l'ordre n'explique rien. Le terrain 0 tire par contact. **Le bras natif n'a jamais existé** : les quatre campagnes sont sans objet et l'étage 1 se rebâtit. |
| **< 20** | l'ordre EST la cause du tir. La panne des cinq autres terrains est du côté de l'**accord** du moteur, pas de la demande → essais B et C. |
| **20 à 100** | **indécis. On ne conclut pas** et on ne rejoue pas ce même essai en espérant mieux. |

La bande indécise est déposée exprès : sans elle, tout résultat serait lisible dans le
sens qui m'arrange.

## Ce qui rendrait cette mesure fausse

- Si le bras 3 tire parce qu'il a reçu un ordre par ailleurs (résidu du tour précédent) :
  la préparation appelle `_x doTarget objNull; _x doWatch objNull` à chaque départ, et
  le canal `BALLE` relèvera la cible que chaque appui s'est donnée.
- Si les deux bras ne voient pas le même monde : ils jouent alternés sur le même
  `HMT_POSER`, dans la même session.

## Taille

6 essais, une séance. **Pas une nuit.** Le tarif était le vrai défaut : deux hypothèses
réfutées à 36 essais pièce.
