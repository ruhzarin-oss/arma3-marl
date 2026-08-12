#!/usr/bin/env python3
"""verifier_fidelite — LA SANDBOX REPRODUIT-ELLE LES VERDICTS D ARMA ?

On ne demande pas si elle « ressemble » a Arma. On lui fait passer les bancs dont Arma a
DEJA rendu le verdict, et on lit l ecart.

═══ LES ATTENTES, ECRITES AVANT D AVOIR LANCE QUOI QUE CE SOIT ═══

  A1. LE CONTOURNEMENT NE REND PAS INVISIBLE.
      Le gymnase nu donnait 96 % de reussite au debordement la ou le juge externe en donne 0.
      Cause nommee : l arc etait un cone de camera — vu a l infini dedans, invisible dehors.
      ATTENDU : l avantage de prise du flanc s EFFONDRE entre le monde nu et le monde fidele.
      CE QUI LA FERAIT ECHOUER : le flanc garde le meme avantage -> le cliquet ne mord pas.

  A2. LE FLANC FAIT ARRIVER, IL NE PROTEGE PAS.
      Mesure Arma certifiee : +17,3 points de TENUE (p=0,012), ZERO sur l elimination.
      ATTENDU : dans le monde fidele, le flanc ameliore la PRISE sans reduire les PERTES.
      CE QUI LA FERAIT ECHOUER : le flanc reduit fortement les pertes -> le monde rend une
      protection qu Arma n a pas mesuree, et l agent apprendra a se cacher au lieu d entrer.

  A3. LE COUT EST L EXPOSITION PAR METRE GAGNE.
      Mesure Arma : les gagnants ENTRENT — 0,65 contre 1,21 d exposition par metre.
      ATTENDU : la doctrine qui prend le point paie MOINS par metre que celle qui echoue.

  A0. ET D ABORD : AUCUN BOUTON INERTE.
      Un mecanisme allume qui ne change rien est pire qu un mecanisme eteint : il donne la
      certitude d une fidelite qu on n a pas. `alerte_niv` a ete calcule puis JETE pendant des
      semaines. Chaque bouton du monde fidele doit deplacer une grandeur, sinon il est nomme.
      CE QUI LA FERAIT ECHOUER : un bouton dont l extinction ne change rien -> il est mort.
"""
import math, sys, torch
sys.path.insert(0, "/home/younes/arma3-marl")
from assault_terrain import AssaultTerrain
from monde_fidele import MONDE_ARMA

EPISODES, PAS, SEED, DEV = 256, 60, 7, "cuda:0"

# le monde NU : les defauts historiques d assault_terrain, rien d allume.
MONDE_NU = dict(A=4, D=8, def_line=True, def_arc=math.pi / 3, def_rand=True,
                secure_task=True, secure_only=True, postures=True, hull=True)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def frontal(e, t):
    return cap(-e.apx, -e.apy)


def flanc(e, t, n_fixe=2, pas_crochet=14):
    act = cap(-e.apx, -e.apy)
    d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
    fixe = torch.zeros(e.N, e.A, dtype=torch.bool, device=e.dev); fixe[:, :n_fixe] = True
    a_portee = d_obj < e.fire_range * 0.9
    act = torch.where(fixe & a_portee, torch.full_like(act, 9), act)
    if t < pas_crochet:
        act = torch.where(~fixe, cap(-e.apy, e.apx), act)
    return act


DOCTRINES = {"frontal": frontal, "flanc": flanc}


def joue(cfg, doctrine, seed=SEED):
    e = AssaultTerrain(num_envs=EPISODES, seed=seed, device=DEV, max_steps=PAS, **cfg)
    e.reset()
    N = e.N
    pris = torch.zeros(N, dtype=torch.bool, device=e.dev)
    fini = torch.zeros(N, dtype=torch.bool, device=e.dev)
    pertes = torch.zeros(N, device=e.dev)
    expo = torch.zeros(N, device=e.dev)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1); dmin = d0.clone()
    f = DOCTRINES[doctrine]
    for t in range(PAS):
        _, _, done, info = e.step(f(e, t), auto_reset=False)
        viv = ~fini
        pris |= (info["took"] & viv)
        pertes = torch.where(viv, info["losses"].float(), pertes)
        expo += info["exposed"] * viv.float()
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        dmin = torch.minimum(dmin, torch.where(viv, d, dmin))
        fini |= done.bool()
        if bool(fini.all()):
            break
    gagne = (d0 - dmin).clamp(min=1.0)
    return dict(prise=100.0 * float(pris.float().mean()),
                pertes=float(pertes.mean()),
                expo_m=float((expo / gagne).mean()))


