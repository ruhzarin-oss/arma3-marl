# Criteres pre-enregistres - DESIGNATION-19-09 : le banc « regard centre » mesure-t-il une cible DESIGNEE ? ( ecrit AVANT tout episode, 19/09, 2 h 50 )

## Le soupcon
BANC3 : en balayage ( doWatch sur une POSITION ), 1 cible connue sur 14 en 90 s, meme dans l axe de la phase et meme avec le balayage repare ; alors qu en
regard centre ( mode 5 : doWatch sur L UNITE ennemie ) une cible debout a 150-215 m est connue a ~100 % en 5 s. Il se peut que designer l unite au moteur
suffise a la faire entrer dans la liste de cibles du groupe. Dans ce cas, SEUIL-PAR-MONDE, PORTEE et BANC3-A mesurent « ce que l IA connait d une cible
qu on lui designe », pas une detection spontanee - et la fenetre de la mission, qui regarde des positions, ne peut pas en profiter.

## Le test : mode 5 contre mode 9, apparies
Mode 9 ( `patch_banc_mode9.py` ) = mode 5 a une difference pres : les hommes sont tournes vers la cible et regardent SA POSITION, jamais l objet.
2 modes x 2 distances ( 150 et 200 m, debout, nuit ) x 4 paires de mondes = 16 jobs, 32 episodes, fenetre 600 s, melanges sur les instances libres.
Validite : comme BANC3 ( la regle « cible masquee » s applique : cible debout ) ; angle de la 1re sonde <= 5 deg dans les DEUX modes ( sinon le mode 9 ne
regarde pas la cible et le test ne vaut rien ).

## Lecture et decision, ecrites d avance
Part connue en 90 s par mode ( toutes distances ), et ecart apparie par ( monde, distance ) quand les deux modes sont valides.
- **DESIGNATION ETABLIE** : le mode 9 connait la cible dans au moins 40 points de moins que le mode 5 ( part connue en 90 s ). Consequence : les portees
  « regard centre » sont a relire comme des portees de cible DESIGNEE, et le compte rendu le dit en tete.
- **PAS DE DESIGNATION** : ecart de moins de 15 points. Le soupcon tombe ; l echec du balayage est a chercher ailleurs ( duree du regard par azimut,
  nombre d hommes qui regardent, cadence de la detection ).
- Entre les deux : indecis, a redire tel quel.
Prediction ( honnete : je ne sais pas ) : je penche pour DESIGNATION ETABLIE, parce que le balayage repare regarde bien l axe 10 s sur 30 et ne connait rien.
