# Compte rendu de la nuit du 18 au 19/09/2026 - perception de la menace, et campagne P2 a types separes

*Travail autonome de 23 h a 9 h, autorise par Younes ( « points 1 a 4 du plan + P2 ; fais du vrai bon travail » ). Interdits tenus : `bancs/chacal` n a
jamais ete touche, rien n a ete pousse vers GitHub, aucun processus n a ete arrete. Tout a tourne sur deux COPIES du banc : `bancs/chacalvue` ( banc de
perception ) et `bancs/chacalp2` ( mission a deux leviers d observation ), chacune avec sa mission MPMissions et sa config serveur a part.
Chaque campagne a ses criteres commites AVANT ses episodes, et sa fumee. Tout est dans `menace/banc_seuil/`.*

## 0. L essentiel, en sept lignes
1. **Une menace DEBOUT et DESIGNEE est connue en 4-8 s** : de nuit presque toujours jusqu a ~250 m, puis de moins en moins ( mediane entre 300 et 450 m selon la
   lecture, rare au-dela de 450 m ) ; de jour jusqu a ~550 m.
2. **Une menace ACCROUPIE - la posture des vraies menaces - est une loterie des 125 m** : ~90 % sous 125 m, puis un tiers a la moitie des cas de 125 a 450 m.
3. **Ces portees sont un MAJORANT** : le banc designait l unite au moteur ( `doWatch <unite>` ). En regardant seulement sa POSITION, regard pourtant centre, la part
   connue tombe de 93 % a 62 % et le delai double ( 6 s -> 12 s ). Ecart de 31 points : « indecis » a mon seuil ecrit d avance ( 40 ), mais l effet est la.
4. **Le balayage de la fenetre d observation ne connait presque rien** ( 1 cible sur 16 en 90 s, meme dans l axe ) : sous `doWatch` seul le pivot est trop lent
   ( 24 deg en 90 s ), et meme repare ( `setDir` ) il ne tient que 10 s par azimut quand une cible non designee en demande ~12.
5. **La porte de variance s ouvre avec le plus petit changement possible** : observer depuis 260 m comme a l origine, mais avec le balayage REPARE : 47 % de menaces
   percues au choix, variance a l interieur d un monde, 7 % de phases 2 abimees. A l origine exacte : 29 %, porte fermee. Observer de plus pres n apporte rien et abime la phase.
6. **Un defaut de `bancs/chacal` a ete trouve par la fumee de P2** : au niveau 4 ( patrouille seule ), `30_opfor.sqf` ligne 194 ne cree PAS le vehicule ( il ne connait que
   les niveaux 1 et 3 ). Corrige sur la copie ; a corriger dans `bancs/chacal` ( une ligne ).
7. **P2 a types separes est EN VOL au moment de ce commit** ( ~5 h 40 ) : lancee a 3 h 09, ~50 jobs sur 64 faits, 0 refus. AUCUN effet n a ete lu ( regle ecrite : une
   seule lecture, apres la fin ). La commande de lecture est en section 6.

## 1. Correction du compte rendu du 18/09 apres-midi ( commitee a 22 h 53, 16b4262 )
Le « seuil de nuit entre 156 et 173 m », « le seuil depend du lieu » et « le delai explose pres du seuil » etaient des artefacts du banc : sous `doWatch` seul, UN
homme finissait aligne ( `angle_min` = le meilleur des dix ) et le pivot prenait jusqu a 90 s. Regard tourne des la premiere seconde ( `patch_banc_regard.py` ) :
29 cibles connues sur 33 en 3-11 s de 128 a 215 m ; les 4 « jamais » etaient des cibles masquees. Detail : `RESULTATS_SEUIL_PAR_MONDE_18-09.md`.

## 2. PORTEE-REGARD-CENTRE-18-09 ( 80 episodes, 0 erreur SQF ; cible debout, DESIGNEE, regard centre ) - part connue en 90 s
| distance vraie | NUIT, lecture stricte | NUIT, sans la regle « masquee » | JOUR, stricte | JOUR, sans la regle |
|---|---|---|---|---|
| 225-275 m | 5/6 = 83 % | 6/7 = 86 % | 4/4 | 8/8 |
| 275-350 m | 3/5 = 60 % | 3/8 = 38 % | 4/5 | 4/6 |
| 350-450 m | 4/4 = 100 % | 4/7 = 57 % | 6/7 | 7/8 |
| 450-550 m | 1/3 = 33 % | 1/7 = 14 % | 4/6 | 4/6 |
| 550-700 m | 1/7 = 14 % | 1/7 = 14 % | 2/6 ( 4/6 en 600 s, mediane 108 s ) | 2/7 |
Pourquoi deux lectures : ma regle « cible masquee » ( `vis_moy` <= 0,01 ) excluait de nuit 11 episodes dont 10 « jamais » ; je ne peux pas prouver que ce sont des
cibles masquees plutot que de vrais echecs. Predictions : 1 ( >= 80 % a 250 m de nuit ) tenue ; 2 ( la nuit passe sous 50 % avant 650 m ) tenue ; 3 ( le jour fait au
moins aussi bien partout ) fausse dans UNE tranche sur petits nombres ; 4 ( pas d allongement du delai ) tenue sauf de jour a 550-700 m ( mediane 108 s ) : a l extreme
limite, l allongement existe.

