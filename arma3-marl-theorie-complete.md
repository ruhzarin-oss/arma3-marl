# Algorithmes comportementaux pour agents de combat — corpus théorique complet

**Cadre du projet.** Former, dans Arma 3, une équipe de 4 agents (1 chef + 3 spécialistes à
capacités fixes, tâches assignées dynamiquement) capable d'opérer une mission de combat
coopérative. Objectif : **maximiser le succès de mission sous contrainte de pertes d'équipe**
(formulation CMDP). Mission compositionnelle (sous-objectifs multiples). Niveau : expert.
Approche : théorie en profondeur. Implémentation cible : Python.

Modèle formel global : **Dec-POMDP coopératif, sous contrainte, hiérarchique**, résolu en
paradigme CTDE (*Centralized Training, Decentralized Execution*).

---

## Table des matières

- Module 0 — Formalisation et complexité
- Module 1 — Décomposition de valeur et principe IGM
- Module 2 — Policy gradient multi-agents et assignation de crédit
- Module 3 — Théorie des rôles
- Module 4 — RL hiérarchique (le chef comme manager)
- Module 5 — Observabilité partielle, mémoire et communication
- Module 6 — Récompense : éparse, shaping, CMDP, curriculum
- Module 7 — L'interface Arma 3 comme décision de modélisation
- Synthèse — l'architecture intégrée
- Frontières et problèmes ouverts
- Bibliographie pivot

---

## Module 0 — Formalisation et complexité

**Dec-POMDP** : ⟨I, S, {Aᵢ}, T, R, {Ωᵢ}, O, h, γ⟩. État global caché S ; chaque agent agit sur
son historique observation-action τᵢ ; récompense d'équipe R(s,**a**) ; dynamique T = Arma 3
(échantillonnée, non écrite).

**Variante sous contrainte (CMDP)** : on ajoute un signal de coût C (pertes) et la contrainte
𝔼[Σ γᵗ C] ≤ c. Objectif : maxₚ 𝔼[Σ γᵗ R] s.c. 𝔼[Σ γᵗ C] ≤ c.

**POSG vs Dec-POMDP** : récompense d'équipe unique → Dec-POMDP. Récompenses hétérogènes par
agent → POSG. Décision retenue : **récompense d'équipe** (survie d'équipe incluse), donc
Dec-POMDP sous contrainte. La spécialisation viendra de la structure (rôles/hiérarchie), pas
de récompenses individuelles.

**Mur de complexité** (Bernstein et al. 2002) :

| Modèle | Résolution optimale |
|---|---|
| MDP | P |
| POMDP | PSPACE-complet |
| Dec-POMDP (n ≥ 2) | **NEXP-complet** |

Conséquence structurante : l'optimum exact est **prouvablement intraitable**. Tout le MARL
coopératif = méthodes approchées exploitant une **structure** (factorisation de valeur, rôles,
hiérarchie, communication). Les rôles ne sont pas un confort de design : ce sont une structure
qui réduit la complexité effective.

**Deux difficultés fondatrices** :
1. **Non-stationnarité** — du point de vue d'un agent, les autres apprennent, l'environnement
   perçu viole Markov → les garanties du RL mono-agent tombent.
2. **Assignation de crédit** — récompense d'équipe → qui a contribué ? Signal de gradient
   noyé sans traitement explicite.

**CTDE** : à l'entraînement on utilise un oracle (état global s, actions de tous) ; à
l'exécution chaque agent n'utilise que πᵢ(·|τᵢ). C'est le compromis qui réconcilie
efficacité d'apprentissage et décentralisation réaliste.

---

## Module 1 — Décomposition de valeur et principe IGM

**Problème** : apprendre des composants Qᵢ décentralisés cohérents avec une valeur d'équipe.

**Principe IGM** (*Individual-Global-Max*, Son et al. 2019) — condition de cohérence centrale :

  argmax_**a** Q_tot(τ,**a**) = ( argmax_{a₁} Q₁(τ₁,a₁), …, argmax_{aₙ} Qₙ(τₙ,aₙ) )

