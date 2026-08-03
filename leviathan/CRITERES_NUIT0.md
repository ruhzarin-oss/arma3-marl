# CRITERES NUIT 0 — ou le succes apparait-il, et dans quel ordre ?

Pre-enregistre AVANT la collecte. Empreinte prise apres ecriture, comparee a la lecture.

## Question

Le plan « modele du monde » suppose qu il existe QUELQUE PART des episodes reussis : la tete de
recompense n apprend rien d un corpus a zero. On ne cherche donc pas a reconfirmer l echec deja
mesure a A=4 (juge : 0 sur 38, Wilson [0 ; 9,2 %]). On cherche le SEUIL ou le succes apparait,
et l ORDRE des manoeuvres a ce seuil.

## Dispositif

- Ferme de 14 instances Altis, geometrie identique au juge (Pyrgos, axe d approche 270).
- Defense constante : D=8, posee par poser_fob.py.
- 4 executeurs Arma : frontal, supfront, envelop, reckless.
- 3 rapports de force : A=4, A=8, A=12.
- n=20 episodes par case, soit 240 episodes.
- Chaque episode enregistre en entier (frames par pas) dans /mnt/data2/lab/replay/nuit0/.

## Ce qui se lit, et RIEN d autre

1. SOURCE DE SUCCES. Il existe au moins une case (mode, A) avec >= 5 succes sur 20.
   - si OUI : cette case est la source de succes du corpus. Le plan continue.
   - si NON sur les 240 episodes : on ne bricole pas. La tache telle que posee est peut-etre
     infaisable a cette geometrie, et c est un arbitrage de cadrage qui remonte au chercheur.

2. ORDRE DES MANOEUVRES. A chaque A, classement des 4 modes par pertes moyennes cote attaquant.
   - lu par mode, PAS en moyenne sur les A : deux rapports de force peuvent bouger en sens
     contraire et s annuler (defaut commis le 29/07 sur l audit d ordre).
   - cet ordre est la CIBLE que le modele du monde devra reproduire (Spearman >= 0,8).

3. VARIANCE. Pour la case la plus fournie en succes : ecart-type des pertes sur 20 repetitions.
   - calibre honnetement la largeur des intervalles de la porte de prediction. Sans ce chiffre,
     un Spearman sur 4 points ne veut rien dire.

## Controles de validite — un resultat qui les rate est nul

- N_ATTENDU : 240 episodes ecrits. Toute case incomplete est declaree, pas comblee.
- ENTITES : chaque episode commence avec exactement 8 defenseurs vivants et A attaquants vivants.
  Un episode qui demarre a 7 defenseurs mesure autre chose : il est REJETE, pas moyenne.
- LONGUEUR : un episode de moins de 3 pas de decision n a pas eu lieu (pont muet, instance
  zombie). REJETE.
- INSTANCE : le debit par instance est journalise. Une instance qui produit deux fois moins que
  la mediane est suspecte et ses episodes sont marques.

## Interdits

- Ne rien retoucher au substitut pendant la collecte.
- Ne pas ajuster un parametre d executeur pour faire apparaitre du succes. On mesure ou il est,
  on ne le fabrique pas.
