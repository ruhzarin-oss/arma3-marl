# Avis de Fable sur l'épisode multiple — 22/09/2026

*Saisi à la demande de Younes (« chaque épisode doit produire beaucoup de résultats : plus d'Oracle, plus
d'Architecte, plus plein de choses »). Idée soumise : un épisode Arma qui joue ~20 rencontres éloignées sur Altis,
chacune jouée sous les deux options, tout journalisé. Déposé avant toute ligne de code.*

## Verdict

Le principe tient, à une condition : l'épisode multiple est un **instrument de différences, pas de niveaux**. Ses
paires valent mieux que les actuelles sur un point (même charge, même naissance de serveur) et moins bien sur un
autre (deux sites au lieu d'un). **Le gain n'est pas ×20** : le budget de la machine est le nombre d'IA en vol.
Objectif réaliste : **×3 à ×6** en paires par heure si la charge le permet, ×1,5 à ×2 sinon, zéro si la perception se
dégrade dès deux cellules par serveur. Le premier test décide.

## Contaminations

- **De mission** (réparables par construction) : toutes les globales (`CHACAL_COMPROMIS`, `CHACAL_FIN`, `CHACAL_PHASE`,
  `CHACAL_FS`, `CHACAL_EST_SITE`, alarme, réserve, patrouille unique, journal des tirs coupé) deviennent un état **par
  cellule**. Point qui pique : `defenseurs_connus` et `ENNEMI_VU_EN_COMBAT` balaient la liste globale — une garnison en
  COMBAT à 12 km compterait pour une autre cellule. La contamination est symétrique.
- **De moteur** (à mesurer à tolérance zéro) : la connaissance de camp entre cellules à 3 km n'a jamais été mesurée —
  `targetKnowledge` croisé entre cellules doit valoir **exactement zéro** sur tous les échantillons. Son et tirs : ≥ 3 km
  entre entités, distance minimale journalisée toutes les 2 s, cellule sous 2,5 km marquée contaminée et exclue.
- **Oubliés** : la charge est commune à toutes les cellules (poison des niveaux, remède des paires) ; les facteurs
  d'épisode (météo, heure, lune, naissance du serveur) font de 20 cellules 20 tirages dans UN monde ; la géométrie fine
  peut ne pas être chargée loin du point de vue du serveur ; la phase de la patrouille devient un paramètre à tirer ; le
  hasard global rend une cellule non rejouable ; l'épisode dure le maximum des cellules (~15-17 min) — les cellules non
  finies sont **censurées**, étiquette à part ; l'ordonnanceur SQF (~1 000 sondes par tour) — la cadence réelle du
  journal est le canari ; les sites se réutilisent ; l'espace de l'Oracle se scinde en armes d'épisode et de cellule.
- Camps différents par cellule : non comme conception, oui comme diagnostic si une fuite est trouvée.

## La paire

Deux **cellules jumelles** : même case (type de menace, distance de passage, phase de patrouille, τ), deux sites de la
même strate de visibilité, même épisode, options croisées — et on **complète le carré** : chaque site joue l'autre option
dans un autre épisode à la même heure ; les deux estimations doivent concorder. Le plancher A/A (deux jumelles sous la
même option) coûte une paire par épisode, en continu. Rejeté : le même tronçon joué deux fois dans l'épisode.

## Combien de cellules par serveur

Une mesure : K ∈ {1, 2, 4, 8, 16}, 3 épisodes chacun, machine sinon vide. Portes : FPS serveur médiane ≥ 30, 5e
centile ≥ 20 ; délai de connaissance (debout, 150 m, nuit) médiane dans [3 ; 11] s et ≤ +3 s de la référence ; 95 % des
intervalles du journal dans [1,8 ; 2,5] s. K\* = le plus grand K qui passe. Ce balayage solde aussi le 52,8 contre 43,8.

## Certification — critères écrits d'avance

| | test | critère | si échec |
|---|---|---|---|
| C3 | charge | K\* ≥ 3 | K\* ≤ 2 → gain ≤ ×2 ; K\* = 1 → abandon |
| C2 | indépendance (10 cellules au contact + 10 sentinelles contre 10 calmes + 10 sentinelles, 120 sentinelles par bras) | `targetKnowledge` croisé = 0 sur 100 % des échantillons ; temps en COMBAT des sentinelles ±2 points ; IC de l'écart de compromission contient 0, demi-largeur ≤ 0,10 | chercher le canal ; espacer à 5 km ; diagnostic par camps ; sinon abandon |
| C1 | contrôles (1 négatif par épisode, 1 positif un épisode sur deux) | positif ≥ 90 % ; négatif ≤ 5 % | négatif > 5 % → fuite de la logique de compromission |
| C6 | dose-réponse : patrouille à 30 / 100 / 300 / 1 000 m, 30 cellules chacune | r(30) − r(1000) ≥ 0,30 ; aucune inversion adjacente > 0,10 | courbe plate → 2 réparations puis abandon |
| C5 | plancher A/A, 60 paires | IC contient 0, \|moyenne\| ≤ 0,08 ; écart-type publié = plancher de la poche | revoir la strate des sites |
| C4 | équivalence de niveau sur les 20 mondes A | **rapportée, pas gardée** : ± 0,08 du corpus, causes à ± 5 points | écrit à côté du nombre de cellules par serveur |

Épreuve de plus : rejouer sur le multiple la question de la confirmation en cours — signes contraires sur un effet
≥ 15 points → le multiple n'est pas arbitre.

**Qui juge quoi** : le multiple arbitre les différences (Architecte, Oracle, pièges, plancher) ; le banc seul reste
l'arbitre des niveaux et des verdicts finaux ; les mondes B n'entrent **jamais** dans le multiple.

## Portée

Un banc neuf **`chacalmulti`**, phase 2 seule, départ au point d'observation, arrêt en fin de phase 2, T_max 900 s. À
K = 1, c'est le banc seul de phase 2 — le témoin, gratuit, déjà ×1,5 à ×2 par la coupe de l'approche. Mais la coupe est
un changement de monde : lire d'abord **quand** tombent les compromissions (si > 30 % pendant l'approche, reculer le
départ) et le rôle de la réserve (> 5 % → garder, par cellule). À garder : `CHACAL_fnc_voit`, la compromission de
l'étape 0, les constructeurs de garnison et de patrouille, l'échantillonneur de sites, la règle d'attente, le format
`CHACAL|…` avec une colonne cellule. À jeter : l'état global, les phases 1 et 3-6, le commandant unique, la coupure des
tirs. À ajouter : `targetKnowledge` dans les deux sens toutes les 2 s, mode de comportement et transitions, `Fired` par
cellule, distance inter-cellules, cadence, censure, lecteur unique `lire_multi.py`.

**Pendant la confirmation** : construire oui ; fumer sous conditions (dossier distinct, instance ≥ 20, un serveur de
plus, rafales ≤ 20 min horodatées comme charge externe dans le journal de la confirmation, jamais de job dans la file
de `HMT_RUN`) ; **mesurer non** — C3 est impossible tant que la charge est confondue.

## Allocation par épisode de 20 cellules

2 contrôles (négatif chaque épisode, positif un sur deux, à ≥ 5 km) ; 2 plancher (une paire A/A) ; 8 Architecte (4 paires
jumelles, dont les répliques des derniers pièges confirmés) ; 6 Oracle (3 paires d'exploration) ; 2 poche (points de
grille non visités). Épisode en quarantaine si le négatif ou la paire A/A déraille. **Ce même épisode remplace le banc
miroir de l'étape 2 de la poche** (toutes les cellules journalisent leur perception de nous, le passage en COMBAT, le
premier tir) ; la cuisson de géométrie reste hors ligne.

