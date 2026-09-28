# Bulletin annuel : le pays grec ressemble-t-il a la Grece sur une annee ?

Monde : Altis, `demographie="grece"`, `--habitants 6375` ( 10 003 habitants crees ), graine 20260922, les 28 domaines. Chauffe de 40 jours ( les prix demarrent loin de leur equilibre : ils doublent entre les jours 5 et 35 ), puis 365 jours de mesure ( jours 40 a 405, du 25/07/2035 au 24/07/2036 ) : chaque flux est annuel, sans saison a corriger. Mesure du 28/09/2026, branche `iles-metiers-emigration` ( partie du tronc 5077c0a ). « Avant » : le meme monde sur le tronc 5077c0a ; « apres » : avec les migrations du domaine 7 corrigees ( HMT-114 ), les indicateurs de la faim et de la population ( HMT-129 ) et l inflation sur 90 jours et plus ( HMT-128 ). La generation d Altis ne change pas ( HMT-126 b : Altis porte deja ses metiers ).

**Dans la bande : 16 sur 44 indicateurs mesures apres** ( avant : 14 sur 40, sans les 4 indicateurs neufs ). Le tableau complet est plus bas.

## Les migrations sur l annee ( HMT-114 )

| | Avant | Apres | Reel ( ELSTAT 2019 ) |
|---|---|---|---|
| Emigres, % par an | 1.66 ( 158 ) | 1.19 ( 113 ) | 0,89 ( 95 020 pour 10,72 millions ) |
| Immigres, % par an | 2.14 ( 204 ) | 1.17 ( 111 ) | 1,21 ( 129 459 ) |
| Morts de faim pour 100 000 par an | 12 560 ( 1199 ) | 12 187 ( 1160 ) | ~0 |
| Emigres des menages qui ont eu faim dans la semaine / des autres, par adulte expose et par an | - | 5.53 % / 1.13 % ( 28 / 85 ) | - |
| Vivants a la fin / a la naissance | 8800 / 10003 | 8785 / 10003 | 0,9997 par an ( 2024 ) |
| Menages sans nourriture, moyenne du jour | 5.7 % | 5.7 % | - |

Taux sur les personnes-annees de la fenetre de 365 jours ( serie quotidienne de `annee.py` ; la ligne de la ressemblance compte de meme ; les emigres comptent les mineurs qui suivent leurs parents ).

Lecture. L immigration tombe dans la bande. L emigration baisse de 1.66 a 1.19 % par an et reste au-dessus du bord ( 1,10 ) : 28 emigres sur 113 viennent des menages qui ont eu faim dans la semaine, qui ne font que 6 % des jours-adultes. Hors d eux, le taux est d environ 0.97 % par an, pres du reel ( 0,89 ; bande 0,65 - 1,10 ). Le reste de l ecart est la famine du monde, pas le taux de base : le pays perd 1160 habitants de faim dans l annee ( 12 % ), ce que l indicateur « menages sans nourriture » ( 5,7 % des menages habites, les vivants seulement ) ne montrait pas.

Inflation ( HMT-128 ). Sur 365 jours, l indice va de 108,72 a 105,82 ( -2,7 % par an ) ; l intervalle a 95 % d une marche au hasard lue par semaines va de -20,9 a +19,7 % par an : meme une annee ne tranche pas, la ligne est « fragile ». L indice du monde bouge de ~0,5 % par jour ; la mesure ne peut pas dire mieux que le monde.

## Les cinq pires ecarts apres ( en demi-bandes )

- Morts de faim pour 100 000 habitants par an : 12 354 contre 0.000 ( bande 0.000 - 1.00, ecart +12353.6 ) - domaine population
- Taux brut de mortalite : 135.9 contre 12.10 ( bande 10.30 - 13.90, ecart +68.8 ) - domaine population
- Policiers pour 100 000 habitants : 2 903 contre 559.2 ( bande 450.0 - 670.0, ecart +21.1 ) - domaine justice
- Taux d epargne brute des menages : 42.07 contre -2.51 ( bande -6.50 - 1.50, ecart +11.1 ) - domaine economie
- Part de l emploi agricole : 34.44 contre 10.97 ( bande 8.50 - 13.50, ecart +9.3 ) - domaine travail

