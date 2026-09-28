# Ressemblance avant et apres : metiers des iles, migrations, faim, inflation ( 28/09/2026 )

Branche `iles-metiers-emigration` ( partie du tronc 5077c0a ). « Avant » : le tronc 5077c0a ; « apres » : la generation dimensionnee sur les sites de chaque ile ( HMT-126 b ), les migrations du domaine 7 au taux reel ( HMT-114 ), les indicateurs de la faim et de la population ( HMT-129 ), l inflation sur 90 jours ( HMT-128 ). Meme graine, meme fenetre avant et apres ; les mondes sont lances par `annee.py` ( chauffe, puis Suivi de ressemblance.py ). Une seule graine par monde : un ecart de quelques points entre avant et apres peut venir de la trajectoire, pas du changement. Les 4 indicateurs neufs n existent pas avant ( « absent » ).

Stratis est construite par `archipel.creer_ile( "Stratis", 1, 20 )` ( comme la session du moteur et la guerre : l echelle des convois y est celle de l ile ), pas par `--iles Stratis`.

#### Altis par defaut ( 10 000 habitants, chauffe 40 j, mesure 90 j )

| Indicateur | Reel | Bande | Avant | Apres |
|---|---|---|---|---|
| Part des 0-14 ans | 13.10 | 11.80-14.40 | 13.98 dans | 14.42 HORS |
| Part des 15-64 ans | 63.50 | 60.50-66.50 | 78.74 HORS | 78.35 HORS |
| Part des 65 ans et plus | 23.40 | 21.10-25.70 | 7.27 HORS | 7.23 HORS |
| Part des moins de 5 ans | 3.80 | 3.20-4.40 | 0.272 HORS | 0.259 HORS |
| Age median | 46.90 | 44.50-49.30 | 39.01 HORS | 38.81 HORS |
| Rapport de masculinite | 96.06 | 93.00-99.00 | 197.0 HORS | 196.8 HORS |
| Taille moyenne des menages | 2.40 | 2.20-2.60 | 1.88 HORS | 1.89 HORS |
| Taux brut de natalite | 6.60 | 5.60-7.60 | 6.10 dans (fragile) | 6.07 dans (fragile) |
| Taux brut de mortalite | 12.10 | 10.30-13.90 | 53.68 HORS | 4.86 HORS |
| Morts de faim pour 100 000 habitants par an | 0.000 | 0.000-1.00 | (absent) | 202.4 HORS |
| Population vivante sur population de depart (sur un an) | 1.000 | 0.985-1.01 | (absent) | 1.00 dans |
| Taux d emigration | 0.890 | 0.650-1.10 | (absent) | 0.850 dans (fragile) |
| Taux d immigration | 1.21 | 1.00-1.45 | (absent) | 1.50 HORS (fragile) |
| Taux d emploi des 20-64 ans | 69.30 | 65.30-73.30 | 77.79 HORS | 77.74 HORS |
| Taux de chomage des 15-74 ans | 10.10 | 7.60-12.60 | 6.85 HORS | 7.12 HORS |
| Part de l emploi public | 15.50 | 12.00-19.00 | 28.32 HORS | 28.32 HORS |
| Part des militaires dans la population | 1.07 | 0.800-1.45 | 9.09 HORS | 9.05 HORS |
| Salaire minimum sur salaire median | 48.70 | 43.70-53.70 | 46.71 dans | 46.71 dans |
| Part de l emploi agricole | 10.97 | 8.50-13.50 | 28.35 HORS | 28.25 HORS |
| Part de l emploi dans l hebergement et la restauration | 9.35 | 7.50-11.20 | 6.53 HORS | 6.50 HORS |
| Part des titulaires d une pension de vieillesse | 19.30 | 16.50-22.10 | 10.00 HORS | 9.98 HORS |
| Part de l alimentation dans le budget des menages | 20.70 | 17.20-24.20 | 23.77 dans | 24.36 HORS |
| Part du logement dans le budget des menages | 14.40 | 10.90-17.90 | 14.97 dans | 15.12 dans |
| Part du transport dans le budget des menages | 13.30 | 9.80-16.80 | 9.96 dans | 9.35 HORS |
| Depense publique totale / PIB | 48.10 | 43.10-53.10 | 55.27 HORS | 55.68 HORS |
| Recettes fiscales et sociales / PIB | 41.70 | 38.20-45.20 | 37.83 HORS | 37.71 HORS |
| Importations de biens et services / PIB | 47.70 | 40.00-55.40 | 20.21 HORS | 20.54 HORS |
| Exportations de biens et services / PIB | 42.10 | 35.00-49.20 | 49.02 dans | 49.05 dans |
| Recettes du tourisme international / PIB | 9.17 | 7.20-11.20 | 37.72 HORS | 37.68 HORS |
| Inflation annuelle | 3.00 | 0.000-6.00 | -39.31 HORS | -32.98 HORS (fragile) |
| Taux d epargne brute des menages | -2.51 | -6.50-1.50 | 47.38 HORS | 47.55 HORS |
| Dette publique / PIB | 154.2 | 134.2-174.2 | 3.63 HORS | 3.95 HORS |
| PIB par habitant (en euros) | 22 480 | 18 000-27 000 | 17 118 HORS | 17 055 HORS |
| Lits d hopital pour 1000 habitants | 4.23 | 3.60-4.90 | 5.34 HORS | 5.28 HORS |
| Medecins pour 1000 habitants | 6.27 | 5.30-7.30 | 7.56 HORS | 7.48 HORS |
| Infirmiers pour 1000 habitants | 2.48 | 2.00-4.20 | 6.75 HORS | 6.68 HORS |
| Hospitalisations pour 1000 habitants par an | 170.0 | 100.0-280.0 | 19.93 HORS | 23.07 HORS |
| Voitures particulieres pour 1000 habitants | 581.0 | 500.0-660.0 | 541.5 dans | 537.2 dans |
| Morts sur la route par million d habitants | 64.00 | 45.00-85.00 | 0.000 HORS (fragile) | 0.000 HORS (fragile) |
| Electricite consommee par habitant | 4 773 | 4 050-5 500 | 3 141 HORS | 3 128 HORS |
| Eleves par enseignant | 7.40 | 6.00-10.00 | 13.67 HORS | 14.20 HORS |
| Detenus pour 100 000 habitants | 110.7 | 90.00-130.0 | 90.67 dans | 89.74 HORS |
| Policiers pour 100 000 habitants | 559.2 | 450.0-670.0 | 2 912 HORS | 2 882 HORS |
| Homicides volontaires pour 100 000 habitants | 0.780 | 0.400-1.20 | 0.000 HORS (fragile) | 0.000 HORS (fragile) |
| Participation aux elections legislatives | 52.80 | 45.00-65.00 | - n.m. | - n.m. |
| Part des personnes logees chez leur menage proprietaire | 69.70 | 64.70-75.70 | 73.76 dans | 73.29 dans |

