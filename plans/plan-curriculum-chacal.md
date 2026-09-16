# Plan — le curriculum CHACAL

*16/09/2026. Proposition, à valider par Younes avant construction.*

## Le principe

L'agent n'apprend plus sur une mission de 3 h dont l'essentiel est de la marche. Il apprend sur des **vignettes** :
chacune démarre quelques secondes avant un choix et s'arrête dès que la conséquence est connue, en moins de 10 min.
Chaque phase a **10 variantes** (10 situations différentes). Avant chaque choix, l'agent lit une **fiche** qui dit ce que
chaque option coûte et rapporte, chiffres mesurés à l'appui. Il monte en difficulté jusqu'à la mission complète.

## 1. Les fondations, communes à toutes les phases

| brique | ce qu'elle fait | pourquoi |
|---|---|---|
| **Départ au choix** | pose le détachement dans l'état voulu (position, pertes, alarme, réserve) juste avant la décision | supprime la marche ; appliqué **après** le tirage du monde, sans consommer d'aléa (faute n°7) |
| **Arrêt à la conséquence** | ferme l'épisode quand l'effet du choix est connu, pas à la fin de la phase | leçon du 16/09 : `arret=5` coupait le combat du bouchon |
| **Point de décision** | chaque choix est un paramètre **forcé** et une **question posée à l'agent** par le pont (fichier, 0,5 s) | forcé pour mesurer, posé pour apprendre |
| **Ligne de décision unique** | `E\|decision\|t\|phase\|point\|options\|choix\|observables` | une seule table dbt `decision` : les triplets situation, action, issue |
| **Fiche** | générée par dbt : options, effets mesurés avec effectif et incertitude, « non mesuré » sinon | l'agent décide informé, jamais sur des chiffres inventés |
| **Mondes séparés** | mondes d'entraînement et d'évaluation distincts, identifiés par leur **site**, à plus de 1 km l'un de l'autre | une politique avait déjà mémorisé son site ; deux graines peuvent donner le même monde |

## 2. Les six phases

### Phase 1 — Insertion
- **Vignette** : départ au poser, arrêt 5 min après ou à la première détection.
- **Choix** : poser loin (discret, plus de marche) ou près (rapide, bruit à portée) ; attendre l'adaptation à la nuit ou partir tout de suite.
- **Variantes** : patrouille absente, à 500 m, à 1 km ; relief entre le poser et l'ennemi ; bruit du vol.
- **Problème** : au palier 4 il n'y a **ni ronde, ni patrouille, ni véhicule sur la route**. Personne ne peut entendre le poser : les options sont interchangeables. Il faut **créer une menace** avant tout.
- **À construire** : départ au poser, distance du poser, une menace minimale.

### Phase 2 — Approche
- **Vignette** : départ à 200 m de la route, arrêt 150 m après ou à la détection.
- **Choix** : traverser tout de suite, attendre d'avoir vu passer la patrouille, ou attendre longtemps ; itinéraire couvert et long ou direct et exposé ; en file ou dispersés.
- **Variantes** : trafic (aucun, 1, 2 véhicules), rythme de la patrouille, route droite ou en courbe, couvert disponible.
- **Existe** : la règle de traversée (`FENETRE_OBSERVEE` / `TRAVERSEE_AVEUGLE`), mais le script décide seul, et **sans trafic au palier 4 elle ne sert à rien**. Les paliers 0 à 3 ont une patrouille de route.
- **Mesuré** : le coût d'un itinéraire est son exposition par mètre ; la pente dans le sens de la marche décide du régime.

### Phase 3 — Observation
- **Vignette** : départ au pied de la crête (pas au regroupement à 900 m), fenêtre d'observation courte, arrêt au compte rendu.
- **Choix** : observer longtemps ou partir vite ; monter à 2 ou à 1 ; observer **l'enceinte** ou **la route de la réserve**.
- **Variantes** : défenseurs visibles, distance de la crête, réserve présente ou non et à quelle distance.
- **Problème** : la phase la plus faible. De nuit à 770 m la crête voit 0 à 3 défenseurs ; **savoir où ils sont ne fait pas gagner** (oracle 8/18 contre 4/12 ; la porte ne compte pas) ; et avant l'alarme **le temps ne coûte rien**, donc observer long ou court est interchangeable.
- **Proposition** : réorienter l'observation vers **la réserve**. Savoir si elle est là et à quelle distance est l'observable qui devrait décider du partage en phase 4.

