# Historique reconstitué du 8 au 13 septembre 2026

*Écrit le 13/09/2026. Sept lecteurs indépendants ont relu le dépôt, les runs et l'historique git,
chacun sur un domaine, avec consigne de n'affirmer que ce qui s'appuie sur un nombre ou un chemin
de fichier, et de déclarer explicitement ce qu'ils n'ont pas pu établir. L'agent de synthèse a
heurté une limite de session ; la mise en forme est faite à la main, sans rien retirer.*

**Pourquoi ce document.** Trois jours de travail n'avaient laissé de trace ni dans les verdicts
ni dans Plane. Ce qui suit est cette trace, y compris — et surtout — ce qui s'est révélé faux.

**73 entrées** sur 7 domaines : 38 ETABLI, 12 OUVERT, 9 REFUTE, 6 CORRIGE, 5 EN COURS, 3 INVALIDE.

---

## ALIZÉ

### [ETABLI] Le banc ALIZE 1 : ce qu'il enregistre et pourquoi

*2026-09-11*

Le banc alize1 est une copie séparée du banc CHACAL, avec sa propre mission ALIZE1.Altis, pour tourner en parallèle de la campagne sans toucher CHACAL.Altis. Le correctif patch_alize1.py ajoute deux gestionnaires d'événement Arma sur nos hommes seulement (side west) dans 50_capture.sqf. Le gestionnaire Hit écrit une ligne CHACAL|E|coup_recu avec l'instant, le blessé, le tireur, le dégât du coup, le dégât total, la distance et la position du tireur. Le gestionnaire FiredNear écrit une ligne CHACAL|E|frole quand un ennemi tire près d'un homme, avec la distance et la position du tireur ; les tirs amis sont exclus par le script lui-même. Ces deux lignes sont exactement les deux entrées de l'alarme locale de SIROCCO : IMPACT et FROLEMENT. Le banc ne fait donc rien apprendre : il enregistre le signal, et la cascade est rejouée après coup, hors d'Arma.

**Mesures.** 2 gestionnaires ajoutés ; 75 lignes coup_recu et 2 412 lignes frole sur les 20 épisodes (1 017 frole run i6, 1 395 run i7) ; 1 203 lignes tir dont 590 tirées par le camp ennemi.

**Sources.** /mnt/data/hmt/depot/bancs/alize1/ ; /mnt/data/hmt/depot/correctifs/patch_alize1.py ; /mnt/data/hmt/depot/bancs/alize1/mission.Altis/chacal/50_capture.sqf (l. 86-105) ; /mnt/data/hmt/depot/bancs/alize1/lancer.sh ; commit 8d9942a du 2026-09-11

**Reste ouvert.** Le canal BRUIT n'est pas capté dans Arma : FiredNear est un capteur de balle qui passe (~60 m), pas de son. Il a fallu le reconstruire hors d'Arma, donc il n'a jamais été éprouvé en jeu.

### [ETABLI] Vingt vignettes d'assaut, deux graines, une seule journée

*2026-09-11*

Deux runs seulement portent le champ banc = alize1, et il n'en existe aucun autre ni dans runs/ ni dans archive/. Le run i6 joue la graine 7, le run i7 la graine 8, dix répétitions chacun. Les deux ont été lancés le 11/09 à 14h29 et 14h30, et se sont terminés à 16h09 et 16h00, soit 6 002 s et 5 409 s. Les deux FIN.json disent COMPLET, 10 épisodes attendus et 10 lus. Ce sont des vignettes d'assaut (arret 5, palier 4, de nuit, bras PLAN, effectif 10, appui_feu 1, accessible 1), pas des missions complètes. Le total exploitable est donc 20 épisodes et 200 hommes de nos forces spéciales.

