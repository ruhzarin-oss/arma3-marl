#!/usr/bin/env python3
"""lire_nuit — LE LECTEUR DU VERDICT. Il APPLIQUE les criteres deposes, il ne les invente pas.

Il fait trois choses, dans cet ordre :
  1. RECALCULE les temoins de mecanisme de TOUTES les cellules depuis les politiques
     sauvegardees, avec le MEME Φ gele — sinon on compare deux thermometres ⟨Fable⟩ ;
  2. imprime le tableau apparie ;
  3. rend le verdict selon `PF2` SEULE, cellule confirmatoire ⟨amendement 3⟩, et refuse de
     conclure hors des bornes deposees.

Il n a le droit de rien decider. Les seuils viennent des amendements, haches :
  PREINSCRIPTION 06c6d263e68a4172 · AM1 a4a0a0193d115512 · AM2 498770c4aad659c0 · AM3 6e9cea219f604da8
"""
import sys, os, json, glob, hashlib
import torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
import banc_raster as BR

DEV = "cuda:0"
SEUIL_SUCCES, SEUIL_ECHEC = 5.0, 3.0

def haches():
    out = []
    for f in ("PREINSCRIPTION_RASTER.md", "AMENDEMENT_BUDGET_RASTER.md",
              "AMENDEMENT_2_RASTER.md", "AMENDEMENT_3_RASTER.md"):
        p = "/home/younes/arma3-marl/" + f
        out.append("%s %s" % (f.split("_")[0][:6],
                              hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] if os.path.exists(p) else "ABSENT"))
    return " · ".join(out)

def temoins_recalcules(bras, graine):
    """Rejoue la politique SAUVEGARDEE avec le Φ GELE, pour que le thermometre soit unique."""
    f = "/mnt/data/pol_%s_%d.pt" % (bras, graine)
    if not os.path.exists(f): return None
    Cls, avec_r, brouille, _ = BR.BRAS[bras]
    e0 = B.monde(8, B.GRAINES_TRAIN[0]); e0.reset()
    pol = Cls(e0._obs().shape[-1]).to(DEV)
    try: pol.load_state_dict(torch.load(f, map_location=DEV))
    except Exception as ex: return {"err": str(ex)[:40]}
    pol.eval()
    p, t, (dhp, surv) = BR.evaluer(pol, bras, B.GRAINES_TEST, n=256)
    return {"prise": p, "tenus": t, "danger_hp": dhp, "survivants": surv}

def charge():
    r = {}
    for f in glob.glob("/mnt/data/dd_res_*.json") + glob.glob("/mnt/data/n2_res_*.json"):
        try: d = json.load(open(f))
        except Exception: continue
        for b, v in d.get("bras", {}).items():
            if not v.get("prise"): continue
            for i, g in enumerate(d["graines_entrainement"]):
                r.setdefault(b, {})[g] = {"prise": v["prise"][i], "tenus": v["tenus"][i],
                                          "film": v.get("film", {}).get(str(g), [])}
    return r

print("=" * 86)
print(" VERDICT DE LA NUIT — criteres deposes AVANT les donnees")
print(" " + haches())
print("=" * 86)

res = charge()
if not res:
    print("\n  aucune cellule terminee pour l instant."); sys.exit(0)

print("\n─── RECALCUL DES TEMOINS AVEC LE Φ GELE (thermometre unique) ───")
tem = {}
for b in sorted(res):
    for g in sorted(res[b]):
        t = temoins_recalcules(b, g)
        if t and "err" not in t: tem[(b, g)] = t
        print("  %-4s graine %d : %s" % (b, g, "recalcule" if t and "err" not in t else "politique absente ou incompatible"))

print("\n─── LE TABLEAU (prise sur GRAINES_TEST, jamais vues, decodeur echantillonnage) ───")
print("  %-5s %-7s %8s %10s %12s %12s" % ("bras", "graine", "prise", "tenus", "danger/h-pas", "survivants"))
for b in ("A", "P", "AF", "PF", "AF2", "PF2", "E3"):
    if b not in res: continue
    for g in sorted(res[b]):
        t = tem.get((b, g), {})
        print("  %-5s %-7d %7.1f %% %9.1f m %12s %12s"
              % (b, g, res[b][g]["prise"], res[b][g]["tenus"],
                 "%.4f" % t["danger_hp"] if t else "—",
                 "%.2f" % t["survivants"] if t else "—"))

def moy(b, k="prise"):
    if b not in res: return None
    v = [res[b][g][k] for g in sorted(res[b])]
    return sum(v) / len(v)

print("\n─── LE VERDICT ───")
print("  ⚠️ SEULE `PF2` DECIDE (amendement 3). `PF` est EXPLORATOIRE et ne se cite qu a fortiori.")
pf2, p = moy("PF2"), moy("P")
if pf2 is None or p is None:
    print("  PF2 ou P manquant — pas de verdict.")
else:
    d = pf2 - p
    tp = tem.get(("P", 0), {}); t2 = tem.get(("PF2", 0), {})
    meca = None
    if tp and t2:
        meca = (t2["danger_hp"] < tp["danger_hp"]) and (t2["survivants"] >= tp["survivants"] - 0.05)
        print("  temoins : danger/h-pas  P %.4f -> PF2 %.4f  %s" % (tp["danger_hp"], t2["danger_hp"],
              "BAISSE" if t2["danger_hp"] < tp["danger_hp"] else "NE BAISSE PAS"))
        print("            survivants    P %.2f   -> PF2 %.2f" % (tp["survivants"], t2["survivants"]))
    print("  PF2 %.1f %%  -  P %.1f %%  =  %+.1f points   (succes >= +%.1f, echec < +%.1f)"
          % (pf2, p, d, SEUIL_SUCCES, SEUIL_ECHEC))
    if d >= SEUIL_SUCCES and meca:
        v = "SUCCES DEPOSABLE — le faconnage rend creditable ce que la greffe prouve actionnable"
    elif d >= SEUIL_SUCCES and meca is False:
        v = "⚠️ FACONNAGE POMPE — le score monte SANS que le danger baisse. OUVRIR UN AVEU."
    elif d < SEUIL_ECHEC:
        v = "ECHEC — ouvrir la branche deposee : DISTILLATION DU MAITRE-GREFFE (professeur a 61,6 %)"
    else:
        v = "ZONE GRISE (+3 a +5) — deux graines de plus, AUCUN VERDICT"
    print("\n  >>> %s" % v)

for a, bq, q in (("AF", "PF", "si AF ~ PF : le signal cote RECOMPENSE suffit, l entree est redondante"),
                 ("AF2", "PF2", "idem, version Φ corrige")):
    x, y = moy(a), moy(bq)
    if x is not None and y is not None:
        print("  arbitre %s %.1f %% contre %s %.1f %% -> ecart %+.1f   (%s)" % (a, x, bq, y, y - x, q))

e3 = moy("E3")
if e3 is not None:
    n = len(res.get("E3", {}))
    print("\n  SONDE E3 (jetons SANS positions) : %.1f %% sur %d graine(s)" % (e3, n))
    print("   -> %s" % ("~61 : ce sont les ATTRIBUTS NON SPATIAUX qui portaient E2" if e3 > 56 else
                        "~49 : le gain de E2 etait du BRUIT REGULARISANT" if e3 < 54 else "entre les deux, illisible"))
    if n < 2: print("   ⚠️ UNE SEULE GRAINE — ne se depose pas (amendement 3).")
print()
