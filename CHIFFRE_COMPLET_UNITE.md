# LE CHIFFRE COMPLET — sonde d'unité, 12 sessions × 6 tirages

17/08/2026, ~04 h. Socle gelé `1.13.0`, régime de la nuit. Aucun serveur démarré pour ce
dépouillement : il relit les journaux existants.

```
  session   rang → 1 2 3 4 5 6    verts  T5  T7
     1             5 5 5 5 5 5      0     6   0
     2             5 5 5 5 5 5      0     6   0
     3             7 . . 5 . 5      3     2   1
     4             5 5 . 5 5 5      1     5   0
     5             5 5 5 5 5 5      0     6   0
     6             5 . . . 5 .      4     2   0
     7             . . . . . .      6     0   0
     8             5 5 5 5 5 5      0     6   0
     9             5 5 5 5 5 5      0     6   0
    10             7 7 7 7 7 7      0     0   6
    11             5 . . . . .      5     1   0
    12             5 5 5 5 5 5      0     6   0
```

**72 tirages · 19 verts (26 %) · T5 = 46 · T7 = 7 · T4 = 0**

## Quatre faits, par ordre d'importance

### 1 · T4 n'a JAMAIS échoué — 0 sur 72
Le témoin tire, toujours. C'est le seul test du prévol qui soit stable, et c'est aussi le
seul qui ait reçu son **contrôle positif** (sabotage des munitions, 3 rouges sur 3). Le lien
n'est pas prouvé, mais il est noté.

### 2 · Les échecs T7 se GROUPENT dans une seule session — 6 sur 7
La session 10 est **entièrement T7** : le canal de feu de l'homme servi est muet **toute la
session**, et T5 y passe six fois sur six. Fable avait demandé exactement ça : *« si les
3 rouges de T7 se groupent dans une session, c'est une information structurale majeure. »*

> **Deux canaux intermittents PARTAGENT la même unité, et une session ne casse pas toujours
> la même chose.** Un serveur naît avec un défaut, et le défaut varie.

### 3 · Le rang 1 est rouge dans 11 sessions sur 12
| rang | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| verts / 12 | **1** | 4 | 5 | 3 | 3 | 3 |

Le premier tirage est **structurellement** le pire. L'hypothèse d'échauffement, que j'avais
déclarée « réfutée à l'envers » hier soir, **n'était pas réfutée** — elle était testée avec
un bras d'une seule session. Elle revient, et cette fois avec une pièce à n=12.

### 4 · Deux populations nettes
- **7 sessions irrécupérables** (1, 2, 4, 5, 8, 9, 12) — T5 rouge du début à la fin ;
- **3 sessions qui démarrent mal puis tiennent** (3, 6, 11) ;
- **1 session T7 pure** (10) · **1 session parfaite** (7).

## LE FILTRE EN TÊTE N'EST PAS ÉVALUABLE — et je retire ce que j'ai annoncé

Mon dépouillement précédent a imprimé « **LE FILTRE TIENT** (P = 1,00 ≥ 0,80) ».
**C'est faux, et je le retire.** Cette probabilité repose sur **une seule session**.

**Mon critère, écrit avant, fixait le seuil et PAS le `n` minimum.** C'est exactement la
faute de la médiane non déclarée au banc des jambes : un critère incomplet laisse la lecture
choisir. Et c'est la faute que Fable m'a reprochée cette nuit — lire un seuil franchi sans
puissance.

> **CLIQUET** — tout critère chiffré déclare, dans la phrase qui le pose : la grandeur, la
> **statistique**, le seuil, **et le `n` minimum en deçà duquel il ne se lit pas**.

Ce qui **est** lisible : un contrôle en tête de session jetterait **11 serveurs sur 12**,
dont **2 qui deviennent bons ensuite**. À 26 % de tirages verts, ce filtre-là ne finance
aucune campagne.

## La piste, mesurée mais insuffisante

**Jeter le rang 1** (échauffement) et contrôler au **rang 2** : 4 sessions, **3 exploitables**.
Trop peu pour un verdict — mais c'est la seule piste que les données soutiennent, et elle se
mesure sans rien inventer.

## Ce que je ne fais pas

Pas de huitième hypothèse cette nuit. Le prochain geste est une sonde d'échauffement au
niveau de la **session** — n déclaré, seuil déclaré, `n` minimum déclaré — et elle se décide
à froid.

Aucun `.npz` ouvert.
