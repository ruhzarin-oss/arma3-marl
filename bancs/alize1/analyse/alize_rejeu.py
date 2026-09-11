#!/usr/bin/env python3
"""alize_rejeu - HMT-39 : la cascade SIROCCO a parametres FIXES, rejouee hors d Arma sur les journaux
du banc ALIZE 1 (coup_recu + frole, homme par homme).

Critere ecrit d avance (Fable, 11/09) : l etage REFLEXE doit se declencher chez AU MOINS 90 % des
hommes qui recoivent un coup ; SOUS 50 %, le signal n existe pas dans Arma et ALIZE attend le canal bruit.

On mesure aussi ce que le critere ne dit pas :
  - l AVANCE : combien de secondes avant son premier coup l homme etait deja en REFLEXE (sur frolement) ;
  - le COUT : les hommes jamais touches qui passent quand meme en REFLEXE, et combien de temps
    (tout ce qui fige un homme coute) ;
  - la sensibilite au seuil : s1 = 0,05 (le plancher du controle positif) et 0,25 (defaut de la cascade).

Usage : .venv/bin/python alize_rejeu.py [runs/*_alize1_*]
"""
import csv, glob, json, os, re, statistics, sys

sys.path.insert(0, "/mnt/data/hmt/depot")
import torch
from sirocco import AlarmeLocale, IMPACT, FROLEMENT
from sirocco_cascade import Cascade, REFLEXE

ROLES_FS = {"CHEF", "ADJOINT", "DEMO_1", "DEMO_2", "MEDECIN", "TIREUR_1", "TIREUR_2", "AT", "FUSILIER_1", "FUSILIER_2"}
INTEN = {IMPACT: 1.0, FROLEMENT: 0.8}


def lire_episode(ep):
    rpt = open(f"{ep}/serveur.rpt", errors="ignore").read()
    fs = {}
    for m in re.finditer(r'CHACAL\|E\|spawn\|[0-9.]+\|(\d+)\|1\|[^|]*\|([A-Z_0-9]+)', rpt):
        if m.group(2) in ROLES_FS:
            fs[int(m.group(1))] = m.group(2)
    ev = []
    for m in re.finditer(r'CHACAL\|E\|coup_recu\|([0-9.]+)\|(\d+)\|(-?\d+)\|([0-9.]+)\|([0-9.]+)\|(-?\d+)\|\[([-0-9.]+),([-0-9.]+)', rpt):
        ev.append((float(m.group(1)), int(m.group(2)), IMPACT, float(m.group(7)), float(m.group(8)), float(m.group(5))))
    for m in re.finditer(r'CHACAL\|E\|frole\|([0-9.]+)\|(\d+)\|(-?\d+)\|(\d+)\|\[([-0-9.]+),([-0-9.]+)', rpt):
        ev.append((float(m.group(1)), int(m.group(2)), FROLEMENT, float(m.group(5)), float(m.group(6)), 0.0))
    ev.sort()
    ticks = {}
    with open(f"{ep}/extrait/etat.csv") as f:
        for r in csv.DictReader(f):
            i = int(float(r["id"]))
            if i in fs:
                ticks.setdefault(float(r["t"]), {})[i] = (float(r["x"]), float(r["y"]), float(r["vivant"]) > 0.5)
    return fs, ev, ticks


