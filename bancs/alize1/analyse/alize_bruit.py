#!/usr/bin/env python3
"""alize_bruit - le CANAL BRUIT d ALIZE, construit HORS d Arma (plan de Fable, 11/09/2026).

Aucun episode rejoue. Chaque coup tire est deja journalise (`CHACAL|E|tir|t|tireur|cible|phase`) et la
position de chaque homme, ennemis compris, est dans extrait/etat.csv toutes les ~2 s. On joint les deux :
chaque coup ENNEMI devient un evenement BRUIT pour chacun de nos hommes a portee d ecoute.

Loi : celle de l ouie MESUREE sur Arma le 03/09 - volume = min(2177/d^2 ; 1,35) / 1,35, plein jusqu a
~40 m. Portee de coupure balayee (100 / 200 / 300 m) : le mal se joue vers 170 m. Tirs amis EXCLUS (sinon
le premier coup de notre pointe fige le detachement) - c est un petit oracle, l oreille d Arma n identifie
pas le camp : on le dit. La cascade lit danger = max(IMPACT, FROLEMENT, poids x BRUIT) ; le BRUIT d un
homme s additionne coup apres coup et plafonne a 1, donc une rafale s accumule, un coup isole au loin non.

Controles OBLIGATOIRES avant toute lecture :
  - la jointure : la position reconstruite du tireur doit tomber a moins de 10 m de la position EXACTE
    portee par les lignes `frole`, sur au moins 90 % d entre elles ; et au moins 95 % des coups ennemis joints ;
  - temoin bas  : portee 0 doit rendre EXACTEMENT le rejeu sans bruit (73 %, 1,4 s sur 16 episodes) ;
  - temoin haut : portee infinie, poids 1, doit mettre presque tout le monde en reflexe (le levier mord).

Critere (Fable) : avance mediane >= 5 s ET >= 90 % des touches en reflexe au coup ; fausses alarmes au plus
le DOUBLE d aujourd hui (temps total en reflexe des jamais-touches) et aucun episode avec tous nos vivants
en reflexe ensemble plus de 10 s.
"""
import csv, glob, json, math, os, re, statistics, sys

sys.path.insert(0, "/mnt/data/hmt/depot")
import torch
from sirocco import AlarmeLocale, IMPACT, FROLEMENT, BRUIT
from sirocco_cascade import Cascade, REFLEXE

ROLES_FS = {"CHEF", "ADJOINT", "DEMO_1", "DEMO_2", "MEDECIN", "TIREUR_1", "TIREUR_2", "AT", "FUSILIER_1", "FUSILIER_2"}
INTEN = {IMPACT: 1.0, FROLEMENT: 0.8}


def volume(d):
    d = max(d, 1.0)
    return min(2177.0 / (d * d), 1.35) / 1.35


def lire(ep):
    rpt = open(f"{ep}/serveur.rpt", errors="ignore").read()
    fs, camp = {}, {}
    for m in re.finditer(r'CHACAL\|E\|spawn\|[0-9.]+\|(\d+)\|(\d+)\|[^|"]*\|([A-Z_0-9]*)', rpt):
        i, s, r = int(m.group(1)), int(m.group(2)), m.group(3)
        camp[i] = s
        if s == 1 and r in ROLES_FS:
            fs[i] = r
    ev = []
    for m in re.finditer(r'CHACAL\|E\|coup_recu\|([0-9.]+)\|(\d+)\|(-?\d+)\|([0-9.]+)\|([0-9.]+)\|(-?\d+)\|\[([-0-9.]+),([-0-9.]+)', rpt):
        ev.append((float(m.group(1)), "C", int(m.group(2)), float(m.group(7)), float(m.group(8)), float(m.group(5))))
    froles = []
    for m in re.finditer(r'CHACAL\|E\|frole\|([0-9.]+)\|(\d+)\|(-?\d+)\|(\d+)\|\[([-0-9.]+),([-0-9.]+)', rpt):
        t, i, tireur, x, y = float(m.group(1)), int(m.group(2)), int(m.group(3)), float(m.group(5)), float(m.group(6))
        ev.append((t, "F", i, x, y, 0.0)); froles.append((t, tireur, x, y))
    tirs = []
    for m in re.finditer(r'CHACAL\|E\|tir\|([0-9.]+)\|(-?\d+)\|', rpt):
        t, tireur = float(m.group(1)), int(m.group(2))
        if camp.get(tireur, 1) == 0:          # ennemis seulement
            tirs.append((t, tireur))
    pos = {}                                  # pos[id] = [(t, x, y)] trie
    ticks = {}
    with open(f"{ep}/extrait/etat.csv") as f:
        for r in csv.DictReader(f):
            i, t = int(float(r["id"])), float(r["t"])
            pos.setdefault(i, []).append((t, float(r["x"]), float(r["y"])))
            if i in fs:
                ticks.setdefault(t, {})[i] = (float(r["x"]), float(r["y"]), float(r["vivant"]) > 0.5)
    for i in pos: pos[i].sort()
    ev.sort(key=lambda e: e[0]); tirs.sort()   # ! les coups puis les froles etaient ajoutes a la suite : le temoin bas l a vu
    return fs, ev, froles, tirs, pos, ticks


