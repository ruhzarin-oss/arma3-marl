# DÉPÔT — L'ARBITRE SUR CANDIDATS (contrôle dynamique)

Date de dépôt : 2026-08-30 · Code : `arbitre.py`, `controle_arbitre.py` · **AUCUN run lancé à ce jour** (le pont est tenu par `force.py`). Ce critère est écrit AVANT les données.

## LA REVENDICATION (une seule)
Un arbitre qui choisit **par échantillonnage** parmi K candidats (8 directions × 2 portées
15/30 m + « continuer » + « rester ») **annotés par le moteur** (être-vu, voir, possibilité de
supprimer — primitives de `champ2.py`, contre le **journal** de contacts, jamais la
vérité-terrain), avec des **coefficients mesurés** (vu ×2,45 ; supprimé ×29,81
[DEPOT_BARREAU] ; être-vu = 2× voir [+75 %, 563 k obs] ; cote suppression ×27,9), perd
**moins d'hommes** qu'une sélection **uniforme** sur les MÊMES candidats et la MÊME
exécution. La seule chose isolée est le SCORE.

## MÉTRIQUE, EFFET MINIMAL, SEUIL
- **Principale : PERTES** (hommes perdus sur 8), par **bloc gelé apparié** (même graine de
  scène `marge.scene`, tous les bras). Les tarifs sont des rapports de taux de MORT — la
  revendication porte sur les morts.
- **Effet minimal pré-inscrit : 1,0 perte sur 8** (12,5 pts) — du même ordre que le seul
  tarif de survie déjà chiffré (tenue : 31,4 % → 19,9 %, ~11,5 pts).
- **Seuil final = max(1,0 ; 2 × plancher de bruit)**, le plancher étant mesuré par
  `arbitre` vs `arbitre_bis` (même score, graines d'échantillonnage différentes) — **avant
  tout seuil**.
- Secondaires (rapportées, **non décisives**) : avance (m vers HMT_OBJ), découverte
  (seuil déposé 1,44).

## ORDRE DE LECTURE — aucun verdict hors de cet ordre
0. **PLANCHER** : |arbitre − arbitre_bis| moyen par bloc. Fixe le seuil. S'il dépasse
   l'effet minimal → le banc ne peut rien dire, **AUCUN VERDICT**.
1. **uniforme − arbitre ≥ seuil** sur les pertes. Sinon **RIEN D'AUTRE N'EST LU**.
2. **anti − arbitre ≥ seuil** : l'anti-score (signes des seuls termes TARIFÉS inversés :
   maximiser être-vu, pénaliser la suppression ; progrès et immobilité non inversés) doit
   **PERDRE d'au moins l'effet revendiqué**. Première façon d'échouer du contrôle positif.
3. **|melange − uniforme| ≤ 2 × plancher** : les annotations permutées entre candidats
   doivent faire retomber l'arbitre sur l'uniforme. Deuxième façon d'échouer. Si melange
   s'écarte, l'arbitre lit autre chose que les annotations → **BANC AUTO-INVALIDE**.
4. **Garde du tempo** : avance(arbitre) ≥ avance(uniforme) − 30 m.

## LES LECTURES PERDANTES, ÉCRITES D'AVANCE
1. **CONTRE L'INCONNU** — si > 50 % du feu reçu vient d'eid **hors journal** au moment de
   l'événement (compté dans le code : `feu_inconnu/feu_total`), les annotations ne pricent
   pas ce qui tue ; arbitre ≈ uniforme jugera le **capteur**, pas l'arbitre.
2. **CONTRE LE TEMPO** — l'arbitre peut acheter ses pertes en refusant d'avancer. Si la
   garde n°4 tombe, le verdict est « il survit en n'entrant pas » ⟨tout-ce-qui-fige-un-
   homme-coûte⟩ — une vraie réponse, pas un échec du banc.
3. **HORS DU MONDE TARIFÉ** — les tarifs (2,45 ; 29,81) viennent d'un autre banc
   (432 transitions). Si l'anti ne perd pas **alors que** les annotations discriminent,
   les tarifs ne transfèrent pas à CE monde-ci : les re-mesurer ICI avant de toucher au score.

## CE QUI EST DIMENSIONNÉ (pas mesuré) — et le dit dans le code
λ_mètre (30 m gagnés = un être-vu), pente d'immobilité (30 s = un être-vu ; la MONOTONIE
sans plateau est la spécification), τ_journal 40 s, τ_feu 12 s, température
d'échantillonnage (un demi-vu), espacement 8 m (avant contact seulement), portée utile
300 m, garde du tempo 30 m. Chacun est un SEUIL au sens de ⟨champ-spatial⟩ « un seuil se
dimensionne » — aucun n'est un poids appris, **aucun ne sera ajusté après lecture des
données de ce banc**.

