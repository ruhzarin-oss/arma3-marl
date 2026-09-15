# Le délai du porteur : établi sur l'assaut, non établi sur la mission

*15 septembre 2026. Deux campagnes appariées, 357 épisodes, bras entrelacés dans la file pour que
la charge machine et l'heure soient les mêmes des deux côtés.*

## Ce qui est établi

**Sur l'assaut, le levier porte.** `delai_porteur` de 45 à 180 s, six mondes, 261 épisodes :

| graine | délai 45 | délai 180 | écart |
|---|---|---|---|
| 5 | 13/24 = 54 % | 11/13 = 85 % | +30 |
| 6 | 14/24 = 58 % | 16/24 = 67 % | +8 |
| 7 | 19/24 = 79 % | 14/16 = 88 % | +8 |
| 8 | 13/24 = 54 % | 30/38 = 79 % | +25 |
| 11 | 15/24 = 62 % | 8/12 = 67 % | +4 |
| 12 | 15/24 = 62 % | 11/14 = 79 % | +16 |

**Écart apparié +15,4 points, IC 95 % [+4,0 ; +26,4], six signes sur six, p = 0,031.** Le
falsificateur posé d'avance — « moins de 8 points » — n'est pas franchi.

**Et le mécanisme est mesuré directement, pas inféré :**

```
porteurs arrivés à moins de 12 m   délai  45 : 355/394 = 90,1 %  [87 ; 93]
                                   délai 180 : 319/333 = 95,8 %  [93 ; 97]
porteurs à bout de délai           délai  45 : 34
                                   délai 180 :  6
PLAFOND_PHASE                      absent des deux bras
```

Le levier fait exactement ce que le diagnostic annonçait : il convertit les porteurs *bloqués*. Ce
qui reste à 180 s est de la **mort de porteur** — 79 % des échecs restants, contre 49 % à 45 s.

## Ce qui n'est pas établi

**Sur la mission, le gain tombe de moitié et ne franchit pas le seuil.** Quatre mondes, 96 épisodes,
`arret=6`, la phase 6 réellement jouée :

| | écart apparié | IC 95 % | signes |
|---|---|---|---|
| charges complètes | +16,7 pts | [−2,1 ; +35,4] | 3/4 |
| **mission réussie** | **+10,4 pts** | **[−8,3 ; +29,2]** | 3/4, p = 0,625 |

Les causes disent où passe la moitié manquante :

```
                       délai 45        délai 180
CHARGES_INCOMPLETES    24/48 = 50 %    16/48 = 33 %     -17 points
EXFIL_MANQUEE           2/48 =  4 %     6/48 = 13 %     + 8 points
```

Le gain sur l'assaut est repris pour moitié au décrochage. **Ce reversement n'est pas significatif
en lui-même** (Fisher p ≈ 0,27), mais il va dans le sens enregistré d'avance et il apparaît dans
les deux lectures successives de la campagne.

C'était la limite écrite avant de lancer : *« à `arret=5` la phase 6 n'est pas jouée : on mesure le
bénéfice d'un homme exposé plus longtemps sans en mesurer le coût »*. La mesure a fait son travail.

## Décision : le levier n'entre PAS dans le socle

La règle posée d'avance était de remesurer à `arret=6` avant d'écrire quoi que ce soit. C'est fait,
et le résultat mission n'est pas établi. **On n'écrit pas 180 s par défaut.**

Ce qu'il faudrait pour trancher : plus de **mondes**, pas plus d'épisodes par monde. Le plan est
apparié, donc la puissance vient du nombre de mondes. Huit mondes concordants donneraient p = 0,008
au test des signes ; quatre plafonnent à 0,625 même quand trois sont positifs.

## La réserve qui domine tout le reste

**Les niveaux absolus de ces campagnes ne sont pas comparables à la référence historique, et je ne
sais pas pourquoi.**

Le bras témoin à 45 s donne 43,8 % de mission sur les graines 7, 8, 11, 12. La référence de 159
épisodes en donne 52,8 % sur les **mêmes** quatre mondes. Et sur la graine 11, les charges tombent
de 72 % à 25 % — Fisher p ≈ 0,006.

J'ai cherché la cause et je ne l'ai pas trouvée :

- **Le point visé est le même.** En mode IMPOSE le point est recalculé par
  `CHACAL_SITE getPos [46, round(az+108)]` ; en mode normal il vient de `CHACAL_OUVERTURES`, bâti
  depuis `_c = CHACAL_SITE` avec le même rayon et le même gisement. Écart : l'arrondi, moins d'un
  mètre sur une ouverture large de 16,5 m.
