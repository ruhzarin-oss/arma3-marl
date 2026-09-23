"""LE SOCLE DU PAYS - domaine 0 de la carte des domaines ( 23/09 ).

Tous les domaines du pays s ecrivent sur ces pieces. Aucune ne sait ce qu est une ferme, une banque ou un soldat :
elles savent compter, dater, tirer au hasard, ranger une echeance, journaliser et faire decider.

  biens.py        le catalogue des biens fongibles, et le stock creux de chaque detenteur
  objets.py       les objets durables ( vehicule, arme, batiment ) : individus et cohortes, conserves par modele
  comptes.py      le grand livre : tout mouvement d argent et de bien, avec son motif ; les creances
  registre.py     qui detient quoi ; la conservation qui en decoule ; le rapprochement par famille
  echeancier.py   les echeances rangees par pas : le cout suit le nombre d evenements, pas la population
  hasard.py       un flux de hasard par domaine, derive de la graine
  calendrier.py   la date, la semaine, les jours feries, les saisons, le soleil
  journal.py      les evenements declares, individuels ou comptes, en memoire bornee
  decision.py     le protocole d un point de decision : regle, observer, actions, note, horizon, temoin
  brancher.py     pose le socle sur un Monde E1 sans modifier monde.py

Les portes : python -m monde.socle.tests_socle      Les couts : python -m monde.socle.cout"""
