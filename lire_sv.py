import re, pathlib
L = pathlib.Path("/mnt/data/harmattan-sandbox/logs/sonde_vitesse.out").read_text(errors="ignore")
D = {}
for b, p, m in re.findall(r'HMT\|SV\|PT\|(\w+)\|periode\|(\d+)\|metres\|([\d.eE+-]+)', L):
    D.setdefault(b, []).append(float(m))
def med(v): v=sorted(v); return v[len(v)//2] if v else 0.0
NOM = {"A_une_fois":"A — UNE emission (le banc actuel)", "B_10Hz":"B — reemission a 10 Hz", "C_aucune":"C — aucune (controle nul)"}
print(f"  {'bras':<36}{'n':>3}{'mediane':>10}{'min':>8}{'max':>8}")
for k in ["A_une_fois","B_10Hz","C_aucune"]:
    v = D.get(k, [])
    if v: print(f"  {NOM[k]:<36}{len(v):>3}{med(v):>9.2f}m{min(v):>7.2f}{max(v):>8.2f}")
a, b, c = med(D.get("A_une_fois",[0])), med(D.get("B_10Hz",[0])), med(D.get("C_aucune",[0]))
print("\n─── CONTROLES POSITIFS ───")
print(f"  1. le bras A reproduit-il la lenteur du banc (~1,4 m) ? {a:.2f} m → " +
      ("✓ PASSE" if 0.5 <= a <= 4.0 else "⛔ TOMBE — la sonde ne mesure pas le banc"))
print(f"  2. le bras C rend-il ~0 m ?                            {c:.2f} m → " +
      ("✓ PASSE" if c < 1.0 else "⛔ TOMBE — il avance sans ordre"))
print("\n─── LA PORTE, DEPOSEE AVANT ───")
print(f"  bras B (10 Hz) : {b:.2f} m par periode   (6 m/s soutenus = 19,7 m)")
if   b > 10: v = "setVelocity est une IMPULSION. Le limiteur est la FREQUENCE d emission, et il se retire."
elif b <  3: v = "REFUTE — la reemission ne change rien. La lenteur vient d ailleurs."
else:        v = "INDECIS (3-10 m). On ne conclut pas, on ne rejoue pas."
print(f"\n  ⇒ {v}")
if b > 0 and a > 0: print(f"\n  gain B/A : x{b/a:.1f}")
