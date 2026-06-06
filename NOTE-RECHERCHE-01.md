---
title: "Un laboratoire à deux échelles pour l'étude empirique des dynamiques stratégiques"
subtitle: "Harmattan — Note de recherche n° 1"
author: "Younes Bouhassoun — Harmattan Intelligence"
date: "6 juin 2026"
lang: fr
titlepage: true
toc: true
toc-own-page: true
colorlinks: true
---

# Résumé exécutif

Cette note documente la construction et l'exploitation d'un **laboratoire de simulation à deux échelles** pour
l'étude empirique des dynamiques stratégiques : un simulateur géopolitique abstrait sur GPU (~300 000 pas de
guerre/seconde, des dizaines de milliers de guerres par condition expérimentale) couplé à un moteur de combat
haute fidélité (Arma 3, balistique et terrain réels, agents pilotés par apprentissage par renforcement).

En 48 heures d'exploitation, l'instrument a produit :

- **dix lois émergentes** sur les dynamiques de puissance (territoire, ressources, doctrines, populations),
  chacune avec protocole, effectifs et domaine de validité ;
- une **couche opérationnelle** où des agents entraînés mènent des opérations multi-phases (raid, contre-attaque,
  exfiltration), évaluée sur **152 opérations** en conditions contrôlées ;
- **trois hypothèses pré-enregistrées** au sens de la discipline tetlockienne — prédictions chiffrées et seuils de
  décision écrits avant les données — toutes tranchées : une validée, deux réfutées proprement ;
- la démonstration répétée qu'un **chiffre global peut mentir** : un taux de succès de 77 % s'est révélé mesurer
  des opérations qui esquivaient leur épreuve principale ; sa décomposition conditionnelle a requalifié la
  conclusion et réorienté le programme.

La thèse de la note n'est pas que ces lois décrivent le monde réel — ce sont les lois d'un modèle. La thèse est
**méthodologique** : un praticien équipé d'un simulateur bien instrumenté, d'une discipline de pré-enregistrement
et d'une chasse systématique aux biais d'instrument peut rendre des questions stratégiques *falsifiables*, à un
coût matériel modeste (une station de travail).

# 1. Objet et programme

Le programme Harmattan vise à rendre **mesurables** des hypothèses sur l'architecture de la puissance : comment le
territoire produit des ressources, comment les ressources deviennent de la force, comment les philosophies
d'allocation s'affrontent, comment les populations subissent et façonnent la guerre. L'approche : construire des
mondes simulés dont chaque règle est explicite, y faire varier **une variable à la fois**, et mesurer ce qui émerge
sur de grands effectifs.

Deux échelles sont nécessaires et complémentaires :

| Échelle | Support | Débit | Rôle |
|---|---|---|---|
| **Stratégique** | simulateur tensoriel GPU (PyTorch, RTX 3090) | ~300 000 pas/s | exploration, lois, entraînement RL |
| **Tactique** | moteur Arma 3 (serveurs dédiés headless) | temps réel (×1) | validation haute fidélité, vérité-terrain |

L'ordre de grandeur qui justifie l'architecture : une décision du cerveau entraîné coûte **~360 microsecondes**
(pour 7 comme pour 672 soldats — le coût est celui du lancement du calcul, pas du calcul) ; un pas de simulation
Arma en coûte **~3 000 000**. L'intelligence représente 0,01 % du temps ; le reste est le prix du réalisme. On
explore donc dans le simulateur rapide et l'on ne paie le moteur que pour **valider**.

# 2. Méthode

Sept disciplines, toutes appliquées au moins une fois dans les résultats présentés :

