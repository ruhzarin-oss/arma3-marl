import sys
"""CRITERES v2, ECRITS AVANT DE REGARDER

  · CONTROLE DE L INSTRUMENT — bras 0 (natif + doMove, fenetre de 15 s) doit rendre PLUS
    DE 15 m. Il ne demande pas si un ordre suffit ; il demande si ce banc sait faire
    marcher un homme. C est la faute de la v1, corrigee sans regarder ses chiffres.
  · La MESURE reste sur 3,28 s : c est la fenetre d un ordre du banc live, on ne la bouge pas.
  · RETENU — au moins 8 m en 3,28 s ET au moins 90 % de temps au sol. Les deux.
  · L EPREUVE DU VERDICT — bras 7 reproduit T5 a l identique. Sous 3 m, T5 est reproductible
    et VERDICT_JAMBES.md tient. Au-dessus de 8 m, il ne l est pas et le verdict TOMBE.
"""
L = [l for l in open("/mnt/data/harmattan-sandbox/logs/serverJB.out", errors="ignore")
     if "HMT|JAMBES|bras" in l]
par = {}
for l in L:
    p = [x.strip().strip('"') for x in l[l.index("HMT|JAMBES|"):].split("|")]
    i = p.index("bras"); d = dict(zip(p[i::2], p[i+1::2]))
    par.setdefault(d["bras"], []).append((float(d["m"]), float(d["sol"])))
med = lambda v: sorted(v)[len(v)//2]
print(f"\n  essais : {len(L)}\n")
print("  %-30s %3s %9s %8s   %s" % ("bras", "n", "metres", "au sol", "min-max"))
R = {}
for k in sorted(par):
    v = par[k]; m = [x[0] for x in v]; s = [x[1] for x in v]
    R[k] = (med(m), med(s), len(v))
    print("  %-30s %3d %8.1f m %6.0f %%   %.1f - %.1f" % (k, len(v), med(m), med(s), min(m), max(m)))
print("\n  ── LES CRITERES, DANS L ORDRE OU ILS ONT ETE ECRITS ──")
c = R.get("0_CONTROLE_natif_15s", (0, 0, 0))
if c[0] <= 15:
    print(f"  ⛔ CONTROLE DE L INSTRUMENT ECHOUE : {c[0]:.1f} m sur 15 s. LE BANC EST MUET."); sys.exit(2)
print(f"  ✓ l instrument sait faire marcher un homme : {c[0]:.1f} m en 15 s")
t7 = R.get("7_REPRO_T5_temoin_apres_tir", (None, None, 0))
if t7[0] is not None:
    if t7[0] < 3:   print(f"  ✓ T5 REPRODUIT : {t7[0]:.1f} m — VERDICT_JAMBES.md tient.")
    elif t7[0] > 8: print(f"  ⛔ T5 NON REPRODUCTIBLE : {t7[0]:.1f} m — VERDICT_JAMBES.md TOMBE.")
    else:           print(f"  ⚠️  T5 entre 3 et 8 m ({t7[0]:.1f}) : ni reproduit ni refute, zone morte.")
ret = [(k, v) for k, v in R.items() if k[0] in "123456" and v[0] >= 8 and v[1] >= 90]
if not ret:
    print("\n  ⛔ AUCUN BRAS RETENU — aucune primitive ne rend 8 m AU SOL par ordre.")
else:
    ret.sort(key=lambda x: -x[1][0])
    print("\n  BRAS RETENUS (>= 8 m ET >= 90 % au sol) :")
    for k, v in ret: print("     %-30s %5.1f m  %3.0f %% au sol" % (k, v[0], v[1]))
    print("\n  ➤ RETENU : %s — %.1f m par ordre (reference haute 19,7 m)" % (ret[0][0], ret[0][1][0]))