- **Le correctif du chien ne change aucun comportement**, seulement une ligne de journal.
- **La charge machine est un suspect** — le banc avertit lui-même que la parallélisation n'a été
  mesurée que jusqu'à deux instances, et le plafond est passé à dix le 14/09. Mais le test est
  **confondu** : les 48 épisodes à charge forte sont tous la campagne de confirmation, les 159 à
  charge faible toutes la référence. Et à graine fixée les signes se contredisent — g7 +10, g8 +6,
  g11 −47, g12 −14. À l'intérieur d'un même bras, un seul monde a assez d'épisodes de part et
  d'autre de la médiane de charge : le test ne peut rien dire.

**Conséquence.** Les comparaisons **appariées à l'intérieur de chaque campagne tiennent** — les deux
bras ont été entrelacés dans la file précisément pour cela, et ils ont tourné à la même heure sous
la même charge. Les **niveaux absolus** ne tiennent pas contre l'historique.

**Ce qu'il faudrait :** un bras exprès, mêmes mondes, même nuit, deux niveaux de parallélisme — deux
instances contre dix. Tant qu'il n'existe pas, tout taux publié doit porter le nombre d'instances
qui tournaient quand il a été mesuré.

## Ce qui est prêt et n'a pas été appliqué

Trois campagnes tournaient ; le lanceur resynchronise la mission à chaque épisode, donc on ne touche
à rien pendant. Deux correctifs attendent, machine au repos, derrière quatre gardes (aucun serveur,
file vide, aucun verrou, dépôt propre) :

- **La relève du porteur** — essayer les porteurs suivants sur le *même* objectif, plafond de trois
  tentatives. Testé à blanc, idempotent, équilibre des délimiteurs inchangé, **zéro `continue` et
  zéro `break` dans la boucle interne** (le piège SQF : ils sortiraient du `forEach` extérieur), les
  quatre sorties dans la condition du `while`. La première tentative est exemptée du garde-fou de
  budget : sans cela le correctif serait une *régression* dans une fenêtre de ~184 s.
  **Gain borné par la mesure : 11 cas de mort de porteur sur 68 épisodes à 180 s.**
- **L'avertissement sur les valeurs hors liste** — `values[]` n'est pas une garde, c'est mesuré
  (voir `le-porteur-narrive-pas-et-personne-ne-le-remplace`). Rien n'arrête une faute de frappe dans
  un job. Le contrôle avertit et ne refuse jamais ; son contrôle positif passe.

*Voir aussi : `le-porteur-narrive-pas-et-personne-ne-le-remplace`,
`audit-banc-neuf-fautes-sur-vingt-quatre`, `le-script-ne-choisit-pas-son-ouverture`,
`parallelisation-arma-mesuree`.*


---

## CORRECTION DU TITRE ET DU RESULTAT : « établi » était prématuré

Ce verdict a été écrit alors que la campagne n'était pas finie — 261 épisodes de vignette sur 288.
Elle en compte maintenant **302**, et le résultat a changé :

| | écart apparié | IC 95 % | signes | p |
|---|---|---|---|---|
| ce que j'ai publié (261 ép.) | +15,4 pts | [+4,0 ; +26,4] | 6/6 | **0,031** |
| **données complètes (302 ép.)** | **+11,1 pts** | **[+0,7 ; +21,6]** | **5/6** | **0,219** |

La graine 7 est passée de +8 à **+0** (19/24 contre 19/24) et la graine 5 de +30 à +17.

**Le titre de ce verdict est donc faux.** L'effet sur l'assaut n'est pas *établi* : le test des
signes ne franchit plus le seuil, et l'intervalle de confiance n'exclut zéro que d'un cheveu
(+0,7). Le bon énoncé est : **l'effet est probablement réel et de l'ordre de dix points, mais il
n'est pas démontré.**

### Ce qui n'a pas bougé, et qui reste le plus solide

```
porteurs arrivés à moins de 12 m   délai  45 : 355/394 = 90,1 %
                                   délai 180 : 422/444 = 95,0 %
porteurs à bout de délai           délai  45 : 34
                                   délai 180 :  9
```

Le mécanisme se mesure sur 838 porteurs envoyés, pas sur 302 épisodes : c'est l'énoncé qui a le
plus de matière derrière lui, et c'est lui qu'il faut retenir. **Le levier fait arriver les
porteurs. Qu'il fasse gagner la mission n'est pas montré.**

### La faute, et sa règle

J'ai lu un résultat intermédiaire et je l'ai qualifié d'établi. Les intervalles étaient publiés à
chaque lecture — ils ont toujours contenu +11 — mais le mot « établi » s'appuyait sur un p calculé
à mi-campagne.

**Un p qu'on regarde pendant que les données arrivent n'est pas un p.** Il faut fixer la taille de
l'échantillon d'avance et ne lire qu'à la fin. Je l'avais fait pour le falsificateur (« moins de
8 points »), pas pour le seuil de significativité.

*Le falsificateur pré-enregistré, lui, tient : +11,1 points reste au-dessus de 8.*
