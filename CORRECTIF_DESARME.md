# Correctif à VERDICT_DESARME.md — le coupable est `combatMode BLUE`, pas `AUTOCOMBAT`

Déposé le 15/08/2026, une heure après le verdict qu'il corrige.

## Ce que j'avais écrit

Que `disableAI "AUTOCOMBAT"` retire la faculté d'engager, et que c'est lui qui désarmait
les attaquants du banc live.

## Ce que la mesure dit

Quatre bras, même scène, déplacement piloté par `setVelocity` :

| bras | coups | mètres gagnés |
|---|---|---|
| **A — les deux `disableAI` maintenus** | **145** | **154** |
| B — `AUTOCOMBAT` rendu | 60 | 149 |
| C — `FSM` rendu | 65 | 154 |
| D — les deux rendus | 14 | 111 |

**Le bras A tire 145 coups avec exactement les deux `disableAI` que j'accusais.**

## Le vrai mécanisme

La seule différence entre ce bras A et le bras muet de la mesure précédente :

```sqf
// muet      : _u setBehaviour "AWARE";  _u setCombatMode "BLUE";
// qui tire  : _u setBehaviour "COMBAT"; _u setCombatMode "RED";
```

**`combatMode "BLUE"` signifie « ne jamais tirer ».** C'est sa définition dans le moteur.
Le banc live le pose sur tous les attaquants.

**Le désarmement tient à un mot, pas à une faculté d'IA.**

## Ce qui TIENT du verdict précédent

**Les attaquants n'ont jamais tiré en 67 épisodes.** Le fait est confirmé, seule son
attribution était fausse. Tout ce qui en découle reste vrai : les 11,9 %, les 17/20
anéantissements, le flanc à 0/18 et le gel ont été obtenus par des hommes qui ne
ripostaient pas.

## Ce que ça change en mieux

Le bras A garde **les deux `disableAI`** — donc la politique garde le contrôle **complet**
du déplacement (154 m, autant qu'avant) **et** les hommes tirent.

Et rendre les deux facultés à l'IA (bras D) est le **pire** des quatre : 14 coups, 111 m.
L'IA se met à piloter contre la politique. **La configuration actuelle était la bonne à
un mot près.**

## Aveu

C'est le troisième diagnostic corrigé en un jour, et le deuxième où **j'ai publié une cause
avant de l'avoir isolée**. La mesure qui l'a corrigé a coûté cinq minutes — je l'aurais eue
pour le même prix avant de déposer.
