# De nuit, une menace regardée est connue en 6 secondes jusqu'à 150 m, et jamais au-delà de 300 m

*18/09/2026 — statut ETABLI — domaine : banc CHACAL (instrument de perception)*
*Banc dédié demandé par Younes. Mission b2084ae, campagne BANC-PERCEPTION-18-09, 10 épisodes, 0 refus.
Sortie : `menace/lecture_banc_perception.txt`. Plan : `plans/plan-menace-visible.md`.*

## Énoncé

De nuit (1 h 30, lune 0,79), avec **jumelles de nuit portées par les 10 hommes** (vérifié dans la ligne
`banc_perception`), une cible **debout, immobile, regardée par tout le détachement**, avec ligne de vue vérifiée :

| distance | vue (canal géométrique) | connue du groupe (`targetKnowledge`) | première connaissance |
|---|---|---|---|
| 50 m | 100 % du temps | oui | **6 s** |
| 100 m | 100 % (1 épisode ; l'autre sans ligne de vue) | oui | **6 s** |
| 150 m | 100 % | oui | **6 s** |
| 300 m | 100 % | **jamais en 300 s** | — |
| 600 m | 100 % (1 épisode sur 2) | **jamais** | — |

La connaissance de l'IA **arrive vite ou jamais** : il n'y a pas de montée lente. Sa portée de nuit est entre 150 et
300 m. Les trois canaux (groupe, camp, homme) montent ensemble, à la même mesure.

## Ce que cela corrige

La veille, les contrôles concluaient « de nuit la connaissance est morte » (2 épisodes sur 8 à 150 m). **C'était un
artefact** : la cible de contrôle était posée dans l'axe du chef, pendant que la fenêtre d'observation faisait regarder
les hommes vers le secteur de la phase. Ils observaient ailleurs. Younes a posé la question qui a fait tomber la
conclusion : « tu es sûr que les jumelles sont pointées juste en face des ennemis ? »

## Conséquences mesurées le même jour

- **La fenêtre d'observation balaie désormais trois azimuts** autour de l'axe de la phase, au lieu de fixer un point.
  Le contrôle positif passe alors à **8 sur 8** (contre 2 sur 8 la veille).
- **Les menaces d'un seul type étaient posées trop loin** : 400 à 800 m en P1, 300 à 700 m en P2, contre 150 à 350 m
  au niveau 3. Hors de portée de perception, donc la variance mesurée tombait à 0-2 épisodes sur 8. D'où les niveaux
  4 et 5, un seul type mais posé près.

## Fautes consignées

1. **La fenêtre figeait le détachement** (corrigée, mission b862eca) : `doStop` sans `doFollow` à la fin. En phase 4,
   les trois éléments ne repartaient jamais : 8 épisodes sur 8 finissaient au plafond, 55 min au lieu de 5.
2. **`BIS_fnc_lowest` n'existe pas** en SQF (corrigée, b862eca) : 114 erreurs par épisode, colonne d'angle à « any ».
   C'est `selectMin`.
3. **Contrôle positif mal visé** (corrigée, b862eca) : cible posée dans l'axe du chef, hommes regardant ailleurs. Un
   contrôle positif doit viser là où l'instrument regarde, sinon il mesure l'orientation, pas la perception.
4. **Types séparés posés plus loin que le niveau 3** (corrigée, niveaux 4 et 5) : séparer les types éloignait la
   menace, ce qui confondait « type » et « distance ».

## Règles

- Un contrôle positif d'instrument doit **placer sa cible là où l'instrument regarde**, et journaliser l'angle.
- **Observer, c'est balayer** : un détachement qui fixe un point ne perçoit pas ce qui est à 45°.
- Avant de séparer un facteur (ici le type de menace), **vérifier qu'on ne change pas en même temps un autre facteur**
  (ici la distance).

## Falsificateur

« Si une cible debout, regardée, à ligne de vue libre et à 150 m n'est pas connue du groupe en moins de 300 s, alors la
connaissance de l'IA est inutilisable de nuit comme perception. » — **non franchi** : elle est connue en 6 s.
