"""journal_audit — ETAPE 2 : le journal de l'officier de theatre a-t-il de quoi apprendre ?

On ne mesure PAS une courbe de perte. On mesure les deux preconditions qui, si elles manquent,
rendent tout entrainement inutile — et qui ne coutent aucun entrainement :

  A) VARIANCE : dans une meme situation, deux ordres differents donnent-ils des scores
     differents ? Si non -> paysage plat -> advantage collapse -> gradient nul.
  B) BUDGET : l'ordre reellement pris est-il deja le meilleur de ceux observes dans des
     situations semblables ? Si oui -> rien a apprendre, meme sur une bonne tache.

Sortie : un verdict GO / NO-GO, ou bien « journal insuffisant » avec le compte manquant.
"""
import sqlite3, json, sys, math
from collections import defaultdict

DB = "/home/younes/arma3-marl/leviathan/leviathan_officer.db"

db = sqlite3.connect(DB)
cols = [r[1] for r in db.execute("PRAGMA table_info(episodes)")]
print("=== SCHEMA ===")
print("  colonnes :", ", ".join(cols))

n = db.execute("SELECT count(*) FROM episodes").fetchone()[0]
print("\n=== VOLUME ===")
print("  episodes total : %d" % n)
if n == 0:
    print("\n  VERDICT : journal VIDE. L'etape 2 ne peut pas s'executer — il faut d'abord l'etape 1.")
    sys.exit(0)

for lvl, c in db.execute("SELECT level, count(*) FROM episodes GROUP BY level ORDER BY 2 DESC"):
    print("    niveau %-10s : %d" % (lvl, c))

# combien ont un OUTCOME grave (= une lecon utilisable) ?
q = "SELECT level, count(*) FROM episodes WHERE outcome IS NOT NULL AND outcome != '' AND outcome != '{}' GROUP BY level"
avec = dict(db.execute(q).fetchall())
print("\n=== LECONS UTILISABLES (outcome grave apres coup) ===")
if not avec:
    print("  AUCUNE. Le journal enregistre des decisions mais jamais leur CONSEQUENCE.")
    print("  -> sans outcome il n'y a pas de recompense : rien de mesurable, rien d'apprenable.")
else:
    for lvl, c in avec.items():
        print("    niveau %-10s : %d avec outcome" % (lvl, c))

# a quoi ressemble une ligne ?
print("\n=== ECHANTILLON (3 lignes) ===")
for row in db.execute("SELECT id, level, tick, decision, outcome, score FROM episodes ORDER BY id DESC LIMIT 3"):
    id_, lvl, tick, dec, out, sc = row
    print("  id=%s level=%s tick=%s score=%s" % (id_, lvl, tick, sc))
    print("     decision : %s" % (str(dec)[:160]))
    print("     outcome  : %s" % (str(out)[:160]))

# --------- A) VARIANCE : plusieurs ordres differents dans des situations semblables ?
print("\n=== A) VARIANCE DES ORDRES ===")
rows = list(db.execute(
    "SELECT decision, score FROM episodes WHERE score IS NOT NULL AND decision IS NOT NULL"))
print("  lignes avec un score : %d" % len(rows))
if len(rows) < 20:
    print("  -> trop peu pour conclure. Il faut du VOLUME (etape 1), pas un algorithme.")
else:
    par_ordre = defaultdict(list)
    for dec, sc in rows:
        try:
            d = json.loads(dec) if isinstance(dec, str) else dec
        except Exception:
            d = {"brut": str(dec)[:40]}
        cle = json.dumps(d, sort_keys=True)[:60]
        par_ordre[cle].append(sc)
    print("  ordres distincts observes : %d" % len(par_ordre))
    for cle, ss in sorted(par_ordre.items(), key=lambda kv: -len(kv[1]))[:6]:
        m = sum(ss) / len(ss)
        print("    n=%-5d moyenne %+.3f   %s" % (len(ss), m, cle))
    moyennes = [sum(s) / len(s) for s in par_ordre.values() if len(s) >= 3]
    if len(moyennes) >= 2:
        ec = max(moyennes) - min(moyennes)
        print("  ECART entre le meilleur et le pire ordre : %.3f -> %s"
              % (ec, "OK" if ec >= 0.05 else "PLAT (gradient nul)"))
    else:
        print("  -> un seul ordre a assez d'occurrences : aucune comparaison possible.")

# --------- B) BUDGET : le choix fait etait-il le meilleur disponible ?
print("\n=== B) BUDGET D'APPRENTISSAGE ===")
scores = [s for (_, s) in rows]
if len(scores) >= 20:
    scores_tries = sorted(scores)
    med = scores_tries[len(scores_tries) // 2]
    print("  score median des decisions prises : %+.3f" % med)
    print("  meilleur observe %+.3f | pire observe %+.3f" % (max(scores), min(scores)))
    print("  -> le budget vrai exige de comparer, POUR UNE MEME situation, l'ordre pris aux")
    print("     ordres non pris. Cela demande soit du contrefactuel, soit des situations repetees.")
    rep = db.execute("SELECT count(*) FROM (SELECT state, count(*) c FROM episodes GROUP BY state HAVING c > 1)").fetchone()[0]
    print("  situations vues plusieurs fois : %d" % rep)
else:
    print("  pas assez de lignes scorees.")

db.close()
