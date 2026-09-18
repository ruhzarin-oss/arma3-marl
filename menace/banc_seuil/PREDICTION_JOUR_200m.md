# Prediction ecrite AVANT le job « jour 200 m » ( BANC-SEUIL-18-09 ) - 18/09/2026, voir l heure du fichier

Etat a 16 h 45 : le job 2026-09-18_SEUIL_JOUR_m45_200m.json est ENCORE EN FILE ( instance 4 occupee par « jour 300 m » ).

## Les deux formes en concurrence
- MARCHE : connue en 6 a 8 s sous le seuil, jamais au-dela. A 200 m de jour ( seuil de jour > 280 m ) : delai attendu 6 a 8 s.
- ACCUMULATEUR QUI FUIT ( idee de CWR, vis ~ 1/d2 ) : delai = t0 + S / ( A/d2 - f ), jamais si A/d2 <= f, seuil d* = racine( A/f ).

## Ajustement de l accumulateur sur les points de JOUR deja lus ( distance vraie, delai )
144 m 7 s ; 147 m 6 s ; 280 m 70 s ; 301 m 259 s ; ( 300 m jamais en 300 s, ancien banc ).
Avec 1/(delai - t0) = alpha/d2 - beta, sur les deux points lointains et t0 = 5 s : alpha = 6661 m2/s, beta = 0,0696 /s,
donc d* = 309 m. ! Trois parametres pour trois distances : cet ajustement est EXACTEMENT identifie, il ne prouve RIEN.
Sa seule valeur est la prediction qui suit, faite sur un point jamais vu.

## Prediction pour 200 m de jour ( a corriger par la distance VRAIE lue )
- ACCUMULATEUR : delai - t0 = 1 / ( 6661/200^2 - 0,0696 ) = 10,3 s ; avec t0 entre 2 et 5 s : DELAI ENTRE 12 ET 16 S.
  ( a 190 m : 11 a 14 s ; a 210 m : 14 a 18 s. ) La sonde tombe toutes les 5 s : lecture attendue 12 a 17 s.
- MARCHE : 6 a 8 s.
- Verdict du point : delai lu <= 8 s dans les deux mondes -> l accumulateur ajuste est FAUX ( la marche garde la main sous le seuil ) ;
  delai lu entre 11 et 18 s -> la marche pure est FAUSSE et l accumulateur survit a son premier test ; autre chose -> ni l un ni l autre,
  le dire tel quel. Angle du regard au debut > 20 deg : le point est lu mais marque « confondu par le pivot ».
