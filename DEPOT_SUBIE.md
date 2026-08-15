# Dépôt — l'exposition est-elle SUBIE ou CHOISIE ? Critères AVANT mesure

Déposé le 15/08/2026. Question posée par Fable à partir d'un paradoxe : **le gymnase
surfacture l'exposition ×2** (tarif 5,77 contre 2,87), donc une politique transférée devrait
être **trop prudente** sur Arma. Elle s'y expose **55 % du temps contre 21,6 %**.

Une exposition qui augmente là où elle coûte moins cher n'est pas un choix rationnel de la
politique. **L'hypothèse est qu'elle est subie** — du transit entre des couverts rares.

C'est la même distinction qui a déjà valu ×10 sur la suppression subie.

## Les grandeurs, définies une seule fois pour les deux mondes

- **« exposé »** = `los > 0,5` (colonne 7) ;
- **« couvert à portée »** = `dcover ≤ 0,033`, soit une cellule de 6,25 m — atteignable en
  un pas dans les deux mondes ;
- **P(exposé | couvert à portée)** = *quand il a le choix, s'expose-t-il quand même ?* ;
- **part forcée** = P(pas de couvert à portée | exposé) = *quelle part de son exposition
  n'avait aucune alternative*.

## Les lectures, déposées

| condition | lecture |
|---|---|
| P(exposé \| couvert à portée) **semblable** entre mondes (rapport 0,7-1,4) **ET** part forcée d'Arma supérieure de **> 20 points** | **SUBIE** — même comportement quand le choix existe ; l'écart vient de l'absence d'alternative |
| P(exposé \| couvert à portée) **> 1,4×** plus haut sur Arma | **CHOISIE** — la politique se conduit autrement là-bas quand elle a le choix |
| tout le reste | **INDÉCIS**, on ne conclut pas |

## CONTRÔLES POSITIFS ⟨règle 16⟩

1. **Les deux situations doivent exister dans les deux mondes** : au moins 100 pas avec
   couvert à portée et 100 sans, de chaque côté. Sinon la conditionnelle est vide.
2. **`los` et `dcover` doivent séparer** : ni l'un ni l'autre constant dans un monde.

## LES PORTES SONT EXÉCUTÉES AVANT DE JUGER ⟨règle 18⟩

Chaque bande est passée sur **deux cas fabriqués** — un qui doit la franchir, un qui doit
la faire tomber. Exécuté, pas argumenté. Le script les imprime **avant** de toucher aux
données réelles. Une porte qu'aucun cas ne satisfait, ou qu'aucun cas ne fait échouer, est
fausse par construction et le run s'arrête.

## Rapporté, NON jugé

L'exposition en mouvement contre l'exposition à l'arrêt. C'est un indice de transit, pas une
preuve : un agent immobile derrière un muret et un agent immobile à découvert sont tous deux
« à l'arrêt ».

## Ce qui n'est PAS promis

Si l'exposition est subie, ça ne dit pas comment y remédier — le levier serait la densité de
couvert et le pas de déplacement, pas le tarif ni la politique, et **ça resterait à mesurer**.
