# Conception d'une IA matricielle pour soldats autonomes — document de travail

*Écrit le 01/08/2026. Ancré sur ce que le projet a MESURÉ, pas sur ce qu'on lit ailleurs.
Chaque fois qu'une constante de ce document vient d'une mesure maison, elle est signalée
par ⟨mesuré⟩ avec sa date.*

---

## 0. Trois corrections préalables au cadrage

Avant les douze sections, trois choses que nos mesures imposent et qui contredisent le
plan naïf.

**(a) Dans Arma, on n'apprend pas à marcher.** Le moteur fait la locomotion. Vouloir la
commander produit exactement le désastre mesuré ⟨31/07⟩ : nos exécuteurs réémettaient un
ordre de déplacement toutes les 3,3 s, ce qui écrase la réaction de survie de l'IA
tactique ; avec un seul ordre, une escouade s'arrête à 102 m d'une position tenue et perd
la moitié de ses hommes sans avancer. L'apprentissage moteur est le chemin **Isaac**
(corps articulé, couple aux articulations). Dans Arma l'agent émet des **intentions** et
le moteur résout le corps. Les deux mondes ne partagent pas la même couche d'action ; ils
partagent l'étage au-dessus, et c'est précisément ce qui rend le transfert possible.

**(b) Le plafond de parallélisme est douze, pas cinq mille.** ⟨mesuré 31/07⟩ Une instance
à 240 entités coûte 6,7 ms par tick d'émetteur et 15 % de FPS serveur ; douze instances
consomment 51 Go sur 60 et 17 à 19 fils sur 24. Au-delà, l'horloge de simulation dérape
(2,19 % de pas hors bande mesurés sous charge) et le corpus devient inutilisable. Ce
plafond n'est pas une limite d'ingénierie à contourner : c'est **la raison d'être du
modèle du monde**.

**(c) La récompense façonnée à la main enseigne des bêtises.** ⟨mesuré 29/07⟩ Un terme
d'exposition soustrait par pas a produit une politique qui apprenait l'immobilité : 0 %
de réussite correctement ordonnée contre 23 % pour la politique mal ordonnée. La
récompense doit venir de **verdicts**, pas de sculptures.

---

## 1. Pourquoi les matrices sont le cœur de l'IA

### 1.1 Ce qu'est une matrice, et pourquoi c'est le bon objet

Une matrice est un tableau de nombres à deux indices, `A ∈ ℝ^{m×n}`. Mais sa nature
profonde n'est pas d'être un tableau : c'est d'être **la représentation d'une application
linéaire** entre deux espaces vectoriels. `A` prend un vecteur de ℝⁿ et rend un vecteur
de ℝᵐ :

```
(Ax)_i = Σ_{j=1}^{n} A_{ij} x_j
```

Toute application linéaire entre espaces de dimension finie EST une matrice, et
réciproquement. C'est le théorème qui fonde tout le reste.

Pourquoi la linéarité ? Parce qu'elle est la seule classe d'applications qui soit à la
fois **assez riche pour mélanger l'information** (chaque sortie voit toutes les entrées)
et **assez pauvre pour être calculable vite** (le coût est un produit de dimensions, pas
une explosion combinatoire).

### 1.2 Vecteurs, matrices, tenseurs

```
scalaire   x ∈ ℝ                  0 indice     la température
vecteur    v ∈ ℝⁿ                 1 indice     l'état d'UN soldat
matrice    A ∈ ℝ^{m×n}            2 indices    l'état de m soldats à n variables
tenseur    T ∈ ℝ^{b×t×m×n}        k indices    b batches × t instants × m soldats × n variables
```

Un tenseur n'est pas un objet mystérieux : c'est un tableau à plus de deux indices. Dans
notre code, l'observation d'un lot est un tenseur `(B, T, F)` — B séquences, T pas de
temps, F nombres par pas. ⟨notre modèle : B=192, T=50, F=92⟩

### 1.3 Pourquoi les GPU

Un produit matriciel `C = AB` avec `A ∈ ℝ^{m×k}`, `B ∈ ℝ^{k×n}` demande `m·n·k`
multiplications-additions, **toutes indépendantes**. C'est le cas idéal du parallélisme
de données : mille cœurs peuvent calculer mille éléments de `C` sans jamais se parler.

Un processeur classique a une dizaine de cœurs très intelligents (prédiction de
branchement, exécution dans le désordre, gros caches). Un GPU a des milliers de cœurs
stupides et un débit mémoire énorme. Pour un `if` compliqué, le processeur gagne. Pour
`m·n·k` multiplications identiques, le GPU gagne d'un facteur cent.

**L'intensité arithmétique** est la quantité qui décide :

```
I = (opérations) / (octets lus)    ;   pour C = AB :  I ≈ (2mnk) / (4(mk + kn + mn))
```

Quand `I` est grand, on est limité par le calcul (bon) ; quand `I` est petit, par la
mémoire (mauvais). Un produit matriciel de grande taille a une intensité élevée : c'est
pour ça qu'il sature un GPU.

