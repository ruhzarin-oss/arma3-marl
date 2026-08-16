> ⛔ **ANNULÉ le 16/08/2026** — mesure faite avec les attaquants en `combatMode "BLUE"`,
> qui signifie « ne jamais tirer ». Les hommes n'ont pas combattu. Voir `REGISTRE_BLUE.md`
> et `VERDICT_ARME.md` (30/67 = 44,8 % une fois armés).

# VERDICT — L'AGENT N'A JAMAIS TIRÉ. Le banc live mesurait une marche sous le feu.

Mesuré le 15/08/2026. Critères déposés avant dans `DEPOT_PILOTE_TIRE.md` (`d14fe8b`).
Trouvé **gratuitement** par l'examen du prévol, dont le test T4 rendait zéro sur un monde sain.

## Le résultat

| bras | coups des ATTAQUANTS | coups des défenseurs | distance finale |
|---|---|---|---|
| **PILOTE** (le mode du banc live) | **0** | 39 | 24 m |
| **NATIF** (IA entière) | **127** | 365 | 57 m |
| **PILOTE + cible désignée** | **1** | 41 | 39 m |

**Contrôle positif PASSÉ** : les défenseurs tirent dans les trois bras.

## La lecture, déposée avant

**0 coup → ILS NE TIRENT PAS.** Et le troisième bras sépare la cause : leur **désigner**
l'ennemi ne donne qu'un coup. Ce n'est pas qu'ils ignorent qui viser — **ils ne peuvent
pas tirer.**

`disableAI "AUTOCOMBAT"` retire à l'homme la faculté d'engager. Le banc live l'applique à
tous les attaquants, depuis toujours, pour que la politique décide à leur place.

## Ce que ça recontextualise

**Les 67 épisodes ne mesurent pas un assaut. Ils mesurent une marche sous le feu, sans arme
utilisable.**

- la prise à **11,9 %** : obtenue par des hommes désarmés en pratique ;
- les **17/20 anéantissements** : ils avancent et se font tuer sans riposter ;
- le **flanc à 0/18** : même mode, même infirmité ;
- le **gel** : une politique qui n'a que ses jambes n'a pas grand-chose à faire varier.

Détail qui achève le tableau : **les hommes pilotés finissent PLUS PRÈS de l'objectif
(24 m) que l'IA native (57 m)** — parce qu'ils marchent tout droit pendant que l'IA
s'arrête pour combattre.

## La tension, nommée

La politique veut **les jambes** et laisse le fusil à Arma. Mais Arma **couple les deux** :
couper `AUTOCOMBAT` retire l'engagement en même temps que le choix de cible.

⟨Fable, ce soir⟩ *« la sémantique est exécutée par Arma lui-même — les jambes restent
natives. »* Il faut le lire dans l'autre sens aussi : **le fusil doit rester natif.**

## Ce qui n'est PAS promis

Rendre le feu à l'agent n'explique pas **tout** l'écart de transfert. Le couvert mal typé
(scalaire contre directionnel) et le cliquet d'exposition (somme contre max irréversible)
restent des désaccords établis par ailleurs, sur d'autres mesures.

Et ce verdict repose sur **un essai par bras**. L'écart 0 contre 127 est trop gros pour
tenir au hasard, mais il n'est pas répété.

## Le geste qui suit

Rendre `AUTOCOMBAT` aux attaquants et ne piloter que le **déplacement**. Puis refaire les
67 épisodes. C'est le premier chantier, avant tout retypage de couvert et toute remontée
de couture — **on ne juge pas la tactique d'un homme à qui on a retiré son arme.**
