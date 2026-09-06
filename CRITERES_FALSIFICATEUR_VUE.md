# CRITERES — LE FALSIFICATEUR DE LA LOI DE TIR

Ecrits AVANT tout chiffre, comme le depot `DEPOT_EQ2_TIR.md` l annoncait.

## LA REVENDICATION QU ON CHERCHE A TUER
Lue dans CWR et confirmee par la config d Arma 3 (`indirectHitRange` = 0,0) :

> **Il n existe aucun tir VISE sur un homme dont la visibilite courante est inferieure a
> `MinVisibleFire` = 0,63.** Donc le +75 % de mortalite des « vus » ne peut pas venir de
> tirs sur des hommes caches.

## CE QUI LA FALSIFIE, ECRIT D AVANCE
Une part NON NEGLIGEABLE d impacts au FUSIL (munition a `indirectHitRange` = 0) subis par
un homme dont la visibilite depuis son tireur, AU MOMENT DE L IMPACT, est < 0,63.

**Seuil pre-inscrit : > 10 % des impacts directs.** Sous 10 %, on met ca au compte du temps
de vol et des cas limites, et la loi TIENT. Au-dessus, **RV3 a change l equation et la loi
se retire du gymnase** — on ne la regle pas, on l enleve.

## LE CONTROLE POSITIF (regle 16, clause 1) — JOUE AVANT LA MESURE
`checkVisibility` n a jamais ete pose sur un cas connu dans ce projet. Deux temoins, et la
mesure ne demarre que s ils passent tous les deux :
- **temoin +** : deux hommes a 50 m en terrain degage, rien entre eux -> visibilite attendue
  proche de 1 (accepte si >= 0,63, c est-a-dire du bon cote du seuil qu on va utiliser) ;
- **temoin -** : le meme couple avec un mur solide interpose -> visibilite attendue proche
  de 0 (accepte si < 0,63).
Si les deux temoins tombent du MEME cote, la sonde ne discrimine pas et **rien n est lu**.

## CLAUSE 2 — JUGER L ACTE
On ne lit pas un etat (`knowsAbout`, `lineOfSight`). On ecoute l EVENEMENT que le moteur
emet : `HitPart`. Pour chaque impact on releve QUATRE NOMBRES, jamais un champ vide :
distance tireur-victime · visibilite tireur->victime · `indirectHitRange` de la munition ·
`isDirect`. La munition dit si l arme a un rayon d effet : c est elle qui separe « tir vise »
de « feu de zone », et c est le coeur de la question.

## RESERVE PORTEE PAR LA MESURE
La visibilite est relevee A L IMPACT, pas au depart du coup. A 820 m/s le temps de vol vaut
0,06 s a 50 m et 0,24 s a 200 m : negligeable devant un pas de 3,28 s, mais ce n est pas nul.
C est pourquoi le seuil de falsification est a 10 % et non a 0 %.

## CE QUI NE SE CONCLUT PAS ICI
Rien sur la prise, rien sur le transfert, rien sur la paire tenue a l ecart. Ce banc repond
a UNE question : peut-on etre touche au fusil en etant cache ?
