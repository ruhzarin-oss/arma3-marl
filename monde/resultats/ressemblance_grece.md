# Ressemblance a la Grece : grece

Monde : graine 20260922, iles Altis, 10029 habitants crees ( 6375 demandes ), domaines tous (28), demographie grece. Chauffe 5 jours, mesure 30 jours (jours 5 a 35, du 20/06/2035 au 20/07/2035), 30 clotures suivies. Les references sont ANNUELLES : une fenetre d ete surestime les flux saisonniers (tourisme, emploi d ete, climatisation) et la ligne reste a lire avec sa saison. Installation 6.0 s ; 1.89 s par jour ; mesure 12 ms.

References : `references/grece.json` (ecrites avant la mesure). Commande : `python -m monde.ressemblance --habitants 6375 --jours 30 --chauffe 5 --domaines tous --demographie grece --etiquette grece`

**Dans la bande : 15 sur 40 indicateurs mesures** (38 %) ; hors bande : 25 ; non mesurables : 1 ; a verifier (hors score) : 1. Sans les 4 verdicts fragiles : 14 sur 36 (39 %).

Ecart : en demi-bandes (0 = la valeur reelle, +-1 = le bord de la bande ; au-dela, hors bande). Surete : « fragile » quand l'intervalle a 95 % d'un flux compte deborde de part et d'autre d'un bord.