**Mesures.** 20 épisodes ; 200 hommes FS (10 par épisode, recomptés à partir des lignes spawn) ; 320 lignes spawn dont 100 ennemis ; 40 charges posées sur 60 ; 20 épisodes sur 20 finissent en ECHEC (14 CHARGES_INCOMPLETES, 6 EXFIL_MANQUEE, cette dernière cause étant attendue puisque la vignette s'arrête en phase 5) ; compromission dans 19 épisodes sur 20.

**Sources.** /mnt/data/hmt/runs/2026-09-11_142934_alize1_i6/ et /mnt/data/hmt/runs/2026-09-11_143019_alize1_i7/ (job.json, FIN.json, g7_r1..r10, g8_r1..r10)

**Reste ouvert.** Deux graines seulement, une seule nuit, un seul palier. Aucun réplica sur un autre monde, un autre palier ou de jour.

### [REFUTE] Le critère était écrit d'avance, et il n'est pas atteint : 63,4 %

*2026-09-11*

Le critère a été inscrit dans le job AVANT le run : le réflexe doit se déclencher chez au moins 90 % des hommes touchés, et sous 50 % le signal n'existe pas dans Arma. La cascade SIROCCO a été rejouée à paramètres fixes sur les journaux, sans rien réapprendre. Le résultat est 26 hommes sur 41, soit 63,4 %. C'est entre les deux bornes : le signal existe mais ne suffit pas. Le verdict écrit est ECHEC. Il est enregistré au registre et repris dans ETAT.md.

**Mesures.** 41 hommes touchés sur 200 ; 27 d'entre eux ont un dégât cumulé supérieur ou égal à 1 dès le premier impact, donc tués sur ce coup ; 26 sur 41 = 63,4 % en réflexe ; critère 90 %, plancher d'échec 50 % ; avance médiane 3,1 s ; résolution de mesure 2 s (le pas d'etat.csv). J'ai recompté indépendamment 20 épisodes, 200 hommes, 41 touchés et 27 tués du premier impact, et je retrouve les mêmes nombres.

**Sources.** /mnt/data/hmt/depot/verdicts/alize-reflexe-trop-tard.md ; /mnt/data/hmt/depot/bancs/alize1/analyse/alize_rejeu.py ; note du job dans /mnt/data/hmt/runs/2026-09-11_142934_alize1_i6/job.json ; commit f049545

**Reste ouvert.** Le seuil s1 a été testé à 0,05 et 0,25 seulement, et les deux donnent 63,4 %. Aucun autre paramètre de la cascade n'a été balayé.

### [CORRIGE] La première mesure était trop généreuse : 75,6 % ramené à 63,4 %

*2026-09-11*

La première version du verdict annonçait 75,6 % (31 sur 41) et un délai de 2,7 s. Une revue de Fable le même jour a trouvé deux fuites dans l'instrument. D'abord, le pas de temps qui coïncide avec le coup contient déjà l'impact : compter ce pas revient à créditer le réflexe d'un signal qui est la blessure elle-même. Ensuite, la balle qui touche produit sa propre ligne tir 0,1 à 0,4 s avant le Hit, et cette ligne était comptée comme un avertissement. Les trois scripts ont été durcis le même jour : on exige désormais le réflexe avant tc moins 1 s, et on exclut le tir du tireur du coup dans cette même fenêtre. Les chiffres tombent de 75,6 % à 63,4 %, et le délai de 2,7 s est remplacé par un constat plus dur. La conclusion, elle, ne change pas.

**Mesures.** 75,6 % (31/41) -> 63,4 % (26/41) ; avance médiane 2,3 s -> 3,1 s ; « 2,7 s après le premier coup de la rafale » -> « la moitié sans aucun avertissement, 3,7 s pour les autres » ; canal bruit 75,6 % / 2,5 s -> 63,4 % / 3,8 s ; 3 fichiers d'analyse modifiés, 90 lignes du JSON de résultat refaites.

**Sources.** commit e933e70 du 2026-09-11 ; diff sur verdicts/alize-reflexe-trop-tard.md, bancs/alize1/analyse/alize_rejeu.py (l. 103), alize_bruit.py (l. 156-157 et 187), delai.py ; version initiale lisible par git show f049545:verdicts/alize-reflexe-trop-tard.md

**Reste ouvert.** Le verdict corrigé porte une note de correction en fin de fichier, mais la fiche mémoire alize-reflexe-trop-tard.md garde encore 75,6 % et 2,7 s dans son champ description.

### [ETABLI] La moitié des hommes touchés n'ont reçu aucun avertissement

*2026-09-11*

C'est le chiffre qui explique tout le reste. Pour 21 des 41 hommes touchés, aucun coup ennemi n'est parti nulle part dans les 10 s qui précèdent, la balle qui touche exclue. Autrement dit, c'est le premier coup de l'engagement qui touche. Le nombre médian de coups ennemis dans les 10 s avant un coup reçu est zéro. En élargissant à 30 s, 17 hommes sur 41 restent sans aucun coup ennemi avant. Aucune oreille, aucun capteur réactif ne peut prévenir un homme d'un coup qui est le premier.

**Mesures.** 21 sur 41 sans aucun coup ennemi dans la fenêtre [tc-10 s, tc-1 s] ; 17 sur 41 sur [tc-30 s, tc-1 s] ; médiane de 0 coup ennemi dans les 10 s avant. Recalculé par moi directement sur les RPT, hors torch : mêmes 21 et 17.

**Sources.** /mnt/data/hmt/depot/bancs/alize1/analyse/alize_bruit.py (bloc DIAGNOSTIC, l. 150-160) ; /mnt/data/hmt/depot/verdicts/alize-reflexe-trop-tard.md

**Reste ouvert.** On ne sait pas si ce 21 sur 41 tient à la vignette d'assaut de nuit au palier 4, ou s'il vaut pour tout engagement dans Arma. Aucune réplication sur un autre dispositif.

### [ETABLI] Pour les 20 autres, la rafale ne donne que 3,7 s

*2026-09-11*

Les 20 hommes touchés qui ont bien eu une rafale ennemie avant eux ne sont pas mieux lotis. Le délai entre le premier coup de la rafale et le coup qui les touche est de 3,7 s en médiane. Un quart d'entre eux ont moins de 2,1 s, un quart plus de 6,4 s. Cinq sur 20 ont moins de 2 s, ce qui est sous la résolution de l'instrument. Douze sur 20 ont moins de 5 s, soit moins que l'avance de 5 s exigée par le critère du canal bruit. La rafale est un avertissement, mais un avertissement trop court.

**Mesures.** n = 20 ; médiane 3,7 s ; quartiles 2,1 et 6,4 s ; moins de 2 s dans 5 cas ; moins de 5 s dans 12 cas. Rafale définie comme une suite de coups ennemis sans trou de plus de 5 s. Recalculé par moi : mêmes valeurs à 0,1 s près.

**Sources.** /mnt/data/hmt/depot/bancs/alize1/analyse/delai.py

**Reste ouvert.** Rien ne dit si un homme averti 6 s à l'avance aurait effectivement survécu : l'avance est mesurée, l'effet de l'avance sur la survie ne l'est pas.

### [REFUTE] Le canal BRUIT ne rachète rien, à aucune portée

*2026-09-11*

Le canal BRUIT n'existe pas dans Arma, il a donc été reconstruit hors du jeu, sans rejouer un seul épisode. Chaque coup ennemi journalisé devient un événement sonore pour chacun de nos hommes, avec le volume de la loi auditive mesurée sur Arma le 03/09. Quinze réglages ont été balayés : portée 0, 100, 200, 300 m et infinie, poids 0,5 et 1, seuil s1 à 0,05 et 0,25. Les quinze rendent exactement 63,4 % de touchés en réflexe, sans une exception. La meilleure avance obtenue est 3,8 s, contre les 5 s exigées. Le témoin haut, portée infinie, mord bien puisqu'il fige les 20 épisodes, mais il ne gagne pas une seconde : il prouve que le levier agit et qu'il n'aide pas.

**Mesures.** 15 lignes de grille, toutes à 63,4 % sur 41 touchés, toutes PASSE = false ; avance médiane 3,1 s au témoin bas et 3,8 s au mieux ; fausses alarmes au témoin bas (portée 0, s1 = 0,05) : 47 hommes jamais touchés mis en réflexe pour 1 027 s au total ; à portée infinie : 159 hommes et 7 792 s, soit 7,6 fois plus, et 20 épisodes sur 20 avec tous les vivants figés ensemble plus de 10 s ; critère complet : 90 % de touchés ET avance médiane supérieure ou égale à 5 s ET fausses alarmes au plus le double du témoin bas ET aucun épisode entièrement figé.

**Sources.** /mnt/data/hmt/depot/bancs/alize1/analyse/alize_bruit.py ; /mnt/data/hmt/depot/bancs/alize1/analyse/alize_bruit_resultat.json ; copie dans /mnt/data/hmt/archive/alize_bruit_resultat.json

**Reste ouvert.** Le canal bruit n'a jamais été joué dans Arma, seulement reconstruit. La loi auditive utilisée est celle du 03/09, jamais contrôlée dans ce dispositif-ci.

### [ETABLI] La jointure du canal bruit a été contrôlée avant d'être lue

*2026-09-11*

Reconstruire un canal hors du jeu suppose de savoir où était le tireur à l'instant du coup. Cette position n'est pas dans la ligne tir : elle est reconstruite par jointure avec etat.csv, échantillonné toutes les 2 s. Le contrôle utilise les 2 412 lignes frole, qui portent, elles, la position exacte du tireur. L'écart médian entre la position reconstruite et la position exacte est de 0,4 m, et 100 % des écarts sont sous 10 m. Les 590 coups ennemis sont joints à 100 %, au-dessus du seuil de 95 % écrit d'avance. L'instrument est donc valide avant toute lecture de résultat.

**Mesures.** 590 coups ennemis, 100,0 % joints (seuil 95 %) ; 2 412 frôlements vérifiés ; 100,0 % d'écarts sous 10 m (seuil 90 %) ; écart médian 0,4 m ; JOINTURE_VALIDE = true.

**Sources.** /mnt/data/hmt/depot/bancs/alize1/analyse/alize_bruit_resultat.json (bloc jointure) ; alize_bruit.py, fonctions position_a et main

**Reste ouvert.** La jointure valide la position du tireur, pas le modèle de propagation du son ni le fait qu'Arma aurait produit ce signal.

### [OUVERT] Un reste de générosité dans le décompte, non signalé par le verdict

*2026-09-11*

Le code compte un homme comme protégé dans deux cas : soit il est déjà en réflexe avant tc moins 1 s, soit il y entre au pas qui suit le coup. Le second cas n'est pas une protection : l'homme est déjà touché. Or le JSON donne, pour le témoin bas, 19 hommes déjà en réflexe alors que le total compté est 26. Sept des 26 ne sont donc en réflexe qu'APRÈS avoir été touchés. Mesuré strictement, la part d'hommes réellement prévenus est 19 sur 41, soit 46,3 %, sous le plancher d'échec de 50 %. Le verdict annonce 63,4 % et reste donc du côté prudent ; le libellé « réflexe AVANT le vol de la balle » ne décrit exactement que 19 des 26 cas.

**Mesures.** 26 comptés = 19 déjà en réflexe + 7 entrés après le coup ; 19/41 = 46,3 % contre 63,4 % annoncé ; le champ deja_en_reflexe vaut 19 ou 20 selon le réglage dans les 15 lignes de grille. Arithmétique déduite du JSON, pas d'une ré-exécution.

**Sources.** /mnt/data/hmt/depot/bancs/alize1/analyse/alize_rejeu.py (l. 106-110) ; alize_bruit.py (l. 187-191) ; champ deja_en_reflexe dans alize_bruit_resultat.json

**Reste ouvert.** Aucun passage du dépôt ne discute ce choix de comptage. À vérifier auprès de Younes si les 7 cas doivent compter ou non ; la conclusion du verdict n'en dépend pas, elle ne ferait que durcir.

### [OUVERT] Ce que le verdict refuse d'établir, et qu'il écrit lui-même

*2026-09-11*

Le verdict ferme la voie du réflexe réactif, et rien d'autre. Il note que l'étage LOCAL de la cascade, celui où le binôme appuie, n'a pas été mesuré. Il note que le recrutement n'a pas été mesuré non plus. Il note que 14 hommes touchés sur 41 ont survécu au premier impact, et que le réflexe pourrait encore servir à ces 14-là. Il conclut que le gain doit venir AVANT le premier coup, donc de l'observation et de l'anticipation de l'intention ennemie. Il précise que l'anticipation est une brique recommandée par Fable et jamais mesurée.

**Mesures.** 14 touchés sur 41 ont survécu au premier impact ; 0 mesure de l'étage LOCAL ; 0 mesure du recrutement ; 0 mesure de l'anticipation d'intention.

**Sources.** /mnt/data/hmt/depot/verdicts/alize-reflexe-trop-tard.md, lignes « Ce que ca N ETABLIT PAS » et « Consequence pour ALIZE »

**Reste ouvert.** Trois mesures nommées et aucune faite : étage LOCAL, recrutement, survie après le premier impact. L'affirmation que l'observation « ne repère presque rien aujourd'hui » n'est appuyée par aucun chiffre que j'aie trouvé dans le dépôt.

### [REFUTE] La suite immédiate : donner l'information ne fait pas gagner non plus

*2026-09-11*

Fable a posé la question suivante le jour même : si le gain doit venir d'avant le premier coup, alors savoir où sont les défenseurs devrait suffire. Un oracle a été posé, les défenseurs révélés à tous nos hommes par reveal, instrument déjà certifié 20/20. Le résultat est 8 poses complètes sur 18 avec l'oracle contre 4 sur 12 sans, mêmes graines et même heure. Le critère écrit d'avance demandait 15 sur 18 : c'est un ECHEC, et l'écart n'est pas significatif. Une réserve majeure est inscrite au verdict : l'oracle est posé APRÈS le choix de la porte d'entrée, donc l'ouverture est encore choisie à l'aveugle. La piste « savoir avant » n'est donc pas fermée, elle est mal testée.

**Mesures.** oracle 8/18 soit 44 % contre référence 4/12 soit 33 % ; critère réussite au moins 15/18, échec au plus 9/18 ; Fisher unilatéral environ 0,4 ; oracle posé ligne 947 de 60_phases.sqf, choix de l'ouverture lignes 884-898.

**Sources.** /mnt/data/hmt/depot/verdicts/oracle-savoir-a-l-assaut.md ; runs 2026-09-11_164849_chacal_i1 à _165119_i5 ; commit c93fc26

**Reste ouvert.** L'oracle complet, posé AVANT le choix de la porte, reste à mesurer. Fable propose aussi oracle plus feu d'appui dirigé depuis une position tenue.

### [OUVERT] ALIZE l'algorithme n'a toujours pas été branché

*2026-07-27 au 2026-09-12*

Il faut distinguer deux choses qui portent le même nom. ALIZE est d'abord un programme d'algorithme, décidé le 27/07 : le réseau n'émet pas d'actions mais les seuils d'une cascade écrite à la main. Son noyau, l'encodeur polaire à convolution circulaire, existe dans le dépôt et son en-tête dit lui-même « brique ISOLEE, rien n'est branche ». J'ai vérifié : aucun fichier du dépôt n'importe alize_encodeur.py. Le banc alize1 de septembre ne teste pas cet algorithme, il teste le signal d'entrée de la cascade que l'algorithme devait piloter. Le protocole à quatre bras d'ALIZE (T0 cascade fixe, T1 MAPPO, A, A moins) n'a jamais été joué.

**Mesures.** 0 import de alize_encodeur.py dans tout le dépôt ; dernier commit touchant ce fichier le 2026-08-04 (a405a3a) ; 3 commits seulement concernent ALIZE en septembre : 8d9942a, f049545, e933e70 ; 0 run des 4 bras du protocole.

**Sources.** /mnt/data/hmt/depot/ALIZE.md ; /mnt/data/hmt/depot/alize_encodeur.py ; /mnt/data/hmt/depot/SIROCCO.md et sirocco_cascade.py

**Reste ouvert.** Le protocole à 4 bras n'est pas lancé. La revue de littérature sur les 4 familles voisines, jugée nécessaire avant d'investir des mois, n'a laissé aucune trace dans le dépôt.

### [ETABLI] Ce qu'ALIZE a débloqué ailleurs : le socle d'exécution

*2026-09-12*

Le verdict du 12/09 sur le socle d'exécution cite alize-reflexe-trop-tard parmi ses dépendances. Il part du même constat : ce n'était pas un problème de plan ni de réaction. Quatre réparations d'exécution posées sous toutes les tactiques font passer l'assaut de 1 réussite sur 10 à 10 sur 10. Ces réparations touchent le porteur unique, l'appui qui part au contact, et le groupe qui se fige. Ajouter une tactique par-dessus le socle coûte : neutralisation préalable 12/20, base de feu 11/20, infiltration 2/10. C'est le mouvement inverse du réflexe : réparer l'exécution plutôt que percevoir le danger.

**Mesures.** socle seul 10/10 à 3 charges sur 3 contre 1/10 pour le script d'origine, Fisher unilatéral p = 0,0001 ; pertes 1,3 contre 2,5 hommes par épisode ; 56 relances du chien de garde.

**Sources.** /mnt/data/hmt/depot/verdicts/socle-execution-10-sur-10.md ; runs 2026-09-12_03*_chacal_i1 à i7 ; commit e1807b8

**Reste ouvert.** Ce verdict n'établit pas que la mission complète gagne. Il ne dit rien non plus sur ALIZE : il déplace simplement la cause des échecs, il ne réhabilite ni ne condamne davantage le réflexe.

### Ce que ce lecteur n'a PAS pu établir

Ce que je n'ai PAS pu établir, explicitement.

1. Je n'ai pas ré-exécuté alize_rejeu.py ni alize_bruit.py. Ces scripts chargent torch et la cascade SIROCCO, et l'ordre était de ne rien lancer. Les chiffres de réflexe proprement dits (26 sur 41, avances de 3,1 et 3,8 s, 47 et 159 fausses alarmes, 1 027 et 7 792 s figés) viennent donc du JSON archivé et du verdict, pas d'un calcul refait par moi.

2. En revanche j'ai recalculé indépendamment, à partir des RPT bruts et sans torch : 20 épisodes exploitables, 200 hommes FS, 41 touchés, 27 tués du premier impact, 590 coups ennemis, 2 412 frôlements, 21 touchés sans aucun coup ennemi dans les 10 s avant, 17 sans coup dans les 30 s avant, et pour les 20 autres un délai médian de 3,7 s avec quartiles 2,1 et 6,4. Tous ces nombres coïncident avec le verdict. Le script de vérification est /private/tmp/claude-503/-Users-ybouhassoun-Documents/94c4761c-abe2-4821-a29a-25b9aa27aab6/scratchpad/alize_verif2.sh.

3. Je n'ai trouvé aucun chiffre dans le dépôt qui appuie la phrase du verdict selon laquelle l'observation « ne repère presque rien aujourd'hui ». C'est une affirmation non mesurée dans ce dossier.

4. L'étage LOCAL de la cascade, le recrutement, et la survie après le premier impact (les 14 sur 41) ne sont mesurés nulle part. Le verdict le dit lui-même ; je confirme n'avoir trouvé aucun run ni script qui s'en approche.

5. Je n'ai trouvé aucune trace d'un run ALIZE avant ou après le 11/09 : deux runs seulement portent banc = alize1, rien dans archive/, et seulement trois commits ALIZE dans tout l'historique du dépôt.

6. Incohérence résiduelle non corrigée que je signale sans pouvoir la trancher : le docstring d'alize_bruit.py annonce un témoin bas à « 73 %, 1,4 s sur 16 episodes », valeurs qui ne correspondent ni à la mesure initiale (75,6 % sur 20 épisodes) ni à la mesure corrigée (63,4 %). C'est une référence périmée laissée dans le commentaire ; le résultat final du fichier, lui, est cohérent.

7. La fiche mémoire /Users/ybouhassoun/.claude/projects/-Users-ybouhassoun-Documents/memory/alize-reflexe-trop-tard.md porte encore 75,6 % et 2,7 s dans son champ description, alors que son corps de texte contient bien la correction à 63,4 %. Le champ de description n'a pas été repris.

8. Les 7 hommes sur 26 qui entrent en réflexe APRÈS le coup sont déduits par arithmétique (26 comptés moins 19 « deja_en_reflexe » au témoin bas), pas lus directement dans une sortie. Une ré-exécution d'alize_rejeu.py trancherait, je ne l'ai pas faite.

9. Je n'ai pas ouvert le wiki Plane, qui est décrit dans ETAT.md comme le journal détaillé. Des éléments d'histoire d'ALIZE peuvent s'y trouver et m'échapper.

10. Rien n'a été modifié, aucun run lancé, aucun processus tué. Les sept serveurs Arma n'ont pas été touchés ; ETAT.md du 12/09 à 20h41 indiquait d'ailleurs 0 serveur, donc la campagne citée a démarré après cet instantané.

---

## Infrastructure et incidents

### [CORRIGE] Collision de dossiers de run nommes a la minute

*2026-09-11*

Le nom du dossier de run etait a la minute pres et ne portait pas l instance : R=$H/runs/$(date +%Y-%m-%d_%H%M)_$B. Tant que la file etait serielle, deux runs du meme banc ne pouvaient pas partir dans la meme minute ; la file par instance du 08/09 l a rendu possible. Le 11/09, deux paires de jobs ont partage leur dossier, et le second a ecrase le job.json du premier. Comme chaque repetition relit $R/job.json, V7 a joue les parametres de V8 et V9 ceux de V5 des la deuxieme repetition. Il n y a eu aucune erreur et aucun signal : mkdir -p accepte silencieusement un dossier deja present. Le correctif met seconde et instance dans le nom et remplace mkdir -p par mkdir, de sorte qu un dossier existant devient un REFUS.

**Mesures.** 2 dossiers partages par 4 jobs : 2026-09-11_0919_chacal (V7+V8) et 2026-09-11_0920_chacal (V9+V5). 4 jobs refuses avec la raison CONTAMINE (V5, V7, V8, V9). Bilan du sauvetage au 11/09 09:59 : V5 = 4 episodes valables, V7 = 1, V9 = 1, V8 = 0, soit 6 valables sur les 7 sous-dossiers restes. Dans le catalogue : 6 episodes portent contamine=1 et coherent=0 sur 513, et 7 episodes du 11/09 n ont pas de porte_lecture. Aucun fichier efface. Les quatre versions ont ete rejouees : V7 = 7 episodes, V8 = 6, V9 = 7, V5 = 10 au catalogue.

**Sources.** commit 68bb218 du 2026-09-11 09:43 (outils/run.sh, 12 ajouts 2 retraits) ; /mnt/data/hmt/depot/outils/run.sh ; /mnt/data/hmt/runs/2026-09-11_0919_chacal/CONTAMINE.txt ; /mnt/data/hmt/runs/2026-09-11_0920_chacal/CONTAMINE.txt ; /mnt/data/hmt/archive/sauvetage_g8/LISEZMOI.txt ; /mnt/data/hmt/queue/refuses/2026-09-11_G8_V5.json.raison ; cause amont : commits 3fd69ec et ca827b4 du 2026-09-08 (file par instance)

**Reste ouvert.** Je n ai pas verifie que les six episodes contamines ont ete retires des lectures de verdict ; ils restent presents dans episodes.csv avec contamine=1.

### [CORRIGE] Fuite de la variable HMT_FIGE entre file3.sh et run.sh

*2026-09-11*

file3.sh se gele en se recopiant dans /tmp puis en se relancant avec HMT_FIGE=1. Cette variable etait exportee dans l environnement et heritee par run.sh. run.sh teste la meme variable pour decider s il doit se geler : il se croyait donc deja gele et lisait le fichier du depot en direct. run.sh a ete edite a 09:43 pendant que la version V1 tournait. A 14:52, apres ses cinq repetitions, run.sh a relu le fichier decale, a produit line 39: RUN: command not found, et a rejoue ses repetitions dans le meme dossier. Le correctif retire la variable au passage de relais : env -u HMT_FIGE bash run.sh. Chaque script se gele desormais lui-meme.

**Mesures.** 1 run touche : 2026-09-11_0918_chacal, version V1, job a 5 repetitions. g8_r1 ecrase par un 6e episode juge valable (memes leviers) ; g8_r2 non ecrase ; le 7e episode interrompu a la main vers 16:45 et son RPT efface a 16:48 par le lanceur de l instance O1, donc 1 episode perdu. V1 = 6 episodes valables au catalogue, dont 1 avec les trois charges. Aucun FIN.json : le run a ete arrete a la main. 6 journaux sauves dans l archive de sauvetage.

**Sources.** commit feb13cb du 2026-09-11 16:45 (outils/file3.sh, 5 ajouts 1 retrait, ligne 135) ; /mnt/data/hmt/depot/outils/file3.sh lignes 25-27 et 131-135 ; /mnt/data/hmt/depot/outils/run.sh lignes 6-8 ; /mnt/data/hmt/runs/2026-09-11_0918_chacal/DOUBLE_BOUCLE.txt ; /mnt/data/hmt/archive/sauvetage_g8/runs/2026-09-11_0918_chacal/ (6 fichiers .rpt) ; /mnt/data/hmt/queue/refuses/2026-09-11_G8_V1.json.raison

**Reste ouvert.** Le mecanisme amont qui a efface le RPT du 7e episode, c est-a-dire le lanceur qui supprime les *.rpt du profil hmtech1 a son demarrage, n est corrige par aucun commit que j aie trouve.

### [CORRIGE] Ecriture de lignes apres la ligne FINI : des episodes censures

*2026-09-12*

Le lecteur ne retient que les lignes CHACAL jusqu a la premiere FINI incluse. Une porte de lecture, rien_apres_fini, refuse tout episode qui a ecrit apres cette ligne. Or trois boucles du socle, la tactique, le chien de garde et la relance, dorment 5 a 10 secondes ; quand l episode se ferme pendant leur sommeil, elles se reveillent et ecrivent apres FINI. La censure allait dans un seul sens : elle frappait preferentiellement les episodes qui durent, donc ceux qui ont eu le temps de poser leurs charges. Le correctif re-teste CHACAL_FIN apres chaque sommeil, avant d ecrire quoi que ce soit, et ferme l episode par un exitWith en tete de phase 5.

**Mesures.** Constat au moment du correctif : 17 episodes refuses sur 96 dans l ablation, dont 10 avaient pose leurs trois charges. Comptage sur disque aujourd hui : 584 fichiers resultat.json portent la porte, 30 la rendent fausse, dont 20 avec charges completes. C est de loin la premiere cause de refus : 30 occurrences contre 7 pour episode_termine, 7 pour echelle_pleine et 7 pour graine_conforme. Au catalogue : 31 REFUSE sur 513 episodes, dont 15 sur 91 pour la campagne ABLATION-12-09, 6 pour SOCLE-CONFIRMATION-12-09 et 5 pour TOURNOI-TACTIQUES-12-09. Apres le correctif : sur 89 episodes lances apres le 12/09 14:37, 0 echec de cette porte (85 ACCEPTE, 4 REFUSE pour d autres portes).

**Sources.** commit bdc52a4 du 2026-09-12 14:37 ; /mnt/data/hmt/depot/correctifs/patch_banc_appui.py lignes 3-7 et 44-69 ; /mnt/data/hmt/depot/bancs/chacal/lire.py ligne 134 (portes[rien_apres_fini]) ; /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/00_socle.sqf ; .../60_phases.sqf ; exemple mesure : /mnt/data/hmt/runs/2026-09-12_131559_chacal_i3/g7_r3/resultat.json (lignes_apres_fini = 1, charges 3 sur 3, issue ECHEC)

**Reste ouvert.** Je n ai pas retrouve le decompte de 96 episodes d ablation cite par le correctif : le catalogue regenere a 18:35 en compte 91 avec 15 refus, et les dossiers d ablation sur disque portent 100 sous-dossiers d episode. L ecart entre 17 sur 96 et 15 sur 91 n est explique nulle part. Les 30 episodes refuses n ont pas ete rejoues.

### [ETABLI] Le plafond de jobs en vol : de MAX=3 a MAX=7 dans file3.sh

*2026-09-08 au 2026-09-11*

Le plafond n est pas passe de 3 a 7 d un coup, mais en quatre pas, tous inscrits en commentaire dans le code. file2.sh nait avec MAX=2 le 08/09, puis passe a 3 le meme jour. file3.sh, cree le 09/09, recopie MAX=3. Le 11/09, la campagne graine 8 le porte a 5, puis le banc ALIZE 1 le porte a 7 quelques heures plus tard. Chaque palier porte sa justification : 3 pour le gymnase plus les deux bancs CHACAL, 5 pour les cinq instances de la campagne, 7 pour ajouter le banc ALIZE 1 alors que le processeur etait a 9 pourcent. Le verdict du 08/09 avait pourtant fixe MAX=2 sur une mesure de debit, avec la regle on ne depasse pas ce qui a ete mesure.

**Mesures.** MAX=2 pose par ca827b4 (08/09). MAX=3 par f33b0b0 (08/09, file2.sh) : gymnase i0 plus bancs CHACAL i1 et i3. MAX=3 recopie dans file3.sh par 74931ba (09/09). MAX=3 vers 5 par c7e9fcd (11/09) : Xeon 12 coeurs, 64 Go. MAX=5 vers 7 par 8d9942a (11/09) : processeur a 9 pourcent. Valeur actuelle : file3.sh ligne 87, MAX=7 ; file2.sh reste a MAX=3 ligne 59. La seule mesure de parallelisation au depot est du 08/09 : facteur 1,86 a deux instances, et rien au-dessus de 13 pourcent ensuite.

**Sources.** /mnt/data/hmt/depot/outils/file3.sh lignes 87 et 93-94 ; /mnt/data/hmt/depot/outils/file2.sh lignes 59 et 63-64 ; commits ca827b4, f33b0b0, 74931ba, c7e9fcd, 8d9942a ; /mnt/data/hmt/depot/verdicts/file-par-instance-08-09.md (section Ce qu il a fallu ajouter)

**Reste ouvert.** Aucune mesure de debit n a ete refaite a 5 ni a 7 instances. Les deux augmentations du 11/09 s appuient sur une charge processeur observee, pas sur un facteur d acceleration mesure, alors que le verdict du 08/09 avait pose la regle inverse. Aucun episode perdu ou refuse n est attribue a ce changement dans le depot : je n ai trouve aucun chiffre reliant MAX=7 a une degradation.

### [ETABLI] Les portes de controle_avant_run.sh

*2026-09-07 au 2026-09-11*

Le controle d avant-run refuse de lancer un job si un piege connu est present. Il porte aujourd hui neuf portes. Trois verifient le contexte : un temoin present sur le disque, le fichier de job lisible, et au moins 50 Go libres. Deux verifient le job : les champs banc, graines, instance et plafond_s sont presents, et la regle de non-singularite est respectee. Deux verifient le depot : le banc a un lancer.sh executable, et ni bancs ni outils ne sont modifies sans commit. Deux verifient la machine : le serveur du labo MCP ne tourne pas si le job ne tolere pas labo, et aucun residu non tolere n est en memoire. Le point de methode important est que les residus sont declares par le job dans un champ tolere, et non interdits dans l absolu, parce que l editeur Unreal du projet Drone est un outil de travail et non un residu.

**Mesures.** Fichier de 61 lignes, 3584 octets. 9 portes. La regle de non-singularite a deux formes : au moins 2 graines distinctes, OU au moins 5 repetitions ; un seul episode reste interdit dans les deux cas. Quatre commits : 6d8973c (07/09, creation), 9cf5b08 (08/09, tolere), 59015e6 (08/09, non-singularite a deux formes), 690cbe1 (11/09, garde du labo, 9 lignes ajoutees). File des refus : 22 fichiers .json, 14 avec une raison ecrite. Refus documentes par une porte : 2026-09-12_SONDE_i2 pour episode singulier (1 graine, 2 repetitions) ; GYM-13 le 08/09 a 17:30 pour outils non commites ; HMT-25 le 08/09 a 12:46 pour UnrealEditor en charge. Les 8 autres raisons sont des arrets a la main, pas des refus de porte.

**Sources.** /mnt/data/hmt/depot/outils/controle_avant_run.sh (lignes 13, 14, 18-19, 27-33, 36, 37, 44-49, 51-55, 59) ; appele par /mnt/data/hmt/depot/outils/run.sh ligne 13 ; /mnt/data/hmt/queue/refuses/2026-09-12_SONDE_i2.json.raison ; /mnt/data/hmt/depot/verdicts/file-par-instance-08-09.md (section LE TROU QUI RENDAIT LE PONT MENTEUR)

**Reste ouvert.** Je ne peux pas dire combien de jobs le controle a refuse au total depuis le 07/09 : seuls 14 fichiers .raison existent et la majorite documente des arrets a la main. Aucune porte ne verifie la collision de dossier ni la fuite de HMT_FIGE : ces deux correctifs vivent dans run.sh et file3.sh, pas dans le controle.

### [ETABLI] Le catalogue : l incident du 11/09 a fabrique la base de connaissance

*2026-09-11*

Le catalogue est ne directement de la collision de dossiers. Sa regle fondatrice est qu un episode se lit depuis sa ligne CHACAL|FINI, jamais depuis le nom de son dossier, parce que le nom du dossier avait menti le 11/09. La ligne FINI porte les leviers reellement joues, donc le champ version_jouee en est deduit et peut differer de la version annoncee par le job. Un second constat a ete fait au passage : les episodes n existaient qu en un exemplaire, seul le code etait sauvegarde. Le meme commit ajoute donc a sauver.sh un miroir de runs, archive et queue sur un disque externe, sans effacement. Une revue du meme jour a durci le champ coherent, qui declarait au lieu de mesurer : il compare maintenant les leviers de la ligne FINI a ceux du job.

**Mesures.** 513 episodes catalogues, lus depuis 754 journaux, 21 journaux sans ligne FINI ignores. 507 episodes coherent=1 et 6 coherent=0, ces 6 etant exactement les contamines du 11/09. 475 ACCEPTE, 31 REFUSE, 7 sans porte de lecture. 180 episodes ont plus d un exemplaire retrouve. 20 leviers suivis, 59 colonnes dans episodes.csv. catalogue.py fait 13179 octets. Regeneration apres chaque run par file3.sh ligne 150, avec un timeout de 600 s et jamais bloquante, et chaque nuit par sauver.sh avant le commit.

**Sources.** commits 61fbdf2 (11/09, creation : catalogue.py 268 lignes, episodes.csv 144 lignes, sauver.sh 13 lignes) et e933e70 (11/09, coherent mesure, 15 lignes dans catalogue.py) ; /mnt/data/hmt/depot/outils/catalogue.py lignes 8, 40, 49, 194-205, 254 ; /mnt/data/hmt/depot/catalogue/episodes.csv ; /mnt/data/hmt/depot/catalogue/LISEZMOI.md ; /mnt/data/hmt/depot/outils/sauver.sh ; /mnt/data/hmt/etat/catalogue.log

**Reste ouvert.** Le miroir sur E: n est verifie par aucune porte : rien ne dit qu il est a jour ni complet. Les 21 journaux sans ligne FINI sont ignores en silence, sans que leur cause soit nommee episode par episode.

### Ce que ce lecteur n'a PAS pu établir

Ce que je n ai PAS pu etablir. 1) L ecart entre le chiffre du correctif de la fuite de journal, 17 episodes refuses sur 96 dans l ablation, et ce que rend le catalogue regenere le 12/09 a 18:35, 15 refuses sur 91 pour la meme campagne : je n ai retrouve nulle part une ablation de 96 episodes, et les dossiers d ablation sur disque portent 100 sous-dossiers. Je donne les deux chiffres avec leur source plutot que d en choisir un. 2) Le nombre total d episodes perdus par la collision de dossiers : les fichiers disent qu aucun fichier n a ete efface et que 6 episodes sur 7 ont ete recuperes, mais personne n a ecrit combien d episodes auraient existe si la collision n avait pas eu lieu ; les jobs demandaient 6 et 10 repetitions, ce qui laisse supposer une dizaine d episodes non joues, mais c est une deduction et je ne la revendique pas. 3) Aucun chiffre ne relie le passage de MAX a 5 puis a 7 a une perte ou a un refus d episode ; le debit reel a 5 et 7 instances n a jamais ete mesure, la seule mesure de parallelisation au depot est un facteur 1,86 a deux instances, du 08/09. 4) Le nombre total de jobs refuses par controle_avant_run.sh depuis sa creation : la file ne garde que 22 jobs refuses et 14 raisons ecrites, dont 8 sont des arrets a la main et non des refus de porte. 5) Je n ai pas verifie si les 30 episodes refuses pour ecriture apres FINI, ni les 6 episodes contamines, ont ete rejoues ou simplement laisses de cote. 6) Le mecanisme qui a efface le RPT du 7e episode de V1, un lanceur qui supprime les journaux du profil hmtech1 a son demarrage, n est corrige par aucun commit que j aie trouve ; il reste un piege actif. 7) Je n ai touche a rien sur la workstation : lecture seule, aucun run lance, aucun processus tue.

