# Perception spatiale & combat collaboratif — Module théorique + cible SOTA 2026 + plan d'attaque

> Document de reprise autonome. Rédigé le 2026-06-13 (session Mac « architecte »).
> Objectif : permettre à **n'importe quelle session** (Mac ou workstation) de reprendre ce pivot sans relire la conversation.
> Registre : expert, mais chaque formule est suivie d'une traduction « en clair » (Younes n'est pas mathématicien).

---

## 0. POUR LA SESSION QUI REPREND — lis ça d'abord

**Le pivot en une phrase.** On donne aux agents la **perception du terrain** (relief, routes, bâtiments, couvert) pour qu'ils évoluent dans un monde qu'ils comprennent (suivre une route, prendre une crête, tenir un goulot). C'est le **complément direct** du pivot du 13/06 (« monde trop uniforme → rien à commander ») : enrichir le monde ne sert à rien si les agents ne le perçoivent pas. La perception du terrain rend le **commandement nécessaire** → sert le cap maître (commandement d'armée dans Arma). Validé par Younes : « très bien », « ça devient du combat collaboratif ».

**La barre fixée par Younes.** « Faire avec l'état des technos 2026 ce qu'il se fait de mieux. » Pas un truc qui marche — le meilleur. Recherche web faite le 13/06 (sources en §9).

**Où on en est.** Théorie exposée (8 piliers, §3) + cible SOTA 2026 identifiée (§4) + build recommandé (§5). Rien de codé pour la perception. Le sandbox rapide existe déjà (`koth_gpu.py`, `op_gpu.py`), c'est là que la perception se développe AVANT Arma.

**✅ FAISABILITÉ CONFIRMÉE (sonde du 13/06, `probe_gpu_terrain.py` + `probe_arma_v2.py`).** Les DEUX côtés du contrat sont remplissables :
- **Sandbox GPU** : pente (gradient) + couvert + LOS (ray-march vectorisé) pour 4096 envs × 8 agents × 8 ennemis = **166 ms (~24 700 envs/s), 1.6 Go VRAM**. La 3090 porte le terrain large.
- **Export Arma** : grille d'élévation 32×32 via `getTerrainHeightASL` en **0.040 s** (64×64 ≈ 0.16 s ; statique → pré-calcul UNE fois) ; routes via **`nearRoads`** (⚠️ PAS `nearestRoads`, syntaxe fausse) ; bâtiments via `nearestObjects`/`nearestTerrainObjects`. Autour de l'objectif Altis : relief ~9 m, 50 routes <300m, ~60-176 bâtiments = vraie structure.
- **Conclusion** : aucun bloqueur, le contrat (§6) est implémentable à l'identique des deux côtés → SCAR sim-to-real adressable. PROCHAIN PAS : figer le contrat (W=128m, c=2m → grille 64×64) puis G-perc-0.

**Par où démarrer (résumé, détail en §8).**
1. Graver la **fiche PhD de référence** (format validé, framework `arma3-marl-algos/phd.py`).
2. Spécifier le **contrat d'observation** (§6) — la pièce dont tout le code dépend.
3. Implémenter le contrat dans le sandbox GPU, puis un exporteur Arma miroir.

**Liens utiles (workstation `~/arma3-marl/`).** `MEMOIRE-COMMUNE.md` (mémoire partagée, tenir le JOURNAL), `VISION-COMMANDEMENT.md` (cap maître), `DOCTRINE-REPERTOIRE.md` (répertoire manœuvres). Code clé : `koth_gpu.py` (champ de bataille 100 % tenseurs cuda), `op_gpu.py` (sim opératif, « pile 1/5 »), `train_league_gpu.py` + `league_*.pt` (ligue PSRO/PFSP), `geometries.py` (5 géométries adversariales), `boucle_complete.py` (officier LLM GRPO), `socket_bridge/hmt_native.c` (pont TCP natif Arma, parké).

---

## 1. LE PIVOT — pourquoi la perception du terrain, maintenant

