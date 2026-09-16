import sqlite3, sys
COMMIT, DBT = sys.argv[1], sys.argv[2]
S = "la-situation-pese-sur-cinq-phases-la-phase-4-est-vide"
c = sqlite3.connect("/mnt/data/hmt/socle/connaissance.sqlite")
if c.execute("select 1 from verdict where slug=?", (S,)).fetchone(): sys.exit("deja consigne")
c.execute("insert into verdict (slug, titre, date, fichier, [commit], statut, enonce, domaine, n_amendements) values (?,?,?,?,?,?,?,?,0)",
  (S, "La situation pese sur cinq phases ; la vignette de phase 4 est vide", "2026-09-16", "verdicts/" + S + ".md", COMMIT, "ETABLI",
   "SITUATION-PAR-PHASE-16-09, 24 episodes, menace de niveau 3 contre temoin sur les memes graines : zero erreur SQF, menaces conformes au niveau, "
   "aucune dans le temoin, monde identique. La menace pese sur les phases 1, 3, 5 et 6 ( contacts 16 a 147 m, tirs, alarme avancee de 130 a 140 s "
   "a l assaut, pertes ) ; sur la phase 2 seulement par la proximite ( 111 et 224 m ) et le temps. La vignette de phase 4 est vide : depart=4 "
   "teleporte la mise en place, la phase dure 11 s, les deux bras sont refuses. La regle de l insertion sous le feu n a pas ete exercee.",
   "banc CHACAL"))
M = [
 ("episodes SQF sans erreur", 24, "episodes", 24, "SITUATION-PAR-PHASE-16-09", "attente 1", None),
 ("P1 menace : distance de contact, graine 5 / 6", 34, "m", 2, "P1 d1a1", "graine 6 : 147 m ; tirs 263 / 36 ; alarme 167 / 145 s ; temoin : rien", "bras=MENACE"),
 ("P2 menace : distance de contact, graine 5 / 6", 224, "m", 2, "P2 d2a2", "graine 6 : 111 m ; 0 tir, ni alarme ni compromission", "bras=MENACE"),
 ("P2 duree d episode, menace graine 5 / 6", 549, "s", 2, "P2 d2a2", "graine 6 : 918 s ; temoin 347 et 340 s", "bras=MENACE"),
 ("P3 menace : distance de contact, graine 5 / 6", 17, "m", 2, "P3 d3a3 obs=1", "graine 6 : 28 m ; tirs 24 / 0 ; alarme 398 s / aucune ; tues 1 / 0", "bras=MENACE"),
 ("P4 duree de la phase 4 a depart=4", 11, "s", 4, "P4 d4a4, menace et temoin", "articulation_non_jouee ; canaris non poses ; 4 episodes REFUSE", None),
 ("P5 instant de l alarme, menace graine 5 / 6", 80, "s", 2, "P5 d4a5", "graine 6 : 39 s ; temoin 212 et 178 s ; tues menace 2 / 2, temoin 0 / 1", "bras=MENACE"),
 ("P6 menace : distance de contact, graine 5 / 6", 44, "m", 2, "P6 d4a6", "graine 6 : 16 m ; tirs 261 / 7 ; tues 2 / 4 contre temoin 1 / 5 ; blessure appliquee au medecin", "bras=MENACE"),
 ("episodes avec mort ennemie pendant l insertion", 0, "episodes", 2, "P1 menace", "regle de l insertion sous le feu non exercee", None),
 ("P3 duree d episode, min - max tous bras", 488, "s", 4, "P3 d3a3", "maximum 1869 s : hors des 10 minutes visees", None),
 ("P6 duree d episode, menace graine 5 / 6", 1643, "s", 2, "P6 d4a6", "graine 6 : 1847 s ; temoin 925 et 232 s", "bras=MENACE"),
]
for q, v, u, n, pop, cit, bras in M:
    c.execute("insert into mesure (verdict_slug, quantite, valeur, unite, n, appariement, population, citation, statut_mesure, bras) values (?,?,?,?,?,1,?,?,?,?)",
              (S, q, v, u, n, pop, cit, "COURANTE", bras))
