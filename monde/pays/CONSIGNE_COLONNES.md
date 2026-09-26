# Écrire un domaine sur le moteur en colonnes ( 24/09 )

1. **Base.** Le moteur n'a plus d'objet par habitant. Avant le prochain domaine, fusionner `pays-sur-colonnes` dans
   `socle-du-pays` : les 14 domaines livrés y tournent, identiques au bit à ce qui a été livré. Mesurer et tester sur ce
   moteur : il est 5 fois plus rapide, une porte de coût mesurée sur l'ancien ne vaut plus rien.
2. **Un habitant n'est plus un objet.** `w.habitants[i]` fabrique une vue sur une ligne de `w.table` ; chaque lecture
   d'attribut coûte environ 1 µs. Interdit dans une routine de chaque pas ou de chaque jour : `for h in w.habitants`,
   `for m in w.menages` avec `m.membres`, `np.fromiter(h.x for h in ...)`, `w.au_travail_de(...)` suivi d'un filtre,
   `sum(... for x in ...)` sur des vues.
3. **Lire les colonnes.** `tb = w.table` : `vivant`, `lieu`, `travail`, `domicile` ( numéros de lieu = `Lieu.n`, -1
   aucun ), `poste`, `role`, `classe`, `etat`, `horaire` ( codes : `population.CODE_*` ), `heures`, `faim`, `age`,
   `menage`. Ménages : `tb.menages` ( `caisse`, `garde_manger`, `domicile` ). Membres : `population.menages_inscrits(tb,
   n)` pour compter, `tb.menages.membres_ids(k)` pour la liste. Travailleurs : `w.ids_au_travail(lieu, role)` ( des
   numéros ). Marché d'un lieu : `w._marche_du_lieu[n]`.
4. **Méthode.** Les colonnes trouvent les lignes concernées ; Python ne traite que celles-là, dans l'ordre des numéros.
   Une vue seulement pour l'habitant qu'un événement touche.
5. **Exactitude.** Garder l'ordre des tirages, des paiements au grand livre et des notes au journal. Une somme Python
   n'est pas un `np.sum` ( autres bits ) : `np.cumsum` ou `math.fsum`.
6. **Pas de coût quadratique, même à l'installation.** Aucun filtre qui parcourt une liste pour chaque habitant.
   Installer à 10 000 puis à 100 000 habitants : le temps doit être multiplié par 10, pas par 100.
7. **Juge.** `python -m monde.porte_domaines` compare le pays entier au bit à une référence : la lancer avant et après
   toute réécriture d'un domaine existant. Les portes de coût restent telles quelles : c'est au domaine d'être aussi
   rapide que le moteur.
8. **Bogue connu, à ne pas corriger sans Younes.** `d04 _accidents` appelle `blesser(p, h, "accident_travail", 0.3|1)`
   alors que la médecine attend un type de `TYPES_LESION` et un ISS de 1 à 75, et tire déjà ses propres accidents du
   travail. Le monde plante dès 100 000 habitants.
