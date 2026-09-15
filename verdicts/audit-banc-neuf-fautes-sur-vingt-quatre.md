# Audit du banc : neuf fautes sur vingt-quatre survivent à la réfutation

*15 septembre 2026. Six lectures indépendantes du banc CHACAL, chacune sur une famille de faute ;
chaque trouvaille confrontée aux 159 épisodes de référence par un vérificateur chargé de la
**réfuter**, avec son propre comptage écrit de zéro. 24 trouvailles, **9 survivent**.*

## La règle du jeu

Une faute n'existe que si elle se **manifeste**. Chaque trouvaille devait porter le fichier, la
ligne, le code cité, et surtout **la requête qui la compte dans les journaux réels et son résultat
chiffré**. Le vérificateur ne confirmait pas : il cherchait à réfuter, refaisait le comptage avec
sa propre requête, et concluait « ne tient pas » en cas de doute.

Cela a mordu. Les vérificateurs ont **rétrogradé leurs propres trouvailles** plutôt que de les
défendre — et c'est le meilleur signe que l'instrument fonctionnait.

## Ce qui tient, et ce que cela coûte vraiment

### 1. La file des objectifs ne fait qu'une passe — **la seule faute lourde**

`60_phases.sqf:1388`. Le `continue` abandonne **l'objectif**, pas seulement le porteur. Comptage
refait à l'identique, chiffre pour chiffre : 61 épisodes sur 159 ferment la phase 5 en `INCOMPLET`,
avec un reste de plafond médian de **549 s** (min 352, max 701) sur 900, et la file entière ne dure
que 171 s en médiane. Les hommes sont là : 7 vivants en médiane à la fermeture.

Le vérificateur a fait ce que la lecture initiale n'avait pas fait — **borner la bascule** :

> **38 épisodes sur 159 changeraient d'issue**, et eux seuls : ce sont les `INCOMPLET` qui
> remplissaient *déjà* l'autre moitié du critère (`exfiltrés ≥ 6`). La mission passerait de
> **52,8 % à 76,7 %**. Les 23 autres ne basculeraient pas : leurs exfiltrés valent 0, 5 ou 3.

Et il a isolé l'**incrément propre** : sur ces 38, 33 sont purement `PORTEUR_N_ARRIVE_PAS`. Une
seconde passe de la file ne rapporterait donc que **5 épisodes sur 159** de plus que le correctif
du porteur seul. Réparé par graine : g12 14, g7 12, g8 7, g11 5 — réparti, pas concentré.

Il refuse aussi d'aller plus loin, et il a raison : le contrefactuel suppose qu'une relance réussit
et ne coûte rien, alors qu'elle coûte 200 à 500 s de plus dans l'enceinte, sous le feu, avec 5 à 7
hommes. 38 est un **plafond**, pas une prévision.

### 2. La réserve ennemie ne part jamais, et le bouchon la garde quand même

`30_opfor.sqf:56`. Au palier 4 : `qrf|0` véhicule, et `delai_qrf|9999` s contre **2078 s** pour
l'épisode le plus long — le seuil est à 4,8 fois la plus longue partie jamais jouée. `qrf_partie` :
**0 ligne sur 159 épisodes**.

Trois hommes sur dix — et le critère de succès en exige six exfiltrés — gardent donc une menace qui
ne peut pas exister. Mesuré au dernier tick, sur les 159 :

| | survie | distance médiane au point de ramassage | tirs |
|---|---|---|---|
| bouchon (AT, FUSILIER_1, FUSILIER_2) | 158, 159, 159 sur 159 | 1,1 m · 11,7 m · 9,0 m | 31 |
| assaut (CHEF, DEMO_1, DEMO_2, MÉDECIN, ADJOINT) | 72, 93, 97, 101, 112 | 68 à 97 m *(survivants seuls)* | 5 753 |

Arrivées au point de ramassage : **bouchon 384, assaut 273, appui 178**. Le bouchon, 30 % de
l'effectif, fournit **46 % des exfiltrés**. Il part en plus avec 242 m d'avance mécanique, son poste
étant à 45° de l'axe vers le point de ramassage. Et **80 des 84 succès ont exactement 6 exfiltrés :
marge nulle.**

**Gravité : INCONNUE, et le vérificateur a refusé de l'inventer.** Ses mots : *« je ne peux nommer
aucun épisode sur 159 dont cette faute change l'issue, et je refuse de convertir un compte de survie
en un compte de bascules »*. Le contrefactuel juste — reverser ces trois hommes à l'assaut — **n'existe
dans aucun bras du corpus**. Direction inconnue : ils gagneraient peut-être des charges, mais
perdraient 3 des 6 exfiltrés exigés et s'exposeraient à 40 % de mortalité.

