#!/usr/bin/env python3
"""etalons — LE RITUEL. Avant toute mesure, le monde rejoue trois scenes connues.

Pourquoi ce rituel existe : le 10e defaut silencieux. L'exposimetre comptait ZERO au-dela
de 110 m (`inr = dist < fire_range`), precisement la ou le crochet fait l'essentiel de son
detour. Le defaut a survecu des semaines parce que RIEN ne le regardait.

Un etalon est une scene dont on connait le resultat, avec une bande de tolerance. Tout run
ulterieur commence par les rejouer ; ecart hors bande = la branche s'arrete et le DIT.

EXIGENCE DE CONCEPTION, a cause de ce defaut precis : **au moins un etalon doit passer
l'essentiel de son temps AU-DELA DE 110 m**. L'etalon doit mordre exactement la ou
l'exposimetre etait aveugle. On le VERIFIE, on ne le suppose pas.

  etalons.py --poser      etablit la reference et les bandes -> etalons_reference.json
  etalons.py --verifier   rejoue et compare ; sortie 2 si un etalon sort de sa bande
"""
import sys
import os
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
REF = LEV + "/etalons_reference.json"

ap = argparse.ArgumentParser()
ap.add_argument("--poser", action="store_true")
ap.add_argument("--verifier", action="store_true")
ap.add_argument("--eval", type=int, default=1024)
ap.add_argument("--device", default="cuda:0")
ap.add_argument("--pt", default=None, help="poids d un agent pour l etalon APPRIS")
a = ap.parse_args()
DEV = a.device


def monde(seed):
    return AssaultTerrain(num_envs=a.eval, A=4, D=8, seed=seed, device=DEV, max_steps=60,
                          R_spawn=170.0, postures=True, hull=True, def_line=True,
                          def_rand=True, secure_task=True, secure_only=True, courbe=COURBE,
                          tir_par_pas=TIR, sec_par_pas=SEC, degat_par_impact=DEG, arc_obs=True)


def cap(dx, dy):
    return (torch.round(torch.atan2(dx, dy) / (math.pi / 4.0)).long() % 8)


def monde_carte(seed):
    """Le monde de la carte typee : c'est LUI qu'il faut pour etalonner un agent entraine
    dessus. Un agent ne s'etalonne pas dans un monde qui n'a pas ses canaux."""
    sys.path.insert(0, LEV)
    # lire_carte parse ses arguments A L'IMPORT : sans ce garde-fou il avale les notres
    # et sort en erreur. Constate avant de lancer, pas apres.
    _av = sys.argv[:]; sys.argv = [sys.argv[0]]
    try:
        import lire_carte as LC
    finally:
        sys.argv = _av
    LC.KC = 9
    return LC.MondeCarte(num_envs=a.eval, A=4, D=8, seed=seed, device=DEV, max_steps=60,
                         R_spawn=170.0, postures=True, hull=True, def_line=True,
                         def_arc=math.pi / 3, def_rand=True, secure_task=True,
                         secure_only=True, courbe=COURBE, tir_par_pas=TIR, sec_par_pas=SEC,
                         degat_par_impact=DEG, arc_obs=True, champ_risque=False,
                         kc=9, empan=90.0)


