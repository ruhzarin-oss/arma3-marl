# Calibrer l'adversaire — critères écrits avant le premier épisode

*20/09/2026 au soir, campagne `CALIBRATION-ADVERSAIRE-20-09`. Suite directe de la calibration cd3a22f : à son
budget normal l'Oracle fait tomber la réussite de 92 % à 72 %, mais **il ne dépense que 3,1 ordres sur 6**. Ce qui
le bride n'est donc pas sa provision, c'est le nombre d'occasions de décider. Cette campagne règle la manette, et
solde le contrôle négatif encore dû au plan § 7.*

## Ce qu'on cherche, et ce qu'on ne cherche pas

On règle un **instrument**. On ne mesure aucun effet de choix : l'option de traversée est équilibrée dans chaque
bras pour ne pas biaiser, et elle ne sera pas lue.

## Dispositif

Quatre bras, joués **entrelacés dans la même campagne** — jamais comparés d'une campagne à l'autre, la charge
machine déplace un taux de plusieurs points.

| bras | `oracle_cmd` | budget B | période δ | ce qu'il sert |
|---|---|---|---|---|
| **T** témoin | 0 | — | — | le monde sans personne en face |
| **N** négatif | 1 | **0** | 60 s | l'Oracle monté mais sans moyen : il doit être indiscernable de T |
| **R** référence | 1 | 6 | 60 s | le réglage d'aujourd'hui, rejoué ici pour être comparable |
| **F** fréquent | 1 | 6 | **30 s** | deux fois plus d'occasions de décider |

8 mondes × 4 situations × 4 bras = **128 épisodes**, 64 jobs de deux graines, 12 instances. L'option est équilibrée :
situations 1 et 2 en *traverser tout de suite*, situations 3 et 4 en *attendre*.

## Portes de qualité, avant toute lecture

- **K1** zéro erreur SQF sur les épisodes acceptés.
- **K2** aucune case (bras, monde, situation) sans le moindre résultat.
- **K3** au moins **24 épisodes valides par bras** sur 32 prévus.
- **K4** la ligne `CHACAL|O|carte` est présente dans **tous** les épisodes à Oracle monté.
- **K5 — contrôle négatif, critère mécanique** : dans le bras N, **zéro ordre de patrouille**, dans 100 % des
  épisodes. C'est une vérification exacte, pas statistique : un seul ordre et le contrôle échoue.
- **K6** les réglages joués (B et δ) relus dans le journal sont ceux du job.

Une porte qui échoue refuse la lecture entière.

## Les trois lectures

### L1 — contrôle négatif, versant issue

Écart de réussite `N − T`, IC 95 % par 10 000 rééchantillonnages appariés par monde, graine 20260920.
**Attendu : un écart nul.** S'il exclut zéro, l'Oracle agit sur le monde **autrement que par ses ordres de
patrouille**, et toute mesure faite avec lui est suspecte. C'est le falsificateur du contrôle négatif.

### L2 — calibration de la période δ

Réussite (`phase discrète`) des quatre bras, avec IC.

**Règle de décision écrite d'avance :** on retient le δ dont la réussite estimée est **la plus proche de 0,50**, à
condition que la **borne haute de son IC soit inférieure à 0,85** — sinon le plafond n'est pas cassé et le réglage
ne sert à rien.

**Honnêtement sur la puissance :** 32 épisodes par bras donnent un IC d'environ ±0,25 sur une différence. **C'est
une estimation pour régler une manette, pas un test.** Aucune prétention de significativité ne sera faite entre R
et F ; si leurs intervalles se recouvrent largement, on le dira et on choisira sur le point estimé, en assumant.

**Falsificateur :** si F ne gagne pas au moins **5 points** de punition sur R, la période de décision n'est pas le
levier, et il faudra chercher ailleurs — une seconde menace, ou une patrouille à pied.

### L3 — l'admissibilité d'un monde, mesurée et non décrétée

Pour chaque monde : nombre de cases atteignables par la route à 400 m, et distance de chaque case à sa route la
plus proche dans un rayon de 2 km (ligne `CHACAL|O|carte`, posée à la mise en place, avant que rien ne bouge).

Ce qu'on sait déjà, et qui motive la mesure : monde 5, la patrouille n'approche jamais à moins de **530 m** et ne
vise jamais la CRÊTE ; monde 12, elle n'a que **deux** cases atteignables. Ailleurs elle arrive à 5-35 m et
compromet 38 à 62 % des épisodes. **La prise de l'adversaire est une propriété de la route.**

