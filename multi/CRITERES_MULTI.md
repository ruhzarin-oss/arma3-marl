# Épisode multiple `chacalmulti` — critères écrits AVANT le premier épisode (22/09/2026)

Avis de Fable : `multi/AVIS_FABLE_22_09.md` (c6d99f0). Younes, 22/09 : « tu stop tout et on teste ça maintenant, on le
calibre pour que ça fonctionne ». Ferme arrêtée à 12 h 50 (0 serveur, file vide, 16 jobs de l'Oracle mis de côté).

## Ce qui a été construit

Une cellule = **le banc seul tout entier** (`bancs/chacaloracle/mission.Altis`), recopié et renommé `CHACAL_` → `MC<k>_`.
Chaque cellule a son monde, sa garnison, son Oracle, son détachement, son enregistreur et son verdict ; la logique de la
phase 2 est celle du banc seul, ligne pour ligne. Les seules retouches (`construire_mission.py`, chacune comptée et
refusée si elle ne s'applique pas exactement une fois) sont les points où le code touche le moteur entier :
`createGroup` (le groupe porte sa cellule), `allUnits` de la garnison, l'enregistreur (ses unités seulement), le
gestionnaire de morts (ses morts seulement), le départ commun, le canari posé loin des autres cellules, la lecture des
paramètres. Journal préfixé `M|k|` ; le lecteur `lire_multi.py` le démultiplexe et fait lire chaque cellule par le
lecteur du banc seul, portes comprises. Vérifié hors ligne sur un vrai épisode : verdict, portes, en-tête et volumes
identiques au banc seul.

Ajouté : compteur d'images non ordonnancé (charge), **sonde de connaissance** hors cellules (debout, 150 m, nuit, regard
posé ; un cycle par minute), **journal croisé** toutes les 2 s (ce que chaque chef de groupe connaît d'une autre
cellule, ennemis et amis) avec son contrôle positif (l'observateur de la sonde doit être vu connaître sa cible), censure
à `T_max`, retrait des unités d'une cellule finie.

## Fait mesuré avant tout épisode : la géographie plafonne K

Emprise d'un monde = segments poser → route → crête → site → regroupement + base de la réserve (149 mondes connus,
`multi/emprises.json`). Plus grand ensemble de mondes deux à deux à ≥ 3 km : **5** (8, 120, 217, 223, 230) ; à 2,5 km : 6 ;
à 2 km : 7. Parmi les 20 mondes A : 3 à 3 km, 4 à 2 km. **K = 8 et K = 16 sont impossibles à l'espacement de Fable** :
le balayage C3 porte donc sur K ∈ {1, 2, 3, 5}, et K\* ≤ 5 quoi qu'il arrive (gain plafonné à ×5 par serveur).

## Étape 1 — fumée (2 épisodes, K = 2, instance 1, machine sinon vide)

Épisode 1 : cellule 1 = monde 8, **contrôle positif** de l'Oracle (`oracle_ctrl` 1 : la patrouille est posée sur eux et
tenue au contact 3 min) ; cellule 2 = monde 120, **contrôle négatif** (palier 9 : aucun ennemi). Épisode 2 : les mondes
échangés. Paramètres communs = ceux des épisodes de l'Oracle (palier 2, départ 2, arrêt 2, effectif 20, fenêtre 120 s,
avant 80 m, balayage 1, Oracle δ 30 s, b 8, ν 15, ε 15, réserve 2). `T_max` 1 500 s.

La fumée PASSE si, sur les deux épisodes :
1. 0 erreur SQF (toutes cellules et commun) ;
2. les 4 cellules finies et ACCEPTÉES par le lecteur du banc seul, monde conforme à la table (écart du site < 5 m) ;
3. les 2 positifs compromis, les 2 négatifs non compromis ;
4. cadence du journal : médiane dans [1,5 ; 2,5] s dans chaque cellule ;
5. journal croisé : **0 connaissance ennemie croisée** entre cellules, et contrôle positif vu dans ≥ 80 % des cycles où la
   sonde a connu sa cible ;
6. sonde : ≥ 5 cycles, délai médian mesuré (pas de seuil à la fumée).
Toute erreur SQF ou tout écart d'identité arrête la suite : on répare, on refume.

## Étape 2 — charge C3 (après la fumée ; un seul serveur à la fois, machine sinon vide)