def bloc(nom, cfg):
    r = {d: joue(cfg, d) for d in DOCTRINES}
    print(f"\n  {nom}")
    print(f"    {'doctrine':<10}{'prise':>9}{'pertes':>9}{'expo/m':>9}")
    for d, v in r.items():
        print(f"    {d:<10}{v['prise']:>8.1f}%{v['pertes']:>9.2f}{v['expo_m']:>9.3f}")
    ec = r["flanc"]["prise"] - r["frontal"]["prise"]
    dp = r["flanc"]["pertes"] - r["frontal"]["pertes"]
    print(f"    -> le flanc rend {ec:+.1f} pt de prise et {dp:+.2f} de pertes")
    return r, ec, dp


print("=" * 76)
print("  A0 — AUCUN BOUTON INERTE   (un mecanisme qui ne change rien ment sur la fidelite)")
print("=" * 76)
ref = joue(MONDE_ARMA, "flanc")["prise"]
morts = []
for bouton in ("alerte", "arc_latence_s", "cible_unique", "supp_residuel",
               "frein_feu", "nav_around", "courbe", "hull"):
    off = dict(MONDE_ARMA)
    off[bouton] = {"alerte": False, "cible_unique": False, "nav_around": False,
                   "hull": False}.get(bouton, None)
    if bouton == "frein_feu":
        off[bouton] = 0.0
    if bouton == "courbe":
        for k in ("courbe", "tir_par_pas", "degat_par_impact"):
            off[k] = None
    try:
        v = joue(off, "flanc")["prise"]
    except Exception as ex:
        print(f"    {bouton:<16} INCONSTRUCTIBLE eteint : {str(ex)[:50]}")
        continue
    ecart = v - ref
    vivant = abs(ecart) > 1.0
    print(f"    {'VIVANT' if vivant else 'INERTE':>7}  {bouton:<16} "
          f"prise {ref:.1f}% -> {v:.1f}%  ({ecart:+.1f} pt)")
    if not vivant:
        morts.append(bouton)

print("\n" + "=" * 76)
print("  A1 / A2 / A3 — LES VERDICTS CERTIFIES D ARMA")
print("=" * 76)
_, ec_nu, dp_nu = bloc("MONDE NU — les defauts historiques", MONDE_NU)
r_fi, ec_fi, dp_fi = bloc("MONDE FIDELE — tout ce qui est mesure, allume", MONDE_ARMA)

print("\n  LECTURE, contre les attentes deposees plus haut")
print("  " + "-" * 72)
a1 = abs(ec_fi) < abs(ec_nu)
print(f"    {'PASSE' if a1 else 'TOMBE':>6}  A1 le contournement ne rend plus invisible")
print(f"            avantage du flanc : {ec_nu:+.1f} pt (nu) -> {ec_fi:+.1f} pt (fidele)")
a2 = dp_fi > -0.15
print(f"    {'PASSE' if a2 else 'TOMBE':>6}  A2 le flanc fait arriver, il ne protege pas")
print(f"            effet sur les pertes : {dp_fi:+.2f}  (Arma : zero sur l elimination)")
gagnant = max(r_fi, key=lambda d: r_fi[d]["prise"])
perdant = min(r_fi, key=lambda d: r_fi[d]["prise"])
a3 = r_fi[gagnant]["expo_m"] < r_fi[perdant]["expo_m"]
print(f"    {'PASSE' if a3 else 'TOMBE':>6}  A3 le gagnant paie moins par metre")
print(f"            {gagnant} {r_fi[gagnant]['expo_m']:.3f} contre "
      f"{perdant} {r_fi[perdant]['expo_m']:.3f}")
if morts:
    print(f"\n    ⚠ BOUTONS INERTES : {morts} — allumes, sans effet mesurable.")
print("\n  Ce banc ne certifie pas la sandbox. Il dit sur quels verdicts elle suit Arma")
print("  et sur lesquels elle s en ecarte — c est ce qu on peut honnetement en dire.")
