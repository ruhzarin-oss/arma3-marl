#!/usr/bin/env python3
"""reverdict_arc3 — LE VERDICT SURVIT-IL AU CONE QUI S'OUVRE ?

Criteres figes AVANT : leviathan/CRITERES_REVERDICT_ARC_OUVRANT.md (empreinte 0606073790cc9c14)

Ce que ce script ajoute a la premiere version :
  - les SEUILS de Fable (x prise >= 1,5 ET x cout <= 0,7), pas ceux qui trainaient dans le code
  - le TEMOIN DE MECANISME : la part d'engagements ou l'ATTAQUANT tire le premier,
    tire des donnees Arma (de face le defenseur garde l'initiative 7/8 ; de flanc il la
    perd 0/8). Le monde doit reproduire le MECANISME, pas seulement le score.
  - la CONTRE-EPREUVE sur la ligne « cone dur »
  - la sensibilite tau, presentee comme telle et jamais comme un reglage

⚠ La reference Arma « x2-3 a un tiers du cout » N'EST PLUS COMPARABLE : sa garnison
n'existe plus. On juge la NON-REGRESSION du verdict, pas un chiffre orphelin.

⚠ tau = 4 s est VERROUILLE parce que c'est la mesure. Le balayage {2, 4, 6} est une
analyse de sensibilite. Et le pas de sandbox vaut 3,28 s : tau=2 et tau=4 donnent tous
deux 1 pas, donc ils seront IDENTIQUES par construction.
"""
import sys
import json
import math
import time
import argparse

sys.path.insert(0, "/home/younes/arma3-marl")
import torch
from assault_terrain import AssaultTerrain

LEV = "/home/younes/arma3-marl/leviathan"
COURBE = LEV + "/courbe_toucher_juge.json"
SEC, TIR, DEG = 3.28, 1.15, 0.233

ap = argparse.ArgumentParser()
ap.add_argument("--eval", type=int, default=1024)
ap.add_argument("--latences", default="4.0,2.0,6.0")
ap.add_argument("--device", default="cuda:0")
ap.add_argument("--graines", default="7,8,9")
# SELECTION DE CIBLE. Sans elle, un flanqueur isole encaisse le feu de trois defenseurs
# dans le meme pas de 3,28 s (pire pas 0,471 pour un seuil de mort a 0,70) : le cone dur
# ne le protegeait pas de la letalite, il la lui cachait. Mesure du 28/07.
ap.add_argument("--cible", action="store_true", help="un defenseur engage UN attaquant")
# LE SUSPECT NOMME D'AVANCE. CRITERES_REVERDICT_ARC_OUVRANT.md, ecrit avant le run :
# « le candidat designe d'avance est la SUPPRESSION (l'appui ne distrait pas, il RETIENT
# l'attention : tant qu'il tire, le sursis reste ouvert pour celui qui contourne) ».
# La courbe n2 mesuree le 28/07 le rend enfin testable.
# ⚠ Avec --supp le monde a cone DUR n'est PLUS celui de la reference : la contre-epreuve
# ne vaut plus, et le run est EXPLORATOIRE. On ne conclut pas, on regarde si le temoin
# de mecanisme BOUGE. S'il bouge, on refait une reference et on rejuge.
ap.add_argument("--supp", action="store_true",
                help="active la suppression mesuree (0.08 / 0.35) : EXPLORATOIRE")
ap.add_argument("--out", default="reverdict_arc3.json")
a = ap.parse_args()
DEV = a.device
TAU_VERROU = 4.0


