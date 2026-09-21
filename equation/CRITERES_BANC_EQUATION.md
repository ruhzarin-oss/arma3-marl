# Critères pré-enregistrés — banc des algorithmes d'équation, sans Oracle

*17/09/2026, vers 10 h 45. Validé par Younes (« oui vas y lance les tests »), suite du plan
`plans/plan-architecte-oracle.md` (418b2e1). Écrit et commité avant tout calcul, code compris (`equation/`).
Une seule lecture par test, quand il est complet.*

## La question

Quel algorithme retrouve la formule qui dit **quand une option vaut mieux que l'autre** ? Il doit la retrouver quand
elle existe, et ne rien inventer quand elle n'existe pas.

## La quantité commune

Chaque algorithme apprend sur la pseudo-issue

```
ψ = 2 · Y · (2a − 1)
```

L'option est tirée à pile ou face (p = 1/2), donc E[ψ | x] = P(Y = 1 | x, a = 1) − P(Y = 1 | x, a = 0) = τ(x). La formule
apprise pour ψ est la formule de l'avantage, et la règle est « option 1 si la formule est > 0 ».
Exception : la logistique L1 apprend directement logit P(Y) = α + β·x + a·(γ₀ + γ·x), et sa règle est γ₀ + γ·x > 0.

## Les algorithmes, réglages fixés d'avance

| algo | réglages |
|---|---|
| `l1` | `LogisticRegressionCV`, 10 valeurs de C, 5 plis, liblinear, perte logarithmique ; variables standardisées |
| `arbre` | arbre de régression sur ψ, profondeur 0 (constante) à 3 choisie par validation croisée à 5 plis, feuilles d'au moins max(20, n/20) épisodes |
| `gplearn` | population 500, 15 générations, tournoi 20, fonctions add, sub, mul, min, max, neg, gt (x > y), constantes dans [−1, 1], parcimonie 0,001 par nœud, 1 thread |

PySR et Deep Symbolic Regression sont plus lourds. Ils passeront **après la fin des campagnes P3 et P6**, avec les mêmes
critères, pour ne pas charger la ferme pendant des épisodes Arma.

Charge pendant les calculs : au plus 2 processus sur 24 threads, avec `OMP_NUM_THREADS=1`.

## Test A — synthétique, vérité connue

**Situations tirées (8 perceptions)**

| perception | loi |
|---|---|
| distance (km) | uniforme [0,1 ; 0,9] |
| moment | uniforme [0 ; 1] |
| alarme | Bernoulli(0,5) |
| vehicule_vu | Bernoulli(0,4) |
| defenseurs_connus | Poisson(3), bornée à [0 ; 8] |
| leurre_uniforme | uniforme [0 ; 1] |
| leurre_binaire | Bernoulli(0,5) |
| leurre_distance | corrélé à la distance (r = 0,7) |

**Niveau de réussite** de l'option 0, en logit :

```
− 0,15·(defenseurs_connus − 3) − 0,2·alarme + 0,2·(distance − 0,5)
```

`defenseurs_connus` agit sur le niveau mais jamais sur l'avantage : c'est un leurre plus subtil.

**Avantage caché de l'option 1** (g, en logit ; la bonne règle est g > 0)

| formule | g(x) | forme |
|---|---|---|
| F0 | 0 | aucune formule : contrôle nul |
| F1 | 10·(0,5 − distance) + 3·(vehicule_vu − 0,4), bornée à ±3 | linéaire |
| F2 | +3 si (distance − 0,5)·(moment − 0,5) > 0, sinon −3 | signe d'un produit, frontière en croix |
| F3 | +3 si alarme = 1 et distance < 0,7, sinon −3 | seuil sur deux variables |

**Calibrage fait avant le banc, sur le générateur seul** (`equation/calibrer.py`, sans aucun algorithme). La fumée,
tirée sur des graines disjointes, a montré qu'avec les premiers effets (±1 à ±2 logits), **même la bonne règle** n'était
déclarée que 9 % (F2) à 80 % (F3) du temps à n = 500 : le banc n'aurait rien départagé. Les effets ont donc été
renforcés à ±3 logits. La bonne règle est maintenant déclarée à n = 500 dans 98,9 % (F1), 100 % (F2) et 97,3 % (F3)
des tirages. Ces effets sont **plus forts** que ceux mesurés dans Arma (9 à 37 points) : un algorithme qui échoue ici
échouera dans Arma, pas l'inverse.

**Plan** : chaque algorithme × chaque formule × n ∈ {200, 500, 1000} × 20 répétitions. Les graines sont identiques
entre algorithmes, donc tous voient les mêmes données.

**Déclaration d'une formule**, sans regarder la vérité :

