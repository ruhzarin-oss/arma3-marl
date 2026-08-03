# CRITÈRES — LE CHAMP REJUGÉ, EXPOSITION CORRIGÉE (figés avant le run)

Écrit le 27/07/2026, après la découverte du 10e défaut silencieux et **avant** le run.

## Pourquoi on rejuge
Le premier verdict du champ — « exposition −22 % » — était un **artefact d'instrument**.
`exposed` utilisait encore `inr = (dist < fire_range)`, la falaise à 110 m retirée des
**dégâts** le 26/07 mais jamais de l'**exposition**. La métrique comptait donc zéro
au-delà de 110 m, précisément là où le crochet fait 74 % de son détour.

Après correction (l'exposition suit la courbe mesurée, comme les dégâts) :

| | prise | expo AVANT | expo CORRIGÉE |
|---|---|---|---|
| crochet scripté | 86,8 % | 0,0136 | 0,0148 |
| appris (arc seul) | 87,3 % | 0,0229 | 0,0209 |
| **appris (champ)** | **94,7 %** | 0,0178 | **0,0337** |

**Le champ ne rend pas l'agent plus habile : il le rend plus payeur.** Il prend 95 % contre
88 %, en s'exposant deux fois plus. C'est-à-dire qu'il CHARGE — ce que la section 0 de
SIROCCO refuse et ce que le banc FIBUA a déjà tranché.

## Le juge change, et il ne changera plus
**PRISE-À-PERTES = prise ÷ pertes par prise.** La métrique du banc certifié.
Elle est immunisée contre le défaut qu'on vient de trouver : elle ne dépend d'aucun seuil
de portée. Les pertes sont des faits, pas une reconstruction.

L'exposition corrigée passe en **SENTINELLE**, pas en critère (recommandation de Fable :
les pertes sont bruyantes, l'exposition est le risque couru — l'une juge, l'autre alerte).

## Le protocole
Deux bras, mêmes graines, tout identique sauf le champ.
- **TÉMOIN** : arc seul
- **CHAMP** : arc + le prix du terrain dans les 8 directions à 35 m
3 graines, 150 rondes, évaluation 300 épisodes, graine différente de l'entraînement.

## Seuils, figés
- **SUCCÈS** : prise-à-pertes **≥ +15 %** contre le témoin, mesuré dans le même run.
- **SUCCÈS PARTIEL** : prise **+2 points au moins** sans que les pertes par prise montent
  de plus de 5 %.
- **ÉCHEC — « il charge »** : la prise monte, payée par plus de pertes. C'est le cas qu'on
  soupçonne maintenant, et il est écrit AVANT de le voir.
- **CONTRE-ÉPREUVE** : le témoin doit rendre ≈87 % de prise et ≈0,021 d'exposition corrigée.

## Sentinelles, logguées sans seuil
- exposition par mètre **corrigée** : si elle se dégrade nettement pendant que la
  prise-à-pertes monte, on gagne aux dés, pas en tactique.
- distance du détour : on sait maintenant qu'elle **descend** avec le champ (126 m contre
  136 m). On le note, on n'en fait plus une théorie.

## Interdits
1. Retoucher `champ_R` (35 m) ou quoi que ce soit après avoir vu les chiffres.
2. Réhabiliter l'exposition comme critère si la prise-à-pertes déplaît.
3. Reproposer une explication de mécanisme avant qu'un instrument ne soit vérifié.
   **Trois théories sont mortes aujourd'hui parce que je les ai posées à un capteur cassé.**
