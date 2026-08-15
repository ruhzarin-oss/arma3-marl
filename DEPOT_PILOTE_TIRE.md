# Dépôt — les attaquants en mode PILOTE tirent-ils ? Critères AVANT

Déposé le 15/08/2026. L'examen du prévol a rendu un raté instructif : son test T4 trouve
**zéro balle** chez des hommes en mode `pilote` (`AUTOCOMBAT` et `FSM` coupés) **avec une
cible acquérable**, alors que les balayages faisaient tirer des hommes en `COMBAT`/`RED`
à FSM active.

**Le mode `pilote` est celui que le banc live emploie pour la politique apprise.**

## QUELLE DÉCISION CETTE MESURE FAIT BASCULER

**Si les attaquants ne tirent pas en mode pilote** → les 67 épisodes ne mesurent pas un
assaut mais **une marche sous le feu sans arme utilisable**. Les 11,9 % et les 17/20
anéantissements changent de sens, et le premier chantier devient **rendre le feu à l'agent**,
avant tout retypage de couvert ou remontée de couture.

**S'ils tirent** → le raté de T4 est un défaut de mon test seul, et rien ne bouge.

## Le dispositif

La scène du banc live, à l'identique : 4 attaquants, 4 défenseurs, 170 m, site (4644, 5652).
60 secondes. On compte les `Fired` **des attaquants**.

Trois bras :
- **PILOTE** — `AUTOCOMBAT` + `FSM` coupés, `PATH` gardé (ce que le banc live fait) ;
- **NATIF** — aucun `disableAI` ;
- **PILOTE+CIBLE** — mode pilote, mais on leur **désigne** l'ennemi (`reveal` + `doTarget`),
  pour séparer « ils ne peuvent pas tirer » de « ils ne savent pas qui viser ».

## CONTRÔLE POSITIF ⟨règle 16⟩

**Les DÉFENSEURS doivent tirer dans les trois bras.** Ils sont en `COMBAT`/`RED`, `PATH`
coupé — leur silence signifierait que le banc lui-même ne produit aucun engagement, et
alors rien ne se lit.

## Les lectures, déposées

| coups des attaquants, bras PILOTE | lecture |
|---|---|
| **0** | **ILS NE TIRENT PAS.** Le banc live n'a jamais mesuré un assaut. |
| **≥ 10** | ils tirent ; le raté de T4 est un défaut de mon test. |
| **1 à 9** | INDÉCIS. On ne conclut pas. |

Et `PILOTE+CIBLE` sépare la cause si `PILOTE` rend 0.

## Ce qui n'est PAS promis

Si les attaquants ne tirent pas, ça n'explique pas **tout** l'écart de transfert — le
gymnase leur donne un feu qu'Arma leur refuse, mais le couvert mal typé et le cliquet
d'exposition restent des désaccords établis par ailleurs.