```
dᵢ = 2·Yᵢ·( 1{aᵢ = r(xᵢ)} − 1{aᵢ = c} )        r et c appris sans le pli de i (5 plis)
G = moyenne(d),  se = écart-type(d)/√n,  formule déclarée si  G − 2,326·se > 0
```

c est la meilleure option fixe sur les autres plis. Le seuil α = 1 % unilatéral est choisi pour que le contrôle nul
puisse tenir « au plus 1 sur 20 ». Avec α = 5 %, un algorithme parfaitement honnête dépasserait 1 fausse sur 20 dans
26 % des cas.

**Formule retrouvée** = déclarée, et accord ≥ 0,80 entre la règle apprise sur tout l'échantillon et la bonne règle, sur
20 000 situations neuves où |g| ≥ 0,5.

**Critère (RETENU)**
- F1, F2 et F3 retrouvées chacune au moins 18 fois sur 20 à n = 500 ;
- F0 déclarée au plus 1 fois sur 20, à chaque n.

**Descriptif, sans décision** : n = 200 et 1000, vraies variables trouvées, leurres pris, `defenseurs_connus` pris,
gain vrai de la règle contre gain idéal, durée.

**Attendu écrit avant** : la logistique L1 ne peut pas représenter la croix de F2. Elle devrait échouer F2.

## Test B — les vrais épisodes Arma

**Données** : épisodes acceptés, sans erreur SQF, des campagnes **déjà lues** avec leurs propres critères :
CHOIX-P1-17-09, CHOIX-P2-17-09, CHOIX-P4-17-09 et PILOTE-P5-DELAI-SITUATION-16-09. P3 et P6 s'ajoutent seulement
après leur lecture.
- Issue Y : l'issue primaire pré-enregistrée de chaque choix.
- a = 1 pour la seconde option.

**Perceptions permises** : ce que la ligne de décision écrit au moment du choix, soit alarme, depuis_alarme, compromis,
vivants et defenseurs_connus. S'y ajoutent vehicule_vu (P2), reco_vivants (P3) et distance_point (P6).
**Interdits** : bras, niveau de menace, verite_defenseurs, graine.

**Constat avant lecture**, sur les perceptions seulement, pas sur les issues :
- P2 : seul vehicule_vu varie (8 épisodes sur 128) ; la décision est prise au début de la phase.
- P4 : rien ne varie.
- P1 : presque rien ne varie.
- Pilote P5 : l'alarme varie (la moitié des épisodes).

Au moment du choix, le détachement ne perçoit donc presque rien de la menace. Le test B est surtout un contrôle nul
sur données réelles.

**Méthode**
- Plis = les 8 mondes (un monde laissé de côté à chaque fois).
- G comme au test A ; IC par 10 000 rééchantillonnages des mondes (graine 20260917).
- Gain déclaré si le percentile 1 % est > 0.

**Attendu écrit avant** : aucun gain déclaré. Un gain déclaré ne sera pas cru avant d'avoir vérifié la fuite de
perception et l'effet d'un seul monde.

## Amendement 1 — ajout d'EvoGP (17/09, vers 11 h 30, avant tout calcul EvoGP)

Younes a demandé d'essayer EvoGP (« essaye celui-là », puis « lance evogp dès que c'est installé »). Les résultats du
test A pour L1 et l'arbre sont calculés mais **pas lus** (lecture unique à la fin du test A). Le test B est lu
(3f0547c), sans gain.

| algo | réglages |
|---|---|
| `evogp` | EvoGP 0.1.0 (EMI-Group), GPU RTX 3090 ; population 5000, 50 générations, arbres de 32 nœuds au plus, profondeur initiale 5 ; fonctions +, −, ×, min, max, neg, > ; constantes {−1 ; −0,5 ; −0,25 ; 0 ; 0,25 ; 0,5 ; 1} ; mutation 0,2, survie 0,3, élite 1 % ; fitness = −MSE sur ψ − 0,001 × nombre de nœuds (même parcimonie que gplearn) ; règle = formule > 0 |

- **Environnement séparé** : `/mnt/data/hmt/evogp/env`, avec Python 3.12, torch 2.7.1+cu126, CUDA 12.6 et gcc 13, installé sans droits administrateur.
- **Graines** : torch et CUDA sont fixées par la graine du banc, mais les noyaux CUDA ne sont pas garantis déterministes.
- **Critères** : les mêmes, test A (RETENU si F1, F2 et F3 ≥ 18/20 à n = 500 et F0 ≤ 1/20) et test B (même méthode).
- **Fumée** : sur graines décalées, pour la durée et le bon fonctionnement seulement.
- **Variante `evogp_p01`**, déclarée avant tout calcul : mêmes réglages, mais parcimonie 0,01 par nœud (10 fois plus
  forte). Raison : EvoGP explore environ 30 fois plus de formules que gplearn (5000 × 50 contre 500 × 15), donc il a
  plus d'occasions d'apprendre le bruit. La fumée (graines décalées, une répétition) a montré des formules longues
  qui prennent des leurres. Les deux variantes sont jugées chacune sur les mêmes critères.
