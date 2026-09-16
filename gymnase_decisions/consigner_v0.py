import sqlite3, sys
COMMIT = sys.argv[1]
S = "gymnase-de-decisions-predit-l-ecart-pas-le-niveau"
c = sqlite3.connect("/mnt/data/hmt/socle/connaissance.sqlite")
if c.execute("select 1 from verdict where slug=?", (S,)).fetchone(): sys.exit("deja consigne")
c.execute("insert into verdict (slug, titre, date, fichier, commit, statut, enonce, domaine, n_amendements) values (?,?,?,?,?,?,?,?,0)",
  (S, "Le gymnase de decisions predit l ecart, pas le niveau", "2026-09-16", "verdicts/" + S + ".md", COMMIT, "ETABLI",
   "Un gymnase qui rejoue les transitions de phase mesurees dans Arma predit 96 episodes jamais vus (CONFIRMATION-MISSION-15-09) : "
   "les deux bras dans l IC d Arma (45 s 0,544 contre 0,438 ; 180 s 0,652 contre 0,542), l enchainement assaut-exfiltration tient "
   "(z = -0,83), l ecart est reproduit (+10,8 contre +10,4). Mais il est optimiste d environ 10 points sur les deux bras et un taux "
   "constant de 52,8 % se trompe deux fois moins sur le niveau (0,104 contre 0,217) : l ecart transfere, le niveau non. "
   "L apprentissage converge sur 5 graines sur 5 (1 000 000 episodes chacune).", "gymnase et fidelite"))