Si IGM tient, l'argmax local de chaque agent reconstitue l'optimum joint → décentralisation
cohérente. Tout l'enjeu : construire Q_tot à partir des {Qᵢ} de sorte qu'IGM soit garanti.

**Hiérarchie d'expressivité** :
- **VDN** (Sunehag 2018) — additivité : Q_tot = Σ Qᵢ. Suffisant pour IGM, mais aucune
  interaction représentable.
- **QMIX** (Rashid 2018) — monotonicité : Q_tot = f_mix(Q₁,…,Qₙ ; s) avec ∂Q_tot/∂Qᵢ ≥ 0.
  Implémentation : réseau de mélange à poids ≥ 0 produits par un **hyperréseau** conditionné
  sur s. Subtilité : s entre par l'hyperréseau, pas dans la combinaison monotone → Q_tot riche
  en s tout en préservant IGM.
- **Limite de QMIX** : ne représente que les Q_tot **monotones** en les Qᵢ. Les jeux à payoff
  **non-monotone** (coordination tout-ou-rien) sont hors d'atteinte. Contre-exemple matriciel
  type : optimum (A,A)=8 entouré de pénalités −12. **Pertinence combat** : un débordement
  réussi est excellent ; un voltigeur isolé sans base de feu est pire que tenir → tactiques
  génériquement non-monotones → QMIX seul insuffisant.
- **QTRAN** (Son 2019), **QPLEX** (Wang 2021), **Weighted QMIX** (Rashid 2020) — visent la
  classe IGM complète. QPLEX (architecture duplex dueling) représente toute la classe en
  restant entraînable.

**Extension CMDP** : deux critiques — retour Q_tot^R et coût Q_tot^C — chacun décomposable.
Couplage lagrangien : ℒ(π,λ) = Q^R − λ(Q^C − c), λ ≥ 0, résolu par montée-descente duale.
λ = « prix du risque » auto-réglé : pertes > seuil → λ ↑ → politique plus prudente. Base du
safe MARL (MAPPO-Lagrangian, MACPO).

---

## Module 2 — Policy gradient multi-agents et assignation de crédit

**Théorème du gradient de politique multi-agents** : pour des acteurs décentralisés
πᵢ(aᵢ|τᵢ ; θᵢ) et un **critique centralisé** Q(s, a₁,…,aₙ),

  ∇_{θᵢ} J = 𝔼[ ∇_{θᵢ} log πᵢ(aᵢ|τᵢ) · Aᵢ(s, **a**) ]

où Aᵢ est un avantage. Le critique centralisé voit tout (oracle CTDE), résolvant en partie la
non-stationnarité ; les acteurs restent décentralisés.

**MADDPG** (Lowe 2017) — gradient de politique déterministe ; un critique centralisé par agent
Qᵢ(s, a₁,…,aₙ). Actions continues, gère coopératif/compétitif. Faiblesse : variance et passage
à l'échelle en n.

**COMA** (Foerster 2018) — *la* réponse théorique à l'assignation de crédit. Avantage
**contrefactuel** :

  Aᵢ(s,**a**) = Q(s,**a**) − Σ_{aᵢ'} πᵢ(aᵢ'|τᵢ) Q(s, (**a₋ᵢ**, aᵢ'))

On marginalise l'action de l'agent i en gardant celles des autres fixes → on mesure la
contribution **propre** de i. C'est une **récompense de différence** (Wolpert & Tumer, WLU /
Aristocrat Utility) approximée par un critique appris. Élimine le bruit du crédit d'équipe.

**MAPPO** (Yu 2021) — PPO multi-agents à fonction de valeur centralisée V(s) (ou par agent),
partage de paramètres, GAE, clipping, value normalization. Le cheval de bataille empirique du
MARL coopératif : robuste, simple, fort. Recommandé comme backbone.

**Crédit formel** : récompense de différence Dᵢ = G(z) − G(z₋ᵢ) (utilité « Wonderful Life »).
COMA en est l'approximation neuronale ; la décomposition de valeur (Module 1) en est l'analogue
côté valeur.

**Variante sous contrainte** : MAPPO-Lagrangian, **MACPO** (Gu et al. 2021), région de confiance
pour la sécurité. Deux critiques (retour + coût) + λ appris, comme au Module 1.

**Pourquoi PG pour ce projet** : (1) pas besoin d'IGM (politiques explicites, pas d'argmax) →
la limite de monotonicité disparaît ; (2) gère nativement l'hétérogénéité (capacités fixes) et
les actions structurées ; (3) s'intègre proprement à la hiérarchie et au lagrangien.