- **Correctif de fumée** : le texte de la formule vient de `to_infix`, car `to_sympy_expr` d'EvoGP refuse un « > » dans un produit.

## Amendement 2 — ajout de PySR et de DSR (21/09/2026, vers 11 h 30, avant tout calcul PySR ou DSR)

Younes : « ajoute PySR et DSR au banc synthétique et lance le test, go ». Le banc annonçait ces deux algorithmes « après la fin des
campagnes P3 et P6 » ; ils n'avaient jamais été installés ni joués (vérifié dans le dépôt le 21/09). Les résultats du test A pour les cinq
premiers algorithmes sont déjà lus (verdict d2d4807) ; rien n'en est retouché.

| algo | réglages |
|---|---|
| `pysr` | PySR 2.5.0 (SymbolicRegression.jl), **CPU, 1 thread**, mode série déterministe ; fonctions +, −, ×, min, max, neg, > (`greater`) ; 30 itérations, 8 populations de 30, 300 cycles par itération, taille 25 au plus, parcimonie 0,001, perte quadratique sur ψ, sélection `best` ; graine = graine du banc |
| `dsr` | Deep Symbolic Optimization (dso-org, master du 21/09), **CPU, 1 thread**, TensorFlow 1.14 ; réseau récurrent + gradient de politique à risque (ε = 0,05, réglages par défaut) ; jetons add, sub, mul, neg et **trois jetons ajoutés** min2, max2, gt2 (x > y) ; constantes fixes {−1 ; −0,5 ; −0,25 ; 0,25 ; 0,5 ; 1}, pas de jeton `const` ; 25 jetons au plus ; **20 000 expressions** par lots de 500 ; graine = graine du banc |
| `dsr_100k` | variante déclarée avant tout calcul : mêmes réglages, **100 000 expressions**. Jouée **à n = 500 seulement** : elle ne peut donc pas être « RETENUE » (le critère demande F0 à chaque n) ; elle dit seulement si le budget change le résultat de `dsr` |

- **Pourquoi des jetons ajoutés à DSR** : dans le code de DSO, `min` et `max` sont déclarés d'arité 1 (défaut amont, inutilisables) et il
  n'existe aucun jeton de comparaison. Sans eux DSR n'aurait pas le jeu de fonctions des autres algorithmes.
- **Budgets fixés par parité de coût, pas par résultat** : la fumée (graines décalées, F1 et F2, n = 500, une répétition) n'a servi qu'à la
  durée et au bon fonctionnement : PySR 26 s par essai (plus ~95 s de compilation Julia, une fois par processus), DSR 61 à 66 s, à comparer
  aux 43 s de gplearn. Les réglages ci-dessus étaient écrits avant la fumée et n'ont pas été retouchés après.
- **Environnements séparés**, sans droits administrateur : `/mnt/data/hmt/pysr/env` (Python 3.12, Julia tiré par juliapkg) et
  `/mnt/data/hmt/dsr/env` (Python 3.7, TensorFlow 1.14, numpy 1.19.5, numba 0.53.1). Correctif d'installation de DSR : le Python 3.7 de
  conda passe `--sysroot=/` à l'éditeur de liens, qui cherche `/lib64/libc.so.6`, absent d'Ubuntu ; `LDSHARED` est redéfini sans ce sysroot.
- **Charge** : la règle du banc, **2 processus à 1 thread**, en priorité basse (`nice 19`). Processus 1 : `pysr` (240 essais, ~1 h 45) puis
  `dsr_100k` à n = 500 (80 essais, ~7 h). Processus 2 : `dsr` (240 essais, ~4 h). Aucun GPU. Rien n'est écrit dans `bancs/`, `outils/` ni la file.
- **Critères** : les mêmes (RETENU si F1, F2 et F3 retrouvées ≥ 18/20 à n = 500 et F0 déclarée ≤ 1/20 à chaque n). Lecture unique par
  `lire_banc.py`, quand les 240 essais d'un algorithme sont écrits. Le test B (Arma) n'est pas rejoué : il n'a montré de gain pour aucun
  algorithme, faute de perception qui varie.
- **Prédiction écrite avant** : `pysr` fait au moins aussi bien qu'`evogp` à n = 500 avec des formules plus courtes et moins de leurres ;
  `dsr` à 20 000 expressions ne retrouve pas F2 et F3 18 fois sur 20 (budget trop court pour un gradient de politique) ; `dsr_100k` fait
  mieux que `dsr` sans atteindre 18/20. Toute prédiction fausse est rapportée telle quelle.

