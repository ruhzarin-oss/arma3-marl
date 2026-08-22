# ✅ NATIF = 59,6 % — mesuré sur un monde à ZÉRO erreur

**22/08/2026, 02 h 09.** Prédicat `DEPOT_NATIF.md`, écrit le **16/08 avant tout épisode**.
Socle **5.5.0-21082026**, canal `sv_vz_preserve_10hz`. 128 épisodes complets sur 134.
Lecteur : `lire_natif.py`.

## LE CHIFFRE

**PRISE** = un attaquant **VIVANT** à moins de **25 m** (`assault_terrain.py:814`).

| | prises | n | taux |
|---|---|---|---|
| passe 1 | 32 | 57 | **56,1 %** |
| passe 2 | 36 | 57 | **63,2 %** |

**Écart 7,0 points** — sous le seuil de 10 déposé. **Les deux passes concordent.**

> ## ➤ NATIF = 59,6 %   ·   n = 114   ·   IC95 [50,6 ; 68,7]

## LES CONDITIONS ÉLIMINATOIRES — TOUTES LEVÉES, POUR LA PREMIÈRE FOIS

| n° | condition | mesure |
|---|---|---|
| 1 | prévol VERT | 114 sur 128 |
| 2 | le natif **BOUGE** | médiane **2,27** et **2,33 m/pas** (seuil 1,0) |
| 3 | le natif **TIRE** | médiane **77** et **72 coups** par épisode (seuil 1) |

**La condition 3 n'avait jamais pu être levée** : `banc_live.py` n'enregistrait aucun coup.
Le compteur a été posé le 20/08 et parle depuis.

**Le monde était propre : ZÉRO erreur de script**, contre **5 306** pour la mesure du 20/08
(214 `_m` + 5 092 `certifier_positions`) — celle qui a été retirée pour cette raison.

**14 épisodes « sans escouade »** sont sortis du compte, **nommés** : l'escouade était tombée
pendant le prévol, l'épisode n'a pas eu lieu. Ils n'étaient comptés nulle part avant le 21/08.

## ⚠️ DEUX FAUSSES LECTURES, ATTRAPÉES AVANT D'ÊTRE CITÉES

**1 · 91,9 %** — mon lecteur calculait le déplacement sur la **dernière** ligne. Depuis que la
sentinelle rend `-1` (« aucun attaquant vivant »), tout épisode où l'escouade meurt avait un
déplacement nul et **sortait par la condition 2**. J'excluais donc les morts, c'est-à-dire
les échecs.

**2 · 87,2 %** — condition 2 appliquée **par épisode**. Mesure décisive :

> **les 36 épisodes qu'elle écarte sont des échecs à 100 % — 0 prise sur 36.**

Un filtre qui ne retire que des échecs n'est pas un filtre. Et la condition 2 est un
**contrôle du MONDE**, pas un tri d'épisodes : elle a été écrite le 15/08 après une IA qui ne
bougeait **pas du tout** (0,07 m/pas sur 18 épisodes). Ici la médiane vaut 2,3 m/pas — le
monde bouge, le contrôle passe, et il n'a pas à trier.

⚠️ **Cliquet : un lecteur qui jette les échecs mesure une réussite qu'il a fabriquée.**
Deux fois en une heure, sur la même mesure, par deux chemins différents.

## CE QUE CE CHIFFRE EST, ET N'EST PAS

C'est **un plancher de MISSION** : natif, 4 contre 4 à 170 m, ce terrain, ce socle.
Il ne dit rien d'un niveau absolu, et **la comparaison à la politique n'est pas encore
permise** — elle le sera quand la politique aura joué sous ce même socle, ce qui est en cours.

⚠️ **Angle mort déclaré** : la mission mord faiblement — 63 % des épisodes sans aucune perte
attaquante (mesuré le 20/08). Un bon attaquant ne peut s'y distinguer que par la prise.
