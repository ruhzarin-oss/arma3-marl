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