Score avant 10/40 ; apres 8/44.


#### Altis grec ( --habitants 6375, 10 003 habitants, chauffe 40 j, mesure 365 j )

| Indicateur | Reel | Bande | Avant | Apres |
|---|---|---|---|---|
| Part des 0-14 ans | 13.10 | 11.80-14.40 | 11.98 dans | 11.87 dans |
| Part des 15-64 ans | 63.50 | 60.50-66.50 | 60.92 dans | 60.93 dans |
| Part des 65 ans et plus | 23.40 | 21.10-25.70 | 27.10 HORS | 27.19 HORS |
| Part des moins de 5 ans | 3.80 | 3.20-4.40 | 3.43 dans | 3.36 dans |
| Age median | 46.90 | 44.50-49.30 | 48.81 dans | 49.17 dans |
| Rapport de masculinite | 96.06 | 93.00-99.00 | 93.24 dans | 93.84 dans |
| Taille moyenne des menages | 2.40 | 2.20-2.60 | 2.43 dans | 2.43 dans |
| Taux brut de natalite | 6.60 | 5.60-7.60 | 7.23 dans (fragile) | 7.24 dans (fragile) |
| Taux brut de mortalite | 12.10 | 10.30-13.90 | 139.8 HORS | 135.9 HORS |
| Morts de faim pour 100 000 habitants par an | 0.000 | 0.000-1.00 | (absent) | 12 354 HORS |
| Population vivante sur population de depart (sur un an) | 1.000 | 0.985-1.01 | (absent) | 0.890 HORS |
| Taux d emigration | 0.890 | 0.650-1.10 | (absent) | 1.20 HORS (fragile) |
| Taux d immigration | 1.21 | 1.00-1.45 | (absent) | 1.18 dans (fragile) |
| Taux d emploi des 20-64 ans | 69.30 | 65.30-73.30 | 79.42 HORS | 80.12 HORS |
| Taux de chomage des 15-74 ans | 10.10 | 7.60-12.60 | 0.025 HORS | 0.000 HORS |
| Part de l emploi public | 15.50 | 12.00-19.00 | 18.75 dans | 18.66 dans |
| Part des militaires dans la population | 1.07 | 0.800-1.45 | 1.61 HORS | 1.61 HORS |
| Salaire minimum sur salaire median | 48.70 | 43.70-53.70 | 46.71 dans | 46.71 dans |
| Part de l emploi agricole | 10.97 | 8.50-13.50 | 34.54 HORS | 34.44 HORS |
| Part de l emploi dans l hebergement et la restauration | 9.35 | 7.50-11.20 | 11.41 HORS | 12.48 HORS |
| Part des titulaires d une pension de vieillesse | 19.30 | 16.50-22.10 | 29.15 HORS | 29.22 HORS |
| Part de l alimentation dans le budget des menages | 20.70 | 17.20-24.20 | 26.80 HORS | 26.87 HORS |
| Part du logement dans le budget des menages | 14.40 | 10.90-17.90 | 13.26 dans | 13.12 dans |
| Part du transport dans le budget des menages | 13.30 | 9.80-16.80 | 13.41 dans | 13.59 dans |
| Depense publique totale / PIB | 48.10 | 43.10-53.10 | 76.34 HORS | 74.37 HORS |
| Recettes fiscales et sociales / PIB | 41.70 | 38.20-45.20 | 39.94 dans | 39.40 dans |
| Importations de biens et services / PIB | 47.70 | 40.00-55.40 | 24.76 HORS | 24.41 HORS |
| Exportations de biens et services / PIB | 42.10 | 35.00-49.20 | 38.50 dans | 40.00 dans |
| Recettes du tourisme international / PIB | 9.17 | 7.20-11.20 | 26.40 HORS | 27.20 HORS |
| Inflation annuelle | 3.00 | 0.000-6.00 | -3.14 HORS | -2.67 HORS (fragile) |
| Taux d epargne brute des menages | -2.51 | -6.50-1.50 | 41.41 HORS | 42.07 HORS |
| Dette publique / PIB | 154.2 | 134.2-174.2 | 22.57 HORS | 21.29 HORS |
| PIB par habitant (en euros) | 22 480 | 18 000-27 000 | 10 957 HORS | 11 160 HORS |
| Lits d hopital pour 1000 habitants | 4.23 | 3.60-4.90 | 6.02 HORS | 6.03 HORS |
| Medecins pour 1000 habitants | 6.27 | 5.30-7.30 | 8.41 HORS | 8.54 HORS |
| Infirmiers pour 1000 habitants | 2.48 | 2.00-4.20 | 8.52 HORS | 8.65 HORS |
| Hospitalisations pour 1000 habitants par an | 170.0 | 100.0-280.0 | 32.66 HORS | 33.23 HORS |
| Voitures particulieres pour 1000 habitants | 581.0 | 500.0-660.0 | 499.5 HORS | 502.6 dans |
| Morts sur la route par million d habitants | 64.00 | 45.00-85.00 | 106.4 HORS (fragile) | 0.000 HORS (fragile) |
| Electricite consommee par habitant | 4 773 | 4 050-5 500 | 3 155 HORS | 3 099 HORS |
| Eleves par enseignant | 7.40 | 6.00-10.00 | 7.45 dans | 7.43 dans |
| Detenus pour 100 000 habitants | 110.7 | 90.00-130.0 | 45.45 HORS | 68.30 HORS |
| Policiers pour 100 000 habitants | 559.2 | 450.0-670.0 | 2 898 HORS | 2 903 HORS |
| Homicides volontaires pour 100 000 habitants | 0.780 | 0.400-1.20 | 0.000 HORS (fragile) | 0.000 HORS (fragile) |
| Participation aux elections legislatives | 52.80 | 45.00-65.00 | - n.m. | - n.m. |
| Part des personnes logees chez leur menage proprietaire | 69.70 | 64.70-75.70 | 81.41 HORS | 82.45 HORS |