C'est le point le plus inconfortable de l'audit, et il reste ouvert. Il demande un bras, pas un
raisonnement.

### 3 à 9. Les fautes réelles dont le coût est petit — et pourquoi il faut quand même les dire

| | faute | ce qu'elle change sur la référence |
|---|---|---|
| 3 | `CHACAL_ASSAUT_X` ne multiplie qu'un plafond jamais atteint, et toutes ses valeurs le desserrent | rien : levier inerte pour ses 4 valeurs |
| 4 | `CHACAL_TENIR` n'a de fenêtre qu'en phase 2 et 4 ; à `depart=5` la phase 4 dure 8 s | rien : les deux valeurs donnent le même monde, et la porte d'identité en donne l'assurance |
| 5 | `FIN.json` dit COMPLET en comptant les épisodes REFUSÉS comme « lus » | **0 épisode ne bascule** ; au plus 1,0 point sur le taux, et dans le sens conservateur |
| 6 | le levier `tactique` est écrasé par la mission puis journalisé sous son propre nom | le corpus ne peut plus dire quel bras a été joué ; 10 épisodes sur 10 rendent 1 pour un job qui demandait 5 |
| 7 | `values[]` ne serait pas une garde : une valeur hors liste serait jouée telle quelle | **question ouverte** — voir plus bas |
| 8 | les 159 épisodes ne sont pas une population unique | **0,3 point** — voir plus bas |
| 9 | la chasse de la réserve dort sans re-tester `CHACAL_FIN` : quatrième boucle de la même forme | 0 sur la référence ; **1 épisode sur 1269** sur tout le corpus, perdu en entier |

Sur la n° 5, le vérificateur a trouvé le chiffre que la lecture initiale n'avait pas donné, et il est
plus parlant que le sien : **sur 242 épisodes REFUSÉS de tout le corpus, 238 sont logés dans un run
marqué COMPLET. 98,3 % des refus ne remontent jamais au niveau du run.** La mesure est saine, la
supervision est aveugle.

Sur la n° 9, le point à retenir n'est pas le chiffre mais sa fragilité : la faute est invisible
*parce que* les campagnes tournent au palier 4. Le défaut de `CHACAL_PALIER` est **3**, soit 45 s de
délai. Toute campagne qui ne fixe pas le palier la réveille.

## Les deux trouvailles qui visent mon propre travail

### La n° 8 : le corpus de référence n'est pas homogène — et cela ne change rien

Reproche fondé : 15 épisodes viennent d'une campagne antérieure, 3 des 144 autres sont REFUSÉS par
le lecteur. J'ai publié tous mes chiffres de la nuit sur 159. J'ai refait le calcul sur le corpus
propre :

| population | n | mission | charges complètes | porteurs arrivés | plafond |
|---|---|---|---|---|---|
| les 159, ce que j'ai publié | 159 | 52,8 % | 61,6 % | 88,7 % | 76,7 % |
| `REFERENCE-PROPRE` acceptés | **141** | **52,5 %** | 61,0 % | 88,1 % | 77,3 % |

**0,3 point d'écart sur la mission, moins d'un point partout.** Le mélange n'a pas faussé mes
conclusions. Je le dis parce que c'est vrai, pas parce que cela m'arrange : l'écart aurait pu être
grand, et le contrôle devait pouvoir échouer.

### La n° 7 : `values[]` est-elle une garde ? — **je n'en sais rien, et j'avais affirmé le contraire**

J'ai écrit dans `le-porteur-narrive-pas-et-personne-ne-le-remplace` qu'une valeur absente de
`values[]` retombe **silencieusement au défaut**, et j'ai choisi 180 plutôt que 150 pour cette
raison. L'audit soutient l'inverse : aucun étage ne validerait la valeur — ni le moteur, ni
`controle_avant_run.sh` qui ne lit jamais `description.ext`, ni `lancer.sh`.

Balayage du disque : **aucun job n'a jamais demandé de valeur hors liste.** La mesure ne peut donc
pas trancher sur l'existant. Un job de quatre minutes est en file — `delai_porteur = 150`,
`geometrie=1`, cinq graines vierges — et il lira ce que la mission a réellement joué. Tant qu'il n'a
pas parlé, **la phrase de mon verdict est une affirmation sans preuve**, et elle est signalée comme
telle.

Le choix de 180 reste bon dans les deux cas — c'est le maximum déclaré, donc le plus puissant. Seule
la *raison* que j'en ai donnée est en sursis.

## Ce qui a été fait cette nuit en conséquence

