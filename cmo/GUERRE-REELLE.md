# La guerre réelle dans CMO ( 02/10/2026 )

Demande de Younes : un agent qui gère CMO dans son ensemble, OTAN contre Russie-Chine, « la totale, troupes au sol, tout
ce qu'offre CMO », branché palier par palier avec des informations réelles. « Que du réel, on ne joue plus » : plus de
drapeaux, de score ni de QG à prendre ; la guerre avance par ce qui est DÉTRUIT.

## Principes

1. **CMO simule, le moteur décide.** CMO calcule capteurs, tirs, dégâts, carburant, réparations. Le moteur ( l'agent et sa
   chaîne de commandement ) décide des achats, des stocks, des missions et des cibles, par des OUTILS du pont testés hors
   jeu ; jamais de Lua libre.
2. **Tout vient du réel.** Types, armes et capteurs : base DB3000 de CMO. Installations : les 3 879 modèles livrés avec CMO
   ( `ImportExport/<pays>/*.inst` ). Budgets : SIPRI. Quantités : bilans publics du type Military Balance. Prix : ordres de
   grandeur publics. Tout chiffre saisi de mémoire est listé plus bas, à valider par Younes.
3. **La destruction fait la guerre.** Une base vaut ce que valent ses éléments : pistes, accès, abris, dépôts de munitions,
   carburant, radars, défense sol-air. Sans piste, pas de décollage ; sans dépôt plein, pas de réarmement. La réparation
   prend le temps et le coût réels. La guerre finit quand un camp ne peut plus combattre, ou quand le moteur dit que sa
   volonté cède ( pertes, économie, population ).
4. **Le brouillard de guerre.** Chaque chef ne voit que les contacts de son camp, jamais la vérité de CMO.
5. **Un palier n'avance qu'avec son verdict** : porte hors jeu ( faux_cmo, avec mutants qui doivent la faire échouer ),
   puis 6 h dans le vrai CMO, critères écrits d'avance. On ne modifie jamais une guerre en cours.

## Ce que la guerre du 29/09 a appris

- Les aérodromes génériques ( 1712, 1877, 1592 ) ET les vrais dépôts ( Ammo Bunker 322 / 325, Ammo Revetment 320 ) ont un
  magasin « Munitions » VIDE dans la base ( magasin 1185, capacité 10 000 ) : un avion posé ne se réarme jamais. Les
  stocks de munitions sont donc à acheter et à livrer, comme dans le réel.
- Une règle de présence ( un avion seul dans le ciel ) n'existe pas dans le réel : abandonnée.

## Les paliers

| Palier | Contenu | Données réelles |
| --- | --- | --- |
| 0 | Réparer : magasins remplis et payés, rotation rapide, seuils de retour ; sondes : magasins, doctrine, contacts, import d'une vraie base, unité au sol | DB3000, prix des munitions |
| 1 | Vraies bases : import des modèles ImportExport ( OTAN, Biélorussie ) ; bases russes montées élément par élément aux vraies coordonnées ; état d'une base = ses éléments vivants | ImportExport, DB3000 |
| 2 | Toute l'aviation : chasse, attaque, radars volants, ravitailleurs ; chargements par mission ; stocks par dépôt | DB3000, quantités réelles |
| 3 | Frappes et suppression des défenses ( SEAD/DEAD ) : missions Strike, bombes, missiles de croisière et balistiques ( Iskander, Kalibr, Tomahawk ), stocks et cadence de production réels | DB3000, production annuelle |
| 4 | Défense sol-air et radars : Patriot, SAMP/T, NASAMS, S-400, Buk, Pantsir, sur leurs vrais sites | ImportExport, DB3000 |
| 5 | Troupes au sol : brigades et divisions réelles ( 11e corps d'armée à Kaliningrad, brigades polonaises, groupements de l'OTAN dans les pays baltes ), artillerie, mouvements sur le terrain de CMO | DB3000 ( véhicules ), ordres de bataille publics |
| 6 | Marine : flottes réelles, ports, missiles antinavires, sous-marins, lutte anti-sous-marine, mines | DB3000, ImportExport |
| 7 | Logistique : carburant, convois de munitions, cargo, réparation des pistes ; l'économie du moteur nourrit la guerre et la guerre vide l'économie | moteur du monde |
| 8 | Soutien : guerre électronique, satellites, communications, cyber, météo, jour et nuit | DB3000, CMO |
| 9 | Plusieurs théâtres à la fois, après un banc de charge ( combien d'unités CMO tient en temps réel ) | — |

## L'agent

Une chaîne de commandement plutôt qu'un agent unique : chef d'État par pays ( budget, alliances, escalade ), commandant
de théâtre, chefs air, mer, sol, défense sol-air. Chacun lit ses contacts, décide par ses outils, avec les délais réels
( ordre de mission aérienne préparé à l'avance, renseignement en retard, règles d'engagement, alliés qui peuvent refuser ).
Le conseil de Qwen tient les décisions politiques. Les pertes et munitions consommées remontent à l'économie du moteur.

## Choix « copiés du réel », à valider par Younes

- Théâtre Baltique : pays engagés et part de leur budget ( theatres/baltique.py ) ; budgets SIPRI 2024 saisis de mémoire
  ( budgets.py ) ; prix des avions ( catalogue.py ) ; prix des munitions ( à venir, munitions.py ).
- Bases russes de la Baltique absentes des modèles de CMO : Tchkalovsk, Donskoïé, Pskov ( Kresty ), Levachovo, Besovets,
  Baltiïsk, Kronstadt, à monter avec les éléments de la DB.
- Stocks de départ des dépôts : à fixer par pays, d'après les estimations publiques.