## Amendement 3 — PySR : un plantage de l'export sympy, et sa réparation (21/09/2026, vers 13 h 10, AVANT toute lecture de `pysr`)

`pysr` s'est arrêté au 132ᵉ essai (F2, n = 200, répétition 11) sur `KeyError: 'pop from an empty set'`, levée par **sympy** pendant l'export
de la table des formules (`pysr2sympy` → `parse_expr(evaluate=False)`), sur une expression imbriquée de `min`, `max` et `greater`. La
recherche de PySR était terminée ; c'est la mise en forme qui a fait tomber l'ajustement. Aucun résultat de `pysr` n'a été lu.

- **Réparation, sans toucher à la recherche, à la perte, au score ni à la sélection** (qui ne passent pas par sympy) :
  1. l'export sympy devient tolérant : en cas d'échec, la colonne reçoit un symbole neutre au lieu de lever une exception ;
  2. la règle ne prédit plus par `model.predict` (qui passe par la forme sympy) mais par un **évaluateur direct de la chaîne de la formule**
     (`min`, `max`, `neg`, `greater`, +, −, ×), donc aussi pour une formule que sympy ne sait pas relire.
- **Contrôle d'équivalence, joué avant de reprendre** (`controle_equivalence.py`, graines décalées, F1, F2, F3 à n = 500) : sur les
  **36 formules** des trois fronts, `model.predict` et l'évaluateur direct donnent un écart maximal de **6,7·10⁻¹⁶** et **0 désaccord de
  règle sur 720 000 prédictions**. Les 131 essais déjà écrits (chemin `model.predict`) et les suivants (évaluateur direct) mesurent donc la
  même chose ; ils sont gardés, le banc reprend au 132ᵉ (il est reprenable par construction).
- **Charge** : pour rester à 2 processus, `dsr_100k`, qui avait démarré à la place de `pysr` (15 essais écrits), est arrêté et reprendra
  après `pysr`, sans rien recalculer.
- Critères, réglages et prédictions de l'amendement 2 : inchangés.

## Lecture de l'amendement 2 — PySR et DSR (21/09/2026, lectures uniques : `pysr` à 14 h 45, `dsr` à 19 h 00)

240 essais chacun, 0 plantage après l'amendement 3, mêmes critères, même lecteur (`lire_banc.py`). Sorties complètes :
`equation/resultats/lecture_synthetique_pysr.txt` et `lecture_synthetique_dsr.txt`.

| retrouvée à n = 500 (critère ≥ 18/20) | F1 | F2 | F3 | F0 déclarée (≤ 1/20 à chaque n) | verdict |
|---|---|---|---|---|---|
| `pysr` | 12/20 | **0/20** | 13/20 | 1, 0, 0 | **NON RETENU** |
| `dsr` (20 000 expressions) | 12/20 | **0/20** | 15/20 | 1, 0, 0 | **NON RETENU** |
| rappel `evogp` | 14/20 | 7/20 | 15/20 | 0 partout | non retenu |
| rappel `l1` | 19/20 | 0/20 | 19/20 | 0 partout | non retenu |

À n = 1000 : `pysr` 18 / **1** / 20 ; `dsr` 17 / **0** / 20 ; `evogp` 19 / 19 / 20. **La croix F2 (distance × moment) n'est retrouvée que par
EvoGP.** Leurres par formule à n = 500 : `pysr` 0,05 à 0,65, `dsr` 0,65 à 1,10, `evogp` 1,25 à 1,35. Durée par essai : `pysr` ~23 s,
`dsr` ~55 à 85 s (CPU, 1 thread), `evogp` ~2 s (GPU).

**Sort des prédictions écrites avant** : « `pysr` fait au moins aussi bien qu'`evogp` à n = 500 » — **FAUSSE** sur le score (moins bien sur
les trois formules, et F2 jamais) ; « avec des formules plus courtes et moins de leurres » — tenue (`0.596 − distance`, `alarme − distance`).
« `dsr` à 20 000 expressions ne retrouve pas F2 et F3 18 fois sur 20 » — tenue ; ses formules sont longues et prennent des leurres.
`dsr_100k` (n = 500, descriptif) : lu à part quand ses 80 essais sont écrits.

**Ce que ça dit** : à coût comparable, ni PySR ni DSR ne trouvent une interaction entre deux variables ; PySR est sobre et ne ment pas
(aucune fausse règle, presque aucun leurre) mais il est aveugle à la croix. Pour chercher une règle de décision où deux perceptions se
croisent, EvoGP sur GPU reste l'outil, à n ≥ 1000. L'indice de fumée « PySR retrouve F2 » était une répétition chanceuse : une fumée ne
compte jamais comme un résultat.