1. **Variation contrôlée** — une variable par expérience (un bonus de revenu, une durée de tenue, une doctrine,
   la nature d'une contre-attaque), le reste figé.
2. **Tests de symétrie systématiques** — toute configuration symétrique doit produire des résultats symétriques
   (~⅓ chacun à trois joueurs) ; tout écart signale un **biais d'instrument**, à traquer avant toute conclusion.
3. **Rotations** — chaque mesure asymétrique est répétée dans toutes les permutations de position ; on ne lit que
   les moyennes par rotation. Cette pratique a, à deux reprises, protégé des conclusions que des biais cachés
   auraient autrement faussées.
4. **Métriques causales plutôt que tautologiques** — exemple : « le premier preneur du point central gagne-t-il ? »
   plutôt que « le détenteur final gagne-t-il ? » (le vainqueur finit toujours par tout tenir).
5. **Matrices d'invasion** — la robustesse d'une stratégie dominante se teste au sens évolutionnaire : une
   stratégie isolée peut-elle envahir un monde homogène d'une autre ? Le monde homogène résiste-t-il ?
6. **Pré-enregistrement** — pour les hypothèses opérationnelles, prédiction chiffrée et seuils de décision écrits
   et committés **avant** le premier run ; les références sont mesurées sur les données antérieures.
7. **Instrumentation native** — chaque étage logue ses décisions et leurs raisons ; un système qui bouge sans
   journal est réputé menteur jusqu'à preuve du contraire (la section 6 montre pourquoi).

# 3. L'instrument

**Échelle stratégique** (`geo_gpu.py`) : N pays sur un anneau de régions ; le territoire produit un trésor, le
trésor est alloué selon la **doctrine** du pays, la force perce aux frontières (conquérir = se surexposer) ;
une **colline** par pays, la victoire exige d'en tenir deux simultanément ; la capitale perdue vaut élimination.
Une **population civile** par région produit le revenu (l'économie est endogène), fuit la menace et meurt aux
changements de mains. Tout est tenseur, 4 096 à 8 192 guerres simultanées sur GPU.

**Échelle tactique** : agents individuels dans Arma 3 (macro-actions : avancer, suppresser, se couvrir, tenir),
pilotés par un réseau entraîné en simulateur puis affiné au feu réel (`koth_finetuned`). Un **pont** logiciel
relie Python au moteur (écriture d'ordres, lecture d'état). Jusqu'à 16 serveurs dédiés en parallèle
(~670 unités simultanées mesurées, charge CPU ~70 %).

**Couche opérationnelle** (`op_arma.py`) : un *chef d'opération* scripté — machine à phases : ordres par escouade
(objectif, posture), transitions conditionnelles, contingences avec raison journalisée. Les **postures**
(approche, assaut, fixation, tenue) sont des biais de logits appliqués au cerveau gelé : quatre comportements
collectifs distincts, zéro réentraînement. Le mouvement opérationnel (colonnes en marche) est délégué au moteur ;
le cerveau reprend la micro au contact — la distinction mouvement/action de toute armée réelle.

# 4. Résultats I — dix lois du bac à sable géopolitique

Chaque loi est issue d'un protocole contrôlé ; les effectifs vont de 40 000 à 120 000 guerres par condition.
Ce sont des **lois du modèle** ; leur intérêt est de montrer qu'on peut les produire, les chiffrer et les borner.

1. **Topologie ≠ valeur.** Un carrefour central rend la guerre totale même s'il ne rapporte rien (éliminations
   1,68 → 1,99/2 ; durée 33 → 16 pas, à bonus nul). L'architecture des connexions pèse avant la richesse des nœuds.
2. **Le calice empoisonné.** L'avantage du premier preneur d'un prix central est **non monotone** : réel pour un
   prix modéré (0,57), il s'inverse pour un prix énorme (0,43, sous la base 0,47) — la valeur concentre l'hostilité.
3. **L'horloge politique contre l'horloge militaire.** Plus une victoire est reconnue vite (tenue exigée courte),
   moins la guerre détruit : 93 % de fins politiques et 0 % d'annihilation à reconnaissance immédiate ; la
   condition politique devient lettre morte (6 %) quand sa validation est plus lente que la chute des capitales.
4. **« Renforcer le succès, pas l'échec ».** À ressources égales, la doctrine qui concentre sur sa pointe la plus
   forte (A) est **strictement dominante** : elle envahit les mondes égalitaire (0,76) et réactif (0,52), et rien
   ne l'envahit. La doctrine réactive — répondre à la menace adverse — est la pire partout : qui ne fait que
   répondre cède l'initiative.
5. **La guerre brûle son propre carburant.** Dès que le revenu vient de la population (économie endogène),
   l'annihilation s'effondre (0,37 → 0,09 en monde offensif) : morts et exodes détruisent la base fiscale avant
   que la conquête totale soit payable.
6. **Le coût civil est une propriété du monde doctrinal.** Monde égalitaire : 18 % de morts civils ; monde
   offensif : 37 %. La doctrine qui perd les guerres est celle qui protège les populations — l'arbitrage
   puissance/humanité devient une grandeur mesurable.
7. **Fuir la géographie, pas la menace.** Des civils dotés d'une politique de fuite **apprise** (RL, signal de
   survie pur) font −48 % de morts par rapport à la règle réactive : ils évacuent **préventivement** les lieux
   stratégiques (les collines-prix) avant l'arrivée des armées, et transfèrent dans tous les mondes non vus à
   l'entraînement. Le déplacement anticipatif observé dans les conflits réels émerge d'un simple signal de survie.