## Dans la bande apres

Part des 0-14 ans, Part des 15-64 ans, Part des moins de 5 ans, Age median, Rapport de masculinite, Taille moyenne des menages, Taux brut de natalite, Taux d immigration, Part de l emploi public, Salaire minimum sur salaire median, Part du logement dans le budget des menages, Part du transport dans le budget des menages, Recettes fiscales et sociales / PIB, Exportations de biens et services / PIB, Voitures particulieres pour 1000 habitants, Eleves par enseignant.

## Avant et apres, indicateur par indicateur

| Indicateur | Reel | Bande | Avant | Apres |
|---|---|---|---|---|
| Part des 0-14 ans | 13.10 | 11.80 - 14.40 | 11.98 dans | 11.87 dans |
| Part des 15-64 ans | 63.50 | 60.50 - 66.50 | 60.92 dans | 60.93 dans |
| Part des 65 ans et plus | 23.40 | 21.10 - 25.70 | 27.10 HORS | 27.19 HORS |
| Part des moins de 5 ans | 3.80 | 3.20 - 4.40 | 3.43 dans | 3.36 dans |
| Age median | 46.90 | 44.50 - 49.30 | 48.81 dans | 49.17 dans |
| Rapport de masculinite | 96.06 | 93.00 - 99.00 | 93.24 dans | 93.84 dans |
| Taille moyenne des menages | 2.40 | 2.20 - 2.60 | 2.43 dans | 2.43 dans |
| Taux brut de natalite | 6.60 | 5.60 - 7.60 | 7.23 dans (fragile) | 7.24 dans (fragile) |
| Taux brut de mortalite | 12.10 | 10.30 - 13.90 | 139.8 HORS | 135.9 HORS |
| Morts de faim pour 100 000 habitants par an | 0.000 | 0.000 - 1.00 | ( neuf ) | 12 354 HORS |
| Population vivante sur population de depart (sur un an) | 1.000 | 0.985 - 1.01 | ( neuf ) | 0.890 HORS |
| Taux d emigration | 0.890 | 0.650 - 1.10 | ( neuf ) | 1.20 HORS (fragile) |
| Taux d immigration | 1.21 | 1.00 - 1.45 | ( neuf ) | 1.18 dans (fragile) |
| Taux d emploi des 20-64 ans | 69.30 | 65.30 - 73.30 | 79.42 HORS | 80.12 HORS |
| Taux de chomage des 15-74 ans | 10.10 | 7.60 - 12.60 | 0.025 HORS | 0.000 HORS |
| Part de l emploi public | 15.50 | 12.00 - 19.00 | 18.75 dans | 18.66 dans |
| Part des militaires dans la population | 1.07 | 0.800 - 1.45 | 1.61 HORS | 1.61 HORS |
| Salaire minimum sur salaire median | 48.70 | 43.70 - 53.70 | 46.71 dans | 46.71 dans |
| Part de l emploi agricole | 10.97 | 8.50 - 13.50 | 34.54 HORS | 34.44 HORS |
| Part de l emploi dans l hebergement et la restauration | 9.35 | 7.50 - 11.20 | 11.41 HORS | 12.48 HORS |
| Part des titulaires d une pension de vieillesse | 19.30 | 16.50 - 22.10 | 29.15 HORS | 29.22 HORS |
| Part de l alimentation dans le budget des menages | 20.70 | 17.20 - 24.20 | 26.80 HORS | 26.87 HORS |
| Part du logement dans le budget des menages | 14.40 | 10.90 - 17.90 | 13.26 dans | 13.12 dans |
| Part du transport dans le budget des menages | 13.30 | 9.80 - 16.80 | 13.41 dans | 13.59 dans |
| Depense publique totale / PIB | 48.10 | 43.10 - 53.10 | 76.34 HORS | 74.37 HORS |
| Recettes fiscales et sociales / PIB | 41.70 | 38.20 - 45.20 | 39.94 dans | 39.40 dans |
| Importations de biens et services / PIB | 47.70 | 40.00 - 55.40 | 24.76 HORS | 24.41 HORS |
| Exportations de biens et services / PIB | 42.10 | 35.00 - 49.20 | 38.50 dans | 40.00 dans |
| Recettes du tourisme international / PIB | 9.17 | 7.20 - 11.20 | 26.40 HORS | 27.20 HORS |
| Inflation annuelle | 3.00 | 0.000 - 6.00 | -3.14 HORS | -2.67 HORS (fragile) |
| Taux d epargne brute des menages | -2.51 | -6.50 - 1.50 | 41.41 HORS | 42.07 HORS |
| Dette publique / PIB | 154.2 | 134.2 - 174.2 | 22.57 HORS | 21.29 HORS |
| PIB par habitant (en euros) | 22 480 | 18 000 - 27 000 | 10 957 HORS | 11 160 HORS |
| Lits d hopital pour 1000 habitants | 4.23 | 3.60 - 4.90 | 6.02 HORS | 6.03 HORS |
| Medecins pour 1000 habitants | 6.27 | 5.30 - 7.30 | 8.41 HORS | 8.54 HORS |
| Infirmiers pour 1000 habitants | 2.48 | 2.00 - 4.20 | 8.52 HORS | 8.65 HORS |
| Hospitalisations pour 1000 habitants par an | 170.0 | 100.0 - 280.0 | 32.66 HORS | 33.23 HORS |
| Voitures particulieres pour 1000 habitants | 581.0 | 500.0 - 660.0 | 499.5 HORS | 502.6 dans |
| Morts sur la route par million d habitants | 64.00 | 45.00 - 85.00 | 106.4 HORS (fragile) | 0.000 HORS (fragile) |
| Electricite consommee par habitant | 4 773 | 4 050 - 5 500 | 3 155 HORS | 3 099 HORS |
| Eleves par enseignant | 7.40 | 6.00 - 10.00 | 7.45 dans | 7.43 dans |
| Detenus pour 100 000 habitants | 110.7 | 90.00 - 130.0 | 45.45 HORS | 68.30 HORS |
| Policiers pour 100 000 habitants | 559.2 | 450.0 - 670.0 | 2 898 HORS | 2 903 HORS |
| Homicides volontaires pour 100 000 habitants | 0.780 | 0.400 - 1.20 | 0.000 HORS (fragile) | 0.000 HORS (fragile) |
| Participation aux elections legislatives | 52.80 | 45.00 - 65.00 | - n.m. | - n.m. |
| Part des personnes logees chez leur menage proprietaire | 69.70 | 64.70 - 75.70 | 81.41 HORS | 82.45 HORS |

