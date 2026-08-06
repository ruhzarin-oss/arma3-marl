#!/usr/bin/env python3
"""pouls_v2.py — DU SEMBLABLE CONTRE DU SEMBLABLE.

Criteres deposes AVANT ce calcul : CRITERES_POULS_V2.md.

  restriction SYMETRIQUE : des deux cotes, on ne garde que les hommes REELLEMENT dans le champ
  d un ennemi vivant — ecart angulaire a sa face < 35 degres, le demi-cone MESURE. La tranche
  de distance est celle de l ennemi ENGAGEANT le plus proche.

  tolerance INCHANGEE : comparable a 2 000 de chaque cote · meme pouls entre 0,5 et 2,0 ·
  passe a 2/3 des tranches et jamais hors facteur 4 · forme suspecte au-dela d un facteur 2,5.

  fourche deposee : DANS la tolerance -> la chaine est saine, le x3,5 de la v1 etait la
  population, AUCUNE correction. HORS -> le facteur se derive du rapport median de la V2 et
  s applique au degat par impact, aucun autre bouton.

Le facteur 0,280 de la v1 NE S APPLIQUE PAS : sa regle presupposait une comparaison entre
semblables, que la clause de limite declarait absente.
"""
import sys, math, numpy as np

TRANCHES = [(0, 50), (50, 100), (100, 150), (150, 200), (200, 250), (250, 400)]
HOR_PAS, N_MIN, DEMI_CONE = 9, 2000, 35.0

# ---------------------------------------------------------------- ARMA, restreint aux ENGAGES
sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/sonde1.py').read()
g = {'__name__': '__pouls2__'}
exec(compile(src.split('print(f"  apprentissage')[0], 'sonde1.py', 'exec'), g)
ENN, MASQ, Y = g['ENN'], g['MASQ'], g['Y']
d_e = ENN[..., 3] * 400.0
a_lui = ENN[..., 4] * 180.0
engage = (MASQ > 0.5) & (a_lui < DEMI_CONE)              # je suis dans SON cone
d_eng = np.where(engage, d_e, 1e9)
d_min_arma = d_eng.min(axis=1)
garde = d_min_arma < 400
Ya, Da = Y[garde], d_min_arma[garde]
print(f"\n  ARMA   {len(Y)} observations -> {len(Ya)} ENGAGEES ({len(Ya)/len(Y):.1%})"
      f" · mortalite des engages {Ya.mean():.2%}  (population entiere : {Y.mean():.2%})")

# ---------------------------------------------------------------- SANDBOX, meme restriction
src2 = open('/home/younes/arma3-marl/agent_complet.py', encoding='utf-8').read()
h = {'__name__': '__pouls3__'}
exec(compile(src2[:src2.index("if '--smoke' in sys.argv:")], 'agent_complet.py', 'exec'), h)
t = h['torch']; dev = h['dev']
POS, AZI, MSK, NC = h['POS'], h['AZI'], h['MSK'], h['NC']
degats_du_pas, SEUIL_MORT = h['degats_du_pas'], h['SEUIL_MORT']
ALLURES, POSTURES_V = h['ALLURES'], h['POSTURES_V']

t.manual_seed(0)
B, NPAS = 4096, 80
idx = t.randint(0, NC, (B,), device=dev)
ang = t.rand(B, device=dev) * 2 * math.pi
p = t.stack([t.sin(ang), t.cos(ang)], -1) * 250.0
wp = t.zeros(B, 3, device=dev); wp[:, 0] = 1.0
deg = t.zeros(B, device=dev); vivant = t.ones(B, device=dev)
d_h, g_h, v_h = [], [], []
for _ in range(NPAS):
    v = p.unsqueeze(1) - POS[idx]
    d = v.norm(dim=-1)
    gis = t.rad2deg(t.atan2(v[..., 0], v[..., 1])) % 360
    ec = ((gis - AZI[idx] + 180) % 360 - 180).abs()
    eng = (MSK[idx] > 0.5) & (ec < DEMI_CONE)            # meme definition, meme demi-cone
    d_eng_sb = t.where(eng, d, t.full_like(d, 1e9)).min(dim=1).values
    d_h.append(d_eng_sb.clone()); g_h.append(deg.clone()); v_h.append(vivant.clone())
    deg = deg + degats_du_pas(p, wp, idx) * vivant
    vivant = vivant * (deg < SEUIL_MORT).float()
    dr = -p / p.norm(dim=-1, keepdim=True).clamp(min=1e-6)
    p = p + dr * ALLURES[2] * POSTURES_V[0] * vivant.unsqueeze(-1)

