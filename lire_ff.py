import re, pathlib
L = pathlib.Path("/mnt/data/harmattan-sandbox/logs/feu_force.out").read_text(errors="ignore")
R = {}
for b, cy, o, s, sup, rip in re.findall(
        r'HMT\|FF\|CY\|(\w+)\|(\d+)\|ordre\|(\d+)\|silence\|(\d+)\|supp\|([\d.eE+-]+)\|riposte\|(\d+)', L):
    R.setdefault(b, []).append((int(cy), int(o), int(s), float(sup), int(rip)))
NOM = {"A_command": "A — commandSuppressiveFire", "B_force": "B — boucle forcee 3 coups/s"}
print(f"  {'bras':<32}{'coups ORDRE':>13}{'coups SILENCE':>15}{'part sur ordre':>16}")
P = {}
for b in ["A_command", "B_force"]:
    v = R.get(b, [])
    if not v: continue
    o, s = v[-1][1], v[-1][2]          # compteurs CUMULES : la derniere ligne porte le total
    tot = o + s; p = 100*o/max(tot, 1)
    P[b] = dict(o=o, s=s, p=p, sup=max(x[3] for x in v), rip=v[-1][4])
    print(f"  {NOM[b]:<32}{o:>13}{s:>15}{p:>15.1f} %")
c = re.search(r'HMT\|FF\|CONTROLE\|cible_a_decouvert_tuee\|(\d)\|en\|(\d+)\|s', L)
print("\n─── CONTROLES POSITIFS ───")
print(f"  1. la boucle tue-t-elle une cible A DECOUVERT ? " +
      (f"{'OUI' if c.group(1)=='1' else 'NON'} (en {c.group(2)} s) → " + ("✓ PASSE" if c and c.group(1)=='1' else "⛔ TOMBE — l executeur ne tire pas vraiment") if c else "pas de ligne"))
if "B_force" in P:
    ps = 100*P["B_force"]["s"]/max(P["B_force"]["o"]+P["B_force"]["s"],1)
    print(f"  2. le silence est-il silencieux ? {ps:.1f} % des coups y tombent (porte < 20 %) → " + ("✓ PASSE" if ps < 20 else "⛔ TOMBE — tir par contact"))
# ⚠️ MON DEPOT DIT QU AUCUNE LECTURE N EST ADMISSIBLE SI UN CONTROLE POSITIF TOMBE.
# La premiere version imprimait le verdict quand meme. Corrige.
_ok1 = bool(c and c.group(1) == "1")
if not _ok1:
    print("\n  ⛔ CONTROLE POSITIF TOMBE — aucune lecture admissible. La porte n est PAS lue.")
    raise SystemExit
print("\n─── LA PORTE, DEPOSEE AVANT ───")
if "B_force" in P:
    p = P["B_force"]["p"]
    print(f"  bras B : {p:.1f} % des balles DANS ses fenetres d ordre")
    print("  ⇒ " + ("L EXECUTEUR MORD. L appui est un verbe utilisable." if p >= 80
          else "L EXECUTEUR EST MORT, comme commandSuppressiveFire." if p < 50
          else "INDECIS (50-80 %). On ne conclut pas."))
print("\n─── RAPPORTE, NON JUGE ───")
for b in P: print(f"  {NOM[b]:<32} getSuppression max {P[b]['sup']:.2f}   ·   ripostes {P[b]['rip']}")