**Conséquence pratique mesurée chez nous** ⟨31/07⟩ : notre modèle passe le même temps par
pas avec un lot de 32 et un lot de 192. Le goulot n'était donc pas le calcul mais le
**lancement des noyaux** — cinquante pas de séquence × une dizaine d'opérations = cinq
cents lancements minuscules. Multiplier le lot par six a multiplié le débit par six,
gratuitement. C'est la leçon d'intensité arithmétique appliquée.

### 1.4 CUDA et les cœurs tensoriels

CUDA est le modèle de programmation : on décrit ce que fait **un** fil, et on lance une
grille de milliers de fils. Les **cœurs tensoriels** vont plus loin : ce sont des unités
matérielles qui exécutent en une instruction un petit produit matriciel accumulé, typiquement

```
D = A·B + C     avec A, B en 16 bits et l'accumulation en 32 bits
```

Le gain vient de deux choses : moins de bits déplacés (la mémoire est le vrai coût), et
une opération de granularité plus grosse (moins de lancements). L'accumulation reste en
32 bits parce que c'est la somme qui perd de la précision, pas les facteurs.

### 1.5 Un réseau de neurones EST une suite de produits matriciels

Une couche dense :

```
h^{(l+1)} = σ( W^{(l)} h^{(l)} + b^{(l)} )
```

Sans la non-linéarité `σ`, empiler des couches ne sert à rien :
`W₂(W₁x) = (W₂W₁)x` — deux couches linéaires valent une seule matrice. **C'est `σ` qui
crée la profondeur.** Le théorème d'approximation universelle dit qu'une seule couche
cachée assez large approche n'importe quelle fonction continue ; la pratique dit que la
profondeur y arrive avec exponentiellement moins de paramètres.

Même l'attention, qui a l'air d'autre chose, est trois produits matriciels et un softmax :

```
Q = X W_Q ,  K = X W_K ,  V = X W_V
Attention(Q,K,V) = softmax( Q Kᵀ / √d_k ) V
```

Le `√d_k` n'est pas cosmétique : sans lui, la variance de `q·k` croît comme `d_k`, le
softmax sature, et le gradient meurt.

---

## 2. Représentation d'un soldat

### 2.1 Le principe : tout devient un vecteur, mais pas n'importe comment

Trois règles, chacune payée par une erreur mesurée.

**Règle 1 — normaliser dans la plage utile, sans compression.** ⟨mesuré 31/07⟩ Nous
avions appliqué `symlog` aux positions, transformation faite pour des grandeurs non
bornées. Elle écrase les grandes valeurs et rendait une erreur d'un mètre invisible face
aux drapeaux vivant/mort. Les positions vivent dans une arène bornée : échelle **linéaire**.

**Règle 2 — distinguer l'absence de la valeur zéro.** ⟨mesuré 01/08⟩ 18,5 % des places
d'attaquant de nos tenseurs étaient vides, remplies de zéros, drapeau « vivant » à zéro
compris. Le modèle apprenait à déclarer morts des hommes qui n'existent pas. Il faut un
**drapeau de présence** explicite et un masque dans la perte.

**Règle 3 — les angles ne se représentent pas par un nombre.** Un cap de 359° et un cap
de 1° sont voisins mais numériquement opposés. On encode `(cos θ, sin θ)`.

### 2.2 Le vecteur d'un soldat

```
CINÉMATIQUE (12)
  position          x, y, z            / 100 m            3
  vitesse           vx, vy, vz         / 6 m·s⁻¹          3
  cap               cos θ, sin θ                          2
  tangage/roulis    cos φ, sin φ, cos ψ, sin ψ            4

CORPS (8)
  posture           debout/accroupi/couché  (one-hot)     3
  santé             1 − dégâts                            1
  fatigue           ∈ [0,1]                               1
  souffle           ∈ [0,1]                               1
  charge portée     / 30 kg                               1
  blessure locale   max sur parties du corps              1

ARMEMENT (10)
  munitions chargeur / capacité                           1
  chargeurs restants / 8                                  1
  type d'arme        (one-hot 5)                          5
  arme épaulée / rangée                                   1
  temps depuis le dernier tir  exp(−Δt/τ)                 1
  temps depuis le dernier rechargement                    1

PERCEPTION (14)
  connaissance de l'ennemi le plus proche ∈ [0,4] / 4      1
  distance à cet ennemi   ⟨falaise à 100 m, cf. 2.3⟩       1
  gisement de cet ennemi  cos, sin                         2
  nombre d'ennemis connus / 8                              1
  nombre d'alliés vivants / 12                             1
  distance au chef                                         1
  a-t-on été touché récemment  exp(−Δt/τ)                  1
  a-t-on entendu un tir proche récemment                   1
  suppression subie ∈ [0,1]  ⟨courbe n°2 mesurée⟩          1
  ligne de vue vers l'objectif  0/1                        1
  ...

TERRAIN LOCAL, en coque radiale (24)
  12 rayons de 30 m : distance au premier obstacle        12
  12 rayons : hauteur du couvert le long du rayon         12
  ⟨la « coque » a été mesurée le 24/07 : +97 % de couvert⟩

CONTEXTE DE MISSION (8)
  verbe de mission (PRENDRE/TENIR/EXTRAIRE/INFILTRER)      4
  distance à l'objectif / 200 m                            1
  temps écoulé / durée max                                 1
  budget de pertes restant                                 1
  budget de temps restant                                  1
```

