# CRITERES — INSTANCIATION DE L EQUATION 1 (canal de detection CWR)

Ecrits AVANT tout chiffre. Regle 16 (controle positif obligatoire) et
« une mesure doit savoir echouer ».

## CE QU ON INSTANCIE
`engine/Poseidon/World/Detection/Target.cpp` de `BohemiaInteractive/CWR`
(moteur Poseidon = RV1, GPL-3.0-or-later, publie par Bohemia). RV1 n est PAS RV3 :
chaque equation est une HYPOTHESE sur Arma 3, jamais une mesure. Arma 3 reste le
certificateur. Il n existe aucune source d Arma 2.

Trois faits d equation, aucun de constante :
1. le couvert MULTIPLIE la vue — `vis = fog * min(rayon*5000/d2, 40) * Visibility(brain, ai)`
2. l ouie TRAVERSE le couvert a 90 % — `aud *= 1 - (1 - landVis) * 0.90`
3. l ouie SEULE n identifie JAMAIS le camp — `min(audAcc*0.5, 1.4)` contre un seuil a 1.5

## CE QUI CHANGE DANS LE GYMNASE, ET RIEN D AUTRE
La designation de cible passe de `los > 0.5` (interrupteur binaire) a `sideAccuracy >= 1.5`
(canal continu). C est tout. `feu_de_zone`, `feu_sur_connu`, `exposed`, la courbe de
toucher, la suppression, l arc : NON TOUCHES.

ETEINT PAR DEFAUT (`canal_cwr=None`). `MONDE_ARMA` ne bouge pas — la batterie gelee
n est pas touchee par cette livraison.

## CE QU ON N INSTANCIE PAS, ET POURQUOI
- graduation de cone 15/17/45 deg : le gymnase tire son arc AU HASARD par episode
  (`def_rand`, decision mesuree) et a deja sa porte `_dans`. Importer les cosinus de RV1
  par-dessus compterait deux fois le meme effet.
- « position connue avec erreur -> probabilite de toucher » : absent de Target.cpp
  (il est dans le code de tir). On ne l invente pas.
- `TacticalFog8` et `night` : indisponibles -> fog=1, night=0, plein jour. C est le regime
  ou la courbe de toucher a ete mesuree le 26/07. Dit, pas cache.

## QUATRE VALEURS QUI MANQUENT — LE CODE DOIT REFUSER DE TOURNER SANS ELLES
`rayon_m`, `sensibilite`, `sensibilite_oreille`, `audible_cible`. Elles sont par TYPE,
lisibles dans Arma 3 par `configFile` (legal, aucune source requise). Precedent :
`tir_par_pas`. Un parametre invente ne se signale jamais.

## CONTROLE POSITIF — quatre tests, tous sur un cas ou la reponse est connue d avance
- **P1 ACTIVITE.** Le canal doit CHANGER au moins une decision de designation contre
  `los > 0.5`. Falsificateur : 0 desaccord sur 2048 environnements = module INERTE, on
  le retire. *(C est exactement le mode d echec deja rencontre : un premier essai qui
  planchonnait `los` dans les termes de tir est reste parfaitement inerte.)*
- **P2 L INTERRUPTEUR EST LEVE.** Un homme partiellement couvert (0 < efrac < 0.5) doit
  pouvoir etre designe. Falsificateur : aucun homme a efrac < 0.5 jamais designe.
- **P3 L OUIE NE DESIGNE JAMAIS.** Un homme a efrac = 0, meme a 5 m, doit avoir
  `acc_ouie > 0` (il est entendu) et `designe = False`. Falsificateur : une seule
  designation a efrac = 0 -> l implementation est fausse, pas l equation.
- **P4 REFUS.** Construire sans les quatre valeurs de config doit LEVER. Falsificateur :
  ca demarre.

## CE QUI NE SE CONCLUT PAS ICI
Aucun verdict de fidelite. Le contraste vu/pas-vu contre les +75 % d Arma 3, et la paire
tenue a l ecart, sont une NUIT ARMA a part — ils ne sont pas dans cette livraison.