---

## Labo MCP Arma

### [ETABLI] Le labo MCP Arma : construit et versé au dépôt le 11/09, en un seul commit

*2026-09-11*

Le labo a d'abord été écrit hors dépôt, dans /mnt/data/hmt/mcp-arma, puis copié dans depot/labo par le commit 690cbe1 du 11/09. C'est le seul commit qui touche labo/ : le code n'a pas bougé depuis. La chaîne est : Claude → mcp_arma.py (transport) → arma_labo.py (module) → pont fichier C:\hmt_bridge\i9 → serveur Arma de l'instance 9, mission Labo.Altis. Le travail est dans le module, pas dans le MCP : 656 lignes contre 232. Le message de commit dit pourquoi il n'y a pas de branche dédiée : les scripts du labo attendent depot/labo, et changer de branche changerait les fichiers sous la file. Le verdict de Fable du 11/09 est GO SOUS CONDITION.

**Mesures.** 1 commit, 17 fichiers, 2240 lignes ajoutées. arma_labo.py 656 lignes ; mcp_arma.py 232 ; test_labo.py 447 (33 fonctions de test) ; faux_arma.py 242 ; banc_pontmcp.py 141 ; lancer_labo.sh 86 ; fonctions.sqf 158 ; initServer.sqf 41 ; mission.sqm 45. Latence de référence inscrite dans le module : 0,516 s médiane et 0,566 s p99, mesurées le 30/08. Plafond SQF 9000 octets, la DLL rendant au plus ~10 239 octets. Battement de la mission toutes les 2 s, BATTEMENT_MAX 6,0 s, PATIENCE 6,0 s.

**Sources.** /mnt/data/hmt/depot/labo/ (arma_labo.py, mcp_arma.py, mcp_arma.sh, lancer_labo.sh, lancer_labo.ps1, arreter_labo.sh, LISEZMOI.md, server.cfg.modele, mission.Altis/) ; commit 690cbe1 « MCP Arma, etapes 0 et 1 » ; lieu de construction d'origine /mnt/data/hmt/mcp-arma/

**Reste ouvert.** Le dossier d'origine /mnt/data/hmt/mcp-arma/ existe toujours en double du dépôt (LISEZMOI.md du 11/09 16:05). Rien ne dit lequel fait foi si quelqu'un l'édite.

### [ETABLI] Les sept outils exposés, et leurs bornes

*2026-09-11*

Le serveur MCP expose exactement sept outils, tous typés par un schéma JSON qui refuse les propriétés inconnues. canari fait un aller-retour à vide et dit si le pont répond, en combien de ms, et si les fonctions sont chargées. etat compte le monde relu dans Arma, et peut détailler jusqu'à 200 hommes. poser_groupe pose des hommes sans ordre et rend le nombre RÉELLEMENT posé, pas le nombre demandé. poser_scene monte des bleus contre des rouges face à face autour d'un point. ordonner donne un ordre à un groupe désigné par son indice. nettoyer fait table rase et échoue si un seul homme reste. sqf passe une ligne de SQF brut, et n'est là que sur demande explicite de Younes.

**Mesures.** 7 outils. poser_groupe : 1 à 24 hommes, skill 0 à 1, défaut 0,5. poser_scene : 0 à 24 bleus et 0 à 24 rouges, distance 30 à 1500 m, défaut 220 m, combat vrai par défaut. etat : detail 0 à 200, défaut 0. ordonner : 7 ordres (aller, arreter, comportement, combat, vitesse, posture, reveler), 5 comportements, 5 modes de combat, 3 vitesses, 4 postures. Coordonnées Altis bornées 0 à 31000 m. Ancre par défaut (8291.45, 10065.42). 3 camps posables sur 4 connus. 4 causes de refus renvoyées par la mission.

**Sources.** /mnt/data/hmt/depot/labo/mcp_arma.py lignes 43 à 93 (la table OUTILS) ; /mnt/data/hmt/depot/labo/arma_labo.py lignes 537 à 656 (canari, etat, poser_groupe, poser_scene, ordonner, nettoyer, sqf) et lignes 69 à 78 (CAMPS, ORDRES, VALEURS, REFUS_MISSION)

**Reste ouvert.** Rien à établir de plus sur la liste des outils : elle est close et vérifiée par les tests.

### [ETABLI] La règle d'usage : MCP = labo, job = mesure, rien ne traverse

*2026-09-11*

La règle est écrite trois fois, au même mot près, dans le LISEZMOI, dans l'en-tête du module et dans les instructions que le serveur envoie au client MCP. Le labo sert à régler une scène et à trouver une panne ; il ne produit aucun chiffre publiable, qui ne naît que d'un job de la file avec ses graines. Le module refuse toute instance autre que la 9, parce que pointé sur le pont d'un job il effacerait ses commandes en s'ouvrant. Un seul écrivain tient le pont, par le verrou etat/labo_i9.ecrivain, et le MCP prend aussi queue/verrous/j9 pour que la file le compte dans son plafond. Chaque commande rend un reçu, et une absence de reçu lève une exception au lieu de rendre une liste vide : jamais « aucun » à la place de « pas de réponse ». Seuls des nombres remontent vers le LLM, jamais du texte du monde. Le SQF brut est refusé s'il contient un commentaire, parce que call compile ne les retire pas et qu'un seul // tue la commande en silence.

**Mesures.** Instance imposée : 9. Un seul écrivain par pont. Reçu obligatoire par commande, de forme « [LABO] ECHO n nonce k », où k est le nombre de lignes de résultat à lire. 5 exceptions typées : PontMort, SansRecu, Incomplet, Occupe, Refus. Le garde de la file est bien posé : controle_avant_run.sh lignes 41 à 47 refuse tout job qui ne tolère pas « labo » quand le serveur du labo tourne. lancer_labo.sh refuse dans l'autre sens, et refuse aussi si le déploiement de la mission n'est pas prouvé par diff.

**Sources.** /mnt/data/hmt/depot/labo/LISEZMOI.md ; /mnt/data/hmt/depot/labo/arma_labo.py lignes 1 à 78 ; /mnt/data/hmt/depot/labo/mcp_arma.py lignes 8 à 38 ; /mnt/data/hmt/depot/outils/controle_avant_run.sh lignes 41 à 47 ; /mnt/data/hmt/depot/labo/lancer_labo.sh lignes 27 à 62

**Reste ouvert.** Le module le dit lui-même : le reçu prouve que la commande s'est compilée et que l'exécution a atteint la dernière ligne. Une erreur au milieu laisse SQF continuer et le reçu arrive quand même. Le compteur erreurs_rpt est un indice, pas une preuve.

### [ETABLI] Le banc pontmcp a été joué et il PASSE, sur deux graines

*2026-09-11*

Le banc existe et il a tourné, ce qui n'était pas acquis. Ses sept critères ont été écrits avant, dans l'en-tête du script et dans le champ note du job. Deux critères sont des contrôles positifs, cinq exigent que le labo sache échouer. Les deux graines rendent PASSE, avec sept critères vrais sur sept chacune. Les mesures sont loin des seuils : la médiane des cent canaris est à 488 ms pour un seuil de 1000 ms, et le p99 à 492 ms pour un seuil de 3000 ms. Le critère le plus dur, E5, tue le serveur et exige que le labo LÈVE au lieu de répondre : il lève PontMort en 12,0 s, avec le message « on ne sait RIEN de l'état du monde ».

**Mesures.** Run de 257 s, code 0, FIN COMPLET, 2 épisodes lus sur 2, 2 graines lues sur 2. C1 : 100 canaris reçus, 0 perdu, médiane 488,5 ms et p99 492 ms (g1) ; 488,0 ms et 493 ms (g2). C2 : 8 posés, 8 comptés, 8 détaillés, écart max 7,7 m (g1) et 8,2 m (g2), seuil 20 m. E1 : SQF avec // refusé, compteur 104 → 105, donc seul le canari est parti. E2 : deuxième processus refusé, code de retour 3. E3 : 8 + 3 posés à la main = 11 non-joueurs comptés. E4 : 20 tirages, 0 écart entre etat.unites et count allUnits. E5 : PontMort levé en 12,0 s sur les deux graines. Labo prêt en 30 s aux deux démarrages, mission d'empreinte 444c90cced11.

**Sources.** /mnt/data/hmt/runs/2026-09-11_165356_pontmcp_i9/ (job.json, FIN.json, run.log, g1/resultat.json, g2/resultat.json, g1/serveur.rpt 76070 octets, g2/serveur.rpt 75702 octets) ; /mnt/data/hmt/depot/labo/banc_pontmcp.py ; /mnt/data/hmt/depot/bancs/pontmcp/lancer.sh ; /mnt/data/hmt/queue/faits/2026-09-11_MCP6_pontmcp.json

**Reste ouvert.** Le banc n'a jamais été rejoué depuis le 11/09. Aucun run pontmcp dans /mnt/data/hmt/archive/. Et il ne prouve rien sur le MCP lui-même : il appelle arma_labo.py en direct, pas le transport JSON-RPC.

### [ETABLI] Le contrôle de contamination : à moitié fait

*2026-09-11*

Le contrôle demandé par Fable, appelé MCP-7, voulait qu'un vrai job tourne sur une autre instance pendant le banc. Cette moitié-là est faite : cinq jobs chacal tournaient sur les instances 1 à 5 au même moment, et tous les cinq déclarent « labo » dans leur champ tolere. Le banc a rendu FIN COMPLET comme attendu. La seconde moitié n'a pas pu marcher comme écrit. Le LISEZMOI attendait que charge_au_lancement cite le serveur du labo, or ce relevé est pris à 16:53:56, au lancement du job, et le labo ne démarre qu'à 16:54:26 dans le passage de la graine 1. Le fichier ne contient donc que « 5 arma3server_x64.exe », sans le labo. Le second point du LISEZMOI, lui, est vérifié par la mesure : le catalogue ignore bien le résultat de pontmcp.

**Mesures.** 5 jobs chacal en parallèle, instances 1 à 5, graines 7 et 8, tous avec tolere = [UnrealEditor, vmware-vmx, labo]. charge_au_lancement = « 5 arma3server_x64.exe », relevé à 16:53:56, labo démarré à 16:54:26. Catalogue : 0 ligne pontmcp sur 514 épisodes, et 0 ligne i9.

**Sources.** /mnt/data/hmt/runs/2026-09-11_165356_pontmcp_i9/charge_au_lancement.txt et run.log ; /mnt/data/hmt/runs/2026-09-11_164849_chacal_i1/job.json à 2026-09-11_165119_chacal_i5/job.json ; /mnt/data/hmt/depot/catalogue/episodes.csv ; /mnt/data/hmt/depot/outils/catalogue.py ligne 211

**Reste ouvert.** Le contrôle de contamination tel qu'écrit dans le LISEZMOI n'a pas été observé : personne ne peut montrer le serveur du labo dans un charge_au_lancement, puisque ce relevé précède son démarrage. Il faudrait relever la charge en cours de run, ou lancer le labo avant le job.

### [ETABLI] Le transport MCP n'a jamais été lancé une seule fois

*2026-09-13*

C'est le constat central de cette revue. mcp_arma.sh écrit une ligne de démarrage horodatée dans etat/mcp_arma.log dès qu'il est appelé, et ce fichier n'existe pas. Le serveur MCP n'a donc jamais tourné, ni en session, ni en essai. L'étape 6 du branchement n'est pas faite non plus : sur le Mac, ~/.claude.json ne déclare qu'un seul serveur MCP, plane. Le labo est pourtant bien utilisé, mais par un autre chemin : des scripts Python qui importent arma_labo directement. Le banc pontmcp fait pareil. Autrement dit, ce qui est prouvé et employé, c'est le module ; le MCP, qui est la partie annoncée par le nom du projet, reste un morceau non joué.

**Mesures.** /mnt/data/hmt/etat/mcp_arma.log : absent. ~/.claude.json : mcpServers = ['plane'], 1 serveur déclaré, 0 nommé arma. 4 scripts hors labo/ importent arma_labo : atelier.py, atelier2.py, atelier3.py, atelier4.py. Le transport est couvert par les tests du jouet, mais jamais face à Arma.

**Sources.** /mnt/data/hmt/depot/labo/mcp_arma.sh ligne 10 (exec 2>>/mnt/data/hmt/etat/mcp_arma.log) ; /Users/ybouhassoun/.claude.json ; /mnt/data/hmt/depot/labo/LISEZMOI.md section « Brancher », étape 6 ; /mnt/data/hmt/atelier/

**Reste ouvert.** Le banc PASSE était la condition écrite pour inscrire le MCP sur le Mac. La condition est remplie depuis le 11/09 et l'inscription n'a pas été faite. Rien dans le dépôt n'explique pourquoi.

### [ETABLI] Ce que le labo a servi à mesurer : le placeur d'appui de CHACAL

*2026-09-12*

C'est le seul usage du labo qui ait changé du code de production. Trois commits du 12/09 citent une mesure faite au labo, et chacun porte ses nombres dans l'en-tête de son correctif. Le labo a servi à reconstruire le site de la graine 7 et à compter, par rayons, combien de positions voient le plancher du site. La première mesure a montré que l'ancien placeur rejetait tout relief local de plus de 6 m, c'est-à-dire exactement les buttes qui donnent la vue par-dessus un mur. La seconde a montré qu'il ratait aussi les positions BASSES qui voient par une porte ou un creux, et que son tirage au hasard manquait un secteur étroit. Le remède mesuré est un balayage systématique où la couverture remplace la hauteur comme juge.

**Mesures.** Première mesure (patch_placeur3) : enceinte de 31 HBarrier à 46 m de rayon, 199 positions sur 504 voient le plancher, les meilleures voient les 37 points, dont une à 150 m avec 11 m de dénivelé. Règle dérivée : hauteur >= D/20 + 2 au-dessus du sol du site, soit 8 m à 150 m et 12 m à 250 m ; platitude jugée sur 5 m ; bande 120-450 m. Seconde mesure (patch_balayage) : site reconstruit avec mur, QG, tour et antenne, 102 positions sur 288 voient le plancher, dont une à 150 m au nord-est située 3 m EN DESSOUS du site. Balayage retenu : 36 azimuts x 8 distances de 150 à 500 m = 288 candidats, ~10 000 rayons par candidat, quelques dixièmes de seconde au labo, écart minimal de 25 degrés à l'axe d'assaut, refus sous 25 % de couverture.

**Sources.** commits 3b2f9ea et 4661dfc du 2026-09-12 ; /mnt/data/hmt/depot/correctifs/patch_placeur3.py (en-tête, MARQUEUR-CORRECTIF-PLACEUR-HAUTEUR) ; /mnt/data/hmt/depot/correctifs/patch_balayage.py (en-tête, MARQUEUR-CORRECTIF-PLACEUR-BALAYAGE) ; /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/00_socle.sqf

**Reste ouvert.** Aucune trace brute de ces séances n'a été retrouvée sur le disque : ni script, ni journal, ni sortie. Les nombres ne vivent que dans les en-têtes de correctif et les messages de commit. On ne peut donc pas rejouer la mesure ni vérifier son instrumentation.

### [EN COURS] Le labo comme témoin : il a montré que la mesure du placeur se tait par moments

*2026-09-12*

C'est le second usage, et le plus utile au raisonnement. Deux épisodes identiques, même graine et même site, ont rendu l'un 0,541 de couverture et l'autre 0 sur 288, avec les mêmes refus géométriques. Le terrain n'avait pas changé, donc l'écart venait de la mesure. Le labo a servi d'arbitre : le même balayage sur trois zones vierges y rend des nombres stables, identiques à froid et vingt secondes plus tard. La conclusion tirée est que la mesure ne se trompe pas, elle se tait. Un témoin au sens de la règle 16 a donc été posé dans le placeur, et le balayage recommence au lieu de conclure. Le 12/09 au soir, le témoin répond 1 et le balayage rend toujours 0 sur une instance : quatre sondes ont été posées pour nommer ce qui arrête les rayons, sans effet sur le choix.

**Mesures.** Deux épisodes, même graine, site [6804.04, 11678.3], 7 pentes et 40 axes refusés sur 288 dans les deux cas ; couverture 0,541 contre 0 sur 288. Au labo : 47, 92 et 56 positions qui voient sur trois zones vierges, identiques à froid et 20 s plus tard. Témoin posé : depuis le centre du site à 2 m de haut, réponse attendue connue. Relance : 3 passes à 6 s d'écart. Le 12/09 au soir : témoin = 1, balayage 0 sur 288 à la première passe, 0,541 à la seconde sur une instance, 0 sur l'autre. La position à 0,541 est à 500 m, où l'appui voit 0 défenseur.

**Sources.** commits 89fae4c et a2c101c du 2026-09-12 ; /mnt/data/hmt/depot/correctifs/patch_temoin.py ; /mnt/data/hmt/depot/correctifs/patch_sonde.py ; /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/00_socle.sqf

**Reste ouvert.** La cause du silence de la mesure n'est pas nommée. Les quatre sondes sont un journal, pas un verdict : au moment de cette revue, rien n'a encore été écrit sur ce qu'elles ont vu. Et le constat que couvrir le plancher n'est pas voir les hommes reste sans remède.

### [EN COURS] L'atelier : une séance de labo en cours pendant cette revue

*2026-09-12 au 2026-09-13*

Un troisième usage a commencé le 12/09 à 23h50 et tournait encore pendant que j'écrivais. Quatre scripts reconstruisent au labo le site de la graine 7 de CHACAL et y jouent des essais à prédiction écrite avant. Le premier essai est un contrôle positif au sens de la règle 16 : un homme seul marche sur le site, et s'il n'est ni vu ni touché, c'est l'atelier qui est cassé. Il est mort, donc l'atelier mesure quelque chose. Le deuxième essai a réfuté la prédiction de son auteur : dix hommes chargeant en ligne droite perdent deux hommes, pas la moitié. Ces scripts vivent hors du dépôt et ne sont pas versionnés. Ils importent arma_labo en direct, alors que leur propre en-tête dit « par le MCP ».

**Mesures.** Site reconstruit : 35 objets, 18 murs HBarrier, 4 bunkers, 5 défenseurs dont 5 dans un bâtiment. E0 contrôle positif : 1 homme à 300 m, 0 vivant sur 1, distance minimale 142 m, 0 coup bleu contre 1 coup rouge, premier coup à 45 s, 5 couples rouges qui savent. E1 assaut nu : 10 hommes, 8 vivants sur 10, 2 rouges tués sur 5, 7 entrés dans l'enceinte, distance minimale 31 m, 420 coups bleus contre 58 rouges, premier coup à 45 s. Prédiction écrite avant (perdre la moitié) : FAUSSE. État à 00:04:33 le 13/09 : atelier4.py vivant en PID 39689, verrou écrivain et verrou j9 tenus, serveur du labo PID 17712 vivant, RPT écrit il y a 2 s, 8 arma3server au total soit les 7 de la campagne plus le labo, et les 7 jobs en cours tolèrent tous « labo ».

