# Le GYMNASE passe enfin son examen — et il échoue sur son couvert

Mesuré le 16/08/2026, geste 4 du plan de Fable, pendant que les 67 tournent sur Arma.

> ⟨Fable⟩ *« Arma subit six tests avant chaque épisode ; le gymnase, zéro — et c'est
> pourtant lui qui fournit le 59,4 %, la référence de tout ton calibrage. Le côté le moins
> audité de ta comparaison, c'est le gymnase. »*

Les six portes ont d'abord passé **leur propre banc** ⟨règle 18⟩ : chacune franchissable
et rejetable sur des cas fabriqués.

## Le résultat

| test | mesure | verdict |
|---|---|---|
| **G1** létalité non nulle | 0,0402 mort par homme-pas (bande 0,01-0,30) | **✓** |
| **G2** le couvert atténue | **×1,21** — sa formule promet ×3,3 | **⛔** |
| **G3** exposition seulement si vu | non mesurable — voir plus bas | **—** |
| **G4** les 8 caps déplacent | **8/8** dans la bonne direction | **✓** |
| **G5** graine = trajectoire | écart max **0,00** | **✓** |
| **G6** prise dans la bande 20-80 | **51,1 %** | **✓** |

## G2 — LE COUVERT DU GYMNASE VAUT UN CINQUIÈME DE CE QU'IL ANNONCE

La formule de dégâts dit `dmg × (1 − 0,7·incover)`, soit une atténuation de **×3,3** sur le
couvert. Mesurée chez les exposés vivants : **×1,21**.

La raison est mécanique : **`incover` est un échantillonnage bilinéaire qui n'atteint
presque jamais 1.** À 0,3 de moyenne, l'atténuation tombe à `1/(1−0,21) = ×1,27` — ce qu'on
observe.

**Le couvert du gymnase ne protège donc ni comme il le prétend, ni en cachant** (masquage
mesuré 1,08 hier). Il est **faible ET scalaire**. Ça renforce la chirurgie que Fable a
tranchée : *« un couvert scalaire ne peut pas enseigner le flanc — et le flanc est ta thèse
produit. »*

## G3 — NON MESURABLE EN L'ÉTAT, et c'est mon test qui est en cause

Deux tentatives, deux fois rouge, deux fois ma faute :

1. la première comparait le **maximum courant** (`exposed = maximum(exposed, …)`, le cliquet)
   à l'instant présent : elle mesurait une **persistance voulue** ;
2. la seconde mesurait les **hausses** — 158 sur 513 sans que personne soit vu. Mais mon
   « vu » lit la colonne `los` de l'observation, qui vise **le plus proche ennemi**, quand
   le calcul d'exposition consulte **tous les défenseurs**. Un homme invisible du plus
   proche peut être vu d'un autre.

**Troisième fois aujourd'hui que j'emploie l'abstraction commode au lieu de la propriété que
le mécanisme utilise** ⟨règle 16 clause 2⟩. Je ne patche pas une troisième fois : mesurer
ceci demande d'instrumenter l'environnement, ce qui est une modification et non une sonde.
**G3 est retiré du prévol jusque-là — un test qu'on ne sait pas poser ne juge rien.**

## Ce que l'examen établit

**Le gymnase n'est pas cassé** : il tue, il déplace, il est déterministe, et sa prise tombe
dans la bande où un banc peut juger. Ses quatre tests valides passent.

**Mais son couvert ne tient aucune de ses deux promesses** : il n'atténue qu'à ×1,21 au lieu
de ×3,3, et il ne cache pas. C'est le seul défaut trouvé, et c'est exactement celui que la
chirurgie doit corriger.

## Ce que ça ne dit pas

Que corriger le couvert fermerait les 15 points d'écart avec Arma. Fable l'a tranché
autrement : la question est désormais **l'ORDRE** — si la nuit armée reproduit sur Arma le
classement du gymnase (FRONTAL 12,8 / FLANC 34,3 / SCRIPT 46,1 / POLITIQUE 51,1), le tarif
absolu est un détail.
