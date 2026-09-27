# Ressemblance a la Grece : autoconsommation_avant

Monde : graine 20260922, iles Altis, 10026 habitants crees ( 10000 demandes ), domaines tous (28), demographie du moteur. Chauffe 5 jours, mesure 30 jours (jours 5 a 35, du 20/06/2035 au 20/07/2035), 30 clotures suivies. Les references sont ANNUELLES : une fenetre d ete surestime les flux saisonniers (tourisme, emploi d ete, climatisation) et la ligne reste a lire avec sa saison. Installation 10.6 s ; 2.81 s par jour ; mesure 10 ms.

References : `references/grece.json` (ecrites avant la mesure). Commande : `python -m monde.ressemblance --habitants 10000 --jours 30 --chauffe 5 --domaines tous --etiquette autoconsommation_avant`

**Dans la bande : 10 sur 40 indicateurs mesures** (25 %) ; hors bande : 30 ; non mesurables : 1 ; a verifier (hors score) : 1. Sans les 4 verdicts fragiles : 8 sur 36 (22 %).

Ecart : en demi-bandes (0 = la valeur reelle, +-1 = le bord de la bande ; au-dela, hors bande). Surete : « fragile » quand l'intervalle a 95 % d'un flux compte deborde de part et d'autre d'un bord.

