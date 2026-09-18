"""Consigne le verdict du prix du temps dans la base de connaissance."""
import sqlite3, sys
COMMIT = sys.argv[1]
S = "vingt-minutes-d-attente-ne-se-paient-pas-de-facon-mesurable"
c = sqlite3.connect("/mnt/data/hmt/socle/connaissance.sqlite")
if c.execute("select 1 from verdict where slug=?", (S,)).fetchone(): sys.exit("deja consigne")
c.execute("insert into verdict (slug, titre, date, fichier, [commit], statut, enonce, domaine, n_amendements) values (?,?,?,?,?,?,?,?,1)",
 (S, "Vingt minutes d'attente ne se paient pas de facon mesurable : ce monde n'a pas d'horloge", "2026-09-18",
  "verdicts/" + S + ".md", COMMIT, "OUVERT",
  "PRIX-DU-TEMPS-V2-18-09, 48 episodes, 48 acceptes, 0 erreur SQF, attente imposee de 0, 600 ou 1200 s avant la phase 5, hors plafond. "
  "Instrument controle avant d etre cru : derive maximale 3 m, assaut a sa place dans 100 % des episodes des trois bras, 0 % d abandon "
  "ARTICULATION_ROMPUE. Mission reussie ( 3 charges ET 6 exfiltres ) 0,625 / 0,562 / 0,500 ; ecart 1200 s - 0 s = -0,125 IC95 "
  "[-0,500 ; +0,188] sur 8 mondes apparies : INDECIS au critere ecrit d avance, ni prix ni gratuite. Ce qui est etabli est plus etroit : "
  "les charges posees sont IDENTIQUES aux trois niveaux ( 0,688 partout ) et l alarme comme la compromission sont deja au plafond au debut "
  "de la phase 5 dans tous les bras - le canal par lequel le temps punirait est sature avant que l attente commence. La version 1 du test "
  "( PRIX-DU-TEMPS-18-09 ) est declaree NULLE : sans ordre pendant l attente, six a sept hommes marchaient 818 m puis revenaient, et son "
  "issue primaire recompensait l abandon.", "banc CHACAL"))
M = [
 ("episodes acceptes sans erreur SQF", 48, "episodes", 48, "PRIX-DU-TEMPS-V2-18-09", "48 sur 48 posts acceptes", None),
 ("derive maximale du detachement pendant l attente", 3, "m", 32, "bras 600 s et 1200 s", "controle d instrument ; 818 m en version 1", None),
 ("assaut a sa place au debut de la phase 5", 100, "%", 48, "les trois bras", "controle positif ; 0 sur 16 a 600 s en version 1", None),
 ("mission reussie, attente 0 s", 0.625, "part", 16, "3 charges ET 6 exfiltres", "8 mondes x 2 repetitions", "attente=0"),
 ("mission reussie, attente 600 s", 0.562, "part", 16, "3 charges ET 6 exfiltres", "8 mondes x 2 repetitions", "attente=600"),
 ("mission reussie, attente 1200 s", 0.500, "part", 16, "3 charges ET 6 exfiltres", "8 mondes x 2 repetitions", "attente=1200"),
 ("ecart de reussite 1200 s - 0 s", -0.125, "points", 8, "mondes apparies, bootstrap graine 20260918", "IC95 [-0,500 ; +0,188] : INDECIS", None),
 ("trois charges posees, chaque niveau d attente", 0.688, "part", 48, "les trois bras", "identique a 0, 600 et 1200 s : l attente ne touche pas l assaut", None),
 ("alarme au debut de la phase 5", 1.0, "part", 32, "bras 0 s et 1200 s", "0,88 a 600 s ; le monde est deja reveille avant l attente", None),
 ("episodes necessaires pour trancher 12 points", 750, "episodes", 0, "calcul de puissance 3,9/delta2", "environ 1,5 jour de ferme ; doubler les repetitions ne suffirait pas", None),
]
for q, v, u, n, pop, cit, bras in M:
    c.execute("insert into mesure (verdict_slug, quantite, valeur, unite, n, population, citation, statut_mesure, bras) "
              "values (?,?,?,?,?,?,?,'COURANTE',?)", (S, q, v, u, n, pop, cit, bras))
c.execute("insert into falsificateur (verdict_slug, enonce, pre_enregistre, franchi) values (?,?,1,NULL)",
 (S, "Si une attente de 20 minutes ne fait pas baisser la reussite de plus de 10 points, alors le temps n a pas de prix mesurable dans ce "
     "monde, et aucune regle ne peut y apprendre a l economiser. NON TRANCHE : point mesure -12,5 points, IC [-50 ; +19]."))
c.commit()
print("consigne :", S, "avec", len(M), "mesures")