## 3. BANC3-19-09 ( 80 episodes, 0 erreur SQF ) - cible ACCROUPIE, et balayage
**A. Accroupie, de nuit, regard centre, designee** - part connue en 90 s :
| distance vraie | lecture stricte | sans la regle « masquee » ( la bonne ici : une cible accroupie a toujours `vis_moy` ~ 0 ) |
|---|---|---|
| 0-125 m | 7/7 | 9/10 = 90 % |
| 125-175 m | 1/2 | 2/6 = 33 % |
| 175-225 m | 2/3 | 4/8 = 50 % |
| 225-275 m | 1/5 | 2/7 = 29 % |
| 275-350 m | 1/3 | 1/6 = 17 % |
| 350-450 m | 2/3 | 2/6 = 33 % |
Quand elle est connue, c est en 4-6 s. Prediction 1 ( sous 50 % avant 300 m ) tenue. Prediction 5 ( moins de 10 % de cibles masquees ) NON EVALUABLE pour une cible accroupie.
**B. Balayage, cible debout a ~200 m, fenetre de 90 s** : balayage de la mission ( mode 7 ) 0/6 ; balayage repare ( mode 8 ) 1/8 ( a 45 deg, en 26 s ) ; 24 refus propres.
Predictions 2 et 3 ( « connue dans la majorite des cas a 0 deg » ) FAUSSES ; prediction 4 ( rien a 90 et 135 deg ) tenue.

## 4. DESIGNATION-19-09 ( 32 episodes, 27 valides ) - le banc mesurait-il une cible designee ?
Mode 5 ( `doWatch <unite>` ) : 13/14 = 93 %, mediane 6-7 s. Mode 9 ( regard tourne vers la cible, `doWatch <position>` ) : 8/13 = 62 %, mediane 10-12 s. Ecart 31 points :
**INDECIS** a la regle ecrite ( etabli a >= 40, nul a < 15 ). Lecture honnete : designer aide ( delai double, part en baisse ), mais ne fait pas tout.
Consequence : les portees des sections 2 et 3 sont un majorant de ce que la fenetre de la mission - qui regarde des positions - peut connaitre.

## 5. La porte de variance ( VARIANCE-OBS-*-19-09, 96 episodes, P2 niveau 5, fenetre 90 s ; portes de `menace/lire_variance.py` INCHANGEES )
| observe depuis | balayage | acceptes | percue > 0 | connue | phase 2 abimee | porte globale | porte intra-monde |
|---|---|---|---|---|---|---|---|
| 260 m ( origine ) | origine | 14 | 29 % | 0 % | 0 % | ECHEC | OK |
| **260 m** | **repare** | 15 | **47 %** | 0 % | 7 % | **OK** | **OK** |
| 180 m | origine | 14 | 29 % | 0 % | 7 % | ECHEC | OK |
| 180 m | repare | 15 | 40 % | 0 % | 20 % | OK | OK |
| 120 m | origine | 15 | 40 % | 0 % | 20 % | OK | OK |
| 120 m | repare | 16 | 44 % | 0 % | 31 % | OK | OK ( ECARTE par le garde-fou de mission, 25 % ) |
Regle ecrite avant : admissible = deux portes + phase abimee <= 25 % ; on retient la part connue la plus proche de 50 %, a egalite le plus proche de l origine.
La part CONNUE vaut 0 % partout : le departage retient **260 m + balayage repare**. Ce que ca dit : la menace n est JAMAIS connue du groupe au moment du choix ; ce qui
varie est le canal geometrique. Le balayage repare fait passer la perception de ~29 % a ~45 % ; observer de plus pres ne l augmente pas et abime la phase ( 0-7 % -> 20-31 % ).
Predictions : a tenue, b tenue pour « connue » mais le balayage repare SUFFIT a ouvrir la porte ( imprevu ), c FAUSSE ( 0 % de connues partout ), d tenue.

## 6. CHOIX-P2-TYPES-19-09 - EN VOL, NON LUE
- Dispositif ( `CRITERES_P2_TYPES_19-09.md`, commite avant, 28a9570 puis 27c879c ) : 2 options ( traverser tout de suite / attendre ) x 2 types de menace poses seuls et pres
  ( niveau 4 PATROUILLE motorisee, niveau 5 POSTE de controle ) x 8 mondes x 4 graines de situation = 128 episodes, banc `chacalp2`, observation depuis 260 m, balayage repare.
- Fumee v1 : le bras PATROUILLE ne posait AUCUNE menace ( defaut de `30_opfor.sqf`, voir 0.6 ). Corrige sur la copie ( 423d3ef ), fumee v2 passee 4/4 : dans le monde 5,
  patrouille + attendre -> vehicule vu, `FENETRE_OBSERVEE`, traversee apres 85 s.