## ORDRE D'EXÉCUTION (quand le pont sera libre)
`controle_arbitre.py --scenarios 6` (5 bras × 6 blocs, ~2 h 30). Résultats :
`/mnt/data/controle_arbitre.json`. La fonction `lecture()` applique l'ordre ci-dessus
mécaniquement — y compris les trois lectures perdantes.

## AMENDEMENT 1 — 2026-08-30, AVANT TOUT RUN, AUCUNE DONNEE LUE

**Rectification.** J'ai d'abord ajoute ici une garde anti-derobade en croyant qu'elle manquait.
Elle ne manquait pas : c'est la **ligne 4, « la garde du tempo »**, deja ecrite dans
`controle_arbitre.py` et deja DECISIVE (comptee dans le ET final). Le present amendement ne
cree donc rien ; il precise une seule chose.

**Ce qui est precise.** La garde du tempo compare l'avance de `arbitre` a celle de `uniforme`
avec une tolerance **dimensionnee a 30 m** (GARDE_TEMPO). Cette tolerance est declaree, pas
mesuree. On y ajoute la lecture stricte :

> **G3 · si l'avance de `arbitre` tombe sous celle de `uniforme` de plus de la tolerance, le
> resultat est rendu comme GAIN PAR DEROBADE** — annonce, chiffre, et jamais compte comme une
> victoire. C'est la porte G3 du gymnase mot pour mot : *« le gain ne vient pas de se terrer »*.

**Pourquoi c'est necessaire ici.** La metrique principale du depot est les PERTES, alors que le
critere du projet a ete tranche par Younes : *« ce qu'on veut c'est qu'ils agissent, qu'ils
bougent, qu'ils decouvrent »*. Avec les seules pertes pour juge, un arbitre qui se terre gagne.
La garde de Fable l'interdit deja ; l'amendement l'inscrit dans le depot pour qu'aucune lecture
future ne puisse la traiter comme secondaire.

**Justification sans reference aux resultats** — aucun run n'a ete lance ; ce texte est ecrit
avant la premiere donnee.

## AMENDEMENT 2 — 2026-08-30, apres la mesure du PLANCHER, avant toute comparaison de bras

**Ce qui a ete lu, et uniquement cela.** Le run du 30/08 a 6 blocs s'est arrete a la ligne 0 :
plancher 3,67 perte(s) pour un effet minimal de 1,0 -> AUCUN VERDICT. J'ai ensuite lu le bruit
du **couple nul** (`arbitre` contre `arbitre_bis`) sur les trois metriques. **Je n'ai PAS lu
`arbitre` contre `uniforme`, ni contre `anti`, ni contre `melange`.** Le present amendement est
donc fonde sur une propriete de l'INSTRUMENT, jamais sur qui gagne.

| metrique | ecart-type du couple nul | variabilite relative | n pour l'effet vise |
|---|---|---|---|
| pertes | 4,41 / 8 | **120 %** | 78 blocs (~36 h) pour 1,0 perte |
| avance | 66,2 m | 460 % | 20 blocs (~9 h) pour 30 m |
| decouverte | 1,76 | **22 %** | 16 blocs (~7 h) pour 1,44 |

**Ce qui change.**
1. **Les PERTES cessent d'etre la metrique principale** — non par preference, mais parce qu'elles
   sont **inmesurables au cout du banc** : 36 h pour un seul mort sur huit. Elles restent
   rapportees, non decisives.
2. **La DECOUVERTE devient la metrique principale**, seuil inchange **1,44** (deja depose,
   plancher 7,42 / sigma 1,78 mesure le 26/08). C'est aussi le critere tranche par Younes :
   *« ce qu'on veut c'est qu'ils agissent, qu'ils bougent, qu'ils decouvrent »*.
3. **L'AVANCE reste decisive** au titre de la garde du tempo (ligne 4), inchangee.
4. **n passe de 6 a 20 blocs.** A n=6 le bruit du couple nul vaut 1,50 pour un seuil de 1,44 :
   **rien n'etait lisible, sur aucune metrique**. A n=20, deux erreurs-types valent 0,79.