- **Correctif appliqué et commité** (`43b3480`) : `inst_de()` de `file3.sh` rendait une chaîne
  **vide**, et non `"?"`, quand sa lecture échouait — ce qui arrive quand un distributeur concurrent
  déplace le fichier pendant la lecture. Le verrou créé s'appelait alors `j` tout court : il ne
  protégeait aucune instance et comptait quand même dans le plafond. Dégât mesuré : le job
  `DELAI180-g8-m2` est parti **deux fois sur l'instance 10**, deux serveurs Arma sur le profil
  `hmtech10` et le port 2502, RPT partagé, numérotation des épisodes trouée. Les deux runs sont
  écartés du corpus et le job rejoué. Cause aggravante assumée : mes déclenchements de `HMT_RUN` en
  rafale toutes les 7 s pour remplir les dix instances ouvraient grand la fenêtre de course.

- **Non appliqué, délibérément** : les fautes 1 à 9 touchent la mission, et trois campagnes tournent.
  On ne modifie pas la mission pendant un run — le lanceur la resynchronise à chaque épisode.

## Ce que l'audit dit de la méthode

Vingt-quatre trouvailles, neuf survivantes, et parmi ces neuf **une seule** change plus de 1 % des
épisodes. Le rendement est faible en apparence — il est exactement ce qu'il doit être : sans
l'obligation de compter dans les journaux, les quinze réfutées auraient été publiées, et parmi elles
des affirmations fausses sur le taux de réussite.

Le contre-exemple est la n° 5 : lue seule, elle annonçait une contamination du corpus. Comptée, elle
ne fait basculer **aucun** épisode et va dans le sens conservateur. Une faute réelle dont le coût est
nul reste une faute — mais on ne réécrit pas un verdict pour elle.

*Voir aussi : `le-porteur-narrive-pas-et-personne-ne-le-remplace`,
`le-script-ne-choisit-pas-son-ouverture`, `un-levier-ecrit-nest-pas-un-levier-lu`,
`phase3-porte-hors-datteinte`, `regle16-controle-positif-instruments`.*


---

## Amendement : la taille de la question n° 2, chiffrée sans dépenser un épisode

Le vérificateur avait refusé de donner une gravité à la faute de la réserve, et il avait raison :
le contrefactuel juste — reverser les trois hommes du bouchon à l'assaut — n'existe dans aucun bras.
Mais on peut faire autre chose, qui ne demande aucun épisode : **re-noter les épisodes déjà au
disque** en ne comptant que les hommes engagés.

**Contrôle d'abord.** La recomposition des exfiltrés à partir des instantanés `CHACAL|S|`, des
rôles lus sur les lignes `E|spawn` et de la position du point de ramassage reproduit le compte que
le script écrit lui-même — **159 épisodes sur 159**, à une unité près. L'instrument sait donc lire
ce qu'il prétend lire.

| critère | succès |
|---|---|
| officiel : 6 exfiltrés sur 10, bouchon compris | 84/159 = **52,8 %** |
| 4 exfiltrés parmi les 7 **engagés** (0,6 × 7, seuil proportionné) | 20/159 = **12,6 %** |
| 6 exfiltrés parmi les 7 engagés (strict) | 6/159 = 3,8 % |
| charges seules, sans condition d'exfiltration | 98/159 = 61,6 % |

Médiane des exfiltrés : **3 du bouchon, 3 du reste**. La moitié du critère est remplie par trois
hommes dont l'adversaire, au palier 4, est configuré pour ne jamais arriver — et qui rentrent dans
99 % des épisodes, avec 242 m d'avance mécanique.

### Ce que ce tableau dit, et ce qu'il ne dit pas

**Il ne dit pas que 12,6 % est le « vrai » taux.** Demander 4 exfiltrés sur 7 engagés est une
mission *différente*, et plus dure. Personne ne l'a jamais jouée.

**Il dit que le critère est bien plus facile que « 6 sur 10 » ne le laisse croire.** Trois des six
sont quasi acquis avant que le premier coup ne parte. Et le critère n'a **aucune marge** : 80 des 84
succès ont exactement 6 exfiltrés. Retirer un seul homme du bouchon du comptage fait tomber la
quasi-totalité des succès.

**Conséquence pour le but du projet.** On veut mesurer si un agent sait mener la mission. Si la
moitié du critère de succès est satisfaite par des hommes hors du combat, alors la mesure est
faiblement couplée à la compétence de l'agent : elle bougera peu quand l'agent s'améliorera, et
elle bougera beaucoup pour des raisons qui ne le concernent pas.

C'est une question de **validité de mesure**, pas une faute de code. Elle ne se tranche pas en
lisant du SQF : elle demande une décision sur ce que la mission doit demander. Elle est posée ici,
chiffrée, et laissée ouverte.