**Sources.** /mnt/data/hmt/atelier/atelier.py, atelier2.py, atelier3.py, atelier4.py ; /mnt/data/hmt/atelier/journal.jsonl (3 lignes) ; /mnt/data/hmt/etat/labo_arma.pid ; /mnt/data/hmt/etat/labo_i9.ecrivain ; /mnt/data/hmt/queue/verrous/j9/pid

**Reste ouvert.** L'atelier n'est dans aucun commit : il vit dans /mnt/data/hmt/atelier/, hors dépôt, et disparaîtrait sans laisser de trace. Le journal ne compte que 3 lignes pour trois essais lancés. Les essais E2 à E5 d'atelier4.py n'ont pas encore écrit leur ligne.

### [OUVERT] Ce qui reste inachevé, nommé et vérifié

*2026-09-13*

Cinq manques tiennent encore, et je les ai vérifiés un par un plutôt que de les recopier du LISEZMOI. Le MCP n'est pas branché : son journal n'existe pas et le Mac ne le déclare pas. La mission du labo n'a toujours pas de place joueur, donc Younes ne peut pas s'y connecter pour regarder. Aucun verdict n'a été écrit sur le labo : le dossier verdicts/ n'en contient aucun qui parle de labo ou de MCP. Le seul manque du LISEZMOI qui soit levé est celui du catalogue, et il l'est par la mesure. Enfin, le labo est resté allumé : c'est un huitième serveur Arma à côté des sept de la campagne, toléré par les jobs en cours mais jamais arrêté.

**Mesures.** mission.sqm : class Entities { items=0; }, donc 0 place joueur, sur 45 lignes de fichier. verdicts/ : 0 fichier sur 58 mentionne labo ou mcp. catalogue : 0 ligne pontmcp sur 514 épisodes, manque levé. etat/mcp_arma.log : absent. Serveurs Arma en cours : 8, dont le labo PID 17712 démarré le 12/09 à 23:49. Verrou écrivain tenu par atelier4.py, PID 39689.

**Sources.** /mnt/data/hmt/depot/labo/mission.Altis/mission.sqm ; /mnt/data/hmt/depot/verdicts/ ; /mnt/data/hmt/depot/catalogue/episodes.csv ; /mnt/data/hmt/etat/ ; /mnt/data/hmt/depot/labo/LISEZMOI.md section « Ce qui manque »

**Reste ouvert.** Le LISEZMOI disait que la place joueur serait ajoutée après le premier PASSE. Le PASSE date du 11/09 et la place joueur n'est pas là. L'arrêt du labo est explicitement réservé à la main de Younes par arreter_labo.sh, ce qui explique qu'il reste allumé mais ne dit pas si c'est voulu.

### Ce que ce lecteur n'a PAS pu établir

Je n'ai rien lancé et rien modifié : tout ce qui suit vient de lectures de fichiers et de l'historique git.

Ce que je n'ai PAS pu établir :

1. Les 33 tests du jouet. J'ai compté 33 fonctions de test dans /mnt/data/hmt/depot/labo/test_labo.py, ce qui confirme le chiffre du LISEZMOI. Mais je n'ai pas exécuté la suite, donc je ne peux pas dire qu'elle passe aujourd'hui. Et je n'ai pas retrouvé les « 7 casses volontaires du module, toutes détectées » annoncées : une seule marque de sabotage explicite est visible, test_labo.py ligne 351 (saboter_a = 7). Les six autres sont peut-être ailleurs sous un autre nom, je ne l'ai pas vérifié.

2. Les séances de labo du 12/09 sur le placeur. Les nombres (199 sur 504, 102 sur 288, 47/92/56, 37 points) ne sont attestés que par les en-têtes des correctifs et les messages de commit. Aucune sortie brute, aucun script de mesure, aucun journal n'a survécu sur le disque : ma recherche des fichiers qui parlent au labo hors depot/labo ne rend que les quatre atelier*.py, créés le 12/09 à 23h50, donc bien après. Ces mesures ne sont pas rejouables en l'état.

3. La page wiki « MCP Arma — dossier », citée dans /mnt/data/hmt/runs/2026-09-11_165356_pontmcp_i9/run.log comme faisant 5347 caractères. Elle vit dans Plane et je ne l'ai pas ouverte. Elle contient peut-être le verdict que je ne trouve pas dans depot/verdicts/.

4. Pourquoi le MCP n'a pas été inscrit sur le Mac alors que sa condition (banc PASSE) est remplie depuis le 11/09. Le dépôt ne porte aucune trace de décision, ni dans les commits, ni dans les verdicts. Je constate le fait, je n'en connais pas la cause.

5. L'issue de la séance d'atelier en cours. Elle tournait encore à 00:04:33 le 13/09 (atelier4.py, PID 39689). Les essais E2 à E5 n'avaient pas encore écrit dans le journal. Je n'ai ni attendu ni interrogé le processus.

6. Le sort du doublon /mnt/data/hmt/mcp-arma/. Il contient une copie complète de labo/ et bancs/ datée du 11/09 16:05, soit avant le commit de 16:46. Je n'ai pas comparé les deux arborescences fichier par fichier, donc je ne peux pas dire si elles ont divergé.

---

## Les leviers de CHACAL

### [REFUTE] Oracle a l assaut (CHACAL_ORACLE = 1) : ne fait pas gagner

*2026-09-11*

Le levier revele les defenseurs du site a tous nos hommes et les inscrit comme vus, puis rafraichit cette connaissance au debut de l assaut. Il ne touche que la connaissance, pas le mouvement ni le feu. Le critere etait ecrit avant le premier episode : reussite si l oracle pose 3 charges sur 3 dans au moins 15 episodes sur 18, echec a 9 sur 18 ou moins. Le resultat tombe a 8 sur 18, donc dans la zone d echec. Le verdict est ECHEC et il porte une reserve majeure : l oracle est pose APRES le choix de la porte d entree, donc la porte reste choisie a l aveugle.

**Mesures.** oracle 8 sur 18 (44 %) contre reference 4 sur 12 (33 %), memes graines 7 et 8, memes heures, 3 jobs oracle contre 2 jobs reference. Detail par graine, oracle : graine 7 = 3 sur 9, graine 8 = 4 sur 8 (17 episodes acceptes au catalogue). Reference : graine 7 = 3 sur 6, graine 8 = 1 sur 6. Fisher unilateral 0,41, ecart non significatif. Vivants moyens 8,7 avec oracle contre 8,0 sans.

**Sources.** /mnt/data/hmt/depot/verdicts/oracle-savoir-a-l-assaut.md ; runs /mnt/data/hmt/runs/2026-09-11_164849_chacal_i1, _164949_chacal_i2, _165019_chacal_i3, _165049_chacal_i4, _165119_chacal_i5 ; code /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/60_phases.sqf lignes 957-963 et 1060-1064 ; declaration /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/00_socle.sqf ligne 46 ; commit c93fc26

**Reste ouvert.** On ne sait pas ce que vaudrait un oracle donne a un executant qui sait s en servir. Le verdict note que l appui qui recoit des cibles en mode RED part au contact au lieu de fixer.

### [OUVERT] Oracle complet (CHACAL_ORACLE = 2) : mesure faite, verdict jamais ecrit

*2026-09-11*

Apres la revue de Fable, l oracle a ete avance AVANT le choix de la porte d entree, pour repondre a la reserve du verdict precedent. Le job porte le meme critere ecrit d avance : reussite a 15 sur 18 ou plus, echec a 9 sur 18 ou moins. Le resultat est exactement 9 sur 18, soit la borne d echec. La reference jouee en meme temps fait 6 sur 11, donc mieux en proportion. Aucun fichier de verdict n existe pour cette mesure, et elle n apparait pas dans la table des verdicts vivants d ETAT.md.

**Mesures.** oracle complet 9 sur 18 (50 %) contre reference 6 sur 11 (55 %), graines 7 et 8, 18 episodes acceptes contre 11. Detail oracle complet : graine 7 = 4 sur 9, graine 8 = 5 sur 9. Reference : graine 7 = 4 sur 6, graine 8 = 2 sur 5. Fisher unilateral 0,73 (calcul fait ici, non pre-inscrit). Vivants moyens 9,1 contre 7,9. Le catalogue compte 18 episodes a oracle = 2, tous dans la campagne ORACLE-COMPLET-11-09.

**Sources.** runs /mnt/data/hmt/runs/2026-09-11_182059_chacal_i1, _182159_chacal_i2, _182230_chacal_i3, _182300_chacal_i4, _182330_chacal_i5 ; job.json champ note de _182059_chacal_i1 ; code 60_phases.sqf lignes 884-890 ; commit 340c61d ; /mnt/data/hmt/depot/catalogue/episodes.csv ; aucun fichier dans /mnt/data/hmt/depot/verdicts/

**Reste ouvert.** Le verdict n a pas ete redige : le chiffre atteint la borne d echec ecrite d avance mais le projet n a rien tranche. Je n ai pas verifie moi-meme, dans les journaux, que la porte choisie change effectivement entre oracle 0 et oracle 2.

### [REFUTE] Accessible (CHACAL_ACCESSIBLE) : correction terrain sans effet

*2026-09-10*

Le levier exige qu une position retenue soit atteignable depuis le point de depart, pas seulement plate. Il est ne d un seul episode ou le moteur declarait l arrivee a 800 m avec des pentes de 29 et 37 degres, fin par ARTICULATION_ROMPUE. Rejoue quatre fois par bras au palier 4, le blocage n est jamais revenu, meme sans la correction. Les deux bras donnent le meme nombre de succes. Le verdict est ECHEC et il tire une lecon de methode : un echec vu une fois se rejoue avant d etre corrige.

**Mesures.** accessible 0 : 2 succes complets sur 4 episodes (graine 7 : 1 sur 2 ; graine 8 : 1 sur 2). accessible 1 : 2 succes sur 4 (graine 7 : 0 sur 2 ; graine 8 : 2 sur 2). La prediction visait a debloquer la graine 7 : elle donne 0 sur 2 AVEC la correction et 1 sur 2 SANS. Aucun abandon sur les 8 episodes. A 4 episodes par bras, un effet de plus de 3 sur 4 est exclu, rien de plus petit n est mesure. Le parametre reste dans le code a 0 par defaut.

**Sources.** /mnt/data/hmt/depot/verdicts/accessible-sans-effet-palier4.md ; runs /mnt/data/hmt/runs/2026-09-09_1625_chacal (accessible 0) et /mnt/data/hmt/runs/2026-09-09_1635_chacal (accessible 1) ; code 00_socle.sqf lignes 66 et 602 ; commit 40530c9

**Reste ouvert.** Un effet inferieur a 3 episodes sur 4 reste possible et n a jamais ete mesure. Les episodes du 09/09 ne portent pas accessible dans leur ligne FINI : l attribution repose sur job.json, pas sur le journal de l episode.

### [OUVERT] Effectif (10 contre 20 hommes) : issue non jugeable, compteur casse

*2026-09-09*

Le levier double le detachement en rejouant deux fois la liste des roles. Les deux episodes a vingt hommes posent les trois charges et ramenent dix-sept vivants sur vingt. Ils sont pourtant juges EXFIL_MANQUEE. La cause est lue dans le code : la phase 6 se fermait des que six hommes arrivaient au point d exfiltration, six ecrit en dur, alors que le verdict exige 0,6 fois l effectif, soit douze a vingt hommes. Un episode a vingt ne pouvait donc jamais etre un succes. Le verdict reste OUVERT.

**Mesures.** 2 episodes acceptes, tous deux 3 charges sur 3 et 17 vivants sur 20, avec exfiltres = 6 exactement pour un seuil de 12. Defenseurs tues 2 et 4 ; durees 6802 s et 6612 s. A dix hommes sur le meme palier, les trois charges ne sont posees que 4 fois sur 8. Le correctif est aujourd hui EN PLACE dans le code : 60_phases.sqf lignes 1406 a 1409 lisent round (0,6 x CHACAL_EFFECTIF). Aucun episode a effectif 20 n a ete rejoue depuis : le catalogue de 513 episodes n en contient aucun.

**Sources.** /mnt/data/hmt/depot/verdicts/vingt-hommes-compteur-plafonne.md ; run /mnt/data/hmt/runs/2026-09-09_1615_chacal ; correctif /mnt/data/hmt/depot/correctifs/2026-09-10_exfil_suit_effectif.py ; code 40_blufor.sqf ligne 63 et 60_phases.sqf lignes 1406-1409 ; commits 4121407 et 40530c9

**Reste ouvert.** Le rejeu V20b, prevu derriere le correctif, n a jamais tourne. On ne sait donc pas si vingt hommes gagnent, et le verdict de positions sans plan de feu previent qu a vingt on gagnerait par attrition, ce qui ferait entrer un faux geste dans le corpus.

### [OUVERT] Feu avant (CHACAL_FEU_AVANT) : tendance en vignette, non repliquee le lendemain

*2026-09-10 au 2026-09-11*

Le levier designe les defenseurs a l appui, le laisse tirer en premier, et fait attendre l assaut son premier coup avant de marcher en AWARE avec un ordre relance toutes les dix secondes. En vignette le 10/09, l assaut passe de 2 a 5 reussites sur 10, un ecart dans le sens attendu mais a 0,17 de probabilite sous le hasard. Le verdict a ete laisse OUVERT. Le 11/09, le meme levier rejoue dix fois sur la graine 8 donne 3 sur 10 contre 4 sur 10 pour sa reference, donc l inverse. Deux mesures sures restent : sans designation l appui ne connait aucune cible et ne tire jamais avant l assaut, et en mode RED il quitte sa position au lieu de tirer.

**Mesures.** 10/09, vignette, graines 7 et 8, cinq repetitions par bras : feu_avant 0 = 2 sur 10 (graine 7 : 0 sur 5 ; graine 8 : 2 sur 5) ; feu_avant 1 = 5 sur 10 (graine 7 : 2 sur 5 ; graine 8 : 3 sur 5) ; Fisher unilateral 0,17. L appui tire avant le premier pas dans 7 episodes sur 10 avec, 0 sur 10 sans. 11/09, graine 8 seule, campagne G8 : V3 (feu_avant 1) = 3 sur 10 contre V2 (reference) = 4 sur 10 ; Fisher unilateral 0,83 (calcul fait ici). Dans les episodes ou l appui ne tire pas, les deux tireurs partent a 11 a 18 km/h, l un finit a 72 m des defenseurs, un autre a 400 m.

**Sources.** /mnt/data/hmt/depot/verdicts/feu-avant-vignette.md ; runs /mnt/data/hmt/runs/2026-09-10_1505_chacal (feu_avant 0), _2026-09-10_1515_chacal (feu_avant 1), 2026-09-10_1445_chacal (controle), 2026-09-11_113559_chacal_i5 (V3) ; code 60_phases.sqf lignes 1147 et 1204-1211 ; commits e8e77ea et 85de336

**Reste ouvert.** Trois mecanismes changent ensemble : designation, attente du premier coup, relance de l ordre. On ne sait pas lequel agit. La relance est soupconnee de casser la marche du porteur vers la tour, ce n est pas verifie.

### [OUVERT] Mitrailleuse a l assaut (CHACAL_MG_ASSAUT) : aucun verdict, ecart nul

*2026-09-11*

Le levier donne une Mk200 a l adjoint de l element d assaut, avec 200 cartouches. La question ecrite dans le job etait de savoir si le defenseur seul de la tour tombe avant nos porteurs. Le bras fait 5 reussites sur 10 contre 4 sur 10 pour sa reference jouee le meme jour sur la meme graine. L ecart est nul au sens statistique. Aucun fichier de verdict n a ete redige et le levier n apparait dans aucun verdict du registre.

**Mesures.** V5 (mg_assaut 1) = 5 episodes a 3 charges sur 3 sur 10 ; V2 (reference, mg_assaut 0) = 4 sur 10. Graine 8 seule. Fisher unilateral 0,50 (calcul fait ici, non pre-inscrit). Sur les 6 episodes de V5 qui passent la porte de lecture, 4 sont a 3 sur 3 ; les 4 autres viennent d un dossier de run contamine le 11/09 et n ont pas de porte de lecture. La munition journalisee vaut 200 dans les dix episodes. Vivants moyens 8,5 contre 7,5 pour la reference.

**Sources.** runs /mnt/data/hmt/runs/2026-09-11_124559_chacal_i5 (6 episodes certifies) et /mnt/data/hmt/runs/2026-09-11_0920_chacal (4 episodes, dossier contamine) ; reference /mnt/data/hmt/runs/2026-09-11_100018_chacal_i2 ; code 60_phases.sqf ligne 1187 ; declaration 00_socle.sqf ligne 42 ; catalogue /mnt/data/hmt/depot/catalogue/episodes.csv, campagne G8-FABLE-11-09 version V5 ; commit c7e9fcd

**Reste ouvert.** Aucun critere de reussite ou d echec n a ete ecrit avant le run, seulement une question. Le chiffre demande par le job, le nombre de porteurs tues a la tour, n a pas ete extrait et je ne l ai pas mesure.

### [OUVERT] Delai du porteur (CHACAL_DELAI_PORTEUR, 45 s puis 120 s) : aucun verdict, ecart nul

*2026-09-11*

Le levier allonge le temps accorde a un porteur pour atteindre son point de pose, de 45 a 120 secondes. La question ecrite etait de savoir si le porteur manque de temps ou de chemin. Le bras fait 5 reussites sur 10 contre 4 sur 10 pour sa reference. Le journal montre que le temps supplementaire est reellement consomme, donc le levier agit bien sur ce qu il vise. L ecart de reussite reste nul. Aucun fichier de verdict n a ete redige.

**Mesures.** V6 (delai 120 s) = 5 episodes a 3 charges sur 3 sur 10 ; V2 (delai 45 s) = 4 sur 10. Graine 8 seule, 10 episodes acceptes de chaque cote. Fisher unilateral 0,50 (calcul fait ici, non pre-inscrit). Preuve que la butee a bouge : les temps de porteur journalises atteignent 121 s a la tour et 120 s a l antenne dans V6, alors qu ils plafonnent a 45 s ou 46 s dans V2, V3 et V4. Vivants moyens 8,2 contre 7,5.

**Sources.** run /mnt/data/hmt/runs/2026-09-11_100139_chacal_i5 ; reference /mnt/data/hmt/runs/2026-09-11_100018_chacal_i2 ; code 60_phases.sqf lignes 1325-1328 ; declaration 00_socle.sqf ligne 43 ; colonne porteur_temps de /mnt/data/hmt/depot/catalogue/episodes.csv ; commit c7e9fcd

**Reste ouvert.** Aucun critere n a ete ecrit avant le run. La question posee, du temps ou un chemin, n a pas recu de reponse : le temps a ete donne et l issue n a pas bouge, ce qui oriente vers le chemin sans le prouver.

### [OUVERT] Appui fixe (CHACAL_APPUI_FIXE) : la reference n a pas produit le phenomene a expliquer

*2026-09-11*

Le levier cloue l element d appui une fois arrive : mode YELLOW, deplacement et LAMBS coupes. La question etait de savoir si c est le mouvement de l appui qui fait reperer le detachement. Le job prevenait lui-meme que si le repere tombe avant l arrivee de l appui, le bras ne peut pas repondre. La reference attendait six reperes sur six ; elle en donne un seul. Avec l appui cloue, il y en a deux, donc plus et non moins. Les deux bras s arretent a la phase 4, avant l assaut : aucune charge n est posee de part et d autre, par construction. Aucun fichier de verdict n a ete redige.