- Etat au commit : lancee a 3 h 09 ; ~50 jobs faits sur 64, ~10 en vol, le reste en file ; 0 refus. Les jobs restants partent seuls ( `HMT_RUN` toutes les 10 min ).
- **LECTURE, UNE SEULE FOIS, QUAND LES 64 JOBS `_P2N_C*` SONT DANS `queue/faits/`** :
  `python3 /mnt/data/hmt/depot/menace/banc_seuil/lire_p2_types.py`
  Le lecteur refuse de lire si une porte de qualite echoue ( Q1 a Q6 ). Amendements du 17/09 repris : remplacement des episodes refuses par l enregistreur, `--sans-monde N`.
- Puissance ecrite d avance : une modulation de moins de ~35 points ne sera pas etablie. Un « indifferent » ne dira que cela.

## 7. BALAYAGE-LENT-19-09 ( 10 s contre 30 s de regard par azimut ) - POSE, SUSPENDU AU COMMIT
Criteres ecrits avant ( `CRITERES_BALAYAGE_LENT_19-09.md` ), levier `CHACAL_CONTROLE_PAS` applique a `chacalvue` ( b9e8ad9 ). 20 jobs courts poses derriere P2 ; 2 ont demarre,
les autres sont ranges dans `queue/suspendus/` au moment ou Younes repasse sur l autre session ( ne pas occuper ses serveurs ). Pour les rejouer :
`python3 menace/banc_seuil/jobs_balayage_lent.py --poser`, puis `python3 menace/banc_seuil/lire_banc_v3.py BALAYAGE-LENT-19-09`.

## 8. Ce que je propose a Younes ( rien n est applique a `bancs/chacal` )
1. **Corriger `bancs/chacal` d une ligne** : `python3 menace/banc_seuil/patch_patrouille_niveau4.py --racine /mnt/data/hmt/depot/bancs/chacal` ( file vide ). Sans cela le
   niveau 4 de la phase 2 ne pose aucune menace, et tout bras « patrouille seule » est un temoin deguise.
2. **Adopter le balayage repare dans la mission** ( levier `CHACAL_BALAYAGE = 1`, `patch_mission_observation.py` + v2 ) : c est le plus petit changement qui ouvre la porte de
   variance, sans rapprocher le point d observation ( qui abime la phase 2 ). A decider par Younes : c est un changement du monde.
3. **Ne pas compter sur « connue » ( niveau 2 ) au moment du choix** : 0 % dans les 96 episodes de la grille. Les menaces sont accroupies a 300-400 m ; la connaissance d une
   cible accroupie n est fiable que sous 125 m. L observable utile pour la regle est le canal geometrique ( `menaces_vues`, `vehicule_vu` ).
4. **Si l on veut une vraie connaissance au choix** : regarder plus longtemps chaque azimut ( test BALAYAGE-LENT a finir ), ou une menace debout, ou de jour - trois leviers
   deja listes au plan v2, a trancher par Younes.
5. **Pour l equation de detection** : les variables qui comptent sont, dans l ordre mesure cette nuit, la POSTURE de la cible, la DESIGNATION ( regarder l unite ou sa position ),
   la duree du regard, la lumiere, puis la distance. La distance seule ne fait presque rien sous 250 m ( debout ) ou 125 m ( accroupie ).
6. **Menage** : `bancs/chacalvue` et `bancs/chacalp2` sont des copies ; les retirer ( et `MPMissions/CHACALVUE.Altis`, `CHACALP2.Altis`, les `server_vue.cfg` / `server_p2.cfg` des
   profils ) une fois les patchs retenus appliques a `bancs/chacal`. 7 jobs TROU + les jobs LENT dorment dans `queue/suspendus/`. Scripts temporaires dans `C:\hmt\tmp\`.

## 9. Fautes et limites de la nuit, dites telles quelles
- J ai annonce a 23 h 29 une portee de nuit « ~450 m » : trop optimiste, corrigee a 1 h 20 ( deux lectures ).
- Mon banc « regard centre » designait la cible au moteur : je ne l ai vu qu a 2 h 45, par l echec du balayage. Tout ce qui a ete mesure avant est un majorant.
- Ma regle « cible masquee » ne vaut rien pour une cible accroupie ; je ne l ai pas changee en cours de campagne, je donne les deux lectures.
- Trois fumees ont echoue sur un point et ont ete corrigees puis rejouees ( regard non centre ; point de pose qui ne suivait pas le levier ; patrouille du niveau 4
  jamais creee ). Deux de mes scripts d attente avaient un defaut ( libelle « echouee » pour « en vol » ; confusion fumee / campagne ) : corriges avant tout effet.
- Un a deux mondes par case presque partout : tout ceci est DESCRIPTIF, sauf P2 qui a son dispositif et sa puissance ecrits.
- Les copies `chacalvue` et `chacalp2` divergent de `bancs/chacal` : la liste des patchs et leur ordre sont dans `menace/banc_seuil/`.