## Plan

| étape | construit | mesure | succès | arrêt | coût |
|---|---|---|---|---|---|
| 0 lecture | rien | moment des compromissions vs fenêtre ; rôle de la réserve ; distances des 20 sites A ; inventaire des globales ; phase de la patrouille à la décision | quatre lectures écrites | > 30 % dans l'approche → départ reculé | ½ jour, 0 ferme |
| 1 construction | `chacalmulti`, cellule, journal, lecteur | fumée K = 2 : 1 positif + 1 négatif | positif compromis, négatif non, cadence 2 ± 0,5 s, 0 erreur SQF | toute erreur SQF | 3-4 jours |
| 2 charge C3 | — | K ∈ {1..16} | K\* ≥ 3 | K\* = 1 → abandon (~3 h perdues) | ~3 h, après la confirmation |
| 3 indépendance C2 | — | 480 cellules | zéro fuite | canal non réparable en 2 itérations → abandon | 3-6 h |
| 4 contrôles et plancher | — | ~900 cellules | dose monotone, négatif ≤ 5 %, A/A nul | courbe plate → abandon | 5-10 h |
| 5 épreuve prospective | — | la confirmation rejouée | même signe | signes contraires → pas arbitre | ~4 h |
| 6 service | allocation | cartes de contrôle | — | quarantaine | continu |

Ferme : 15-25 h ; deux semaines jusqu'à la certification si K\* ≥ 3 ; abandon possible à J+5 pour trois heures de ferme.

**Le gain, honnêtement** : K\* = 6 → ~90 paires/h (×5-6) ; K\* = 3 → ~45 (×3) ; K\* = 2 → ×2 ; K\* = 1 → ×1,5-2 par la seule
coupe de l'approche. « Mieux vaut 3 cellules qui perçoivent comme le banc seul que 20 qui perçoivent autrement. »

## Pièges

Publier un taux sans le nombre de cellules par serveur ; certifier sur des niveaux ; laisser un agrégat lire une liste
globale ; croire l'indépendance acquise à 3 km ; confondre censure et issue ; tester la charge avec des cellules vides ;
oublier que le contrôle positif charge et fait du bruit ; mesurer C3 pendant qu'autre chose tourne ; faire entrer un
monde B ; tirer une règle d'un taux par classe à 15 exemplaires ; lancer l'étape 2 sans avoir lu l'étape 0.

*Note d'exécution : la confirmation en cours est posée PAR la boucle `HMT_ORACLE` ; elle ne s'arrête donc pas pendant
les fumées — celles-ci sont annotées comme charge externe dans son journal, comme Fable le demande.*
