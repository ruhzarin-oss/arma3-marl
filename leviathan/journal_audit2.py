"""journal_audit2 — ETAPE 2, analyse propre.

Le premier passage donnait un « ecart 0.344 » entre ordres : il est FAUX comme mesure de la
qualite d'un ordre, parce qu'il compare des ordres pris dans des situations DIFFERENTES. Un
ordre pris dans une situation calme marque haut parce que la situation est calme, pas parce que
l'ordre etait bon. On ne peut comparer deux ordres que DANS LA MEME SITUATION.

Il n'y a aucune situation strictement identique. On travaille donc par VOISINAGE : on regroupe
les situations proches (cosinus sur l'embedding de theatre, celui-la meme que le RAG utilise),
et on ne compare des ordres qu'a l'interieur d'un voisinage.

A) VARIANCE UTILE : dans un voisinage, deux ordres DIFFERENTS donnent-ils des scores differents ?
B) BUDGET : l'ordre reellement pris etait-il deja le meilleur du voisinage ?
C) EXPLORATION : l'officier a-t-il seulement essaye plusieurs verbes ?
"""
import sqlite3, json, sys
import numpy as np
from collections import Counter, defaultdict

DB = "/home/younes/arma3-marl/leviathan/leviathan_officer.db"
SIM = 0.995          # seuil de « meme situation »

db = sqlite3.connect(DB)
rows = list(db.execute(
    "SELECT id, emb, decision, score FROM episodes "
    "WHERE score IS NOT NULL AND emb IS NOT NULL AND decision IS NOT NULL ORDER BY id"))
print("=== base : %d episodes scores ===" % len(rows))

E, D, S = [], [], []
for _id, emb, dec, sc in rows:
    v = np.frombuffer(emb, dtype=np.float32)
    E.append(v); S.append(float(sc))
    try:
        d = json.loads(dec)
    except Exception:
        d = {}
    D.append(d)
E = np.stack(E); S = np.array(S)
print("  embedding : %d dimensions" % E.shape[1])

# ---------------------------------------------------------------- C) EXPLORATION
print("\n=== C) EXPLORATION : quels verbes l'officier a-t-il reellement essayes ? ===")
verbes = Counter(); par_fob = defaultdict(Counter); n_ordres = Counter()
for d in D:
    ords = d.get("ordres") or []
    n_ordres[len(ords)] += 1
    for o in ords:
        a = (o.get("action") or "?").upper()
        verbes[a] += 1
        par_fob[o.get("fob", "?")][a] += 1
tot = sum(verbes.values())
for a, c in verbes.most_common():
    print("    %-12s %6d  (%5.1f %%)" % (a, c, 100.0 * c / max(1, tot)))
print("  verbes distincts : %d" % len(verbes))
fob_mono = sum(1 for f, c in par_fob.items() if len(c) == 1)
print("  FOB n'ayant JAMAIS recu qu'un seul verbe : %d sur %d" % (fob_mono, len(par_fob)))

# ---------------------------------------------------------------- signature d'ordre
def signature(d):
    ords = d.get("ordres") or []
    return tuple(sorted("%s:%s" % (o.get("fob"), (o.get("action") or "?").upper()) for o in ords))

SIGS = [signature(d) for d in D]
print("  plans d'ordres distincts (FOB+verbe) : %d" % len(set(SIGS)))

# ---------------------------------------------------------------- A/B) voisinages
print("\n=== A/B) COMPARAISON A SITUATION EGALE (cosinus >= %.3f) ===" % SIM)
N = E / (np.linalg.norm(E, axis=1, keepdims=True) + 1e-9)
G = N @ N.T

vus = np.zeros(len(N), dtype=bool)
groupes = []
for i in range(len(N)):
    if vus[i]:
        continue
    idx = np.where((G[i] >= SIM) & (~vus))[0]
    vus[idx] = True
    if len(idx) >= 2:
        groupes.append(idx)
print("  voisinages d'au moins 2 situations : %d" % len(groupes))

utiles, ecarts, regrets = 0, [], []
for idx in groupes:
    sigs = [SIGS[j] for j in idx]
    if len(set(sigs)) < 2:
        continue                       # meme situation, meme ordre -> ne dit rien
    utiles += 1
    par_sig = defaultdict(list)
    for j in idx:
        par_sig[SIGS[j]].append(S[j])
    moy = {k: float(np.mean(v)) for k, v in par_sig.items()}
    ec = max(moy.values()) - min(moy.values())
    ecarts.append(ec)
    best = max(moy.values())
    regrets += [best - S[j] for j in idx]

print("  voisinages contenant AU MOINS DEUX ORDRES DIFFERENTS : %d" % utiles)
if utiles == 0:
    print("\n  VERDICT — NO-GO, et la cause est nommee :")
    print("  L'officier n'a JAMAIS donne deux ordres differents dans une meme situation.")
    print("  Aucun contrefactuel n'existe dans ce journal : on ne peut pas savoir si un autre")
    print("  ordre aurait fait mieux. Ce n'est pas un probleme d'algorithme, c'est un probleme")
    print("  d'EXPLORATION — le meme mur qu'au niveau KOTH, ou 'harceler' sortait 0 fois sur 256.")
else:
    print("  ECART moyen entre ordres a situation egale : %.3f" % float(np.mean(ecarts)))
    print("  ECART maximum observe                      : %.3f" % float(np.max(ecarts)))
    print("  REGRET moyen de l'ordre reellement pris    : %.3f" % float(np.mean(regrets)))
    print("  -> A) %s" % ("OK, il y a de la variance" if np.mean(ecarts) >= 0.05 else "PLAT"))
    print("  -> B) %s" % ("OK, il y a du budget" if np.mean(regrets) >= 0.05
                          else "RIEN A APPRENDRE : l'officier prenait deja le meilleur"))

# ---------------------------------------------------------------- distribution des scores
print("\n=== DISTRIBUTION DES SCORES (le paysage vu de haut) ===")
for lo, hi in [(-1, 0), (0, 0.5), (0.5, 1.0), (1.0, 1.2), (1.2, 1.3), (1.3, 2.0)]:
    c = int(((S >= lo) & (S < hi)).sum())
    print("    [%+.1f, %+.1f) : %5d  %s" % (lo, hi, c, "#" * int(60.0 * c / len(S))))
print("  ecart-type des scores : %.4f" % float(S.std()))
db.close()