**Mesures.** V9 (appui_fixe 1) : 2 compromissions sur 6 episodes acceptes, a 1941 s et 1991 s, cause ENNEMI_VU_EN_COMBAT, phase 4. V7 (reference, appui_fixe 0) : 1 compromission sur 6, a 1747 s, meme cause. Attendu ecrit dans le job pour la reference : 6 sur 6. Fisher unilateral 0,50 (calcul fait ici). Dix vivants sur dix dans les douze episodes ; 0 charge sur 3 dans les douze, la vignette s arretant a la phase 4. Durees 1946 a 2074 s.

**Sources.** runs /mnt/data/hmt/runs/2026-09-11_114559_chacal_i4 (V9) et /mnt/data/hmt/runs/2026-09-11_112559_chacal_i2 (V7) ; code 60_phases.sqf lignes 925, 1090 et 1394 ; declaration 00_socle.sqf ligne 44 ; commit c7e9fcd

**Reste ouvert.** La mesure ne peut pas trancher : le phenomene qu elle devait expliquer, etre repere, ne s est produit qu une fois sur six dans la reference. A 6 episodes par bras, rien de plus petit qu un ecart enorme ne serait visible. Le meme clouage a ete repris plus tard dans le socle du 12/09, ou il est mesure autrement.

### [OUVERT] Tenir (CHACAL_TENIR) : deux mesures, aucun verdict

*2026-09-08 au 2026-09-11*

Le levier fait poursuivre le plan malgre la compromission ; la compromission reste journalisee a l identique, seule la reaction change. Au palier 0 le 08/09, il supprime l abandon pour eloignement mais double la duree et coute des survivants, sans faire poser une seule charge. Le 11/09 au palier 4, avec la mise en place jouee depuis le regroupement, il donne 3 reussites sur 6 contre 4 sur 10 pour la reference d assaut. Le job portait sa propre phrase de refutation : repere et tenant, l assaut ne pose pas plus que la reference. A 50 % contre 40 % et dans le bruit, cette phrase n est pas contredite. Aucun fichier de verdict n a ete redige.

**Mesures.** 08/09, palier 0, une graine par episode. tenir 1 : graine 7 ABANDON ARTICULATION_ROMPUE, 5 vivants, 8718 s, compromis a 5034 s ; graine 8 ECHEC CHARGES_INCOMPLETES, 2 vivants, 6454 s, compromis a 4718 s. tenir 0 : graine 7 ABANDON COMPROMIS_LOIN, 9 vivants, 3666 s, compromis a 1420 s ; graine 8 ABANDON COMPROMIS_LOIN, 8 vivants, 2856 s, compromis a 1058 s. Zero charge sur 3 dans les quatre episodes. 11/09, palier 4, graine 8 : V8 (tenir 1) = 3 sur 6 a 3 charges sur 3, vivants 10, 10, 9, 5, 5, 9, compromis dans les 6 entre 2053 et 2258 s ; reference V2 = 4 sur 10. Fisher unilateral 0,55 (calcul fait ici).

**Sources.** runs /mnt/data/hmt/runs/2026-09-08_2235_chacal (tenir 1) et _2026-09-08_2255_chacal (tenir 0) ; run /mnt/data/hmt/runs/2026-09-11_100219_chacal_i3 (V8) ; reference /mnt/data/hmt/runs/2026-09-11_100018_chacal_i2 ; code 00_socle.sqf ligne 67, 60_phases.sqf lignes 401 et 740 ; commits d689033 et bc4d95b

**Reste ouvert.** La comparaison du 08/09 vaut deux episodes par bras, et le verdict du plancher de bruit dit que les comparaisons de ce jour ont perdu leur valeur de preuve. Les deux bras du 11/09 ne partagent pas la meme phase d arret, donc la comparaison V8 contre V2 n est pas appariee.

### [ETABLI] Palier de force : le seul levier qui deplace l issue de bout en bout

*2026-09-07 au 2026-09-12*

Le palier ne regle pas notre camp, il regle l adversaire. Le palier 0 met quatre hommes de garnison, une ronde interieure, une piece servie et un vehicule de reserve a 180 secondes. Le palier 4, dit leger, laisse quatre defenseurs et rien d autre : ni ronde, ni patrouille, ni piece servie, ni reserve. Le palier 9 vide le monde de tout ennemi et sert de controle positif de l acte lui-meme. Le taux de pose suit ces trois niveaux sans ambiguite, et c est le plus gros effet du banc, plus gros que tous les leviers tactiques mesures.

**Mesures.** Sur les 513 episodes du catalogue, en ne gardant que ceux dont la porte de lecture est ACCEPTE : palier 0 = 3 episodes a 3 charges sur 3 sur 44 (6,8 %), 5,2 vivants en moyenne, cinq causes de fin differentes ; palier 4 = 171 sur 405 (42 %), 8,5 vivants ; palier 9 = 26 sur 26 (100 %), 10 vivants. Le verdict du palier 4 donne 4 succes complets sur 8. Le verdict du monde vide donne 20 sur 20 a 3 charges sur 3. Parametres lus dans le code : garnison 4 / 6 / 7 / 8 / 4, pieces servies 1 / 1 / 2 / 2 / 0, reserves 1 / 1 / 2 / 2 / 0, delai de la reserve 180 / 120 / 75 / 45 / 9999 s, competence 0,40 / 0,47 / 0,55 / 0,55 / 0,40 pour les paliers 0 a 4.

**Sources.** code /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/30_opfor.sqf lignes 25-58 ; /mnt/data/hmt/depot/verdicts/palier4-gagne-une-fois-sur-deux.md ; /mnt/data/hmt/depot/verdicts/socle-posable-monde-vide.md ; /mnt/data/hmt/depot/verdicts/compromission-charniere.md ; /mnt/data/hmt/depot/catalogue/episodes.csv ; commits cd90f8d et b61f86f

**Reste ouvert.** Les trois taux agreges melangent des configurations tres differentes du cote bleu, socle et tactiques compris : ils disent le sens, pas l amplitude a configuration fixe. Les paliers 1, 2 et 3 sont declares dans le code mais aucun episode du catalogue ne les joue.

### Ce que ce lecteur n'a PAS pu établir

Ce que je n ai PAS pu etablir.

1. Verdicts inexistants. Il n y a aucun fichier de verdict pour mg_assaut, delai_porteur, appui_fixe, tenir, ni pour l oracle complet (ORACLE = 2). Je l ai verifie de deux facons : la liste de /mnt/data/hmt/depot/verdicts/ (57 fichiers) et la table « Verdicts vivants » de /mnt/data/hmt/depot/ETAT.md, regeneree le 2026-09-12 a 20:41. Ces cinq leviers ont donc des chiffres et pas de decision.

2. Criteres non pre-inscrits. Pour les leviers de la campagne du 11/09 (V5 mitrailleuse, V6 delai, V7 et V9 appui fixe, V8 tenir), le champ « note » des job.json porte une question et un chiffre a lire, mais pas de seuil de reussite ni d echec, sauf pour V8 et V9 qui portent une phrase de refutation. Seuls l oracle (1 et 2) et le feu avant ont un critere chiffre ecrit avant le run.

3. Valeurs de Fisher. Les probabilites que je cite pour mg_assaut, delai_porteur, appui_fixe, tenir et l oracle complet sont calculees par moi, unilaterales, apres coup, et sur des effectifs de 6 a 18 episodes. Elles ne sont pas pre-inscrites et ne valent pas decision. Celles de l oracle a l assaut (0,41) et du feu avant (0,17) sont, elles, citees depuis les fichiers de verdict.

4. Attribution des leviers du 09/09. Les episodes du 09/09 ne portent pas accessible, effectif, feu_avant ni appui_feu dans leur ligne CHACAL|FINI : ces colonnes ne sont journalisees qu a partir du correctif du 10/09. Pour ces episodes, l attribution repose sur job.json, pas sur le journal de l episode lui-meme. Le catalogue le reflete : la colonne effectif ne contient AUCUNE valeur 20 sur 513 episodes, alors que deux episodes a vingt hommes existent bien.

5. Episodes non certifies comptes dans mg_assaut. Le chiffre de 5 sur 10 pour mg_assaut inclut 4 episodes issus d un dossier de run partage le 11/09 (colonne contamine = 1, aucune porte de lecture). Sur les seuls episodes certifies, mg_assaut vaut 4 sur 6.

6. Oracle complet, mecanisme non verifie par moi. Le job demande de lire d abord la ligne du choix d ouverture, pour savoir si les comptes de gardes par porte different. Je n ai pas trouve cette ligne sous le nom « choix_ouverture » dans les journaux et je n ai pas cherche plus loin. Je ne peux donc pas confirmer que l oracle 2 a reellement change la porte choisie ; je rapporte seulement l issue.

7. Chiffres demandes par les jobs et non extraits. Le nombre de porteurs tues a la tour (mg_assaut), les metres parcourus par les tireurs d appui (appui_fixe) et les coups par tireur (tenir) sont demandes dans les notes de job. Je ne les ai pas mesures.

8. Rejeu a vingt hommes. Le correctif du seuil d exfiltration est bien applique dans le code actuel (60_phases.sqf lignes 1406 a 1409), mais aucun episode a effectif 20 n a tourne depuis le 2026-09-09. La question « vingt hommes gagnent-ils » n a donc aucune mesure valide.

9. Runs en cours. Sept jobs dates du 2026-09-12 a 23:35 (runs 2026-09-12_2335*_chacal_i1 a i7) n ont encore aucune ligne FINI. Je ne les ai pas comptes et je n y ai pas touche.

---

## Le socle d'exécution, les tactiques, l'ablation

### [ETABLI] Ce qu'est le socle d'exécution CHACAL_SOCLE

*2026-09-12*

Le socle n'est pas une tactique, c'est un paquet de cinq réparations d'exécution posées sous toutes les tactiques. S1 : chaque homme de l'assaut porte une charge, avec une relève écrite d'avance (DEMO_1, DEMO_2, ADJOINT, CHEF, MEDECIN). S3 : l'appui est cloué, feu libre mais PATH et LAMBS coupés, il ne peut plus partir au contact. S4 : les porteurs ne combattent pas, AUTOCOMBAT et LAMBS coupés, ils marchent et posent. S4bis : un chien de garde relance l'ordre quand l'assaut n'avance plus de 5 m en 30 s, puis pose un fumigène au deuxième échec. S5 : un défenseur qui TIRE est révélé à l'appui, il s'est trahi lui-même, ce n'est pas un oracle. Le levier est un booléen unique CHACAL_SOCLE (0 = comportement d'origine, 1 = socle), déposé le 12/09 à 03h49.

**Mesures.** Levier binaire CHACAL_SOCLE {0,1}. Témoins d'exécution dans le journal : relances du chien de garde et fumigènes. Sur les 10 épisodes du premier bras socle : 56 relances et 23 fumigènes, contre 0 et 0 pour le script d'origine joué la même nuit.

**Sources.** /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/00_socle.sqf ; /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/60_phases.sqf ; /mnt/data/hmt/depot/bancs/chacal/mission.Altis/description.ext ; /mnt/data/hmt/depot/correctifs/patch_tactiques.py ; commit e1807b8 (2026-09-12 03:49)

**Reste ouvert.** La pièce S3 (appui cloué) a été mesurée inerte le 12/09 après-midi : voir l'entrée sur le contrôle positif de l'appui. Le socle a donc au plus quatre pièces utiles sur cinq.

### [ETABLI] Contrôle positif S0 : les trois charges sont posables en monde vide

*2026-09-12*

Avant de mesurer une tactique, il fallait savoir si l'acte est seulement faisable. Le palier 9 retire tous les défenseurs et ne laisse que la géométrie. Les trois charges sont posées dans les 20 épisodes sur 20, tour comprise, alors que la grande tour manquait une fois sur trois au palier 4. Aucune cause ELEMENT_N_ARRIVE_PAS ni PORTEUR_N_ARRIVE_PAS n'apparaît. Les échecs du palier 4 ne sont donc pas de la géométrie : ils sont tactiques, ou des pannes d'exécution sous le feu.

**Mesures.** 20/20 épisodes à 3 charges sur 3 (100 %), pertes moyennes 0,00 homme. Graines 7 et 8, 2 épisodes par graine sur 5 instances. Vignette d'assaut : départ phase 5, arrêt phase 5.

**Sources.** /mnt/data/hmt/depot/verdicts/socle-posable-monde-vide.md ; runs /mnt/data/hmt/runs/2026-09-12_0221*_chacal_i1 à i5

**Reste ouvert.** Ce contrôle ne dit rien de la pose SOUS LE FEU. C'est exactement ce que le tournoi devait mesurer.

### [CORRIGE] Le socle contre le script d'origine : le 10/10 n'a pas tenu

*2026-09-12*

Le verdict écrit le 12/09 à 07h03 annonce « socle seul 10 sur 10 contre 1 sur 10 pour le script d'origine ». Ce chiffre est celui d'un seul job de 10 épisodes, le premier des deux prévus. Le second job du même bras, joué quatre heures plus tard sur les mêmes graines, rend 6 sur 10. Le bras socle seul du tournoi vaut donc 16 sur 20, pas 10 sur 10. Deux jobs de confirmation ajoutent 15 sur 20, et le témoin haut de l'ablation, même levier, rend 11 sur 20 seulement. L'écart avec le script d'origine survit, mais il passe de 100 % à environ 70 %, et le titre du verdict reste faux tel qu'il est écrit.

**Mesures.** Script d'origine (REF, socle=0, tactique=0) : 1/10 = 10 %. Socle seul, job 1 : 10/10 = 100 %. Socle seul, job 2 : 6/10 = 60 %. Bras socle seul du tournoi : 16/20 = 80 %. Confirmation : 6/10 puis 9/10, soit 15/20 = 75 %. Témoin A0 de l'ablation : 11/20 = 55 %. Cumul des trois campagnes à socle seul : 42/60 = 70 %. Fisher unilatéral : 10/10 contre 1/10 donne p = 0,00006 ; 16/20 contre 1/10 donne p = 0,00041 ; 11/20 contre 1/10 donne p = 0,021. Le critère écrit d'avance dans le job de confirmation était « rester au-dessus de 24/30 » : le compte visé fait 25/30, il passe de justesse.

**Sources.** /mnt/data/hmt/depot/verdicts/socle-execution-10-sur-10.md ; runs /mnt/data/hmt/runs/2026-09-12_034940_chacal_i1 (REF), 035040_chacal_i2 (10/10), 070710_chacal_i7 (6/10), 070409_chacal_i1 et 070509_chacal_i2 (confirmation), 113201_chacal_i1 et 113302_chacal_i2 (A0)

**Reste ouvert.** Le fichier de verdict n'a jamais été amendé. Son champ « remplace_par » est vide et aucun verdict postérieur n'existe dans /mnt/data/hmt/depot/verdicts/ : le dernier fichier du dossier date du 12/09 à 07h03.

### [INVALIDE] Les pertes annoncées par le verdict reposent sur un compteur contredit par l'autre

*2026-09-12*

Le verdict annonce « pertes 1,3 contre 2,5 hommes par épisode ». Ce chiffre vient du champ vivants de la ligne FINI : 10 moins 8,70 vaut 1,30 pour le socle, 10 moins 7,50 vaut 2,50 pour la référence. La même ligne FINI porte un second champ, pertes_est, qui vaut 2,90 pour le socle ET 2,90 pour la référence, soit aucun écart. Les deux compteurs se contredisent épisode par épisode : le run 035040 g7_r2 déclare vivants=10 et pertes_est=3 dans la même ligne. Tant que l'un des deux n'est pas déclaré faux, l'affirmation sur les pertes n'est pas établie.

**Mesures.** Référence : vivants moyens 7,50, pertes_est moyen 2,90 (n=10). Socle seul, premier job : vivants moyens 8,70, pertes_est moyen 2,90 (n=10). Effectif déclaré 10 dans les deux bras.

**Sources.** /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/70_verdict.sqf ; runs /mnt/data/hmt/runs/2026-09-12_034940_chacal_i1 et 2026-09-12_035040_chacal_i2 (fichiers g*_r*/serveur.rpt)

**Reste ouvert.** Je n'ai pas trouvé la définition de pertes_est dans 70_verdict.sqf, donc je ne peux pas dire lequel des deux compteurs est le bon.

### [INVALIDE] Le tournoi de tactiques CHACAL_TACTIQUE : T1, T2, T5

*2026-09-12*

Trois tactiques ont été posées SUR le socle, chacune sous la même valeur du paramètre CHACAL_TACTIQUE. T1 base de feu : l'appui cloué arrose le défenseur connu le plus loin de l'assaut, réitère toutes les 30 s, et l'assaut ne part qu'après le premier coup de l'appui. T2 neutralisation préalable : l'appui tue les défenseurs un par un, le fusilier-mitrailleur d'abord, 60 s par cible, l'assaut n'entre qu'à un défenseur restant ou après 8 min ; l'oracle est assumé dans ce bras, c'est lui qui donne les cibles. T5 infiltration silencieuse : personne ne tire tant que rien ne nous tire dessus, bascule en T1 à la première balle. Toutes les trois font moins bien que le socle seul, et le verdict en tire « attendre coûte ». Ce tournoi est invalidé le même jour : T1 et T2 pilotent un appui dont le contrôle positif montrera qu'il ne tire pas.

**Mesures.** Socle seul : 16/20 = 80 %. T1 base de feu : 7/10 puis 4/10, soit 11/20 = 55 %. T2 neutralisation préalable : 7/10 puis 5/10, soit 12/20 = 60 %. T5 infiltration : 2/10 = 20 %, un seul job au lieu des deux prévus. T1 corrigé (tir de zone quand aucun défenseur n'est localisé) : 7/10 = 70 %. Après les portes de lecture : socle 14/18, T1 9/18, T2 11/19, T5 2/10. Aucune tactique ne bat le socle seul (Fisher unilatéral p ≥ 0,96 dans les trois cas).

**Sources.** /mnt/data/hmt/depot/correctifs/patch_tactiques.py ; /mnt/data/hmt/depot/correctifs/patch_t1.py ; runs /mnt/data/hmt/runs/2026-09-12_035110_chacal_i3 et 035241_chacal_i6 (T1), 035140_chacal_i4 et 035311_chacal_i7 (T2), 035211_chacal_i5 (T5), 070640_chacal_i6 (T1 corrigé) ; commits e1807b8 et b3f13ad

**Reste ouvert.** T5 n'a reçu que 10 épisodes sur les 20 prévus ; aucun job B5-2 n'existe dans /mnt/data/hmt/runs/. Le tournoi d'appui est déclaré à refaire par le correctif du 12/09 14h37, mais il n'a pas été rejoué.

### [ETABLI] Le contrôle positif de l'appui : la pièce S3 rend l'appui muet

*2026-09-12*

Quatre mesures depuis le 10/09 avaient constaté le même appui inerte sous quatre noms différents. La règle 16 exige de certifier l'instrument avant d'empiler une cinquième mesure. Le banc laisse l'appui à la position que la mission lui donne, lui révèle les quatre défenseurs, l'oriente vers eux, et compte ses coups pendant 300 s. Deux bras seulement : cloué comme dans le socle, ou non cloué. L'appui cloué tire dans 1 épisode sur 20 ; l'appui non cloué tire dans 18 épisodes sur 20. Le critère écrit d'avance était « l'appui tire dans au moins 18 épisodes sur 20 », avec un seuil de refus explicite : « sous 10 sur 20, le socle n'a que trois pièces et tout le tournoi des tactiques d'appui est à refaire ». Le bras cloué fait 1 sur 20 : la pièce S3 du socle est réfutée, et avec elle la lecture de T1 et T2.

**Mesures.** Appui cloué : 1/20 épisodes avec un coup, 6 coups au total, 0 défenseur tué. Appui non cloué : 18/20 épisodes avec un coup, 370 coups, 27 défenseurs tués. Fisher unilatéral p < 0,00001. Dans les DEUX bras, le journal par tireur donne defenseurs_vus = 0 sur 4 depuis la position de tir. Cause nommée le soir même : l'IA d'Arma cesse d'engager au-delà de 600 m, alors que l'appui était posté à 500 ou 779 m.

**Sources.** /mnt/data/hmt/depot/correctifs/patch_banc_appui.py ; commit bdc52a4 (2026-09-12 14:37) ; runs /mnt/data/hmt/runs/2026-09-12_143803_chacal_i1 et 143904_chacal_i2 (cloué), 143934_chacal_i3 et 144004_chacal_i4 (non cloué) ; note du job /mnt/data/hmt/runs/2026-09-12_233559_chacal_i1/job.json

**Reste ouvert.** Aucun fichier de verdict n'a été écrit pour ce banc. Le tournoi des tactiques d'appui, déclaré à refaire, n'a pas été rejoué. Le placeur d'appui qui devait réparer la cause rend encore 0 coup avec une couverture mesurée de 0,541 du plancher du site.

### [INVALIDE] L'ablation par retrait CHACAL_ABLATION, et la version par ajout jetée

*2026-09-12*

Une première version de l'ablation procédait par AJOUT : activer une pièce du socle à la fois. Quatre relecteurs l'ont refusée pour une raison chiffrable : quatre hommes sur cinq portent déjà une charge dans la dotation d'origine, donc le bras « S1 seul » ne faisait varier presque rien. La version retenue procède par RETRAIT : le socle complet est en place et on enlève une pièce à la fois, CHACAL_ABLATION étant un masque de bits (1 sans chien de garde, 2 sans porteurs non combattants, 4 sans appui cloué, 8 sans révélation par le tir). Aucun bras ne se sépare du témoin A0 joué la même nuit. Pire, le témoin haut lui-même tombe à 11/20 alors que le même levier valait 16/20 et 15/20 les heures précédentes. L'ablation ne désigne donc aucune pièce indispensable, et le retrait de l'appui cloué fait même légèrement mieux que le socle complet, ce que le banc d'appui expliquera l'après-midi.

**Mesures.** A0 socle complet : 11/20 = 55 %. A1 sans chien de garde : 13/20 = 65 %. A2 sans porteurs non combattants : 9/20 = 45 %. A4 sans appui cloué : 13/20 = 65 %. A8 sans révélation par le tir : 11/20 = 55 %. Fisher unilatéral contre A0 : A1 p = 0,37, A2 p = 0,83, A4 p = 0,37, A8 p = 0,62. Contrôle d'exécution du levier : le bras A1 journalise 0 relance et 0 fumigène, contre 116 relances et 43 fumigènes pour A0, donc le retrait a bien eu lieu. Le chiffre « 29 réussites sur 37 » cité dans les notes de job pour le socle complet n'est pas reproductible aujourd'hui : je retrouve 31/40 brut et 25/34 après les portes de lecture.

**Sources.** /mnt/data/hmt/depot/correctifs/patch_ablation2.py (en-tête, lignes 4 à 15) ; commit 65597e4 (2026-09-12 11:31) ; /mnt/data/hmt/depot/bancs/chacal/mission.Altis/description.ext (classe CHACAL_ABLATION) ; runs /mnt/data/hmt/runs/2026-09-12_113201 à 113533_chacal_i1 à i7, 125559_chacal_i1, 130559_chacal_i2, 131559_chacal_i3 ; /mnt/data/hmt/archive/ablation_recompte.csv

**Reste ouvert.** Aucun verdict n'a été écrit pour l'ablation. Le fichier patch_ablation.py de la première version n'existe nulle part dans le dépôt ni dans l'historique git : seule la trace écrite de son refus subsiste. Je n'ai pas trouvé le rapport des quatre relecteurs.

### [CORRIGE] La fuite de journal : la porte de lecture censurait dans un seul sens

*2026-09-12*

Les boucles du socle (tactique, chien de garde, relance) dorment 5 à 10 secondes. Quand l'épisode se ferme pendant ce sommeil, elles écrivent APRÈS la ligne FINI. La porte de lecture rien_apres_fini refuse alors l'épisode entier. Sur les 96 épisodes de l'ablation qui avaient été relus, 17 sont refusés, dont 10 qui avaient posé leurs trois charges : la censure allait donc dans un seul sens, elle retirait surtout des réussites. Le remède est de re-tester CHACAL_FIN après chaque sommeil avant d'écrire quoi que ce soit. Tous les taux de l'ablation existent donc en deux versions, brute et après portes, et l'écart est important sur le bras A8.

**Mesures.** 17 épisodes refusés sur 96, dont 10 avec 3 charges sur 3. Effet sur les bras : A0 11/20 brut contre 10/18 après portes ; A2 9/20 contre 7/17 ; A4 13/20 contre 11/16 ; A8 11/20 contre 6/11, avec 9 épisodes refusés dont 5 réussites. Le bras A1, qui n'a pas de chien de garde, n'a aucun épisode refusé : 13/20 dans les deux lectures. Le socle seul de la confirmation perd ses 4 épisodes refusés, tous des réussites : 15/20 brut contre 11/16 après portes.

**Sources.** /mnt/data/hmt/depot/correctifs/patch_banc_appui.py (points 1, lignes 4 à 8) ; /mnt/data/hmt/depot/bancs/chacal/lire.py ligne 134 ; /mnt/data/hmt/archive/ablation_recompte.csv (colonnes verdict et apres_fini) ; commit bdc52a4

**Reste ouvert.** Le correctif n'a pas été appliqué rétroactivement : les campagnes du tournoi, de la confirmation et de l'ablation restent lues avec le biais. Aucune des deux lectures n'a été déclarée la bonne dans un verdict.

### [ETABLI] Toutes ces mesures sont des vignettes d'assaut : la victoire y était impossible

*2026-09-12*

Le socle, le tournoi et l'ablation ont tous été joués avec arrêt = 5, c'est-à-dire que la phase 6 d'exfiltration n'est jamais jouée. Le compteur d'exfiltrés vaut donc 0 par construction, et l'issue SUCCÈS est structurellement inatteignable. Chaque épisode de ces campagnes se termine en ECHEC, avec pour cause CHARGES_INCOMPLETES ou EXFIL_MANQUEE. Le seul critère réellement mesuré est « 3 charges posées sur 3 », et c'est ce que tous les taux de ce domaine comptent. Le recompte montre en plus que poser trois charges ne veut pas dire détruire trois objectifs : 13 épisodes de l'ablation déclarent 3 posées et 0 détruites.

**Mesures.** 487 dossiers d'épisode à arrêt = 5 dans les runs chacal du 10 au 12/09, contre 23 à arrêt = 6. 17 épisodes seulement, sur les 481 lus de cette fenêtre, déclarent exfiltrés > 0. Dans les 230 épisodes des campagnes tournoi, confirmation et ablation, l'issue est ECHEC dans 100 % des cas et exfiltrés vaut 0. Charges posées sans destruction, par bras d'ablation : A0 1, A1 5, A2 1, A4 3, A8 3.

**Sources.** /mnt/data/hmt/depot/bancs/chacal/mission.Altis/description.ext (classe CHACAL_ARRET) ; /mnt/data/hmt/runs/2026-09-12_233559_chacal_i1/job.json (note de la campagne VICTOIRE-BOUT-EN-BOUT-12-09) ; /mnt/data/hmt/archive/ablation_recompte.csv (colonnes posees et detruites)

**Reste ouvert.** La campagne VICTOIRE-BOUT-EN-BOUT-12-09, lancée le 12/09 à 23h35 avec départ = 1 et arrêt = 6, tournait encore quand j'ai lu. Aucun de ses épisodes n'a de ligne FINI : le résultat n'existe pas encore.

### Ce que ce lecteur n'a PAS pu établir

Ce que je n'ai PAS pu établir. 1) Le chiffre « 29 réussites sur 37 » cité dans toutes les notes de job de l'ablation pour le socle complet : je ne le reproduis pas. Les deux comptes reproductibles aujourd'hui sont 31/40 brut et 25/34 après les portes de lecture, sur les runs 035040_i2, 070710_i7, 070409_i1 et 070509_i2. L'écart s'explique probablement par un comptage fait à 11h31 alors que des épisodes n'étaient pas encore relus, mais je n'ai aucune trace écrite qui le prouve. 2) La première version de l'ablation, « par ajout » : aucun fichier patch_ablation.py n'existe dans /mnt/data/hmt/depot/correctifs/ ni dans l'historique git (git log --all sur ce chemin ne donne rien). La seule trace de son existence et de son refus est l'en-tête de patch_ablation2.py. Je n'ai pas retrouvé le rapport des quatre relecteurs ni leurs noms : aucun document contenant « relecteur » n'existe dans /mnt/data/hmt en dehors de deux fichiers de correctif. 3) Aucun fichier de verdict n'a été écrit pour le tournoi complet à 20 épisodes, pour l'ablation, ni pour le contrôle positif de l'appui. Le dossier /mnt/data/hmt/depot/verdicts/ s'arrête à socle-execution-10-sur-10.md, daté du 12/09 à 07h03, et son champ « remplace_par » est vide. Le titre « 10 sur 10 » n'est donc formellement rétracté nulle part, alors que la mesure ne tient pas. 4) La définition du champ pertes_est : je ne l'ai pas trouvée dans 70_verdict.sqf, donc je ne peux pas dire lequel des deux compteurs de pertes est juste. 5) Le résultat de la campagne VICTOIRE-BOUT-EN-BOUT-12-09 (7 instances, lancée à 23h35) n'existe pas encore : aucun de ses épisodes n'a de ligne FINI. Je n'ai touché à aucun processus. 6) Le contrôle positif de l'appui identifie un appui muet quand il est cloué, mais je n'ai pas mesuré ce que vaut le socle une fois S3 retiré et le reste conservé sur un nombre d'épisodes suffisant : le bras A4 de l'ablation (13/20) est le seul élément et il ne sépare pas de A0 (p = 0,37).

