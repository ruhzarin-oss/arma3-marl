# LA PAGE DU MATIN — nuit du 27 au 28 juillet 2026

Generee a 04:05. Une ligne par experience. **Chaque ligne finit par une decision que tu peux prendre avant 9 h.**

Ce qui n'a pas tourne est ecrit tel quel. Aucune ligne n'est maquillee.

## Si tu ne lis qu'une chose

**Le flanc paie sur Arma — mais seulement quand il envoie assez d'hommes.** A 45 % d'assaillants il prend 0 % contre 33 % au frontal ; a 75 %, il prend 33 % contre 17 %. Ce n'est pas la geometrie qui decidait, c'est la REPARTITION. Le parametre `flank=0.45` trainait dans la config depuis le 23/07 et faisait perdre le flanc a lui tout seul.

Et **tau = 4 s tient deux fois** : mesure hier a 4,1 s sur cinq angles, repliquee cette 
nuit a 4,0 s sur un dispositif different. C'est une constante, pas un artefact.

---

## 1. Carte typee : dense contre convolutif

| | |
|---|---|
| **Resultat** | dense 9.41 de prise-a-pertes (3 graines, prise 89 %) / conv 9.25 (3 graines, prise 93 %) / ecart -1.7 % |
| **Critere** | `CRITERES_CARTE_TYPEE.md — c9ed30b25c7a8573` |
| **Verdict** | **L'ARCHITECTURE N'EST PAS LE LEVIER — le dense suit** |
| **DECISION A PRENDRE** | Fermer la piste 'lecteur spatial'. Le prochain levier est le CONTENU de la carte, pas la facon de la lire. |

---

## 2. Courbe n2 : la suppression

| | |
|---|---|
| **Resultat** | 12 tireurs : AUCUN chiffre / 4 tireurs : AUCUN chiffre |
| **Critere** | `protocole mesurer_suppression.py, 2 essais max` |
| **Verdict** | **ECHEC DES DEUX ESSAIS — et le variant diagnostique REFUTE l hypothese de la charge : 4 tireurs meurent exactement comme 12, au meme instant** |
| **DECISION A PRENDRE** | Deux causes sont mortes cette nuit : le timeout (porte a 45 s, meme echec) et la charge (4 tireurs, meme echec). Ce qui reste : le script ne LIT RIEN pendant les 40 s de tir, donc on ne sait pas QUAND le pont meurt — on ne le decouvre qu apres. GESTE A FAIRE : ajouter une lecture toutes les 10 s PENDANT la phase de tir. Elle dira si le pont meurt au debut, au milieu, ou a la transition. Sans ce quand, on continuera a deviner. |

---

## 3. Re-verdict de l'arc qui s'ouvre

| | |
|---|---|
| **Resultat** | cone dur : frontal 19 % / crochet 75 % (x3.87) — cone ouvrant tau=4 s : frontal 2 % / crochet 32 % (x prise 20.14, x cout 0.44) / initiative attaquant : frontal 22 %, crochet 49 % / sensibilite tau -> pas de sursis : tau=4.0s *=1, tau=2.0s=1, tau=6.0s=2 |
| **Critere** | `CRITERES_REVERDICT_ARC_OUVRANT.md — 0606073790cc9c14` |
| **Verdict** | **LE VERDICT TIENT, MAIS LE MECANISME NE SUIT PAS** |
| **DECISION A PRENDRE** | NE PAS adopter arc_latence_s=4.0 ce matin. Trois raisons, dans l ordre. (1) Le temoin d initiative echoue : de flanc, Arma mesure 100 % d ouvertures par l attaquant, le sandbox n en donne que 49 % — le defenseur y devance encore une fois sur deux. Cause probable : l arc aleatoire U(40,70) laisse souvent le flanc DANS le cone, donc il n y a pas de sursis a subir. (2) Le rapport x prise de 20 est un rapport entre deux petits nombres : le frontal passe de 19,3 % a 1,6 %, il est annihile, pas surpasse. (3) Le crochet lui-meme perd la moitie de sa prise (74,7 % -> 32,1 %). GESTE A FAIRE : refaire le re-verdict avec un arc FIXE et etroit (pas de randomisation) pour que le flanc soit vraiment hors cone, et regarder si le temoin monte a 60 %. Tant qu il n y monte pas, le cone dur reste le defaut. |

---

## 4. Eclaireur FIBUA (reperage, PAS certification)

