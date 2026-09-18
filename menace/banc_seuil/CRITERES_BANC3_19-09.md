# Criteres pre-enregistres - BANC3 : cible ACCROUPIE et BALAYAGE ( ecrit AVANT tout episode, nuit du 18 au 19/09/2026 )

Banc `chacalvue` + `patch_banc_modes.py` ( version 3 : posture, modes 7 et 8, ecart d azimut, nouvelle pose si la cible reelle est masquee ).
Tout de NUIT ( l heure de la mission ), fenetre et sonde comme la veille.

## Fumee FUMEE-BANC3-19-09 ( 3 jobs, mondes 4 et 5 ) - rien ne part si un point echoue
| job | reglage | attendu |
|---|---|---|
| REGRESSION | mode 5, debout, 150 m | 0 erreur SQF ; connue en <= 10 s dans au moins un monde ( comme la veille ) ; champs `mode`, `posture`, `essais`, `vis_pose`, `candidats` presents ; `vis_pose` >= 0,10 ou `essais` = 6 |
| ACCROUPIE | mode 5, accroupie, 100 m | 0 erreur SQF ; `posture` = 1 ; angle de la 1re sonde <= 5 deg ; l episode se rend ( VOID BANC_TERMINE ou refus propre ) |
| BALAYAGE | mode 8, debout, 150 m, ecart 45 deg | 0 erreur SQF ; `az_consigne` = 45 ; l azimut pose est a moins de 12 deg de `axe` + 45 ; l angle regard-cible VARIE pendant la fenetre ( max - min >= 30 deg : les hommes balaient, ils ne fixent pas la cible ) |

## Campagne BANC3-19-09 ( 40 jobs x 2 mondes = 80 episodes, melanges sur les instances libres )
**A. ACCROUPIE, regard centre** ( mode 5, posture 1 ) : 100, 150, 200, 250, 300, 400 m x 4 paires de mondes = 24 jobs, fenetre 600 s.
   Question : a quelle distance une menace accroupie - la posture des vraies menaces de `35_menaces.sqf` - est-elle encore connue ?
**B. BALAYAGE** ( cible debout a 200 m : connue a 100 % la veille quand on la regarde ) : modes 7 ( balayage de la mission ) et 8 ( repare )
   x ecarts 0, 45, 90, 135 deg x paires 4-5 et 6-7 = 16 jobs, fenetre 90 s ( celle de la mission ).
   Question : le balayage de la mission voit-il ce qui est dans son secteur, et le balayage repare fait-il mieux ?

## Validite ( comme PORTEE ) : ligne de vue, pas de refus, 0 erreur SQF, vis_moy > 0,01, fenetre achevee pour un « jamais » ;
en mode 5 angle de la 1re sonde <= 5 deg ; en modes 7 et 8 aucun critere d angle ( c est la mesure ).

## Predictions ecrites avant
1. ACCROUPIE : la part connue en 90 s est inferieure a celle de la cible debout a distance egale ( debout, nuit : ~100 % jusqu a 225 m,
   ~70 % vers 250-350 m ) ; elle passe sous 50 % avant 300 m.
2. BALAYAGE DE LA MISSION ( mode 7 ) : a l ecart 0 la cible est connue en 90 s dans la majorite des cas ; a 45 deg, dans moins de la moitie
   ( le pivot sous doWatch est trop lent pour tenir 10 s par azimut ).
3. BALAYAGE REPARE ( mode 8 ) : a 0 et a 45 deg, connue en 90 s dans la majorite des cas ; il fait au moins aussi bien que le mode 7 a chaque ecart.
4. A 90 et 135 deg, aucun des deux balayages ne connait la cible ( elle est hors du secteur -45 / +45 ) : si c est faux, le champ de vision
   de l IA est plus large que le secteur et le balayage compte moins que je ne le crois.
5. NOUVELLE POSE : la part de cibles masquees ( vis_moy <= 0,01 ) tombe sous 10 % ( 30 % dans PORTEE ).
Toute prediction fausse est rapportee telle quelle.
