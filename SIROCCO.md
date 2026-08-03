# SIROCCO — le système immunitaire tactique

> Conception, 27/07/2026. Une carto de signal qui stimule des zones, déclenche des réactions
> en chaîne, et anticipe. Modèle : la réponse immunitaire, prise au sérieux (pas en décoration).

---

## 1. Le problème, en trois phrases

Ton agent ne sait pas qu'on lui tire dessus. Il l'a montré : aveugle à l'arc de tir, il contourne
à 132 m quand le crochet le fait à 184 m — même manœuvre, tarif fort. Il subit le monde au lieu
de le sentir.

Tu as déjà deux pièces du puzzle, mais elles sont mal placées :

- `carte.py` — un champ de menace qui **vieillit** et **diffuse**. C'est déjà de la chimie. Mais il
  vit chez le commandant, pas dans le soldat, et il n'a qu'un seul canal (vu / pas vu).
- `_champ_danger` (assault_terrain) — le prix du terrain dans 8 directions. Excellent, mais il lit
  la **vérité terrain** : positions réelles, LOS réel, arc réel. C'est un oracle. Un corps vivant
  n'a pas d'oracle.

SIROCCO remplace l'oracle par un **système de détection distribué**. Personne ne sait tout.
Chacun sent localement, dépose un signal, le signal se propage, et la réaction se déclenche par
seuils.

---

## 2. Ce que fait vraiment l'immunité — les six lois qu'on garde

Ce ne sont pas des images. Ce sont des contraintes de conception.

**Loi 1 — On réagit au DANGER, pas à l'étranger.**
L'immunologie moderne (modèle du danger) dit que le corps ne se demande pas « est-ce moi ? ».
Il se demande « est-ce que ça abîme ? ». Traduction : ton agent doit réagir à ce qui lui **coûte**,
pas à ce qu'il **voit**. C'est déjà ta ligne — le coût est l'exposition par mètre gagné.