**Ce qui ne change pas** : l'ordre de lecture (0 -> 4), les deux facons d'echouer (anti doit
perdre ; melange doit retomber sur l'uniforme), la garde anti-derobade, les trois lectures
perdantes, et tous les parametres dimensionnes du score — **aucun ne sera ajuste**.

**Regle appliquee** : ⟨un seuil se dimensionne : plancher de bruit mesure + n necessaire pour le
detecter⟩. Le run de 6 blocs n'etait pas un echec, c'etait la mesure du plancher que cette regle
exige AVANT tout verdict.

## AMENDEMENT 3 — 2026-08-30, run des 20 blocs EN VOL, aucune de ses donnees lue

Ecrit apres la revue de Fable, **avant toute lecture des 20 blocs**. Le run tourne ; seul compte
ce qui est ecrit avant lecture.

### 3.1 RECTIFICATION DE REGISTRE — une phrase de l'amendement 2 etait trop genereuse
L'amendement 2 dit : *« je n'ai PAS lu `arbitre` contre `uniforme`, ni contre `anti`, ni contre
`melange` »*. **C'est faux pour les PERTES** : la table des cinq bras du run a 6 blocs etait sous
les yeux au moment de la decision. **La cecite ne vaut que pour la DECOUVERTE**, qui n'a jamais
ete lue bras contre bras.

Ce qui reste vrai, et qui doit etre inscrit avec la faute : **la donnee vue ne flattait pas le
bras defendu.** Sur les pertes, `anti` faisait 3,17 contre 3,67 pour `arbitre` — l'anti-score
BATTAIT l'arbitre. Le changement de metrique ne pouvait donc pas etre un choix opportuniste :
il abandonne une metrique ou l'arbitre PERDAIT.

### 3.2 LE STATUT DES DEUX JEUX
- Les **6 blocs** du 30/08 sont BRULES : jeu de REGLAGE. Ils ont servi a mesurer le plancher et
  a redimensionner n. Ils ne seront **jamais** mis en commun avec les 20.
- Les **20 blocs** en cours sont le jeu de CONFIRMATION. Ils n'ont pas ete regardes.
- **CLIQUET** : tout amendement ecrit APRES la moindre lecture des 20 blocs les brule a leur tour,
  et exigera des blocs NEUFS. Il n'y aura pas de quatrieme amendement gratuit.
- `pertes` et `avance` deviennent DESCRIPTIVES : aucun langage de verdict ne leur est applique.

### 3.3 LE CONFLIT SCORE ↔ METRIQUE, ecrit AVANT les donnees
Le score **minimise l'etre-vu**. Or `knowsAbout` est de CAMP et la detection part des hommes vus :
se cacher coupe les lignes de vue **dans les deux sens**. Un arbitre qui s'expose peu peut donc
decouvrir moins **par construction**. Contre-mecanisme : un mort ne decouvre rien — survivre, c'est
percevoir plus longtemps. Lequel domine est EMPIRIQUE, et le bras `anti` — qui cherche
l'exposition — en est le temoin exact.

> **LECTURE PERDANTE (ajoutee).** Si `anti` egale ou bat `arbitre` en decouverte, la metrique
> recompense l'APPETIT D'EXPOSITION, pas la qualite du sensing. Le verdict porte alors sur la
> METRIQUE, pas sur le score — et l'instrument est a rechoisir, sans rejouer le meme banc en
> esperant autre chose.

> **LECTURE GAGNANTE (explicitee comme HYPOTHESE, pas comme evidence).** `arbitre > uniforme` ET
> `arbitre > anti` signifierait que **l'economie d'exposition produit de l'information en
> sous-produit**. C'est l'hypothese reellement testee. Le score ne maximise PAS la decouverte —
> c'est ce qui le met a l'abri du wireheading, et c'est aussi ce qui rend l'hypothese refutable.

### 3.4 CE QUI EST VERIFIE, PAS SUPPOSE
`controle_arbitre.py:72` — `scene(b, graine)` est appele AVANT le bras : tous les bras d'un bloc
jouent **les memes placements**. La geometrie initiale est donc eliminee de l'appariement, et le
plancher de 3,67 pertes ne lui est pas imputable.

### 3.5 PARALLELISATION — REFUSEE POUR CE RUN
Arma est mono-thread par serveur. Sous ~15–20 FPS serveur, l'IA elle-meme change (reactions,
cadence de tir, chemins) : ce n'est pas du bruit ajoute, **c'est un autre monde**. Et l'effet peut
interagir avec le bras — une politique qui ordonne davantage souffre plus de la latence — donc
confondant DE BRAS, pas seulement de niveau.
- Le run en cours **finit a UNE instance**. Les deux regimes ne seront jamais melanges dans une
  meme pre-inscription.
- Avant tout run a 4x : une PORTE — couple nul, FPS serveur, et distribution des intervalles de
  decision, mesures a 1x et a 4x. Elles doivent coincider. ⟨une porte certifie DANS SON MONDE :
  la sonde 13/13 a une instance ne dit rien de quatre⟩
- Si adoptee : chaque instance execute **TOUS les bras** — l'instance devient un facteur BLOQUE,
  jamais confondu avec le bras.

### 3.6 RESERVE SUR LE « 78 BLOCS »
Un ecart-type estime sur 6 differences a lui-meme un intervalle enorme. Les 78 blocs (et les 20)
sont un ORDRE DE GRANDEUR, pas un nombre. Cette reserve est inscrite pour qu'aucune lecture future
ne traite ces n comme exacts.
