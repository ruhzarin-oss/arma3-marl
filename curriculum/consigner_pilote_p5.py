import sqlite3, sys
H = sys.argv[1]; S = "le-delai-du-porteur-domine-sans-inversion"
c = sqlite3.connect("/mnt/data/hmt/socle/connaissance.sqlite")
if c.execute("select 1 from verdict where slug=?", (S,)).fetchone(): sys.exit("deja consigne")
c.execute("insert into verdict (slug, titre, date, fichier, [commit], statut, enonce, domaine, n_amendements) values (?,?,?,?,?,?,?,?,0)",
  (S, "Le delai de 180 s domine avec ou sans menace : la situation ne l inverse pas", "2026-09-16", "verdicts/" + S + ".md", H, "ETABLI",
   "PILOTE-P5-DELAI-SITUATION-16-09, 192 episodes apparies ( 8 mondes x 2 bras x 2 delais x 6 ), 192 ACCEPTE, 0 erreur : 180 s au lieu de 45 rend l assaut "
   "utile ( 3 charges et 6 vivants ) plus souvent sans menace ( +0,333 IC [+0,125 ; +0,542] ) et avec menace ( +0,146 IC [+0,021 ; +0,271] ). "
   "Modulation -0,188 IC [-0,375 ; +0,021] : non etablie, pas d inversion. Le choix n entre pas au curriculum comme decision dependant de la situation : "
   "c est une option dominante, pas une option indifferente comme la porte. 180 s ne coute pas d hommes.", "banc CHACAL"))
M = [("assaut utile, TEMOIN, delai 45 s", 0.479, "proportion", None, None, None, 48, 1, "PILOTE-P5, 8 mondes", "23/48", "CONTRASTE", "bras=TEMOIN;delai=45"),
     ("assaut utile, TEMOIN, delai 180 s", 0.812, "proportion", None, None, None, 48, 1, "PILOTE-P5, 8 mondes", "39/48", "CONTRASTE", "bras=TEMOIN;delai=180"),
     ("assaut utile, MENACE, delai 45 s", 0.438, "proportion", None, None, None, 48, 1, "PILOTE-P5, 8 mondes", "21/48", "CONTRASTE", "bras=MENACE;delai=45"),
     ("assaut utile, MENACE, delai 180 s", 0.583, "proportion", None, None, None, 48, 1, "PILOTE-P5, 8 mondes", "28/48", "CONTRASTE", "bras=MENACE;delai=180"),
     ("ecart assaut utile 180 - 45, TEMOIN", 0.333, "proportion", 0.125, 0.542, None, 96, 1, "PILOTE-P5, apparie par monde", "C1 ; IC par 10 000 reechantillonnages des mondes", "COURANTE", "bras=TEMOIN"),
     ("ecart assaut utile 180 - 45, MENACE", 0.146, "proportion", 0.021, 0.271, None, 96, 1, "PILOTE-P5, apparie par monde", "IC par reechantillonnage des mondes", "COURANTE", "bras=MENACE"),
     ("modulation assaut utile ( ecart menace - ecart temoin )", -0.188, "proportion", -0.375, 0.021, None, 192, 1, "PILOTE-P5, apparie par monde", "C2 non etablie ; 5 mondes negatifs, 2 nuls, 1 positif", "COURANTE", None),
     ("modulation trois charges", -0.229, "proportion", -0.438, 0.000, None, 192, 1, "PILOTE-P5", "secondaire, descriptive", "COURANTE", None),
     ("tues en phase 5, TEMOIN 45 / 180 s", 2.208, "hommes", None, None, None, 48, 1, "PILOTE-P5", "180 s : 2,083", "CONTRASTE", "bras=TEMOIN"),
     ("tues en phase 5, MENACE 45 / 180 s", 3.125, "hommes", None, None, None, 48, 1, "PILOTE-P5", "180 s : 2,833 ; la menace coute ~1 homme, 180 s n en coute pas", "CONTRASTE", "bras=MENACE"),
     ("episodes acceptes du pilote", 192, "episodes", None, None, None, 192, 0, "PILOTE-P5", "0 refuse, 0 erreur SQF, 32 cases pleines", "COURANTE", None)]
for q, v, u, lo, hi, p, n, ap, pop, cit, st, bras in M:
    c.execute("insert into mesure (verdict_slug, quantite, valeur, unite, ic_bas, ic_haut, p, n, appariement, population, citation, statut_mesure, bras) values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (S, q, v, u, lo, hi, p, n, ap, pop, cit, st, bras))
c.execute("insert into falsificateur (verdict_slug, enonce, pre_enregistre, franchi) values (?,?,1,1)",
          (S, "Si C2 n est pas etablie, la menace de phase 5 n a pas change le meilleur delai du porteur a la precision de ce dispositif, et le choix ne sert pas encore a apprendre a decider selon la situation."))
for e, portee in (("Un choix peut ne rien apprendre de deux facons : indifferent ( la porte ) ou domine ( 180 s gagne partout ). Classer les choix en trois : dependant de la situation, domine, indifferent.", "MESURE"),
                  ("Un choix se juge sur sa modulation par la situation, pas sur son effet moyen : un effet fort et partout du meme signe donne une regle fixe, pas une decision.", "MESURE")):
    c.execute("insert into regle (enonce, verdict_slug, portee) values (?,?,?)", (e, S, portee))
for cible, nature in (("delai-porteur-le-mecanisme-tient-pas-le-resultat", "COMPLETE"), ("la-situation-pese-sur-cinq-phases-la-phase-4-est-vide", "DEPEND_DE"),
                      ("la-porte-nest-pas-une-decision", "COMPLETE"), ("gymnase-de-decisions-predit-l-ecart-pas-le-niveau", "COMPLETE")):
    if c.execute("select 1 from verdict where slug=?", (cible,)).fetchone():
        c.execute("insert into lien (slug_source, slug_cible, nature) values (?,?,?)", (S, cible, nature))
    else: print("lien non pose :", cible)
c.execute("insert into verdict_episode (verdict_slug, campagne, n_episodes, n_rpt, n_refuses, role, methode_lien, note, n_graines) values (?,?,?,?,?,?,?,?,?)",
          (S, "PILOTE-P5-DELAI-SITUATION-16-09", 192, 192, 0, "ETABLIT", "campagne dans job.json", "2 bras x 2 delais x 8 mondes x 6 repetitions, bras entrelaces", 8))
c.execute("insert into verdict_episode (verdict_slug, campagne, n_episodes, n_rpt, n_refuses, role, methode_lien, note, n_graines) values (?,?,?,?,?,?,?,?,?)",
          (S, "FUMEE-DECISION-P5-16-09", 4, 4, 0, "CONTROLE", "campagne dans job.json", "fumee de la ligne de decision : 10 attentes tenues", 2))
c.commit()
print({t: c.execute(f"select count(*) from {t}").fetchone()[0] for t in ("verdict", "mesure", "falsificateur", "regle", "lien", "verdict_episode")})