Total ≈ **76 nombres par soldat**. Ce n'est pas beaucoup — et c'est volontaire. Chaque
nombre ajouté est une dimension de plus à apprendre avec les mêmes données.

### 2.3 Deux constantes du monde, mesurées, qui doivent être dans la représentation

**La falaise de conscience** ⟨mesuré 30/07 sur Arma⟩ : la connaissance qu'un défenseur a
d'un attaquant vaut 4,00 (saturée) sous 30 m, et **0,00 au-delà de 100 m**. La transition
est brutale, et elle est **insensible au mouvement** : un homme qui court est détecté à la
même distance qu'un homme immobile. En revanche, courir **comprime la durée** d'exposition.

```
   connaissance
   4 ┤■■■■■■■■
     │        ╲
   2 ┤         ╲
     │          ╲
   0 ┤           ■■■■■■■■■■■■■■■■
     └──┬────┬───┬────┬────┬─────  distance
        30   60  100  150  200
```

**La courbe de toucher** ⟨mesuré 28/07⟩ : probabilité de toucher par tir, de 75 % à 25 m
à 26 % à 200 m. Se coucher divise par 1,4 — pas par 5, comme on le croyait.

Ces deux constantes ne sont pas des paramètres à apprendre : elles sont **la physique du
monde**, et un modèle du monde qui ne les reproduit pas est faux.

---

## 3. Construction des matrices

### 3.1 Le principe : une matrice par ensemble d'entités homogènes

```
X_soldats    ∈ ℝ^{N_s × F_s}     N_s = 100 soldats,   F_s = 76
X_ennemis    ∈ ℝ^{N_e × F_e}     N_e = 100,           F_e = 76 (masqué par la connaissance)
X_bâtiments  ∈ ℝ^{N_b × F_b}     N_b = 500,           F_b = 24 (position, emprise, ouvertures)
X_véhicules  ∈ ℝ^{N_v × F_v}     N_v = 100,           F_v = 40
X_objectifs  ∈ ℝ^{N_o × F_o}     N_o = 8,             F_o = 12
```

**Le piège de la dimension.** Une matrice `100 × 76` fait 7 600 nombres. Une matrice
d'interaction `100 × 100` en fait 10 000 — et elle croît en `N²`. À 1 000 soldats, la
matrice d'interaction fait un million d'entrées **par pas de temps**. C'est là que les
architectures naïves meurent.

### 3.2 Les matrices d'interaction, et comment les rendre calculables

**Visibilité** `V ∈ {0,1}^{N_s × N_e}` : `V_ij = 1` si le soldat i voit l'ennemi j.
Coût naïf : `N_s · N_e` lancers de rayon par pas. À 100 × 100 et 5 Hz, c'est 50 000
lancers par seconde — impraticable.

*Solution* : la falaise à 100 m rend `V_ij = 0` pour toute paire au-delà. On indexe donc
les entités dans une **grille spatiale** de maille 100 m et on ne teste que les paires
d'une même cellule ou de cellules voisines. Le coût passe de `O(N²)` à `O(N·k)` avec
`k` le nombre moyen de voisins.

**Bruit** `S ∈ ℝ^{N_s × N_s}` : `S_ij = A_j · exp(−d_ij / λ)`, atténuation exponentielle
de l'amplitude d'un tir. Même astuce de grille, avec un rayon de coupure à `3λ`.

**Thermique** `T ∈ ℝ^{H × W}` : une image, pas une matrice d'interaction. Elle se traite
avec un petit encodeur convolutif si un jour on a des optiques thermiques.

**Communications** `C ∈ {0,1}^{N_s × N_s}` : qui peut parler à qui. Souvent une matrice
de blocs (escouade, section, compagnie) plus une portée radio.

**Météo** : ce n'est PAS une matrice, c'est un vecteur global de 6 nombres — vent,
pluie, brouillard, luminosité, heure, température. Le faire tenir dans une matrice serait
du gaspillage. *Une bonne conception distingue ce qui est par-entité, par-paire, ou global.*

### 3.3 Le graphe plutôt que la matrice dense

Au-delà de quelques dizaines d'entités, la bonne représentation n'est plus une matrice
dense mais un **graphe creux** :

```
G = (V, E)     V = entités             |V| = N
               E = paires en interaction  |E| ≈ k·N  avec k ≪ N
```

Les matrices d'interaction deviennent des **listes d'arêtes** avec leurs attributs. C'est
ce qui rend praticables les centaines d'agents, et c'est le fondement des réseaux de
neurones sur graphes (§8).

---

## 4. Architecture neuronale

### 4.1 Le squelette

