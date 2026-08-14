# Dépôt — étalonnage de `dcover`, critères écrits AVANT

Déposé le 14/08/2026. **Quatrième fois que cette colonne est fausse.** Cette fois le
mécanisme du gymnase a été LU, pas supposé.

## Ce que le gymnase calcule (terrain_gpu.py:46-47, 57-64)

```python
gy, gx = torch.gradient(hm, dim=(1,2)); slope = (gx*gx + gy*gy).sqrt()   # difference centrale, m/cellule
cover  = (slope > 1.4 * slope.mean((1,2), keepdim=True))                  # moyenne PAR ENVIRONNEMENT
dcover = _dist_field(cover, G, iters=16)                                  # max-pool 3x3 itere = TCHEBYCHEV, sentinelle 16
dc     = (dcover / 30).clamp(max=1)                                       # dans l obs
```

## Les deux fautes du côté Arma

1. **Le seuil est une CONSTANTE GLOBALE.** `_SEUIL = 1.4 * 2.315`, où 2,315 est « la pente
   moyenne de Stratis × 5 ». Deux erreurs empilées : le ×5 vient de la normalisation de la
   colonne `slope` et n'a rien à faire dans une comparaison de gradients bruts ; et surtout
   **le gymnase normalise par la moyenne de SON PROPRE terrain, pas par une constante de
   carte.** Un site à relief doux a une moyenne basse, donc un seuil bas, donc il trouve du
   couvert. Le seuil global, lui, n'y trouve rien et rend le garde-fou.
2. **Le rayon de recherche s'arrête à 8 cellules** quand la sentinelle vaut 16. Le gymnase
   cherche jusqu'à 15 avant de rendre 16.

## Ce qu'on fait — on recopie, on ne règle pas

Le seuil devient `1,4 × (gradient moyen local)`, la moyenne étant prise **une fois** sur
une grille de 64×64 cellules de 6,25 m centrée sur l'objectif — soit 400 m de côté, ce qui
correspond au `terr_R = 200` du gymnase. Le rayon de recherche passe à 15, sentinelle 16.

Aucun nombre n'est choisi : 1,4 vient de `cover_thr`, 64 et 16 de `G` et `iters`, 6,25 m de
la maille du terrain d'Arma.

## CONTRÔLES POSITIFS ⟨règle 16 clause 1⟩

1. **La moyenne locale doit être > 0.** Si elle vaut zéro, le seuil vaut zéro, tout devient
   couvert et `dcover` vaut 0 partout — dégénéré. La sonde doit le refuser.
2. **La sonde doit reproduire l'ancien défaut** en repassant l'ancien seuil : sur le site
   plat (1734, 5391), elle doit retrouver ~78 % de garde-fou. Un instrument qui ne
   reproduit pas la panne connue ne prouve pas qu'il l'a réparée.

## La porte

**La médiane de `dcover` sur le site du banc doit tomber dans la plage du gymnase
[0,000 ; 0,131]**, cible 0,035. Mesurée sur les points que les hommes traversent
réellement, pas sur un disque uniforme — l'échantillonnage uniforme est ce qui m'a fait
prédire 0,167 quand l'épisode a rendu 0,033.

## Ce qui ferait échouer

- moyenne locale nulle → dégénéré, on ne déploie pas ;
- l'ancien seuil ne reproduit pas les 78 % de garde-fou → la sonde ne mesure pas ce que
  le banc mesurait, et rien ne se conclut ;
- médiane hors [0,000 ; 0,131] → l'étalonnage rate et on ne le déploie pas.

## Ce qui n'est PAS promis

Réparer `dcover` ne dit rien de la prise. Le 0/20 restera à remesurer **après**, et il
pourra très bien rester 0.
