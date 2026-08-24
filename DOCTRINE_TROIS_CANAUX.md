# LE MODE ERRE — et la doctrine à trois canaux qui rend le pipeline utilisable

**24/08/2026, soir.** Corrections exigées par Fable, mesurées, puis la doctrine qui en sort.

## ⛔ CORRECTION 1 — « bifurcation précoce » est RÉFUTÉ comme mécanisme

Fable exigeait de garder le verdict et de lâcher l'adjectif : aux itérations 100-250 les
deux lectures sont **au plancher** (échantillonnage 0,1 %), et *une divergence entre deux
zéros ne date rien*. Il proposait la sonde qui tranche — **l'accord d'argmax entre points**.

**Accord avec le mode final, sur 61 440 états d'une trajectoire de référence commune :**

| | it 100 | it 300 | it 700 |
|---|---|---|---|
| graine 0 | 29 % | 47 % | 60 % |
| **graine 1** | **12 %** | 38 % | 53 % |

> **Aucun mode n'est verrouillé tôt. Les deux ERRENT et ne convergent que tard.**
> La graine 1 ne partage que **12 %** de ses décisions avec son propre mode final.

**C'est la seconde structure de Fable** : un mode qui erre entre plusieurs mauvais **sans
jamais traverser un bon**. **La région des bons modes est petite**, voilà tout.

**Ce qui entre au registre**, et rien de plus : *à chaque instant où il y avait quelque
chose à lire, l'argmax de la graine 1 était déjà inutilisable* (max **7,9 %** sur 24
lectures), *pendant que la graine 0 tient de façon stable* (écart-type **2,0**).

⭐ **Cliquet : nommer un mécanisme qu'on n'a mesuré qu'en performance, c'est déposer une
hypothèse sous le costume d'un fait.**

## CORRECTION 2 — la précision qu'exigeait Fable

Les mesures d'argmax centré et du film ont tourné sur **`GRAINES_SELECT[201, 202, 203]`**,
et non sur les six. Le registre le dit maintenant.

## ⭐⭐⭐ LA DOCTRINE À TROIS CANAUX

Le danger nommé par Fable : *si chaque condition future se lit par « meilleure graine sur
SELECT, jugée sur TEST », toute comparaison A contre B devient une comparaison de MAXIMA de
tirages bruités.* Et pire : une intervention peut **améliorer la politique ET baisser le
rendement de condensation**, et paraîtrait alors une régression.

| canal | ce qu'il porte | comment il se lit |
|---|---|---|
| **SCIENTIFIQUE** — comparer des conditions | la lecture **échantillonnée**, **toutes graines publiées**, moyenne et dispersion | c'est le canal **reproductible** : graines 0 et 1 rendent **37,9 et 42,3 %** (4 points d'écart) là où l'argmax donne 3 et 50 |
| **SANTÉ** — surveiller la loterie | le **rendement de condensation** : x/k graines dont l'argmax passe 30 % sur SELECT | détecte les interventions qui **tuent la loterie** sans toucher au niveau échantillonné |
| **LIVRAISON** — le seul chiffre citable | l'artefact **choisi sur SELECT**, jugé sur **TEST, une fois** | c'est « la politique livrée », et rien d'autre |

**k = 4 graines** pour livrer (à p ≈ 1/2, ~94 % de chances d'avoir un candidat ; **6 h 40**,
une nuit). **k fixé d'avance et identique dans les deux bras** de toute comparaison.

⚠️ **Règle de résolution déclarée** : à k = 3-4 graines, **un effet sous 5-6 points est NON
RÉSOLU à ce budget**. On l'écrit tel quel, on ne le cite pas.

⚠️ **p = 1/2 sort d'un n = 2** : son intervalle couvre presque tout. Chaque expérience
future l'affine **gratuitement**, si le registre loge les trois canaux **par graine**.

## Les interdits, repris tels quels

1. **k ne devient jamais « autant qu'il faut pour qu'une passe »**. Un **0/k est un
   résultat** — le rendement a bougé — pas une invitation à relancer. *Contamination n°1,
   et elle s'installe silencieusement.*
2. **Jamais de comparaison de conditions sur le canal de LIVRAISON.**
3. **Ne pas brûler TEST** : une lecture par artefact livré, tout l'exploratoire sur SELECT.
   Si SELECT absorbe des dizaines de décisions au fil des mois, **le noter et le faire tourner** — TEST, jamais.

## ⚠️ UNE DÉCISION À PRENDRE AVANT DE ROUVRIR LE TRANSFERT

> **Quel objet part dans Arma — l'argmax ou l'échantillonné ?**

`banc_live.py` déploie en argmax **par héritage**, pas par choix. Si le pont peut tirer au
sort à chaque pas, **la condensation cesse d'être une porte pour tout le programme de
transfert**, et l'argmax redevient un luxe de reproductibilité pour le débogage.
**Cette décision conditionne ce que la recette doit livrer. Elle revient à Younes, et elle
se prend explicitement — pas par défaut, au fil de l'histoire du banc.**

## Le « pourquoi » : ABANDONNÉ, avec son déclencheur de réouverture

**Abandonné aujourd'hui.** Et mon protocole était mauvais : des points toutes les 5
itérations regarderaient **deux lectures au plancher diverger autour de zéro** — effet de
plancher, datation vide.

**Déclencheur de réouverture, écrit ici** : si le **rendement de condensation** varie
fortement avec une intervention (les postures qui le feraient passer de 1/2 à 1/5), la
question **regagne sa priorité sur des motifs applicatifs**, et le registre aura déjà les
données pour la poser.

**Le seul design qui déciderait**, si le jour vient : **engagement contre performance** —
sur k graines fraîches, mesurer **quand l'argmax atteint ~80 % d'accord avec son propre mode
final**, et si cet engagement **précède** la sortie du plancher de l'échantillonnage.

⭐ **Cliquet : écrire l'abandon avec son déclencheur, c'est la différence entre abandonner
et perdre.**

## Le bilan, tel que Fable le corrige — et il a raison

Mon « aucune réparation sur une cause supposée » était juste de compte, faux d'étiquette.
**Il y a eu trois réparations, toutes sur le BANC, aucune sur l'algorithme** : la lecture de
courbe arrêtée à 200 itérations · le `torch.save` dans le `if` qui jetait les pièces à
conviction · et la **couche de lecture** (argmax contre échantillonnage) devenue un choix
**explicite et pré-inscriptible**.

> **L'algorithme n'a jamais été en panne. Il lui fallait du budget, des graines, et un
> instrument qui dise la vérité.**

Et l'asymétrie qui est la vraie leçon transférable : **les huit hypothèses sont mortes sous
des mesures de quelques minutes, jamais sous un réentraînement.** Les runs chers ont été
rares, et chacun portait sa règle déposée d'avance.

> **La loterie n'est pas expliquée — elle est TARIFÉE.** Pour un programme d'ingénierie,
> c'est la bonne monnaie.
