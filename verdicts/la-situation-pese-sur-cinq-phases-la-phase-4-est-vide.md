# La situation pèse sur cinq phases ; la vignette de phase 4 est vide

*16/09/2026 — statut ETABLI — domaine : banc CHACAL*
*Campagne SITUATION-PAR-PHASE-16-09 : 12 jobs, 24 épisodes, un serveur par phase et par bras. Attentes écrites dans
chaque job avant le lancement. Couche de situation : commit 2d3ddd2. Lecture : dbt (commit dbt à la suite).*

## Énoncé

La couche de situation fonctionne : zéro erreur SQF, menaces posées comme le niveau le demande et aucune dans le
témoin, monde identique entre les deux bras. Une menace de niveau 3 **pèse** sur les phases 1, 3, 5 et 6
(contacts de 16 à 147 m sur les phases 1, 3 et 6, tirs, alarme avancée, pertes). Sur la phase 2, elle n'agit que par la proximité et le
temps (contacts à 111 et 224 m, sans tir ni alarme, épisode plus long de 200 à 580 s). **La vignette de phase 4
est vide** : à `depart=4`, le détachement est téléporté en place, la phase dure 11 s et les deux bras sont refusés.
La règle « une mort ennemie à l'insertion n'annule pas l'épisode » **n'a pas été exercée** : aucun cas.

## Le dispositif

Chaque phase a deux bras sur les mêmes graines 5 et 6 et la même graine de situation 1 : **MENACE** (niveau 3 sur
cette phase seulement) et **TÉMOIN** (tout à 0). Vignettes : P1 `d1a1`, P2 `d2a2`, P3 `d3a3 obs=1`, P4 `d4a4`,
P5 `d4a5`, P6 `d4a6`.

## Les six attentes écrites avant

| attente | résultat |
|---|---|
| (1) zéro erreur SQF | **tenue** : 24 sur 24 |
| (2) menaces comme le niveau le demande, aucune dans le témoin | **tenue** : `situation_conforme_au_job`, `temoin_sans_situation` |
| (3) soldats des menaces dans la capture | **tenue après correction du test** (voir faute) |
| (4) monde identique entre menace et témoin | **tenue** : `monde_identique_au_controle` |
| (5) mort ennemie à l'insertion non annulée | **non exercée** : aucun épisode n'a eu de mort par l'ennemi pendant l'insertion ; le test passait sur zéro cas |
| (6) la menace pèse dans au moins un des deux épisodes | **5 phases sur 6** ; phase 4 non lisible |

## Phase par phase (graine 5 / graine 6)

| phase | bras menace | bras témoin | la menace pèse ? | durée menace / témoin |
|---|---|---|---|---|
| 1 insertion | contact 34 / 147 m ; tirs 263 / 36 ; alarme 167 / 145 s ; tués 1 / 0 | rien | **oui**, dans les deux | 230-214 s / 231-210 s |
| 2 route | contact 224 / 111 m ; 0 tir ; ni alarme ni compromission | rien | **par la proximité seulement** ; épisode plus long | 549-918 s / 347-340 s |
| 3 observation | contact 17 / 28 m ; tirs 24 / 0 ; alarme 398 s / — ; tués 1 / 0 | rien | **oui** (graine 5) | 488-1869 s / 1056-1601 s |
| 4 mise en place | positions à 198 / 350 m au départ ; rien d'autre | rien | **non lisible** : phase de 11 s, deux bras refusés | 80-44 s / 85-42 s |
| 5 assaut | alarme forcée à 80 / 39 s ; tués 2 / 2 | alarme 212 / 178 s ; tués 0 / 1 | **oui** : alarme avancée de 130 à 140 s, plus de pertes | 394-420 s / 351-412 s |
| 6 exfiltration | contact 44 / 16 m ; tirs 261 / 7 ; tués 2 / 4 ; un homme blessé aux jambes (le médecin, graine 5) | tués 1 / 5 ; un succès | **oui** | 1643-1847 s / 925-232 s |

Deux épisodes par bras : ce test montre que chaque menace **existe et agit**, pas la taille de son effet.

## Fautes