def position_a(pos, i, t):
    """Derniere position connue de i a l instant t (pas de 2 s). None si inconnue."""
    l = pos.get(i)
    if not l: return None
    lo, hi = 0, len(l) - 1
    if t < l[0][0] - 3: return None
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if l[mid][0] <= t: lo = mid
        else: hi = mid - 1
    return l[lo][1], l[lo][2]


def rejouer(fs, ev, tirs_pos, ticks, s1, portee, poids):
    ids = sorted(fs); A = len(ids); ix = {i: k for k, i in enumerate(ids)}
    ts = sorted(ticks)
    spp = statistics.median([b - a for a, b in zip(ts, ts[1:])]) if len(ts) > 1 else 2.0
    dev = torch.device("cpu")
    al = AlarmeLocale(1, A, dev, sec_par_pas=spp)
    ca = Cascade(1, A, dev, sec_par_pas=spp, s1=s1)
    px = torch.zeros(1, A); py = torch.zeros(1, A); viv = torch.ones(1, A, dtype=torch.bool)
    debut, histo = {}, {i: [] for i in ids}
    t_ref = {i: 0.0 for i in ids}; tous_fige, tous_fige_max = 0.0, 0.0
    k_ev = k_tir = 0
    for t in ts:
        for i, (x, y, v) in ticks[t].items():
            px[0, ix[i]] = x; py[0, ix[i]] = y; viv[0, ix[i]] = v
        while k_ev < len(ev) and ev[k_ev][0] <= t:
            te, typ, i, sx, sy, _ = ev[k_ev]; k_ev += 1
            if i not in ix: continue
            act = torch.zeros(1, A, dtype=torch.bool); act[0, ix[i]] = True
            canal = IMPACT if typ == "C" else FROLEMENT
            al.signaler(canal, px, py, torch.full((1, A), sx), torch.full((1, A), sy), INTEN[canal], actif=act)
        while k_tir < len(tirs_pos) and tirs_pos[k_tir][0] <= t:
            te, sx, sy = tirs_pos[k_tir]; k_tir += 1
            if portee <= 0: continue
            d = torch.sqrt((px - sx) ** 2 + (py - sy) ** 2)
            v = d.clone().apply_(volume) if portee != math.inf else d.clone().fill_(1.0)
            v = torch.where((d <= portee) & viv, v, torch.zeros_like(v))
            if float(v.max()) > 0:
                al.signaler(BRUIT, px, py, torch.full((1, A), sx), torch.full((1, A), sy), v)
        danger = torch.maximum(al.danger(), poids * al.inten[:, :, BRUIT])
        out = ca.pas(danger, px, py, al.menace()[..., :2], vivant=viv)
        en_ref = 0
        for i in ids:
            r = int(out["etat"][0, ix[i]]) == REFLEXE
            if r:
                t_ref[i] += spp; debut.setdefault(i, t); en_ref += 1
            else:
                debut.pop(i, None)
            histo[i].append((t, r, debut.get(i)))
        nviv = int(viv.sum())
        if nviv > 0 and en_ref == nviv:
            tous_fige += spp; tous_fige_max = max(tous_fige_max, tous_fige)
        else:
            tous_fige = 0.0
        al.pas()
    return histo, t_ref, spp, tous_fige_max