**Loi 2 — Le signal est chimique : diffusé, périssable, sans adresse.**
Une cellule blessée ne téléphone pas au ganglion. Elle relâche une molécule qui se répand et
s'évapore. Personne ne reçoit un message : on baigne dans une concentration. C'est robuste
(pas de destinataire à perdre) et honnête (l'information vieillit toute seule).

**Loi 3 — La réponse est graduée par seuils.**
Rien → local → régional → général. Chaque étage coûte plus cher que le précédent et ne se
déclenche que si le signal dépasse une barre. Aucun étage ne « décide » : il franchit.

**Loi 4 — Deux vitesses qui tournent ensemble.**
L'inné répond en secondes, câblé, imprécis, jamais appris. L'adaptatif répond en jours, spécifique,
appris. Le second ne remplace pas le premier — il arrive derrière.

**Loi 5 — Il y a un frein, et le frein est vital.**
Sans résolution, l'inflammation tue l'hôte. Ton blob à 150 agents qui cale, c'est un choc
cytokinique : tout le monde a répondu au même signal, en même temps, au même endroit.

**Loi 6 — La mémoire rend le second contact quasi instantané.**
Même antigène, deuxième fois : la réponse est plus rapide d'un ordre de grandeur. **C'est ça,
l'anticipation.** Pas prédire l'avenir : abaisser le seuil là où ça a déjà mordu.

---

## 3. Le dictionnaire

| Immunité | Fonction | Tactique | Chez toi |
|---|---|---|---|
| Peau, muqueuse | barrière passive | dispositif, formation, arc de tir | `formations.py`, ligne FIBUA |
| Macrophage résident | sentinelle sur place | le soldat qui capte | obs par agent |
| PAMP (motif connu) | « ça ressemble à un pathogène » | silhouette, son de tir, véhicule | LOS, `_losc` |
| **DAMP (signal de dommage)** | « je suis abîmé » | **impact reçu, camarade touché, balle qui frôle** | **manquant** |
| Cytokine | signal diffusé, périssable | le champ d'alarme | extension de `carte.py` |
| Chimiokine + chimiotactisme | gradient qui attire | recrutement des voisins vers la zone | manquant |
| Vaisseau lymphatique | canal de drainage | voisinage + comms escouade | `team_obs` |
| Ganglion | nœud où le signal est présenté et arbitré | le chef de groupe | à créer |
| Réponse innée | réflexe câblé, < 1 s | se plaquer, rompre LOS, pivoter | postures, `arc_obs` |
| Réponse adaptative | politique apprise, spécifique | manœuvre choisie | SHAMAL, commander.pt |
| Expansion clonale | on fabrique plus d'effecteurs là où ça brûle | allocation de force sur l'axe | officier |
| Opsonisation (anticorps) | marquer une cible pour la rendre traitable | désignation d'objectif | rôles |
| Complément | cascade à seuil qui s'auto-amplifie | escalade de la réaction | à créer |
| Cellule mémoire | second contact = réponse immédiate | seuil pré-abaissé sur zone connue | PRÉSAGE |
| Treg, résolution | éteindre l'inflammation | retour au dispositif | **manquant, critique** |
| Soi / IFF | ne pas s'attaquer | reconnaissance ami | à créer |
| Site immuno-privilégié | zone où l'on ne réagit pas | ROE, secteur interdit | à créer |
| Moelle osseuse | fabrique les effecteurs | le gym sandbox | sandbox calibrée |
| Thymus | sélection : élimine ce qui attaque le soi | banc de certification | **Arma** |

Deux lignes de ce tableau portent tout le projet : **DAMP** (le signal manquant) et **résolution**
(le frein manquant).

---

## 4. Les organes — l'architecture

Cinq étages, cinq horloges. Chacun a une fréquence propre. C'est ça qui empêche l'ensemble de
s'emballer.

```
          ORGANE                    HORLOGE        DÉCIDE
  [5] Rate / officier            30 s et +      le plan, l'allocation
  [4] Ganglion / chef de groupe   5–10 s        recruter ou pas, où
  [3] Réseau lymphatique          1–2 s         propager, diffuser, oublier
  [2] Sentinelle / le soldat      1 pas         déposer le signal, lire le champ local
  [1] Réflexe inné                immédiat      se plaquer, pivoter, rompre
```

Règle dure : **un étage ne peut jamais court-circuiter celui d'en dessous.** Le réflexe part
même si l'officier dit autre chose. Un corps qui attend l'ordre du cerveau pour retirer sa main
du feu est un corps mort.

---

## 5. La carto — les six canaux du champ

Le champ est une grille (comme `carte.py`, G×G), mais **six canaux** au lieu de deux. Chaque canal
a sa demi-vie et son rayon de diffusion. C'est la table de conception la plus importante :

| Canal | Déclenché par | Portée du dépôt | Demi-vie | Diffusion | Signe |
|---|---|---|---|---|---|
| **CONTACT** | j'ai vu un ennemi | point vu | longue (~6 s) | forte | l'ennemi est là |
| **IMPACT** | je prends des dégâts | ma position + direction du tir | courte (~2 s) | faible | on me touche |
| **FRÔLEMENT** | une balle passe près | ma position + direction | courte (~2 s) | faible | **on me vise** |
| **BRUIT** | un tir entendu | direction, sans distance fiable | moyenne | très forte | ça se bat par là |
| **PERTE** | un camarade tombe | sa position | longue | moyenne | ici on meurt |
| **SOI** | mes camarades vivants | leurs positions | courte | faible | ne pas tirer, ne pas s'agglutiner |

Trois choses à voir dans ce tableau.

**FRÔLEMENT est le canal qui change tout.** C'est le seul qui informe *avant* le coût. Il dit
« quelqu'un t'a dans son arc » sans qu'on ait payé. Biologiquement, c'est l'interféron : le signal
qu'une cellule voisine émet avant même d'être détruite.

**Les demi-vies sont l'inverse de la portée.** Le signal qui vient de loin (BRUIT) est vague et
dure. Le signal local (IMPACT) est précis et s'éteint vite. C'est ce qui donne au champ sa
structure : un cœur net qui pulse, un halo flou qui traîne.

**SOI est un canal négatif.** Il sert à deux choses : ne pas tirer sur un ami (auto-immunité) et
ne pas converger au même endroit (le blob). Sans lui, la loi 5 est violée par construction.

Ce que l'agent lit : pas le champ entier. Un **patch local** (5×5 cellules autour de lui) plus le
**gradient** de chaque canal. Douze à vingt nombres. À comparer aux **deux** nombres d'arc de tir
qui ont déjà fait −28 % d'exposition.

---

## 6. La cascade — les réactions programmées

Chaque étage a quatre choses : un seuil d'entrée, une latence, une réaction, et un **ticket de
sortie**. L'oubli du ticket de sortie est la faute classique — c'est l'inflammation chronique.

| Étage | Entre quand | Latence | Réaction | Sort quand | Plafond |
|---|---|---|---|---|---|
| **0 — Veille** | — | — | tient son poste, arc de tir orienté | — | — |
| **1 — Réflexe** | IMPACT ou FRÔLEMENT franchit s₁ | immédiate | se plaque, pivote vers la source, rompt la LOS | signal sous s₁ pendant 3 s | l'individu seul |
| **2 — Local** | étage 1 tenu > 2 s, ou 2 agents en étage 1 | 1–2 s | le binôme appuie vers la source, le plus exposé bondit en arrière | plus personne en étage 1 | le binôme |
| **3 — Recrutement** | somme du champ sur la zone > s₃ | 5–10 s | l'escouade voisine remonte le gradient ; base de feu + manœuvre | zone sous s₃, ou objectif pris | **N max unités** |
| **4 — Adaptatif** | étage 3 tenu > 20 s sans progression | 20–30 s | l'officier change de plan : axe, contournement large, renonce | nouveau plan émis | — |
| **5 — Résolution** | champ global décroît | 10 s | retour au dispositif, on ré-arme les seuils, on écrit la mémoire | — | — |

Deux garde-fous, à mettre dès le premier jour :

**Le plafond de recrutement.** L'étage 3 ne peut jamais appeler plus de N unités. Sans ce nombre,
tu re-fabriques le blob que tu as déjà mesuré. Le plafond est un paramètre, pas une opinion : on
le balaye.

**Le ticket de sortie obligatoire.** Aucun étage n'a le droit d'exister sans condition de retour.
Un agent qui reste plaqué est un agent mort qui ne le sait pas encore.

---

## 7. Ce qui est câblé, ce qui est appris

Ne pas tout apprendre. C'est le partage qui a déjà marché chez toi (imiter, puis affiner).

**Câblé, jamais appris** — les étages 0, 1, 5. Les réflexes et le frein. Parce qu'ils doivent être
instantanés, prévisibles et certifiables. Un réflexe appris est un réflexe qu'on ne peut pas
garantir.

**Réglé, puis balayé** — les seuils s₁, s₃, les demi-vies, le plafond N. Ce sont des nombres. On
les fixe à la main, on les balaye, on garde ce qui passe le banc.

**Appris** — les étages 2, 3, 4. *Où* appuyer, *qui* bondit, *quand* recruter, *quel* axe. C'est là
que le RL a quelque chose à découvrir, parce que c'est un arbitrage sous coût.

La règle : **le RL choisit dans un vocabulaire, il ne l'invente pas.** Même logique que ton officier
LLM qui choisit dans un menu pré-calculé.

---

## 8. L'anticipation — la mémoire immunitaire

PRÉSAGE prédit aujourd'hui *ton exposition dans L pas*. Ici, on lui donne une cible plus utile :
**le champ dans L pas**. Où le signal va monter, pas où il est.

Mais l'anticipation immunitaire n'est pas une prédiction. C'est un **seuil abaissé**. Deux mémoires :

**Mémoire courte — la sensibilisation (durée : le run).** Une cellule où le canal IMPACT a
franchi le seuil garde une marque. Y revenir déclenche l'étage 1 pour deux fois moins de signal.
Le corps ne prédit rien : il est devenu chatouilleux à cet endroit.

**Mémoire longue — le priming (durée : la carte, la mission).** Certains lieux mordent toujours :
la fenêtre en enfilade, l'angle de rue, la crête. On entre déjà sensibilisé. C'est ce que fait un
soldat expérimenté, et ce n'est pas de la voyance — c'est un a priori sur la géométrie.

L'effet visé est mesurable et binaire : **la réaction part-elle avant le premier impact ?**
Aujourd'hui, la réponse est non par construction — il n'y a que l'impact pour informer.

---

## 9. Les quatre pathologies — à instrumenter dès la brique 1

Un système immunitaire mal réglé ne fait pas « moins bien ». Il tue son hôte. Chaque pathologie
a un compteur, et les compteurs entrent dans le banc **avant** les données.

| Pathologie | Ce qui se passe | Compteur |
|---|---|---|
| **Anergie** | seuils trop hauts, l'agent encaisse sans réagir | délai entre 1er impact et 1re réaction. **C'est l'état actuel.** |
| **Auto-immunité** | réaction sur signal ami, fratricide | tirs dont un ami est dans l'arc |
| **Choc cytokinique** | tout le monde répond au même signal → blob | rayon de dispersion de l'escouade quand le champ monte |
| **Inflammation chronique** | jamais de résolution, plus personne n'avance | temps en étage ≥ 2 sans gain de terrain vers l'objectif |

Le choc cytokinique est le risque n° 1, parce que tu l'as **déjà mesuré** sous un autre nom : les
blobs qui calent à 150 agents. SIROCCO, mal bridé, est une machine à en fabriquer.

---

## 10. Le plan — cinq briques, un verrou chacune

Une question par brique. Un seuil écrit **avant** le run. Rien ne passe sans son verrou.

### B1 — LE SIGNAL D'ALARME *(le plus petit, le plus rentable)*
Ajouter FRÔLEMENT et IMPACT directionnel à l'observation. Quatre nombres : intensité et direction,
maintenant, avec décroissance. Rien d'autre. Pas de champ, pas de cascade.
**Verrou** : exposition en baisse d'au moins 15 % à prise égale, sur le banc FIBUA ligne.
*Référence : deux nombres d'arc de tir ont donné −28 %. Quatre nombres qui disent « on te vise »
devraient faire au moins la moitié.*

### B2 — LE CHAMP
Étendre `carte.py` aux six canaux, avec demi-vie et diffusion par canal. Descendre la lecture au
niveau du soldat : patch local + gradient.
**Verrou** : atteindre au moins 80 % du gain du `_champ_danger` **omniscient**, sans lire une seule
information non détectée. On ne cherche pas à battre l'oracle — on cherche à ne presque rien payer
pour cesser de tricher.

### B3 — LA CASCADE
Les étages, les seuils, les tickets de sortie, la résolution.
**Verrou** : gain sur **prise-à-pertes** (pas la survie — ta leçon FIBUA), **et** les quatre
compteurs de pathologie sous leur seuil. Un gain avec un compteur dans le rouge est un échec.

### B4 — LE RECRUTEMENT
Le chimiotactisme entre escouades, avec le plafond N.
**Verrou** : le flanc reste payant (référence mesurée : ×2,37 en prise, ×0,51 en coût). Si le
recrutement fabrique un blob, ce ratio s'effondre — le verrou détecte la maladie tout seul.

### B5 — LA MÉMOIRE
PRÉSAGE sur le champ, plus la sensibilisation locale et le priming.
**Verrou** : la réaction précède le premier impact dans au moins la moitié des contacts, sans que
les faux départs explosent (à borner avant le run).

Puis **certification Arma**, selon ta règle : la sandbox est le gym, Arma est le juge. En trois
bras, pour isoler ce qui paie.

---

## 11. La couture Arma — ce qui existe, ce qui reste à vérifier

Le système ne vaut que si ses signaux existent côté Arma. Bonne nouvelle : ce sont des événements
natifs, pas des inventions de sandbox.

- **FiredNear** — se déclenche quand une arme tire près d'une unité. C'est littéralement le canal
  FRÔLEMENT, avec la distance et le tireur.
- **HandleDamage / Hit** — l'impact, avec la source. Le canal IMPACT.
- **Suppression** (LAMBS / `getSuppression`) — un état déjà calculé par le moteur.
- **Killed** — le canal PERTE.
- `knowsAbout` existe aussi, mais **on ne s'en sert pas** : c'est l'oracle, exactement ce qu'on
  cherche à supprimer.

À vérifier sur ton pont avant de graver : ces événements remontent-ils, à quelle fréquence, et
tiennent-ils la charge à 80 agents. C'est une mesure de plomberie, pas un pari — mais c'est une
mesure, et elle passe avant B1.

---

## 12. Ce que ce système est, en une phrase

Pas une IA qui comprend le champ de bataille. **Un corps qui a mal au bon endroit, assez vite pour
bouger.**

---

## 13. Le code — écrit, testé en isolation, **non branché**

Cinq fichiers dans `~/arma3-marl/`. Aucun ne touche `assault_terrain.py`, `carte.py` ni un env.

| Fichier | Ce qu'il contient |
|---|---|
| `sirocco.py` | `ChampSirocco` (6 canaux, vieillissement, diffusion, patch, gradient, masse) et `AlarmeLocale` (le DAMP par agent, `lire_b1()` = les 4 nombres) |
| `sirocco_cascade.py` | les 5 étages, seuils, latences, tickets de sortie, plafond de recrutement |
| `sirocco_memoire.py` | sensibilisation (le run) + priming (la carte), `seuil()` = le seul point qui touche au seuil |
| `sirocco_patho.py` | les 4 compteurs et le verdict, seuils pré-enregistrés |
| `sirocco_test.py` | le banc : 4 smokes + démonstration de chaîne + le test d'anticipation |
| `sonde_firednear.py` | la sonde Arma. **Écrite, syntaxe vérifiée, jamais exécutée.** |

État : `python sirocco_test.py` → **tout passe** (banc en isolation, GPU 3090).

---

## 14. Ce que l'écriture du code a appris

Trois choses qui n'étaient pas dans la conception, et dont deux auraient tué le système en
silence.

**Le dépôt doit saturer les quatre cellules voisines, pas une seule.** La lecture du champ est
bilinéaire ; un dépôt mono-cellule se relit entre 25 % et 100 % de sa valeur selon l'endroit où
l'agent se tient *à l'intérieur* de sa cellule. Un seuil qui bouge avec le pied est un seuil qui
ment — et rien ne l'aurait signalé.

**La mémoire dilate, elle ne diffuse pas.** Premier jet : la sensibilisation utilisait le même
floutage que le champ. Résultat mesuré : une marque posée valait 0.15 quarante pas plus tard et
n'abaissait plus le seuil que de 3 %. Le mécanisme était là, l'effet avait disparu. Un souvenir
ne se dilue pas : la zone dangereuse **gagne ses abords sans que son centre s'affadisse**. C'est
un `max_pool`, pas un `avg_pool`. Corrigé, l'anticipation passe de 0 à +20 pas.

**L'anticipation ne paie que si le signal précoce est faible.** Le banc joue le même scénario
dans deux régimes :

| Régime | sans mémoire | 1er passage | 2e passage | gain |
|---|---|---|---|---|
| frôlement fort (0.30) | pas 4 | pas 4 | pas 4 | **+0** |
| frôlement faible (0.06) | pas 29 | pas 29 | pas 9 | **+20 pas (14 s)** |

Si le frôlement suffit à lui seul à franchir le seuil, la mémoire n'a rien à apporter. **La
valeur de la brique B5 dépend donc directement de ce que `FiredNear` donne sur Arma** : fort et
continu → B5 est superflue ; faible ou intermittent → B5 est le cœur du système. C'est la sonde
qui tranche, pas nous.

---

## 15. Le prochain pas

**Faire tourner `sonde_firednear.py`.** C'est le seul point du système qui repose sur un pari, et
il conditionne à la fois B1 et B5. Rien d'autre ne mérite d'être branché avant sa réponse.

Deux choses restent à trancher, sans urgence :

1. **Les six canaux** — la liste te va, ou tu retires BRUIT (le plus douteux : Arma le donne mal) ?
2. **Le plafond de recrutement** — il est à 2 (la taille du binôme) par défaut. C'est le nombre
   qui décide si SIROCCO devient un blob ; il se balaye en B4.
