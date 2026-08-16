# DÉPÔT — LA PORTE NE COUVRAIT PAS LE MONDE OÙ LA NUIT TOURNAIT

16/08/2026, ~23 h. Nuit NATIF **coupée** à 34 lancements sur 134.

## Le fait

| | tirages | verts | rouges | cause |
|---|---|---|---|---|
| porte, `prevol.py normal` (21 h) | 50 | 48 | 2 | T4 sans vue |
| nuit, `banc_live.py natif` (22 h) | 34 | **10** | **24** | **T5 IMMOBILE, 24 fois sur 24** |

**70 % de rouges contre 4 %.** Le prévol certifié zéro rouge sur cinquante en rougit 24 fois
sur 34 deux heures plus tard, sur le même hash `5741a81`.

## La faute, et elle est à moi

**J'ai certifié le prévol dans un contexte et armé la nuit dans un autre.** `prevol.py`
crée la scène et appelle le prévol. `banc_live.py natif` envoie **entre les deux** un réveil
qui rend l'IA entière à tout le monde :

```
{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_ENNEMI;
{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_FR;
```

La porte n'a jamais vu ce monde. Elle a mesuré un instrument dans un monde au repos, et
j'ai armé 134 épisodes dans un monde où quatre défenseurs sont pleinement actifs.

Fable avait écrit : *« la porte certifiera CE hash, rien d'autre. »* Je l'ai lu comme une
contrainte sur le **code**. C'en est aussi une sur le **monde** : une porte certifie un
instrument **dans les conditions où elle l'a éprouvé**, et nulle part ailleurs.

## Ce qui n'est PAS établi

- Que le prévol soit fautif. Il refuse peut-être **à juste titre** : un homme sous le feu de
  quatre défenseurs actifs ne parcourt pas 24 m, et T5 le dirait correctement.
- Que les 10 épisodes valides soient bons ou mauvais. **Aucun `.npz` n'a été ouvert**, et
  aucun ne le sera : 10 sur 67, la règle de complément l'interdit.

## La sonde — quatre causes, une passe, écrites avant

Symptôme : T5 rouge 24/34 avec réveil natif, 0/50 sans réveil.

- **(a) LES DÉFENSEURS TIRENT SUR LE TÉMOIN.** Le réveil les rend actifs ; le témoin naît
  dans leur champ. → régime natif rouge, régime politique vert, et le témoin est **connu**
  des ennemis (`knowsAbout` > 0).
- **(b) LE RÉVEIL ATTEINT LE TÉMOIN.** Mon `disableAI "AUTOCOMBAT"` serait défait.
  → `checkAIFeature "AUTOCOMBAT"` du témoin **vrai** au moment de T5.
- **(c) LE SERVEUR NEUF.** Un serveur qui vient de démarrer n'est pas dans le même état que
  le cinquantième prévol d'une session. → les deux régimes rougissent également, et le
  premier tirage de la porte aurait dû rougir aussi.
- **(d) LE HASARD DES POSITIONS.** → corrélation avec la pente et le lieu déjà journalisés,
  et pas d'écart entre les deux régimes.

**Le banc alterne les deux réveils tirage par tirage, sur le même serveur.** Seul le réveil
change ; tout le reste est tenu.

## Ce qui est dû, quoi qu'il arrive

La porte devra être repassée **dans le bras où les épisodes seront joués**, et pas ailleurs.
Une porte par bras. C'est le cliquet de cette faute.