### Phase 4 — Mise en place
- **Vignette** : le choix se fait en phase 4 mais ses effets tombent en phase 6. Il se teste dans une **vignette de phase 6 qui démarre avec le partage déjà appliqué**.
- **Choix** : combien au bouchon (3, 2 ou 1) ; appui sur la crête (loin, à l'abri) ou rapproché (tir efficace, exposé) ; par quelle porte.
- **Variantes** : réserve absente, 1 ou 2 véhicules, à 1 ou 2 km, délai court ou long.
- **Existe** : `partage`, `qrf_n`, `qrf_delai`, `qrf_dist`, `appui_feu`, `placeur`. Combat au bouchon dans ~80 % des épisodes à `arret=6`.
- **La porte** : mesurée sans effet. Elle reste comme **choix témoin** — un bon agent doit apprendre qu'elle est indifférente.

### Phase 5 — Assaut
- **Vignette** : départ phase 5, ~8 min — **la seule qui tient déjà en 10 min**.
- **Choix** : infiltration silencieuse, base de feu ou neutralisation préalable ; l'appui tire avant l'assaut ou non ; mitrailleuse à l'assaut ou à l'appui ; attendre le porteur blessé ou passer à l'objectif suivant.
- **Variantes** : 4 à 8 défenseurs, mitrailleuse servie ou non, alarme déjà donnée ou non, blessés au départ.
- **Existe** : `tactique`, `feu_avant`, `mg_assaut`, `delai_porteur` — 4 leviers sur 4.
- **Mesuré** : attendre le porteur donne +11 points de charges posées, **non établi** (p = 0,22).

### Phase 6 — Exfiltration
- **Vignette** : départ phase 6, arrêt à l'extraction ou à la perte du groupe (durée à mesurer).
- **Choix** : repli prudent ou rapide ; le bouchon tient jusqu'au bout ou décroche avec l'assaut ; extraction principale ou de secours ; continuer ou abandonner si des blessés ne marchent plus.
- **Variantes** : réserve absente, 1 ou 2 véhicules, distance et délai, blessés incapables de marcher, compromission.
- **Existe** : `exfil`, `tenir`, point d'extraction de secours dans l'ordre d'opération, comptage des hommes qui ne marchent plus.

## 3. Les niveaux du curriculum

| niveau | ce que l'agent affronte | fiche |
|---|---|---|
| 1 | un choix, une phase, une situation claire | complète |
| 2 | un choix, une phase, 10 variantes dont certaines où la bonne option **s'inverse** | complète |
| 3 | deux phases enchaînées (4→6, 5→6) | complète |
| 4 | trois phases (3→4→6 : voir la réserve, partager, tenir) | allégée |
| 5 | la mission complète **compressée** (poser à ~800 m) : ~30-40 min | allégée |
| 6 | **mondes jamais vus** — l'examen | aucune |

La fiche s'allège en montant : au début elle guide, à la fin l'agent doit savoir sans elle.

## 4. La fiche — exemple réel, avec ce qui est mesuré et ce qui ne l'est pas

```
POINT DE DECISION   combien d'hommes au bouchon ?
SITUATION           reserve detectee, 2 vehicules, ~1 km, alarme donnee il y a 2 min

OPTION A            3 au bouchon, 5 a l'assaut
  mesure            combat au bouchon dans 81 % des episodes (13/16) ; 18 hommes du bouchon tues sur 16
  effet sur l'issue non mesure

OPTION B            1 au bouchon, 7 a l'assaut
  mesure            non mesure
  attendu           plus de puissance a l'objectif ; le bouchon cede si le second vehicule combat
```

## 5. Les portes de validation dbt, dans l'ordre

Une vignette n'entre dans le curriculum qu'après les avoir franchies :

1. **Démarrage conforme** — l'état de départ est celui de la variante, et le monde n'a pas bougé.
2. **Choix exécuté** — l'option forcée est bien jouée.
3. **Conséquence avant l'arrêt** — l'effet du choix a le temps d'arriver.
4. **Durée** — médiane de 10 min au plus.
5. **Symétrie** — les options coûtent des choses différentes (sur papier d'abord, puis dans les traces).
6. **Observable vivant** — ce qui devrait décider n'est pas constant.
7. **Effet puis inversion** — le choix change l'issue, et la meilleure option change selon la situation.

Les portes 1 à 6 se passent en tournées de 10 min. La porte 7 demande ~200 épisodes, soit ~2 à 3 h de ferme par phase.
Un choix qui franchit 1 à 6 mais pas 7 reste comme **choix témoin**.

## 6. L'ordre de construction — du plus mesurable au plus fragile

| étape | quoi | pourquoi à ce rang | estimation |
|---|---|---|---|
| 0 | fondations | tout en dépend | 1 à 2 jours |
| 1 | **pilote phase 5** | déjà 8 min, 4 leviers existants | ½ journée + tournées |
| 2 | phase 6 | leviers existants, réserve rendue réelle le 16/09 | ½ à 1 jour |
| 3 | phase 4 | se teste dans la vignette de phase 6 | ½ jour |
| 4 | phase 2 | la règle de traversée existe, il faut du trafic | 1 jour |
| 5 | phase 3 | à réorienter vers la réserve | 1 jour |
| 6 | phase 1 | il faut d'abord créer une menace | 1 jour |
| 7 | niveaux 3 à 6 | enchaînements, mission compressée, mondes jamais vus | 2 à 3 jours |

À chaque niveau, cinq agents sont mesurés : **le script actuel** (la référence à battre), **le hasard** (le plancher),
**l'oracle** (le plafond : la meilleure option mesurée), puis **l'officier LLM avec sa fiche**, puis **une politique apprise**.

## 7. Les pièges, tous payés cette semaine

| piège | garde-fou |
|---|---|
| options interchangeables (la porte) | test de symétrie avant tout épisode |
| conséquence coupée (`arret=5`) | porte 3 |
| le monde bouge quand on déplace un élément (faute n°7) | test d'identité du monde |
| levier qui ne s'applique pas (`obs=0`, job copié une seule fois) | porte 2 |
| mondes cassés (mondes 7 et 11) | tests d'anomalie |
| mémorisation du site | mondes d'évaluation séparés par site |
| lire les résultats en cours de route | règle écrite dans le test dbt avant le lancement |
| **forcer 10 variantes là où la phase n'a pas de vrai choix** | la règle d'arrêt du cahier des charges, appliquée phase par phase |

## 8. Première étape proposée

Le **pilote phase 5**, de bout en bout, avant de toucher aux autres phases : ligne de décision et table dbt `decision`,
10 variantes, 2 choix (tactique, porteur), une tournée de 10 min, les portes 1 à 6, une première fiche, et les deux
premiers agents (script et hasard). S'il tourne proprement, on le réplique aux autres phases.