D = t.stack(d_h).cpu().numpy(); G = t.stack(g_h).cpu().numpy(); V = t.stack(v_h).cpu().numpy()
mort = np.zeros_like(G)
for k in range(len(G)):
    fin = min(k + HOR_PAS, len(G) - 1)
    mort[k] = (G[fin] >= SEUIL_MORT) & (G[k] < SEUIL_MORT)
ok = (V > 0.5) & (D < 400)
Ds, Ys = D[ok], mort[ok]
print(f"  SANDBOX {ok.size} pas -> {len(Ys)} ENGAGES ({len(Ys)/ok.size:.1%})"
      f" · mortalite des engages {Ys.mean():.2%}")

print("\n" + "=" * 78)
print(f"  {'tranche':>12} {'ARMA n':>9} {'ARMA':>8} {'SANDBOX n':>10} {'SANDBOX':>9} {'rapport':>9}")
print("  " + "-" * 76)
rap, hors, comp = [], 0, 0
for a, b in TRANCHES:
    ma = (Da >= a) & (Da < b); ms = (Ds >= a) & (Ds < b)
    na, ns = int(ma.sum()), int(ms.sum())
    ya = Ya[ma].mean() if na else float('nan')
    ys = Ys[ms].mean() if ns else float('nan')
    if na >= N_MIN and ns >= N_MIN and ya > 0:
        comp += 1; r = ys / ya; rap.append(r)
        etat = 'OK' if 0.5 <= r <= 2.0 else ('HORS x4' if (r > 4 or r < 0.25) else 'hors')
        hors += 0 if 0.5 <= r <= 2.0 else 1
        print(f"  {a:5d}-{b:<6d} {na:>9d} {ya:>7.2%} {ns:>10d} {ys:>8.2%} {r:>8.2f}  {etat}")
    else:
        print(f"  {a:5d}-{b:<6d} {na:>9d} {ya:>7.2%} {ns:>10d} {ys:>8.2%} {'.':>8}  non comparable")
print("  " + "-" * 76)

print("\n" + "=" * 78)
if comp == 0:
    print("  AUCUNE TRANCHE COMPARABLE. Le pouls ne se prend pas — on l ecrit tel quel.")
else:
    dans = comp - hors
    pire = max(max(rap), 1 / min(rap))
    med = sorted(rap)[len(rap) // 2]
    forme = max(rap) / min(rap)
    print(f"  {dans}/{comp} tranches dans la tolerance (exige >= 2/3) · pire ecart x{pire:.2f}"
          f" (exige < 4) · rapport median {med:.2f} · variation entre tranches x{forme:.2f}")
    if dans / comp >= 2 / 3 and pire < 4:
        print("\n  LE POULS EST BON. La chaine est saine : le x3,5 de la v1 etait la POPULATION,")
        print("  pas le tarif. AUCUNE correction. Affaire close.")
    else:
        print(f"\n  HORS TOLERANCE sur du semblable. Facteur DERIVE : {1/med:.3f} sur le degat")
        print("  par impact. Aucun autre bouton. La nuit rejoue les trois bras, MEME monnaie.")
        if forme > 2.5:
            print(f"  ⚠ l ecart varie d un facteur {forme:.1f} selon la distance : ce n est pas la")
            print("    chaine, c est la FORME de la courbe. Le facteur unique ne suffira pas.")
print("  " + "=" * 76)