@torch.no_grad()
def joue(nom, seed, net=None):
    e = monde_carte(seed) if nom == "agent" else monde(seed)
    obs = e.reset()
    N, A = e.N, e.A
    pris = torch.zeros(N, dtype=torch.bool, device=DEV)
    fini = torch.zeros(N, dtype=torch.bool, device=DEV)
    pertes = torch.zeros(N, device=DEV)
    expo = torch.zeros(N, device=DEV)
    loin = torch.zeros((), device=DEV)      # homme-pas passes au-dela de 110 m
    total = torch.zeros((), device=DEV)
    d0 = torch.sqrt(e.apx ** 2 + e.apy ** 2).mean(1)
    dmin = d0.clone()
    for t in range(60):
        d_obj = torch.sqrt(e.apx ** 2 + e.apy ** 2)
        vv = ~fini
        m = vv.unsqueeze(1).float() * e._aalive().float()
        loin = loin + ((d_obj > 110.0).float() * m).sum()
        total = total + m.sum()
        if nom == "frontal":
            act = cap(-e.apx, -e.apy)
        elif nom == "crochet":
            act = cap(-e.apx, -e.apy)
            fixe = torch.zeros(N, A, dtype=torch.bool, device=DEV)
            fixe[:, :2] = True
            act = torch.where(fixe & (d_obj < e.fire_range * 0.9), torch.full_like(act, 9), act)
            if t < 14:
                act = torch.where(~fixe, cap(-e.apy, e.apx), act)
        elif nom == "guet_140":
            # ETALON CONCU POUR MORDRE AU-DELA DE 110 m : on approche jusqu'a 140 m, puis
            # on TIENT. Si la falaise d'exposition a 110 m revenait, l'exposition de cet
            # etalon tomberait a zero — et c'est exactement ce qu'on veut voir tomber.
            act = torch.where(d_obj > 140.0, cap(-e.apx, -e.apy), torch.full_like(d_obj, 8).long())
        else:
            act = torch.distributions.Categorical(logits=net.a_logits(obs)).sample()
        obs, _, done, info = e.step(act, auto_reset=False)
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
            "prise_a_pertes": (pr / pe) if (pe == pe and pe > 0) else float("nan"),
            "expo_totale": float(expo.mean()),
            "expo_par_metre": float((expo / gagne).mean()),
            "part_au_dela_110m": float(loin / total.clamp(min=1)),
            "distance_min": float(dmin.mean())}


def charge_agent():
    """Un agent au champ : on prend le premier .pt disponible parmi les cases de la nuit."""
    import glob
    from train_koth_gpu import Net
    cands = sorted(glob.glob(LEV + "/carte_dense_g*.pt"))
    if a.pt:
        cands = [a.pt] + cands
    if not cands:
        return None, None
    e = monde_carte(7)
    o = e.reset().shape[-1]
    del e
    for p in cands:
        try:
            n = Net(o, 13).to(DEV)
            n.load_state_dict(torch.load(p, map_location=DEV))
            n.eval()
            print("    agent charge : %s (O=%d)" % (os.path.basename(p), o), flush=True)
            return n, os.path.basename(p)
        except Exception as x:
            print("    (%s illisible : %s)" % (os.path.basename(p), str(x)[:80]), flush=True)
            continue
    return None, None


CLES = ["prise", "pertes_par_prise", "prise_a_pertes", "expo_totale", "expo_par_metre",
        "part_au_dela_110m", "distance_min"]


def moyenne_et_bande(runs):
    """La bande n'est pas choisie : elle est MESUREE. Trois graines d'evaluation, bande =
    moyenne +- 3 ecarts-types, avec un plancher pour ne pas serrer plus que le bruit."""
    out = {}
    for k in CLES:
        v = [r[k] for r in runs if r[k] == r[k]]
        if not v:
            out[k] = None
            continue
        m = sum(v) / len(v)
        var = sum((x - m) ** 2 for x in v) / max(len(v) - 1, 1)
        sd = math.sqrt(var)
        demi = max(3 * sd, 0.02 * max(abs(m), 1.0), 0.02)
        out[k] = {"valeur": m, "bande": demi, "n": len(v)}
    return out