```
   ┌──────────────────────────────────────────────────────────────┐
   │  ENCODEURS PAR TYPE (poids partagés dans un type)            │
   │                                                              │
   │  soldats    ──► MLP_s ──┐                                    │
   │  ennemis    ──► MLP_e ──┤                                    │
   │  bâtiments  ──► MLP_b ──┼──► agrégation permutation-invariante│
   │  véhicules  ──► MLP_v ──┤     (somme ou attention)           │
   │  terrain    ──► MLP_t ──┘                                    │
   └───────────────────────────┬──────────────────────────────────┘
                               │  e_t ∈ ℝ^{256}
   ┌───────────────────────────▼──────────────────────────────────┐
   │  MÉMOIRE RÉCURRENTE — modèle latent d'état                   │
   │                                                              │
   │     h_t = GRU( [s_{t-1}, a_{t-1}] , h_{t-1} )     déterministe│
   │     s_t ~ q( · | h_t , e_t )                       a posteriori│
   │     ŝ_t ~ p( · | h_t )                              a priori  │
   └───────────────────────────┬──────────────────────────────────┘
                               │  (h_t , s_t)
        ┌──────────────────────┼──────────────────────┐
        ▼                      ▼                      ▼
   décodeur              tête de valeur         tête de politique
   (reconstruit)         V(h,s)                 π(a | h,s)
```

### 4.2 Pourquoi chaque pièce, et ce qu'on a payé pour l'apprendre

**L'encodeur partagé par type.** Les défenseurs sont interchangeables : la réponse à
« un ennemi à 80 m au nord-est » ne doit pas dépendre du fait qu'il s'appelle le n° 3.
On encode donc cette invariance au lieu de la faire apprendre — ce qui divise par `N!`
l'espace des fonctions à explorer.

**L'agrégation, et son piège.** ⟨mesuré 01/08⟩ Nous avions agrégé par **somme** seule.
Une somme est permutation-invariante, mais **on ne retrouve pas douze positions
individuelles dans un total** : le décodeur ne pouvait pas reconstruire la scène. Il faut
soit garder la vue brute à côté de la somme, soit remplacer la somme par une **attention**,
qui est permutation-équivariante et conserve l'identité :

```
somme        : e = Σ_j f(x_j)              invariante, destructive
attention    : e_i = Σ_j α_ij f(x_j)       équivariante, conserve i
               α_ij = softmax_j( q_i · k_j / √d )
```

**La mémoire récurrente.** Le combat est partiellement observable : un ennemi vu il y a
dix secondes derrière un mur existe encore. Un agent sans mémoire réagit à ce qu'il voit ;
un agent avec mémoire raisonne sur ce qu'il **croit**. C'est la différence entre un
réflexe et une tactique.

**Le latent stochastique.** Le monde est incertain : la même situation peut mener à
plusieurs futurs. Un modèle déterministe prédit la moyenne des futurs, qui n'est aucun
d'eux. ⟨mesuré 31/07⟩ Notre modèle prédisait mieux à vingt pas qu'à un seul, parce qu'il
récitait la moyenne au lieu de regarder où sont les hommes.

**Le choix du latent, et notre correction.** DreamerV3 utilise un latent **catégoriel**
(32 variables × 32 classes) parce que son observation est une image : la multimodalité y
compte plus que la précision. ⟨mesuré 31/07⟩ Chez nous, 16 × 16 = 64 bits par pas ne
suffisent pas à décrire quarante positions au mètre près, et **l'observation n'atteint la
mémoire qu'en passant par ce goulot**. On est passé à un latent **continu** de 64
dimensions.

**L'équilibre des pertes.** ⟨mesuré 31/07, le défaut le plus instructif⟩ Notre
reconstruction était une **moyenne** sur 92 nombres, donc 0,018, quand la divergence
valait 0,66. Le terme qui pousse à l'oubli pesait **trente-sept fois** celui qui pousse à
décrire. L'optimiseur a fait le calcul avant nous : il a tout oublié, c'était moins cher.
La divergence se compte en nats ; la reconstruction doit se **sommer**, pas se moyenner.

---

## 5. Contrôle moteur — la section à couper en deux

### 5.1 Ce qui n'est PAS à apprendre dans Arma

Marcher, courir, ramper, sauter, franchir, monter un escalier, ouvrir une porte, nager :
**le moteur d'Arma le fait déjà**, et mieux que ce qu'on apprendrait en un an. Chercher à
le commander produit le désastre mesuré : nos actionneurs écrasaient la prudence de l'IA
tactique cinq fois par minute, et c'est **la seule raison** pour laquelle nos « manœuvres »
avançaient.

La bonne couche d'action dans Arma est l'**intention** :

```
a_t = ( itinéraire, posture souhaitée, cible à supprimer, rôle dans l'échelon,
        emploi de la fumée, seuil d'engagement )
```

L'agent commande **au-dessus** de l'IA tactique, jamais à sa place.

### 5.2 Ce qui EST à apprendre, et où

