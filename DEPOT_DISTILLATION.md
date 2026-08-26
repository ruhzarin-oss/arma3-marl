# PRÉ-INSCRIPTION — DISTILLATION DU MAÎTRE-GREFFE

**Déposée le 26/08/2026, AVANT le premier pas.** Branche déclenchée par l'échec de la cellule
confirmatoire `PF2` (−8,4 pts contre P, seuil d'échec +3,0), conformément à
`AMENDEMENT_2_RASTER.md` §6 et à la branche déposée d'avance par Fable.

## POURQUOI CETTE VOIE, ET PAS UN QUATRIÈME RÉGLAGE DE RÉCOMPENSE

Le coupable est **l'attribution du crédit** — établi par élimination, chaque suspect exonéré
par mesure : le monde (le prix vaut +20,4 pts en scripté), l'échelle (rapport 0,63),
l'architecture (le prix entre brut en première couche), le juge (38,6 contre 38,9 sur la
même politique).

La distillation **contourne** ce coupable au lieu de le combattre : le professeur donne une
action cible **à chaque pas**, en supervisé. Il n'y a plus rien à créditer.

## LE PROFESSEUR

La **greffe** : politique `A` figée, et parmi ses 3 actions les plus probables, la **moins
chère** au sens du prix `_champ_danger(K=8)` à `move` mètres. Mesurée à **61,6 %** contre
39,3 % pour la même politique lue normalement, 6 graines sur 6 appariées, dont **+15,3 pts
attribuables au prix** (le reste étant le rabattage sur le top-3).

⚠️ **Le professeur est un DÉCODEUR, pas un agent.** Il a besoin du prix à l'exécution. Tout
l'objet de la distillation est de produire un élève qui n'en a plus besoin.

## LES TROIS ÉLÈVES — c'est là qu'est la question

| élève | ce qu'il voit | ce qu'il teste |
|---|---|---|
| **D1** | les **12 nombres seuls** | l'élève peut-il **INTERNALISER** le prix ? |
| **D2** | 12 nombres **+ le prix** | l'élève peut-il au moins **RECOPIER** le professeur ? |
| **D3** | 12 nombres, cible **PERMUTÉE** | **LE CONTRÔLE** |

**D3 est le contrôle sans lequel rien ne vaut** : même professeur, mêmes états, mais l'action
cible est tirée dans le top-3 **au hasard** au lieu d'être la moins chère. Il mesure ce que
rapporte le seul fait d'imiter un rabattage sur le top-3, sans l'information de prix.

## LES PORTES, ÉCRITES AVANT LES DONNÉES

**G1 — LA PORTE.** `D1 − A ≥ +5,0 points` sur `GRAINES_TEST`, deux graines, étendue publiée.
En dessous de +3,0 : échec. Entre les deux : deux graines de plus, aucun verdict.

**G2 — LE CONTRÔLE, SE LIT AVANT G1.** `D1 − D3 ≥ +3,0`. Si D3 vaut D1, l'élève n'a rien
appris du prix — il a appris à imiter un rabattage, ce qui est un fait sur le décodeur et
non sur la perception, et **G1 ne veut rien dire quel que soit son résultat**.

**G3 — L'INTERNALISATION, la vraie question.** Si `D2 > D1` nettement, l'élève ne sait
recopier qu'en gardant le prix sous les yeux : le savoir n'est pas internalisé, et il faudra
porter le prix jusqu'à Arma. Si `D1 ≈ D2`, le prix est **entré dans les poids** — c'est le
résultat fort, celui qui se transporte.

**G4 — PLAFOND ET PLANCHER.** Le professeur est à 61,6 % : un élève au-dessus est suspect et
appelle une vérification, pas une célébration. Un élève sous 49,6 % (la référence) est un
échec quel que soit le reste.

