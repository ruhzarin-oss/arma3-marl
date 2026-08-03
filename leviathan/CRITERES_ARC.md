# CRITÈRES — L'AGENT VOIT-IL L'ARC DE TIR ? (figés avant le premier run)

Écrit le 27/07/2026, **avant** d'avoir touché au code de l'observation et avant d'avoir
vu le moindre résultat. Toute modification ultérieure doit être datée et justifiée, et
invalide les runs qui la précèdent.

## La question
L'agent entraîné dans le monde mesuré gagne **en force** (79 % de prise pour 0,032
d'exposition par mètre) et non **en manœuvre** (le crochet scripté fait 90 % pour 0,014).
Est-ce parce qu'il ne PERÇOIT pas où regarde l'adversaire ?

**Constat de code, établi le 27/07 :** `dface` (la direction que regarde le défenseur) et
`_dfarc` (la largeur de son cône) n'apparaissent QUE dans l'initialisation, la remise à
zéro et le **calcul des dégâts**. **Jamais dans `_obs()`.** L'agent est dans l'angle mort
ou dans la ligne de mire — son observation est rigoureusement identique. Seuls les dégâts
diffèrent. Et la géométrie est randomisée à chaque épisode (`def_rand=True`), donc il ne
peut même pas mémoriser un côté.

Une lecture de code établit que l'information est ABSENTE. Elle ne prouve pas que
l'ajouter suffira. D'où ce test.

## Le protocole
Deux bras, **même monde mesuré, mêmes graines, tout identique sauf l'observation.**
- **AVEUGLE** : l'observation actuelle (témoin)
- **VOYANT** : la même + 2 nombres — sinus et cosinus de l'angle entre la direction que
  regarde le défenseur le plus proche et la direction sous laquelle il me voit

⚠️ **On donne la GÉOMÉTRIE, pas le VERDICT.** Pas de booléen « peut-il me tirer dessus » :
ce serait souffler la réponse. L'agent reçoit *où l'autre regarde*, à lui d'en faire
quelque chose.

## Repères mesurés dans le monde mesuré (nuit du 26 au 27/07)
| | exposition/m | prise |
|---|---|---|
| frontal scripté | 0,035 | 36 % |
| **appris AVEUGLE** | **0,032** | **79 %** (3 graines : 79,3 / 82,7 / 74,3) |
| crochet scripté | 0,014 | 90 % |

## Seuils, figés
- **SUCCÈS** : le bras VOYANT atteint **≤ 0,023** d'exposition par mètre (au moins la
  moitié de l'écart entre l'appris aveugle et le crochet scripté comblée) **ET** ne perd
  pas en prise (≥ le bras aveugle, aux fluctuations près).
- **ÉCHEC** : l'écart entre les deux bras reste dans le bruit. → **ce n'est pas la
  perception**, on passe à l'horizon sans discuter.
- **CONTRE-ÉPREUVE OBLIGATOIRE** : le bras AVEUGLE doit reproduire les chiffres de la
  nuit (≈79 % de prise, ≈0,032 d'exposition). Sinon autre chose a bougé et la comparaison
  ne vaut rien. **On vérifie l'instrument avant de lire sa mesure.**
- **Témoin de mécanisme** : le temps passé dans le SECTEUR AVEUGLE du défenseur. C'est ça,
  contourner. Il doit monter dans le bras voyant.

## Volume et arrêt
3 graines par bras, 150 rondes, évaluation sur 300 épisodes avec une graine **différente**
de l'entraînement. Chevauchement persistant → **un seul doublement** à 6 graines. Toujours
ambigu à 6 → la perception n'est pas la cause.

## Interdits, sans exception
1. Retoucher la récompense ou la largeur de l'arc pour faire passer le résultat.
2. Déplacer un seuil après avoir vu les chiffres.
3. Conclure « il a appris à manœuvrer » sur la seule prise. **Une prise qui monte sans que
   l'exposition descende, c'est encore de la force.**

## Ce test peut échouer et rester utile
Si donner la vue ne change rien, on aura éliminé l'hypothèse la moins chère et gagné le
droit d'aller vers l'horizon. Ce n'est pas un test qu'on cherche à faire réussir.