def main():
    t0 = time.time()
    net, ptnom = charge_agent()
    scenes = [("frontal", None), ("crochet", None), ("guet_140", None)]
    if net is not None:
        scenes.append(("agent", net))
    else:
        print("    (aucun .pt disponible : l'etalon APPRIS est remplace par 'guet_140' seul)", flush=True)

    print("=== RITUEL DES ETALONS ===", flush=True)
    print("    %d scenes x 3 graines d'evaluation | banc fige A=4 D=8" % len(scenes), flush=True)
    ref = {}
    for nom, n in scenes:
        runs = [joue(nom, s, n) for s in (7, 8, 9)]
        ref[nom] = moyenne_et_bande(runs)
        r = ref[nom]
        print("  %-9s prise %5.1f%%  prise-a-pertes %6.2f  expo tot %7.3f  expo/m %.4f  au-dela de 110 m : %4.0f%%"
              % (nom, 100 * r["prise"]["valeur"], r["prise_a_pertes"]["valeur"] if r["prise_a_pertes"] else float("nan"),
                 r["expo_totale"]["valeur"], r["expo_par_metre"]["valeur"],
                 100 * r["part_au_dela_110m"]["valeur"]), flush=True)

    # EXIGENCE DE CONCEPTION : au moins un etalon majoritairement au-dela de 110 m
    loin = [(nom, ref[nom]["part_au_dela_110m"]["valeur"]) for nom in ref]
    best = max(loin, key=lambda t: t[1])
    exigence = best[1] >= 0.5
    print("", flush=True)
    print("  EXIGENCE DE CONCEPTION (un etalon majoritairement au-dela de 110 m) :", flush=True)
    print("    le plus lointain est '%s' a %.0f %% de son temps -> %s"
          % (best[0], 100 * best[1], "SATISFAITE" if exigence else "NON SATISFAITE"), flush=True)
    if not exigence:
        print("    l'exposimetre n'a PAS de sentinelle la ou il etait aveugle. Dit tel quel.", flush=True)

    # REVUE 17/08 : `--verifier` SANS reference sautait la verification en silence, puis
    # la branche `a.poser or not os.path.exists(REF)` POSAIT le run courant comme nouvel
    # etalon, exit 0. Sur une machine neuve ou apres effacement, un monde derive devenait
    # la reference et la nuit entiere validait la derive contre elle-meme.
    if a.verifier and not os.path.exists(REF):
        print("", flush=True)
        print("  ⛔ --verifier SANS REFERENCE : il n'y a rien contre quoi vérifier.", flush=True)
        print("     Utilise --poser explicitement si tu veux fixer l'étalon.", flush=True)
        return 3
    if a.verifier and os.path.exists(REF):
        anc = json.load(open(REF))["etalons"]
        print("", flush=True)
        print("=== VERIFICATION CONTRE LA REFERENCE ===", flush=True)
        hors = []
        for nom in ref:
            if nom not in anc:
                continue
            for k in CLES:
                A_ = anc[nom].get(k)
                B_ = ref[nom].get(k)
                if not A_ or not B_:
                    continue
                if abs(B_["valeur"] - A_["valeur"]) > A_["bande"]:
                    hors.append((nom, k, A_["valeur"], B_["valeur"], A_["bande"]))
        for h in hors:
            print("  HORS BANDE : %-9s %-18s reference %.4f, mesure %.4f (bande +-%.4f)"
                  % (h[0], h[1], h[2], h[3], h[4]), flush=True)
        if hors:
            print("  -> LA BRANCHE S'ARRETE. Le monde a bouge ; on ne mesure rien dessus.", flush=True)
            json.dump({"quand": time.strftime("%Y-%m-%d %H:%M"), "etalons": ref,
                       "hors_bande": hors, "exigence_110m": exigence, "agent": ptnom},
                      open(LEV + "/etalons_verification.json", "w"), indent=1)
            return 2
        print("  -> tous les etalons sont dans leur bande. On peut mesurer.", flush=True)

    if a.poser or (not a.verifier and not os.path.exists(REF)):
        json.dump({"quand": time.strftime("%Y-%m-%d %H:%M"), "etalons": ref,
                   "exigence_110m": exigence, "agent": ptnom, "eval": a.eval},
                  open(REF, "w"), indent=1)
        print("", flush=True)
        print("-> reference posee : %s  (%.0f s)" % (REF, time.time() - t0), flush=True)
    print("ETALONS_DONE", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
