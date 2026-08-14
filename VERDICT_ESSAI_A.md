# VERDICT — ESSAI A : le bras natif n'a jamais existé

Mesuré le 14/08/2026. Critères déposés avant la mesure dans `DEPOT_ESSAI_A.md`.
Terrain 0, même session, bras alternés, 3 répétitions chacun.

|  | n | coups par essai | total | murs | corps | supp moy |
|---|---|---|---|---|---|---|
| **bras 2 — AVEC ordre** | 3 | 289, 274, 252 | **815** | 347 | 175 | 0,521 |
| **bras 3 — SANS ordre** | 3 | 259, 262, 244 | **765** | 272 | 339 | 0,668 |

**Contrôle positif : PASSÉ** (bras 2 à 815 coups, seuil déposé à 100).

## Le verdict

**94 % du feu part sans qu'aucun ordre ne soit donné.** `commandSuppressiveFire` réémis
toutes les 4 secondes ajoute 50 coups sur 765. Le terrain 0 ne tirait pas parce que
l'ordre y passait : il tirait par **contact spontané**, et les cinq autres terrains ne
tiraient pas parce que leurs appuis **n'ont jamais été en contact**.

**Les quatre campagnes de l'étage 1 n'ont pas comparé « suppression ordonnée » contre
« rien ». Elles ont comparé « appuis armés en contact » contre « appuis désarmés ».**
Ce n'est pas le cahier des charges, qui portait sur la suppression comme *décision*.

## Ce que l'ordre fait quand même — et c'est net

Il ne déclenche pas le feu, il le **redirige**. Sur les trois paires, sans exception :

- **murs** : 118, 131, 98 avec ordre contre 93, 94, 85 sans → 3/3
- **corps** : 59, 55, 61 avec ordre contre 141, 106, 92 sans → 3/3

Sans ordre, les appuis tirent **deux fois plus au corps**. Avec ordre, ils battent la
lisière. L'ordre est donc un **répartiteur de visée**, pas un déclencheur de feu.

## Ce que je n'affirme PAS

La suppression délivrée semble plus haute sans ordre (0,668 contre 0,521), mais
**ce n'est pas établi** : 0,451 / 0,586 / 0,526 contre 0,761 / 0,758 / 0,486 — la
troisième paire s'inverse. 2 sur 3 n'est pas un résultat. Non cité.

## Conséquences

1. **Les essais B et C de Fable sont sans objet.** Ils cherchaient quelle porte du moteur
   refuse l'ordre sur cinq terrains. La question ne se pose plus : l'ordre ne déclenchait
   rien nulle part.
2. La vraie panne des terrains 1 à 5 est **l'absence de contact** entre appuis et
   défenseurs, pas un refus moteur. C'est une faute de **placement**, dans mon banc.
3. L'étage 1 se rebâtit sur une autre mécanique de suppression, ou se pose autrement.
   **Gel des campagnes confirmé.**

## Le coût, pour mémoire

Quatre campagnes, 144+ essais, deux diagnostics faux — pour une réponse que **six essais
en vingt minutes** ont rendue. Fable : *« Le défaut n'était pas ton jugement, c'était le
tarif. »*