Constat du 13/06 : sur une colline unique avec une garnison, M3 domine partout → rien à arbitrer → l'officier-sélecteur ne vaut que +4.7 (marginal). Diagnostic : **le monde est trop uniforme**. La reconnaissance est morte (mesurée 3×) parce que toutes les postures se comportent pareil sous pression et que les défenses gardent la même géométrie.

La perception du terrain est la pièce qui referme ça : un monde avec relief/routes/bâtiments **et** des agents qui le perçoivent crée de vraies décisions (quelle route, quelle crête, quel goulot) — donc commander redevient nécessaire, donc le projet avance vers son cap (commandement d'armée).

C'est aussi ce qui fait passer « des agents qui tirent côte à côte » à du **combat collaboratif** : la coordination devient spatiale (feu et mouvement, prendre la hauteur, tenir un point de passage). Aucune de ces tactiques n'existe sans terrain perçu.

---

## 2. CADRE FORMEL (rappel)

Chaque agent ne reçoit pas l'état du monde `s` mais une **observation** `oᵢ = Oᵢ(s)` — une vue partielle filtrée par un « capteur ». « Percevoir le terrain » = **concevoir `Oᵢ`** pour exposer la structure spatiale.

Décision de fond : couper l'état en deux.

```
s = ( s_statique , s_dynamique )
     relief, routes,   alliés, ennemis,
     bâtiments, couvert   tirs, fumée
```

> **En clair.** Le monde a deux natures. Le décor (relief, routes, murs) ne bouge pas et est connu. Les acteurs (alliés, ennemis) bougent et sont en partie cachés. Presque toute la théorie qui suit découle de cette coupure.

Cadre global du projet (déjà verrouillé) : **Dec-POMDP coopératif sous contrainte (CMDP), résolu en CTDE**, équipe de 4 (1 chef manager + 3 spécialistes), récompense de survie au niveau ÉQUIPE, objectif = succès de mission sous contrainte pertes ≤ seuil.

---

## 3. LES 8 PILIERS THÉORIQUES

### Pilier 1 — Le repère : l'égocentrique est une symétrie, pas un confort
Si on fait pivoter tout le champ de bataille de 90°, la bonne décision pivote aussi : la guerre ne dépend pas du Nord. Formellement, il existe un groupe `G` (rotations, translations) qui laisse dynamique et récompense invariantes :

```
P(g·s′ | g·s, g·a) = P(s′ | s, a)      R(g·s, g·a) = R(s, a)
⇒ Q*(g·s, g·a) = Q*(s, a)      (homomorphisme de MDP, Ravindran & Barto)
```

> **En clair.** « Ennemi à 50 m sur ma droite derrière un muret » est UNE leçon, pas une leçon différente selon qu'on regarde au nord ou au sud. Une carte du monde (nord en haut) → le réseau voit 4 images et apprend 4 fois. Une vue centrée+orientée sur l'agent (devant = en haut) → 1 seule entrée, apprise une fois.

Gain : on divise le problème par le groupe de symétrie (≈ ×4 cardinal, bien plus en continu). Crucial sur une seule 3090.

### Pilier 2 — Statique vs dynamique = théorie de la croyance
En partiellement observable, la politique optimale dépend de tout l'historique, résumé par la **croyance** (statistique suffisante) :

```
bₜ(s) = P( sₜ = s | o₁:ₜ , a₁:ₜ₋₁ )
```

- Sur `s_statique` (relief, routes) : connu d'avance, constant → croyance = certitude → AUCUNE inférence/mémoire → injecté comme conditionnement « privilégié ».
- Sur `s_dynamique` (ennemis) : réellement incertain → là, et là seulement, il faut une vraie croyance, donc de la MÉMOIRE (récurrente/transformer).

> **En clair.** On n'a pas besoin de « se souvenir » où est la montagne. On a besoin de se souvenir où l'ennemi a disparu. La théorie dit OÙ dépenser la mémoire : sur ce qui bouge et se cache, jamais sur le décor.

### Pilier 3 — Quoi percevoir = une statistique suffisante pour la VALEUR
Une variable de terrain mérite d'être perçue ssi la valeur optimale en dépend. Appliqué au CMDP du projet :

| Calque | Quantité tactique | Objectif servi |
|---|---|---|
| relief / pente | ligne de vue, portée, défilement | engagement, observation |
| couvert / abris | proba de survie sous le feu | **la contrainte de pertes du CMDP** |
| routes | vitesse, tempo | rapidité de manœuvre |
| bâtiments | couvert dur + goulots | points décisifs |

> **En clair.** On choisit les calques parce que chacun répond à une question que l'agent doit trancher pour gagner SANS se faire tuer. Le couvert n'est pas décoratif : c'est le terme qui nourrit la contrainte λ sur les pertes.

### Pilier 4 — Comment encoder = apparier la symétrie de la donnée à celle du réseau (biais inductif)
- grille (terrain rasterisé) → **CNN** (partage de poids = équivariance par translation)
- ensemble d'entités (alliés/ennemis) → **Deep Sets / attention** (invariance par permutation : l'ordre des coéquipiers n'a pas de sens)
- topologie (réseau routier en graphe) → **GNN** (planification « suivre la route »)

> **En clair.** Chaque type d'information a sa lentille naturelle. Mauvaise lentille = échantillons gaspillés à réapprendre une structure connue. L'observation n'est donc pas UN tenseur mais plusieurs flux fusionnés. (NB : la version 2026 remplace ce bricolage par un encodeur tokenisé unique, voir §4.)

### Pilier 5 — « Suivre la route » = une option + un façonnage qui ne triche pas
**(a) Option (Sutton, SMDP).** Une option = `(I initiation, π_o politique, β_o arrêt)`. « Suivre la route R jusqu'au point P » : `π_o` = pathfinding du moteur (navmesh), `β_o` = arrivé ou contact. Le RL choisit des options, ne pilote pas les pas → c'est la hiérarchie manager-worker déjà verrouillée.

**(b) Façonnage par potentiel (Ng, Harada & Russell 1999).** Récompenser « +0,1 par pas sur une route » change l'optimum → l'agent flâne (Goodhart). La SEULE forme sûre :

```
F(s, s′) = γ·Φ(s′) − Φ(s)      laisse la politique optimale INCHANGÉE, ∀ Φ
```

Bon potentiel ici : `Φ(s) = − (distance le long du réseau routier jusqu'à l'objectif)`.

> **En clair.** On ne récompense pas « être sur une route » mais « avoir RAPPROCHÉ l'objectif en suivant le réseau ». Cette nuance sépare l'agent qui exploite la route comme un humain de celui qui farme des points en faisant des allers-retours sur le bitume.

### Pilier 6 — La coordination spatiale rouvre le crédit
Coopération spatiale (un fixe, l'autre déborde) → qui a causé la victoire ? Crédit contrefactuel (COMA / difference rewards) :

```
Aᵢ = Q(s, a) − Σ_{aᵢ′} πᵢ(aᵢ′) · Q(s, (a₋ᵢ, aᵢ′))
```

> **En clair.** « Est-ce que MON mouvement vers la crête a changé l'issue, ou l'équipe aurait gagné de toute façon ? » Empêche le « lazy agent » spatial (celui qui suit le groupe sans jamais prendre l'initiative d'un débordement).

### Pilier 7 — Généralisation : apprendre à LIRE le terrain, pas UNE carte
Sur une seule carte, l'agent mémorise une trajectoire au lieu d'une politique. L'écart de généralisation rétrécit avec la DIVERSITÉ des terrains. Cure = **PLR (Prioritized Level Replay)** + randomisation de domaine (déjà dans la besace du projet).

> **En clair.** Toujours la même colline → il apprend CETTE colline. L'égocentrique (Pilier 1) fait la moitié du travail ; varier le terrain fait l'autre. Perception du terrain et génération de niveaux = le même chantier vu de deux côtés.

### Pilier 8 — Sim-to-real : l'observation est un CONTRAT
SCAR n°1 du projet : manager 83 % sim → 0 % Arma (sur-apprend une fiction). Une politique est une fonction de son entrée ; si la distribution d'entrée change entre sandbox 2D et Arma, elle s'effondre. Donc `Oᵢ` (jeu de calques, résolution, taille de fenêtre, convention égocentrique) doit être **identique** dans les deux mondes — un contrat partagé, pas deux implémentations.

> **En clair.** La grille égocentrique n'est pas « le truc d'Arma ». C'est l'interface que le sandbox ET Arma remplissent à l'octet près. On la définit une fois ; le sandbox la produit en vectorisé (rapide, pour la 3090), Arma la produit pour de vrai.

---

## 4. CIBLE SOTA 2026 (la pile, mappée sur le projet)

Légende statut : **[déjà]** on l'a · **[upgrade]** à mettre à niveau · **[nouveau]** SOTA 2026 à intégrer.

1. **Encodeur = Perceiver / attention tokenisée multi-modale [nouveau].** On tokenise tout (patches de terrain, chaque entité, chaque variable) → attention croisée (Perceiver IO) → latent unique. PAS « CNN + colle » (ma version datée). Éprouvé : **a remplacé le Transformer d'AlphaStar à perf égale** → adapté à l'échelle StarCraft du projet ; gère un nombre variable d'entités nativement.

2. **Symétrie = équivariance PARTIELLE / canonicalisation locale [nouveau].** Découverte 2025 (PEnGUiN ; *Partially Equivariant RL in Symmetry-Breaking Environments*, déc. 2025) : **le terrain BRISE la symétrie** (obstacles, objectif, repères) → équivariance pleine = contre-productive. SOTA = **score de symétrie appris** qui interpole équivariant (espace libre, permutations d'alliés) ↔ libre (terrain). Le repère égocentrique reste le gain « 90 % gratuit ». *Ironie utile : la chose qu'on veut ajouter (terrain) est ce qui casse la symétrie → l'outil de pointe est celui inventé pour ce cas.*

3. **Mémoire/croyance = Spatially-Aware Transformer / Neural Map [nouveau].** Mémoire indexée par LIEU (pas par temps) pour le dynamique caché (ennemi vu en dernier). Implémente le Pilier 2.

4. **Politique jointe / CTDE = famille Multi-Agent Transformer (MAT / AOAD-MAT 2025) [upgrade].** Remplace les critiques CTDE faits main. AOAD-MAT apprend **l'ordre dans lequel les agents décident** = la hiérarchie « le chef décide d'abord » rendue apprenable. TransMix = mixing transformer (lignée QMIX/décompo de valeur).

5. **Efficacité-échantillon = modèle du monde latent (lignée Dreamer) [nouveau].** Apprendre un modèle latent de la dynamique, puis s'entraîner « en imagination » : **×10 à ×100 en échantillons**. Variantes 2026 SANS reconstruction de pixels (MuDreamer, M3PO) → on ne modélise que le latent + la récompense, parfait puisque le terrain est connu. *Le levier le plus rentable pour une seule 3090 ET pour le budget sim-to-real (moins de pas Arma coûteux).* Mixture-of-world-models ↔ multi-théâtre Arma/CMO/DCS.

6. **Généralisation = PLR + randomisation terrain/spawns/types façon SMACv2 [déjà].** SMACv2 randomise types et points d'apparition pour tuer le surapprentissage d'une carte (Pilier 7) ; SMAC-HARD = ennemis hybrides (↔ notre ligue adaptative). Le champ a institutionnalisé ce qu'on fait déjà.

7. **Sommet = officier LLM + modèle du monde [déjà].** C'est la forme exacte de la frontière « embodied AI » 2025-26 (survey Tsinghua « des LLM aux modèles du monde »). Notre archi LLM-officier est alignée frontière, pas à côté.

**ANTI-HYPE (à éviter même si c'est 2026) :**
- Modèle du monde à **reconstruction de pixels** → gaspille la capacité sur un terrain connu ; prendre la variante latente sans reconstruction.
- **Équivariance pleine** → sous-optimale dès qu'il y a du terrain ; partielle uniquement.
- **Gros modèles fondation spatiaux** (Genie, etc.) → spectaculaires mais ne tiennent pas sur une 3090 ; pas le point d'entrée.

---

## 5. BUILD RÉALISTE RECOMMANDÉ

**Chaîne de décision (exécution) :**
```
observation égocentrique (contrat sim↔Arma)
   → encodeur Perceiver tokenisé  +  équivariance partielle
   → petite mémoire spatiale (lieu-centrique) pour le dynamique caché
   → politique CTDE type MAT
le tout sous : CMDP (contrainte pertes) · ligue PSRO/PFSP · PLR/randomisation
côté entraînement : modèle du monde latent (Dreamer) pour l'efficacité-échantillon
au sommet : officier LLM (raisonnement haut niveau, explicable)
```

**Feuille de route GATÉE (chaque marche calibrée anti-fiction, comme les briques précédentes) :**
- **G-perc-0 — Variables seules.** dist/cap route, pente sous les pieds, distance au couvert, LOS ennemi oui/non. Pas cher, fait tourner le pipeline, BASE DE RÉFÉRENCE. Gate : le pipeline tourne, métrique stable.
- **G-perc-1 — Fenêtre égocentrique + encodeur tokenisé.** Ajouter la grille (calques §3) + encodeur Perceiver. Gate : bat les variables seules sur une tâche de navigation/manœuvre.
- **G-perc-2 — Équivariance partielle + mémoire spatiale.** Gate : généralisation à des terrains non vus (randomisation/PLR) sans chute.
- **G-perc-3 — Modèle du monde latent.** Gate : même perf avec ×10 moins de pas réels.
- **G-perc-4 — Calibration sim→Arma.** Le contrat d'obs produit par Arma = par le sandbox (Pilier 8). Gate : pas d'effondrement 83→0.

⚠️ Discipline : on développe d'abord dans le **sandbox GPU rapide** (`koth_gpu.py`/`op_gpu.py`), JAMAIS directement dans Arma (chaque mécanique se calibre sur données Arma, leçon op_gpu calibré sur 200 ops).

---

## 6. LE CONTRAT D'OBSERVATION (premier artefact à spécifier — commence ici pour coder)

À figer noir sur blanc, partagé sandbox↔Arma (esquisse, à valider avec Younes) :

- **Repère** : égocentrique, orienté cap (devant = +y/haut). Origine = position de l'agent.
- **Fenêtre** : carré de côté `W` mètres centré sur l'agent (proposition : W = 128 m, à trancher selon la portée tactique utile).
- **Résolution** : cellule de `c` mètres (proposition : c = 2 m → grille 64×64, à trancher selon mémoire/portée).
- **Calques statiques** (canaux d'image) : élévation normalisée, pente, masque route, masque bâtiment, masque couvert. Pré-calculés UNE fois → cache numpy ; à chaque pas on DÉCOUPE la fenêtre locale (jamais de requête terrain live).
- **Couche dynamique** (overlay ou tokens d'entités) : alliés, ennemis vus, tirs/menaces, fumée. Seule lue en direct.
- **Variables vectorielles** : cap, vitesse, état (PV/munitions), bearing+distance à l'objectif, rôle (embedding).
- **Normalisation** : identique des deux côtés (mêmes échelles, même clipping).
- **Tokenisation** (pour l'encodeur Perceiver) : patches de terrain → tokens ; chaque entité → 1 token ; variables → tokens. Encodage positionnel relatif (égocentrique).

Où l'implémenter : côté sandbox dans `koth_gpu.py`/`op_gpu.py` (vectorisé, sur la 3090) ; côté Arma via le pont (`socket_bridge/hmt_native.c` + sérialiseur d'état) — exporteur miroir produisant EXACTEMENT le même format.

---

## 7. DÉCISIONS OUVERTES (à trancher avec Younes)

1. **Taille de fenêtre `W` et résolution `c`** (compromis portée tactique ↔ mémoire/3090).
2. **Méthode d'export terrain Arma → grille numpy** (SQF `getTerrainHeightASL`/`nearestTerrainObjects`/`roadsConnectedTo` vs extension ; pré-calcul offline à l'ouverture de mission).
3. **Dynamique : overlay sur la grille OU tokens d'entités séparés** (le Perceiver permet les deux ; tokens = plus propre pour nb variable).
4. **Mémoire spatiale : Neural Map explicite vs transformer spatialement conscient** (coût mémoire sur 3090).
5. **Modèle du monde : maintenant ou après G-perc-2 ?** (gros chantier ; peut attendre que l'encodeur soit validé).
6. **Ordre des chantiers** : graver la fiche d'abord, ou coder le contrat d'abord ?

---

## 8. COMMENT DÉMARRER LA PROCHAINE SESSION (action items)

**Option A — graver la fiche de référence (recommandé en premier, c'est l'ancre).**
- Fiche PhD « Module : perception spatiale, SOTA 2026 » dans le format validé (formule → en clair → image → philo).
- Réutiliser le framework `arma3-marl-algos/phd.py` (CSS + équations mathtext→PNG + figures matplotlib + `build_fiche`). Voir `_build_fiche09.py` comme modèle.
- ⚠️ Pièges PDF connus : chemin ABSOLU dans l'URL `file://` de Chrome ; SUPPRIMER le PDF cible avant de relancer Chrome ; attendre que le PDF soit stable puis killer Chrome (il ne sort pas seul) ; mathtext = `\mathrm` pas `\text`, `\leq` pas `\le`.
- Contenu = §1–§6 de ce document, mis en forme.

**Option B — spécifier puis coder le contrat d'observation.**
- Figer §6 avec Younes (trancher W, c, overlay vs tokens).
- Implémenter le producteur d'observation dans le sandbox GPU (vectorisé torch, sur cuda:0 = 3090 = index nvidia-smi 1).
- Écrire l'exporteur Arma miroir (stub d'abord) qui produit le même format.
- Test : mêmes positions → même tenseur d'obs des deux côtés (garde-fou sim-to-real).

**Préliminaire commun.** Lire `MEMOIRE-COMMUNE.md` (état à jour, JOURNAL) et `VISION-COMMANDEMENT.md`. Vérifier l'état de la flotte/3090 avant tout entraînement (fuite mémoire ~3.8 Go/serveur, reboot préventif `multi_server.sh` ; 3090 plafonnée 315 W `set_3090_powerlimit.sh`).

---

## 9. BIBLIOGRAPHIE (recherche web du 13/06/2026)

- Perceiver IO — architecture générale, remplace le Transformer d'AlphaStar à perf égale : https://arxiv.org/pdf/2107.14795
- AOAD-MAT — Multi-Agent Transformer avec ordre de décision appris (2025) : https://arxiv.org/html/2510.13343v1
- Partially Equivariant RL in Symmetry-Breaking Environments (déc. 2025) : https://arxiv.org/pdf/2512.00915
- PEnGUiN — réseaux partiellement équivariants à « score de symétrie » (2025) : https://www.researchgate.net/publication/395649444_Local-Canonicalization_Equivariant_Graph_Neural_Networks_for_Sample-Efficient_and_Generalizable_Swarm_Robot_Control
- S5WM — successeur de DreamerV3 (modèles du monde, 2025) : https://arxiv.org/html/2502.20168v1
- Spatially-Aware Transformer for Embodied Agents : https://arxiv.org/html/2402.15160v3
- From Memories to Maps — mécanismes du RL en contexte chez les transformers (2025) : https://arxiv.org/pdf/2506.19686
- Embodied AI: des LLM aux modèles du monde — survey Tsinghua (Q4 2025) : https://mn.cs.tsinghua.edu.cn/xinwang/PDF/papers/2025_Embodied%20AI%20from%20LLMs%20to%20World%20Models.pdf

Fondations (antérieures, citées dans les piliers) : Ravindran & Barto (homomorphismes de MDP) ; Sutton et al. (options/SMDP) ; Ng, Harada & Russell 1999 (façonnage par potentiel) ; Foerster et al. (COMA) ; Hafner et al. (DreamerV3).
