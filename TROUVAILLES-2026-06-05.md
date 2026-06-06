---
title: "Harmattan — Sandbox géopolitique : trouvailles du 5 juin 2026"
author: "Younes Bouhassoun — Harmattan Intelligence (avec Claude, bâtisseur)"
date: "5 juin 2026"
lang: fr
titlepage: true
toc: true
toc-own-page: true
colorlinks: true
---

# Objet

Ce document consigne les résultats d'une journée de recherche sur le **sandbox géopolitique Harmattan** : un laboratoire
sur GPU où des lois de la puissance (territoire, ressources, doctrines, populations) deviennent **mesurables**, couplé en
fin de journée au moteur Arma 3 pour résoudre les batailles en haute fidélité. Sept lois émergentes ont été établies dans
le simulateur abstrait, une huitième trouvaille (propagation d'un micro-biais tactique en hégémonie stratégique) est
sortie du couplage Arma. Tout est reproductible : chaque loi est adossée à un protocole, des effectifs de guerres
simulées, et ses limites.

**Portée épistémique, énoncée d'emblée** : ce sont des lois *de ce modèle*. Leur valeur n'est pas « voilà comment marche
le monde » mais « voilà une méthode qui rend des hypothèses stratégiques comparables et falsifiables » — variation
contrôlée, baselines, rotations, seeds indépendantes, vérification adversariale.

# L'instrument

- **`geo_gpu.py`** (v1→v4) : N pays sur un anneau de régions ; territoire → trésor → force ; combat de frontière
  (le plus fort perce, conquérir = surextension) ; capitale = mort ; **une colline par pays, victoire = tenir 2 collines
  simultanément** (règle Younes) ; **doctrines d'allocation par pays** (A/E/Z) ; **population civile par région**
  (produire, fuir, mourir — économie endogène). 100 % tenseurs PyTorch sur RTX 3090, ~200-350 k pas de guerre/s,
  10⁴-10⁵ guerres par condition expérimentale.
- **`run_geo.py`** : harnais de mesure (types de fin, durées, winrates par doctrine, métriques civiles, mode `--summary`
  pour sweeps).
- **`train_civ.py`** : politique civile **apprise** (PPO, avantage partagé par région) remplaçant la règle de fuite.
- **`geo_arma.py`** : couplage stratégique→tactique — 10 serveurs Arma headless, la bataille de la colline la plus
  menacée de chaque guerre est résolue dans le vrai moteur (45 unités/bataille, 450 simultanées), le verdict remonte
  dans la carte.

# Les sept lois émergentes (simulateur abstrait)

## Loi 1 — Topologie ≠ valeur : un carrefour rend la guerre totale, même gratuit

**Protocole** : ajout d'une région centrale (KOTH) reliée à une porte de chaque pays ; sweep du bonus de revenu 0→12
(4 096 envs, 50-113 k guerres/point).
**Résultat** : à bonus **zéro**, la simple existence du carrefour fait passer les éliminations de 1.68 à 1.99/2 et la
durée des guerres de 33 à 15.6 pas. La géographie de connexion détruit le tampon de l'anneau avant que la richesse joue.
**Lecture** : l'architecture des connexions pèse avant la valeur des nœuds.

## Loi 2 — Le calice empoisonné : un prix modéré est un atout, un prix énorme est un piège

**Protocole** : même sweep, métrique causale « le 1ᵉʳ preneur du centre gagne-t-il ? » (la métrique « détenteur final »
est tautologique — le vainqueur finit par tout tenir).
**Résultat** : non-monotone — 0.47 (bonus 0) → pic **0.57 (bonus 1)** → **0.43 (bonus 12, sous la baseline)**. Prendre
un prix énorme en premier concentre l'hostilité des deux autres et la surextension : l'avantage se retourne (malédiction
*relative* : toujours > hasard 0.33).
**Lecture** : la valeur d'un prix stratégique s'inverse au-delà d'un seuil — le désigner trop précieux le rend toxique.

## Loi 3 — L'horloge politique contre l'horloge militaire

**Protocole** : règle « 2 collines » ; sweep de `hold_T` (durée de tenue exigée pour que la victoire soit reconnue),
1→20 pas (41-79 k guerres/point).
**Résultat** : hold 1 → **93 %** de victoires politiques, **0 %** d'annihilation, le perdant survit (vainqueur ~46 % du
territoire). hold 20 → la victoire politique devient lettre morte (6 %) et la guerre redevient totale (77 %
d'annihilation). Invariant : le vainqueur tient TOUJOURS sa propre colline (1.00 sur ~250 k guerres) — le seul chemin
gagnant observé est *consolidation intérieure + projection*.
**Lecture** : plus une victoire est reconnue vite, moins la guerre détruit ; si l'horloge politique est plus lente que
l'horloge militaire, la condition de victoire n'arrête plus rien (théorie de la terminaison des guerres, retrouvée
empiriquement).

## Loi 4 — « Renforcer le succès, pas l'échec » : la doctrine réactive perd partout

**Protocole** : doctrine = politique d'**allocation** du trésor à revenu identique (on isole la philosophie, pas
l'avantage numérique). **A**=Amplificateur (tout sur sa pointe la plus forte), **E**=Égaliseur (uniforme sur le front),
**Z**=Zéro-somme/Déni (tout face à la plus grosse force ennemie — réactif). 21 runs : sanity symétriques (~0.333
partout), mix AEZ ×3 rotations (invariant), **matrice d'invasion complète ×3 positions d'envahisseur** (invariante).
**Résultat** (winrate envahisseur, équité = 0.33) :

| envahisseur ↓ / monde → | monde-A | monde-E | monde-Z |
|---|---|---|---|
| **A** | — | **0.757** | **0.523** |
| **E** | 0.062 | — | 0.310 |
| **Z** | 0.150 | 0.205 | — |

A est **strictement dominante** (envahit tout, rien ne l'envahit — seule stratégie évolutionnairement stable des trois).
Z, la doctrine réactive, est la pire partout. Mix AEZ : A 0.50 / E 0.34 / Z 0.16.
**Lecture** : allouer en réponse à la menace adverse = céder l'initiative en permanence. La maxime militaire classique
(*reinforce success, starve failure*) ressort comme propriété d'équilibre.
**Sous-trouvailles** : le caractère du monde dépend de sa composition (monde-E le moins décisif → conflits gelés ;
monde-Z hyper-décisif et bref ; la diversité doctrinale rend le monde plus décisif que l'homogénéité). **Effet
état-tampon** : une doctrine faible ne gagne pas mais *redistribue* la victoire — selon le côté où un résident siège
par rapport à l'envahisseur, son sort diverge ×3-7 (possiblement amplifié par l'asymétrie de placement des collines —
non promu en loi avant vérification).

## Loi 5 — La guerre brûle son propre carburant

**Protocole** : v4 « civils » — le revenu ne vient plus d'une rente territoriale mais de la **population** des régions
tenues (production calibrée pour matcher l'ancienne rente) ; les civils fuient la menace et meurent quand une région
change de mains (micro-règles assumées).
**Résultat** : l'annihilation s'effondre partout (AAA : 0.37→0.09 ; EEE : 0.30→0.17 ; ZZZ : 0.40→0.31) ; guerres plus
longues, moins décisives ; la victoire politique devient la fin dominante.
**Lecture** : quand l'économie est endogène, morts et exodes détruisent la base fiscale avant que la conquête totale
soit payable. Première limitation de la guerre produite par une mécanique *interne* et non par une règle imposée.

## Loi 6 — Le coût civil est une propriété du monde doctrinal

**Résultat** (mondes symétriques, v4) : morts/population initiale — monde-E **0.179**, monde-Z 0.299, monde-A **0.367**
(et le plus d'exode : 0.86). La doctrine qui *perd* les guerres (E) est celle qui protège les populations ; la dominante
(A) est la plus meurtrière. En mix, l'économie endogène **amplifie** la hiérarchie : A 0.58 / E 0.37 / **Z 0.05**
(le réactif ne capture jamais de base fiscale ; le conquérant saisit le tissu fiscal intact — 77 % de la population
restante sous son contrôle : la conquête paie *en population*, pas de victoire à la Pyrrhus dans ce régime).
**Lecture** : l'arbitrage puissance/humanité devient mesurable — c'est une variable morale-structurelle au sens du
programme world-model.

## Loi 7 — Les civils appris fuient la géographie stratégique, pas la menace visible

**Protocole** : la règle de fuite scriptée est remplacée par une politique neuronale partagée par région (obs locales,
actions {rester, fuir-G, fuir-D}, reward = survie pure), PPO, monde AAA ; baselines no-flee et règle-main ; évaluation
sur seed indépendante (24 k guerres) ; sonde comportementale (11 k guerres) ; test de transfert sur mondes jamais vus.
**Résultat** : morts — RL **0.190** vs règle 0.368 vs immobiles 0.450 (**−48 % vs la règle**). Comportement découvert :
le RL fuit *moins* que la règle à tout niveau de menace visible, mais **évacue préventivement à t<3 quand la menace est
nulle** (0.13 vs 0.00) et **vide les collines** (population finale 9.3 % vs 32.1 %) — il a appris où la guerre IRA
(les prix de la condition de victoire), pas où l'armée EST. Transfert : bat la règle dans tous les mondes non vus
(EEE 0.126<0.181 ; ZZZ 0.255<0.300 ; AEZ 0.236<0.365) — comportement structurel, pas surajusté.
**Lecture** : le déplacement anticipatif observé dans les vrais conflits (les populations près des objectifs
stratégiques partent les premières) émerge d'un signal de survie pur.
**Limites assumées** : pas d'attachement au lieu (partir est gratuit), pas de besoins, pas de loyauté, un seul cerveau.
Chaque absence est une expérience suivante.

# Le couplage Arma (test du 5 juin au soir)

## Le pipeline

10 serveurs Arma headless = 10 guerres géopolitiques en parallèle (doctrines AEZ, civils RL dans la boucle). À chaque
pas géo, la bataille de la colline la plus menacée est résolue dans le moteur : KOTH 3 factions, 15 unités/faction
(45/bataille, 450 simultanées — plafond CPU pratique), cerveau `koth_finetuned.pt`, handicap de dégâts ∝ rapport de
forces géo, verdict (capture, sinon contrôle cumulé) imposé à la carte. **Premier run : 10/10 guerres bouclées en
20 minutes, 66 batailles Arma (68 % décidées par vraie capture à 45 unités, contre ~10 % à 9 unités — la masse rend le
combat décisif), 27 verdicts de colline imposés par Arma.** La boucle stratégique(GPU)→tactique(Arma)→stratégique est
fermée.

## Trouvaille 8 — Un micro-avantage tactique se propage en hégémonie stratégique

Baseline abstraite (mêmes guerres, même seed) : **A gagne 8/10**. Avec batailles Arma : **le pays mappé sur OPFOR gagne
10/10** — le moteur renverse la hiérarchie doctrinale.

**Enquête (chronologie honnête)** :

1. Hypothèse « armure CSAT » → **réfutée** : à équipement strictement égalisé (aucune protection, même fusil pour
   tous), OPFOR gagne encore 19/19.
2. Vraie cause, trouvée **dans notre code** : artefact d'échelle de la formule de spawn — la file d'unités s'étire vers
   le nord-est en coordonnées monde quel que soit le camp ; négligeable à 3 unités (±12 m), elle déporte de **+78/+91 m**
   à 15 unités, et la file d'OPFOR (spawn au sud-ouest) pointe droit dans la zone de capture. OPFOR gagnait *à la course
   de spawn*, pas au combat.
3. Correctif (spawn en cercle centré) → le biais **s'inverse** (BLUFOR 17/18, 40 % d'indécis) : le spawn était le moteur
   principal, mais un résidu demeure — suspect : le cerveau lui-même, affiné dans l'ancien monde biaisé (observations en
   coordonnées monde → habitudes positionnelles).
4. Réponse méthodologique définitive : **neutralisation statistique par rotation pays↔faction** (guerre i : pays c →
   faction (c+i) mod 3) — quel que soit le biais résiduel, il se répartit également sur les trois doctrines.

**Ce qui reste vrai et démontré** : un avantage tactique microscopique (~80 m au spawn), invisible à petite échelle et
indétectable dans le sim abstrait, **amplifié par la boucle de rétroaction stratégique (colline→territoire→trésor→
forces), produit un sweep hégémonique 10/10**. Micro-cause, macro-effet : le couplage des échelles révèle ce qu'aucune
des deux échelles ne montre seule — c'est l'argument empirique central en faveur de l'architecture deux-échelles.

## Test doctrines propre (rotation + égalisation + spawn corrigé) — résultat final

10 guerres, 76 batailles Arma (51 % décidées par capture en jeu — le combat *juste* stalemate davantage que le biaisé,
qui décidait à 68 %), 22 verdicts de colline imposés, 25 minutes.

| Vainqueurs | Géo-Arma (propre) | Baseline abstraite (mêmes guerres) |
|---|---|---|
| **A — Amplificateur** | **5** | **8** |
| **E — Égaliseur** | 3 | 2 |
| **Z — Zéro-somme** | 2 | 0 |

**Conclusion 1 — la hiérarchie doctrinale survit au vrai moteur.** L'Amplificateur reste premier une fois tout biais
neutralisé : le signal traverse la chaîne complète doctrine → trésor → forces géo → handicap de spawn → bataille réelle
→ verdict de colline. La « philosophie économique » d'un pays se lit jusque dans l'issue de ses fusillades.

**Conclusion 2 — la friction du réel est l'alliée du faible.** Arma adoucit la domination (A : 8→5) et donne au
réactif ses premières victoires (Z : 0→2) — dont une par élimination, au terme de la guerre la plus longue (11 pas)
et la plus coûteuse en civils (0.31 contre 0.18 de moyenne) : le réactif ne gagne qu'à l'usure totale. Le bruit du
combat réel (terrain, balistique, stalemates) empêche l'avantage structurel de se convertir mécaniquement.

**Réserve** : n = 10 guerres — cohérent avec l'abstrait, pas une preuve statistique indépendante (viser ~30+ guerres
pour des intervalles propres).

# Bilan méthodologique

Ce que la journée valide comme **méthode** (le vendable, au-delà des lois) :

1. **Variation contrôlée d'une seule variable** → loi émergente (sweeps bonus/hold/doctrines).
2. **Baselines et sanity systématiques** (mondes symétriques ~⅓, rotations invariantes) avant toute conclusion.
3. **Métriques causales vs tautologiques** (1ᵉʳ preneur vs détenteur final).
4. **Matrice d'invasion** (stabilité évolutionnaire) pour tester la robustesse d'une dominance.
5. **Seeds indépendantes + transfert** pour le RL.
6. **Chasse aux biais d'instrument** : hypothèse → test → réfutation → cause réelle → correctif → neutralisation
   statistique quand la chasse est sans fin.
7. **Journal autoritaire** (`MEMOIRE-COMMUNE.md`) tenu au fil de l'eau, erreurs incluses (hypothèse CSAT réfutée,
   incident du garde `__main__`).