---

## Quelles phases ont réellement été jouées

### [ETABLI] Le corpus du 10 au 12 septembre est une vignette de deux phases sur six

*2026-09-10 au 2026-09-12*

J ai lu les 87 job.json des runs datés du 10 au 12 septembre et les 515 RPT qu ils contiennent. 509 épisodes ont écrit une ligne CHACAL|FINI, donc 509 épisodes sont exploitables. Le champ arret vaut 5 dans 474 d entre eux, soit 93,1 % du corpus. Un arret à 5 signifie que la mission se ferme à la fin de la phase 5 : les phases 1, 2, 3 et 6 ne sont pas jouées. Le champ depart vaut 5 dans 467 épisodes, ce qui supprime aussi tout ce qui précède la mise en place. Autrement dit, la très grande majorité des mesures récentes ne porte que sur MISE_EN_PLACE puis ASSAUT.

**Mesures.** 509 épisodes terminés (515 RPT lus, 6 sans ligne FINI). Par arret : arret=5 → 474 épisodes (93,1 %) ; arret=6 → 23 épisodes (4,5 %) ; arret=4 → 12 épisodes (2,4 %). Par banc : chacal 489, alize1 20. 87 dossiers de run portent un job.json, aucun n en manque.

**Sources.** /mnt/data/hmt/runs/2026-09-1[012]_* (job.json, champs depart et arret) ; /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/60_phases.sqf lignes 55-66 (fnc_finPhase pose CHACAL_FIN quand _n >= CHACAL_ARRET) ; exemple lisible : /mnt/data/hmt/runs/2026-09-12_143803_chacal_i1/job.json et /mnt/data/hmt/runs/2026-09-12_143803_chacal_i1/run.log (commit=bdc52a4)

**Reste ouvert.** Je n ai pas vérifié si la porte de lecture (lire.py) avait rejeté certains épisodes au-delà des 6 RPT sans ligne FINI ; le run.log affiche verdict ACCEPTE mais je n ai pas recompté les refus.

### [ETABLI] Compte exact de chaque phase jouée sur la période

*2026-09-10 au 2026-09-12*

J ai compté toutes les lignes CHACAL|PH|n|NOM|debut et |fin de tous les RPT de la période. Aucune phase n est à zéro absolu sur les trois jours, mais quatre des six phases sont marginales. La phase 4 est jouée 512 fois et la phase 5 jouée 498 fois. Les phases 1 et 2 ne sont jouées que 18 fois chacune, la phase 3 43 fois, la phase 6 23 fois. Les phases d ouverture et de sortie de mission représentent donc moins de 5 % du corpus.

**Mesures.** PH1 INSERTION : 18 débuts, 18 fins, 18 ATTEINT (100 %). PH2 APPROCHE : 18 débuts, 18 fins, 11 ATTEINT (61,1 %), 7 ENLISE. PH3 OBSERVATION : 43 débuts, 43 fins, 0 ATTEINT (0 %), 43 RENSEIGNEMENT_PAUVRE. PH4 MISE_EN_PLACE : 512 débuts, 512 fins, 503 ATTEINT (98,2 %), 9 COMPROMIS. PH5 ASSAUT : 498 débuts, 495 fins, 212 ATTEINT (42,8 %), 189 INCOMPLET, 85 BANC_APPUI, 6 ARTICULATION_ROMPUE, 3 PLAFOND. PH6 EXFILTRATION : 23 débuts, 23 fins, 11 ATTEINT (47,8 %), 12 PLAFOND.

**Sources.** Toutes les lignes CHACAL|PH des RPT sous /mnt/data/hmt/runs/2026-09-1[012]_*/**/serveur.rpt ; émission des lignes : /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/60_phases.sqf lignes 49 et 56 ; catalogue des six phases : mêmes fichiers lignes 558, 672, 766, 869, 996, 1383

**Reste ouvert.** L écart entre 512 fins de PH4 et 509 épisodes vient de 3 RPT (runs PLACEUR-HAUTEUR) qui ont journalisé la phase 4 sans jamais écrire de ligne FINI. Je n ai pas cherché pourquoi ces serveurs se sont arrêtés.

### [ETABLI] Dans les campagnes nommées du 11 et 12 septembre, quatre phases sur six sont à zéro

*2026-09-11 au 2026-09-12*

La question demandait quelles phases n ont jamais été jouées. Sur les trois jours entiers, aucune phase n est à zéro strict. Mais si l on se restreint aux campagnes qui portent les verdicts récents, la réponse change. Dans les 467 épisodes à depart=5 et arret=5, la phase 1 est jouée 0 fois, la phase 2 0 fois, la phase 6 0 fois, et la phase 3 exactement 1 fois. Toutes les campagnes ORACLE, TOURNOI-TACTIQUES, ABLATION, BANC-APPUI, PLACEUR, S0-CONTROLE-POSITIF, SONDE et ALIZE-1 sont dans ce cas. Ces campagnes ne mesurent donc rien de l insertion, de l approche, de l observation ni de l exfiltration.

**Mesures.** Épisodes à depart=5/arret=5 : 467 (447 chacal + 20 alize1). PH1 = 0, PH2 = 0, PH6 = 0, PH3 = 1 (un seul épisode, G8-FABLE V5). Effectifs par campagne : ABLATION-12-09 100 épisodes, TOURNOI-TACTIQUES-12-09 80, BANC-APPUI-12-09 40, PLACEUR-* 40, ORACLE-11-09 30, ORACLE-COMPLET-11-09 30, SOCLE-CONFIRMATION B0+B1c 30, S0-CONTROLE-POSITIF 20, ALIZE-1 20, SONDE-12-09 3. Toutes n ont que PH4 et PH5 dans leurs RPT. Les 12 épisodes à arret=4 (G8-FABLE V7 et V9) n ont même pas joué la phase 5.

**Sources.** /mnt/data/hmt/runs/2026-09-11_1648* à _1651* (ORACLE), _1820* à _1823* (ORACLE-COMPLET), /mnt/data/hmt/runs/2026-09-12_03* (TOURNOI), _1132* à _1315* (ABLATION), _1438* à _1440* (BANC-APPUI), _1628* à _1756* (PLACEUR), _0221* à _0223* (S0), /mnt/data/hmt/runs/2026-09-11_142934_alize1_i6 et _143019_alize1_i7

**Reste ouvert.** Je n ai pas vérifié si les auteurs de ces campagnes avaient l intention explicite de mesurer autre chose que l assaut ; la note des job.json le suggère mais je n ai lu que quelques notes.

### [ETABLI] Une issue SUCCES était structurellement inatteignable dans 95,5 % des épisodes

*2026-09-10 au 2026-09-12*

Le verdict de la mission n accorde SUCCES que si toutes les charges sont posées ET si au moins 0,6 x effectif hommes sont exfiltrés. Le compteur d exfiltrés n est écrit qu à un seul endroit du code, dans la phase 6. Or la phase 6 commence par un garde qui la coupe net si la vignette est déjà fermée. Avec arret=5 ou arret=4, la phase 6 ne s exécute jamais, le compteur reste nul, et la branche SUCCES est fausse par construction. Ce n est pas une propriété du hasard : c est une conséquence du code, vérifiable ligne par ligne. 486 épisodes sur 509 sont dans ce cas.

**Mesures.** 486 épisodes sur 509 (95,5 %) avaient SUCCES inatteignable : 474 à arret=5 et 12 à arret=4. Contrôle direct dans les RPT : le champ exfiltres vaut 0 dans les 472 épisodes à arret=5 qui portent ce champ, et 0 dans les 14 épisodes à arret=4. Aucune exception. À arret=6, exfiltres vaut 2, 3, 5 ou 6 selon l épisode. Seuil requis à 10 hommes : round(0,6 x 10) = 6.

**Sources.** /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/70_verdict.sqf ligne 172 (_exf = 0 si CHACAL_EXFILTRES est nil) et ligne 188 (if (_actes >= _objTotal && _exf >= (round (0.6 * CHACAL_EFFECTIF))) then SUCCES) ; /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/60_phases.sqf ligne 1380 (if (CHACAL_FIN) exitWith) et ligne 1408 (seule affectation de CHACAL_EXFILTRES)

**Reste ouvert.** Rien sur ce point : la chaîne est complète et fermée.

### [ETABLI] 204 épisodes étiquetés ECHEC / EXFIL_MANQUEE sont en réalité des assauts réussis

*2026-09-10 au 2026-09-12*

Quand arret=5, la mission qui a posé les trois charges tombe dans la branche par défaut du verdict. Comme le compteur d exfiltrés est à zéro, la cause écrite est EXFIL_MANQUEE. Le mot dit qu une exfiltration a échoué, alors qu elle n a jamais été programmée. J ai croisé l issue de la phase 5 et la cause finale : les 204 épisodes ECHEC/EXFIL_MANQUEE à arret=5 ont tous une phase 5 ATTEINT, c est-à-dire 3 charges sur 3. Lire le taux de SUCCES des RPT comme un taux de réussite tactique sous-compte donc massivement ce qui a été accompli.

**Mesures.** Issues finales sur 509 épisodes : ECHEC 497, SUCCES 6, ABANDON 6. Causes : CHARGES_INCOMPLETES 291, EXFIL_MANQUEE 206, CHARGES_ET_EXFIL 6, ARTICULATION_ROMPUE 6. Croisement à arret=5 : PH5=ATTEINT → ECHEC/EXFIL_MANQUEE 204 sur 204 ; PH5=INCOMPLET → ECHEC/CHARGES_INCOMPLETES 180 ; PH5=BANC_APPUI → ECHEC/CHARGES_INCOMPLETES 85 ; PH5=PLAFOND → ECHEC/CHARGES_INCOMPLETES 3.

**Sources.** /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/70_verdict.sqf lignes 189-192 (branche ECHEC, cause EXFIL_MANQUEE quand _actes >= _objTotal) ; lignes CHACAL|FINI de /mnt/data/hmt/runs/2026-09-1[012]_*/**/serveur.rpt

