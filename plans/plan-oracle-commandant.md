# Plan — l'Oracle commandant : un adversaire qui cherche

*19/09/2026. Demandé par Younes après la lecture de P2 : « il n'y a pas de vrai script en face contre nous, donc pas
de vrai choix à apprendre ». Prolonge `plans/plan-architecte-oracle.md` (17/09) sans le contredire. **Aucune ligne de
code avant validation.***

## 0. Pourquoi, et ce qui est mesuré

| mesure | source | ce qu'elle dit |
|---|---|---|
| le détachement n'est **jamais détecté** dans 92 % des épisodes | CHOIX-P2-TYPES-19-09, 120 épisodes | l'ennemi ne cherche pas |
| `phase_discrete` réussit dans 85 % | même campagne | rien ne punit |
| attendre 20 min ne change pas les charges posées (0,688 partout) | PRIX-DU-TEMPS-V2, 48 épisodes | le temps est gratuit |
| aucun des 6 choix ne dépend de la situation | six campagnes, 16 au 18/09 | il n'y a pas de situation |

Ces quatre lignes disent la même chose. **Un choix n'existe que s'il y a quelqu'un en face pour le faire payer.**
L'adversaire d'aujourd'hui est un décor : une garnison statique, une patrouille qui fait la navette entre deux points
fixes, une réserve qui dort à 6 km. Il ne cherche pas, ne raisonne pas, ne se trompe pas.

## 1. Deux Oracles, deux moments

- **L'Oracle concepteur** (déjà écrit, § 4 du plan du 17/09) choisit θ **avant** l'épisode : type de menace, distance,
  moment, monde. Il cherche la faille de la règle de l'Architecte.
- **L'Oracle commandant** (ce plan) joue θ **pendant** l'épisode : il commande le camp est comme un chef le ferait,
  avec une image incomplète et un budget fini.

Les deux se composent : le concepteur fixe le décor et les moyens, le commandant les emploie. Un seul jeu de
paramètres θ_O les décrit, et c'est lui que le duel fait varier.

## 2. Ce que le commandant a le droit de savoir

C'est la règle la plus importante du plan. Un adversaire omniscient ne fabrique pas des situations, il fabrique un
mur — et un mur n'apprend rien à personne.

Le commandant ne lit **que** ces canaux, tous déjà présents dans le moteur :

```
z_t = (  D_t   détections propres au camp est : targetKnowledge des groupes est ( champ 0 ),
         S_t   bruits : tirs entendus, moteur, explosion, avec leur azimut et leur instant,
         T_t   traces : un mort trouvé, un véhicule détruit, une charge découverte,
         A_t   son propre état : alarme, pertes, unités qui ne répondent plus,
         t     le temps écoulé depuis le début de la mission )
```

Interdits, et vérifiés par un contrôle (§ 7) : la position réelle du détachement, `CHACAL_FS`, la vérité `θ`, et tout
appel à `reveal`. **L'Oracle concepteur voit θ ; le commandant ne le voit pas.** C'est la même discipline que pour
l'Architecte, qui ne voit que x.

## 3. La croyance : où est le détachement ?

Le terrain utile est découpé en un petit nombre de **cases** c (une douzaine suffit) : la zone de poser, les deux
axes vers la route, le point de traversée, la crête, les abords du site, l'axe d'exfiltration. Le commandant tient
une loi de probabilité b_t sur ces cases.

**Mise à jour, en deux temps.** D'abord la marche du détachement, ensuite l'observation :

```
prédiction   b̄_t(c)   =  Σ_{c'} P(c | c')  b_{t-1}(c')
correction   b_t(c)    ∝  L( z_t | c )  ·  b̄_t(c)
```

- `P(c | c')` est le **modèle de marche** : un détachement d'infanterie va vers l'objectif à 1,0–1,4 m/s, par les
  couverts. On le pose une fois, à la main, à partir des trajets déjà mesurés — pas appris.
- `L(z_t | c)` est la **vraisemblance**. Son ingrédient central est la probabilité de détecter à distance d, que nous
  avons **mesurée** cette nuit :

```
p_d( d, posture, nuit )  ≈   0,9   si d < 125 m et la cible est accroupie
                             0,9   si d < 250 m et la cible est debout et DESIGNEE
                             faible et lente au-delà, nulle au-delà de 450 m de nuit
```

- **L'information négative compte autant que la positive.** Si un poste regarde la case c pendant Δt et ne voit rien,
  alors `L(rien | c) = 1 − p_d(d_c)` et la probabilité de c **baisse**. C'est ce qui fait chercher un adversaire :
  il élimine, puis il se déplace vers ce qui reste.

## 4. Ce que le commandant peut faire, et ce que ça lui coûte

Un budget fini est ce qui empêche le mur. Le commandant dispose de B points par épisode (B est un paramètre, § 6) :

| action | délai | coût | effet |
|---|---|---|---|
| réorienter un poste (secteur de regard) | 10 s | 0 | change `p_d` sur une case |
| déplacer la patrouille de route vers une case | 60–180 s | 1 | déplace une détection mobile |
| envoyer une patrouille à pied fouiller une case | 120–300 s | 2 | détection sur place, puis elle reste |
| poser un guetteur sur un axe | 60 s | 1 | surveillance durable d'une case |
| réveiller une fraction de la réserve | 300 s+ | 3 | pression tardive, coûteuse |
| tendre une embuscade sur l'axe d'exfiltration | 240 s | 3 | frappe la phase 6 |