L'apprentissage moteur vrai — équilibre, appuis, franchissement — se fait dans un
simulateur physique articulé (Isaac). Là, l'action est un couple par articulation :

```
τ ∈ ℝ^{28}       28 degrés de liberté pour un humanoïde
```

et la boucle tourne à 200 Hz, avec des récompenses de style « avance sans tomber, sans
patiner » ⟨notre correction du 15/07 : pénalité de glissement des pieds + terminaison à
0,7 de hauteur de bassin⟩.

### 5.3 La couture, et pourquoi c'est le vrai sujet de thèse

```
   ARMA                          ISAAC
   ┌────────────────┐            ┌────────────────┐
   │  cerveau       │            │  cerveau       │   ← LE MÊME
   │  (intentions)  │            │  (intentions)  │
   └───────┬────────┘            └───────┬────────┘
           │  itinéraire, posture, cible │
   ┌───────▼────────┐            ┌───────▼────────┐
   │ IA du moteur   │            │ contrôleur bas │
   │ (locomotion)   │            │ niveau appris  │
   └────────────────┘            └────────────────┘
```

Le transfert inter-incarnation consiste à garder l'étage du haut et à rebrancher l'étage
du bas. C'est faisable **parce que** l'intention ne parle pas de jambes.

---

## 6. Récompenses

### 6.1 Le principe, payé cher

⟨mesuré 29/07⟩ Une récompense sculptée à la main a enseigné l'immobilité. Le principe qui
en sort : **la récompense doit être un verdict, pas une opinion**.

```
R = R_mission  +  λ_c · R_coût  +  λ_p · R_pénalités
```

où `R_mission` est **binaire et mesuré à la fin** :

```
R_mission = 1  si un attaquant vivant tient l'objectif ⟨rayon 50 m⟩
               pendant 60 s CONTINUES, zéro adverse dedans
            0  sinon
```

⟨mesuré 01/08⟩ Le durcissement importe : la version « instantanée » du même critère
comptait comme prise un homme ayant dérivé à moins de 60 m — du bruit d'étiquette pur.

### 6.2 Le coût, la variable qui sépare

⟨mesuré 29/07⟩ La grandeur qui distingue les manœuvres n'est ni la vitesse ni les pertes
brutes, c'est **l'exposition par mètre gagné** :

```
C = ( Σ_t Σ_i 1[ soldat i exposé au pas t ] · Δt ) / ( distance gagnée vers l'objectif )
```

⟨0,65 pour les gagnants contre 1,21 pour les perdants⟩

### 6.3 Ce qu'on peut ajouter sans mentir

Les termes suivants sont **mesurables** et non arbitraires :

| terme | définition | signe |
|---|---|---|
| pertes | attaquants morts / effectif initial | − |
| tir fratricide | touches sur allié | −− |
| munitions | consommées / emportées | − faible |
| détection précoce | temps entre première détection ennemie et premier tir subi | + |
| coordination | corrélation temporelle des progressions d'escouades | + faible |

Et les termes qu'il faut **refuser** : « rester à couvert », « ne pas s'exposer »,
« avancer vite ». Ce sont des moyens, pas des fins, et les récompenser enseigne le moyen
au détriment de la fin. C'est exactement l'erreur du 29/07.

### 6.4 Le crédit temporel

Le problème dur : la mission dure 40 à 60 décisions et la récompense arrive à la fin.

```
G_t = Σ_{k=0}^{T-t} γ^k r_{t+k}                    retour
A_t^{GAE} = Σ_{l=0}^{∞} (γλ)^l δ_{t+l}             avantage généralisé
δ_t = r_t + γ V(s_{t+1}) − V(s_t)                  erreur temporelle
```

`γ` proche de 1 (0,997) parce que la récompense est lointaine ; `λ` à 0,95 pour arbitrer
biais et variance.

---

## 7. Mémoire hiérarchique

Quatre échelles, quatre objets mathématiques différents.

```
┌─────────────────────────────────────────────────────────────────┐
│ IMMÉDIATE      ~2 s     état latent du GRU        h_t ∈ ℝ^{384} │
│                          ce que je fais maintenant               │
├─────────────────────────────────────────────────────────────────┤
│ TACTIQUE       ~2 min   carte de croyance          M ∈ ℝ^{G×G×C}│
│                          où je crois que sont les ennemis        │
├─────────────────────────────────────────────────────────────────┤
│ STRATÉGIQUE    ~1 h     graphe de l'objectif       G = (V,E)     │
│                          quels points comptent, qui les tient    │
├─────────────────────────────────────────────────────────────────┤
│ LONG TERME     ∞        poids du réseau            θ             │
│                          ce que j'ai appris de tous les combats  │
└─────────────────────────────────────────────────────────────────┘
```

**La carte de croyance** mérite d'être détaillée, parce qu'elle est le seul de ces objets
qui soit spécifique au combat. ⟨notre `carte.py`, 22/07⟩ C'est une grille `G × G` de
cellules, chacune portant `C` canaux :

