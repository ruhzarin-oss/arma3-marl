# Criteres pre-enregistres - BALAYAGE-LENT-19-09 : un regard de 30 s par azimut connait-il ce que 10 s ne connait pas ? ( ecrit AVANT tout episode, 19/09, 3 h 35 )

## D ou vient la question
BANC3 : le balayage ( 10 s par azimut ) ne connait presque rien en 90 s ( 1 sur 16 ), meme dans l axe. DESIGNATION ( lecture provisoire, 18 episodes valides ) :
regard centre sur la POSITION de la cible, elle est connue dans ~60 % des cas avec un delai median de 12-13 s ; designee ( doWatch sur l unite ), 100 % en 6 s.
Si la connaissance d une cible non designee demande ~12 s et plus de regard continu, un balayage qui ne tient que 10 s par azimut repart juste avant.

## Le test ( levier CHACAL_CONTROLE_PAS, `patch_banc_pas.py`, banc chacalvue, nuit, cible debout a 200 m, fenetre de 90 s )
- mode 8 ( balayage repare ), ecarts 0 et 45 deg, pas de 10 s contre pas de 30 s, 4 paires de mondes : 16 jobs ;
- mode 7 ( balayage de la mission, doWatch seul ), ecart 0, pas de 30 s, 4 paires : 4 jobs. Total 20 jobs, 40 episodes ( beaucoup seront refuses :
  la cible doit tomber dans un secteur de +-10 deg ). Validite : comme BANC3.

## Lecture et decision
Part connue en 90 s par ( mode, pas ), ecarts 0 et 45 confondus.
- **LE PAS COMPTE** : mode 8 au pas de 30 s connait au moins 40 points de plus qu au pas de 10 s. Alors la fenetre de la mission gagnerait a regarder chaque azimut
  plus longtemps ( un passage de 3 x 30 s ), et c est une piste a proposer a Younes pour la mission - pas a appliquer seul.
- **LE PAS NE COMPTE PAS** : moins de 15 points d ecart. L echec du balayage vient d ailleurs.
- Entre les deux : indecis.
Prediction : le pas compte ( >= 40 points ). Je rapporte le resultat tel quel.
