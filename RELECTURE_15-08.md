# RELECTURE PROFONDE — état réel au 15/08/2026, et reprise sur base saine

Objectif de Younes, redit ce soir : **un agent qui comprend et sait jouer Arma, et remplir
des missions.** Pas un dossier. Tout ce qui suit est jugé là-dessus.

---

## 1. OÙ ON EN EST, EN UN CHIFFRE

**L'agent ne sait pas jouer Arma.** Il prend l'objectif **8 fois sur 67 — 11,9 %**,
IC95 [4,2 ; 19,7], contre **59,4 %** dans son gymnase. Il est dégénéré **un épisode sur
quatre** (gel 25,4 %, IC [15,0 ; 35,8], référence gymnase 3,1 % exclue).

Décomposition faite : retirer toute la dégénérescence achèterait **4 points**, pas 45.
**Le monde est le coupable**, pas l'optimisation.

---

## 2. CE QUI EST ÉTABLI, ET QUI TIENT

**Certifié sur Arma, indépendant du gymnase — l'actif VV&A :**
- toucher **75 → 26 %** entre 25 et 200 m ;
- angle mort **absolu** : 18/18 dans le cône contre 0/26 hors ;
- être vu tue **2× plus fort** que voir ne protège (+75 %, 563k obs) ;
- le flanc fait **ARRIVER** sans protéger (+17,3 pts, p=0,012) ;
- coût = **exposition par mètre gagné** (ratio 9,34, p=0,001, 1111 engagements) ;
- suppression **subie** ×10 ; sursis de l'arc **4 s** ; suppression = 8 % de capacité.

**Établi ces deux jours :**
- `setVelocity` est une **impulsion**, pas une consigne : 2,58 m par pas émise une fois,
  **20,22 m** réémise à 10 Hz. Corps réparé ×14,1 ;
- **le cerveau transfère, le corps non** — rendement de pilotage 0,42 gymnase contre 0,46 Arma ;
- **le couvert du gymnase protège sans cacher** : `los = _losc(hm)` ignore `cover`,
  `dmg = p·los·tir·(1 − 0,7·incover)`. Masquage mesuré **1,08** ;
- **A retenue sur la carte seule** : le couvert est **3× plus loin** sur Arma (0,033 contre 0,100) ;
- **le tarif ne l'explique pas** : Arma facture l'exposition **moins** cher (2,87 contre 5,77) ;
- classement gymnase : FRONTAL 12,8 · FLANC 34,3 · **SCRIPT 46,1** · POLITIQUE 51,1 ;
- **FLANC sur Arma : 0/18**, hommes mobiles, 15/18 anéantis.

**Le résultat le plus lourd de conséquence :** au gymnase, **le feu-et-mouvement scripté
fait 46,1 % contre 51,1 % à la politique apprise.** Trente lignes sans apprentissage
capturent neuf dixièmes. **Le vocabulaire porte presque tout ; l'optimisation ajoute
5 points sur 51.**

---

## 3. CE QUI EST MORT OU RETIRÉ

- **L'étage 1** : le bras natif n'a jamais existé, 94 % du feu partait sans ordre. Gelé.
- **L'arc** : −40,8 pts, tentative unique consommée.
- **La fidélité en coefficients** : **cible épuisée, pas cible fausse** ⟨Fable⟩. Une
  inversion de classement conditionnelle (1,73 contre 2,87) ne se répare par aucun
  coefficient — multiplier tous les tarifs par k la préserve.
- **`doSuppressiveFire`** : oriente sans déclencher.
- **Le linteur SQF** : il prévient lui-même qu'il ne comprend pas le SQF. Abandonné.
- Six sursitaires + la cohorte « armure » à verser (boucle fermée, courbes du gymnase).

---

## 4. L'AUDIT MÉCANIQUE — CE QUI RESTE PIÉGÉ

543 fichiers de banc existent ; **19 sont en service**. Sur ces 19 :

| famille | fichiers marqués |
|---|---|
| arme au sac (`createUnit` sans `selectWeapon`) | **4** |
| `disableAI` posé sans être rendu | **3** |
| contrôle d'état sans acte | **0** |
| définitions déjà réfutées encore présentes | **2** |