| Theme | Indicateur | Unite | Simule | Reel (annee) | Bande | Verdict | Ecart | Surete | Domaine | Mesure |
|---|---|---|---|---|---|---|---|---|---|---|
| demographie | Part des 0-14 ans | % | 14.71 | 13.10 (2024) | 11.80 - 14.40 | hors bande | +1.2 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Part des 15-64 ans | % | 78.43 | 63.50 (2024) | 60.50 - 66.50 | hors bande | +5.0 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Part des 65 ans et plus | % | 6.87 | 23.40 (2024) | 21.10 - 25.70 | hors bande | -7.2 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Part des moins de 5 ans | % | 0.060 | 3.80 (2024) | 3.20 - 4.40 | hors bande | -6.2 |  | population | vivants ; etat civil ( naissance_j ) |
| demographie | Age median | ans | 38.60 | 46.90 (2024) | 44.50 - 49.30 | hors bande | -3.5 |  | population | mediane des ages des vivants |
| demographie | Rapport de masculinite | hommes pour 100 femmes | 197.2 | 96.06 (2024) | 93.00 - 99.00 | hors bande | +34.4 |  | population | 6647 hommes, 3370 femmes vivants |
| demographie | Taille moyenne des menages | personnes | 1.88 | 2.40 (2024) | 2.20 - 2.60 | hors bande | -2.6 |  | moteur | 10017 vivants dans 5315 menages habites ( au moins un vivant ) |
| demographie | Taux brut de natalite | pour 1000 par an | 7.29 | 6.60 (2024) | 5.60 - 7.60 | dans la bande | +0.7 | fragile ( 6 evenements ) | population | 6 naissances sur 823.0 personnes-annees |
| demographie | Taux brut de mortalite | pour 1000 par an | 10.94 | 12.10 (2024) | 10.30 - 13.90 | dans la bande | -0.6 | fragile ( 9 evenements ) | population | 9 deces ( toutes causes ) sur 823.0 personnes-annees |
| travail | Taux d emploi des 20-64 ans | % | 81.90 | 69.30 (2024) | 65.30 - 73.30 | hors bande | +3.1 |  | travail | 5995 en emploi ( salarie, fonctionnaire, independant ) sur 7320 vivants de 20-64 ans ; les militaires comptent en emploi |
| travail | Taux de chomage des 15-74 ans | % des actifs | 1.95 | 10.10 (2024) | 7.60 - 12.60 | hors bande | -3.3 |  | travail | 120 chomeurs ( statut CHOMEUR ) sur 6151 actifs de 15-74 ans |
| travail | Part de l emploi public | % de l emploi | 26.79 | 15.50 (2023) | 12.00 - 19.00 | hors bande | +3.2 |  | travail | 1616 en emploi dans un metier public du moteur ( config.ROLES ) sur 6031 en emploi |
| travail | Part des militaires dans la population | % de la population | 9.33 | 1.07 (2024) | 0.800 - 1.45 | hors bande | +21.7 |  | armee | 935 vivants aux effectifs de l armee ( ar_rang ) sur 10017 |
| travail | Salaire minimum sur salaire median | % | 46.71 | 48.70 (2024) | 43.70 - 53.70 | dans la bande | -0.4 |  | travail | SMIC horaire brut 4.86 dr sur le taux horaire brut median de 4019 salaries et fonctionnaires ( 10.40 dr ) |
| travail | Part de l emploi agricole | % de l emploi | 26.58 | 10.97 (2024) | 8.50 - 13.50 | hors bande | +6.2 |  | travail | 1603 paysans en emploi sur 6031 |
| travail | Part de l emploi dans l hebergement et la restauration | % de l emploi | 11.49 | 9.35 (2024) | 7.50 - 11.20 | hors bande | +1.2 |  | tourisme | 693 en emploi dans l hotellerie sur 6031 |
| travail | Part des titulaires d une pension de vieillesse | % de la population | 9.74 | 19.30 (2024) | 16.50 - 22.10 | hors bande | -3.4 |  | travail | 976 vivants titulaires d une pension de vieillesse ( ou de l allocation des non-assures ) sur 10017 |
| economie | Part de l alimentation dans le budget des menages | % de la consommation | 36.08 | 20.70 (2024) | 17.20 - 24.20 | hors bande | +4.4 |  | economie | motifs nourriture / consommation des menages ( TVA comprise ) ; 30 clotures du grand livre |
| economie | Part du logement dans le budget des menages | % de la consommation | 11.80 | 14.40 (2024) | 10.90 - 17.90 | dans la bande | -0.7 |  | economie | motifs loyer, facture_electricite, facture_eau / consommation des menages ( TVA comprise ) ; 30 clotures du grand livre |
| economie | Part du transport dans le budget des menages | % de la consommation | 6.76 | 13.30 (2024) | 9.80 - 16.80 | hors bande | -1.9 |  | economie | motifs carburant, carburant_station, entretien_vehicule, reparation_vehicule, vente_vehicule, reprise_vehicule, lecons_conduite / consommation des menages ( TVA comprise ) ; 30 clotures du grand livre |
| economie | Depense publique totale / PIB | % du PIB | 49.75 | 48.10 (2024) | 43.10 - 53.10 | dans la bande | +0.3 |  | etat | depense consolidee des administrations ( hors financier ) / PIB ( 30 jours de comptes nationaux ) ; 30 clotures du grand livre |
| economie | Recettes fiscales et sociales / PIB | % du PIB | 43.31 | 41.70 (2024) | 38.20 - 45.20 | dans la bande | +0.5 |  | etat | impots et cotisations recus par les administrations / PIB ( 30 jours de comptes nationaux ) ; 30 clotures du grand livre |
| economie | Importations de biens et services / PIB | % du PIB | 34.22 | 47.70 (2024) | 40.00 - 55.40 | hors bande | -1.8 |  | exterieur | importations des comptes nationaux ( domaine 6 ) / PIB, 30 jours |
| economie | Exportations de biens et services / PIB | % du PIB | 56.88 | 42.10 (2024) | 35.00 - 49.20 | hors bande | +2.1 |  | exterieur | exportations des comptes nationaux ( domaine 6 ) / PIB, 30 jours |
| economie | Recettes du tourisme international / PIB | % du PIB | 38.04 | 9.17 (2024) | 7.20 - 11.20 | hors bande | +14.2 |  | tourisme | recettes touristiques venues de l exterieur ( motif recette_touristique ) / PIB ( 30 jours de comptes nationaux ) ; 30 clotures du grand livre |
| economie | Inflation annuelle | % par an | 270 626 | 3.00 (2024) | 0.000 - 6.00 | hors bande | +90207.6 |  | banques | indice 105.02 -> 201.10 en 30 jours, annualise ( panier de 4 biens des marches ) |
| economie | Taux d epargne brute des menages | % du revenu disponible | 35.37 | -2.51 (2024) | -6.50 - 1.50 | hors bande | +9.4 |  | economie | ( revenu disponible - consommation ) / revenu disponible ; 30 clotures du grand livre |
| economie | Dette publique / PIB | % du PIB | 2.33 | 154.2 (2024) | 134.2 - 174.2 | hors bande | -7.6 |  | etat | dette nominale ( Maastricht, domaine 6 ) / PIB annualise sur 30 jours |
| economie | PIB par habitant (en euros) | euros par habitant | 18 825 | 22 480 (2024) | 18 000 - 27 000 | dans la bande | -0.8 |  | etat | PIB annualise ( 30 jours ) par habitant, converti a 1.15 euro la drachme ( pays.EUROS_PAR_DRACHME ) : un MONTANT, le niveau des prix du monde est un choix de calibrage |
| sante | Lits d hopital pour 1000 habitants | pour 1000 | 5.29 | 4.23 (2024) | 3.60 - 4.90 | hors bande | +1.6 |  | hopitaux | 53 lits de 4 etablissements ouverts, dont 2 de reanimation et 11 dans 1 hopitaux militaires ( sans eux : 4.19 ) |
| sante | Medecins pour 1000 habitants | pour 1000 | 7.49 | 6.27 (2024) | 5.30 - 7.30 | hors bande | +1.2 |  | hopitaux | 75 medecins en poste ( role du moteur ) |
| sante | Infirmiers pour 1000 habitants | pour 1000 | 6.69 | 2.48 (2024) | 2.00 - 4.20 | hors bande | +2.4 |  | hopitaux | 67 infirmiers en poste ( role du moteur ) |
| sante | Hospitalisations pour 1000 habitants par an (a verifier) | pour 1000 par an | 35.24 | 170.0 (2015) | 100.0 - 280.0 | hors bande | -1.9 | sur ( 29 evenements ) | hopitaux | 29 sejours admis sur 823.0 personnes-annees |
| transport | Voitures particulieres pour 1000 habitants | pour 1000 | 551.3 | 581.0 (2024) | 500.0 - 660.0 | dans la bande | -0.4 |  | transport | 5522 voitures des menages habites ( les flottes d entreprise ne sont pas comptees ) |
| transport | Morts sur la route par million d habitants | par million et par an | 0.000 | 64.00 (2024) | 45.00 - 85.00 | hors bande | -3.4 | fragile ( 0 evenements ) | transport | 0 morts de la route ( sur le coup et des suites a l hopital ) sur 823.0 personnes-annees, sur la fenetre |
| energie | Electricite consommee par habitant | kWh par an | 3 444 | 4 773 (2024) | 4 050 - 5 500 | hors bande | -1.8 |  | energie | 2834212 kWh servis par les reseaux ( tous usages finals, hors pertes ), annualises, sur la fenetre |
| education | Eleves par enseignant | eleves | 16.41 | 7.40 (2024) | 6.00 - 10.00 | hors bande | +3.5 |  | education | 1821 eleves de la maternelle au lycee ( ed_cycle 1-5 ) pour 111 enseignants en poste |
| justice | Detenus pour 100 000 habitants | pour 100 000 | 99.83 | 110.7 (2024) | 90.00 - 130.0 | dans la bande | -0.5 |  | justice | 10 detenus vivants ( provisoires et condamnes ) |
| justice | Policiers pour 100 000 habitants | pour 100 000 | 2 875 | 559.2 (2024) | 450.0 - 670.0 | hors bande | +20.9 |  | justice | 288 policiers en poste ( role du moteur ) |
| justice | Homicides volontaires pour 100 000 habitants | pour 100 000 par an | 0.000 | 0.780 (2024) | 0.400 - 1.20 | hors bande | -2.1 | fragile ( 0 evenements ) | justice | 0 homicides ( verite du domaine ) sur 823.0 personnes-annees, sur la fenetre |
| politique | Participation aux elections legislatives | % des inscrits | - | 52.80 (2023) | 45.00 - 65.00 | non mesurable |  |  |  | aucun scrutin tenu depuis l installation ( prochain prevu au jour 639 ) |
| logement | Part des personnes logees chez leur menage proprietaire | % de la population | 73.33 | 69.70 (2024) | 64.70 - 75.70 | dans la bande | +0.6 |  | immobilier | personnes des menages proprietaires de leur logement / personnes des menages habites |

**Les ecarts les plus graves (en demi-bandes)** :

- Inflation annuelle : 270 626 contre 3.00 (+90207.6) - domaine banques
- Rapport de masculinite : 197.2 contre 96.06 (+34.4) - domaine population
- Part des militaires dans la population : 9.33 contre 1.07 (+21.7) - domaine armee
- Policiers pour 100 000 habitants : 2 875 contre 559.2 (+20.9) - domaine justice
- Recettes du tourisme international / PIB : 38.04 contre 9.17 (+14.2) - domaine tourisme
- Taux d epargne brute des menages : 35.37 contre -2.51 (+9.4) - domaine economie
- Dette publique / PIB : 2.33 contre 154.2 (-7.6) - domaine etat
- Part des 65 ans et plus : 6.87 contre 23.40 (-7.2) - domaine population
- Part des moins de 5 ans : 0.060 contre 3.80 (-6.2) - domaine population
- Part de l emploi agricole : 26.58 contre 10.97 (+6.2) - domaine travail

**Non mesurables** :

- Participation aux elections legislatives : aucun scrutin tenu depuis l installation ( prochain prevu au jour 639 )