Chaque action est **journalisée** comme nos décisions à nous : `CHACAL|O|decision|t|action|case|croyance|budget`.
Sans cette ligne, l'Oracle est invérifiable, donc inutilisable.

## 5. Comment il décide

Une règle gloutonne à un coup, lisible et jouable en SQF :

```
choisir l'action u qui maximise   G(u) = Σ_c b_t(c) · Δp_intercept( u, c )  −  λ · coût(u)
```

`Δp_intercept(u, c)` est le gain de probabilité d'intercepter si le détachement est en c, sur un horizon H (par
exemple 300 s). λ règle l'avarice. Pas d'apprentissage ici : on veut un adversaire **compétent et explicable**, pas
un second agent à entraîner. Ce qui s'apprend, c'est la règle de l'Architecte ; l'Oracle est l'épreuve.

## 6. Le niveau, et les paramètres du duel

```
θ_O = ( B budget, λ avarice, H horizon, δ période de décision, ν bruit de croyance, ε taux d'erreur volontaire )
```

- **ν** floute la croyance : un vrai chef se trompe. Sans ν, l'Oracle converge trop vite et redevient un mur.
- **ε** lui fait parfois choisir la deuxième meilleure action. C'est ce qui rend la situation **variée** plutôt que
  déterministe — et la variance est ce qui nous manque depuis trois jours.
- Niveaux livrés : **0** décor actuel (témoin, comparable aux campagnes d'août et septembre), **1** réorientation et
  patrouille de route seulement, **2** plus la fouille à pied, **3** plus la réserve et l'embuscade.

Le duel du 17/09 s'applique tel quel : θ_O est tiré par poids exponentiels avec part uniforme η, proportionnellement
au regret estimé ρ̂ₖ de la règle courante. L'Oracle ne gagne rien sur les mondes injouables ni sur les mondes faciles.

## 7. Contrôles — l'Oracle doit pouvoir échouer (règle 16)

Aucune campagne ne part avant que les cinq passent. Ils sont écrits avant le premier épisode.

1. **Positif** : détachement qui traverse à découvert à 100 m d'un poste, de jour. Interception ≥ 90 % des épisodes.
   Si l'Oracle ne trouve pas ça, il ne trouvera rien.
2. **Négatif** : aucun détachement dans le monde. L'Oracle ne déclenche jamais l'alarme et ne dépense aucun point.
3. **Non-triche** : on téléporte le détachement d'une case à l'autre en cours d'épisode. La croyance **ne doit pas**
   suivre avant une détection légitime. C'est le contrôle qui prouve qu'il ne lit pas nos positions.
4. **Jouabilité** : au niveau retenu, la réussite de mission reste dans la bande **20–80 %**. En dessous c'est un mur,
   au-dessus c'est du décor. Mesuré sur 24 épisodes avant toute campagne.
5. **Bascule** : il existe au moins un couple (choix, perception observable) où la meilleure option **change de
   signe** entre deux états. Sans ça, l'Oracle a rendu le monde dur, pas décidable — et c'est décidable qu'on veut.

## 8. Ce que ça doit produire pour la science

La première bascule visée est la plus simple, et elle est déjà à portée : la patrouille de route a une **phase**
observable — le temps qu'il lui reste avant d'arriver au point de traversée.

```
x = temps estimé avant passage de la patrouille   ( canal géométrique, lisible par le détachement )
si x est petit   → traverser tout de suite est mauvais, attendre est bon
si x est grand   → attendre est mauvais ( on reste exposé ), traverser est bon
```

C'est exactement la forme `signe(τ(x))` qui change, que six campagnes n'ont pas trouvée. Le commandant la rend
possible parce qu'il **déplace** la patrouille vers là où il croit que nous sommes, au lieu de tourner en rond.

## 9. Coût et ordre

| étape | durée | serveurs |
|---|---|---|
| croyance, cases et journal `CHACAL|O|decision`, sans action | 1 j | 0 |
| les trois premières actions et le budget | 1 j | 0 |
| les cinq contrôles (§ 7) | 4 h | 12 |
| calibrage du niveau sur la bande 20–80 % | 4 h | 12 |
| campagne de bascule sur P2, 128 épisodes | 1 nuit | 12 |

## 10. Falsificateur du plan entier

« Si, avec un adversaire qui cherche, réagit et dépense un budget, **aucun** des six choix ne devient dépendant de la
situation, alors la dépendance ne vient pas de l'adversaire. Il faudra la chercher ailleurs — dans le terrain, dans
l'effectif, ou admettre que cette mission n'a pas de décision à apprendre. »

## Décisions pour Younes

1. **Le niveau de départ** : 1 (patrouille mobile seule) ou 2 (avec fouille à pied) ?
2. **Le budget B et l'avarice λ** : je propose de les calibrer par le contrôle 4 plutôt que de les fixer à la main.
3. **La comparabilité** : le niveau 0 reste le décor actuel, donc toutes les mesures d'août et septembre restent
   comparables au témoin. Confirmes-tu qu'on garde ce témoin dans chaque campagne ?