# Artefacts produits (état au 5 juin, 21 h)

| Fichier | Rôle |
|---|---|
| `geo_gpu.py` | sandbox géopolitique v4 (collines, doctrines, civils, hook `civ_policy`) |
| `run_geo.py` | harnais de mesure + sweeps |
| `train_civ.py` | PPO civils (garde `__main__` posé) |
| `civ_learner.pt` | politique civile apprise (morts 0.190 vs règle 0.368) |
| `geo_arma.py` | couplage 10 serveurs géo→Arma→géo (rotation, égalisation, handicaps) |
| `arma_env_koth.py` | env KOTH 3 factions — **spawn corrigé** (cercle centré) |
| `MEMOIRE-COMMUNE.md` | journal autoritaire complet |
| `multi_server.sh` (sandbox) | lanceur M serveurs headless |

# Nuit du 5 au 6 juin — la couche opérationnelle

## L'architecture à trois étages

Construite et validée dans la nuit : **chef d'opération** (machine à phases : ordres par escouade {objectif, posture},
transitions conditionnelles, contingences avec raison loggée) → **escouades** (cerveau gelé `koth_finetuned` en micro,
postures = biais de logits : move/assault/suppress/hold, zéro réentraînement) → **moteur** (ennemi scripté : garnison,
patrouilles, QRF déclenchable). Opération-type HARMATTAN-1 : raid en 5 phases (infiltration 2 axes → mise en place →
assaut sous suppression → consolidation contre contre-attaque → exfiltration), critères de succès mesurables.
**Leçon de mouvement** : le micro-pilotage étrangle la marche (~10 m/min) — séparation mouvement opérationnel
(waypoint de groupe hors contact) / action tactique (le cerveau au contact), comme une vraie unité.
**Validation** : garnison de 8 anéantie pour 7 % de pertes amies dès le run 3.

