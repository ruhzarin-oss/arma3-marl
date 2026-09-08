#!/usr/bin/env python3
"""HMT-19 — CONTROLE (ii) et l HISTOGRAMME DE f, sur le terrain GENERE.

Fable, 08/09 : « Ne laisse pas (i) bloquer la nuit : (ii) n en depend pas — lance B au
gymnase canal eteint puis allume sur `hm`, et lis (ii) d abord, c est l ancre. »

Et : « Sur sites plats, `hm` donnera f dans {0, 1} sauf couche : tu fabriquerais une
continuite que R ne contient pas — JOURNALISE L HISTOGRAMME DE f avant de lui faire porter
l exposant 0,72. » C est fait ici, et c est la premiere chose qu on lit.

⚠️ Ce banc ne CONCLUT PAS le controle (ii) : l ancre B d Arma n existe pas encore (nuit 1 en
attente de la file). Il pose les deux niveaux du gymnase, canal eteint et allume, pour qu ils
soient prets a etre confrontes des que l ancre tombe. Il rend aussi l histogramme, qui lui
peut trancher tout de suite.
"""
import sys, json, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from monde_fidele import MONDE_ARMA
from assault_terrain import AssaultTerrain
from distillation import cible_shamal
import math

# ⛔ FAUTE CORRIGEE LE 08/09 : j avais etiquete « B » ce qui etait la DOCTRINE scriptee.
# Le bras B du dispositif d Arma, c est 4 fixeurs + 4 assaillants FRONTAUX — rien d autre.
# Un niveau lu sur la mauvaise action ne se compare a aucune ancre.
def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)

def bras_B(e, t, n_fixe=4):
    a = cap(-e.apx, -e.apy)
    a[:, :n_fixe] = 9            # les quatre premiers FIXENT (tirent), les quatre autres assaillent
    return a
import canal_cwr as CANAL

GRAINES = [901, 902, 903, 904, 905, 906]
N = int(sys.argv[1]) if len(sys.argv) > 1 else 192
PAS = 92
SORTIE = "/home/younes/arma3-marl/controle_ii.json"

BRAS = {"canal ETEINT": dict(), "canal ALLUME sur hm": dict(canal_cwr=CANAL.constantes_arma3())}


def monde(n, seed, sur):
    return AssaultTerrain(num_envs=n, seed=seed, device="cuda:0", max_steps=PAS,
                          A=8, D=4, R_spawn=220.0, terr_R=260.0, **dict(MONDE_ARMA, **sur))


def jouer(e):
    e.reset()
    pris = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    dv = dn = 0.0; nv = nn = 0
    for t in range(PAS):
        e.step(bras_B(e, t), auto_reset=False)
        vu = (e._vu_geo > 0.5); viv = e._aalive(); d = e.last_dmg_in
        dv += float((d * (vu & viv)).sum()); nv += int((vu & viv).sum())
        dn += float((d * (~vu & viv)).sum()); nn += int((~vu & viv).sum())
        info = e.last_info if hasattr(e, "last_info") else None
        fini |= torch.zeros_like(fini)
    return 100.0 * float(pris.float().mean()), dv, nv, dn, nn


def jouer2(e):
    """Comme `jouer` mais en lisant `info['took']`, la prise officielle du monde."""
    e.reset()
    pris = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
    dv = dn = 0.0; nv = nn = 0
    for t in range(PAS):
        _, _, done, info = e.step(bras_B(e, t), auto_reset=False)
        pris |= info["took"] & ~fini
        fini |= done.bool()
        vu = (e._vu_geo > 0.5); viv = e._aalive(); d = e.last_dmg_in
        dv += float((d * (vu & viv)).sum()); nv += int((vu & viv).sum())
        dn += float((d * (~vu & viv)).sum()); nn += int((~vu & viv).sum())
        if bool(fini.all()):
            break
    return 100.0 * float(pris.float().mean()), dv, nv, dn, nn


res = {}
for nom, sur in BRAS.items():
    pr = []; DV = NV = DN = NN = 0.0; hist = torch.zeros(6, device="cuda:0")
    for g in GRAINES:
        e = monde(N, g, sur)
        p, a, b, c, d = jouer2(e)
        pr.append(p); DV += a; NV += b; DN += c; NN += d
        if getattr(e, "hist_frac", None) is not None:
            hist += e.hist_frac
    m = sum(pr) / len(pr)
    et = (sum((x - m) ** 2 for x in pr) / max(len(pr) - 1, 1)) ** 0.5
    mv = DV / max(NV, 1); mn = DN / max(NN, 1)
    res[nom] = dict(prise=m, demi_ic=1.96 * et / len(pr) ** 0.5,
                    dmg_vu=mv, dmg_non_vu=mn,
                    rapport=(mv / mn) if mn > 0 else None,
                    hist=[float(x) for x in hist.tolist()])
    print("  %-22s prise %5.1f %% ± %.1f · vu %.5f · non vu %.5f · rapport %s"
          % (nom, m, res[nom]["demi_ic"], mv, mn,
             ("%.2f" % (mv / mn)) if mn > 0 else "INFINI"), flush=True)

print("\n  " + "=" * 74)
h = res["canal ALLUME sur hm"]["hist"]
tot = sum(h) or 1
print("  HISTOGRAMME DE f (fraction de corps visible), canal allume, terrain GENERE")
print("  case        " + "  ".join("%.2f-%.2f" % (i / 6, (i + 1) / 6) for i in range(6)))
print("  part        " + "  ".join("%7.1f%%" % (100 * x / tot) for x in h))
extremes = (h[0] + h[-1]) / tot
print("\n  part dans les cases EXTREMES (f proche de 0 ou de 1) : %.1f %%" % (100 * extremes))
if extremes > 0.75:   # seuil resserre : 0,90 laissait passer un f quasi binaire
    print("  ⛔ f est QUASI BINAIRE sur le terrain genere : la continuite n existe pas dans R.")
    print("     ⚠️ NE PAS faire porter l exposant 0,72 a cette grandeur — elle n a pas de milieu.")
    print("     C est exactement ce que Fable annoncait le 08/09.")
else:
    print("  ✔ f a un MILIEU peuple : l exposant mesure a de quoi s appliquer.")

print("\n  CONTROLE (ii) — les deux niveaux, prets pour l ancre")
for nom, v in res.items():
    print("    %-22s B = %5.1f %%  [%.1f ; %.1f]"
          % (nom, v["prise"], v["prise"] - v["demi_ic"], v["prise"] + v["demi_ic"]))
print("    ⚠️ NON CONCLU : l ancre B d Arma n existe pas encore (nuit 1 en attente de la file).")
json.dump(res, open(SORTIE, "w"), indent=1, ensure_ascii=False)
print("  ecrit : %s" % SORTIE)