```
M[i,j,0]  = probabilité de présence ennemie
M[i,j,1]  = âge de l'information   exp(−Δt/τ)
M[i,j,2]  = danger subi (tirs reçus depuis cette cellule)
M[i,j,3]  = couvert disponible
```

Mise à jour bayésienne à chaque observation, et **vieillissement** entre deux :

```
M_{t+1} = (1−α) · M_t · e^{−Δt/τ}  +  α · O_t
```

L'agent ne lit pas l'ennemi, il lit **sa carte**. C'est ce qui fait qu'il continue de se
méfier d'un coin de rue d'où on lui a tiré dessus il y a trente secondes.

---

## 8. Coopération à plusieurs centaines

### 8.1 Le paradigme : entraînement centralisé, exécution décentralisée

```
ENTRAÎNEMENT               │  EXÉCUTION
critique Q(s_global, a⃗)     │  chaque agent : a_i ~ π(· | o_i)
voit tout                  │  ne voit que son observation
```

Le critique centralisé résout la **non-stationnarité** : du point de vue d'un agent, les
autres changent de politique pendant l'apprentissage, donc son environnement bouge sous
ses pieds. Un critique qui voit tout le monde n'a pas ce problème.

### 8.2 Le passage à l'échelle : du dense au graphe

Un transformeur multi-agents coûte `O(N²)` en attention. À N=500, c'est 250 000 paires
par pas — impraticable.

Un **réseau sur graphe** ne propage l'information que le long des arêtes existantes :

```
m_{i←j} = φ_msg( h_i , h_j , e_ij )              message de j vers i
h_i'    = φ_upd( h_i , Σ_{j ∈ N(i)} m_{i←j} )    mise à jour
```

Avec un voisinage borné par la portée radio et la distance (`k ≈ 8`), le coût est
`O(N·k)` — linéaire. **Deux ou trois tours de propagation** suffisent à faire circuler
l'information dans une escouade, ce qui est exactement la profondeur d'un échelon.

### 8.3 Communication implicite et explicite

**Implicite** : je vois ce que tu fais, donc j'en déduis ce que tu sais. C'est gratuit et
c'est ce qui produit le feu-et-mouvement. ⟨mesuré 26/07 : le feu-et-mouvement ÉMERGE de
quatre intentions, sans être scripté⟩

**Explicite** : j'émets un vecteur `c_i ∈ ℝ^{16}` que mes voisins reçoivent. Le contenu
n'est pas défini par nous — il est **appris**, et le gradient traverse le canal. C'est
plus puissant et beaucoup plus lent à converger.

Recommandation, vu notre budget d'échantillons : commencer implicite, ajouter l'explicite
seulement si une tâche l'exige et qu'on peut le mesurer.

### 8.4 Hiérarchie et leadership émergent

```
      commandant (1 décision / 30 s)     ← objectifs par escouade
           │
      chefs d'escouade (1 / 5 s)         ← itinéraire, posture, rôle
           │
      soldats (1 / 1 s)                  ← intentions individuelles
```

Le leadership **émergent** consiste à ne pas fixer qui commande : un score d'influence
`w_i` est appris, et l'agent au plus fort score voit son message pondéré davantage. C'est
élégant, c'est plus difficile, et ça ne se tente qu'après que la hiérarchie fixe marche.

---

## 9. Entraînement massif — le mur de réalité

### 9.1 Ce qui est physiquement possible

⟨mesuré 31/07 et 01/08⟩

```
1 instance Arma, 240 entités  →  6,7 ms/tick d'émetteur, −15 % FPS, ~2,4 Go, ~2 fils
12 instances                  →  51 Go / 60, 17-19 fils / 24, horloge encore propre
au-delà                       →  l'horloge dérape (2,19 % de pas hors bande), corpus perdu
```

**Il n'y a pas de « 5 000 simulations Arma en parallèle »** sur une machine. Sur un
cluster, chaque nœud plafonne pareil : c'est le simulateur qui est le mur, pas le matériel.

Débit réel mesuré : **65 accrochages par heure sur 12 mondes**, soit environ 500 par nuit,
et environ 100 000 pas d'état par heure.

### 9.2 La conséquence architecturale

Un algorithme sans modèle demande typiquement 10⁶ à 10⁸ pas. À 100 000 pas/heure, 10⁷ pas
demandent **quatre mois**. C'est rédhibitoire.

D'où l'architecture obligée :

```
   ┌──────────────┐  500 accrochages/nuit   ┌────────────────┐
   │  12 mondes   │ ──────────────────────► │ corpus disque  │
   │  Arma        │                          └───────┬────────┘
   └──────▲───────┘                                  │
          │                                  ┌───────▼────────┐
          │  certification                   │ modèle du monde│
          │  (30 accrochages/soir)           │  (GPU, rapide) │
          │                                  └───────┬────────┘
   ┌──────┴───────┐                                  │
   │ politique    │ ◄────────────────────────────────┘
   │              │   entraînement DANS l'imagination
   └──────────────┘   (millions de pas, minutes)
```

Le simulateur devient un **certificateur**, pas un gymnase. C'est le renversement que le
projet a acté.