---

## Module 3 — Théorie des rôles

**Trois formalisations du « rôle »** :
1. **Rôle = restriction d'espace d'action** (RODE, Wang 2021). On partitionne l'espace d'action
   joint en sous-ensembles (regroupés par effet sur l'environnement) ; un **sélecteur de rôle**
   assigne les rôles à échelle grossière ; les politiques de rôle opèrent sur des sous-espaces
   restreints. Réduit l'espace de recherche effectif. Naturellement hiérarchique.
2. **Rôle = variable latente** (ROMA, Wang 2020). Le rôle conditionne la politique ;
   régularisateurs info-théoriques : rôles identifiables depuis le comportement (max I(rôle ;
   trajectoire)), spécialisés et temporellement stables. Rôles **émergents**.
3. **Rôle = type/capacité fixe** (ton cas). Embedding de capacité rᵢ figé, tronc partagé +
   conditionnement. C'est l'apprentissage hétérogène à paramètres partagés.

**Ton modèle = hybride** : capacité **fixe** rᵢ (latent figé : médecin, mitrailleur…) +
**tâche dynamique** gᵢᵗ (sous-objectif assigné par le chef). Politique :
π(aᵢ | oᵢ, rᵢ, gᵢᵗ). La capacité est statique (qui tu es), la tâche est dynamique (ce que tu
fais maintenant) — la dynamicité vient du chef (Module 4), pas du rôle.

**Partage de paramètres + ID/rôle** (Gupta 2017) : un seul réseau conditionné par l'embedding
de rôle → partage l'expérience entre agents (efficacité d'échantillonnage) tout en permettant
la spécialisation. Compromis central : partage (efficace, peu spécialisé) ↔ réseaux séparés
(spécialisés, voraces en données). Le conditionnement par rôle est le point d'équilibre.

**Pourquoi la spécialisation aide** : division du travail = réduction de l'espace de politiques
à explorer par agent + diversité de couverture. Lien avec l'apprentissage multi-tâches.

---

## Module 4 — RL hiérarchique (le chef comme manager)

**Abstraction temporelle = semi-MDP**. Le chef ne micro-gère pas : il assigne des tâches qui
**durent**.

