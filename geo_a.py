import sys, re, math, pathlib, numpy as np, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import terrain_gpu as TG, boucle as B

# ═══ REGLE 18 : les portes passent leur banc AVANT les donnees ═══
def lire(r):
    if r > 2:   return "A RETENUE"
    if r < 0.5: return "A refutee dans l autre sens"
    return "A REFUTEE"
print("─── REGLE 18 : les portes passent leur propre banc ───")
for v, att in [(3.0,"A RETENUE"), (1.0,"A REFUTEE"), (0.3,"A refutee dans l autre sens")]:
    got = lire(v); print(f"  {'✓' if got==att else '⛔'} rapport {v:.1f} → {got}")
print("  ✓ chaque bande est atteignable ET rejetable.\n")

# ─── ARMA : mesure de CARTE deja faite (sonde_dcover, site du banc, seuil repare)
L = pathlib.Path("/mnt/data/harmattan-sandbox/logs/sonde_dcover.out").read_text(errors="ignore")
A = [int(n)/30 for nom, d, a, n in
     re.findall(r'HMT\|DC\|PT\|(\w+)\|dist\|(\d+)\|ancien\|(\d+)\|nouveau\|(\d+)', L) if nom == "NOUVEAU"]
A = np.array(A)

# ─── GYMNASE : memes rayons sur les terrains de MONDE_ARMA, pur torch
e = B.monde(64, 101)
G = []
gen = torch.Generator(device=e.dev); gen.manual_seed(7)
for _ in range(24):                                   # 24 rayons, comme la sonde Arma
    az = float(torch.rand(1, generator=gen, device=e.dev)) * 2*math.pi
    for k in range(8):                                # 8 distances : 170 -> 30 m
        d = 170.0 - k*20.0
        # (N, A) et non (N,) : `sample` gather sur deux dimensions
        px = torch.full((e.N, 1), d*math.sin(az), device=e.dev)
        py = torch.full((e.N, 1), d*math.cos(az), device=e.dev)
        G.append(TG.sample(e.dcover, px, py, e.terr_R).cpu().numpy()/30.0)
G = np.concatenate(G)

print("─── LE COULOIR D APPROCHE, CARTE SEULE ───")
for nom, X in [("GYMNASE", G), ("ARMA", A)]:
    print(f"  {nom:<9} n={len(X):5d}   1% {np.percentile(X,1):.3f}   mediane {np.percentile(X,50):.3f}   99% {np.percentile(X,99):.3f}   moyenne {X.mean():.3f}")

print("\n─── CONTROLE POSITIF : l echantillonnage represente-t-il le couloir parcouru ? ───")
VECU = {"GYMNASE": 0.041, "ARMA": 0.123}
ok = True
for nom, X in [("GYMNASE", G), ("ARMA", A)]:
    v = VECU[nom]; r = X.mean()/v; b = 0.5 <= r <= 2.0; ok &= b
    print(f"  {nom:<9} carte {X.mean():.3f} contre vecu {v:.3f}  → facteur {r:.2f}  " + ("✓" if b else "⛔ hors facteur 2"))
if not ok: raise SystemExit("\n  ⇒ le couloir echantillonne n est pas celui qui est parcouru. RIEN NE SE LIT.")

r = np.percentile(A,50)/max(np.percentile(G,50),1e-9)
print(f"\n─── LA LECTURE ───\n  mediane Arma / mediane gymnase = {r:.2f}")
print(f"\n  ⇒ {lire(r)}")