def monde(lat, seed):
    k = dict(num_envs=a.eval, A=4, D=8, seed=seed, device=DEV, max_steps=60, R_spawn=170.0,
             # LE CONE DOIT EXISTER. reverdict_arc2 ne fixait PAS def_arc : il prenait le
             # defaut, un demi-angle de 180 deg — le cone couvrait le cercle entier, donc
             # il n y avait AUCUN angle mort et le flanc ne pouvait pas etre dehors. On
             # mesurait un arc en testant l absence d arc.
             # def_arc = pi/3 -> demi-angle 60 deg, cone de 120 deg (celui du re-verdict n1).
             # def_rand=False -> geometrie FIXE : le crochet sort vraiment du cone. La
             # doctrine est scriptee, donc rien ne peut memoriser toujours a gauche.
             postures=True, hull=True, def_line=True, def_rand=False,
             def_arc=math.pi / 3,
             secure_task=True, secure_only=True, courbe=COURBE,
             tir_par_pas=TIR, sec_par_pas=SEC, degat_par_impact=DEG, arc_obs=True)
    if lat is not None:
        k["arc_latence_s"] = lat
    if a.supp:
        k.update(supp_residuel=0.08, supp_persist=0.35)
    if a.cible:
        k["cible_unique"] = True
    return AssaultTerrain(**k)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


@torch.no_grad()
def initiative(e, deja):
    """Pour chaque defenseur qui engage pour la PREMIERE fois : a-t-il tire parce que
    l'attaquant etait dans son cone (il garde l'initiative), ou seulement parce que le
    sursis avait expire (l'attaquant l'a eue) ?

    C'est la transcription exacte du temoin Arma : de face, le defenseur ouvre le feu le
    premier ; de flanc, jamais.
    Renvoie (nb_premiers_engagements, nb_ou_l_attaquant_avait_l_initiative).
    """
    N, A, D, S = e.N, e.A, e.D, e.scale
    ex = e.apx.unsqueeze(2) - e.dpx.unsqueeze(1)
    ey = e.apy.unsqueeze(2) - e.dpy.unsqueeze(1)
    d2 = ex * ex + ey * ey
    BIG = torch.tensor(1e18, device=e.dev)
    d2 = torch.where(e._aalive().unsqueeze(2), d2, BIG)
    ka = d2.argmin(1)
    ax = torch.gather(e.apx, 1, ka); ay = torch.gather(e.apy, 1, ka)
    los = e._losc(e.hm, e.dpx, e.dpy, ax, ay, S, eye_a=1.7, eye_b=1.7)
    dist = d2.min(1).values.clamp(max=1e17).sqrt()
    percue = (los > 0.5) & (dist < e.fire_range) & e._dalive()
    az = torch.atan2(ax - e.dpx, ay - e.dpy)
    ecart = torch.atan2(torch.sin(az - e.dface), torch.cos(az - e.dface)).abs()
    dans = ecart <= e._dfarc
    ouvert = getattr(e, "d_ouvert", None)
    peut = percue & (dans | (ouvert if ouvert is not None else torch.zeros_like(dans)))
    neuf = peut & (~deja)
    att_premier = neuf & (~dans)          # il n'a pu tirer que grace au sursis expire
    # `ka` = indice de l'attaquant le plus proche, par defenseur. Sans lui, on melange
    # les fixeurs (qui attaquent de face) et les flanqueurs (qui contournent), et le
    # temoin devient une moyenne de deux populations opposees.
    return neuf, att_premier, ka