### 9.3 L'infrastructure concrète

```
COLLECTE      12 processus Arma (CPU) + 12 lecteurs de journal (Python)
              → JSONL append-only, ~100 Mo/h
              ⟨le pont TCP est INTERDIT pour la capture : il meurt après 20-40 min⟩

STOCKAGE      /mnt/data2 (3,6 To) ; ~2,4 Go/jour de corpus, ~5,5 Go/jour de journaux
              JSONL plat, pas de base de données tant que le volume ne mord pas

AUDIT         7 taux de contamination, seuils à 1 %, contrôle nul à zéro exact
              empreinte sha256 du monde ET des actionneurs dans chaque enregistrement

ENTRAÎNEMENT  1 GPU, corpus résident en mémoire vidéo (36 Mo pour 2 000 fenêtres)
              lots de 192, 5 000 pas de gradient ≈ 1 h

CERTIFICATION 30 accrochages réels par soir, évaluation appariée
              fil de détente : si l'imaginé dépasse le réel de 20 points, on arrête
```

---

## 10. Algorithmes — lequel, et pourquoi

| famille | échantillons requis | adapté ici ? |
|---|---|---|
| **PPO** | 10⁶–10⁷ | non seul : trop gourmand pour 10⁵/h |
| **SAC** | 10⁵–10⁶ | actions continues ; nos actions sont discrètes |
| **TD3** | 10⁵–10⁶ | même remarque |
| **Dreamer / RSSM** | 10⁵ **réels** | **oui** — conçu pour le régime pauvre en données |
| **MuZero** | 10⁶+ | recherche arborescente ; notre monde est trop stochastique |
| **Decision Transformer** | dépend du corpus | **oui en amorçage** : apprend d'un corpus figé |
| **RL hiérarchique** | — | **oui** : notre structure est hiérarchique par nature |
| **Imitation** | corpus | **oui d'abord** ⟨notre recette validée : imiter puis affiner⟩ |
| **RL hors ligne** | corpus | **oui** : on a 500 accrochages/nuit qui dorment |
| **RL inverse** | corpus expert | intéressant : déduire la récompense de LAMBS |

**La recette que nos mesures soutiennent** ⟨validée le 26/07 : imitation puis affinage bat
le professeur de 5,9 points sur graines tenues à l'écart⟩ :

```
1. IMITATION       apprendre à copier LAMBS depuis le corpus       (rapide, hors ligne)
2. MODÈLE DU MONDE apprendre la dynamique depuis le même corpus     (GPU, hors ligne)
3. AFFINAGE        améliorer la politique DANS l'imagination        (millions de pas)
4. CERTIFICATION   la juger dans le vrai simulateur                 (30/soir)
```

Le point délicat, et il est connu : une politique entraînée dans l'imagination
**exploite les erreurs du modèle**. D'où le fil de détente quantitatif : si le taux de
réussite imaginé dépasse le réel de plus de 20 points, on arrête et on réentraîne le
modèle sur des données fraîches.

---

## 11. Les mathématiques qui comptent

### 11.1 Rétropropagation

Pour une chaîne `x → h¹ → h² → … → L` :

```
∂L/∂W^{(l)} = δ^{(l)} (h^{(l−1)})ᵀ
δ^{(l)} = ( (W^{(l+1)})ᵀ δ^{(l+1)} ) ⊙ σ'( z^{(l)} )
```

Tout est produit matriciel et produit terme à terme. Le coût de la passe arrière est
environ deux fois celui de la passe avant.

### 11.2 Jacobienne et Hessienne

```
J_ij = ∂f_i/∂x_j             (m × n)   comment la sortie bouge quand l'entrée bouge
H_ij = ∂²L/∂θ_i ∂θ_j         (p × p)   courbure de la perte
```

La Hessienne d'un réseau à 2 millions de paramètres a 4·10¹² entrées : on ne la forme
jamais. On utilise des produits Hessienne-vecteur, ou des approximations diagonales —
c'est exactement ce que fait Adam :

```
m_t = β₁ m_{t−1} + (1−β₁) g_t             moment 1 (direction)
v_t = β₂ v_{t−1} + (1−β₂) g_t²            moment 2 (échelle)
θ_{t+1} = θ_t − η · m̂_t / (√v̂_t + ε)
```

### 11.3 Rotations et quaternions

Une rotation dans ℝ³ est une matrice orthogonale de déterminant 1 :

```
R ∈ SO(3) :   RᵀR = I ,  det R = 1
```

Les angles d'Euler souffrent du **blocage de cardan** : à certaines orientations, deux axes
se confondent et un degré de liberté disparaît. Le quaternion l'évite :

```
q = (w, x, y, z) ,  ‖q‖ = 1
rotation de v :  v' = q ⊗ (0,v) ⊗ q*
```

Quatre nombres au lieu de neuf, pas de singularité, interpolation naturelle. **Pour un
réseau**, on donne les quaternions ou les paires (cos, sin) — jamais les angles bruts.

### 11.4 Les divergences

