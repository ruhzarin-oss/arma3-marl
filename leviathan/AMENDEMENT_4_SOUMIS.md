# AMENDEMENT 4 — SOUMIS À YOUNES, NON APPLIQUÉ

Rédigé le 2026-07-29 par Opus 5, sur protocole de Fable. **Non appliqué : l'interdit n°8 du
jalon 1 réserve à Younes le retrait d'une référence publiée.**

## CE QUI EST DEMANDÉ
Retirer la table d'étalon du 2026-07-29 et la remplacer par la table ci-dessous.

## MOTIF, EN UNE PHRASE
L'ancienne table a été mesurée avec un compteur de pas cassé ; les trois doctrines qui ont
une phase unique en début d'épisode ne l'exécutaient jamais.

## LE MÉCANISME, PRÉCISÉMENT
`manuel.py` reçoit un pas `t` **scalaire**. Trois doctrines s'en servent pour une phase unique :
`debordement_simple` et `debordement_double` crochètent tant que `t < 14`, `infiltration`
déploie son éventail tant que `t < 20` et pose sa posture à `t == 0`.

L'ancienne mesure tournait en remise à zéro automatique : les épisodes se terminent et
redémarrent à des instants différents selon l'environnement, alors que `t` continue de courir
globalement. **Passé le quatorzième pas global, plus aucun épisode ne recevait jamais `t < 14`** —
donc plus aucun crochet, plus aucun éventail, sur des dizaines de milliers d'épisodes.
On mesurait la version amputée de ces trois doctrines.

Les trois doctrines qui n'utilisent pas `t`, ou qui n'en font qu'une alternance courte,
retombent dans la tolérance : c'est la signature du mécanisme, pas une coïncidence.

## LA NOUVELLE MESURE
Protocole **persisté** — `etalon_j1.sh`, banc `banc_mission.py`, analyse `analyse_journal.py`,
critères `CRITERES_JALON1.md` (`2129aea319627f8f`).
Mode **episode** (`auto_reset=False`) : tous les environnements partent à zéro et ne
redémarrent jamais, le pas scalaire est donc exact pour tous.
1024 épisodes par cellule, graine 3, D=8, 80 pas, verbe forcé, permutation nulle.

Ligne de commande reproductible :
```
bash /home/younes/arma3-marl/leviathan/etalon_j1.sh
```

| doctrine | PRENDRE | INFILTRER | ancienne PRENDRE | ancienne INFILTRER |
|---|---|---|---|---|
| frontal_delibere | **46,2** | **5,8** | 44,0 | 7,6 |
| appui_mouvement | **46,8** | **11,6** | 49,8 | 14,5 |
| debordement_simple | **84,2** | **60,2** | 54,3 | 32,2 |
| debordement_double | **86,3** | **59,6** | 54,3 | 31,7 |
| infiltration | **83,8** | **48,9** | 53,0 | 18,1 |
| bonds_alternes | **22,1** | **7,7** | 24,8 | 9,6 |

Contrôles passés : le prédicat de succès recalculé depuis les ingrédients bruts égale celui du
monde sur **100 % des 12 288 épisodes** ; l'appariement des missions tient entre les douze
passes ; aucun épisode ne finit en `horizon`.

## CE QUE ÇA CHANGE POUR LA SUITE
La barre à battre monte beaucoup. L'agent ne doit plus dépasser 54,3 % et 32,2 %, mais
**86,3 % et 60,2 %**. Le jalon 4 devient nettement plus dur — et honnête.

## VÉRIFICATION SUPPLÉMENTAIRE PROPOSÉE, SI TU LA VEUX
Rejouer `debordement_simple` en mode désynchronisé, uniquement comme diagnostic, pour vérifier
qu'on retrouve bien les ~54 % d'origine. Ce serait la preuve directe du mécanisme. Le banc
refuse ce mode par sécurité ; il faudrait le forcer explicitement pour ce seul diagnostic.

## TON ARBITRAGE
- [ ] **Accepter** — la nouvelle table devient la référence, l'ancienne est retirée avec ce motif.
- [ ] **Demander d'abord la vérification** ci-dessus.
- [ ] **Refuser** — et alors il faut dire quelle mesure fait foi, car les deux ne peuvent pas.