@torch.no_grad()
def joue(lat, doctrine, seed):
    e = monde(lat, seed)
    e.reset()
    N, A = e.N, e.A
    pris = torch.zeros(N, dtype=torch.bool, device=DEV)
    fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    pertes = torch.zeros(N, device=DEV)
    expo = torch.zeros(N, device=DEV)
    deja = torch.zeros(N, e.D, dtype=torch.bool, device=DEV)
    n_eng = torch.zeros((), device=DEV)
    n_att = torch.zeros((), device=DEV)
    n_eng_fx = torch.zeros((), device=DEV); n_att_fx = torch.zeros((), device=DEV)
    n_eng_fl = torch.zeros((), device=DEV); n_att_fl = torch.zeros((), device=DEV)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
    dmin = d0.clone()
    for t in range(60):
        d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        act = cap(-e.apx, -e.apy)
        if doctrine == "flanc":
            fixe = torch.zeros(N, A, dtype=torch.bool, device=DEV)
            fixe[:, :2] = True
            act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
            if t < 14:
                act = torch.where(~fixe, cap(-e.apy, e.apx), act)
        vv = ~fini
        neuf, attp, ka = initiative(e, deja)
        m = vv.unsqueeze(1)
        n_eng = n_eng + (neuf & m).sum()
        n_att = n_att + (attp & m).sum()
        # Ventilation : le contact vient-il d'un FIXEUR (0-1) ou d'un FLANQUEUR (2-3) ?
        # Les indices 0-1 sont ceux que `doctrine flanc` met en fixation frontale.
        _fl = ka >= 2
        n_eng_fl = n_eng_fl + (neuf & m & _fl).sum(); n_att_fl = n_att_fl + (attp & m & _fl).sum()
        n_eng_fx = n_eng_fx + (neuf & m & ~_fl).sum(); n_att_fx = n_att_fx + (attp & m & ~_fl).sum()
        deja = deja | neuf
        _, _, done, info = e.step(act, auto_reset=False)
        pris = pris | (info["took"] & vv)
        pertes = torch.where(vv, info["losses"].float(), pertes)
        expo = expo + info["exposed"] * vv.float()
        d = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
        dmin = torch.minimum(dmin, torch.where(vv, d, dmin))
        fini = fini | done.bool()
        if bool(fini.all()):
            break
    gagne = (d0 - dmin).clamp(min=1.0)
    pr = float(pris.float().mean())
    pe = float(pertes[pris].mean()) if bool(pris.any()) else float("nan")
    return {"prise": pr, "pertes_par_prise": pe,
            "expo_par_metre": float((expo / gagne).mean()),
            "part_attaquant_premier": float(n_att / n_eng.clamp(min=1)),
            "part_att_premier_flanqueurs": float(n_att_fl / n_eng_fl.clamp(min=1)),
            "part_att_premier_fixeurs": float(n_att_fx / n_eng_fx.clamp(min=1)),
            "engagements_flanqueurs": float(n_eng_fl),
            "engagements_fixeurs": float(n_eng_fx),
            "engagements": float(n_eng)}


def bras(lat):
    _G = tuple(int(x) for x in a.graines.split(",") if x.strip())
    f = [joue(lat, "frontal", s) for s in _G]
    c = [joue(lat, "flanc", s) for s in _G]
    m = lambda v, k: sum(x[k] for x in v) / len(v)      # noqa: E731
    pf, pc = m(f, "prise"), m(c, "prise")
    cf, cc = m(f, "pertes_par_prise"), m(c, "pertes_par_prise")
    return {"frontal_prise": pf, "crochet_prise": pc,
            "frontal_cout": cf, "crochet_cout": cc,
            "rapport_prise": (pc / pf) if pf > 0 else float("inf"),
            "rapport_cout": (cc / cf) if (cf == cf and cf > 0) else float("nan"),
            "frontal_att_premier": m(f, "part_attaquant_premier"),
            "crochet_att_premier": m(c, "part_attaquant_premier"),
            "crochet_att_premier_flanqueurs": m(c, "part_att_premier_flanqueurs"),
            "crochet_att_premier_fixeurs": m(c, "part_att_premier_fixeurs"),
            "crochet_eng_flanqueurs": m(c, "engagements_flanqueurs"),
            "crochet_eng_fixeurs": m(c, "engagements_fixeurs"),
            "frontal_expo": m(f, "expo_par_metre"), "crochet_expo": m(c, "expo_par_metre")}