K ∈ {1, 2, 3, 5}, 3 épisodes chacun, mondes emboîtés (K = 1 : monde 8 ; 2 : + 120 ; 3 : + 217 ; 5 : + 223, 230).
Cellules : menace de phase 2 en rotation (5, 4, 3, 1, 2), option en alternance (1, 2), Oracle actif. `T_max` 1 500 s.
Ordre de passage : K = 1, puis 5, 5, 5, puis 1, 1, puis 3 × 3, puis 2 × 3 (la réponse décisive d'abord).

Portes par K (sur les images mesurées pendant que les K cellules sont TOUTES actives) :
- FPS serveur médiane ≥ 30 et 5e centile ≥ 20 ;
- délai de la sonde : médiane dans [3 ; 11] s et ≤ médiane à K = 1 + 3 s ;
- cadence : ≥ 95 % des intervalles VC dans [1,8 ; 2,5] s (toutes cellules). **Si K = 1 échoue lui-même à cette porte**, elle
  devient « ≥ valeur de K = 1 − 2 points » (écrit maintenant : le banc seul sous la ferme pleine était à 94,4 %) ;
- 0 erreur SQF, 0 connaissance ennemie croisée.

**K\* = le plus grand K qui passe.** K\* ≥ 3 → on continue (C2, C1…) ; K\* = 2 → gain ≤ ×2, on le dit ; K\* = 1 → abandon
du multiple (reste la coupe de l'approche). Lecture UNIQUE après le dernier épisode de K = 2 ; aucun épisode rejoué pour
changer une porte. Le taux de compromission par K est RAPPORTÉ, jamais gardé (C4).

## Amendement 1 — après l'épisode 1 de la fumée v1 (13 h 08-13 h 20), avant toute mesure C3

La fumée v1 (commit 49687b1) a tourné sans erreur SQF, deux cellules montées à 10,9 km, le positif compromis 0,5 s
après la pose de la patrouille (`ENNEMI_VU_EN_COMBAT`). Elle a montré trois défauts ; la v1 devient une fumée de
diagnostic, la fumée qui compte est la v2, rejouée en entier.

1. **Horloges** : l'Oracle, le contrôle positif et la machine à phases partaient au MONTAGE de la cellule. Dans le
   multiple, la cellule 1 est montée jusqu'à ~1 min 30 avant la dernière : son Oracle aurait décidé 3 fois avant que
   son détachement ne bouge. Réparé : toutes les horloges attendent `MULTI_DEPART`, qui joue le rôle du chargement du
   banc seul (Oracle à t0, phase 2 à t0 + 8 s, contrôle à t0 + 30 s, canari à t0 + 20 s, comme dans le banc seul).
2. **Sonde** : un observateur seul, qui pivotait par `doWatch`, n'a rien connu en 45 s (2 cycles sur 2). Refaite comme le
   banc de seuil du 18/09 : dix hommes du détachement TOURNÉS vers la cible avant de la regarder (patch 2786e65), cible
   posée au point testé, visibilité RÉELLE mesurée (`checkVisibility` < 0,3 → cycle refusé, compté à part), 60 s.
3. **FPS** : 27,5 à 28,2 images/s à K = 1 sur machine vide avec 25 unités, et 28 dans le banc seul sous la ferme pleine :
   le serveur plafonne vers 28, quelle que soit la charge. La porte absolue « médiane ≥ 30 » est inatteignable par le
   banc seul lui-même. Elle devient : **médiane(K) ≥ médiane(K = 1) − 3 et 5e centile ≥ 20** (le plancher de Fable reste).
4. **Canari des positifs** : un positif compromis finit sa phase ~30 s après le départ, avant la fin du cycle du canari
   (~85 s) ; ses portes « canari » échouent par construction. Pour les cellules positives, toutes les portes sauf celles
   du canari sont exigées ; les cellules négatives gardent toutes leurs portes. (Écrit après avoir vu l'épisode 1.)

## Amendement 2 — après l'épisode 1 de la fumée v2 (13 h 16-13 h 23), avant toute mesure C3

Épisode 1 v2 : 0 erreur SQF ; négatif ACCEPTÉ, non compromis, monde conforme (écart 0 m), cadence médiane 2,02 s
(100 % dans la bande) ; positif compromis (`ENNEMI_VU_EN_COMBAT`, 26 s après l'ouverture de la phase) ; sonde connue
7 fois sur 7, délai médian 3,5 s (2,7 à 4,6), dans la bande du banc de référence ; 15 cycles refusés pour cible
masquée ; journal croisé : 0 ennemi, 0 ami, contrôle positif vu 10 fois ; FPS 28,2 (K = 2, les deux actives).
Un défaut : la porte « rien après FINI » du positif échoue — le serveur tourne pour l'autre cellule, et le canari du
positif écrit encore après son verdict. Dans le banc seul le serveur est arrêté sur FINI. Réparé : **après sa ligne
FINI, une cellule n'écrit plus que des lignes OK et AVERT** (celles que le lecteur du banc seul tolère). L'épisode 2 de
la fumée v2 tourne avec l'ancien code ; la réparation est vérifiée par le premier épisode du balayage C3 (K = 1) : si la
porte « rien après FINI » y échoue, ou si une erreur SQF apparaît, le balayage s'arrête.
