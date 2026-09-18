# Criteres pre-enregistres - banc de perception, le trou 150-300 m et le jour

*18/09/2026, ecrit AVANT de poser les jobs. Demande de Younes : « lance deux serveurs de verification maintenant ».
Hors depot ( une autre session ecrit dans le depot aujourd hui ) : ce fichier vit dans /mnt/data/hmt/en-attente/.
Aucun code de mission neuf : memes leviers que menace/jobs_banc.py ( b2084ae ), seuls `controle_dist` et `jour` changent.*

## Ce qui est deja etabli ( verdict d666662 )
De nuit, cible debout REGARDEE, ligne de vue libre : connue du groupe en 6 s a 50, 100, 150 m ; jamais a 300 ni 600 m.

## Questions
1. NUIT : ou tombe le seuil entre 150 et 300 m ?
2. JOUR : la portee depasse-t-elle 300 m ? ( jamais mesure sur ce banc )
3. FORME : une MARCHE ( delai ~6 s jusqu au seuil, puis jamais ) ou une ACCUMULATION a la CWR
   ( vis ~ 1/d2 : le delai avant connaissance s allonge a l approche du seuil ) ?

## Jobs - campagne BANC-TROU-18-09, 2 instances, 10 jobs, 20 episodes
- instance 1, NUIT ( jour=0 ) : 225, 200, 250, 175, 275 m ( dans cet ordre : le milieu d abord )
- instance 2, JOUR ( jour=1 ) : 300, 600, 150, 450, 800 m
- chaque job : mondes 4 et 5, 1 repetition, fenetre 300 s, sonde toutes les 5 s, controle_perception=5.

## Lecture ( par episode )
- `connue` = le groupe connait la cible avant la fin de la fenetre ( canal groupe de la ligne de sonde ) ;
- `delai` = premiere ligne de sonde ou elle est connue ( resolution 5 s ) ;
- validite : 0 erreur SQF, ligne de vue verifiee par le banc, angle regard-cible journalise.

## Controles
- POSITIF jour : 150 m de jour doit etre connue ( sinon le bras JOUR est muet et rien ne se lit ).
- Temoin de nuit : 150 m ( 2/2 ) et 300 m ( 0/2 ) viennent du banc du matin ; un point du trou qui contredit
  la monotonie ( connu a 250 mais pas a 200 ) = banc suspect, pas une decouverte.

## Predictions ecrites avant
- MARCHE : tous les delais des episodes connus <= 10 s, quelle que soit la distance.
- ACCUMULATION : au moins un episode connu avec un delai >= 30 s dans les 50 m sous le seuil.
- Jour : seuil attendu au-dela de 300 m ( sinon la lumiere n est pas le levier, et il faut regarder ailleurs ).

## Limites dites d avance
- 2 mondes par distance : DESCRIPTIF, aucun intervalle de confiance, aucun verdict ETABLI a en tirer.
- Charge : lances pendant la campagne PRIX DU TEMPS ( 8 serveurs en vol ) sur decision de Younes ;
  la charge est archivee dans chaque run. La perception est lue en secondes de jeu, mais a verifier.
- Cible debout, regardee, a decouvert : ni l angle, ni la posture, ni le couvert ne sont balayes ici.
