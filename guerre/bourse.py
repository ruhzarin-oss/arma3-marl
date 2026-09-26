"""LA BOURSE DE GUERRE : ce que l economie d une ile donne a son armee dans Arma, minute par minute d horloge murale.

Decision de Younes ( 26/09 ) : le moteur tourne TOUJOURS a pleine vitesse, Arma en temps reel ; on ne fixe pas de
taux de change du temps, l horloge murale arbitre. Chaque minute reelle, une ile verse a son camp ce que son
economie a produit pour la defense pendant CETTE minute, quel que soit le nombre de jours du moteur qu elle contient.

La regle ( une seule formule, chaque terme lu dans le moteur ) :

    points = f x part_defense x recettes x euros_par_unite / EUROS_PAR_POINT

- recettes : les recettes de l Etat ( domaine 6, tresor.serie ) des jours du moteur clos pendant la minute - c est
  la que les resultats des menages et des entreprises deviennent de l argent public ( TVA, IR, IS, douanes... ) ;
- part_defense : la part de la ligne « defense » dans les credits votes de l exercice ( la loi de finances de l ile ) ;
- euros_par_unite : l etalon-or de l ile ( monde/or_reel.py ) - les six monnaies se comparent en euros ;
- f = min( 1, PLAFOND_ARMA / militaires ) : Arma ne porte que PLAFOND_ARMA hommes par camp ( 765 corps par serveur
  mesures le 23/09, et Warlords garde ses secteurs neutres ) ; le front recoit la part du budget de defense qui
  correspond a la part de l armee qui y combat. Sans ce facteur, une ile d un million d habitants verserait le
  budget de toute son armee a une bataille de cent hommes.

CHOIX A TRANCHER PAR YOUNES ( pris en copiant le reel quand c est possible, liste au LISEZMOI ) :
- EUROS_PAR_POINT = 100 : un point de Warlords vaut 100 euros ; un fusilier ( 100 points ) coute 10 000 euros, l ordre
  de grandeur de l equipement individuel d un fantassin europeen. Les RAPPORTS entre les prix restent ceux de
  Warlords ( un char vaut 50 fusiliers, 300 a 600 dans le reel ) : jeu, pas reel.
- PLAFOND_ARMA = 100 hommes par camp."""

EUROS_PAR_POINT = 100.0
PLAFOND_ARMA = 100


def part_du_front(militaires, plafond=PLAFOND_ARMA):
    """La part de l armee de l ile qui combat dans Arma."""
    if militaires <= 0: return 1.0
    return min(1.0, plafond / float(militaires))


def points_de_la_minute(recettes, part_defense, euros_par_unite, militaires, plafond=PLAFOND_ARMA,
                        euros_par_point=EUROS_PAR_POINT):
    """( points de Warlords, f, euros ) pour une minute d horloge murale. Rien de negatif : une recette negative
    ( remboursements d impot superieurs aux entrees ) ne reprend pas ce qui a deja ete verse."""
    if not (0.0 <= part_defense <= 1.0): raise ValueError(f"part de la defense hors [0 ; 1] : {part_defense!r}")
    if euros_par_unite <= 0: raise ValueError(f"etalon-or non positif : {euros_par_unite!r}")
    f = part_du_front(militaires, plafond)
    euros = max(0.0, f * part_defense * recettes * euros_par_unite)
    return euros / euros_par_point, f, euros
