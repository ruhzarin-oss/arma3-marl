import re, pathlib
L = pathlib.Path("/mnt/data/harmattan-sandbox/logs/verif_corps.out").read_text(errors="ignore")
R = [(int(p), float(m), float(f)) for p, m, f in
     re.findall(r'HMT\|VC\|PT\|(\d+)\|metres\|([\d.eE+-]+)\|fps\|([\d.eE+-]+)', L)]
if not R: print("  rien encore"); raise SystemExit
def med(v): v=sorted(v); return v[len(v)//2]
M = [m for _,m,_ in R]; F = [f for _,_,f in R]
print(f"  {len(R)} periodes de 3,28 s, un homme, action 0 (cap nord)\n")
print(f"  metres par periode   mediane {med(M):7.2f}   min {min(M):6.2f}   max {max(M):6.2f}")
print(f"  FPS serveur          mediane {med(F):7.1f}   min {min(F):6.1f}   max {max(F):6.1f}")
print("\n─── LE CONTROLE POSITIF DE LA GREFFE ───")
print(f"  avant la greffe : 2,58 m par periode (sonde)  ·  1,43 m dans le banc live")
print(f"  cible           : 6 m/s x 3,28 s = 19,7 m")
print(f"  mesure          : {med(M):.2f} m  →  " + ("✓ LA GREFFE A MORDU" if med(M) > 10 else "⛔ TOMBE — la greffe n a pas mordu"))
print(f"\n  gain : x{med(M)/2.58:.1f} sur la sonde  ·  x{med(M)/1.43:.1f} sur le banc live")
print("\n─── LE COUT, QUI EST LA RAISON D ETRE DU LIMITEUR ───")
print(f"  FPS mediane {med(F):.1f}  →  " + ("acceptable a UN homme" if med(F) > 30 else "⚠️ deja bas a UN homme"))
print("  ⚠️ mesure a UN homme. Le banc live en a 4, la ferme jusqu a 40. NON extrapolable.")
