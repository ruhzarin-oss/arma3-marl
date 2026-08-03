# Inventaire complet des paramètres captables — Arma 3

*01/08/2026. Objectif : tout brancher. On choisira ce qui sert à DÉCIDER plus tard ;
capturer large est réversible, capturer étroit ne l'est pas.*

**Légende**
`✓` déjà capturé aujourd'hui · `+` à brancher · `?` à vérifier dans CE build du moteur
`dim` = nombre de nombres produits · `N` = nombre d'hommes · `M` = nombre d'ennemis

⚠ **Vérification obligatoire avant câblage.** Ce build a déjà démenti une commande que
la documentation donne pour standard : `currentTarget` n'existe pas ici ⟨mesuré 29/07 —
un gestionnaire l'appelait et mourait EN SILENCE, emportant tout le script⟩. Chaque `?`
doit passer un test d'existence avant d'entrer dans la capture.

---

## A. SOLDAT — cinématique · dim 16

| # | grandeur | commande | dim | état |
|---|---|---|---|---|
| A1 | position sol | `getPosATL` | 3 | ✓ |
| A2 | position mer | `getPosASL` | 3 | + |
| A3 | vitesse vectorielle | `velocity` | 3 | + |
| A4 | vitesse scalaire | `speed` | 1 | + |
| A5 | cap | `getDir` → cos, sin | 2 | + |
| A6 | vecteur de visée | `vectorDir` | 3 | + |
| A7 | vecteur haut (tangage/roulis) | `vectorUp` | 3 | + |
| A8 | accélération | dérivée de A3 entre ticks | 3 | + |

*Note : l'accélération ne se lit pas, elle se calcule hors ligne. Ne pas l'émettre.*

## B. SOLDAT — corps et physiologie · dim ~20

| # | grandeur | commande | dim | état |
|---|---|---|---|---|
| B1 | vivant | `alive` | 1 | ✓ |
| B2 | dégâts globaux | `damage` | 1 | + |
| B3 | dégâts par point d'impact | `getAllHitPointsDamage` | ~10 | + |
| B4 | état de vie | `lifeState` | 1 | + |
| B5 | inconscient | `ace_medical` / `incapacitated` | 1 | ? |
| B6 | posture | `unitPos` (UP/MIDDLE/DOWN) | 3 one-hot | + |
| B7 | fatigue | `getFatigue` | 1 | + |
| B8 | souffle avancé | `ace_advanced_fatigue` | 1 | ? |
| B9 | charge portée | somme des masses du loadout | 1 | + |
| B10 | captif | `captive` | 1 | + |

*B3 est le bloc le plus riche du corps : dix points d'impact séparés (tête, torse, bras,
jambes) qui disent OÙ l'homme a été touché. C'est ce qui distingue une égratignure d'une
blessure invalidante.*

## C. SOLDAT — armement et équipement · dim ~25 + loadout complet

| # | grandeur | commande | dim | état |
|---|---|---|---|---|
| C1 | arme courante | `currentWeapon` | 1 catégoriel | + |
| C2 | bouche de feu courante | `currentMuzzle` | 1 | + |
| C3 | mode de tir | `currentWeaponMode` | 1 | + |
| C4 | arme épaulée / rangée | `weaponState` | 1 | ? |
| C5 | munitions du chargeur | `ammo currentWeapon` | 1 | + |
| C6 | chargeurs restants par type | `magazines` + comptage | ~4 | + |
| C7 | munitions détaillées | `magazinesAmmoFull` | variable | + |
| C8 | armes portées | `weapons` | ~4 | + |
| C9 | accessoires | `primaryWeaponItems` | ~4 | + |
| C10 | grenades / fumigènes | filtrage de `magazines` | 2 | + |
| C11 | équipement complet | `getUnitLoadout` | ~50 | + |
| C12 | optique en usage | `currentVisionMode` | 1 | ? |

*C11 est énorme et surtout CONSTANT pendant un accrochage. À capturer UNE FOIS à
l'apparition, pas à chaque tick. Règle générale : ce qui ne change pas ne se répète pas.*

## D. SOLDAT — état de combat et intention de l'IA · dim ~12

| # | grandeur | commande | dim | état |
|---|---|---|---|---|
| D1 | comportement | `behaviour` | 5 one-hot | + |
| D2 | mode de combat | `combatMode` | 5 one-hot | + |
| D3 | allure | `speedMode` | 4 one-hot | + |
| D4 | formation | `formation` (groupe) | ~8 | + |
| D5 | ordre en cours | `currentCommand` | 1 catégoriel | + |
| D6 | cible désignée | `assignedTarget` | id | ? |
| D7 | cible courante | `currentTarget` | — | ⛔ **N'EXISTE PAS dans ce build** |
| D8 | suppression subie | `getSuppression` | 1 | + |
| D9 | a tiré depuis le tick | notre drapeau | 1 | ✓ |
| D10 | point de passage courant | `currentWaypoint` | 1 | + |
| D11 | état LAMBS | variables du mod | ? | ? |

