# L'azimut d'assaut ne porte pas, et le bruit dicte ce qu'on peut encore demander à cette machine

*Verdict du 13/09/2026. Campagne AZIMUT-VIGNETTE-13-09, 72 épisodes, vignette assumée.*

## La couture, d'abord

C'est le premier endroit de CHACAL où une décision est ouverte à autre chose que le script. Douze
azimuts candidats, trois décideurs : le script (score sur les deux ouvertures), le hasard (tirage
uniforme semé par la graine), et un azimut imposé par le job. Elle fonctionne : l'épisode de contrôle
a joué 270° alors que les deux ouvertures du site étaient à 81° et 256° — une direction que la mission
**ne pouvait pas choisir seule**.

## Ce qui est mesuré

| Bras | 3 charges sur 3 | Taux | Intervalle 95 % | Azimuts joués |
|---|---|---|---|---|
| A script | 17/24 | 70,8 % | 50,8 – 85,1 | 81°, 273° |
| B hasard | 15/24 | 62,5 % | 42,7 – 78,8 | 180°, 300° |
| C imposé 0° | 12/24 | 50,0 % | 31,4 – 68,6 | 0° |

| Comparaison | Écart | Fisher bilatéral |
|---|---|---|
| script contre hasard | +8,3 pts | **p = 0,76** |
| script contre imposé 0° | +20,8 pts | p = 0,24 |
| hasard contre imposé 0° | +12,5 pts | p = 0,56 |

## Le verdict

**Aucune comparaison ne tranche.** La prédiction écrite avant le lancement — « le script bat le hasard
d'au moins 15 points » — est fausse : l'écart est de 8 points et il est indistinguable du bruit.

Le falsificateur inscrit dans le job se déclenche : *si le hasard fait aussi bien que le script, alors
le score qui choisit l'ouverture ne sert à rien.* C'est le cas, à cette échelle.

Et la seconde prédiction est fausse aussi : l'azimut 0°, que l'atelier donnait comme le meilleur, est
le **pire** des trois.

## L'atelier ne s'est pas transposé, et il faut le dire

L'atelier MCP avait mesuré, sur cinq essais par bras, azimut 45 à zéro entrée, azimut 0 à 3,8 entrées,
azimut 126 à 2,6. Cette hiérarchie **ne se retrouve pas** dans la mission.

Le labo mesurait cinq hommes en garnison sur un site reconstruit. La mission joue un palier complet,
avec ses rondes et sa réserve. Un banc de labo propose une piste ; il ne la transporte pas.

## Ce que ce verdict apporte de plus utile : la limite de la machine

Puissance statistique, 80 %, deux bras :

| Écart à démontrer | Épisodes **par bras** |
|---|---|
| 8 points | **541** |
| 15 points | 144 |
| 20 points | 77 |

À une heure par épisode en mission complète, un écart de 8 points est **hors de portée** de cette
ferme. Un écart de 20 points coûte une nuit.

**Conséquence de méthode.** Il faut soit ne viser que des leviers à gros effet, soit réduire le bruit
lui-même — par appariement sur la graine, ou par un critère plus fin que le tout-ou-rien des trois
charges. Une campagne qui vise un petit écart sans l'un des deux est une dépense perdue d'avance,
et c'est mesurable avant de la lancer.

## Ce que ce verdict ne dit pas

- La vignette ne joue ni l'approche ni l'exfiltration. L'azimut pourrait porter sur la mission entière
  sans porter sur l'assaut seul.
- Deux graines seulement.
- Le bras hasard n'a tiré que deux azimuts distincts (180° et 300°) sur douze possibles, parce que le
  tirage est semé par la graine et qu'il n'y a que deux graines. **C'est un défaut du témoin** : il
  échantillonne mal l'espace qu'il est censé représenter.

---

# AMENDEMENT DU 14/09/2026 : LE TITRE EST FAUX. L'AZIMUT PORTE, MAIS PAR SITE

**Ce verdict a mesuré la moyenne de deux vérités opposées.** Signalé par Fable, vérifié sur les mêmes
données, sans une seconde d'Arma en plus.

## Les mêmes 72 épisodes, stratifiés par graine

| Graine 7 | | Graine 8 | |
|---|---|---|---|
| azimut 180° | **83,3 %** (10/12) | azimut 273° | 66,7 % (8/12) |
| azimut 81° | 75,0 % (9/12) | azimut 0° | 66,7 % (8/12) |
| azimut 0° | **33,3 %** (4/12) | azimut 300° | 41,7 % (5/12) |
| **étendue 50,0 points**, Fisher **p = 0,036** | | étendue 25,0 points, p = 0,414 | |

## Ce qui s'était passé

**L'azimut 0° donne 33 % sur la graine 7 et 67 % sur la graine 8.** Regroupés, ils se lisent 50 % —
la moyenne exacte de deux comportements opposés. Le bras « hasard » tirait 180° sur la graine 7 et
300° sur la graine 8, soit le meilleur azimut d'un site et le pire de l'autre : son taux global
moyennait les deux et ressemblait à celui du script.

Le p de 0,76 qui a produit le titre de ce verdict ne mesurait pas l'absence d'effet. Il mesurait le
mélange de deux mondes.

## Ce qui est donc établi

1. **L'azimut d'assaut porte**, avec une étendue de 50 points sur la graine 7 et un Fisher à 0,036.
2. **Le meilleur azimut dépend du site.** Il n'existe pas de bonne direction en général.
3. **Le script ne le trouve pas.** Sur la graine 7, le hasard fait mieux que lui — 10/12 contre 9/12 —
   parce qu'il a tiré 180° par chance. Le score qui choisit l'ouverture n'est pas un prédicteur.

## Pourquoi cela change la suite

C'est le premier signal du projet qui réunit les trois conditions d'un apprentissage utile : l'effet
est **grand** (50 points, donc mesurable par cette ferme, qui demande 77 épisodes par bras pour
20 points), il est **dépendant du site** (donc il y a quelque chose à apprendre, et non une constante
à écrire en dur), et le **script actuel échoue** (donc il y a une marge à prendre).

La couture de l'azimut, posée le 13/09, est donc au bon endroit. C'est la mesure qui était mal conçue.

## La leçon de méthode

**Ne jamais regrouper deux graines avant d'avoir regardé chacune.** Une graine est un monde, pas une
répétition. Cette règle rejoint celle du 13/09 sur la puissance : à cette échelle de bruit, il faut
soit de gros effets, soit de la stratification — et ici la stratification a révélé l'effet que le
regroupement avait détruit.

Corollaire pour le bras témoin : un tirage semé par la graine ne tire qu'un azimut par graine. Ce
n'est pas un plancher uniforme, c'est un azimut fixe déguisé en hasard. Un vrai témoin doit tirer
indépendamment des répétitions.

## Ce qui reste à établir

L'étendue n'est significative que sur une graine. Huit jobs sont en file au 14/09 pour compléter la
courbe — quatre azimuts de plus par graine, 48 épisodes — avec pour prédiction une étendue supérieure
à 30 points sur chaque graine, et pour falsificateur une étendue sous 15 points sur les deux.