## Le wargaming : 60 opérations, deux fausses conclusions tuées

| n=60 (30/plan) | Plan A — appui d'abord | Plan B — assaut direct |
|---|---|---|
| Succès | **23/30 (77 %)** | **23/30 (77 %)** |
| Pertes moyennes | 17.4 % | 13.8 % |
| Ennemis restants | 0.77 | 0.53 |

**Égalité parfaite au succès** — et un cas d'école : la série 1 (n=15/plan) « prouvait » la supériorité de B (67-80),
la série 2 « prouvait » celle de A (87-73). Régression vers la moyenne des deux côtés : une publication à n=15 aurait
été fausse dans les deux sens. Conclusion défendable : **l'opération est robuste à la partition — le succès vient de
la micro apprise et de la structure phases/contingences, pas du choix doctrinal de surface.** Modes d'échec distincts :
A échoue par indécision (pertes faibles, garnison intacte), B par saignée.

## Loi 9 — la richesse rend la guerre totale (carte de régimes, 48 conditions, ~1.8 M guerres)

À horloge politique fixe, augmenter la richesse du monde fait exploser l'annihilation (AEZ hold 10 : 0.77→0.93) :
la richesse accélère l'horloge **militaire** pendant que l'horloge politique reste fixe — les capitales tombent avant
que la victoire politique soit validée. Corollaires mesurés : guerres riches plus **brèves** et moins meurtrières pour
les civils *par guerre* ; **exception égalitaire** (le monde-E riche se gèle : paix par impuissance mutuelle, le plus
humain de la carte) ; en guerre totale, le vainqueur contrôle jusqu'à 89 % de la population restante. Par ailleurs la
hiérarchie A>E>Z est **universelle** sur la carte — aucun renversement par la richesse : la loi 4 est généralisée.