Score avant 14/40 ; apres 16/44.


#### Stratis ( archipel.creer_ile, graine 1, echelle 20, chauffe 40 j, mesure 200 j )

| Indicateur | Reel | Bande | Avant | Apres |
|---|---|---|---|---|
| Part des 0-14 ans | 13.10 | 11.80-14.40 | 13.28 dans | 13.34 dans |
| Part des 15-64 ans | 63.50 | 60.50-66.50 | 77.15 HORS | 77.82 HORS |
| Part des 65 ans et plus | 23.40 | 21.10-25.70 | 9.57 HORS | 8.84 HORS |
| Part des moins de 5 ans | 3.80 | 3.20-4.40 | 0.476 HORS | 0.524 HORS |
| Age median | 46.90 | 44.50-49.30 | 40.09 HORS | 40.13 HORS |
| Rapport de masculinite | 96.06 | 93.00-99.00 | 160.6 HORS | 145.3 HORS |
| Taille moyenne des menages | 2.40 | 2.20-2.60 | 2.06 HORS | 2.08 HORS |
| Taux brut de natalite | 6.60 | 5.60-7.60 | 6.61 dans (fragile) | 6.61 dans (fragile) |
| Taux brut de mortalite | 12.10 | 10.30-13.90 | 372.5 HORS | 241.5 HORS |
| Morts de faim pour 100 000 habitants par an | 0.000 | 0.000-1.00 | (absent) | 23 680 HORS |
| Population vivante sur population de depart (sur un an) | 1.000 | 0.985-1.01 | (absent) | 0.877 HORS |
| Taux d emigration | 0.890 | 0.650-1.10 | (absent) | 1.65 HORS |
| Taux d immigration | 1.21 | 1.00-1.45 | (absent) | 1.19 dans (fragile) |
| Taux d emploi des 20-64 ans | 69.30 | 65.30-73.30 | 80.37 HORS | 62.12 HORS |
| Taux de chomage des 15-74 ans | 10.10 | 7.60-12.60 | 0.647 HORS | 24.82 HORS |
| Part de l emploi public | 15.50 | 12.00-19.00 | 30.17 HORS | 38.01 HORS |
| Part des militaires dans la population | 1.07 | 0.800-1.45 | 9.20 HORS | 9.03 HORS |
| Salaire minimum sur salaire median | 48.70 | 43.70-53.70 | 46.71 dans | 46.71 dans |
| Part de l emploi agricole | 10.97 | 8.50-13.50 | 33.61 HORS | 40.84 HORS |
| Part de l emploi dans l hebergement et la restauration | 9.35 | 7.50-11.20 | 0.000 HORS | 0.000 HORS |
| Part des titulaires d une pension de vieillesse | 19.30 | 16.50-22.10 | 12.90 HORS | 11.86 HORS |
| Part de l alimentation dans le budget des menages | 20.70 | 17.20-24.20 | 28.77 HORS | 28.83 HORS |
| Part du logement dans le budget des menages | 14.40 | 10.90-17.90 | 15.07 dans | 16.02 dans |
| Part du transport dans le budget des menages | 13.30 | 9.80-16.80 | 10.25 dans | 10.38 dans |
| Depense publique totale / PIB | 48.10 | 43.10-53.10 | 81.75 HORS | 81.27 HORS |
| Recettes fiscales et sociales / PIB | 41.70 | 38.20-45.20 | 48.47 HORS | 46.86 HORS |
| Importations de biens et services / PIB | 47.70 | 40.00-55.40 | 25.15 HORS | 25.36 HORS |
| Exportations de biens et services / PIB | 42.10 | 35.00-49.20 | 37.79 dans | 36.89 dans |
| Recettes du tourisme international / PIB | 9.17 | 7.20-11.20 | 27.75 HORS | 26.77 HORS |
| Inflation annuelle | 3.00 | 0.000-6.00 | -15.04 HORS | -10.91 HORS (fragile) |
| Taux d epargne brute des menages | -2.51 | -6.50-1.50 | 45.44 HORS | 45.39 HORS |
| Dette publique / PIB | 154.2 | 134.2-174.2 | 13.60 HORS | 15.12 HORS |
| PIB par habitant (en euros) | 22 480 | 18 000-27 000 | 12 527 HORS | 12 603 HORS |
| Lits d hopital pour 1000 habitants | 4.23 | 3.60-4.90 | 6.46 HORS | 6.04 HORS |
| Medecins pour 1000 habitants | 6.27 | 5.30-7.30 | 8.78 HORS | 8.21 HORS |
| Infirmiers pour 1000 habitants | 2.48 | 2.00-4.20 | 8.05 HORS | 7.87 HORS |
| Hospitalisations pour 1000 habitants par an | 170.0 | 100.0-280.0 | 30.06 HORS | 30.91 HORS |
| Voitures particulieres pour 1000 habitants | 581.0 | 500.0-660.0 | 506.1 dans | 527.5 dans |
| Morts sur la route par million d habitants | 64.00 | 45.00-85.00 | 0.000 HORS (fragile) | 0.000 HORS (fragile) |
| Electricite consommee par habitant | 4 773 | 4 050-5 500 | 2 891 HORS | 2 836 HORS |
| Eleves par enseignant | 7.40 | 6.00-10.00 | 10.51 HORS | 10.71 HORS |
| Detenus pour 100 000 habitants | 110.7 | 90.00-130.0 | 48.78 HORS | 45.60 HORS |
| Policiers pour 100 000 habitants | 559.2 | 450.0-670.0 | 3 366 HORS | 3 227 HORS |
| Homicides volontaires pour 100 000 habitants | 0.780 | 0.400-1.20 | 0.000 HORS (fragile) | 0.000 HORS (fragile) |
| Participation aux elections legislatives | 52.80 | 45.00-65.00 | - n.m. | - n.m. |
| Part des personnes logees chez leur menage proprietaire | 69.70 | 64.70-75.70 | 82.68 HORS | 79.68 HORS |