**G5 — LES TÉMOINS DE MÉCANISME**, mêmes que le 2×2 : danger par homme-pas **et** survivants,
en colonnes séparées, jamais en ratio. Un élève qui gagne en rampant et en mourant
(survivants effondrés, comme `PF2` à 0,11) n'est pas un élève qui a appris.

## CE QUE CE BANC NE PROUVERA PAS

Résultat de **GYMNASE**. Il ne dit rien d'Arma tant qu'il n'y est pas certifié. Et l'objection
de fond demeure : deux objets indépendants — la greffe à 61,6 % et E2 à 61,7 % — atterrissent
au même endroit, ce qui suggère un **plafond de ce gymnase vers 61-62 %** sous cette recette.
Un élève qui atteint 61 n'aura peut-être pas appris à voir : il aura atteint le plafond.

---

# AMENDEMENT — DÉPOSÉ LE 26/08 À 11h05, PENDANT LE RUN, AVANT TOUT ÉLÈVE JUGÉ

Vérifiable : zéro ligne `== ELEVE` dans `/mnt/data/dist_*.log` à cette heure.

## A. LE DÉCODEUR DE JUGEMENT EST DÉPOSÉ ⟨Fable⟩

**Échantillonnage, pour tous les élèves**, comme pour tout le dossier. Sans ce dépôt, la
**netteté** apprise par la perte d'entropie croisée deviendrait un degré de liberté au moment
de lire : un élève très net gagne à l'argmax, un élève mou gagne à l'échantillonnage, et on
choisirait le décodeur qui arrange. Il est écrit d'avance et il ne bouge pas.

## B. LE BUDGET SE JUGE SUR LE PLATEAU, PAS SUR LA PARITÉ D'ITÉRATIONS

600 itérations de supervisé contre 1200 de RL n'est pas un handicap : le supervisé reçoit un
signal **par pas** là où le RL reçoit un crédit terminal. **Le critère déposé est la
CONVERGENCE DE LA PERTE** : si elle a plateauté, le budget suffisait. Si elle descend encore
à l'itération 600, le verdict est **suspendu** et le budget est étendu — pas de conclusion
sur une courbe qui bouge encore.

## C. ⭐ LE TRI DE CONTRADICTION — comment distinguer « il a appris à voir » de « il a touché le plafond »

**Le problème.** La greffe fait 61,6 % et E2 fait 61,7 % : deux objets indépendants
atterrissent au même endroit, ce qui suggère un **plafond du gymnase**. Un élève qui atteint
61 % n'aura peut-être rien appris du prix — il aura simplement touché ce plafond. **Le score
seul ne sait pas trier.**

**L'instrument** ⟨Fable⟩. On ne juge plus le score, on juge l'**ACCORD**, et uniquement sur
les états qui séparent :

> les états où **le moins-cher-du-top-3 CONTREDIT l'action la plus probable de A**.

Sur ces états-là, et sur eux seuls, on mesure la part où l'élève choisit l'action du MAÎTRE.
· un élève qui a **touché le plafond** échoue à ce tri — il suit A, pas le prix ;
· un élève qui a **internalisé le prix** le réussit.

**Et il porte son propre contrôle** : si `D3` atterrit lui aussi vers 61 %, la porte G2 tombe
et la question est tranchée d'elle-même, sans le tri.

Fichier : `tri_contradiction.py`. Se joue sur les élèves SAUVEGARDÉS, après coup, sans
réentraînement.

## D. LA PISTE `PF` EST CLASSÉE, PAS POURSUIVIE ⟨Fable⟩

`PF` à 53,3 % (+6,1 sur P) est **une cellule sur huit, une vague, sélectionnée après coup** —
le jardin des sentiers qui bifurquent. L'hypothèse mécanique (la prime à la mort annulait
l'incitation à ramper) est cohérente, mais sa forme propre serait **« Φ gelé + vrai prix de
la mort »**, ce qui est une AUTRE étude. On n'y revient que si la distillation échoue.
