# Hiérarchie des métriques — déposée AVANT tout dépouillement par bras

*5 août 2026, 18h30. Le run tourne. **Aucun score par bras n'a été lu.***

## Pourquoi ce fichier existe

Le **+12,3 points** du 2 août mesurait la **tenue 60 secondes** — un objectif *pris et gardé*.

Or le monde recalibré se résout autrement. Sur les 95 accrochages du calibrage :

| cause de fin | n |
|---|---|
| chronomètre | 48 |
| élimination | 39 |
| **tenue** | **8** |

**Seulement 8 victoires par tenue.** Le « taux de prise » que je mesurais jusqu'ici est donc
surtout un taux d'**élimination**. Je risque de comparer deux bras sur une grandeur qui n'est
pas celle du fait fondateur.

> ⟨Fable, 05/08 : « c'est le seul point qui puisse invalider la nuit. Ce qui ne se rattrape
> pas hors ligne, c'est une métrique choisie APRÈS avoir vu les résultats. »⟩

Tout est dans les journaux et se recalcule hors ligne. Ce qui ne se recalcule pas, c'est
l'honnêteté du choix. D'où ce dépôt, horodaté par le commit qui le porte.

## La hiérarchie, fixée maintenant

**PRIMAIRE — la tenue.** Le verdict reconstruit au plus près du 2 août : un camp tient
l'objectif exclusivement pendant 60 secondes continues, et n'en était pas le propriétaire
initial. C'est `cause = prise` dans le journal.

**SECONDAIRE A — l'élimination.** Un camp a détruit l'autre. Analysée **séparément**.

**SECONDAIRE B — le chronomètre.** Victoire du défenseur par épuisement du temps. Analysée
**séparément**.

> **Les trois ne sont jamais agrégées après coup.** Le « taux de prise » global — qui
> mélangeait tenue et élimination — n'est plus une métrique de ce banc.

## L'hypothèse, déposée comme telle et non comme sauvetage futur

> **Si l'avantage du deux-axes apparaît sur la TENUE mais pas sur l'ÉLIMINATION, alors la
> lecture « le flanc ne protège pas, il fait ARRIVER » devient directement testée.**

C'est le résultat le plus intéressant que ce run puisse rendre — et il est écrit avant de
l'avoir vu. Le journal `ARR` (premier franchissement du rayon de tenue, par axe) le mesure
en propre.

## Condition d'échec du run, déposée

Si à l'aube le nombre d'événements de **tenue** est inférieur à **~30 au total**, la
primaire est illisible. Alors :

- **la nuit ne juge que les secondaires**, et je le dis tel quel ;
- aucun verdict sur le +12,3 n'est prononcé ;
- et il faudra un monde où la tenue se produit plus souvent — ce qui est un autre chantier.

## Portée du réglage, à recopier dans le verdict final

Le calibrage a été fait **à charge constante de six accrochages simultanés**, et je n'ai pas
pu séparer l'effet du rapport de force de celui de la charge — la charge faible n'a qu'un
seul accrochage dans les données.

> **Le réglage retenu vaut pour : charge 6, ratio 1,5-3,0.** Rien au-delà.