def rejouer(fs, ev, ticks, s1):
    ids = sorted(fs); A = len(ids); ix = {i: k for k, i in enumerate(ids)}
    ts = sorted(ticks)
    spp = statistics.median([b - a for a, b in zip(ts, ts[1:])]) if len(ts) > 1 else 2.0
    dev = torch.device("cpu")
    al = AlarmeLocale(1, A, dev, sec_par_pas=spp)
    ca = Cascade(1, A, dev, sec_par_pas=spp, s1=s1)
    px = torch.zeros(1, A); py = torch.zeros(1, A); viv = torch.ones(1, A, dtype=torch.bool)
    entree = {}; t_reflexe = {i: 0.0 for i in ids}
    debut = {}; histo = {i: [] for i in ids}   # histo[i] = [(t, en_reflexe, debut_plage)]
    k_ev = 0; t_prec = -1e9
    for t in ts:
        for i, (x, y, v) in ticks[t].items():
            px[0, ix[i]] = x; py[0, ix[i]] = y; viv[0, ix[i]] = v
        while k_ev < len(ev) and ev[k_ev][0] <= t:
            te, i, canal, sx, sy, _ = ev[k_ev]; k_ev += 1
            if i not in ix: continue
            act = torch.zeros(1, A, dtype=torch.bool); act[0, ix[i]] = True
            al.signaler(canal, px, py, torch.full((1, A), sx), torch.full((1, A), sy), INTEN[canal], actif=act)
        out = ca.pas(al.danger(), px, py, al.menace()[..., :2], vivant=viv)
        for i in ids:
            r = int(out["etat"][0, ix[i]]) == REFLEXE
            if r:
                entree.setdefault(i, t); t_reflexe[i] += spp; debut.setdefault(i, t)
            else:
                debut.pop(i, None)
            histo[i].append((t, r, debut.get(i)))
        al.pas(); t_prec = t
    return entree, t_reflexe, spp, histo


def main():
    eps = sorted(glob.glob("/mnt/data/hmt/runs/*_alize1_i*/g*_r*"))
    eps = [e for e in eps if os.path.exists(f"{e}/serveur.rpt") and os.path.exists(f"{e}/extrait/etat.csv")]
    rapport = {"episodes": len(eps)}
    for s1 in (0.05, 0.25):
        touches = reflexe_ok = avant = 0; avances = []; fausses = 0; fausses_s = []; hommes = 0
        tues_premier = 0
        for ep in eps:
            fs, ev, ticks = lire_episode(ep)
            entree, t_ref, spp, histo = rejouer(fs, ev, ticks, s1)
            premier_coup = {}
            for te, i, canal, sx, sy, tot in ev:
                if canal == IMPACT and i not in premier_coup:
                    premier_coup[i] = (te, tot)
            hommes += len(fs)
            for i in fs:
                if i in premier_coup:
                    touches += 1
                    tc, tot = premier_coup[i]
                    if tot >= 1: tues_premier += 1
                    # le reflexe compte s il est entre AVANT la mort ; un homme tue sur le coup
                    # ne l a que si un frolement l a mis en reflexe avant.
                    # STRICT : en reflexe AU MOMENT du coup (dernier pas <= tc), ou entre au pas
                    # qui suit le coup s il est encore vivant. Un reflexe retombe avant ne compte pas.
                    avant_coup = [h for h in histo[i] if h[0] <= tc]
                    apres_coup = [h for h in histo[i] if tc < h[0] <= tc + spp]
                    if avant_coup and avant_coup[-1][1]:
                        reflexe_ok += 1; avant += 1; avances.append(tc - avant_coup[-1][2])
                    elif apres_coup and apres_coup[0][1]:
                        reflexe_ok += 1
                elif i in entree:
                    fausses += 1; fausses_s.append(t_ref[i])
        pct = 100.0 * reflexe_ok / touches if touches else float("nan")
        verdict = "PASSE" if pct >= 90 else ("ECHEC : le signal n existe pas" if pct < 50 else "ENTRE LES DEUX")
        rapport[f"s1={s1}"] = {
            "hommes": hommes, "touches": touches, "tues_du_premier_coup": tues_premier,
            "reflexe_avant_ou_au_coup": reflexe_ok, "pourcent": round(pct, 1), "verdict_HMT39": verdict,
            "dont_deja_en_reflexe_au_coup": avant,
            "avance_mediane_s": round(statistics.median(avances), 1) if avances else None,
            "avance_min_max_s": [round(min(avances), 1), round(max(avances), 1)] if avances else None,
            "jamais_touches_mis_en_reflexe": fausses,
            "jamais_touches_temps_median_en_reflexe_s": round(statistics.median(fausses_s), 1) if fausses_s else None,
        }
    print(json.dumps(rapport, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