**Cadre des options** (Sutton, Precup, Singh 1999) : une option ω = ⟨Iω (ensemble
d'initiation), πω (politique intra-option), βω (condition de terminaison)⟩. Apprentissage par
SMDP Q-learning sur les options ; apprentissage intra-option. Une « manœuvre doctrinale »
(supprimer, déborder, bondir, soigner) se modélise comme une option.

**Le chef = manager** :
- **FeUdal Networks** (Vezhnevets 2017) : le manager fixe des buts directionnels dans un espace
  latent à basse résolution temporelle ; le worker reçoit une **récompense intrinsèque** pour
  suivre la direction du manager (similarité cosinus). Entraînement découplé des deux niveaux.
- **Feudal Multi-Agent Hierarchies** (Ahilan & Dayan 2019) : un agent-manager + agents-workers ;
  les actions du manager = buts/récompenses transmis aux workers. **Correspond exactement** à
  ta structure 1 chef + 3 spécialistes.
- **Option-Critic** (Bacon 2017) : apprend les options de bout en bout par gradient (valeur
  d'option, gradient intra-option, gradient de terminaison) → évite de coder les options à la
  main. Alternative si on veut que les manœuvres émergent.

**Espace d'action du chef** : « assigner le sous-objectif g au spécialiste i » — petit,
structuré, combinatoire (problème d'allocation de tâches). Beaucoup plus traitable que l'espace
d'action joint brut.

**CMDP × hiérarchie** : la contrainte de risque peut être posée au **niveau manager**
(budget de risque alloué entre sous-tâches) ou propagée aux workers. Le manager devient un
**planificateur sous contrainte** qui répartit un « budget de pertes acceptable ».

**Robustesse à la perte du chef** (problème ouvert) : si le chef tombe, qui commande ? Pistes :
politique de manager partagée et ré-attribuable, repli décentralisé, taille d'équipe variable.

---

## Module 5 — Observabilité partielle, mémoire et communication

**État de croyance** : en POMDP, la statistique suffisante est la **croyance** b(s) = P(s |
historique), mise à jour par filtrage bayésien ; la politique optimale fait croyance → action.
Exact = intraitable → approché.

**Spécificité Dec-POMDP** : aucun agent ne peut maintenir la **vraie** croyance (il faudrait
les observations des autres) → chacun maintient une croyance/encodage **local** de son
historique τᵢ.

**Mémoire pratique** : réseau **récurrent** (GRU/LSTM) encodant τᵢ en un état caché ≈ croyance
approchée / statistique suffisante. **DRQN** (Hausknecht & Stone 2015) ; **R2D2** (Kapturowski
2019) pour le replay récurrent à grande échelle. Standard dans les implémentations QMIX/MAPPO.

**Vue info-théorique** : compresser l'historique en une statistique qui préserve l'information
pertinente pour la décision (suffisance prédictive). Lien avec les représentations d'état
prédictives.

**Communication apprise** : pour surmonter l'observabilité partielle, les agents échangent des
messages **différentiables** :
- **DIAL** (Foerster 2016) — messages à gradient traversant le canal ;
- **CommNet** (Sukhbaatar 2016) — communication continue moyennée ;
- **TarMAC** (Das 2019) — communication ciblée par attention.
Pour ton cas : la **radio** = un canal de communication appris, à **bande passante limitée**
(messages discrets/courts) → réalisme tactique + régularisation.

**Fog of war = collecte active d'information** : la reconnaissance a une **valeur**. Modélisable
par des objectifs dirigés par l'information (ρ-POMDP, planification en espace de croyance) →
le sniper/éclaireur qui réduit l'incertitude est récompensé pour la réduction d'entropie.

---

## Module 6 — Récompense : éparse, shaping, CMDP, curriculum

**Problème de la récompense éparse** : « mission réussie » arrive rarement → gradient quasi nul
→ exploration intraitable sans aide.

**Shaping par potentiel** (Ng, Harada, Russell 1999) — **théorème d'invariance de politique** :
F(s,s') = γΦ(s') − Φ(s) ne change **pas** la politique optimale. C'est la **seule** forme de
shaping prouvablement sûre. Garde-fou critique : tout shaping ad hoc (récompenser « tirer »,
« avancer ») risque de **détourner** la politique de l'objectif réel (reward hacking).

**Machines à récompense** (Toro Icarte 2018/2022) — *l'outil pour mission compositionnelle* :
on encode la structure de la mission comme un **automate** (machine de Mealy) ; chaque état =
une étape ; les transitions déclenchent les récompenses. Bénéfices : (1) shaping par potentiel
**automatique** par état d'automate ; (2) expérience contrefactuelle (**QRM** met à jour tous
les états d'automate en parallèle) ; (3) décomposition de tâche prête pour la hiérarchie. Les
« objectifs multiples » deviennent un graphe de tâches exploitable.

**RL conditionné par but + HER** : π(a|o, g) ; **Hindsight Experience Replay** (Andrychowicz
2017) réétiquette les échecs comme succès vers le but **effectivement atteint** → signal dense
gratuit en milieu épars.

**Curriculum** : missions faciles → dures (objectif proche, sans ennemi → loin, défendu).
Curriculum **automatique** : teacher-student, **PLR** (Jiang 2021), UED régret (PAIRED, Dennis
2020), self-play / population pour le combat.

**Motivation intrinsèque** (pour trouver le signal épars) : curiosité **ICM** (Pathak 2017),
**RND** (Burda 2018), comptage. Récompense l'exploration de l'inconnu.

**Imitation / IRL** (si démonstrations Arma humaines disponibles) : clonage comportemental
(amorçage), **GAIL** (Ho & Ermon 2016), **AIRL** (Fu 2018) pour récupérer une récompense, ou
**IRL** pour extraire la « doctrine » implicite d'un expert. Réduit drastiquement le coût
d'exploration.

**CMDP comme signal** : le coût (pertes) est un signal type-récompense ; le lagrangien est une
forme de shaping auto-réglée par λ (Modules 1-2).

**Risque (raffinement avancé)** : passer de l'espérance à **CVaR** (Chow 2015) — optimiser la
queue (pire 5 % des issues) encode l'aversion au risque, plus réaliste que l'espérance pour du
combat.

---

## Module 7 — L'interface Arma 3 comme décision de modélisation

**Niveau d'abstraction de l'action = définit le MDP.** Choix structurant :
- **Bas niveau** : aller-à-coordonnée, tirer, posture. Espace énorme, horizon long, très
  difficile à apprendre.
- **Haut niveau (macro-actions)** : supprimer ce secteur, déborder par la droite, se mettre à
  couvert, soigner. Espace réduit, décisions rares.

**Hybridation BT/doctrine ⊕ RL** (le point pragmatique majeur) : modéliser les macro-actions
comme des **options** dont la politique intra-option est un **Behavior Tree / script doctrinal**
codé à la main. **Le RL apprend QUAND (sélection d'options) ; le BT exécute COMMENT.**
Formellement, un semi-MDP sur des options à politiques fixes. Réduit massivement ce qu'il faut
apprendre → réconcilie la voracité du MARL avec la lenteur d'Arma.

**Abstraction d'observation** : quelles features exposer (brutes vs tactiques : distances,
secteurs, contacts, état des coéquipiers). Critère : suffisance de Markov de l'observation.

**Échelle de temps** : Arma est temps réel. Fréquence de décision, frame-skip / répétition
d'action. Temps-sim vs temps-mur : peut-on tourner **headless** et **plus vite que le temps
réel**, en **plusieurs instances parallèles** ? C'est ce qui détermine le débit d'échantillons
→ la faisabilité même du projet.

**Le pont** : extension Arma (callExtension → socket) vers Python ; wrapper de type Gym
(reset/step/observation/action). Reproductibilité/déterminisme des épisodes pour la stabilité
de l'apprentissage.

**Réalité d'efficacité d'échantillonnage** : le MARL sans modèle réclame des millions de pas ;
Arma est lent → **le débit est LE goulot d'étranglement**. Leviers : (a) abstraction d'action
haute, (b) hybride BT (moins à apprendre), (c) parallélisme headless, (d) amorçage par
imitation, (e) éventuellement model-based.

---

## Synthèse — l'architecture intégrée

Tout se compose en un **acteur-critique hiérarchique, sous contrainte, en CTDE** :

```
                    MACHINE À RÉCOMPENSE  (états = étapes de mission)
                              │  fournit le contexte de tâche + shaping par potentiel
                              ▼
   ┌──────────────────────────────────────────────────────────────┐
   │  CHEF — manager (semi-MDP, échelle lente)                       │
   │  • sélectionne des options / sous-objectifs gᵢ par spécialiste  │
   │  • planificateur sous contrainte : alloue un budget de risque   │
   │  • observe sa vue locale (CTDE : critique privilégié à l'entraî.)│
   └───────────────┬────────────────────────────────────────────────┘
            assigne gᵢ (buts temporellement étendus)
        ┌──────────┼───────────┐
        ▼          ▼           ▼
   spécialiste  spéc.       spéc.        ◂ politique partagée conditionnée
   π(a | oᵢ, rᵢ, gᵢ)                        par capacité rᵢ (fixe) + tâche gᵢ
   • encodeur récurrent (croyance locale, fog of war)
   • actions = macro-actions/options, intra-politique = Behavior Tree doctrinal
   • communication apprise à bande passante limitée (radio)
        │
        ▼
   CRITIQUES CENTRALISÉS (CTDE, jetés à l'exécution)
   • Q_tot^R (retour mission)  +  Q_tot^C (coût/pertes)  — décomposés (IGM)
   • couplage lagrangien : ℒ = Q^R − λ(Q^C − c),  λ appris (prix du risque)
   • crédit : avantage contrefactuel (COMA) / décomposition de valeur
```

**Entraînement** : curriculum (facile → dur) + motivation intrinsèque + amorçage par imitation
si données ; instances Arma headless parallèles pour le débit.
**Exécution** : chaque agent (chef compris) agit sur sa croyance locale récurrente — décentralisé,
réaliste, robuste à la coupure de l'oracle.

**Lecture transversale des modules** :
- Module 0 donne l'objet et la barrière (NEXP) → justifie l'approche approchée.
- Modules 1-2 donnent le moteur d'apprentissage (valeur vs politique) et l'assignation de crédit.
- Module 3 donne la spécialisation (capacités fixes conditionnées).
- Module 4 donne le commandement (manager/options) qui rend la dynamicité des tâches possible.
- Module 5 donne la perception réaliste (mémoire, croyance, comms).
- Module 6 donne le signal d'apprentissage (épars → dense de façon sûre) + le risque.
- Module 7 ancre tout dans Arma et fixe le vrai goulot (débit d'échantillons).

---

## Frontières et problèmes ouverts (spécifiques à ce projet)

1. **Limite de représentation** : tactiques non-monotones (coordination tout-ou-rien) → exige
   au-delà de QMIX (QPLEX ou acteur-critique).
2. **Robustesse à la perte d'agents** : mort du chef / taille d'équipe variable → *ad hoc
   teamwork* (Stone 2010), coordination zéro-shot (*Other-Play*, Hu 2020).
3. **Non-stationnarité multi-niveaux** : manager et workers co-adaptent → instabilité ; il faut
   découpler les échelles de temps / geler des niveaux.
4. **Sécurité pendant l'entraînement** : le CMDP garantit la contrainte à convergence, pas
   forcément pendant l'exploration → safe exploration.
5. **Complexité d'échantillon vs débit Arma** : contrainte liante du projet ; arbitrage
   abstraction/hybridation/parallélisme/imitation.
6. **Reproductibilité & variance** du simulateur → stabilité et évaluation.
7. **Généralisation** inter-missions / inter-cartes (zéro-shot) vs surapprentissage d'un
   scénario.
8. **Spécification de récompense** : reward hacking dans un sim riche → s'appuyer sur shaping
   par potentiel + machines à récompense, jamais sur du shaping ad hoc non prouvé.

---

## Bibliographie pivot

**Fondations** — Bernstein et al. 2002 (complexité Dec-POMDP) ; Oliehoek & Amato 2016 (manuel
Dec-POMDP).
**Décomposition de valeur** — Sunehag 2018 (VDN) ; Rashid 2018 (QMIX) ; Son 2019 (QTRAN, IGM) ;
Wang 2021 (QPLEX) ; Rashid 2020 (Weighted QMIX).
**Policy gradient / crédit** — Lowe 2017 (MADDPG) ; Foerster 2018 (COMA) ; Yu 2021 (MAPPO) ;
Wolpert & Tumer 2002 (difference rewards).
**Rôles** — Wang 2020 (ROMA) ; Wang 2021 (RODE) ; Gupta 2017 (partage de paramètres).
**Hiérarchie** — Sutton, Precup, Singh 1999 (options) ; Bacon 2017 (option-critic) ;
Vezhnevets 2017 (FeUdal) ; Ahilan & Dayan 2019 (feudal multi-agents).
**Observabilité / comms** — Hausknecht & Stone 2015 (DRQN) ; Kapturowski 2019 (R2D2) ;
Foerster 2016 (DIAL) ; Sukhbaatar 2016 (CommNet) ; Das 2019 (TarMAC).
**Récompense** — Ng, Harada, Russell 1999 (shaping par potentiel) ; Toro Icarte 2018/2022
(reward machines) ; Andrychowicz 2017 (HER) ; Pathak 2017 (ICM) ; Burda 2018 (RND) ;
Ho & Ermon 2016 (GAIL).
**Contrainte / risque** — Altman 1999 (CMDP) ; Achiam 2017 (CPO) ; Gu et al. 2021 (MACPO) ;
Chow 2015 (CVaR).
**Curriculum / généralisation** — Jiang 2021 (PLR) ; Dennis 2020 (PAIRED) ; Stone 2010 (ad hoc
teamwork) ; Hu 2020 (Other-Play).