**Reste ouvert.** Je n ai pas vérifié si un outil d agrégation (catalogue.py, lire.py) corrige déjà cette étiquette avant de produire les tableaux lus par les verdicts.

### [ETABLI] Le verdict socle 10/10 du 12 septembre repose sur une vignette de deux phases

*2026-09-12*

Le verdict socle-execution-10-sur-10.md annonce que le socle fait passer l assaut de 1 à 10 réussites sur 10. J ai retrouvé les runs sources et lu leurs job.json. Ils sont tous à depart=5 et arret=5. La réussite mesurée est l issue ATTEINT de la phase 5, qui vaut exactement 3 charges posées sur 3. Le chiffre est juste et je le confirme épisode par épisode. Mais il porte sur l assaut seul, pas sur la mission : ni insertion, ni approche, ni observation, ni exfiltration n ont été jouées dans ces runs. Le verdict le dit lui-même dans sa dernière ligne, et c est cohérent.

**Mesures.** 2026-09-12_034940_chacal_i1 (version REF) : PH5 ATTEINT 1, INCOMPLET 9 ; charges 3/3 dans 1 épisode sur 10. 2026-09-12_035040_chacal_i2 (version B0, socle) : PH5 ATTEINT 10 sur 10 ; charges 3/3 dans 10 épisodes sur 10. Les deux runs sont à depart=5, arret=5. Les cinq autres runs du lot : B1 7/10 puis 4/10, B2 7/10 puis 5/10, B5 2/10. Toutes phases 1, 2, 3 et 6 absentes des sept RPT.

**Sources.** /mnt/data/hmt/depot/verdicts/socle-execution-10-sur-10.md ; /mnt/data/hmt/runs/2026-09-12_034940_chacal_i1 à /mnt/data/hmt/runs/2026-09-12_035311_chacal_i7 (job.json et serveur.rpt) ; critère de la phase 5 : /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/60_phases.sqf lignes 1363-1368 ; commit cité par le verdict : e1807b8

**Reste ouvert.** Je n ai pas recalculé le test de Fisher annoncé (p = 0,0001) ni les pertes moyennes de 1,3 contre 2,5 hommes.

### [ETABLI] 85 épisodes n ont pas joué d assaut du tout

*2026-09-12*

Les campagnes BANC-APPUI, PLACEUR et SONDE utilisent un levier banc_appui qui remplace l assaut par une mesure de tir d appui. Dans ces épisodes la phase 5 s ouvre puis se ferme immédiatement avec l issue BANC_APPUI. Aucune charge n est posée et le verdict final est mécaniquement ECHEC / CHARGES_INCOMPLETES. Ces 85 épisodes ne doivent donc jamais entrer dans un taux de réussite d assaut. Ils représentent 17 % des épisodes de la période et 19 % de tous ceux qui ont ouvert la phase 5.

**Mesures.** 85 épisodes avec PH5 fin = BANC_APPUI : BANC-APPUI-12-09 BA-CLOUE 20, BA-LIBRE 20, PLACEUR-12-09 PL-A 14, PL-B 14, PLACEUR-BALAYAGE PL4-A 3, PL4-B 3, PLACEUR-HAUTEUR PL3-A 2, PL3-B 2, PLACEUR-TEMOIN PL5-A 2, PL5-B 2, SONDE-12-09 3. Tous à depart=5, arret=5. Tous terminent ECHEC / CHARGES_INCOMPLETES, 85 sur 85.

**Sources.** /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/60_phases.sqf ligne 1099 ([5, ASSAUT, BANC_APPUI] call CHACAL_fnc_finPhase) ; /mnt/data/hmt/runs/2026-09-12_143803_chacal_i1/job.json (champ banc_appui = 1, note décrivant le contrôle positif) ; runs 2026-09-12_1438*, _1439*, _1440*, _1628* à _1630*, _1721* à _1723*, _1735* à _1739*, _1755* à _1756*, _181029

**Reste ouvert.** Je n ai pas lu les compteurs tirs_banc de ces épisodes, donc je ne dis rien de ce que le banc d appui a mesuré ni s il a passé son critère de 18 sur 20.

### [ETABLI] La mission complète n a été jouée que 23 fois, et gagnée 6 fois

*2026-09-10 au 2026-09-12*

Seuls 23 épisodes de la période ont arret=6 et jouent donc jusqu à l exfiltration. Ils viennent de cinq runs du 10 septembre et de trois runs MSOCLE du 12 septembre au matin. Sur ces 23 épisodes, 6 se terminent en SUCCES, 6 en ABANDON et 11 en ECHEC. La phase 3 OBSERVATION y échoue 23 fois sur 23 : le détachement n a jamais réuni assez de vues pour valider son renseignement. C est la seule fenêtre où un taux de réussite de mission a un sens sur cette période, et elle est très étroite.

**Mesures.** 23 épisodes à arret=6. Répartition : depart=1 arret=6 → 18 épisodes ; depart=3 arret=6 → 5 épisodes. Issues : SUCCES 6, ABANDON 6, ECHEC 11. Détail depart=1 : PH1 18/18 ATTEINT, PH2 11/18 ATTEINT, PH3 0/18, PH4 12/18 ATTEINT, PH5 8 ATTEINT + 4 INCOMPLET + 6 ARTICULATION_ROMPUE, PH6 10/18 ATTEINT. Détail depart=3 : PH3 0/5, PH4 5/5, PH5 0 ATTEINT sur 5, PH6 1/5 ATTEINT. Les 6 SUCCES viennent de 2026-09-10_0635 (1), 2026-09-10_0645 (1), 2026-09-10_1525 (2), 2026-09-12_070600_i4 (1), 2026-09-12_070610_i5 (1).

**Sources.** /mnt/data/hmt/runs/2026-09-10_0635_chacal, _0645_chacal, _1525_chacal ; /mnt/data/hmt/runs/2026-09-12_070539_chacal_i3, _070600_chacal_i4, _070610_chacal_i5 (campagne SOCLE-CONFIRMATION-12-09, version MSOCLE) ; /mnt/data/hmt/runs/2026-09-11_0918_chacal (G8-FABLE V1, depart=3 arret=6)

**Reste ouvert.** 6 succès sur 23 est un effectif trop petit pour trancher quoi que ce soit, et les 23 épisodes mélangent deux dates, deux versions de code et deux valeurs de depart. Je n ai pas calculé d intervalle de confiance.

### [EN COURS] La mesure de la mission complète était en cours au moment de la lecture

*2026-09-12*

Sept runs ont été lancés le 12 septembre à 23h36 sous la campagne VICTOIRE-BOUT-EN-BOUT-12-09. Six sont en version V6-PLEIN avec depart=3 et arret=6, un en V6-SONDE-DUREE avec depart=1 et arret=6. Ce sont les sept serveurs Arma qui tournaient pendant ma lecture. Aucun n avait encore écrit la moindre ligne CHACAL|FINI. Ils ne contribuent donc à aucun chiffre de ce rapport. C est précisément la mesure qui manquait : socle plus six phases, de l insertion à l exfiltration.

**Mesures.** 7 runs, 0 épisode terminé au moment de la lecture. Versions : V6-PLEIN 6 runs (depart=3, arret=6), V6-SONDE-DUREE 1 run (depart=1, arret=6). Aucun autre run de la période n est sans épisode terminé, hormis 4 RPT incomplets dans les runs PLACEUR-HAUTEUR.

**Sources.** /mnt/data/hmt/runs/2026-09-12_233559_chacal_i1 (V6-SONDE-DUREE) et /mnt/data/hmt/runs/2026-09-12_233601_chacal_i2 à /mnt/data/hmt/runs/2026-09-12_233832_chacal_i7 (V6-PLEIN)

**Reste ouvert.** Tout : je n ai lu ni leur note de prédiction ni leur critère de réussite écrit d avance, et je n ai évidemment pas leurs résultats.

### [ETABLI] La phase 3 OBSERVATION n a jamais réussi sur la période

*2026-09-10 au 2026-09-12*

Chaque fois que la phase OBSERVATION a été jouée, elle s est fermée sur l issue RENSEIGNEMENT_PAUVRE. Jamais une seule fois sur ATTEINT. C est le seul cas de la période où une phase affiche un taux de réussite de zéro pour cent. Le seuil de renseignement n est donc jamais atteint dans le format de mission actuel. Cela concerne 43 épisodes, dont les 23 qui vont jusqu à l exfiltration. Le verdict oracle-savoir-a-l-assaut du 11 septembre note le même fait sous une autre forme : au moment de choisir la porte d entrée, le journal indique renseignement = 0.

**Mesures.** PH3 OBSERVATION : 43 débuts, 43 fins, 0 ATTEINT, 43 RENSEIGNEMENT_PAUVRE. Répartition : depart=1 arret=6 → 18, depart=3 arret=4 → 12, depart=3 arret=5 → 7, depart=3 arret=6 → 5, depart=5 arret=5 → 1.

**Sources.** /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/60_phases.sqf lignes 766 et 861 (issue ATTEINT si count CHACAL_VUES >= CHACAL_SEUIL_RENS) ; /mnt/data/hmt/depot/verdicts/oracle-savoir-a-l-assaut.md (réserve majeure, choix de la porte à l aveugle) ; RPT des runs 2026-09-11_0918, _0919, _100219, _112559, _114559, _124559 et 2026-09-12_07053*, _070600, _070610

**Reste ouvert.** Je n ai pas lu la valeur de CHACAL_SEUIL_RENS ni le nombre de vues réellement obtenu par épisode, donc je ne sais pas de combien le seuil est manqué.

### Ce que ce lecteur n'a PAS pu établir

Ce que je n ai PAS établi.

1. Je n ai pas vérifié la valeur du seuil de renseignement (CHACAL_SEUIL_RENS) ni le nombre de vues obtenu, donc je ne peux pas dire si la phase 3 échoue de peu ou de loin.

2. Je n ai pas recalculé les tests statistiques cités par les verdicts de la période (Fisher p = 0,0001 pour le socle, p = 0,17 pour le feu avant, ~0,4 pour l oracle). J ai seulement confirmé les effectifs bruts.

3. Je n ai pas lu les compteurs tirs_banc des 85 épisodes banc_appui, donc je ne dis rien de ce que le banc d appui a conclu.

4. Je n ai pas établi pourquoi 6 RPT de la période n ont aucune ligne CHACAL|FINI (dont 4 dans les runs PLACEUR-HAUTEUR du 12/09 à 17h21). Serveur arrêté avant la fin, plantage ou coupure : je ne sais pas.

5. Je n ai pas vérifié si les outils d agrégation du dépôt (catalogue.py, lire.py) retraitent l étiquette EXFIL_MANQUEE avant de produire les tableaux qui alimentent les verdicts. Si un verdict a repris cette étiquette telle quelle, il aurait compté 204 assauts réussis comme des échecs ; je n ai trouvé aucun verdict de la période qui le fasse, mais je n ai lu que les six verdicts datés du 10 au 12 septembre.

6. Je n ai pas relu les notes de prédiction (champ note) de tous les job.json, seulement quelques-unes. Il est donc possible que certaines campagnes annoncent explicitement leur périmètre réduit d une façon que je n ai pas reprise.

7. Les 6 SUCCES de la période viennent de 5 runs répartis sur deux dates et deux versions de code. Je n ai pas vérifié que l empreinte de mission était identique entre le 10 et le 12 septembre, donc je ne les traiterais pas comme un seul échantillon.

8. Je n ai touché à rien : aucune écriture, aucun lancement, aucun processus arrêté. Mes scripts de lecture sont déposés dans /mnt/c/Users/Younes/portee_phases_0*.sh et /mnt/c/Users/Younes/portee_lire_*.sh.

---

## L'appui et son placeur

### [ETABLI] Pourquoi un placeur d'appui a été écrit

*2026-09-09 au 2026-09-10*

Le 09/09, au palier 4 le plus léger, l'assaut est anéanti en 38 secondes. L'attribution des morts montre qu'UN seul défenseur tire 36 coups et signe les cinq morts. Le détachement de dix hommes tire UNE balle sur tout l'épisode. L'élément d'appui, deux hommes en place et vivants, tire ZÉRO. La cause est de conception et tient en une ligne du script : CHACAL_POS_APPUI = CHACAL_OP, c'est-à-dire que la position d'appui EST l'observatoire, à 773 m et 183 m plus haut. Le 10/09 à 06h26, un placeur distinct est écrit pour donner à l'appui une position choisie pour TIRER.

**Mesures.** 1 défenseur signe 5 morts ; 36 coups ennemis entre 4959 et 4997 s ; 1 coup tiré par le détachement de 10 hommes ; 0 coup de l'appui ; observatoire à 773 m et +183 m

**Sources.** /mnt/data/hmt/depot/verdicts/plan-de-positions-sans-plan-de-feu.md (run 2026-09-09_1115_chacal, graine 8) ; commit ed3079d du 2026-09-10 06:26 « CHACAL_APPUI_FEU : une position d appui choisie pour tirer, distincte de l observatoire »

**Reste ouvert.** Le verdict dit lui-même qu'il n'établit pas qu'une position d'appui bien choisie suffise à gagner.

### [REFUTE] Placeur version 1 : la vue vers l'ouverture, par tirage au hasard

*2026-09-10*

Le premier placeur cherche sur un arc autour du site. Il exige une portée utile de 160 à 350 m de l'ouverture, une ligne de vue dégagée vers l'ouverture testée par lineIntersectsSurfaces, un azimut décalé de 40 à 120 degrés de l'axe d'assaut, et un terrain où un homme peut se coucher. Il tire 220 positions au hasard dans ce secteur. S'il ne trouve rien, il se replie sur l'observatoire et journalise un avertissement. Ce placeur est resté le défaut (CHACAL_PLACEUR = 0) jusqu'au 12/09. Le 12/09 il est réfuté : ses postes voient l'ouverture mais pas les hommes.

**Mesures.** 220 tirages ; bande 160-350 m ; décalage d'axe 40-120 degrés ; postes effectivement occupés le 12/09 : 186 à 208 m (graine 7) et 275 à 330 m (graine 8) ; couverture du plancher non calculée (champ couverture = -1)

**Sources.** commit ed3079d ; /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/00_socle.sqf (CHACAL_fnc_positionAppui) ; runs 2026-09-12_162822_chacal_i1 et 2026-09-12_162922_chacal_i2 (version PL-A)

**Reste ouvert.** Aucune mesure appariée n'a isolé l'effet de ce placeur sur l'issue de la mission entre le 10 et le 12/09.

### [OUVERT] Le feu de l'appui avant le premier pas de l'assaut

*2026-09-10*

Le 10/09 à 14h43, un second levier est ajouté : les défenseurs sont révélés à l'appui, une cible est désignée, le feu est libre, et l'assaut attend le premier coup. En vignette d'assaut, le bras avec feu préalable pose les trois charges 5 fois sur 10 contre 2 fois sur 10 sans. L'écart va dans le sens attendu mais le test de Fisher unilatéral donne p = 0,17. Deux faits sûrs sortent du run. Sans désignation, l'appui ne connaît aucune cible et ne tire pas avant l'assaut. Avec désignation en mode RED, dans les épisodes où il ne tire pas, les deux tireurs QUITTENT leur position à 11-18 km/h, l'un finissant à 72 m des défenseurs.

**Mesures.** feu_avant 0 = 2/10 (graine 7 : 0/5 ; graine 8 : 2/5) ; feu_avant 1 = 5/10 (graine 7 : 2/5 ; graine 8 : 3/5) ; Fisher unilatéral p = 0,17 ; l'appui tire avant le premier pas dans 7 épisodes sur 10 avec, 0 sur 10 sans

**Sources.** /mnt/data/hmt/depot/verdicts/feu-avant-vignette.md ; commit e8e77ea ; runs 2026-09-10_1505_chacal (VA0) et 2026-09-10_1515_chacal (VA1) ; /mnt/data/hmt/depot/correctifs/patch_feu_avant.py

**Reste ouvert.** Quelle pièce du plan agit reste inconnu : désignation, attente et relance de l'ordre changent ensemble. Le verdict est resté OUVERT et figure encore dans les portes ouvertes de /mnt/data/hmt/depot/ETAT.md.

### [ETABLI] Quatre mesures d'affilée constatent le même appui muet

*2026-09-10 au 2026-09-12*

Entre le 10/09 et le 12/09, quatre campagnes différentes touchent à l'appui sous quatre noms : feu avant, oracle, tournoi des tactiques, ablation. Toutes constatent le même appui inerte. Le compte écrit dans le socle est de 0 coup sur 17 épisodes du socle complet. C'est ce constat répété qui déclenche, le 12/09 à 14h37, la décision de certifier le mécanisme lui-même au lieu d'empiler une cinquième mesure, au titre de la règle 16.

**Mesures.** 0 coup sur 17 épisodes du socle complet ; 4 campagnes concernées

**Sources.** /mnt/data/hmt/depot/bancs/chacal/mission.Altis/chacal/00_socle.sqf, commentaire d'en-tête de CHACAL_fnc_bancAppui ; commit bdc52a4 du 2026-09-12 14:37

**Reste ouvert.** Je n'ai pas recompté moi-même ces 17 épisodes : le chiffre est celui écrit dans le code et le message de commit.

### [ETABLI] Le banc d'appui : combien d'épisodes, combien de coups

*2026-09-12*

Le banc d'appui est un épisode de certification. L'appui reste à SA position, les quatre défenseurs lui sont révélés, il est orienté vers le plus proche, et on compte ses coups pendant 300 secondes. L'assaut et le bouchon sont mis hors jeu. Deux bras tranchent : banc_appui = 1, l'appui est cloué comme dans le socle (PATH coupé et LAMBS désactivé) ; banc_appui = 2, il est libre, RED seulement. Le critère était écrit d'avance : au moins 18 épisodes sur 20 avec un coup. Le bras cloué le manque très largement, le bras libre le passe.

**Mesures.** 118 dossiers d'épisode lancés avec banc_appui non nul, dont 85 portent une ligne banc_appui_fin ; 376 coups au total, tous dans la campagne BANC-APPUI-12-09 ; bras CLOUÉ 20 épisodes, 1 tire, 6 coups, 0 défenseur tué ; bras LIBRE 20 épisodes, 18 tirent, 370 coups, 27 défenseurs tués ; durée de mesure 300 s ; les 2 tireurs survivent dans tous les épisodes (appui_vivant = 2)

**Sources.** /mnt/data/hmt/depot/correctifs/patch_banc_appui.py ; 00_socle.sqf, fonction CHACAL_fnc_bancAppui ; runs 2026-09-12_143803_chacal_i1 et 2026-09-12_143904_chacal_i2 (BA-CLOUE), 2026-09-12_143934_chacal_i3 et 2026-09-12_144004_chacal_i4 (BA-LIBRE) ; exemple de ligne : « CHACAL|E|banc_appui_fin|326.62|coups|61|par_tireur|TIREUR_1:40 TIREUR_2:21 |defenseurs_tues|2|duree|300|appui_vivant|2|cloue|2 »

**Reste ouvert.** Les 78 épisodes des campagnes de placeur ont tous tiré 0 coup ; 33 d'entre eux ont été interrompus avant la ligne banc_appui_fin, leur mesure n'existe donc pas.

### [ETABLI] Ce n'était pas le clouage : 79 postes sur 80 ne voient aucun défenseur

*2026-09-12*

Chaque tireur écrit à la pose ce qu'il VOIT réellement, par un rayon lineIntersectsSurfaces vers l'aimPos de chaque défenseur. Sur les 80 postes des 40 épisodes du banc, 79 ne voient AUCUN défenseur sur 4. Le seul tireur cloué qui en voyait un est exactement le seul qui a tiré. Le contraste brut « cloué 1/20 contre libre 18/20 » n'opposait donc pas deux réglages de tir. Il opposait un homme immobilisé sur un poste aveugle à une patrouille qui quitte sa position et va chercher son tir. Le placeur devient l'accusé, pas le clouage.

