import sqlite3, sys
COMMIT = sys.argv[1]
S = "le-chercheur-de-causes-n-est-pas-encore-cru"
c = sqlite3.connect("/mnt/data/hmt/socle/connaissance.sqlite")
if c.execute("select 1 from verdict where slug=?", (S,)).fetchone(): sys.exit("deja consigne")
c.execute("insert into verdict (slug, titre, date, fichier, [commit], statut, enonce, domaine, n_amendements) values (?,?,?,?,?,?,?,?,0)",
  (S, "Le chercheur de causes n est pas encore cru", "2026-09-16", "verdicts/" + S + ".md", COMMIT, "REFUTE",
   "Un chercheur automatique de causes ( 618 variables fabriquees par regle generique, leviers forces compares a monde et autres leviers egaux, "
   "permutations dans les strates ) retrouve les causes fortes ( socle, tactique, arret, palier ) et ne voit plus rien sur 5 placebos une fois "
   "sa statistique corrigee, mais rate un mecanisme etabli : delai 180 s, charges manquees faute de porteur 0,32 -> 0,18, p = 0,0043, q = 0,0502. "
   "Selon la regle ecrite d avance, ses trouvailles ne sont pas publiees. En v0, sans garde, les 5 placebos decouvraient 19 a 32 variables chacun.",
   "instrument"))
M = [
 ("placebos avec au moins une decouverte, v0", 5, "placebos", None, None, None, 5, 0, "chercheur v0, 1556 episodes", "19 a 32 variables intermediaires par placebo ; z tire du bruit d arrondi", "CONTRASTE", "version=v0"),
 ("placebos avec au moins une decouverte, v1", 0, "placebos", None, None, None, 5, 0, "chercheur v1, 1556 episodes", "garde de variance intra-strate et p a 20 000 permutations", "CONTRASTE", "version=v1"),
 ("p normal contre p permute des decouvertes du placebo 0, v0", 0.0, "p", None, None, None, 21, 0, "placebo_0, 21 variables", "p a 20 000 permutations = 1,0 pour les 21", "COURANTE", None),
 ("C+1 socle 0 -> 1, charges ( moyenne ponderee socle 0 )", 1.50, "charges", None, None, None, 10, 1, "TOURNOI-TACTIQUES-12-09, 2 strates", "socle 1 : 2,67 ; q = 0,020 ; passe", "CONTRASTE", "socle=0"),
 ("C+2 tactique 0 -> 5, charges ( moyenne ponderee tactique 5 )", 1.30, "charges", None, None, None, 10, 1, "TOURNOI-TACTIQUES-12-09, 2 strates", "tactique 0 : 2,67 ; q = 0,020 ; passe", "CONTRASTE", "tactique=5"),
 ("C+4p delai 45 -> 180, charges manquees faute de porteur par episode, 45 s", 0.322, "charges", None, None, None, 269, 1, "lecture non entrelacee, 10 strates", "180 s : 0,185 ; z = -2,84 ; p = 0,0043 ; q = 0,0502 ; ECHOUE", "CONTRASTE", "delai=45"),
 ("C+4p q de BH, famille M du delai ( 105 variables )", 0.0502, "q", None, None, 0.0043, 475, 1, "lecture non entrelacee, 10 strates", "seuil 0,05", "COURANTE", None),
 ("delai 45 -> 180, charges, lecture non entrelacee, ecart", 0.150, "charges", None, None, 0.034, 475, 1, "10 strates, 269 contre 206", "q = 0,31 : non decouvert ; coherent avec le verdict amende", "COURANTE", None),
 ("arret 5 -> 6, succes, lecture non entrelacee", 0.48, "proportion", None, None, None, 382, 1, "16 strates, 270 contre 112", "a arret=5 : 0 ; raison ph|6|issue=ATTEINT part 1,00", "COURANTE", None),
]
for q, v, u, lo, hi, p, n, ap, pop, cit, st, bras in M:
    c.execute("insert into mesure (verdict_slug, quantite, valeur, unite, ic_bas, ic_haut, p, n, appariement, population, citation, statut_mesure, bras) values (?,?,?,?,?,?,?,?,?,?,?,?,?)",
              (S, q, v, u, lo, hi, p, n, ap, pop, cit, st, bras))