## Le tableau complet apres ( ressemblance.tableau_markdown )

Monde : mode monde, graine 20260922, iles Altis, 10003 habitants crees, demographie grece, 28 domaines. Chauffe 40 jours, mesure 365 jours (jours 40 a 405), 365 clotures suivies.

**Dans la bande : 16 sur 44 indicateurs mesures** (36 %) ; hors bande : 28 ; non mesurables : 1 ; a verifier (hors score) : 1. Sans les 6 verdicts fragiles : 14 sur 38 (37 %).

Ecart : en demi-bandes (0 = la valeur reelle, +-1 = le bord de la bande ; au-dela, hors bande). Surete : « fragile » quand l'intervalle a 95 % d'un flux compte deborde de part et d'autre d'un bord.

| Theme | Indicateur | Unite | Simule | Reel (annee) | Bande | Verdict | Ecart | Surete | Domaine | Mesure |
|---|---|---|---|---|---|---|---|---|---|---|
| demographie | Part des 0-14 ans | % | 11.87 | 13.10 (2024) | 11.80 - 14.40 | dans la bande | -0.9 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Part des 15-64 ans | % | 60.93 | 63.50 (2024) | 60.50 - 66.50 | dans la bande | -0.9 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Part des 65 ans et plus | % | 27.19 | 23.40 (2024) | 21.10 - 25.70 | hors bande | +1.6 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Part des moins de 5 ans | % | 3.36 | 3.80 (2024) | 3.20 - 4.40 | dans la bande | -0.7 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Age median | ans | 49.17 | 46.90 (2024) | 44.50 - 49.30 | dans la bande | +0.9 |  | population | mediane des ages des vivants |
| demographie | Rapport de masculinite | hommes pour 100 femmes | 93.84 | 96.06 (2024) | 93.00 - 99.00 | dans la bande | -0.7 |  | population | 4253 hommes, 4532 femmes vivants |
| demographie | Taille moyenne des menages | personnes | 2.43 | 2.40 (2024) | 2.20 - 2.60 | dans la bande | +0.2 |  | moteur | 8785 vivants dans 3615 menages habites ( au moins un vivant ) |
| demographie | Taux brut de natalite | pour 1000 par an | 7.24 | 6.60 (2024) | 5.60 - 7.60 | dans la bande | +0.6 | fragile ( 68 evenements ) | population | 68 naissances sur 9390.0 personnes-annees |
| demographie | Taux brut de mortalite | pour 1000 par an | 135.9 | 12.10 (2024) | 10.30 - 13.90 | hors bande | +68.8 | sur ( 1276 evenements ) | population | 1276 deces ( toutes causes ) sur 9390.0 personnes-annees |
| demographie | Morts de faim pour 100 000 habitants par an | pour 100 000 par an | 12 354 | 0.000 (2021) | 0.000 - 1.00 | hors bande | +12353.6 | sur ( 1160 evenements ) | population | 1160 morts de faim ( cause faim, domaine 1 ) sur 9390.0 personnes-annees |
| demographie | Population vivante sur population de depart (sur un an) | rapport | 0.890 | 1.000 (2024) | 0.985 - 1.01 | hors bande | -7.5 |  | population | 8785 vivants pour 10003 a la naissance du monde, en 405 jours ( rapport brut 0.8782, ramene a un an ) ; emigres et morts comptent |
| demographie | Taux d emigration | % par an | 1.20 | 0.890 (2019) | 0.650 - 1.10 | hors bande | +1.5 | fragile ( 113 evenements ) | exterieur | 113 emigres ( domaine 7, ext_emigre_j ), mineurs compris sur 9390.0 personnes-annees |
| demographie | Taux d immigration | % par an | 1.18 | 1.21 (2019) | 1.00 - 1.45 | dans la bande | -0.1 | fragile ( 111 evenements ) | exterieur | 111 immigres ( domaine 7, ext_immigre_j ), mineurs compris sur 9390.0 personnes-annees |
| travail | Taux d emploi des 20-64 ans | % | 80.12 | 69.30 (2024) | 65.30 - 73.30 | hors bande | +2.7 |  | travail | 3949 en emploi ( salarie, fonctionnaire, independant ) sur 4929 vivants de 20-64 ans ; les militaires comptent en emploi |
| travail | Taux de chomage des 15-74 ans | % des actifs | 0.000 | 10.10 (2024) | 7.60 - 12.60 | hors bande | -4.0 |  | travail | 0 chomeurs ( statut CHOMEUR ) sur 4062 actifs de 15-74 ans |
| travail | Part de l emploi public | % de l emploi | 18.66 | 15.50 (2023) | 12.00 - 19.00 | dans la bande | +0.9 |  | travail | 758 en emploi dans un metier public du moteur ( config.ROLES ) sur 4062 en emploi |
| travail | Part des militaires dans la population | % de la population | 1.61 | 1.07 (2024) | 0.800 - 1.45 | hors bande | +1.4 |  | armee | 141 vivants aux effectifs de l armee ( ar_rang ) sur 8785 |
| travail | Salaire minimum sur salaire median | % | 46.71 | 48.70 (2024) | 43.70 - 53.70 | dans la bande | -0.4 |  | travail | SMIC horaire brut 4.86 dr sur le taux horaire brut median de 2328 salaries et fonctionnaires ( 10.40 dr ) |
| travail | Part de l emploi agricole | % de l emploi | 34.44 | 10.97 (2024) | 8.50 - 13.50 | hors bande | +9.3 |  | travail | 1399 paysans en emploi sur 4062 |
| travail | Part de l emploi dans l hebergement et la restauration | % de l emploi | 12.48 | 9.35 (2024) | 7.50 - 11.20 | hors bande | +1.7 |  | tourisme | 507 en emploi dans l hotellerie sur 4062 |
| travail | Part des titulaires d une pension de vieillesse | % de la population | 29.22 | 19.30 (2024) | 16.50 - 22.10 | hors bande | +3.5 |  | travail | 2567 vivants titulaires d une pension de vieillesse ( ou de l allocation des non-assures ) sur 8785 |
| economie | Part de l alimentation dans le budget des menages | % de la consommation | 26.87 | 20.70 (2024) | 17.20 - 24.20 | hors bande | +1.8 |  | economie | motifs nourriture / consommation des menages ( TVA comprise ) ; 365 clotures du grand livre |
| economie | Part du logement dans le budget des menages | % de la consommation | 13.12 | 14.40 (2024) | 10.90 - 17.90 | dans la bande | -0.4 |  | economie | motifs loyer, facture_electricite, facture_eau / consommation des menages ( TVA comprise ) ; 365 clotures du grand livre |
| economie | Part du transport dans le budget des menages | % de la consommation | 13.59 | 13.30 (2024) | 9.80 - 16.80 | dans la bande | +0.1 |  | economie | motifs carburant, carburant_station, entretien_vehicule, reparation_vehicule, vente_vehicule, reprise_vehicule, lecons_conduite / consommation des menages ( TVA comprise ) ; 365 clotures du grand livre |
| economie | Depense publique totale / PIB | % du PIB | 74.37 | 48.10 (2024) | 43.10 - 53.10 | hors bande | +5.3 |  | etat | depense consolidee des administrations ( hors financier ) / PIB ( 365 jours de comptes nationaux ) ; 365 clotures du grand livre |
| economie | Recettes fiscales et sociales / PIB | % du PIB | 39.40 | 41.70 (2024) | 38.20 - 45.20 | dans la bande | -0.7 |  | etat | impots et cotisations recus par les administrations / PIB ( 365 jours de comptes nationaux ) ; 365 clotures du grand livre |
| economie | Importations de biens et services / PIB | % du PIB | 24.41 | 47.70 (2024) | 40.00 - 55.40 | hors bande | -3.0 |  | exterieur | importations des comptes nationaux ( domaine 6 ) / PIB, 365 jours |
| economie | Exportations de biens et services / PIB | % du PIB | 40.00 | 42.10 (2024) | 35.00 - 49.20 | dans la bande | -0.3 |  | exterieur | exportations des comptes nationaux ( domaine 6 ) / PIB, 365 jours |
| economie | Recettes du tourisme international / PIB | % du PIB | 27.20 | 9.17 (2024) | 7.20 - 11.20 | hors bande | +8.9 |  | tourisme | recettes touristiques venues de l exterieur ( motif recette_touristique ) / PIB ( 365 jours de comptes nationaux ) ; 365 clotures du grand livre |
| economie | Inflation annuelle | % par an | -2.67 | 3.00 (2024) | 0.000 - 6.00 | hors bande | -1.9 | fragile | banques | indice 108.72 -> 105.82 en 365 jours, annualise ( panier de 4 biens des marches ) ; intervalle a 95 % [-20.9 ; 19.7] ( marche au hasard, semaines entieres ) |
| economie | Taux d epargne brute des menages | % du revenu disponible | 42.07 | -2.51 (2024) | -6.50 - 1.50 | hors bande | +11.1 |  | economie | ( revenu disponible - consommation ) / revenu disponible ; 365 clotures du grand livre |
| economie | Dette publique / PIB | % du PIB | 21.29 | 154.2 (2024) | 134.2 - 174.2 | hors bande | -6.6 |  | etat | dette nominale ( Maastricht, domaine 6 ) / PIB annualise sur 365 jours |
| economie | PIB par habitant (en euros) | euros par habitant | 11 160 | 22 480 (2024) | 18 000 - 27 000 | hors bande | -2.5 |  | etat | PIB annualise ( 365 jours ) par habitant, converti a 1.15 euro la drachme ( pays.EUROS_PAR_DRACHME ) : un MONTANT, le niveau des prix du monde est un choix de calibrage |
| sante | Lits d hopital pour 1000 habitants | pour 1000 | 6.03 | 4.23 (2024) | 3.60 - 4.90 | hors bande | +2.7 |  | hopitaux | 53 lits de 4 etablissements ouverts, dont 2 de reanimation et 11 dans 1 hopitaux militaires ( sans eux : 4.78 ) |
| sante | Medecins pour 1000 habitants | pour 1000 | 8.54 | 6.27 (2024) | 5.30 - 7.30 | hors bande | +2.2 |  | hopitaux | 75 medecins en poste ( role du moteur ) |
| sante | Infirmiers pour 1000 habitants | pour 1000 | 8.65 | 2.48 (2024) | 2.00 - 4.20 | hors bande | +3.6 |  | hopitaux | 76 infirmiers en poste ( role du moteur ) |
| sante | Hospitalisations pour 1000 habitants par an (a verifier) | pour 1000 par an | 33.23 | 170.0 (2015) | 100.0 - 280.0 | hors bande | -2.0 | sur ( 312 evenements ) | hopitaux | 312 sejours admis sur 9390.0 personnes-annees |
| transport | Voitures particulieres pour 1000 habitants | pour 1000 | 502.6 | 581.0 (2024) | 500.0 - 660.0 | dans la bande | -1.0 |  | transport | 4415 voitures des menages habites ( les flottes d entreprise ne sont pas comptees ) |
| transport | Morts sur la route par million d habitants | par million et par an | 0.000 | 64.00 (2024) | 45.00 - 85.00 | hors bande | -3.4 | fragile ( 0 evenements ) | transport | 0 morts de la route ( sur le coup et des suites a l hopital ) sur 9390.0 personnes-annees, sur la fenetre |
| energie | Electricite consommee par habitant | kWh par an | 3 099 | 4 773 (2024) | 4 050 - 5 500 | hors bande | -2.3 |  | energie | 29098398 kWh servis par les reseaux ( tous usages finals, hors pertes ), annualises, sur la fenetre |
| education | Eleves par enseignant | eleves | 7.43 | 7.40 (2024) | 6.00 - 10.00 | dans la bande | +0.0 |  | education | 914 eleves de la maternelle au lycee ( ed_cycle 1-5 ) pour 123 enseignants en poste |
| justice | Detenus pour 100 000 habitants | pour 100 000 | 68.30 | 110.7 (2024) | 90.00 - 130.0 | hors bande | -2.0 |  | justice | 6 detenus vivants ( provisoires et condamnes ) |
| justice | Policiers pour 100 000 habitants | pour 100 000 | 2 903 | 559.2 (2024) | 450.0 - 670.0 | hors bande | +21.1 |  | justice | 255 policiers en poste ( role du moteur ) |
| justice | Homicides volontaires pour 100 000 habitants | pour 100 000 par an | 0.000 | 0.780 (2024) | 0.400 - 1.20 | hors bande | -2.1 | fragile ( 0 evenements ) | justice | 0 homicides ( verite du domaine ) sur 9390.0 personnes-annees, sur la fenetre |
| politique | Participation aux elections legislatives | % des inscrits | - | 52.80 (2023) | 45.00 - 65.00 | non mesurable |  |  |  | aucun scrutin tenu depuis l installation ( prochain prevu au jour 639 ) |
| logement | Part des personnes logees chez leur menage proprietaire | % de la population | 82.45 | 69.70 (2024) | 64.70 - 75.70 | hors bande | +2.1 |  | immobilier | personnes des menages proprietaires de leur logement / personnes des menages habites |

**Les ecarts les plus graves (en demi-bandes)** :

- Morts de faim pour 100 000 habitants par an : 12 354 contre 0.000 (+12353.6) - domaine population
- Taux brut de mortalite : 135.9 contre 12.10 (+68.8) - domaine population
- Policiers pour 100 000 habitants : 2 903 contre 559.2 (+21.1) - domaine justice
- Taux d epargne brute des menages : 42.07 contre -2.51 (+11.1) - domaine economie
- Part de l emploi agricole : 34.44 contre 10.97 (+9.3) - domaine travail
- Recettes du tourisme international / PIB : 27.20 contre 9.17 (+8.9) - domaine tourisme
- Population vivante sur population de depart (sur un an) : 0.890 contre 1.000 (-7.5) - domaine population
- Dette publique / PIB : 21.29 contre 154.2 (-6.6) - domaine etat
- Depense publique totale / PIB : 74.37 contre 48.10 (+5.3) - domaine etat
- Taux de chomage des 15-74 ans : 0.000 contre 10.10 (-4.0) - domaine travail

**Non mesurables** :

- Participation aux elections legislatives : aucun scrutin tenu depuis l installation ( prochain prevu au jour 639 )

