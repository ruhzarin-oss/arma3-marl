# Le script ne choisit pas son ouverture, et la porte B n'a jamais été jouée

*14 septembre 2026. Mesuré sur 145 épisodes de référence déjà au disque et sur les 137 mondes
dont la géométrie est connue. Aucun épisode n'a été dépensé pour ce verdict.*

## Ce qui est établi

**1. À l'intérieur d'un monde, rien de ce qui est connu avant l'assaut ne prédit son issue.**

145 épisodes de `REFERENCE-PROPRE-13-09` et `REFERENCE-JAMBES-13-09`, quatre graines (7, 8, 11, 12),
84 réussites contre 61 `CHARGES_INCOMPLETES`. Vingt-cinq variables connues avant l'assaut ont été
comparées entre les deux groupes, **graine par graine**.

Les variables qui semblent séparer — `d_pz` (écart normé 0,32), `d_qrf` (0,31), `azimut_joue` (0,30),
`d_op` (0,29), `d_route` (0,28) — sont **constantes à l'intérieur d'une graine** : ce sont des
distances du site, tirées avec le monde. Elles ne séparent qu'entre graines, parce que les graines
n'ont pas le même taux. C'est un Simpson, pas un signal.

Les seules variables qui varient réellement d'un épisode à l'autre — `ouv_score`, `dist_a`, `dist_b`,
`t_choix`, `t_ph5`, `t_premier_pas` — donnent toutes un écart normé inférieur à 0,16, et leur signe
change d'une graine à l'autre (`+-++`). Rien.

Une seule variable discrète sépare, et c'est une conséquence, pas une décision : la **cause** du
compromis. `FEU_PROCHE` dans 47,5 % des échecs contre 32,1 % des réussites ; `ENNEMI_VU_EN_COMBAT`
dans 49,2 % des échecs contre 67,9 % des réussites. Être trahi par un tir proche va avec l'échec.
Mais cela se sait *pendant* la fusillade, pas avant.

À choix figés, la variance de la mission est du bruit de combat. Cela rejoint
`champ-spatial-ne-sapprend-pas` et `modele-monde-retrouve-le-tarif` : *quand* oui, *où* non.

**2. Le choix de l'ouverture est gelé.**

```
ouv_indice = 0     dans 145 épisodes sur 145
gardes_a   = 0     gardes_b = 0     dans 145 sur 145
ouv_rens   = 0     dans 145 sur 145
```

La ligne `E|choix_ouverture` a été écrite pour enregistrer une décision. Elle enregistre une
constante. Le script prend toujours la première ouverture, n'a jamais vu un garde à l'une ni à
l'autre, et n'a jamais eu de renseignement. Ce n'est pas un choix : c'est un défaut.

C'est le même motif que `un-levier-ecrit-nest-pas-un-levier-lu`, d'un cran plus profond : ici le
levier est lu, mais l'instrument qui devait mesurer la décision mesure une valeur qui ne bouge pas.
**Un instrument dont toutes les lectures sont identiques n'a pas été contrôlé.**

**3. L'enceinte est la même dans les 137 mondes.**

```
portes = [108,000 ; 282,857] relatifs à az    dans 137 mondes sur 137
```

Seule la rotation `az` change — `az` étant par construction la direction site → crête. La géométrie
de l'objectif ne dépend pas du site. Ce qui dépend du site, c'est ce qu'il y a autour : le
relèvement de la dépose, le terrain, la crête d'où l'ennemi observe.

**4. La porte B n'a jamais été jouée. Pas une fois, sur aucun monde.**

Balayage des 137 mondes : aucun épisode, dans aucune campagne, n'a joué un azimut à moins de 5° de
`az + 282,857`. La campagne d'azimut du 13–14/09 a fait tourner la direction sur une grille de
multiples de 30° — qui ne tombe jamais sur la seconde porte.

## Ce que cela corrige dans ce qui était écrit

`azimut-ne-porte-pas-et-le-bruit-commande` chiffrait l'effet de l'azimut par l'écart entre la
meilleure et la pire case d'une grille : 33 points sur g7, 67 sur g8. **Cet estimateur est biaisé
vers le haut** — c'est le maximum de sept cases de six épisodes, donc gonflé par le bruit.
L'ajustement d'une sinusoïde sur les mêmes données donne l'amplitude honnête : **24 points sur g7,
14 points sur g8**. L'effet reste réel ; il est deux fois plus petit qu'annoncé.

Et la question « l'optimum d'azimut est-il une constante en relatif ? » est **indécidable à cette
échelle** : l'intervalle de confiance à 90 % de l'écart des phases entre les deux graines est
[−132° ; +86°], large de 218°. Le test ne sait pas échouer, donc il ne conclut pas — ni dans un sens
ni dans l'autre. Le trancher sur un azimut continu demanderait plus de 400 épisodes.

## Ce qui est ouvert, et pourquoi c'est la bonne question

La direction d'attaque est le **seul** levier pré-assaut dont l'effet soit démontré. Le script en
joue une valeur et une seule, sans regarder. Et le choix entre les deux portes est une décision à
**un bit** — infiniment moins cher à trancher qu'un azimut continu.