```
KL( q ‖ p ) = Σ q(x) log( q(x)/p(x) )
```

Pour deux normales diagonales, forme close :

```
KL = Σ_i [ log(σ_p,i/σ_q,i) + (σ_q,i² + (μ_q,i − μ_p,i)²) / (2σ_p,i²) − ½ ]
```

⟨notre erreur du 31/07 : un plancher de bits libres appliqué à la SOMME au lieu de chaque
dimension laissait le modèle tout ignorer en restant sous un nat au total⟩

### 11.5 Intervalles de confiance — la statistique qui décide

L'intervalle de Wilson, plus honnête que l'approximation normale quand `p` est proche de
0 ou 1 :

```
        p̂ + z²/2n  ±  z √( p̂(1−p̂)/n + z²/4n² )
CI  =   ───────────────────────────────────────
                    1 + z²/n
```

⟨utilisé partout dans nos critères : 0 succès sur 38 donne [0 ; 9,2 %], ce qui EST une
mesure et non un « on n'a rien vu »⟩

### 11.6 Puissance statistique

Pour détecter un écart `Δ` entre deux proportions au seuil α avec puissance 1−β :

```
n ≈ 2 ( z_{α/2} + z_β )² · p̄(1−p̄) / Δ²
```

⟨application du 01/08 : Δ = 8,6 points, p̄ ≈ 0,57 → n ≈ 520 par bras. Nos 125 verdicts
donnaient p ≈ 0,18 : la direction sans la preuve.⟩

---

## 12. Vision longue

### 12.1 Ce qui rend possible l'invention de tactiques

Une tactique nouvelle n'apparaît que si trois conditions tiennent ensemble.

**Le monde doit récompenser la manœuvre.** Si toutes les conduites se valent, il n'y a
rien à inventer. ⟨c'est précisément ce qu'on mesure en ce moment : deux axes contre un,
8,6 points d'écart, non encore établi⟩

**L'espace d'action doit contenir la tactique.** On ne découvre pas le contournement si
l'action est « avancer tout droit ». D'où l'importance de l'espace d'intentions.

**La pression de sélection doit être variée.** Une seule carte, un seul rapport de force,
et l'agent trouve l'optimum local de ce cas-là. La **matrice** de conditions n'est pas un
luxe méthodologique : c'est la condition de l'invention.

### 12.2 Co-évolution

```
   politique bleue  ──► s'améliore contre la rouge courante
           ▲                        │
           │                        ▼
   politique rouge  ◄── s'améliore contre la bleue courante
```

Le risque connu est l'**oubli catastrophique** : bleu bat rouge_t mais perd contre
rouge_{t−10}. La parade est une **ligue** : on garde un vivier d'anciennes versions et on
échantillonne l'adversaire dedans. ⟨notre `coevo` du 21/07 : meilleure-réponse + ligue
anti-oubli, validées en live⟩

### 12.3 Généralisation aux cartes et aux mods

Deux mécanismes, et ils ne se remplacent pas.

**La randomisation de domaine** : varier les cartes, la météo, les effectifs pendant
l'entraînement. Elle rend robuste, elle ne rend pas intelligent.

**L'abstraction du terrain** : ne jamais donner de coordonnées absolues au réseau, mais
des grandeurs **relatives et locales** — la coque radiale, la distance au couvert le plus
proche, la pente sous les pieds. Un réseau qui ne voit que du relatif n'a rien à
réapprendre sur une carte neuve. ⟨c'est déjà notre choix : positions centrées, coque de
12 rayons⟩

### 12.4 Véhicules, hélicoptères, drones

Le même cerveau ne pilotera pas un char et un fantassin — les échelles de temps diffèrent
d'un ordre de grandeur. Mais **l'étage d'intention** peut être commun :

```
intention : « supprimer ce point », « occuper cette crête », « éclairer cet axe »
   ├─ fantassin : le contrôleur d'infanterie l'exécute
   ├─ blindé    : le contrôleur de char l'exécute
   └─ drone     : le contrôleur de vol l'exécute
```

C'est exactement la couture de la §5.3, appliquée à d'autres corps. **Et c'est le sujet
de thèse** : ce qui transfère n'est ni la politique motrice ni la carte, c'est la
représentation d'une situation et la décision qu'elle appelle.

### 12.5 L'horizon honnête

Ce qui est atteignable en un an de travail sérieux : un agent qui bat LAMBS dans le cadre
mesuré, sur plusieurs cartes, avec une politique qui transfère d'une carte à l'autre sans
réentraînement.

Ce qui ne l'est pas : une IA qui « invente la doctrine ». L'invention supposerait qu'elle
explore un espace de tactiques que nous n'avons pas encodé — et aujourd'hui l'espace
d'action, c'est nous qui l'écrivons.

**Le vrai jalon n'est pas l'invention. C'est le transfert.** Le jour où le même cerveau,
sans réentraînement, se débrouille sur une carte qu'il n'a jamais vue, on aura montré
qu'il a appris quelque chose du combat et non de la carte.