8. **Un micro-avantage tactique se propage en hégémonie stratégique.** Dans le couplage aux deux échelles, un
   biais de ~80 m au placement initial des unités — invisible à petite échelle — a produit un balayage 10/10 des
   guerres stratégiques par amplification (colline → territoire → trésor → forces). Le couplage révèle ce
   qu'aucune échelle isolée ne montre ; et la hiérarchie doctrinale, elle, **survit** au moteur réel une fois le
   biais neutralisé, la friction du réel adoucissant la domination (le faible y gagne ses premières victoires).
9. **La richesse rend la guerre totale.** Sur une carte de régimes de 48 conditions (~1,8 M de guerres) :
   à horloge politique fixe, l'enrichissement du monde fait exploser l'annihilation (0,77 → 0,93) — l'horloge
   militaire accélère, pas la politique. Exception : le monde égalitaire riche se **gèle** (paix par impuissance
   mutuelle). La hiérarchie doctrinale, elle, est invariante à la richesse.
10. **Le prédateur économique est co-dominant mais instable.** La doctrine du **déni de revenu** (frapper les
    régions peuplées adverses) fait jeu égal avec la doctrine offensive en écologie mixte (0,50/0,49) en dévorant
    l'égalitaire — mais le **bloc égalitaire collectif repousse le prédateur isolé** (0,06), et le réactif,
    perdant universel, **envahit le monde des prédateurs** (0,43). Sous un sommet stable, l'écologie des doctrines
    est non transitive — pierre-feuille-ciseaux stratégique.

# 5. Résultats II — l'escalade opérationnelle (152 opérations)

## 5.1 Le mirage du chiffre global

Une première campagne de 60 opérations (raid en cinq phases, deux plans : *appui d'abord* vs *assaut direct*)
avait conclu à une robustesse de 77 % indifférente au plan. La **décomposition conditionnelle** a montré que la
contre-attaque ennemie — l'épreuve centrale du scénario — n'avait été réellement affrontée que **3 fois sur 60**
(0/3), une contingence de délai escamotant la phase critique. Le vrai énoncé : *le raid réussit tant qu'il esquive
la contre-attaque*. Le chiffre était juste ; la conclusion était fausse. Sous-produit : les opérations qui
*saignent tôt* (contact avec les patrouilles loin de l'objectif) réussissent 30 points de plus que les approches
propres — la garnison engagée à distance est une garnison déjà entamée.

## 5.2 Trois hypothèses pré-enregistrées, trois verdicts

Les seuils ci-dessous ont été écrits et committés avant les données, références mesurées à l'appui.

**P-v2** — *« une fois la phase critique rendue atteignable, le succès s'effondre »* : **validée**. Consolidation
atteinte 71 % (contre 5 %) ; succès 12,5 % (contre 77 %). Les escouades échouent par **impuissance** (la
contre-attaque survit), non par anéantissement.

**H1** — *« face à une contre-attaque mécanisée, la doctrine d'appui surperforme »* : **réfutée** (A = B = 8 % ;
secondaires plates ou inverses). Trouvaille latérale : le blindé ne change pas le taux d'échec mais son **mode** —
d'impuissance à **saignée mutuelle** (le véhicule charge, meurt sous les armes antichar dans 58 % des cas, et
double les pertes amies en mourant).

