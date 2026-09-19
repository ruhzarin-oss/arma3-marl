"""Consigne le premier choix dependant de la situation dans la base de connaissance."""
import sqlite3, sys
COMMIT = sys.argv[1]
S = "contre-une-patrouille-on-traverse-contre-un-poste-on-attend"
c = sqlite3.connect("/mnt/data/hmt/socle/connaissance.sqlite")
if c.execute("select 1 from verdict where slug=?", (S,)).fetchone(): sys.exit("deja consigne")
c.execute("insert into verdict (slug, titre, date, fichier, [commit], statut, enonce, domaine, n_amendements) values (?,?,?,?,?,?,?,?,2)",
 (S, "Le premier choix qui depend de la situation : contre une patrouille on traverse, contre un poste on attend",
  "2026-09-19", "verdicts/" + S + ".md", COMMIT, "ETABLI",
  "CHOIX-P2-TYPES-19-09, 144 episodes joues, 134 acceptes, 0 erreur SQF, six portes de qualite passees apres retrait du monde 11 "
  "( amendement 3 ecrit d avance ; lecture sur 7 mondes, minimum 6 ). Vignette d2a2 de nuit, option tiree a pile ou face, bras = TYPE de "
  "menace pose seul. PATROUILLE motorisee : traverser tout de suite 0,936 contre attendre 0,714, ecart -0,221 IC [-0,371 ; -0,071]. "
  "POSTE de controle : 0,781 contre 0,929, ecart +0,148 IC [-0,048 ; +0,457]. Modulation -0,369 IC [-0,640 ; -0,126], signes opposes : "
  "DEPENDANT du type de menace, avec inversion, cinq mondes sur sept dans le meme sens et aucun contre. C est le PREMIER des sept choix "
  "mesures depuis le 16/09 qui depend de la situation. L hypothese pre-enregistree disait l inverse ( attendre vaut mieux contre une "
  "patrouille ) : elle est REFUTEE. Limite majeure : la regle n est pas encore jouable par l agent, car au moment du choix le vehicule "
  "n est percu que dans 7 episodes sur 58 et la menace n est JAMAIS connue du groupe ( 0 sur 118 ).", "banc CHACAL"))
M = [
 ("episodes acceptes sans erreur SQF", 134, "episodes", 144, "CHOIX-P2-TYPES-19-09", "8 refus d hygiene remplaces, 2 episodes du monde 11 sans decision", None),
 ("phase discrete, patrouille, traverser tout de suite", 0.936, "part", 29, "7 mondes apparies", "le meilleur des quatre cas", "bras=PATROUILLE"),
 ("phase discrete, patrouille, attendre", 0.714, "part", 29, "7 mondes apparies", "attendre une patrouille, c est l attendre", "bras=PATROUILLE"),
 ("phase discrete, poste, traverser tout de suite", 0.781, "part", 32, "7 mondes apparies", None, "bras=POSTE"),
 ("phase discrete, poste, attendre", 0.929, "part", 28, "7 mondes apparies", None, "bras=POSTE"),
 ("ecart attendre moins tout de suite, patrouille", -0.221, "points", 7, "mondes apparies, bootstrap graine 20260919", "IC [-0,371 ; -0,071]", "bras=PATROUILLE"),
 ("ecart attendre moins tout de suite, poste", 0.148, "points", 7, "mondes apparies, bootstrap graine 20260919", "IC [-0,048 ; +0,457]", "bras=POSTE"),
 ("modulation patrouille moins poste", -0.369, "points", 7, "mondes apparies, bootstrap graine 20260919", "IC [-0,640 ; -0,126] : ETABLIE, 37 points pour un seuil de puissance a 35", None),
 ("mondes dont la modulation va dans le sens mesure", 5, "mondes", 7, "4, 6, 8, 9, 12 negatifs ; 5 et 7 nuls", "aucun monde ne va contre", None),
 ("vehicule percu au moment du choix, bras patrouille", 7, "episodes", 58, "ligne de decision", "la regle n est pas encore jouable par l agent", "bras=PATROUILLE"),
 ("menace CONNUE du groupe au moment du choix", 0, "episodes", 118, "ligne de decision, les deux bras", "le canal connaissance reste mort au moment de choisir", None),
]
for q, v, u, n, pop, cit, bras in M:
    c.execute("insert into mesure (verdict_slug, quantite, valeur, unite, n, population, citation, statut_mesure, bras) "
              "values (?,?,?,?,?,?,?,'COURANTE',?)", (S, q, v, u, n, pop, cit, bras))
c.execute("insert into falsificateur (verdict_slug, enonce, pre_enregistre, franchi) values (?,?,1,0)",
 (S, "Si la modulation n est pas etablie, le type de menace ne change pas la meilleure option, et le choix de la phase 2 ne sert pas "
     "encore a apprendre a decider selon la situation. NON FRANCHI : modulation -0,369 IC [-0,640 ; -0,126]."))
c.commit()
print("consigne :", S, "avec", len(M), "mesures")