⚠️ **L'audit flagge un RISQUE, pas une panne** : `sonde_impact.sqf` porte trois marques et
a pourtant tiré 98 coups. Et son détecteur « vieilles définitions » a des faux positifs sur
les commentaires. **Cet audit lui-même n'a pas de contrôle positif** — il ne prouve pas
qu'il attraperait une faute qu'on lui cacherait.

Sur les 543 fichiers, les mêmes familles touchent **185** et **182** fichiers. C'est la
preuve chiffrée du diagnostic de Fable : *« une réparation dans un fichier n'est pas une
réparation, c'est une réparation dans UNE copie. »*

---

## 5. LE COÛT RÉEL DE LA JOURNÉE

**Neuf fautes d'instrument, zéro verdict faux.** Les contrôles déposés les ont toutes
attrapées — c'est un succès d'intégrité. Mais **≈ 13 h de machine perdues**, 1,5 h par faute.

Trois d'entre elles étaient **la même** : l'arme au sac, réparée le matin dans un fichier,
non reportée dans deux autres.

**La métrique change** ⟨Fable⟩ : plus « fautes par jour » — inatteignable à zéro — mais
**heures de machine perdues par faute**, de 1,5 h à 0,02 h.

---

## 6. LA REPRISE — SOCLE, PRÉVOL, CLIQUET

**SOCLE.** Quatre briques dont tous les bancs héritent au lieu de les réécrire : scène ·
armement (`addWeapon` + `selectWeapon` + relecture de `currentWeapon`) · pilotage (l'état
`disableAI` appartient au socle, jamais posé à la main) · grandeurs (**une seule**
définition de `slope`, `los`, `dcover`, avec unité et convention).

**PRÉVOL.** Après la mise en scène, le socle **relit chaque état qu'il a posé** et refuse
de lancer si la relecture diffère. Plus trois preuves d'**actes** : une balle réelle
(`Fired`), 5 m parcourus en 10 s, `currentWeapon` non vide et FSM active.
**60 secondes. Pas de prévol vert, pas d'épisode.**

> *« La règle 16 existait et n'a pas tourné, parce que c'est TOI qui devais la faire tourner.
> La volonté n'est pas un mécanisme. »*

**CLIQUET.** Chaque faute attrapée devient le soir même un test permanent du prévol.
**Neuf fautes aujourd'hui = neuf tests.** Et un verdict porte désormais **l'empreinte de son
instrument** — version du socle + rapport de prévol, sha256. Sans empreinte, non citable.

**Ne pas ralentir** : la vitesse n'a pas produit l'arme au sac, **la réécriture l'a produite**.

---

## 7. LA DIRECTION, APRÈS LE RECADRAGE

> *« La méthode s'est trompée d'ÉTAGE. Le transfert réussit à l'altitude où les deux mondes
> partagent les mêmes types. »*

Le commandant qui parle en **intentions** a transféré (48 % contre 13 % en live). Le soldat
qui parle en **vitesses** non. L'étage soldat se rebâtit ainsi :

**La géométrie propose, la politique dispose.** Un proposeur déterministe fabrique 6
candidats (3 couverts vers l'objectif via la coque 12 rayons, 2 points d'angle mort, 1
couvert arrière) ; **quatre verbes fermés** — `BOND(k)`, `APPUYER(secteur)`, `TENIR`,
`DÉCROCHER(k)` ; une décision **toutes les 5-10 s**, jamais en hertz ; ~33 nombres, tous
calculables à l'identique des deux côtés.

**Et le gymnase doit CLASSER comme Arma classe, pas FACTURER comme Arma facture** —
tolérance d'amplitude ×3, **tolérance de signe nulle**.

---

## 8. L'ORDRE DES TRAVAUX

1. **Le socle et le prévol** (une journée). Se rembourse en un jour.
2. **Les 9 fautes versées comme tests** du prévol.
3. **Migrer les 5 bancs en service.**
4. Reprendre les 3 bras morts ce soir — natif, feu forcé, scripté — **sous prévol**.
5. Retyper le couvert au gymnase (le **type**, pas les coefficients) + le cliquet
   d'exposition, puis pré-entraîner et **finir sur Arma**.
6. Critère de fin : **3 missions de la batterie remplies au-dessus de la baseline**,
   sans anéantissement.