def main():
    eps = sorted(glob.glob("/mnt/data/hmt/runs/*_alize1_i*/g*_r*"))
    eps = [e for e in eps if os.path.exists(f"{e}/serveur.rpt") and os.path.exists(f"{e}/extrait/etat.csv")]
    donnees = []
    ecarts, n_tirs, n_joints = [], 0, 0
    diag = []
    for ep in eps:
        fs, ev, froles, tirs, pos, ticks = lire(ep)
        tp = []
        for t, tireur in tirs:
            n_tirs += 1
            p = position_a(pos, tireur, t)
            if p: n_joints += 1; tp.append((t, p[0], p[1]))
        for t, tireur, x, y in froles:
            p = position_a(pos, tireur, t)
            if p: ecarts.append(math.hypot(p[0] - x, p[1] - y))
        donnees.append((fs, ev, tp, ticks))
        # DIAGNOSTIC : combien de coups ennemis, n importe ou, dans les 10 s AVANT le premier coup recu ?
        # Zero = le coup qui touche est le premier de la rafale : aucun son ne peut prevenir.
        premier = {}
        for te, typ, i, sx, sy, tot in ev:
            if typ == "C" and i not in premier: premier[i] = te
        for i, tc in premier.items():
            # sans la balle qui touche : coups ennemis anterieurs a tc - 1 s
            n10 = sum(1 for t, x, y in tp if tc - 10 <= t < tc - 1.0)
            n30 = sum(1 for t, x, y in tp if tc - 30 <= t < tc - 1.0)
            diag.append((n10, n30))
    jointure = {
        "episodes": len(eps), "coups_ennemis": n_tirs,
        "coups_joints_pourcent": round(100.0 * n_joints / n_tirs, 1) if n_tirs else None,
        "froles_verifies": len(ecarts),
        "ecart_position_moins_10m_pourcent": round(100.0 * sum(1 for e in ecarts if e < 10) / len(ecarts), 1) if ecarts else None,
        "ecart_median_m": round(statistics.median(ecarts), 1) if ecarts else None,
    }
    jointure["JOINTURE_VALIDE"] = bool(ecarts) and jointure["ecart_position_moins_10m_pourcent"] >= 90 and jointure["coups_joints_pourcent"] >= 95
    print(json.dumps({"jointure": jointure}, ensure_ascii=False))
    sans10 = sum(1 for a, b in diag if a == 0); sans30 = sum(1 for a, b in diag if b == 0)
    print(f"DIAGNOSTIC : {len(diag)} hommes touches ; aucun coup ennemi dans les 10 s avant : {sans10} ; dans les 30 s avant : {sans30} ; mediane des coups ennemis dans les 10 s avant : {statistics.median([a for a, b in diag]) if diag else None}")

    lignes = []
    grille = [(0, 1.0, 0.05), (0, 1.0, 0.25), (math.inf, 1.0, 0.05)]
    grille += [(p, w, s) for p in (100, 200, 300) for w in (0.5, 1.0) for s in (0.05, 0.25)]
    for portee, poids, s1 in grille:
        touches = ok = deja = 0; avances = []; faux_s = 0.0; faux_n = 0; hommes = 0; ep_fige = 0
        for fs, ev, tp, ticks in donnees:
            histo, t_ref, spp, fige_max = rejouer(fs, ev, tp, ticks, s1, portee, poids)
            if fige_max > 10: ep_fige += 1
            premier = {}
            for te, typ, i, sx, sy, tot in ev:
                if typ == "C" and i not in premier: premier[i] = te
            hommes += len(fs)
            for i in fs:
                if i in premier:
                    touches += 1; tc = premier[i]
                    av = [h for h in histo[i] if h[0] < tc - 1.0]; ap = [h for h in histo[i] if tc < h[0] <= tc + spp]
                    if av and av[-1][1]:
                        ok += 1; deja += 1; avances.append(tc - av[-1][2])
                    elif ap and ap[0][1]:
                        ok += 1
                elif t_ref[i] > 0:
                    faux_n += 1; faux_s += t_ref[i]
        pct = round(100.0 * ok / touches, 1) if touches else None
        av_med = round(statistics.median(avances), 1) if avances else None
        lignes.append({"portee": "inf" if portee == math.inf else portee, "poids": poids, "s1": s1,
                       "touches": touches, "au_coup_pourcent": pct, "deja_en_reflexe": deja, "avance_mediane_s": av_med,
                       "faux_hommes": faux_n, "faux_total_s": round(faux_s), "episodes_tous_figes_10s": ep_fige})
    base = next(l for l in lignes if l["portee"] == 0 and l["s1"] == 0.05)
    for l in lignes:
        l["PASSE"] = bool(l["au_coup_pourcent"] and l["au_coup_pourcent"] >= 90 and l["avance_mediane_s"]
                          and l["avance_mediane_s"] >= 5 and l["faux_total_s"] <= 2 * base["faux_total_s"]
                          and l["episodes_tous_figes_10s"] == 0)
    print("portee poids  s1   | touches au_coup% deja avance_med | faux_hommes faux_total_s ep_figes | PASSE")
    for l in lignes:
        print(f"{str(l['portee']):>6} {l['poids']:>4} {l['s1']:>5} | {l['touches']:>7} {str(l['au_coup_pourcent']):>8} {l['deja_en_reflexe']:>4} {str(l['avance_mediane_s']):>10} | {l['faux_hommes']:>11} {l['faux_total_s']:>12} {l['episodes_tous_figes_10s']:>8} | {l['PASSE']}")
    json.dump({"jointure": jointure, "grille": lignes}, open("/mnt/data/hmt/archive/alize_bruit_resultat.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
