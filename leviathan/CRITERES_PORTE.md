# CRITERES — LA PORTE DE PREDICTION DU MODELE DU MONDE

Pre-enregistre AVANT d ecrire une seule ligne du modele. Empreinte prise apres ecriture.

## Ce que la porte tranche

Un modele du monde entraine sur Arma doit d abord PREDIRE Arma. Tant qu il ne predit pas, aucune
politique n est entrainee dedans. Sinon on refabrique le mensonge du bac a sable ecrit a la main,
appris au lieu d ecrit — et on ne s en apercevrait qu apres des semaines.

On ne juge PAS sur l erreur de reconstruction pas a pas. Le bac a sable condamne le 30/07 avait des
PIECES justes (courbe de toucher, suppression, repartition du feu, toutes mesurees sur Arma) et une
ISSUE fausse. On juge donc sur des VERDICTS.

## Le monde de reference

Empreinte du monde obligatoire : les cibles ci-dessous ont ete mesurees sur le monde
0c9714e8044d92a4 (jeu de mods du juge). Un modele entraine ou juge sur un autre monde ne passe pas
cette porte, il en passe une autre. Motif : le 30/07 la ferme a tourne sans aucun mod et l accord
zero contre zero a ete pris pour un accord.

## Les cibles, et pourquoi seulement celles-la

Mesurees sur la nuit 0 modee, 493 episodes, D=8 constant, objectif Pyrgos.

Une cible n entre ici que si elle survit au reechantillonnage DANS LA METRIQUE QUI LA JUGERA. On
note en Spearman : on exige donc que la borne basse a 5 % du Spearman entre le classement reel et
ses reechantillonnages depasse 0,60. Exiger un ordre exactement identique serait un critere
etranger a la porte, et sur quatre manoeuvres il y a vingt-quatre ordres possibles.

| cible | classement (du meilleur au pire) | Spearman moyen | borne basse 5 % | n par case |
|---|---|---|---|---|
| prise a A=8  | reckless > frontal > envelop > supfront | 0,927 | 0,800 | 60 |
| prise a A=12 | reckless > frontal > supfront > envelop | 0,911 | 0,800 | 60 |

Taux mesures, avec intervalles de Wilson a 95 % :

  A=8   reckless 70,0 % [57,5 ; 80,1]   frontal 46,7 % [34,6 ; 59,1]
        envelop  40,0 % [28,6 ; 52,6]   supfront 28,3 % [18,5 ; 40,8]
  A=12  reckless 91,7 % [81,9 ; 96,4]   frontal 71,7 % [59,2 ; 81,5]
        supfront 70,0 % [57,5 ; 80,1]   envelop  51,7 % [39,3 ; 63,8]

ECARTEES, et pourquoi — on le consigne pour ne pas les reintroduire par oubli :
  - toutes les cibles a A=4 : borne basse 0,40. A 0-10 % de prise sur 20 repetitions, rien n y est
    separable ; il faudrait des centaines d episodes pour un gain nul, l information d inversion
    etant deja portee par le contraste entre les deux cibles retenues.
  - tous les classements par PERTES : bornes basses de 0,20 a 0,40. Les manoeuvres s y separent de
    fractions d homme pour un ecart-type proche de l unite. On mesurerait du bruit.

## Le protocole de mesure du modele

Pour chacune des 6 politiques de reference, 35 episodes reels TENUS HORS ENTRAINEMENT. On donne au
modele l observation initiale et la suite d actions reellement jouee, on deroule EN BOUCLE OUVERTE
sans jamais lui rendre d observation, 100 tirages stochastiques par episode. On compare les
distributions agregees par politique.

## Les deux etages, decides d avance

ETAGE « PASSE » — les trois conditions ensemble :
  1. le taux de prise predit tombe dans l intervalle de Wilson a 95 % du reel, pour CHACUNE des
     8 cases retenues (4 manoeuvres x 2 rapports de force) ;
  2. le nombre moyen d attaquants perdus predit tombe dans l intervalle de confiance a 95 % du
     reel, pour chacune de ces 8 cases ;
  3. Spearman moyen >= 0,60 sur les DEUX classements complets retenus.

ETAGE « FORTE » — rapporte, non exige du premier modele :
  les deux Spearman >= 0,80, et la generalisation hors support (voir ci-dessous) passee.

GENERALISATION HORS SUPPORT — le test le plus dur, celui qui approche ce que fera une politique qui
devie des professeurs : entrainer SANS une manoeuvre, predire ses episodes dans les memes bornes.
Rapporte des le premier modele, exige a l etage FORTE.

## Pourquoi le classement complet et pas seulement le vainqueur

Le vainqueur est le meme (reckless) aux deux rapports de force retenus : un predicteur CONSTANT
passerait un critere « nomme le meilleur » sans rien savoir du monde. Toute l information
discriminante est dans l ordre des trois perdants, et il CHANGE entre A=8 et A=12 (envelop et
supfront s echangent). C est cette inversion que la porte mesure.

## Fil de detente, apres la porte

Chaque jour d entrainement d une politique : 30 episodes d evaluation reelle. Si le taux de reussite
IMAGINE depasse le REEL de plus de 20 points, arret et reentrainement du modele sur donnees
fraiches. C est la reformulation apprise de : ne jamais croire un simulateur qu on n a pas
confronte.

## Interdits

- Ne pas entrainer sur les episodes tenus a l ecart, ni sur ceux du monde sans mods
  (replay/nuit0_sansmods) ni sur les sessions de mise en service (replay/mise_en_service).
- Ne pas ajuster une cible apres avoir vu la prediction du modele.
- Ne pas remplacer un critere au moment ou il echoue : consigner l echec, amender de maniere
  PROSPECTIVE avec une nouvelle empreinte, et prouver que le critere neuf sait echouer.
