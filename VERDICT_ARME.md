> SURSITAIRE le 16/08/2026 — mesure prise SANS prevol. Le temoin naissait a 300 m au hasard
> sur le meme relief : le regime a 28 pourcent d echec existait probablement deja, non compte.
> Le bandeau emporte les DEUX moities: le 44,8 % ET le  le gymnase surestime d un tiers .
> Voir DEPOT_REPARATION_TEMOIN.md.

# VERDICT — L'AGENT ARMÉ PREND L'OBJECTIF PRESQUE UNE FOIS SUR DEUX

Mesuré le 16/08/2026. 67 épisodes, banc live 4 contre 4, site (4644, 5652), corps réparé,
**attaquants en `combatMode "RED"`**. Critères de `DEPOT_20_EPISODES.md`, repris à
l'identique pour la quatrième fois.

## Les trois contrôles positifs passent

- scène confirmée par **le jeu** : `def=4 att=4` sur **67/67** ;
- azimuts de naissance : écart-type **96,4°** (porte > 60) ;
- **`enmain=4`** — les quatre hommes ont l'arme en main à chaque épisode. *C'est le champ
  ajouté hier soir après la découverte du désarmement ; il est ici la preuve que la
  correction a mordu.*

## LE RÉSULTAT

| | **ARMÉS** | désarmés (`BLUE`) | Fisher |
|---|---|---|---|
| **PRISE** | **30/67 = 44,8 %** | 8/67 = 11,9 % | **p = 4,0 × 10⁻⁵** |
| IC95 | **[32,9 ; 56,7]** | [4,2 ; 19,7] | |
| tous morts | **27/67 = 40 %** | 57/67 = 85 % | **p = 1,2 × 10⁻⁷** |
| **gel** | **5/67 = 7,5 %** | 17/67 = 25,4 % | **p = 0,009** |
| durée médiane | 29 pas | 17 pas | |
| actions distinctes (médiane) | 3 | 2 | |

**Un seul mot rendu — `RED` au lieu de `BLUE` — quadruple la prise, divise la mortalité
par deux, et fait disparaître le gel.**

## Le gel n'existait pas

`5/67 = 7,5 %`, IC95 **[1,2 ; 13,8]** — **qui contient les 3,1 % du gymnase.**

Ce que j'ai appelé pendant deux jours « la politique est dégénérée sur Arma », établi à
p < 10⁻⁶ et déposé comme un fait, était **un homme à qui on avait interdit de tirer**.
Le fait était vrai, sa cause était ailleurs, et sa disparition le prouve.

## L'écart de transfert ne tient plus que de justesse

**44,8 % contre 59,4 %.** L'intervalle d'Arma est [32,9 ; 56,7] : le gymnase reste dehors,
mais **de peu**. Fisher contre le gymnase : **p = 0,038**, contre 2,2 × 10⁻⁴ hier.

**Je ne dis donc pas que le transfert est acquis** — il reste statistiquement au-dessus.
Je dis que l'écart est passé de 47 points à 15.

## Ce que ça annule

Tout ce qui a été conclu sur des hommes désarmés est **sans objet** :
`VERDICT_TRANSFERT.md` (0/20), `VERDICT_67.md` (11,9 % et le gel « réel »),
`VERDICT_SERIE3.md` (3/20), le flanc à 0/18, et la lecture du gel comme symptôme d'une
politique dégénérée. Les séries sont archivées sous `_BLUE_desarme` et ne se relisent pas.

**Restent debout, parce qu'ils ne dépendaient pas de ça** : le couvert du gymnase protège
sans cacher ; le couvert est 3× plus loin sur Arma ; `setVelocity` est une impulsion ;
le tarif n'explique pas l'écart ; le classement des quatre bras au gymnase.

## Deux réserves

1. **Cette série n'a pas tourné sous le prévol du socle.** Elle a bénéficié de la
   correction, pas de la garantie. Le prochain run passera par `HMT_JOUER`.
2. Le gymnase reste **au-dessus statistiquement**. 15 points d'écart demandent encore une
   explication, et les candidats sont déjà mesurés : couvert mal typé, exposition sommée
   au lieu du cliquet.

## Ce que ça dit du travail lui-même

Deux jours de conclusions noires venaient **d'un mot dans une ligne de mise en scène**.
Aucun verdict faux n'a survécu — les contrôles déposés les ont tous rattrapés — mais
aucun contrôle ne demandait *« mes hommes ont-ils tiré ? »*. C'est exactement la règle 16
dans son énoncé le plus simple : **on vérifiait des états, jamais l'acte.**

C'est maintenant le test **T4** du prévol, et il ne repassera plus.
