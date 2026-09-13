# Ce que le moteur d'Arma dit de lui-même : la portée dépend de la lunette, et le tir dépend d'une position

*Verdict du 13/09/2026. Source : récolte ARMA3_RECOLTE, configs dérapifiées et chaînes du binaire serveur,
build du 24/06/2025. Six lecteurs, dix-neuf vérifications adverses.*

## 1. La portée d'engagement n'est pas une propriété de l'arme, mais du couple arme + lunette

Chaque mode de tir déclare `minRange / midRange / maxRange` et trois probabilités. Mais un mode
n'est **utilisable** que si la lunette montée porte le bon `requiredOpticType`. Onze classes
seulement portent `opticType` dans tout le jeu. **Les collimateurs ACO n'en portent aucun.**

| Unité | Arme + lunette | Portée où p ≥ 0,5 |
|---|---|---|
| `B_recon_M_F` (appui CHACAL) | MXM + DMS (opticType 2) | **0 à 626 m**, plateaux à 0,70 vers 250, 450 et 550 m |
| `B_Soldier_F` (assaut CHACAL) | MX + **ACO** | **400 m au maximum**, p < 0,5 dès 300 m |
| `O_Soldier_F` (garnison) | Katiba + **ACO** | **400 m au maximum**, p < 0,5 dès 300 m |
| `O_Sharpshooter_F` (guetteur) | DMR_05 + KHS (opticType 2) | seule pièce de la garnison au-delà de 400 m, 0,80 à 300 m |

`aiMaxRange` n'existe sur aucune arme d'infanterie : le plafond est le `maxRange` du mode.
Le silencieux ne change rien aux portées (tous ses coefficients valent 1).

**Ce que cela change.** La mesure du labo du 12/09 — 32 coups à 300 m, 23 à 450, 0 à 600 — n'était
pas un accident : c'est la table du moteur. Et l'appui de CHACAL, posté à 500 ou 779 m, était hors
de portée par construction. La bonne distance est **250 à 550 m**, et elle est maintenant un nombre.

## 2. Le tir passe par une POSITION, et couper PATH coupe cette position

Trois choses lues dans le binaire, dans cet ordre :

- Le bloc d'état de combat range deux positions d'attaque **entre** la cible et l'état de tir :
  `attackTarget`, `attackAggresivePos`, `attackEconomicalPos`, puis `fireState`.
  **Le moteur choisit d'où tirer avant d'armer le tir.**
- Le catalogue de tâches contient un état nommé **« Bad attack pos »**, dont tous les voisins
  immédiats sont des déplacements. La sortie de cet état est un mouvement.
- `COVER` et `PATH` partagent le même objet d'état : `wantedPositionCover`, `noPath`, `updatePath`,
  `exposureChange` vivent dans le même bloc.

**Conséquence.** Un homme sous `disableAI "PATH"` qui n'a pas de ligne de vue au départ est bloqué
dans « ma position est mauvaise pour attaquer », et la seule sortie lui est interdite. C'est le
mécanisme derrière la mesure du 12/09 : cloué sans vue initiale, 0 tir sur 4 ; libre, 2 fois sur 3.

Deux corollaires qui vont à l'encontre de l'intuition :
- **L'intention de Bohemia est l'inverse.** Sur 55 usages de `disableAI "PATH"` dans son code, 47
  sont sur la même ligne qu'un `setUnitPos` et un `setDir` : l'idiome du garde planté qui doit
  continuer à se battre. La mesure contredit l'intention.
- **Figer AMÉLIORE la visée.** Le composant `AIBrainAimingErrorComponent` porte `movingInfluence`
  et `turningInfluence` : un homme immobile a une erreur de visée plus faible. Le problème n'est
  donc pas la visée, c'est le placement.

**Remède à mesurer** : `forceSpeed 0` ou `doStop` écrivent dans les drapeaux d'entité
(`isStopped`, `userStopped`, `limitSpeedForced`), pas dans le masque de facultés. Ils n'atteignent
ni le planificateur ni le cerveau. Mesure du 12/09 au labo : `doStop` tire 3 fois sur 5.

## 3. Quatre pièges d'instrument, à corriger avant toute nouvelle ablation

1. **La liste des neuf `disableAI` est périmée.** C'est la chaîne d'aide, pas la table du moteur.
   La vraie énumération (0x018eec68) contient six noms de plus, et le code de Bohemia en passe
   dix-huit, dont `PATH` (60 usages) et `ANIM` (121), absents de l'aide.
2. **`setHideBehind` n'est pas implémentée** côté unité : « MicroAI: Command setHideBehind not
   implemented ». Un contrôle positif sur `COVER` bâti dessus serait muet sans rien signaler.
3. **`setWaypointForceBehaviour` coupe `AUTOCOMBAT`** à l'insu du banc. À vérifier dans la mise en
   place de la garnison avant d'attribuer un effet à une ablation.
4. **`knowsAbout` rend zéro dans deux cas indiscernables** : « je ne vois rien » et « cette cible
   n'est pas dans ma liste » (décompilation : 166 octets, recherche dans la liste, zéro si échec).

## 4. La porte de localité est POSÉE, et elle passe

La phrase du moteur — « les unités qui ne sont pas dans un groupe comptant au moins un membre local
ne vérifient pas la visibilité des autres unités » — est le **texte d'aide de `disableRemoteSensors`**,
une optimisation qu'une mission doit activer elle-même. Zéro occurrence dans tout HARMATTAN, ni dans
les mods CBA et LAMBS. Et la ferme n'a aucun client headless : `isDedicated=true`,
`CBA_isHeadlessClient=false`, `hasInterface=false`, zéro processus client.

**Toutes les unités sont locales au serveur. Les verdicts appuyés sur `knowsAbout` tiennent.**

## 5. Deux nombres pour la nuit et pour la suppression

- **Détection de nuit.** Un défenseur en garnison sans jumelles détecte un assaillant qui marche à
  36 m en médiane, trois quarts des cas sous 120 m, presque jamais au-delà de 250 m. Mais 73 % des
  premières détections passent par un autre canal que ses yeux.
- **Suppression.** Elle n'est alimentée que si les balles passent à moins de 6 m du défenseur
  (`suppressionRadiusBulletClose`) ou frappent à moins de 8 m (`suppressionRadiusHit`, munition
  6,5 mm). Tirer vaguement vers un bâtiment ne supprime personne.

## 6. La géométrie du site, côté postes

Le site de CHACAL offre 29 postes de tir intérieurs : 13 dans le seul `Cargo_HQ`, 1 par maison,
2 dans la tour, 3 par bunker, et **zéro sur les 31 segments d'enceinte**. Les défenseurs sont donc
concentrés dans quatre bâtiments, et l'enceinte n'est qu'un masque, jamais un poste.

## Ce que ce verdict ne dit pas

Ce sont des **paramètres**, pas des connaissances : ils disent comment le moteur est réglé, pas ce
que le combat fait. La formule exacte d'interpolation entre `minRange`, `midRange` et `maxRange`
n'est pas établie — un segment linéaire par morceaux est une hypothèse, pas une lecture. Et aucune
chaîne du binaire ne dit ce que `PATH` fait : le mécanisme du point 2 est une déduction structurelle
appuyée sur l'ordre des champs et sur une mesure, pas une déclaration du moteur.