1. **Vignette de phase 4 vide (banc).** À `depart=4`, la mise en place est téléportée (`articulation_non_jouee`),
   la phase 4 dure 11 s et l'épisode se ferme avant la pose des canaris : verdict REFUSE sur les deux bras. La
   menace de phase 4 ne peut pas agir. Une vignette de phase 4 doit **partir du regroupement et jouer la marche**,
   sans la phase 3 (qui dure 8 à 31 min).
2. **Test dbt `menaces_presentes_dans_la_capture` faux.** Il comptait `BLESSE_JAMBES` comme une menace de terrain :
   « hommes » y compte nos hommes blessés, pas des soldats ennemis. Il échouait sur 4 épisodes : les 2 de la phase 6, où la
   blessure est bien appliquée (`E|situation_blesse`), et les 2 de la fumée, arrêtés en phase 1, où elle n'était pas
   encore due. Corrigé : référence `DETACHEMENT` exclue.
3. **Test qui passe sur zéro cas.** `insertion_sous_le_feu_non_annulee` passait sans qu'aucun cas n'existe. Ajout
   du test `insertion_sous_le_feu_exercee` (avertissement tant que la règle n'a jamais servi).

## Ce qui reste hors des 10 minutes

Phase 3 (8 à 31 min) et phase 6 (4 à 31 min) dépassent la durée visée par le curriculum. Phase 2 menace, graine 6 :
15 min.

## Conséquences

- La couche de situation peut servir au curriculum sur les phases 1, 2, 3, 5 et 6.
- Phase 4 : construire un départ « au regroupement, sans observation » avant tout test.
- Phase 2 : une menace qui ne fait que retarder est un vrai choix (attendre ou traverser), mais il faut mesurer ce
  que coûte l'attente.
- Ces 24 épisodes versent de premières expériences entrelacées au chercheur de causes (levier `menace_pK`).

## Amendement 1 — 16/09, 19:40 : la phase 4 corrigée pèse aussi

*Campagne PHASE4-REGROUPEMENT-16-09 : 2 jobs, 4 épisodes, attentes écrites dans les jobs avant le lancement.
Garde du contrôle avant run : commit ad50266. Test dbt `phase_arretee_jouee` : dbt 37fafbe.*

**Correction sans code de mission** : `depart=3 obs=0 arret=4` pose le détachement au regroupement, coupe
l'observation et **joue la marche** de mise en place. Le contrôle avant run refuse désormais toute vignette qui
s'arrête sur une phase que son départ ne joue pas (vérifié : l'ancien `d4a4` et `d3 obs=0 a3` refusés, les
vignettes valides acceptées).

| attente écrite avant | résultat |
|---|---|
| (1) zéro erreur SQF | **tenue** : 4 sur 4 |
| (2) verdict ACCEPTE | **tenue** : 4 sur 4 (contre 0 sur 4 à `depart=4`) |
| (3) phase 4 jouée : observation coupée, pas de téléport, au moins 60 s | **tenue** : 174 à 376 s |
| (4) menaces posées, soldats dans la capture, aucune dans le témoin | **tenue** : patrouille de 3 à 313 / 374 m, poste d'écoute de 2 à 297 / 230 m |
| (5) monde identique | **tenue** |
| (6) la menace pèse dans au moins un épisode | **tenue** (graine 5) |
| (7) épisode de 10 min au plus | **tenu** : 234 à 408 s |

| graine | menace | témoin |
|---|---|---|
| 5 | contact 103 m, 14 tirs, **alarme à 169 s**, compromis à 230 s par un coup reçu, 1 tué, phase 4 interrompue à 174 s | compromis à 350 s en arrivant (ennemi vu en combat), sans alarme, 0 tué |
| 6 | contact 237 m, rien d'autre, positions atteintes à 376 s sans compromission | compromis à 359 s en arrivant, sans alarme, 0 tué |

**Lecture** : la menace de phase 4 agit (graine 5 : alarme, perte, compromission deux minutes plus tôt). Mais sans
menace, le détachement est déjà compromis en arrivant dans les deux graines, et avec menace la graine 6 ne l'est
pas : à deux épisodes par bras, **le sens de l'effet n'est pas lisible**, seulement son existence. La mise en place
compromet déjà 60 épisodes sur 283 à `depart=3` dans l'historique, sans menace.

**La couche de situation pèse maintenant sur les six phases** (la phase 2 par la proximité seulement). La faute
« vignette de phase 4 vide » est corrigée.