*D11 est le plus intéressant et le moins documenté : LAMBS stocke SES décisions dans des
variables d'unité. Les lire, c'est enregistrer ce que le PROFESSEUR décide, pas seulement
ce qu'il fait. C'est la différence entre imiter un geste et imiter une intention.*
⟨Fable l'a demandé explicitement : « enregistre ce que le professeur décide, pas seulement
les positions, sinon tu récoltes un corpus dont on ne peut rien imiter »⟩

## E. PERCEPTION — par paire · dim N×M

| # | grandeur | commande | dim | état |
|---|---|---|---|---|
| E1 | connaissance de la cible | `knowsAbout` ∈ [0,4] | N×M | + |
| E2 | ligne de vue | `lineIntersectsSurfaces` | N×M | + |
| E3 | visibilité pondérée | `checkVisibility` | N×M | + |
| E4 | distance | calcul | N×M | + |
| E5 | gisement relatif | calcul | 2·N×M | + |

**C'est le bloc qui explose.** Pour 20 hommes : 400 paires × 5 grandeurs = 2 000 nombres
par tick. À 5 Hz, dix mille nombres par seconde et par monde.

**Coupure obligatoire, ancrée sur une mesure** ⟨falaise du 30/07⟩ : au-delà de 100 m,
`knowsAbout` vaut 0,00. Donc on n'évalue E1–E5 que pour les paires sous 150 m, indexées
par grille spatiale. Le coût passe de `O(N·M)` à `O(N·k)` avec k ≈ 5.

## F. GROUPE · dim ~10

| # | grandeur | commande | dim | état |
|---|---|---|---|---|
| F1 | identifiant de groupe | `group` | 1 | + |
| F2 | chef | `leader` | 1 | + |
| F3 | effectif vivant | `count units` | 1 | + |
| F4 | formation | `formation` | 8 one-hot | + |
| F5 | rang dans le groupe | `rank` | 6 one-hot | + |
| F6 | position dans la formation | `formationPosition` | 3 | ? |
| F7 | groupe en combat | `combatMode` du groupe | 1 | + |

## G. VÉHICULE — si monté · dim ~20

| # | grandeur | commande | dim | état |
|---|---|---|---|---|
| G1 | véhicule occupé | `vehicle` / `objectParent` | 1 | + |
| G2 | rôle à bord | `assignedVehicleRole` | 1 | + |
| G3 | tourelle | `currentTurret` | 2 | + |
| G4 | carburant | `fuel` | 1 | + |
| G5 | dégâts par partie | `getAllHitPointsDamage` | ~12 | + |
| G6 | munitions des armes de bord | `magazinesTurret` | ~4 | + |
| G7 | vitesse et cap du véhicule | `velocity`, `getDir` | 4 | + |

⚠ **Trou connu** ⟨signalé par Fable le 31/07⟩ : notre capteur de tir est posé sur les
HOMMES. Les armes de bord vivent sur la coque, donc **leurs tirs ne sont pas enregistrés**.
À mesurer avant de corriger : compter les impacts dont le tireur est tracé mais sans
événement de tir dans les 2 s.

## H. TERRAIN LOCAL · dim au choix — c'est un échantillonnage, pas une lecture

| # | grandeur | commande | dim | état |
|---|---|---|---|---|
| H1 | **coque radiale de couvert** | rayons + `lineIntersectsSurfaces` | 12 à 36 | + ⭐ |
| H2 | hauteur du sol | `getTerrainHeightASL` | 1 | + |
| H3 | pente | dérivée locale de H2 | 2 | + |
| H4 | normale à la surface | `surfaceNormal` | 3 | + |
| H5 | type de surface | `surfaceType` | ~8 one-hot | + |
| H6 | eau | `surfaceIsWater` | 1 | + |
| H7 | végétation proche | `nearestTerrainObjects` type BUSH/TREE | ~4 | + |

**H1 est le bloc décisif.** ⟨mesuré 24/07 : avec la coque, 97 % de couvert atteint ;
sans, 0 %⟩ Les poids existent déjà : `soldier_shell.pt`. C'est la brique la plus dure de
la représentation, et elle est **déjà faite** — simplement pas branchée sur la capture.

## I. BÂTIMENTS · dim ~10 par bâtiment

| # | grandeur | commande | dim | état |
|---|---|---|---|---|
| I1 | bâtiments proches | `nearestTerrainObjects ["HOUSE"]` | liste | + |
| I2 | positions internes | `buildingPos -1` | 3 × n | + |
| I3 | emprise au sol | `boundingBoxReal` | 6 | + |
| I4 | occupé par qui | croisement position | 1 | + |
| I5 | détruit | `damage` du bâtiment | 1 | + |
| I6 | ouvertures | `animationNames` (portes) | variable | ? |

*I2 est déjà utilisé par le générateur pour poser la garnison. I6 (portes ouvertes ou
fermées) est plus incertain et dépend du modèle 3D de chaque bâtiment.*

## J. ENVIRONNEMENT GLOBAL · dim ~14 — partagé par tous

