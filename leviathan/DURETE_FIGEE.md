# LA DURETÉ DU BANC — FIGÉE

Figée le 27/07/2026, **avant** que le moindre mécanisme ne soit testé dessus.
Calibrée sur les **doctrines scriptées uniquement** — jamais sur les agents appris.

## La configuration

```
A          = 4      attaquants
D          = 8      défenseurs        <-- LE SEUL CHANGEMENT
R_spawn    = 170 m
max_steps  = 60
def_line   = True
def_rand   = True
secure_only = True
courbe     = courbe_toucher_juge.json + les 3 conversions mesurées
```

## Pourquoi celle-là

Le critère n'est pas « plus dur ». C'est **l'écart entre l'assaut frontal et le crochet** —
cet écart EST la place que la manœuvre a pour exister. Un banc où les deux doctrines sont
à 95 % ou à 5 % ne mesure rien, quelle que soit sa difficulté.

| configuration | frontal | crochet | écart |
|---|---|---|---|
| 4 défenseurs (ancien) | 39,1 % | 89,1 % | 50,0 pt |
| 6 défenseurs | 25,5 % | 80,5 % | 55,0 pt |
| **8 défenseurs** | **19,3 %** | **74,7 %** | **55,4 pt** |
| 10 défenseurs | 15,9 % | 70,2 % | 54,3 pt |
| départ 280 m | 34,0 % | 69,8 % | 35,8 pt |

**8 défenseurs** : le crochet à 75 % laisse de la marge des deux côtés, le frontal à 19 %
rend l'échec possible. L'ancien banc plafonnait — le meilleur bras y prenait 96 % des
objectifs, et l'axe du stress y a été testé sans aucune place pour montrer quoi que ce soit.

**Le levier « distance de départ » est écarté** : il referme l'écart (35,8 pt). Il pénalise
le crochet plus que le frontal — il rend le banc plus dur ET moins discriminant.

## ⛔ DEUX LEVIERS SONT INERTES, ET IL FAUT LE SAVOIR

**`def_arc` est IGNORÉ quand `def_rand=True`.** Vérifié dans le code : l'arc est alors tiré
au hasard, `U(40°, 70°)` de demi-angle. Toutes les expériences du 27/07 l'ont utilisé sans
le savoir. **Les comparaisons A/B tiennent** (mêmes graines, même tirage des deux côtés),
mais les fichiers de critères qui annoncent « arc de tir 120° » sont FAUX.

**Le temps ne mord pas au-dessus de 25 pas.** Mesuré : la médiane de fin d'épisode est de
25 pas, le maximum 59. Passer la limite de 60 à 28 ne change rien.
→ **Conséquence pour l'axe du stress** : la pression temporelle ne peut pas jouer tant que
les épisodes s'arrêtent d'eux-mêmes. Pour la tester un jour, il faudra une limite **sous**
25 pas, pas au-dessus. Le test du 27/07 était vide d'avance, pour cette raison en plus de
la saturation.

## La règle

**On ne retouche plus cette dureté.** Si un mécanisme échoue, on ne rend pas le banc plus
facile pour qu'il passe. Si on doit la changer, la nouvelle valeur se calibre à nouveau sur
les doctrines scriptées, et on refait TOUS les repères.

## Ce qui devient incomparable
Tous les chiffres antérieurs au 27/07 18 h sont mesurés à 4 défenseurs. Les repères
scriptés (frontal 36 %, crochet 90 %) et tous les verdicts de mécanisme sont à refaire
dans ce banc-ci avant d'être opposés à quoi que ce soit.
