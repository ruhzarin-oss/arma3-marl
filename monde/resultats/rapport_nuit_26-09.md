# Nuit du 25 au 26 septembre : ce qui a ete trouve, repare, verifie

## Repare ( chaque correction : ses portes, un controle positif, un commit )
1. **Memoire** ( 86dd806 ) : borne de 2 horizons sur les choix en attente, journal du moteur a 200 000 evenements.
   Mon premier diagnostic ( « ateliers vides » ) etait faux : la file d entretien monte puis plafonne vers 45.
2. **Enregistreur** ( 8656b6e, 7fab129 ) : TOUT en Parquet ( paiements, biens, choix, notes, evenements, photos du soir
   des habitants, menages, marches, entreprises, Etat ). ~75 Mo par ile et par jour a un million. Lecture : pyarrow
   ( DuckDB n est pas installe : a installer si tu le veux ).
3. **Faim, cause 1** ( 06d3d50 ) : une commande publique non servie etait recomptee comme demande a chaque heure ->
   demande de carburant x13 000, pas d import, pas de camion, recoltes bloquees aux fermes.
4. **Faim, cause 2** ( 87dfca5, a7ad896 ) : stocks, caisse et fonds de roulement des marches fixes ( faits pour 167
   habitants par marche ) -> proportionnels a la population servie ( moteur ET domaine du travail ).

## Resultat a un million d habitants par pays ( 6 pays, Qwen )
| | nuit du 25 ( ancien code ) | nuit du 26 ( code 7fab129 ) |
|---|---|---|
| faim jours 3-4 | 71 a 73 % | 2 a 3 % |
| conservation | tenue | tenue |

## Decisions prises a ta place ( « copier le reel » )
- Stocks et caisse d un marche proportionnels a sa population ( un pays reel demarre avec ses stations pleines ).
- Une commande publique = une demande ( un bon de commande ne se recompte pas chaque heure ).

## A trancher par toi
- Deux portes du pays de plus en echec depuis les corrections : `economie.test_credit` ( mise en scene : la
  pharmacie videe demande au jour 5, pas 4 ), `immobilier.test_decision_loyer` ( p 0,060 pour 0,05 ). Pays 132/145.
- Les dettes impayees ( loyer, taxe locale, salaires ) grossissent sans fin : prescription ? faillite personnelle ?
- Le garde-manger vise 1,5 jour : un jour d approvisionnement rate donne des creux de faim ponctuels.
- Les references des portes sont hors du depot : `/mnt/data/hmt/ref_domaines.json` ( v4 ) et l ancien moteur temoin
  `/mnt/data/hmt/ref/monde_ancien` ( corrige des memes lignes, sauvegardes a cote ).