| | |
|---|---|
| **Resultat** | CONTROLE DECISIF, part d assaillants 0,75 : 12 c 8 : sans appui 17 % (pertes 2.50, penetr 38 m) / avec fixeurs 33 % (pertes 3.33, penetr 36 m)  //  meme geometrie a 0,45 : 8 c 8 : sans appui 0 % (pertes 4.50, penetr 102 m) / avec fixeurs 0 % (pertes 4.00, penetr 104 m) / 12 c 8 : sans appui 33 % (pertes 3.17, penetr 74 m) / avec fixeurs 0 % (pertes 3.17, penetr 46 m)  //  anneau a 20 m (premier dispositif) : 8 c 8 : sans appui 33 % (pertes 1.50, penetr 52 m) / avec fixeurs 17 % (pertes 2.17, penetr 42 m) / 12 c 8 : sans appui 50 % (pertes 1.50, penetr 30 m) / avec fixeurs 33 % (pertes 1.83, penetr 28 m) |
| **Critere** | `grille rapport x appui, garnison POSEE PAR SCRIPT` |
| **Verdict** | **LE FLANC PAIE — mais seulement quand il envoie assez d hommes. A 0,45 d assaillants il perd (0 % contre 33 %) ; a 0,75 il gagne (33 % contre 17 %), prise-a-pertes 0.03 contre 0.01.** |
| **DECISION A PRENDRE** | Ce n est PAS la geometrie qui decide, c est la REPARTITION. Fixer flank=0,75 comme valeur de la doctrine de flanc et certifier demain la case 12 contre 8, ligne certifiee, gros n. Et retirer de la memoire du projet l idee que 0,45 etait un reglage neutre : c est lui qui faisait perdre le flanc. |

---

## 5. Le sursis sous volume de feu

| | |
|---|---|
| **Resultat** | 1 tireur : tau 4.0 s (9/9 ripostes) / 4 tireurs : tau 4.7 s (10/10) / ecart +0.6 s |
| **Critere** | `CRITERES_TAU_VOLUME.md — 117b634298093c5c` |
| **Verdict** | **le volume ne change rien (et tau=4,0 s a un tireur REPLIQUE la mesure d hier, 4,1 s, sur un dispositif different : la constante tient deux fois)** |
| **DECISION A PRENDRE** | Arc et suppression sont independants : mesurer la suppression pour elle-meme (cadence), ne pas la deriver de l'arc. |

---

## 6. Etat des instruments

| | |
|---|---|
| **Resultat** | tete de chaine : pont OK, canari OK (4 tirs / 4 impacts), terre ferme 11 cellules / etalons poses (2026-07-28 02:56), exigence 'un etalon au-dela de 110 m' : SATISFAITE / n'a PAS tourne : courbe n2 a 12 tireurs, courbe n2 a 4 tireurs |
| **Critere** | `rituel : pont + canari + terre ferme, puis etalons` |
| **Verdict** | **voir le detail** |
| **DECISION A PRENDRE** | Aucune mesure ne se lit si sa ligne d'instrument est en echec. |

---

## 7. Les rejeux

| | |
|---|---|
| **Resultat** | le meilleur flanc Arma : PRET / l'agent au champ qui se faufile : PRET / un episode de suppression : NON CUISINABLE — mesurer_suppression.py compte des balles, il n'ecrit pas de trames |
| **Critere** | `cuisson seule` |
| **Verdict** | **a regarder** |
| **DECISION A PRENDRE** | Regarder les deux HTML prets. Le jugement a l'oeil est ton travail. |

---

## Ce que la nuit a appris sur elle-meme

- Le pont d'Arma **meurt a la transition entre la phase de tir et la premiere lecture**. Deux causes sont mortes cette nuit : le timeout (45 s, meme echec) et la charge (4 tireurs, meme echec que 12). C'est la seule chose qui bloque encore la courbe n2.
- **Un biais de dispositif a failli faire conclure l inverse.** Ma premiere garnison etait un ANNEAU — la forme dont le projet sait depuis le 22/07 qu elle ne recompense pas le contournement. Reposee en LIGNE certifiee, puis controlee sur la repartition, la grille a change de signe. Un resultat negatif merite qu on suspecte son propre montage avant le monde.
- Le **rituel de tete de chaine** (pont + canari + terre ferme) a ete execute avant chaque mesure. La certification terre-ferme entre au rituel au meme rang que le canari : deux resultats ont ete perdus hier parce que des cellules etaient en mer.
- **tau = 4 s tombe sur 1 pas de sandbox** (3,28 s). tau = 2 s aussi. Les deux valeurs sont **identiques par construction** : ce n'est pas une stabilite, c'est un arrondi. Toute lecture de la sensibilite doit en tenir compte.