Deux issues, toutes deux utiles :

- **une porte bat l'autre partout** → une constante à écrire, et des points gratuits sur une mission
  qui est à 51,4 % ;
- **le gagnant change selon le monde** → c'est la première décision dépendante du site du projet,
  donc la cible d'entraînement qu'on cherche depuis le début.

**Prédiction géométrique enregistrée d'avance.** `az` est la direction site → crête. La porte A est
donc à +108° de la crête, la porte B à −77°. La force arrive de la dépose, dont le relèvement varie
selon le monde. Si le gagnant change, il devrait être la porte dont le relèvement est le plus proche
de celui de l'arrivée, ou le plus éloigné de la crête d'où l'ennemi observe. Ces deux règles se
calculent sur des données déjà au disque — elles pourront être confrontées sans dépenser un épisode
de plus.

**Falsificateur de la campagne.** Si la porte B n'est jamais atteinte (`E|ouverture|issue` jamais
`ATTEINT`), elle est hors d'atteinte comme l'était le seuil 3 de la phase 3 — 110 échecs sur 111 et
55 heures pour zéro information — et la campagne n'a pas lieu d'être. C'est le premier des trois
contrôles posés avant elle.

## Méthode

Le tort évité ici est celui du 13/09 : conclure d'un écart entre graines. Toute comparaison a été
refaite **à l'intérieur de chaque graine**, et c'est cette précaution seule qui a fait tomber les
cinq variables de tête. Une variable constante par monde ne peut rien expliquer de ce qui varie
dans ce monde.

*Voir aussi : `une-graine-n-est-pas-un-monde`, `un-levier-ecrit-nest-pas-un-levier-lu`,
`phase3-porte-hors-datteinte`, `azimut-ne-porte-pas-et-le-bruit-commande`.*


---

## Amendement du 15 septembre : réparer le seuil ne servirait à rien

Le corps de ce verdict montrait que le terme « gardes » de la règle de choix est inerte par
construction — seuil de 110 m contre une corde de 92 m entre les deux ouvertures. La réparation
évidente était de rétrécir ce seuil pour que la règle voie enfin de quel côté sont les défenseurs.

**Cette réparation ne vaut rien, et c'est mesuré.** Sur les 159 épisodes de référence, on a
reconstitué la position des quatre défenseurs à l'instant exact du choix, depuis les instantanés
`CHACAL|S|` du journal, puis calculé l'asymétrie : combien sont plus près de la porte A, combien de
la porte B.

À graine fixée, cette asymétrie ne prédit rien :

| | valeur | intervalle à 95 % | p |
|---|---|---|---|
| pente intra-graine | **−0,1 point** par défenseur déplacé | [−4,2 ; +4,4] | 1,00 |
| Mantel-Haenszel, asym > 0 contre asym ≤ 0 | OR = 0,83 | — | 0,86 |
| écart de taux pondéré intra-graine | −5,4 points | [−29,3 ; +17,3] | — |
| asymétrie de **cap** (cône de 60°) | −0,85 point | — | 0,84 |

Le signal apparent — **−1,8 point** par unité en lecture poolée — est un **Simpson d'un facteur 18**.
La graine 7 est la deuxième meilleure (58,8 %) et ne produit *jamais* d'asymétrie positive ; la
graine 12, deuxième pire (44,4 %), en produit dans 42 % de ses épisodes. Lu en vrac, le tableau
donne 61,5 % à asym = −4 contre 33,3 % à asym = +4. C'est une composition de graines, pas un effet.

### Le contrôle qui rend ce zéro lisible

Un zéro ne vaut que si l'instrument sait produire autre chose qu'un zéro. Celui-ci a deux contrôles,
et le second est le bon :

- les quatre défenseurs sont vivants et recensés dans **159 épisodes sur 159** ; aucun au-delà de
  55 m du site — et 55 m est bien le rayon de garnison écrit dans `30_opfor.sqf`, pas les 46 m du
  mur que l'on croyait ;
- **l'extracteur reproduit les `distances|[da,db]` que le script écrit lui-même, à 0,96 m près pour
  la porte A et 1,19 m pour la porte B, sur 159 épisodes sur 159** — médianes 0,23 et 0,25 m.

Ce second contrôle valide d'un coup la lecture du format `S`, les positions calculées des deux
ouvertures et l'identification des cinq hommes d'assaut. Il a d'ailleurs fait son travail en levant
une erreur : un cinquième « défenseur » apparaissait dans 16 épisodes — le canari, recensé avant que
son rôle ne soit posé.

### Ce que cela change

La couture du choix d'ouverture n'a pas d'entrée informative connue. Si la porte compte — c'est ce
que mesure `PORTE-A-CONTRE-PORTE-B-14-09` —, ce qui la commande n'est pas où se tiennent les
défenseurs, mais quelque chose du terrain : relèvement de l'arrivée, crête, cheminement.

Et surtout : le goulot de l'assaut est ailleurs. Voir
`le-porteur-narrive-pas-et-personne-ne-le-remplace`.