c.execute("insert into falsificateur (verdict_slug, enonce, pre_enregistre, franchi) values (?,?,1,1)",
          (S, "Si un controle testable echoue, les trouvailles du chercheur ne sont pas publiees comme resultats ( franchi en v0 et en v1 )."))
for e, portee in (("Toute machine qui cherche des effets passe des placebos dans la meme machine : sans eux, le chercheur v0 publiait 19 a 32 fausses raisons par faux levier.", "MESURE"),
                  ("Un controle positif se choisit sur un verdict ETABLI, jamais AMENDE : un effet non demontre ne peut pas juger un instrument.", "MESURE"),
                  ("Une variable constante dans chaque strate ne se teste pas par permutation : la statistique permutee est constante et son z sort du bruit d arrondi.", "CODE"),
                  ("Compter les tests apres avoir fusionne les variables identiques : les doublons exacts diluent la correction BH sans ajouter d hypothese.", "MESURE")):
    c.execute("insert into regle (enonce, verdict_slug, portee) values (?,?,?)", (e, S, portee))
F = [("chercheur de causes v0 : z tire du bruit d arrondi", "B", "chercheur_causes/chercher.py",
      "Les variables constantes dans chaque strate ( geometrie du monde, evenement present dans toute une strate ) etaient testees : statistique permutee constante, ecart-type de l ordre de 1e-15, z jusqu a 19, p normal 0 ; p a 20 000 permutations 1,0. Les 5 placebos decouvraient 19 a 32 variables. Attrape par le controle C-2.",
      "placebos du chercheur : decouvertes M > 0", 1, "CORRIGEE", "00d8623"),
     ("chercheur de causes v0 : controle positif pris sur un verdict amende", "D", "chercheur_causes/CRITERES_CHERCHEUR_CAUSES_V0.md",
      "C+4 exigeait que le delai du porteur augmente les charges, alors que delai-porteur-le-mecanisme-tient-pas-le-resultat est AMENDE ( p 0,031 -> 0,219 ). Remplace en v1 par le mecanisme etabli.",
      "select statut from verdict where slug = slug du controle", 1, "CORRIGEE", "00d8623")]
for nom, fam, fich, desc, sig, exe, st, com in F:
    c.execute("insert into faute (nom, famille, date, fichier_fautif, description, signature, signature_executable, statut, commit_correctif, verdict_slug) values (?,?,?,?,?,?,?,?,?,?)",
              (nom, fam, "2026-09-16", fich, desc, sig, exe, st, com, S))
for cible, nature in (("delai-porteur-le-mecanisme-tient-pas-le-resultat", "DEPEND_DE"), ("socle-execution-10-sur-10", "DEPEND_DE"),
                      ("la-porte-nest-pas-une-decision", "DEPEND_DE"), ("victoire-bout-en-bout-47-pourcent", "DEPEND_DE"),
                      ("gymnase-de-decisions-predit-l-ecart-pas-le-niveau", "COMPLETE")):
    if c.execute("select 1 from verdict where slug=?", (cible,)).fetchone():
        c.execute("insert into lien (slug_source, slug_cible, nature) values (?,?,?)", (S, cible, nature))
    else: print("   lien non pose :", cible)
c.execute("insert into verdict_episode (verdict_slug, campagne, n_episodes, role, methode_lien, note) values (?,?,?,?,?,?)",
          (S, "TOUTES_CAMPAGNES_CHACAL_SAUF_SITUATION", 1556, "ETABLIT", "campagne dans job.json",
           "ACCEPTE, 0 erreur SQF, avec ligne FINI ; exclus : sans campagne, SITUATION-PAR-PHASE-16-09 et FUMEE-SITUATION-16-09 ( campagne en cours )"))
c.commit()
print({t: c.execute(f"select count(*) from {t}").fetchone()[0] for t in ("verdict", "mesure", "falsificateur", "faute", "regle", "lien", "verdict_episode")})