**Cette campagne mesure, elle n'exclut rien.** Le seuil d'admissibilité sera pré-enregistré dans la campagne
suivante et **validé sur des mondes neufs** : un critère taillé sur les huit mondes qui l'ont inspiré ne prouve
rien tant qu'il n'a pas trié des mondes qu'il n'a jamais vus.

## Résultat — 21/09 00 h 15 : le contrôle négatif passe, la calibration de δ ne conclut pas

Six portes passées après réparation de l'unique case vide (bras R, monde 6, situation 3 — une réparation, pas un
amendement : K2 compte des cases précisément pour ça). 122 épisodes lus, 30 à 31 par bras, zéro erreur SQF.

### L1 — contrôle négatif : **PASSE**, et deux fois

- **Mécaniquement : 0 ordre de patrouille sur 31 épisodes** du bras N. L'Oracle monté sans budget délibère (2 à 9
  décisions par épisode) mais ne touche jamais au monde. Vérification exacte, pas statistique.
- **Sur l'issue :** réussite N 0,839 contre T 0,742, écart +0,097 IC [−0,062 ; +0,250], contient zéro.

C'est le deuxième des cinq contrôles du plan § 7 qui est soldé.

### L2 — calibration de δ : **NON CONCLUANTE**, et la faute est dans mon dispositif

| bras | réussite | compromis | ordres | IC de l'écart au témoin |
|---|---|---|---|---|
| T témoin | 0,742 | 0,258 | 0,0 | — |
| N négatif | 0,839 | 0,161 | 0,0 | [−0,062 ; +0,250] |
| R δ = 60 s | 0,733 | 0,267 | 3,0 | [−0,281 ; +0,188] |
| F δ = 30 s | 0,733 | 0,267 | 3,6 | [−0,250 ; +0,188] |

Le falsificateur écrit d'avance est **franchi** : F ne gagne pas 5 points de compromission sur R, il en gagne
**zéro**. Mais je ne conclus pas « la période n'est pas le levier », parce que **le bras de référence ne se
reproduit pas lui-même** : R devrait retrouver les +0,197 mesurés hier sur ORACLE-P2, et il donne **+0,009**.
Un contrôle positif implicite qui échoue interdit de lire le reste (règle 16).

**La cause, et c'est une faute de conception :** j'ai **confondu l'option avec la situation** — situations 1 et 2
en *traverser*, 3 et 4 en *attendre*. Les quatre bras partagent le même mélange, donc ils restent comparables
entre eux ; mais ce mélange est **chargé en cases où le monde punit déjà tout seul** :

| | (1, s1) | (1, s2) | (2, s3) | (2, s4) |
|---|---|---|---|---|
| témoin de la calibration | 0,125 | 0,125 | 0,250 | **0,571** |

Le témoin compromet **0,258 ici contre 0,082 sur ORACLE-P2**. Il ne reste presque plus de place au-dessus pour que
l'Oracle ajoute quoi que ce soit — le plafond que je croyais avoir cassé s'est reformé par le bas, à cause du
mélange que j'ai choisi. Et avec 30 épisodes par bras, l'IC vaut ±0,23 : il contient à la fois zéro **et** les
+0,20 d'hier. **Cette campagne ne sait pas les distinguer.**

**À refaire ainsi :** option **fixée** (traverser seule), quatre situations, quatre bras, 8 mondes — même coût,
plus de confusion, et la variance du choix en moins.

### L3 — l'admissibilité d'un monde : **mesurée, et elle prédit**

| cases atteignables par la route | mondes | compromission | patrouille au plus près |
|---|---|---|---|
| **7** | 7, 8, 9, 11 | 0,56 · 0,25 · 0,50 · 0,38 — **moyenne 0,42** | 27 · 20 · 199 · 24 m |
| **4 ou 5** | 4, 5, 6, 12 | 0,12 · 0,12 · 0,12 · 0,25 — **moyenne 0,15** | 145 · 193 · 615 · 6 m |

Et les cases hors route le sont franchement : la CRÊTE du monde 5 est à **1 865 m** de la route la plus proche,
les ABORDS à 1 899 m. Voilà pourquoi la patrouille n'y approchait jamais à moins de 530 m.

**`cases_routieres`, journalisé à la mise en place avant que rien ne bouge, prédit la prise de l'adversaire.**
Aucune exclusion n'est faite ici : le seuil sera pré-enregistré dans la campagne suivante et **validé sur des
mondes neufs**.

*Note d'instrument : l'affichage de L3 par le lecteur était cassé (les guillemets de l'array SQF étaient retirés
avant `literal_eval`). Réparé et relu ; c'est un descriptif, aucun effet n'en dépend.*