| Theme | Indicateur | Unite | Simule | Reel (annee) | Bande | Verdict | Ecart | Surete | Domaine | Mesure |
|---|---|---|---|---|---|---|---|---|---|---|
| demographie | Part des 0-14 ans | % | 13.08 | 13.10 (2024) | 11.80 - 14.40 | dans la bande | -0.0 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Part des 15-64 ans | % | 63.48 | 63.50 (2024) | 60.50 - 66.50 | dans la bande | -0.0 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Part des 65 ans et plus | % | 23.45 | 23.40 (2024) | 21.10 - 25.70 | dans la bande | +0.0 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Part des moins de 5 ans | % | 3.82 | 3.80 (2024) | 3.20 - 4.40 | dans la bande | +0.0 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Age median | ans | 46.81 | 46.90 (2024) | 44.50 - 49.30 | dans la bande | -0.0 |  | population | mediane des ages des vivants |
| demographie | Rapport de masculinite | hommes pour 100 femmes | 95.89 | 96.06 (2024) | 93.00 - 99.00 | dans la bande | -0.1 |  | population | 4896 hommes, 5106 femmes vivants |
| demographie | Taille moyenne des menages | personnes | 2.40 | 2.40 (2024) | 2.20 - 2.60 | dans la bande | -0.0 |  | moteur | 10002 vivants dans 4169 menages habites ( au moins un vivant ) |
| demographie | Taux brut de natalite | pour 1000 par an | 6.08 | 6.60 (2024) | 5.60 - 7.60 | dans la bande | -0.5 | fragile ( 5 evenements ) | population | 5 naissances sur 822.0 personnes-annees |
| demographie | Taux brut de mortalite | pour 1000 par an | 9.73 | 12.10 (2024) | 10.30 - 13.90 | hors bande | -1.3 | fragile ( 8 evenements ) | population | 8 deces ( toutes causes ) sur 822.0 personnes-annees |
| travail | Taux d emploi des 20-64 ans | % | 77.94 | 69.30 (2024) | 65.30 - 73.30 | hors bande | +2.2 |  | travail | 4540 en emploi ( salarie, fonctionnaire, independant ) sur 5825 vivants de 20-64 ans ; les militaires comptent en emploi |
| travail | Taux de chomage des 15-74 ans | % des actifs | 0.000 | 10.10 (2024) | 7.60 - 12.60 | hors bande | -4.0 |  | travail | 0 chomeurs ( statut CHOMEUR ) sur 4664 actifs de 15-74 ans |
| travail | Part de l emploi public | % de l emploi | 16.92 | 15.50 (2023) | 12.00 - 19.00 | dans la bande | +0.4 |  | travail | 789 en emploi dans un metier public du moteur ( config.ROLES ) sur 4664 en emploi |
| travail | Part des militaires dans la population | % de la population | 1.82 | 1.07 (2024) | 0.800 - 1.45 | hors bande | +2.0 |  | armee | 182 vivants aux effectifs de l armee ( ar_rang ) sur 10002 |
| travail | Salaire minimum sur salaire median | % | 46.71 | 48.70 (2024) | 43.70 - 53.70 | dans la bande | -0.4 |  | travail | SMIC horaire brut 4.86 dr sur le taux horaire brut median de 2918 salaries et fonctionnaires ( 10.40 dr ) |
| travail | Part de l emploi agricole | % de l emploi | 29.85 | 10.97 (2024) | 8.50 - 13.50 | hors bande | +7.5 |  | travail | 1392 paysans en emploi sur 4664 |
| travail | Part de l emploi dans l hebergement et la restauration | % de l emploi | 12.86 | 9.35 (2024) | 7.50 - 11.20 | hors bande | +1.9 |  | tourisme | 600 en emploi dans l hotellerie sur 4664 |
| travail | Part des titulaires d une pension de vieillesse | % de la population | 25.74 | 19.30 (2024) | 16.50 - 22.10 | hors bande | +2.3 |  | travail | 2575 vivants titulaires d une pension de vieillesse ( ou de l allocation des non-assures ) sur 10002 |
| economie | Part de l alimentation dans le budget des menages | % de la consommation | 40.74 | 20.70 (2024) | 17.20 - 24.20 | hors bande | +5.7 |  | economie | motifs nourriture / consommation des menages ( TVA comprise ) ; 30 clotures du grand livre |
| economie | Part du logement dans le budget des menages | % de la consommation | 8.93 | 14.40 (2024) | 10.90 - 17.90 | hors bande | -1.6 |  | economie | motifs loyer, facture_electricite, facture_eau / consommation des menages ( TVA comprise ) ; 30 clotures du grand livre |
| economie | Part du transport dans le budget des menages | % de la consommation | 9.17 | 13.30 (2024) | 9.80 - 16.80 | hors bande | -1.2 |  | economie | motifs carburant, carburant_station, entretien_vehicule, reparation_vehicule, vente_vehicule, reprise_vehicule, lecons_conduite / consommation des menages ( TVA comprise ) ; 30 clotures du grand livre |
| economie | Depense publique totale / PIB | % du PIB | 49.00 | 48.10 (2024) | 43.10 - 53.10 | dans la bande | +0.2 |  | etat | depense consolidee des administrations ( hors financier ) / PIB ( 30 jours de comptes nationaux ) ; 30 clotures du grand livre |
| economie | Recettes fiscales et sociales / PIB | % du PIB | 42.09 | 41.70 (2024) | 38.20 - 45.20 | dans la bande | +0.1 |  | etat | impots et cotisations recus par les administrations / PIB ( 30 jours de comptes nationaux ) ; 30 clotures du grand livre |
| economie | Importations de biens et services / PIB | % du PIB | 33.54 | 47.70 (2024) | 40.00 - 55.40 | hors bande | -1.8 |  | exterieur | importations des comptes nationaux ( domaine 6 ) / PIB, 30 jours |
| economie | Exportations de biens et services / PIB | % du PIB | 62.09 | 42.10 (2024) | 35.00 - 49.20 | hors bande | +2.8 |  | exterieur | exportations des comptes nationaux ( domaine 6 ) / PIB, 30 jours |
| economie | Recettes du tourisme international / PIB | % du PIB | 42.22 | 9.17 (2024) | 7.20 - 11.20 | hors bande | +16.3 |  | tourisme | recettes touristiques venues de l exterieur ( motif recette_touristique ) / PIB ( 30 jours de comptes nationaux ) ; 30 clotures du grand livre |
| economie | Inflation annuelle | % par an | 279 204 | 3.00 (2024) | 0.000 - 6.00 | hors bande | +93067.0 |  | banques | indice 104.14 -> 199.93 en 30 jours, annualise ( panier de 4 biens des marches ) |
| economie | Taux d epargne brute des menages | % du revenu disponible | 37.25 | -2.51 (2024) | -6.50 - 1.50 | hors bande | +9.9 |  | economie | ( revenu disponible - consommation ) / revenu disponible ; 30 clotures du grand livre |
| economie | Dette publique / PIB | % du PIB | 2.76 | 154.2 (2024) | 134.2 - 174.2 | hors bande | -7.6 |  | etat | dette nominale ( Maastricht, domaine 6 ) / PIB annualise sur 30 jours |
| economie | PIB par habitant (en euros) | euros par habitant | 15 905 | 22 480 (2024) | 18 000 - 27 000 | hors bande | -1.5 |  | etat | PIB annualise ( 30 jours ) par habitant, converti a 1.15 euro la drachme ( pays.EUROS_PAR_DRACHME ) : un MONTANT, le niveau des prix du monde est un choix de calibrage |
| sante | Lits d hopital pour 1000 habitants | pour 1000 | 5.30 | 4.23 (2024) | 3.60 - 4.90 | hors bande | +1.6 |  | hopitaux | 53 lits de 4 etablissements ouverts, dont 2 de reanimation et 11 dans 1 hopitaux militaires ( sans eux : 4.20 ) |
| sante | Medecins pour 1000 habitants | pour 1000 | 7.60 | 6.27 (2024) | 5.30 - 7.30 | hors bande | +1.3 |  | hopitaux | 76 medecins en poste ( role du moteur ) |
| sante | Infirmiers pour 1000 habitants | pour 1000 | 7.60 | 2.48 (2024) | 2.00 - 4.20 | hors bande | +3.0 |  | hopitaux | 76 infirmiers en poste ( role du moteur ) |
| sante | Hospitalisations pour 1000 habitants par an (a verifier) | pour 1000 par an | 45.01 | 170.0 (2015) | 100.0 - 280.0 | hors bande | -1.8 | sur ( 37 evenements ) | hopitaux | 37 sejours admis sur 822.0 personnes-annees |
| transport | Voitures particulieres pour 1000 habitants | pour 1000 | 547.4 | 581.0 (2024) | 500.0 - 660.0 | dans la bande | -0.4 |  | transport | 5475 voitures des menages habites ( les flottes d entreprise ne sont pas comptees ) |
| transport | Morts sur la route par million d habitants | par million et par an | 0.000 | 64.00 (2024) | 45.00 - 85.00 | hors bande | -3.4 | fragile ( 0 evenements ) | transport | 0 morts de la route ( sur le coup et des suites a l hopital ) sur 822.0 personnes-annees, sur la fenetre |
| energie | Electricite consommee par habitant | kWh par an | 3 388 | 4 773 (2024) | 4 050 - 5 500 | hors bande | -1.9 |  | energie | 2784841 kWh servis par les reseaux ( tous usages finals, hors pertes ), annualises, sur la fenetre |
| education | Eleves par enseignant | eleves | 10.57 | 7.40 (2024) | 6.00 - 10.00 | hors bande | +1.2 |  | education | 1205 eleves de la maternelle au lycee ( ed_cycle 1-5 ) pour 114 enseignants en poste |
| justice | Detenus pour 100 000 habitants | pour 100 000 | 99.98 | 110.7 (2024) | 90.00 - 130.0 | dans la bande | -0.5 |  | justice | 10 detenus vivants ( provisoires et condamnes ) |
| justice | Policiers pour 100 000 habitants | pour 100 000 | 2 519 | 559.2 (2024) | 450.0 - 670.0 | hors bande | +17.7 |  | justice | 252 policiers en poste ( role du moteur ) |
| justice | Homicides volontaires pour 100 000 habitants | pour 100 000 par an | 0.000 | 0.780 (2024) | 0.400 - 1.20 | hors bande | -2.1 | fragile ( 0 evenements ) | justice | 0 homicides ( verite du domaine ) sur 822.0 personnes-annees, sur la fenetre |
| politique | Participation aux elections legislatives | % des inscrits | - | 52.80 (2023) | 45.00 - 65.00 | non mesurable |  |  |  | aucun scrutin tenu depuis l installation ( prochain prevu au jour 639 ) |
| logement | Part des personnes logees chez leur menage proprietaire | % de la population | 73.32 | 69.70 (2024) | 64.70 - 75.70 | dans la bande | +0.6 |  | immobilier | personnes des menages proprietaires de leur logement / personnes des menages habites |

**Les ecarts les plus graves (en demi-bandes)** :

- Inflation annuelle : 279 204 contre 3.00 (+93067.0) - domaine banques
- Policiers pour 100 000 habitants : 2 519 contre 559.2 (+17.7) - domaine justice
- Recettes du tourisme international / PIB : 42.22 contre 9.17 (+16.3) - domaine tourisme
- Taux d epargne brute des menages : 37.25 contre -2.51 (+9.9) - domaine economie
- Dette publique / PIB : 2.76 contre 154.2 (-7.6) - domaine etat
- Part de l emploi agricole : 29.85 contre 10.97 (+7.5) - domaine travail
- Part de l alimentation dans le budget des menages : 40.74 contre 20.70 (+5.7) - domaine economie
- Taux de chomage des 15-74 ans : 0.000 contre 10.10 (-4.0) - domaine travail
- Morts sur la route par million d habitants : 0.000 contre 64.00 (-3.4) - domaine transport
- Infirmiers pour 1000 habitants : 7.60 contre 2.48 (+3.0) - domaine hopitaux

**Non mesurables** :

- Participation aux elections legislatives : aucun scrutin tenu depuis l installation ( prochain prevu au jour 639 )
