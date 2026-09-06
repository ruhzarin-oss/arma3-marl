# CRITERES — LE BRAS A TROIS VOIES SUR ARMA (frontal / suppression / flanc)

Ecrits AVANT tout chiffre. Dispositif reclame par Fable le 23/07, jamais joue.

## POURQUOI MAINTENANT
Le bras du milieu (04/09, GPU) a montre que la courbe remesuree INVERSE l avantage du flanc
dans le gymnase : flanc − frontal passe de **+22,1 pts** (ancienne courbe, qui reproduit le
signe gele +17,3) a **−13,4 pts** (courbe neuve), parce que le frontal passe de 13,9 % a
73,3 %. Les deux reparations de letalite sont pourtant COHERENTES entre elles : l ancienne
probabilite de toucher etait trop HAUTE (compteur qui sur-comptait) et l ancien « 3 impacts
pour tuer » trop BAS (compteur qui sous-comptait) — les deux erreurs gonflaient la letalite.

**Le signe « le flanc paie » a donc ete mesure dans un monde deux fois trop meurtrier.**
Un signe issu d un monde faux n est pas un fait acquis. Seul Arma peut trancher.

## LE DEFAUT QUE CE BANC CORRIGE (Fable, 23/07)
Un A/B a deux bras melange DEUX variables — la suppression et la geometrie de flanc. Il faut
TROIS bras, effectif total EGAL, tout le reste egalise :
- **A** frontal simple : tous assaillent de face.
- **B** fixeurs + assaut FRONTAL : feu-et-mouvement SANS l angle.
- **C** fixeurs + debordement par le FLANC.

Lecture :
- **C > B > A** -> la geometrie paie, le signe gele survit, ma courbe est suspecte.
- **C ≈ B > A** -> c est la SUPPRESSION seule qui paie ; « le flanc » est du folklore, et le
  carnet est a reecrire.
- **A ≈ B ≈ C** -> aucun des trois ne se distingue, le banc ne discrimine pas.

## CE QUI FERAIT ECHOUER LE BANC
- **canari d activation** : les defenseurs DOIVENT ouvrir le feu. Si `Fired` = 0 cote
  defenseur sur un episode, l episode est ECARTE — le monde ne combattait pas.
- **gagnabilite** : si A gagne 0/n ET C gagne 0/n, le banc est dans un regime sature et ne
  discrimine pas ; on ne conclut pas, on change le rapport de force.
- moins de **12 episodes par bras** -> rien n est rendu.
- ecart entre bras dont l IC enjambe zero -> **non concluant**, pas « pas de difference ».

## CONTROLE POSITIF
Le monde combat : sur l ensemble des episodes, au moins la moitie doit compter des morts des
DEUX cotes. Sinon on mesure un stand de tir ⟨piege paye le 28/07⟩.

## MESURE
Prise = un assaillant vivant a moins de 15 m du barycentre defenseur avant la fin.
On releve aussi les pertes de chaque camp, pour que « C gagne » ne cache pas « C perd tout ».

## CE QUI NE SE CONCLUT PAS ICI
Rien sur la courbe elle-meme, rien sur ÉQ. 1. Ce banc tranche UN signe.