| # | grandeur | commande | dim |
|---|---|---|---|
| J1 | couverture nuageuse | `overcast` | 1 |
| J2 | pluie | `rain` | 1 |
| J3 | brouillard | `fogParams` | 3 |
| J4 | vent | `wind` | 3 |
| J5 | rafales | `gusts` | 1 |
| J6 | humidité | `humidity` | 1 |
| J7 | heure | `daytime` → cos, sin | 2 |
| J8 | luminosité solaire | `sunOrMoon` | 1 |
| J9 | lune | `moonIntensity` | 1 |
| J10 | distance de vue | `viewDistance` | 1 |

*Ces quatorze nombres sont **globaux**, pas par homme. Les répéter par soldat serait
multiplier par vingt une information constante. À stocker une fois par tick.*

## K. MISSION ET CONTEXTE · dim ~10

| # | grandeur | dim | état |
|---|---|---|---|
| K1 | verbe de mission | 4 one-hot | + |
| K2 | position de l'objectif | 3 | ✓ (générateur) |
| K3 | temps écoulé / durée max | 2 | + |
| K4 | pertes subies / budget | 2 | + |
| K5 | camp défenseur | 1 | ✓ |
| K6 | effectifs initiaux | 2 | ✓ |
| K7 | nombre d'axes d'assaut | 1 | ✓ |

## L. ÉVÉNEMENTS — déjà capturés · asynchrones

| # | événement | source | état |
|---|---|---|---|
| L1 | apparition | recenseur | ✓ |
| L2 | disparition | recenseur | ✓ |
| L3 | tir + projectile | `Fired` | ✓ |
| L4 | impact | `HitPart` | ✓ |
| L5 | mort + tueur | `EntityKilled` | ✓ |
| L6 | tir entendu proche | `FiredNear` | + |
| L7 | dégâts détaillés | `HandleDamage` | ⛔ sous-compte ×4 ⟨mesuré⟩ |
| L8 | changement de posture | dérivé de B6 | + |
| L9 | rechargement | `Reloaded` | + |
| L10 | montée / descente de véhicule | `GetIn` / `GetOut` | + |

---

## Totaux

| bloc | dimension par tick | pour 20 hommes |
|---|---|---|
| A cinématique | 16 | 320 |
| B corps | 20 | 400 |
| C armement (variable) | 25 | 500 |
| D état de combat | 12 | 240 |
| E perception par paire | 5 par paire | ~2 000 (400 paires) |
| F groupe | 10 | 40 (4 groupes) |
| G véhicule | 20 | 0 à 200 |
| H terrain, coque à 12 | 24 | 480 |
| I bâtiments | 10 par bâtiment | ~200 (20 bâtiments) |
| J environnement | 14 | 14 (global) |
| K mission | 10 | 10 (global) |

**Par tick, pour un accrochage de vingt hommes : environ 4 200 nombres.**
Aujourd'hui on en enregistre **140**. Facteur **trente**.

**Constant, capturé une seule fois par homme :** l'équipement complet (~50), soit 1 000
de plus par accrochage — mais une fois, pas deux cents fois.

---

## Le coût, chiffré

À 5 Hz, 20 hommes, 4 200 nombres par tick :

```
21 000 nombres / seconde / monde
× 6 mondes                    = 126 000 / s
× 3600 s                      = 450 millions / heure
en JSONL, ~8 octets par nombre = 3,6 Go / heure
× 12 h de nuit                = 43 Go par nuit
```

Contre 100 Mo/heure aujourd'hui. **Facteur trente-six.**

Le disque tient — 3,1 To libres, donc environ deux mois. Mais deux choses cassent avant :

**Le coût d'émission.** ⟨mesuré 31/07⟩ L'émetteur coûte 6,7 ms par tick pour 7 nombres ×
240 entités. À 4 200 nombres, la construction de chaîne explose. **Il faudra changer de
format** — binaire au lieu de texte, ou n'émettre que ce qui a changé.

**L'exploitation.** Cinq cents accrochages par nuit restent cinq cents exemples pour
apprendre un verdict. Capturer trente fois plus ne crée pas un exemple de plus.

---

## Ordre de câblage recommandé — du plus utile au moins

1. **H1, la coque radiale** — déjà construite et validée, la plus décisive, 24 nombres
2. **D8 suppression, B6 posture, C5 munitions** — trois lignes, très informatives
3. **E1 knowsAbout** sous coupure à 150 m — ce que chacun SAIT, pas ce qui est vrai
4. **D11 les variables de LAMBS** — les décisions du professeur, pour pouvoir l'imiter
5. **B3 dégâts par point d'impact** — distingue l'égratignure de l'invalidation
6. **A3–A7 cinématique complète** — vitesse et orientation
7. **C11 équipement** — une seule fois par homme, à l'apparition
8. **J environnement** — global, quatorze nombres, presque gratuit
9. **G véhicules** — quand il y en aura, avec le capteur de tir manquant
10. **I6 portes** — le plus incertain, le moins urgent

**Avant tout câblage : le test d'existence.** Chaque commande marquée `?` doit être
appelée sur une unité de test et son résultat vérifié. ⟨règle payée le 29/07 : une
commande inexistante fait mourir le gestionnaire EN SILENCE et emporte tout le script⟩