M = [
 ("taux de mission predit, bras 45 s", 0.544, "proportion", 0.485, 0.607, None, 467, 0, "gymnase v0, mondes 7 8 11 12", "G1 ; IC bootstrap 2000 du gymnase", "CONTRASTE", "delai=45;porte=A"),
 ("taux de mission Arma, bras 45 s, test", 0.438, "proportion", 0.307, 0.577, None, 48, 0, "CONFIRMATION-MISSION-15-09", "G1 ; IC Wilson ; 21/48", "CONTRASTE", "delai=45;porte=A"),
 ("taux de mission predit, bras 180 s", 0.652, "proportion", 0.565, 0.737, None, 467, 0, "gymnase v0, mondes 7 8 11 12", "G2 ; IC bootstrap 2000 du gymnase", "CONTRASTE", "delai=180;porte=A"),
 ("taux de mission Arma, bras 180 s, test", 0.542, "proportion", 0.403, 0.674, None, 48, 0, "CONFIRMATION-MISSION-15-09", "G2 ; IC Wilson ; 26/48", "CONTRASTE", "delai=180;porte=A"),
 ("enchainement : z des succes observes contre attendus en exfiltration", -0.83, "z", None, None, None, 56, 0, "episodes test entres en phase 6 avec 3 charges", "G3 ; 47 observes, 48,9 attendus", "COURANTE", None),
 ("3 charges predit contre Arma, bras 45 s ( predit )", 0.638, "proportion", None, None, None, 467, 0, "gymnase v0", "G4 diagnostic ; Arma 0,500 IC [0,364 ; 0,636] : ECHOUE", "CONTRASTE", "delai=45"),
 ("3 charges Arma, bras 45 s, test", 0.500, "proportion", 0.364, 0.636, None, 48, 0, "CONFIRMATION-MISSION-15-09", "G4 diagnostic", "CONTRASTE", "delai=45"),
 ("ecart de mission 180 - 45 predit par le gymnase", 0.108, "proportion", 0.014, 0.194, None, 467, 0, "gymnase v0", "G5 et L2 ; Arma +0,104 non etabli", "COURANTE", None),
 ("ecart de mission porte B - porte A a 45 s, gymnase", -0.003, "proportion", -0.128, 0.120, None, 467, 0, "gymnase v0", "G6 et L3 ; coherence avec la-porte-nest-pas-une-decision", "COURANTE", None),
 ("erreur absolue cumulee sur les deux bras, gymnase", 0.217, "proportion", None, None, None, 96, 0, "CONFIRMATION-MISSION-15-09", "N informative : ECHOUE contre le naif", "CONTRASTE", "predicteur=gymnase"),
 ("erreur absolue cumulee sur les deux bras, taux constant 52,8 %", 0.104, "proportion", None, None, None, 96, 0, "CONFIRMATION-MISSION-15-09", "N informative", "CONTRASTE", "predicteur=naif_constant"),
 ("ecart maximal Q appris - valeur exacte, 5 graines", 0.0043, "proportion", None, None, None, 5000000, 0, "gymnase v0, 5 graines x 1 000 000 episodes", "L1 : 5 graines sur 5 choisissent 180 s porte A", "COURANTE", None),
]
for q, v, u, lo, hi, p, n, ap, pop, cit, st, bras in M:
    c.execute("insert into mesure (verdict_slug, quantite, valeur, unite, ic_bas, ic_haut, p, n, appariement, population, citation, statut_mesure, bras) values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (S, q, v, u, lo, hi, p, n, ap, pop, cit, st, bras))
c.execute("insert into falsificateur (verdict_slug, enonce, pre_enregistre, franchi) values (?,?,1,0)",
          (S, "Si G1 ou G2 echoue, le gymnase ne reproduit pas Arma sur des episodes qu il n a pas vus, et il ne sert pas a entrainer."))
for e, portee in (("Un gymnase se valide aussi contre un predicteur naif constant, pas seulement contre l IC d Arma : des IC de 48 episodes laissent passer un biais de niveau de 10 points.", "MESURE"),
                  ("Dans le gymnase de decisions, lire les ECARTS entre options, jamais les niveaux absolus : le niveau derive d une campagne Arma a l autre, l ecart transfere.", "EXPLOITATION"),
                  ("Un choix jamais joue dans Arma est interdit dans le gymnase de decisions : il n est ni extrapole ni suppose additif.", "CODE")):
    c.execute("insert into regle (enonce, verdict_slug, portee) values (?,?,?)", (e, S, portee))
for cible, nature in (("delai-porteur-le-mecanisme-tient-pas-le-resultat", "DEPEND_DE"), ("la-porte-nest-pas-une-decision", "COMPLETE"),
                      ("recette-gymnase-loterie", "COMPLETE"), ("transfert-non-etabli", "COMPLETE"), ("un-taux-porte-sa-charge-machine", "DEPEND_DE")):
    if c.execute("select 1 from verdict where slug=?", (cible,)).fetchone():
        c.execute("insert into lien (slug_source, slug_cible, nature) values (?,?,?)", (S, cible, nature))
    else: print("   lien non pose, slug absent :", cible)
for camp, n, note in (("CONFIRMATION-MISSION-15-09", 96, "TEST jamais lu par la construction : 2 bras x 4 mondes x 12"),
                      ("REFERENCE-PROPRE-13-09", 141, "construction phases 5 et 6"), ("REFERENCE-JAMBES-13-09", 15, "construction phases 5 et 6"),
                      ("DELAI-PORTEUR-14-09", 110, "construction phase 5, bras 180 s, mondes 7 8 11 12"),
                      ("PORTE-A-CONTRE-PORTE-B-14-09", 96, "construction phase 5, porte A 45 s"), ("PORTE-B-CONTROLE-14-09", 10, "construction phase 5, porte B"),
                      ("PORTE-HUIT-MONDES-15-09", 95, "construction phase 5, portes A et B, mondes 7 8 11 12")):
    c.execute("insert into verdict_episode (verdict_slug, campagne, n_episodes, role, methode_lien, note, n_graines) values (?,?,?,?,?,?,?)",
              (S, camp, n, "ETABLIT", "campagne dans job.json", note, 4))
c.commit()
print({t: c.execute(f"select count(*) from {t}").fetchone()[0] for t in ("verdict", "mesure", "falsificateur", "regle", "lien", "verdict_episode")})
