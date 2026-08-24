# L'ARGMAX DE LA GRAINE 1 MARCHE EN LIGNE DROITE ET MANQUE L'OBJECTIF

**24/08/2026.** Autopsies prescrites par Fable, faites sur les artefacts conservés, **sans
entraîner**. Deux hypothèses meurent, la troisième explique tout.

## ⛔ Le « continuum de netteté » ne suffit pas

| artefact | prise (argmax) | entropie | écart top1−top2 |
|---|---|---|---|
| graine 1 (TOMBE) | **3,3 %** | 1,654 | 0,152 |
| graine 0 (PASSE) | 49,6 % | **1,219** | **0,332** |
| **artefact 13/08** | **50,7 %** | **1,525** | **0,176** |

L'artefact du 13/08 est **presque aussi plat** que la graine 1 (1,525 contre 1,654 ;
0,176 contre 0,152) — **et son argmax rend 50,7 %.** La platitude ne décide pas.

## ⛔ Le « portefeuille » ne discrimine pas non plus

| artefact | dispersion argmax | dispersion τ=1 |
|---|---|---|
| graine 1 | 23,0 m | 36,7 m |
| graine 0 | 25,9 m | 35,9 m |
| **13/08** | **22,3 m** | 37,5 m |

**Les trois groupent sous argmax et se dispersent en échantillonnant, presque à l'identique.**
L'effet est réel — et le 13/08, qui groupe **le plus**, réussit. **L'hypothèse de Fable est
mesurée et écartée.**

## ⭐⭐⭐ Ce qui explique tout : un champ d'action SPATIALEMENT CONSTANT

| graine 1, argmax | actions | profil de distance |
|---|---|---|
| | **NO 44 % · APPUYER 43 %** (87 % à deux actions) | 170 m → **103 m** au pas 15 → **150 m** au pas 30 → **168 m** au pas 59 |

> ## Elle approche jusqu'à 103 m, puis **repart**, et finit **plus loin qu'au départ**.

**Elle marche en ligne droite sur un cap fixe qui manque l'objectif de 103 mètres**, le
dépasse, et continue. Ce n'est pas une politique qui hésite : c'est une politique dont
**l'argmax ne dépend presque plus de la position**.

En échantillonnant (τ=1) le verrou saute — NO 21 %, SE 15 %, APPUYER 13 %, S 12 % — et le
profil devient 170 → 83 → 80 → **89 m** : elle approche et tient.

**La graine 0, elle, a un vrai champ** : E 27 %, N 22 %, SO 21 %, O 16 %, et le profil
descend sans revenir — 170 → 107 → 76 → **53 m**, l'escouade se consumant à 0,1 vivant.

## Le mécanisme, bout à bout

L'écart top1−top2 de la graine 1 vaut **0,152** : l'argmax se joue sur un **quasi ex-æquo**.
La position module bien les logits, mais **pas assez pour faire basculer le premier rang**.
Le vainqueur est alors décidé par un biais quasi constant — d'où un **champ spatialement
constant**, d'où la ligne droite.

**Et ça se raccorde exactement au défaut n°5 déposé le 23/08** (`97b996e`) :
l'avantage est **normalisé pas par pas**, donc il n'encode que le **rang**, jamais la
grandeur. Le gradient garde une amplitude constante pour toujours, les logits ne s'affûtent
jamais, et la dépendance à la position reste **sous le seuil qui départage le premier rang**.

> **Chaîne complète, chaque maillon mesuré ou lu dans le code :**
> normalisation pas par pas → les logits ne s'affûtent pas → l'argmax se joue à 0,15 →
> le champ devient spatialement constant → l'escouade marche droit et manque l'objectif.

⭐ **Cliquet : une politique peut être bonne en moyenne et dégénérée en son mode.** Ce n'est
pas une question de netteté, c'est une question de **dépendance à l'état**.

## ⚠️ Ce que ça ne dit pas

- **La chaîne n'est pas établie**, seulement cohérente : le dernier maillon (la normalisation
  cause le non-affûtage) demande le **rejeu instrumenté** prescrit par Fable — journaliser
  l'avantage brut et normalisé sur les mêmes trajectoires, et mesurer la part de la norme du
  gradient qui revient aux pas de prise. **1 h 40, aucun entraînement neuf.**
- **n = 2** pour la loterie (le 13/08 vient d'une autre recette et ne va pas dans l'urne).
- **L'entropie annelée est disqualifiée** comme geste : elle règle la pression à rester
  étalé, elle ne crée pas une dépendance à la position. Ma recommandation d'hier soir tombe.