**H2** — *« à quatre escouades, le coût de coordination explose »* : **réfutée par le haut**. Toutes les métriques
de coordination montent mais restent sous les seuils prédits ; le succès **triple** (25 % pour le plan
appui+réserve) contre un ennemi doublé ; surtout, **la consolidation — le tueur des paliers précédents — est tenue
13 fois sur 14, à une perte près**. La masse au bon moment vaut plus que la doctrine. Nouveau goulet, identifié et
chiffré : *atteindre* la consolidation (44 %) et l'horloge d'exfiltration (10 échecs sur 26 sont « administratifs » :
objectif détruit, pertes contenues, délai de repli dépassé — le taux de missions militairement accomplies est ~50 %).

## 5.3 Leçon transversale

Deux demi-échantillons successifs de la première campagne « prouvaient » des conclusions opposées (B dominant,
puis A) ; l'échantillon complet a rendu la parité. **À n = 15, on publie des erreurs — dans les deux sens.**
L'escalade n'a produit ses résultats que parce que chaque palier a été pré-enregistré, dimensionné, et jugé sur
des seuils antérieurs aux données.

# 6. La fiabilité de l'instrument : chasses aux biais

Quatre enquêtes, toutes parties d'une asymétrie inexpliquée dans un test de symétrie, toutes conclues par une
cause matérielle dans l'instrument — jamais par « le hasard » :

| Symptôme | Cause réelle | Leçon érigée en règle |
|---|---|---|
| Une faction gagne 19/19 à conditions égales | formule de placement étirant les files d'unités vers le nord-est (+80 m à 15 unités) | tout artefact d'échelle est invisible au petit effectif qui a servi à valider |
| Le pont moteur meurt après 8 commandes, chaque soir | une exception SQF dans une commande tue la boucle de l'actuateur ; des *heartbeats* tiers masquent la mort | le silence d'un composant n'est pas sa santé ; isoler chaque exécution |
| Le pays 0 gagne 45 % d'un monde symétrique | trois départages déterministes (`argmax`) : pointe d'attaque, fuite civile, **couronnement des vainqueurs simultanés** | *tout argmax est un tie-break déguisé ; tout tie-break déterministe est un biais en embuscade* — bruiter par défaut |
| Le véhicule de contre-attaque est invulnérable et immobile | signature d'API inversée : le véhicule **n'existait pas** ; les lectures reflétaient les valeurs d'initialisation | ne jamais confondre sa propre initialisation avec une mesure du monde |

S'y ajoute la règle de gestion : *jamais d'optimisation sans re-validation contre le run de référence* — une
« amélioration » de la marche d'assaut, appliquée sans re-test, a envoyé dix opérations défiler sous le feu.

# 7. Portée et limites

- **Ce sont les lois d'un modèle.** Aucun des énoncés de la section 4 ne doit être lu comme une découverte sur le
  monde réel. Ce que la note démontre : la capacité à formuler, instrumenter, falsifier et borner des hypothèses
  stratégiques — la méthode, pas la carte.
- **Les agents tactiques sont étroits** : un seul cerveau, entraîné sur un seul type d'engagement, généralisé par
  paramétrage d'objectif et biais de posture. Les civils du simulateur n'ont ni attachement, ni besoins, ni
  loyauté — chaque absence est une expérience future.
- **Les effectifs opérationnels restent modestes** (n = 16-30 par bras) : suffisants pour tuer des hypothèses aux
  seuils choisis, insuffisants pour des effets fins (l'écart A/B de 13 points du palier 2 demeure indécidé).
- **La comparabilité prime la performance** : tout tourne en environnement vanilla figé ; la porte des extensions
  (réalisme accru) reste fermée tant qu'un cycle de réentraînement dédié ne l'accompagne pas.

# 8. Programme

1. **Manager appris** : remplacer le chef d'opération scripté par une politique apprise (les exécutants restant
   gelés), entraînée à l'échelle stratégique puis validée en moteur — la baseline à battre est désormais chiffrée
   (25 %).
