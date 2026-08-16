import sys
"""CRITERES v3, ECRITS AVANT DE REGARDER — et les ecartements le sont aussi.

  · ECARTES AVANT TOUTE LECTURE :
      - tout essai dont `nt` < 25 pour une fenetre de 3,28 s (le serveur n a pas tenu la
        cadence : moins d impulsions emises, ce qui penalise les bras `vel` et pas les autres) ;
      - tout essai du bras 7 avec `coups` = 0 (il ne reproduit pas T5, qui suppose un tir) ;
      - tout essai avec `enmain` faux (l homme n avait pas son arme en main).
  · CONTROLE DE L INSTRUMENT — bras 0 (natif + doMove, 15 s) doit rendre PLUS DE 15 m.
    Il demande seulement : ce banc sait-il faire marcher un homme ?
  · RETENU — au moins 8 m en 3,28 s ET au moins 90 % de temps au sol. Les deux.
  · L EPREUVE DU VERDICT — bras 7 sous 3 m : T5 reproduit, VERDICT_JAMBES.md tient.
    Au-dessus de 8 m : non reproduit, le verdict TOMBE et je le retire.
"""
L = [l for l in open("/mnt/data/harmattan-sandbox/logs/serverJB.out", errors="ignore")
     if "HMT|JAMBES|bras" in l]
par, ecartes = {}, {"cadence": 0, "sans_tir": 0, "desarme": 0}
for l in L:
    p = [x.strip().strip('"') for x in l[l.index("HMT|JAMBES|"):].split("|")]
    i = p.index("bras"); d = dict(zip(p[i::2], p[i+1::2]))
    nt, du = int(d["nt"]), float(d["duree"])
    if d.get("enmain", "true") == "false": ecartes["desarme"] += 1; continue
    if du <= 4.1 and nt < 25:              ecartes["cadence"] += 1; continue
    if d["bras"].startswith("7") and int(d["coups"]) == 0: ecartes["sans_tir"] += 1; continue
    par.setdefault(d["bras"], []).append((float(d["m"]), float(d["sol"]), nt, int(d["fps"])))
med = lambda v: sorted(v)[len(v)//2]
print(f"\n  essais : {len(L)}   ecartes : {ecartes}\n")
if not par: print("  ⛔ TOUT A ETE ECARTE."); sys.exit(2)
print("  %-30s %3s %9s %8s %6s %5s   %s" % ("bras","n","metres","au sol","iter","fps","min-max"))
R = {}
for k in sorted(par):
    v = par[k]; m=[x[0] for x in v]; s=[x[1] for x in v]; n=[x[2] for x in v]; f=[x[3] for x in v]
    R[k] = (med(m), med(s), len(v))
    print("  %-30s %3d %8.1f m %6.0f %% %6d %5d   %.1f - %.1f"
          % (k, len(v), med(m), med(s), med(n), med(f), min(m), max(m)))
print("\n  ── LES CRITERES, DANS L ORDRE OU ILS ONT ETE ECRITS ──")
c = R.get("0_CONTROLE_natif_15s", (0,0,0))
if c[0] <= 15:
    print(f"  ⛔ CONTROLE DE L INSTRUMENT ECHOUE : {c[0]:.1f} m sur 15 s. LE BANC EST MUET."); sys.exit(2)
print(f"  ✓ l instrument sait faire marcher un homme : {c[0]:.1f} m en 15 s")
t7 = R.get("7_REPRO_T5_temoin_apres_tir")
if t7 is None: print("  ⚠️  bras 7 : aucun essai valide, le verdict n est PAS mis a l epreuve.")
elif t7[0] < 3: print(f"  ✓ T5 REPRODUIT : {t7[0]:.1f} m — VERDICT_JAMBES.md tient.")
elif t7[0] > 8: print(f"  ⛔ T5 NON REPRODUCTIBLE : {t7[0]:.1f} m — VERDICT_JAMBES.md TOMBE, je le retire.")
else:           print(f"  ⚠️  bras 7 a {t7[0]:.1f} m : entre 3 et 8, zone morte, on ne conclut pas.")
ret = [(k,v) for k,v in R.items() if k[0] in "123456" and v[0] >= 8 and v[1] >= 90]
if not ret: print("\n  ⛔ AUCUN BRAS RETENU — aucune primitive ne rend 8 m AU SOL par ordre.")
else:
    ret.sort(key=lambda x: -x[1][0])
    print("\n  BRAS RETENUS (>= 8 m ET >= 90 % au sol) :")
    for k,v in ret: print("     %-30s %5.1f m  %3.0f %% au sol" % (k, v[0], v[1]))
    print("\n  ➤ RETENU : %s — %.1f m par ordre (reference haute 19,7 m)" % (ret[0][0], ret[0][1][0]))