**Mesures.** 79 postes sur 80 voient 0 défenseur sur 4 ; 1/1 contre 0/39 pour le bras cloué, p = 0,025 ; tous les postes connaissent pourtant les 4 défenseurs (champ connait = 4, effet du reveal) ; épisode concerné : 2026-09-12_143803_chacal_i1/g7_r5, TIREUR_1 à 196 m, 1 défenseur vu, 6 coups

**Sources.** /mnt/data/hmt/depot/correctifs/patch_placeur.py (en-tête) ; lignes « CHACAL|E|banc_appui_poste » dans les serveur.rpt des quatre runs 2026-09-12_1438xx et 2026-09-12_1439xx

**Reste ouvert.** Le chiffre « la patrouille marche 459 m et finit à 108 m du site » est affirmé dans l'en-tête de patch_placeur.py et vient d'un script d'analyse (/mnt/c/Users/Younes/an_c2.py) dont la sortie n'a pas été conservée. Je n'ai pas pu le recalculer.

### [REFUTE] Placeur version 2 : battre le plancher du site

*2026-09-12*

Le placeur ne cherche plus la vue vers l'ouverture mais la vue sur l'INTÉRIEUR du site. Trente-sept points fixes sont posés à 1,1 m du sol : le centre, plus des anneaux à 0,30, 0,60 et 0,85 du rayon, à 8, 12 et 16 points. La couverture d'un candidat est la part de ces points que son œil atteint. Le score vaut 3 fois la couverture, plus le gain d'altitude sur 20, moins l'écart à 250 m, moins le relief sur 12. Et il sait dire non : sous 0,25 de couverture il refuse. Résultat : il a refusé dans les 14 épisodes, s'est replié sur l'observatoire, et l'appui n'a tiré aucun coup.

**Mesures.** 14 épisodes du bras B, 14 lignes « aucune_position_battante », meilleure couverture 0, candidats 206 (graine 7) et 220 (graine 8) ; 0 coup sur 14 épisodes ; bras A de contrôle : 0 coup sur 14 ; les postes de repli sont à 751-821 m ; 10 postes sur 28 y voient 1 ou 2 défenseurs et ne tirent toujours pas ; occulteurs nommés : Land_Cargo_HQ_V1_F, Land_HBarrier_Big_F, Land_Cargo_Patrol_V1_F

**Sources.** commit ee275c7 ; /mnt/data/hmt/depot/correctifs/patch_placeur.py ; runs 2026-09-12_162953_chacal_i3 et 2026-09-12_163023_chacal_i4 (PL-B) contre 2026-09-12_162822_chacal_i1 et 2026-09-12_162922_chacal_i2 (PL-A)

**Reste ouvert.** Le critère de réussite (18 sur 20) n'a jamais pu être atteint : aucun des deux bras n'a produit un seul coup, donc le bras A/B ne discrimine rien.

### [REFUTE] Placeur version 3 : chercher la hauteur utile

*2026-09-12*

Une mesure au labo MCP montre que 199 positions sur 504 voient encore le plancher malgré l'enceinte, dont une à 150 m avec 11 m de dénivelé. L'ancien filtre rejetait tout relief local de plus de 6 m, c'est-à-dire exactement les buttes qui donnent la vue. La règle devient : hauteur au moins égale à D/20 + 2 au-dessus du SOL DU SITE, platitude jugée sur 5 m seulement, bande 120-450 m. Le filtre retient 37 candidats sur 320 et rejette 282 pour cause de hauteur. Le placeur refuse encore, se replie à 769-789 m, et l'appui ne tire pas.

**Mesures.** labo : 199 positions sur 504 voient le plancher, enceinte de 31 HBarrier à 46 m de rayon ; règle D/20 + 2, soit 8 m à 150 m et 12 m à 250 m ; en mission : retenus 37, refus_trop_bas 282, refus_pente 1 ; 4 épisodes menés à terme, 0 coup ; 6 postes sur 8 du bras B voient 1 défenseur depuis 769-789 m et ne tirent pas

**Sources.** commit 3b2f9ea ; /mnt/data/hmt/depot/correctifs/patch_placeur3.py ; script de labo /mnt/c/Users/Younes/scan2.py ; runs 2026-09-12_172207_chacal_i2 et 2026-09-12_172237_chacal_i3 (PL3-B)

**Reste ouvert.** Les 12 dossiers d'épisode de cette campagne n'ont produit que 4 lignes banc_appui_fin : la campagne a été arrêtée après 15 minutes.

### [REFUTE] Placeur version 4 : le balayage systématique

*2026-09-12*

Au labo, le site de la graine 7 est reconstruit avec son mur, son QG, sa tour et son antenne : 102 positions sur 288 voient le plancher, plusieurs en voient les 37 points. Le placeur les ratait deux fois : il tirait au hasard dans un secteur étroit, et son filtre de hauteur jetait les positions basses qui voient par une porte ou un creux. Le tirage est remplacé par un balayage de 36 azimuts sur 8 distances, soit 288 candidats, dont la couverture est MESURÉE, environ 10 000 rayons. Le filtre de hauteur disparaît. Le résultat est instable : deux épisodes identiques rendent 0 et 0,541 sur les mêmes 288 candidats, avec les mêmes refus géométriques.

**Mesures.** labo : 102 positions sur 288 voient le plancher ; en mission : 288 balayés, refus_eau 0, refus_pente 7, refus_axe 40 ; meilleure couverture 0 dans deux épisodes, 0,541 dans un troisième ; écart minimal de 25 degrés à l'axe d'assaut ; refus sous 25 % ; 6 épisodes menés à terme, 0 coup ; la position à 0,541 est à 485 m et n'y voit 0 défenseur

**Sources.** commit 4661dfc ; /mnt/data/hmt/depot/correctifs/patch_balayage.py ; script de labo /mnt/c/Users/Younes/scan3.py ; runs 2026-09-12_173801_chacal_i2 et 2026-09-12_173836_chacal_i3 (PL4-B)

**Reste ouvert.** Couvrir le plancher n'est pas voir les hommes : la meilleure position mesurée voit 0 défenseur sur 4.

### [ETABLI] Placeur version 5 : un témoin dans la mesure

*2026-09-12*

Deux épisodes identiques avaient répondu 0,541 et 0 sur les mêmes 288 candidats. Au labo, le même balayage sur trois zones vierges rend 47, 92 et 56 positions qui voient, identiques à froid et 20 secondes plus tard : la mesure est stable quand elle répond. On applique la règle 16 et on pose un témoin dont on connaît la réponse : depuis le centre du site, à 2 m de haut, on voit forcément une large part du plancher. Le témoin est écrit à chaque passe, et si aucune position ne bat le site, le balayage recommence, jusqu'à 3 passes espacées de 6 secondes. Résultat : le témoin répond 1 à chaque passe. La mesure n'est donc pas muette, et le refus du balayage est réel.

**Mesures.** labo : 47, 92 et 56 positions sur 288 dans trois zones vierges, identiques à froid et après 20 s ; en mission : témoin = 1 à toutes les passes ; une instance refuse aux 3 passes, l'autre passe de 0 à 0,541 à la deuxième passe ; 4 épisodes menés à terme, 0 coup

**Sources.** commit 89fae4c ; /mnt/data/hmt/depot/correctifs/patch_temoin.py ; script de labo /mnt/c/Users/Younes/froid.py ; runs 2026-09-12_175559_chacal_i2 et 2026-09-12_175612_chacal_i3 (PL5-B) ; ligne « CHACAL|E|appui_balayage|...|passe|2|temoin|1|balayes|288|...|meilleure_couverture|0.541|retenue|3 »

**Reste ouvert.** Pourquoi la même géométrie rend 0 à la première passe et 0,541 à la seconde n'est pas expliqué. Le falsificateur écrit d'avance (témoin non nul ET balayage à 0) s'est produit, ce qui renvoyait au plancher, pas à la mesure.

### [ETABLI] Quatre sondes pour nommer ce qui arrête les rayons

*2026-09-12*

Avant de retoucher encore le placeur, on regarde. Quatre sondes fixes sont posées à 150 m du site, aux azimuts 0, 90, 180 et 270. Pour chacune, on compte les rayons libres vers les 37 points du plancher, ceux qui butent sur le TERRAIN, et le type des objets rencontrés. Ces sondes n'ont aucun effet sur le choix : c'est un journal. Le résultat est net : à 150 m, dans les quatre directions, AUCUN rayon n'est libre sur 37. Sur la graine 7, deux azimuts butent sur le terrain, les deux autres sur des objets. Sur la graine 8, aucun ne bute sur le terrain et ce sont le QG, la tour de garde et le mur qui bloquent.

**Mesures.** graine 7 : azimut 0 -> 0/37 libres, 0 terrain, gain +11 m ; azimut 90 -> 0/37, 31 terrain, -20 m ; azimut 180 -> 0/37, 37 terrain, -28 m ; azimut 270 -> 0/37, 0 terrain, objet Land_HBarrier_Big_F, -10 m. graine 8 : 0/37 libres aux quatre azimuts, 0 terrain partout, objets Land_HBarrier_Big_F, Land_Cargo_HQ_V1_F et Land_Cargo_Patrol_V1_F

**Sources.** commit a2c101c ; /mnt/data/hmt/depot/correctifs/patch_sonde.py ; run 2026-09-12_181029_chacal_i2 (version SONDE), lignes « CHACAL|E|appui_sonde »

**Reste ouvert.** Trois épisodes seulement portent ces sondes. La campagne SONDE était déclarée « diagnostic, pas une mesure ».

### [ETABLI] Labo MCP : la portée à laquelle l'IA ouvre le feu

*2026-09-12*

Toute la chasse au placeur supposait que l'appui ne tire pas parce qu'il ne voit pas. Or en mission il voit un défenseur sur quatre à 779 m et ne tire pas. Deux montages sont donc faits au labo MCP à 18h20 et 18h28. Le premier pose deux B_recon_M_F cloués en mode RED contre quatre O_Soldier_F en terrain libre, à 150, 300, 450, 600 et 800 m, avec la même désignation reveal 4 que la mission. Le second refait la même chose avec la recette du labo qui combat, deux groupes face à face, même skill. On compte les coups pendant 60 secondes à chaque distance. La conclusion retenue, écrite dans la note du job de 23h35, est que l'IA cesse d'engager au-delà de 600 m.

**Mesures.** cinq distances testées : 150, 300, 450, 600 et 800 m ; 60 s de comptage par distance ; seuil retenu : l'IA cesse d'engager au-delà de 600 m ; les postes réels de la mission étaient à 500 m et 779 m

**Sources.** /mnt/c/Users/Younes/portee.py et /mnt/c/Users/Younes/portee2.py ; contrôle d'instrument /mnt/c/Users/Younes/ctrl.py ; module /mnt/data/hmt/depot/labo/arma_labo.py ; conclusion citée dans /mnt/data/hmt/queue/en_cours/2026-09-12_V6_PLEIN_i2.json, champ note

**Reste ouvert.** La sortie chiffrée de portee.py et portee2.py n'a été écrite nulle part : elle n'existait qu'à l'écran. Je n'ai donc pas le tableau distance par distance, seulement le seuil de 600 m rapporté dans la note du job. Le RPT du serveur de labo de cet après-midi-là n'existe plus.

### [ETABLI] Labo MCP : l'effet de clouer un homme

*2026-09-12*

Le second suspect était le clouage lui-même. Un montage est fait au labo à 18h35, à 300 m, c'est-à-dire à portée : mêmes hommes, même monde, seul change disableAI PATH. L'appui cloué a tiré 0 coup, l'appui libre 28. Le même script teste aussi si l'arme allonge l'enveloppe, en refaisant 600 m avec un EBR 7.62 et une lunette DMS. À 18h42, une mesure de suite cherche une façon d'immobiliser QUI LAISSE TIRER, avec cinq bras : libre, disableAI PATH, disableAI MOVE, doStop, forceSpeed 0. Avec deux répétitions, cela ne tranchait pas : chaque bras immobilisé donnait un essai à 0 et un essai fourni, pendant que le bras libre donnait 16 et 15. À 18h53, la mesure est reprise à cinq répétitions sur trois bras, avec le nombre de tireurs posés et le nombre de rayons libres contrôlés à chaque essai.

**Mesures.** à 300 m : cloué 0 coup, libre 28 coups ; bras libre en n=2 : 16 et 15 coups ; chaque bras immobilisé en n=2 : un essai à 0 et un essai fourni ; cinq bras testés puis trois bras à cinq répétitions ; 60 s de comptage par essai ; 2 tireurs contre 4 défenseurs, skill 0,6

**Sources.** /mnt/c/Users/Younes/cloue.py (18:35), /mnt/c/Users/Younes/immo.py (18:42), /mnt/c/Users/Younes/immo2.py (18:53) ; les chiffres cités sont ceux écrits dans les en-têtes des scripts suivants, qui rapportent le résultat du précédent

**Reste ouvert.** Le résultat d'immo2.py, c'est-à-dire la façon d'immobiliser qui laisse tirer, n'est repris dans aucun fichier postérieur. Je n'ai pas pu établir quelle façon a été retenue, ni si l'une d'elles a passé. Les sorties de cloue.py, immo.py et immo2.py ne sont écrites nulle part.

### [EN COURS] La décision du soir : l'appui est coupé

*2026-09-12*

À 23h35, sept jobs partent pour la campagne VICTOIRE-BOUT-EN-BOUT-12-09. L'appui y est coupé : appui_feu = 0, placeur = 0, banc_appui = 0. La note du job donne la raison en une phrase : l'appui n'a jamais tiré un coup utile, et la mesure du 12/09 au labo montre que l'IA cesse d'engager au-delà de 600 m alors qu'il était posté à 500 ou 779 m. Le levier retenu à sa place est le socle d'exécution. La campagne joue enfin la phase 6, l'exfiltration, qui n'avait jamais été jouée dans les 245 épisodes du 10 au 12/09. Ces sept jobs tournaient encore au moment de ma lecture.

**Mesures.** 7 jobs, graines 7 et 8, 3 répétitions, arret = 6, socle = 1, plafond 5400 s ; un huitième job, la sonde de durée, joue l'approche complète de 4,4 km avec un plafond de 10800 s ; prédiction écrite : taux de succès entre 10 et 40 %, cause d'échec dominante CHARGES_INCOMPLETES

**Sources.** /mnt/data/hmt/queue/en_cours/2026-09-12_V6_PLEIN_i2.json à _i7.json et 2026-09-12_V6_SONDE-DUREE_i1.json ; runs 2026-09-12_233559_chacal_i1 à 2026-09-12_233832_chacal_i7

**Reste ouvert.** Le résultat de cette campagne n'était pas encore lisible : aucun FIN.json, les serveurs tournaient encore.

### [EN COURS] L'atelier : le site rebâti au labo pour reprendre à zéro

*2026-09-12 au 2026-09-13*

À 23h50, après l'échec du placeur, le site de la graine 7 est reconstruit à l'identique dans le labo MCP, à partir de 20_decor.sqf. L'enceinte compte 20 segments à 46 m de rayon, avec deux ouvertures aux azimuts 126 et 252, plus un PC, deux maisons, une tour, deux antennes, un radar, un groupe électrogène, cinq lampes et quatre bunkers. Un contrôle positif est posé d'abord : un homme seul marche sur le site. Il est tué par le guetteur de la tour à 142 m, d'un seul coup, à 45 secondes. L'atelier mesure donc bien quelque chose. L'assaut nu à dix hommes donne ensuite 8 vivants sur 10 et 7 hommes entrés dans l'enceinte, ce qui réfute la prédiction écrite d'avance qui annonçait la perte de la moitié de l'effectif. Un essai E3 est prévu avec un appui non cloué à 300 m, c'est-à-dire à la distance que le moteur accepte.

**Mesures.** 35 objets posés, 18 segments de mur, 4 bunkers, 5 défenseurs dont 5 dans un bâtiment ; E0 : 1 homme, 0 vivant sur 1, 0 rouge tué, distance minimale 142 m, 0 entré, 0 coup bleu, 1 coup rouge, premier coup à 45 s, 5 couples qui savent ; E1 : 10 hommes, 8 vivants sur 10, 2 rouges tués sur 5, distance minimale 31 m, 7 entrés, 420 coups bleus, 58 coups rouges, premier coup à 45 s, 22 couples qui savent

**Sources.** /mnt/data/hmt/atelier/journal.jsonl (3 lignes) ; /mnt/data/hmt/atelier/atelier.py, atelier2.py, atelier3.py, atelier4.py ; RPT du labo /mnt/c/Users/Younes/hmtech9/arma3server_x64_2026-09-12_23-49-18.rpt

**Reste ouvert.** Les essais E2 à E5 d'atelier4.py, dont E3 qui pose un appui non cloué à 300 m, n'avaient pas encore écrit de ligne dans le journal au moment de ma lecture.

### Ce que ce lecteur n'a PAS pu établir

Ce que je n'ai PAS pu établir.

1. Les chiffres bruts des mesures de labo MCP du 12/09 au soir. Les scripts /mnt/c/Users/Younes/portee.py, portee2.py, cloue.py, immo.py et immo2.py impriment leurs tableaux à l'écran et n'écrivent aucun fichier. Je n'ai donc ni le tableau coups-par-distance (150, 300, 450, 600, 800 m), ni le détail des cinq façons d'immobiliser. Les seuls chiffres que je peux citer sont ceux recopiés dans l'en-tête du script suivant (300 m : cloué 0, libre 28 ; bras libre 16 et 15 en n=2) et le seuil de 600 m cité dans la note du job V6. Le RPT du serveur de labo de cet après-midi a été effacé : il ne reste qu'un RPT dans /mnt/c/Users/Younes/hmtech9/, celui de 23h49.

2. Le résultat final d'immo2.py. Aucune façon d'immobiliser l'appui qui le laisse tirer n'est nommée dans un fichier postérieur. Je ne sais pas si l'une d'elles a passé.

3. Aucun verdict écrit. Ni le banc d'appui, ni le placeur, ni les mesures de labo n'ont donné de fichier dans /mnt/data/hmt/depot/verdicts/. Le dernier verdict d'appui est feu-avant-vignette.md du 10/09, toujours OUVERT. Tout le travail du 12/09 n'existe que dans les messages de commit, les en-têtes des correctifs et les notes de job.

4. Le chiffre « la patrouille marche 459 m et finit à 108 m du site » (en-tête de patch_placeur.py). Il vient d'un script d'analyse a posteriori, /mnt/c/Users/Younes/an_c2.py, dont la sortie n'a pas été conservée. Je n'ai trouvé aucune ligne de journal qui le porte et je ne l'ai pas recalculé.

5. Le compte de « 0 coup sur 17 épisodes du socle complet » (commit bdc52a4). Je le cite tel qu'écrit dans le code ; je ne l'ai pas recompté épisode par épisode.

6. L'effet du placeur version 1 sur l'issue de la mission entre le 10 et le 12/09. Aucun bras apparié n'isole CHACAL_APPUI_FEU seul ; le 10/09 il est monté en même temps que d'autres leviers.

7. La cause de l'instabilité du balayage. Le témoin répond 1, donc la mesure fonctionne, et pourtant deux passes identiques rendent 0 puis 0,541. Rien n'explique cet écart.

8. 33 des 118 épisodes lancés sous banc_appui n'ont pas de ligne banc_appui_fin : ils ont été tués avant la fin (scripts arreter_pl.sh, arreter_pl3.sh, arreter_pl4.sh, arreter2.sh). Leur mesure n'existe pas et je ne l'ai pas reconstituée.

Note de méthode : je n'ai rien modifié, rien lancé et tué aucun processus. Les sept serveurs Arma de la campagne VICTOIRE-BOUT-EN-BOUT tournaient pendant toute ma lecture et tournent toujours.

---