2. **Réparations de partition** : horloge d'exfiltration et complétion d'assaut (gains estimés : succès ~40-50 %).
3. **Palier 3** : opération complexe complète (échelle + blindés + patrouilles), maintenant que ses ingrédients
   sont isolés et compris.
4. **Côté stratégique** : coût de départ des populations civiles (le dilemme du déplacé), doctrines apprises par
   pays, cartes de régimes étendues.
5. **Démonstrateur visuel** : une opération de palier 2 en spectateur, chaque plan adossé à ses statistiques.

# Glossaire

**Partition** — le plan d'opération exécutable : la suite des phases, leurs ordres, leurs conditions de
transition et leurs contingences. C'est un objet *éditable* : les « réparations de partition » modifient le plan,
jamais le monde ni les agents.

**Phase** — un temps de l'opération (infiltration, mise en place, assaut, consolidation, exfiltration) défini par
des **ordres** par escouade et une **condition de sortie**.

**Horloge (ou budget) de phase** — le nombre maximal de pas accordé à une phase avant qu'une contingence ne
force la suite. Réalisme d'état-major (« l'extraction est à H+45 ») ; mal réglée, elle produit des **échecs
administratifs** : mission militairement accomplie, délai dépassé. L'**horloge globale** plafonne l'opération
entière et doit rester cohérente avec la somme des horloges de phase.

**Contingence** — règle de bascule conditionnelle (« pertes ≥ 25 % → engager la réserve », « assaut enlisé →
décrocher ») ; chaque déclenchement est journalisé avec sa raison.

**Posture** — modulation du comportement d'une escouade (approche, assaut, fixation, tenue) obtenue par biais des
préférences du cerveau gelé, sans réentraînement.

**Consolidation** — la phase de tenue de l'objectif conquis face à la contre-attaque (QRF) ; le verrou principal
identifié par l'escalade.

**QRF** (*Quick Reaction Force*) — la contre-attaque ennemie déclenchée par la prise de l'objectif ; infanterie ou
mécanisée selon le palier.

**Gabarit** — la configuration complète d'une campagne d'évaluation (géométrie, effectifs, ennemi, horloges,
critères) ; les comparaisons ne valent qu'à gabarit identique, d'où leur numérotation (v1, v2, v3).

**Pré-enregistrement** — l'écriture, avant le premier run, de la prédiction chiffrée et des seuils de décision ;
les références sont mesurées sur les données antérieures.

**Baseline** — le score de référence qu'une nouvelle méthode doit battre ; la partition scriptée v3 fournit celle
du futur manager appris.

**Horloges politique et militaire** (échelle stratégique, loi 3) — respectivement : le délai de reconnaissance
d'une victoire (tenue exigée des objectifs) et la vitesse à laquelle la force détruit (chute des capitales) ;
leur course relative décide si les guerres finissent par accord ou par annihilation.

# Annexe — inventaire des artefacts

| Artefact | Contenu |
|---|---|
| `geo_gpu.py`, `run_geo.py` | simulateur stratégique + harnais de mesure |
| `koth_gpu.py`, ligues `league_*.pt` | simulateur tactique GPU + cerveaux de ligue |
| `koth_finetuned.pt` | cerveau tactique affiné au feu réel (Arma) |
| `civ_learner.pt`, `train_civ.py` | politique civile apprise |
| `op_arma.py`, `run_op.py`, `wargame_op.py` | couche opérationnelle + harnais de wargaming |
| `wargame_*.jsonl` (5 fichiers) | 212 opérations journalisées (60 + 152) |
| `carte_regimes.txt` | 48 conditions × ~65 000 guerres |
| `MEMOIRE-COMMUNE.md` | journal autoritaire — chronologies honnêtes, erreurs incluses |
| `TROUVAILLES-2026-06-05.pdf` | dossier détaillé des dix lois (12 p.) |
| dépôt git + 5 bundles sur disque d'archive | traçabilité complète, chaque jalon committé |
