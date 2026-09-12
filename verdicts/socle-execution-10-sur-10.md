porte: Le SOCLE seul fait passer l assaut de 1 a 10 reussites sur 10 : la moitie des echecs etaient des pannes d execution, pas de tactique
date: 2026-09-12
graines: 7, 8, cinq repetitions chacune par bras, tous joues la meme nuit sur 7 instances, meme charge
chiffre: socle seul 10/10 a 3 charges sur 3 contre 1/10 pour le script d origine (Fisher unilateral p = 0,0001) ; pertes 1,3 contre 2,5 hommes par episode ; 56 relances du chien de garde ; les tactiques POSEES SUR le socle font moins bien : neutralisation prealable 12/20, base de feu 11/20, infiltration 2/10
verdict: PASSE
depend_de: socle-posable-monde-vide, alize-reflexe-trop-tard, plan-de-positions-sans-plan-de-feu
remplace_par: 
source: runs 2026-09-12_03*_chacal_i1 a i7 ; commit e1807b8 ; document « 8 tactiques de raid » du 11/09

Le socle n est pas une tactique : ce sont quatre reparations d execution, posees sous toutes les tactiques.
  S1 chaque homme de l assaut porte une charge, avec une releve ecrite d avance (DEMO_1, DEMO_2, ADJOINT, CHEF, MEDECIN) ;
  S3 l appui est CLOUE : feu libre, mais PATH et LAMBS coupes, il ne peut plus partir au contact (mesure du 10/09 : 11 a 18 km/h) ;
  S4 les porteurs ne combattent pas : AUTOCOMBAT et LAMBS coupes, ils marchent et posent ;
  S4bis un chien de garde relance l ordre quand l assaut n avance plus de 5 m en 30 s, puis pose un fumigene au deuxieme echec ;
  S5 un defenseur QUI TIRE est revele a l appui - il s est trahi lui-meme, ce n est pas un oracle.
Resultat : 10 episodes sur 10 posent les trois charges, contre 1 sur 10 au script d origine, sur les memes graines et la meme nuit.
Ce que ca etablit : les echecs du palier 4 etaient des PANNES D EXECUTION. Le porteur unique qui meurt, le groupe qui se fige, l appui qui part au contact - pas un defaut de plan.
Ce que ca etablit AUSSI : ajouter une tactique par-dessus le socle a COUTE ici. Attendre la neutralisation (12/20) ou le premier coup de l appui (11/20) fait perdre du temps sous le feu ; l infiltration silencieuse (2/10) est la pire.
Ce que ca N ETABLIT PAS : que la mission complete gagne. C est la mesure suivante, lancee dans la foulee : socle + six phases, de l insertion a l exfiltration.