Score avant 7/40 ; apres 8/44.


#### Flux sur la fenetre de mesure ( series quotidiennes )

| Monde | Jours | Emigres % an | Immigres % an | Morts de faim | Menages sans nourriture ( moyenne ) | Vivants debut -> fin |
|---|---|---|---|---|---|---|
| Altis defaut avant | 90 | 1.54 ( 38 ) | 2.56 ( 63 ) | 120 | 6.3 % | 10018 -> 9926 |
| Altis defaut apres | 90 | 0.85 ( 21 ) | 1.50 ( 37 ) | 5 | 4.7 % | 10010 -> 10029 |
| Altis grec avant | 365 | 1.66 ( 158 ) | 2.14 ( 204 ) | 1199 | 5.7 % | 10000 -> 8800 |
| Altis grec apres | 365 | 1.19 ( 113 ) | 1.17 ( 111 ) | 1160 | 5.7 % | 9995 -> 8785 |
| Stratis avant | 200 | 1.71 ( 88 ) | 1.92 ( 99 ) | 1837 | 12.0 % | 10015 -> 8200 |
| Stratis, generation seule | 200 | 2.01 ( 105 ) | 1.88 ( 98 ) | 1273 | 8.3 % | 10011 -> 8741 |
| Stratis apres | 200 | 1.63 ( 85 ) | 1.17 ( 61 ) | 1218 | 8.4 % | 10003 -> 8771 |