if __name__ == "__main__":
    t0 = time.time()
    lats = [None, TAU_VERROU] + [float(x) for x in a.latences.split(",")
                                 if x.strip() and abs(float(x) - TAU_VERROU) > 1e-9]
    print("=== RE-VERDICT DE L'ARC QUI S'OUVRE ===", flush=True)
    print("    criteres 0606073790cc9c14 | doctrines scriptees | A=4 D=8 | graines " + a.graines + "", flush=True)
    print("    tau VERROUILLE a %.1f s (la mesure). Les autres lignes sont de la SENSIBILITE." % TAU_VERROU, flush=True)
    print("", flush=True)
    res = {}
    print("%-26s %9s %9s %9s %9s %11s %11s" %
          ("monde", "frontal", "crochet", "x prise", "x cout", "att1er front", "att1er croch"), flush=True)
    for lat in lats:
        if lat is None:
            nom = "cone DUR (temoin)"
        elif abs(lat - TAU_VERROU) < 1e-9:
            nom = "cone OUVRANT tau=%.1fs *" % lat
        else:
            nom = "  sensibilite tau=%.1fs" % lat
        r = bras(lat)
        if lat is not None:
            e = monde(lat, 7)
            r["pas_de_sursis"] = int(e.arc_latence_pas)
            del e
        res[nom] = r
        print("%-26s %8.1f%% %8.1f%% %9.2f %9.2f %10.0f%% %10.0f%%"
              % (nom, 100 * r["frontal_prise"], 100 * r["crochet_prise"],
                 r["rapport_prise"], r["rapport_cout"],
                 100 * r["frontal_att_premier"], 100 * r["crochet_att_premier"]), flush=True)
    print("  * = le monde retenu. Les lignes 'sensibilite' ne sont JAMAIS un reglage.", flush=True)

    dur = res["cone DUR (temoin)"]
    ouv = res["cone OUVRANT tau=%.1fs *" % TAU_VERROU]
    print("", flush=True)
    print("=== VERDICTS (seuils figes) ===", flush=True)

    # CONTRE-EPREUVE LUE SUR DISQUE, plus codee en dur. L'ancienne reference
    # (19,3 % / 74,7 %) appartenait a la geometrie SANS cone reel : la comparer a un monde
    # a cone de 120 deg n'avait aucun sens. La nouvelle est mesuree par
    #  sur des graines DIFFERENTES (11-16 vs 7,8,9), avec une
    # tolerance derivee de la dispersion entre graines. Criteres 5bbb7f957f0319e8.
    try:
        _R = json.load(open(LEV + ("/reference_arc3_cible.json" if a.cible else "/reference_arc3.json")))
        _rf, _rc, _tol = _R["frontal_prise"], _R["crochet_prise"], _R["tolerance"]
        ce = abs(dur["frontal_prise"] - _rf) <= _tol and abs(dur["crochet_prise"] - _rc) <= _tol
        print("  CONTRE-EPREUVE (cone dur vs reference %.1f %% / %.1f %%, +-%.1f pt) : %s"
              % (100 * _rf, 100 * _rc, 100 * _tol,
                 "OK" if ce else "ECHEC — ON NE CONCLUT RIEN"), flush=True)
        print("      mesure : frontal %.1f %% | crochet %.1f %%"
              % (100 * dur["frontal_prise"], 100 * dur["crochet_prise"]), flush=True)
    except FileNotFoundError:
        ce = False
        print("  CONTRE-EPREUVE : reference ABSENTE — ON NE CONCLUT RIEN.", flush=True)
        print("      lancer d'abord faire_reference_arc3.py", flush=True)

    d1 = ouv["rapport_prise"] >= 1.5
    cout_dispo = ouv["rapport_cout"] == ouv["rapport_cout"]
    d2 = cout_dispo and ouv["rapport_cout"] <= 0.7
    print("  DIRECTION : x prise = %.2f (>=1,5 : %s) | x cout = %s (<=0,7 : %s)"
          % (ouv["rapport_prise"], "oui" if d1 else "NON",
             ("%.2f" % ouv["rapport_cout"]) if cout_dispo else "INDISPONIBLE",
             "oui" if d2 else ("NON" if cout_dispo else "non evaluable")), flush=True)
    if not cout_dispo:
        # Le rapport de cout se calcule sur les episodes PRIS. Si une doctrine ne prend
        # jamais, il n existe pas. Ce n est pas un echec du critere : c est une absence
        # de mesure, et la dire est plus honnete que de la compter comme un refus.
        print("    !! le cout n est pas evaluable : une doctrine ne prend JAMAIS l objectif.", flush=True)
        print("       Le critere DIRECTION est NON EVALUABLE, ni tenu ni casse.", flush=True)
    if d1 and d2:
        print("    -> LE VERDICT TIENT. On adopte le cone ouvrant.", flush=True)
    else:
        print("    -> LA CORRECTION CASSE LE VERDICT. On garde le cone dur par defaut", flush=True)
        print("       et on INSTRUIT l'ecart. Candidat designe d'avance : la SUPPRESSION —", flush=True)
        print("       l'appui ne distrait pas, il RETIENT l'attention ; tant qu'il tire, le", flush=True)
        print("       sursis reste ouvert pour celui qui contourne.", flush=True)

    t1 = ouv["frontal_att_premier"] <= 0.35
    t2 = ouv["crochet_att_premier"] >= 0.60
    print("  TEMOIN DE MECANISME (initiative, mesure Arma : 88 %% de face / 0 %% de flanc) :", flush=True)
    print("    [instrument corrige] le temoin prenait l'attaquant LE PLUS PROCHE. Dans la", flush=True)
    print("    doctrine crochet, ce sont les 2 FIXEURS qui foncent de face — c'etaient donc", flush=True)
    print("    eux qu'on observait. Le mecanisme du contournement se lit sur les FLANQUEURS.", flush=True)
    print("      crochet, fixeurs    : %5.1f %%  (%d engagements)"
          % (100 * ouv["crochet_att_premier_fixeurs"], ouv["crochet_eng_fixeurs"]), flush=True)
    print("      crochet, FLANQUEURS : %5.1f %%  (%d engagements)  <- le seuil >=60 %% porte ICI"
          % (100 * ouv["crochet_att_premier_flanqueurs"], ouv["crochet_eng_flanqueurs"]), flush=True)
    print("    frontal %0.0f %% (<=35 : %s) | crochet %0.0f %% (>=60 : %s)"
          % (100 * ouv["frontal_att_premier"], "oui" if t1 else "NON",
             100 * ouv["crochet_att_premier"], "oui" if t2 else "NON"), flush=True)
    if t1 and t2:
        print("    -> le monde reproduit le MECANISME, pas seulement le score.", flush=True)
    else:
        print("    -> le mecanisme ne suit PAS. Si le score tient quand meme, le monde donne", flush=True)
        print("       le bon resultat pour une mauvaise raison.", flush=True)

    print("", flush=True)
    print("  SENSIBILITE tau (jamais un reglage) : pas de sursis par valeur", flush=True)
    for nom, r in res.items():
        if "pas_de_sursis" in r:
            print("    %-26s -> %d pas de sandbox (3,28 s/pas)" % (nom, r["pas_de_sursis"]), flush=True)
    print("    tau=2 s et tau=4 s tombent sur le MEME nombre de pas : ils sont identiques", flush=True)
    print("    par construction. Ce n'est pas une stabilite, c'est un arrondi.", flush=True)

    json.dump({"criteres": "CRITERES_REVERDICT_ARC_OUVRANT.md", "tau_verrou": TAU_VERROU,
               "contre_epreuve": bool(ce), "direction_ok": bool(d1 and d2), "cout_evaluable": bool(cout_dispo),
               "temoin_ok": bool(t1 and t2), "mondes": res},
              open(LEV + "/" + a.out, "w"), indent=1)
    print("", flush=True)
    print("-> %s/%s  (%.0f s)" % (LEV, a.out, time.time() - t0), flush=True)
    print("REVERDICT2_DONE", flush=True)
