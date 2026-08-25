# AMENDEMENT À LA PRÉ-INSCRIPTION DES POSTURES — écrit avant le premier entraînement

**25/08/2026, 15 h.** Amende `PREINSCRIPTION_POSTURES.md` (`b3626e1`). Règle 13 : un
amendement s'énonce **sans référence à un résultat** et ne peut que **RESSERRER**.

## Pourquoi l'expérience n'a jamais eu lieu

Elle a tourné le 23/08 à **140 itérations** et rendu **0 %**. On sait depuis que **140
itérations est trop court pour N'IMPORTE QUELLE configuration** — le bras à 10 actions y
rendait 5,7 %, contre 49,6 % à 1 200. **Ce « 0 % » mesurait le budget, pas les postures.**

## Ce que l'amendement change — trois resserrements

| | avant | **maintenant** |
|---|---|---|
| budget | 140 itérations | **1 200** |
| graines | 1 | **k = 4, identique dans les deux bras** |
| décodeur | argmax | **échantillonnage**, τ = 1 (décision du 24/08) |
| témoin | l'artefact du 13/08, 50,7 % | **un bras à 10 actions rejoué dans les mêmes conditions** |
| lecture | GRAINES_TEST | **GRAINES_SELECT** — on ne brûle pas TEST pour de l'exploratoire |

**Le témoin change et c'est le resserrement principal** : comparer les postures à un artefact
d'une autre époque, d'un autre budget et d'un autre décodeur aurait mesuré trois choses à la
fois. **Les deux bras sont désormais rejoués côte à côte**, mêmes graines, même tout.

## Les prédictions, réécrites pour ce dispositif

| n° | prédiction |
|---|---|
| **P1** | le bras **13 actions** bat le bras **10 actions** d'au moins **5 points** (moyenne sur 4 graines, lecture échantillonnée, sur SELECT) |
| **P2** | les **trois colonnes de posture cessent d'être constantes** — dispersion > 0,05 |
| **P3** | **`los` devient LU** : le brouiller coûte **plus de 5 points** (aujourd'hui **−3,0**, c'est-à-dire rien) |

⚠️ **Règle de résolution, déclarée d'avance** ⟨Fable⟩ : à **k = 4**, un effet **sous 5-6
points est NON RÉSOLU à ce budget**. Si P1 sort à 3 points, **ce n'est pas un petit succès,
c'est un résultat illisible**, et on l'écrit ainsi.

## Les falsificateurs

> **P1 sans P3** : l'agent a gagné en survivant mieux **sans regarder personne**. Ce n'est
> pas de la tactique, c'est un réglage — et le gain **ne se présente pas** comme une lecture
> du monde.

> **P2 échoue** — les postures restent constantes alors que l'action existe : **rien ne paie
> de se coucher**. Le levier n'est alors pas le vocabulaire mais **la récompense**, et c'est
> le geste suivant.

> **P1 échoue** : donner des actions ne suffit pas. Reste à savoir si c'est parce que rien ne
> les paie (→ récompense) ou parce que le monde ne montre rien à lire (→ `dcover` a une
> dispersion de **0,029**, le gymnase ne montre presque pas de couvert — et ça, c'est un
> problème de MONDE).

## Interdits

- **Ne pas changer la récompense dans le même geste.** Un bras, un levier.
- **Ne pas lire TEST.** Toute cette expérience vit sur SELECT ; TEST attend un artefact livré.
- **k ne devient jamais « autant qu'il faut »** : un 0/4 est un résultat.
- **Ne pas choisir les seuils après.** 5 points, 0,05 et 5 points sont posés ici.