## Loi 10 — le prédateur économique : co-dominant mais instable (doctrine D, instrument nettoyé)

La doctrine **D (déni de revenu)** vise la région ennemie la plus **peuplée** — étrangler la base fiscale. Après
correction complète des tie-breaks (sanity DDD : 0.334/0.334/0.332 ; rotations invariantes à ±0.003) :

- **Bataille royale A-D-E : D 0.499 / A 0.488 / E 0.013** — le prédateur économique fait jeu égal avec
  l'Amplificateur en écologie mixte, en dévorant l'Égaliseur.
- **Matrice d'invasion** : A reste l'**unique stratégie évolutionnairement stable** (rien n'envahit son monde,
  il envahit tout — y compris le monde-D à 0.370). Mais sous lui, un **sous-monde non transitif** : le bloc
  égalitaire collectif **repousse** le prédateur isolé (D→EE : **0.057** — pas de point riche faible quand la
  défense est uniforme) ; et le contre-forceur Z, perdant partout ailleurs, **envahit le monde des prédateurs**
  (Z→DD : **0.430** — la pointe du chasseur de population s'expose au contre-punch).

**Lectures géopolitiques** : la prédation économique paie dans les mondes divers à cibles molles ; la défense
collective égalitaire est *la* structure anti-prédateur ; la contre-force est un spécialiste anti-prédateur.
Le monde tout-D reste le plus brutal mesuré (annihilations massives, guerres-éclair, vainqueur sur des ruines).

**Leçon d'instrument (3 incarnations en 24 h : pointe, fuite civile, couronnement du vainqueur)** : *tout argmax
est un tie-break déguisé, et tout tie-break déterministe est un biais en embuscade* — l'asymétrie DDD venait en
dernier ressort des **complétions simultanées de victoire** (fréquentes dans les guerres symétriques de prédation,
quasi absentes ailleurs — d'où des sanity trompeusement propres sur A/E/Z). Bruiter les départages par défaut.

## Les leçons d'ingénierie de la nuit (à relire avant chaque session)

1. **Garde `__main__` sur tout script** — le même bug a mordu deux fois en 12 h (train_civ, run_op).
2. **Jamais d'optimisation sans re-validation** — « l'amélioration » de la marche d'assaut a envoyé 10 opérations
   défiler sous le feu ; le run de référence existait, il suffisait de re-tester contre lui.
3. **Le parallélisme est la seule accélération sur serveur dédié** (`setAccTime` ignoré) — 16 serveurs validés.
4. **À n=15, on publie des erreurs** — dans les deux sens.

# Dette et prochaines étapes

- **Dette de consolidation (maximale)** : pas de `git` ; ce document et le snapshot `save01` en tiennent lieu
  provisoirement. Priorité : dépôt git + note de recherche au format publiable.
- Variante **Z = déni de revenu** (l'interprétation zéro-somme non testée).
- **Coût de départ des civils** (attachement) — le vrai dilemme du déplacé.
- **RL stratégique** (cerveau-pays) : question ouverte du *tertius gaudens*.
- Ré-entraîner le cerveau KOTH dans le monde au spawn corrigé (lever le biais résiduel à la source).
- Sweep de régimes (income / nombre de pays / létalité) → carte de régimes.
