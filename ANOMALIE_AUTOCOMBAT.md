> ✅ **CLOSE le 16/08/2026 — NON CONFIRMEE.** Trois mesures (11 lectures pas-a-pas,
> le format innocente, 7 lectures sur l engagement soutenu) montrent que 
> prend et TIENT. L attribution des 44,8 % est retablie. Voir .

# Anomalie ouverte — `disableAI "AUTOCOMBAT"` ne prend pas sur les attaquants du banc

Constatée le 16/08/2026 par la sonde du témoin. **Non expliquée, non devinée.**

## Le fait

| | coups en 6 s | mètres en 4 s | `AUTOCOMBAT` |
|---|---|---|---|
| témoin du socle (mode `pilote`) | **0** | 24 | **false** |
| **attaquant de la scène** | **13** | 14 | **true** |
| témoin posé au lieu même de la scène | **0** | 14 | **false** |

Le tir suit `AUTOCOMBAT`, et le troisième bras **réfute la cause du lieu**.

## L'anomalie

`banc_live.py` appelle explicitement, sur chaque attaquant :

```sqf
_u disableAI "AUTOCOMBAT"; _u disableAI "FSM";
```

Et `checkAIFeature "AUTOCOMBAT"` rend **true** sur ces mêmes hommes. **L'ordre ne prend pas.**

Trois pistes possibles, **aucune testée** : un rappel ultérieur qui le réactive (comme `WAKE`
l'a fait pour `FSM` le 15/08) ; un effet du `setCombatMode "RED"` posé après ; ou une
différence entre l'ordre des appels dans la scène et dans `HMT_PILOTER`.

## Pourquoi ça compte au-delà du prévol

Toute l'architecture du banc suppose que la politique décide **à la place** de l'IA, ce que
`disableAI "AUTOCOMBAT"` est censé garantir. Si l'ordre ne prend pas, **l'IA d'Arma choisit
ses cibles en parallèle de la politique** — et les 44,8 % de prise mesurés ce matin sont
ceux d'un attelage, pas d'une politique seule.

**Ça ne les invalide pas** : ils restent la mesure de ce que le banc produit réellement.
Mais leur attribution — « la politique apprise obtient 44,8 % » — n'est pas établie.

## Ce qu'il faut mesurer (pas deviner)

Une passe, trois lectures de `checkAIFeature "AUTOCOMBAT"` sur le même homme : juste après
le `disableAI`, après le `setCombatMode`, et après le `WAKE`. La ligne où il repasse à
`true` nomme la cause.

## En attendant

Le témoin du prévol passe en mode **`temoin`**, qui garde `AUTOCOMBAT` — il doit pouvoir
tirer pour **prouver qu'une balle part**. C'est un contournement assumé du blocage, pas une
réparation de l'anomalie.
