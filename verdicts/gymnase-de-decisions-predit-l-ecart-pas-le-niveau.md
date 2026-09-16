# Le gymnase de décisions prédit l'écart, pas le niveau

*16/09/2026 — statut ETABLI — domaine : gymnase et fidélité*
*Critères pré-enregistrés : `gymnase_decisions/CRITERES_GYMNASE_DECISIONS_V0.md`, commit 0fe722e, écrit avant le calcul.*

## Énoncé

Un gymnase qui **rejoue les transitions de phase mesurées dans Arma**, au lieu de simuler le combat, prédit
96 épisodes Arma qu'il n'a jamais vus : les deux bras tombent dans l'intervalle d'Arma, l'enchaînement assaut →
exfiltration tient (z = −0,83), et l'écart entre les deux choix est reproduit (+10,8 points contre +10,4).
Mais il est **optimiste d'environ 10 points sur les deux bras**, et un taux constant de 52,8 % se trompe deux fois
moins que lui sur le niveau. Il transfère l'écart entre les options, pas le niveau absolu.

## Ce qui a été construit

- **Phase 5 (assaut)** : 467 épisodes Arma, rangés par (monde, porte, délai du porteur). Le gymnase en tire un et lit
  l'état en fin d'assaut : charges posées et hommes vivants.
- **Phase 6 (exfiltration)** : 97 épisodes entrés en exfiltration avec 3 charges, rangés par (monde, classe de vivants).
- Choix permis : 45 s porte A, 45 s porte B, 180 s porte A. **180 s porte B n'a jamais été joué : il est interdit.**
- Mondes 7, 8, 11, 12, `depart=5`, palier 4, sans réserve ni menace.

## Les portes

| porte | résultat | chiffres |
|---|---|---|
| G1 bras 45 s | **passe** | gymnase 0,544 contre Arma 21/48 = 0,438, IC Wilson [0,307 ; 0,577] |
| G2 bras 180 s | **passe** | gymnase 0,652 contre Arma 26/48 = 0,542, IC [0,403 ; 0,674] |
| G3 enchaînement | **passe** | 56 épisodes test entrés en exfiltration avec 3 charges : 47 succès observés, 48,9 attendus, z = −0,83 |
| G4 assaut seul, 45 s | échoue (diagnostic) | 3 charges : gymnase 0,638 contre Arma 0,500, IC [0,364 ; 0,636] |
| G4 assaut seul, 180 s | passe | gymnase 0,749 contre Arma 0,667, IC [0,525 ; 0,783] |
| G5 signe de l'écart | passe | gymnase +0,108, IC [+0,014 ; +0,194], contre Arma +0,104 |
| G6 porte témoin | passe | B − A = −0,003, IC [−0,128 ; +0,120] |
| N contre le naïf | **échoue** (informative) | erreur cumulée : gymnase 0,217, taux constant 52,8 % : 0,104 |

**Le v0 est validé au sens des critères** (G1, G2, G3). G1 et G2 passent près du bord de l'intervalle.

## Où est l'erreur

L'exfiltration est juste (G3). L'erreur vient de **l'assaut** : sur les mêmes quatre mondes, la campagne test pose
ses trois charges moins souvent que les campagnes de construction (0,500 contre 0,638 à 45 s). C'est la dérive
déjà mesurée d'une campagne Arma à l'autre (verdict `un-taux-porte-sa-charge-machine` : 52,8 % contre 43,8 %,
mêmes mondes). Le gymnase hérite du niveau des campagnes anciennes. La dérive touche les deux bras : **l'écart
survit, le niveau non.**

## L'apprentissage

Q tabulaire, 1 000 000 d'épisodes par graine, 5 graines, 8 s de calcul pour l'ensemble.

- **L1 passe** : les 5 graines choisissent 180 s porte A, le choix du calcul exact ; écart maximal Q − exact 0,0043.
  La recette n'est pas une loterie ici (elle l'était sur l'ancien gymnase : 49,6 % ou 3,3 % selon la graine).
- **L2 passe** : 180 s devance 45 s de +0,108, IC [+0,014 ; +0,194].
- **L3 passe** : aucune préférence entre les portes.
- **Par monde**, la supériorité de 180 s n'est établie que sur le monde 8 (IC [+0,07 ; +0,36]). Aucune inversion
  établie : rien ne montre qu'un monde demande l'autre option.

## Ce que ce n'est pas

- **Pas une connaissance nouvelle.** « 180 s vaut mieux » est le résultat de la vignette du délai du porteur (+11,1
  points de charges, IC [+0,7 ; +21,6]) propagé jusqu'à la mission par un modèle d'exfiltration validé. Dans Arma,
  de bout en bout, l'écart n'est **pas établi** (+10,4, IC [−8,3 ; +29,2]). Le gymnase le rend significatif parce
  qu'il combine plus d'épisodes, sous deux hypothèses : l'enchaînement (testée, G3) et l'absence de dérive (réfutée
  pour le niveau, G4).
- **Pas un examen sur mondes jamais vus** : le test tient des épisodes à l'écart, pas des mondes.
- **Pas « des millions de choix »** : il y a 3 options. Un million d'épisodes suffit ici à montrer que la recette
  converge ; ce qui manque, ce sont des choix mesurés dans des situations variées.

## Conséquences

1. **Lire les écarts entre options, jamais les niveaux absolus** du gymnase.
2. Pour recaler le niveau, chaque nouvelle campagne Arma garde un bras témoin entrelacé (règle déjà écrite).
3. Le gymnase s'agrandit à mesure qu'Arma mesure de nouveaux choix : le partage au bouchon avec réserve (phase 4 → 6)
   et les menaces des six phases (couche de situation, 16/09) sont les prochains.

## Falsificateur pré-enregistré

« Si G1 ou G2 échoue, le gymnase ne reproduit pas Arma sur des épisodes qu'il n'a pas vus, et il ne sert pas à
entraîner. » — **non franchi.**

## Reproduire

```bash
/mnt/data/hmt/socle/.venv/bin/python gymnase_decisions/extraire_phases.py
/mnt/data/hmt/socle/.venv/bin/python gymnase_decisions/gymnase_v0.py
```

Sortie : `/mnt/data/hmt/gymnase_decisions/resultats_v0.json`, copiée dans `gymnase_decisions/resultats_v0.json`.