for e, pr, fr in (("( 1 ) zero erreur SQF ; ( 2 ) menaces conformes au niveau, aucune dans le temoin ; ( 3 ) soldats dans la capture ; ( 4 ) monde identique ; ( 5 ) mort ennemie a l insertion non annulee ; ( 6 ) la menace pese dans au moins un des deux episodes du bras menace, ecrit dans chaque job avant le lancement", 1, 1),):
    c.execute("insert into falsificateur (verdict_slug, enonce, pre_enregistre, franchi) values (?,?,?,?)", (S, e + " - franchi pour la phase 4 ( non lisible ) ; ( 5 ) non exercee", pr, fr))
F = [("vignette de phase 4 vide a depart=4", "A", "bancs/chacal/mission.Altis/chacal/60_phases.sqf",
      "A depart=4 la mise en place est teleportee ( articulation_non_jouee ) : la phase 4 dure 11 s, l episode se ferme avant la pose des canaris et les deux bras sont REFUSE. La menace de phase 4 ne peut pas agir.",
      "PH|4|MISE_EN_PLACE fin - debut < 30 s a depart=4", 1, "OUVERTE", None),
     ("test dbt menaces_presentes_dans_la_capture comptait BLESSE_JAMBES comme des soldats", "F", "harmattan/tests/situation/menaces_presentes_dans_la_capture.sql",
      "hommes vaut 1 pour BLESSE_JAMBES mais designe NOTRE homme blesse ( reference DETACHEMENT ), pas des soldats ennemis : 4 echecs sur des episodes ou E|situation_blesse est bien ecrit. Corrige en excluant la reference DETACHEMENT.",
      "dbt test --select menaces_presentes_dans_la_capture", 1, "CORRIGEE", DBT),
     ("test dbt insertion_sous_le_feu_non_annulee passait sur zero cas", "B", "harmattan/tests/situation/insertion_sous_le_feu_non_annulee.sql",
      "Aucun episode n a eu de mort par l ennemi pendant l insertion : le test passait sans jamais s exercer. Ajout de insertion_sous_le_feu_exercee ( avertissement ).",
      "dbt test --select insertion_sous_le_feu_exercee", 1, "CONTOURNEE", DBT)]
for nom, fam, fich, desc, sig, exe, st, com in F:
    c.execute("insert into faute (nom, famille, date, fichier_fautif, description, signature, signature_executable, statut, commit_correctif, verdict_slug) values (?,?,?,?,?,?,?,?,?,?)",
              (nom, fam, "2026-09-16", fich, desc, sig, exe, st, com, S))
for e, portee in (("Une vignette ne se lance pas a un depart qui teleporte la phase qu elle teste : a depart=4 la phase 4 dure 11 s et la menace n a rien sur quoi agir.", "EXPLOITATION"),
                  ("Chaque test dbt qui peut passer sur zero cas a son jumeau qui previent quand il n a jamais ete exerce.", "MESURE")):
    c.execute("insert into regle (enonce, verdict_slug, portee) values (?,?,?)", (e, S, portee))
for cible, nature in (("le-chronometre-coupait-le-combat-du-bouchon", "COMPLETE"), ("cahier-des-charges-banc-a-decisions", "COMPLETE"),
                      ("le-chercheur-de-causes-n-est-pas-encore-cru", "COMPLETE")):
    if c.execute("select 1 from verdict where slug=?", (cible,)).fetchone():
        c.execute("insert into lien (slug_source, slug_cible, nature) values (?,?,?)", (S, cible, nature))
for camp, n, nr, note in (("SITUATION-PAR-PHASE-16-09", 20, 4, "12 jobs x 2 graines ; 4 REFUSE en phase 4 ( menace et temoin )"),
                          ("FUMEE-SITUATION-16-09", 2, 0, "fumee du 16/09 : toutes phases au niveau 3 ; relue par le test corrige")):
    c.execute("insert into verdict_episode (verdict_slug, campagne, n_episodes, n_rpt, n_refuses, role, methode_lien, note, n_graines) values (?,?,?,?,?,?,?,?,?)",
              (S, camp, n, n + nr, nr, "ETABLIT", "campagne dans job.json", note, 2))
c.commit()
print({t: c.execute(f"select count(*) from {t}").fetchone()[0] for t in ("verdict", "mesure", "falsificateur", "faute", "regle", "lien", "verdict_episode")})
