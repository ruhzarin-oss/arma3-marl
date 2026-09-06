#!/usr/bin/env python3
"""controle_assemblage — POURQUOI aucune forme n est atteinte. Juger l ACTE, pas l ETAT.

`assemblage.py` rend 0/15 : jamais atteinte. Avant d en faire un verdict, il faut savoir si
mon ordre a seulement ETE EXECUTE. Trois bras qui separent les causes :

  A · doMove, ennemis PRESENTS      -> deja mesure : 0/15
  B · doMove, MONDE VIDE            -> si ca assemble, le coupable est LE COMBAT (H1)
                                       si ca n assemble pas non plus, c est MON ORDRE (H2)
  C · setFormation NATIF + doMove du CHEF, ennemis presents
                                    -> le chemin du moteur, celui que j aurais du essayer
                                       d abord. Arma SAIT poser une formation.

Le bras B est le controle positif : il ne peut pas etre ecrase par le combat, donc s il echoue,
l instrument est en cause et le 0/15 ne vaut rien.
"""
import sys, math, time, json
import numpy as np
sys.path.insert(0, "/home/younes/arma3-marl"); sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from marge import scene
from assemblage import etat, cap_et_ancre, places, E, TOL, SP, RR
import formations as F

# Correspondance catalogue -> formation NATIVE d Arma. Declaree ici, avant de lire quoi que ce soit.
NATIF = {"colonne": "FILE", "losange": "DIAMOND", "coin": "WEDGE", "ligne": "LINE", "cercle": "VEE"}
FORMES = ("colonne", "losange", "coin", "ligne")

def vider(b):
    """MONDE VIDE : on retire les rouges. Le combat ne peut plus rien ecraser."""
    b.query('{ deleteVehicle _x } forEach (units HMT_GO); ' + E("HMTV %1", "1"), r"HMTV (\d+)", want=1, timeout=40)

def suivre(b, pl, duree=150):
    q = E("HMTA %1 %2", "{ _x } count [" + ",".join(
            '(((units HMT_GB select {alive _x}) select %d) distance2D [%.0f,%.0f,0]) < %.0f' % (i, x, y, TOL)
            for i, (x, y) in enumerate(pl)) + "]",
          "round (10 * ([" + ",".join(
            '(((units HMT_GB select {alive _x}) select %d) distance2D [%.0f,%.0f,0])' % (i, x, y)
            for i, (x, y) in enumerate(pl)) + "] call BIS_fnc_arithmeticMean))")
    t0 = time.time(); arrive = None; nmax = 0; dfin = -1
    while time.time() - t0 < duree:
        time.sleep(5)
        r = b.query(q, r"HMTA (\d+) (\d+)", want=1, timeout=40)
        if not r: continue
        n_ok, dm = int(r[0].group(1)), int(r[0].group(2)) / 10.0
        nmax = max(nmax, n_ok); dfin = dm
        if arrive is None and n_ok >= 6: arrive = time.time() - t0; break
    return arrive, nmax, dfin

def poser(b, pl):
    b.query("".join('((units HMT_GB select {alive _x}) select %d) doMove [%.0f,%.0f,0];' % (i, x, y)
                    for i, (x, y) in enumerate(pl)) + E("HMTF %1", "1"), r"HMTF (\d+)", want=1, timeout=40)

def ordre_recu(b, pl):
    """CONTROLE DE L ACTE : la destination attendue du moteur est-elle bien celle que j ai donnee ?
    `expectedDestination` dit ce que l unite compte faire. Si elle est loin de ma place, mon ordre
    n a PAS pris — et le 0/15 mesurait mon pont, pas le monde."""
    r = b.query(E("HMTE %1", "round ([" + ",".join(
        '(((units HMT_GB select {alive _x}) select %d) distance2D ((expectedDestination ((units HMT_GB select {alive _x}) select %d)) select 0))' % (i, i)
        for i in range(len(pl))) + "] call BIS_fnc_arithmeticMean)"), r"HMTE (\d+)", want=1, timeout=40)
    return int(r[0].group(1)) if r else None

if __name__ == "__main__":
    print("=" * 92); print(" CONTROLE POSITIF — l ordre a-t-il seulement ETE EXECUTE ?"); print("=" * 92)
    R = {"B_vide": {}, "C_natif": {}}
    b = None
    try:
        b = NativeBridge(port=5801, timeout=90)

        print("\n─── BRAS B — doMove en MONDE VIDE (controle positif) ───", flush=True)
        for nom in FORMES:
            R["B_vide"][nom] = []
            for sc in range(2):
                scene(b, sc); time.sleep(2); vider(b); time.sleep(3)
                m, ctr = etat(b)
                if m is None: continue
                cap, ancre = cap_et_ancre(np.zeros(8), ctr)     # pas d ennemi -> cap courant, ancre au nord
                pl = places(nom, 8, cap, ancre)
                poser(b, pl); time.sleep(4)
                ecart = ordre_recu(b, pl)
                a, nmax, dfin = suivre(b, pl)
                R["B_vide"][nom].append({"t": a, "nmax": nmax, "dfin": dfin, "ecart_ordre": ecart})
                print("  %-9s sc%d : %-20s  max %d/8  fin %4.0f m  | ecart ordre-moteur %s m"
                      % (nom, sc, ("atteinte %.0f s" % a) if a else "JAMAIS", nmax, dfin,
                         ecart if ecart is not None else "?"), flush=True)

        print("\n─── BRAS C — setFormation NATIF + doMove du CHEF, ennemis presents ───", flush=True)
        for nom in FORMES:
            R["C_natif"][nom] = []
            for sc in range(2):
                scene(b, sc); time.sleep(3)
                m, ctr = etat(b)
                if m is None: continue
                cap, ancre = cap_et_ancre(m, ctr)
                b.query('HMT_GB setFormation "%s"; (leader HMT_GB) doMove [%.0f,%.0f,0];'
                        % (NATIF[nom], ancre[0], ancre[1]) + E("HMTN %1", "1"),
                        r"HMTN (\d+)", want=1, timeout=40)
                # ici la « place » est celle que le MOTEUR choisit : on mesure la COMPACITE atteinte,
                # pas l ecart a mes slots — le moteur a ses propres places, et c est le sujet.
                t0 = time.time(); serre = []
                while time.time() - t0 < 150:
                    time.sleep(5)
                    r = b.query(E("HMTC %1 %2",
                                  "round (10 * ([" + ",".join(
                                    '((units HMT_GB select {alive _x}) select %d) distance2D (leader HMT_GB)' % i
                                    for i in range(1, 8)) + "] call BIS_fnc_arithmeticMean))",
                                  "count (units HMT_GB select {alive _x})"),
                                r"HMTC (\d+) (\d+)", want=1, timeout=40)
                    if r: serre.append((round(time.time() - t0), int(r[0].group(1)) / 10.0, int(r[0].group(2))))
                d0 = serre[0][1] if serre else -1; d1 = serre[-1][1] if serre else -1
                R["C_natif"][nom].append({"debut": d0, "fin": d1, "viv": serre[-1][2] if serre else 0})
                print("  %-9s sc%d : dispersion autour du chef  %5.1f m -> %5.1f m   (%d vivants)"
                      % (nom, sc, d0, d1, serre[-1][2] if serre else 0), flush=True)
    finally:
        if b:
            try: b.close()
            except Exception: pass

    print("\n" + "=" * 92)
    bt = [e for v in R["B_vide"].values() for e in v]
    ok_b = sum(1 for e in bt if e["t"])
    ec = [e["ecart_ordre"] for e in bt if e["ecart_ordre"] is not None]
    print("  BRAS B (monde vide) : %d/%d assemblees" % (ok_b, len(bt)))
    if ec: print("     ecart median entre MA place et la destination du moteur : %.0f m" % np.median(ec))
    if ok_b == 0:
        print("  ⛔ MEME SANS UN SEUL ENNEMI, la forme n est pas atteinte -> le coupable n est pas le")
        print("     combat, c est MON ORDRE. Le 0/15 mesurait mon pont. Le verdict est SUSPENDU.")
    else:
        print("  ✅ en monde vide ca assemble -> le coupable est bien LE COMBAT (H1).")
    ct = [e for v in R["C_natif"].values() for e in v]
    if ct:
        g = [e["debut"] - e["fin"] for e in ct if e["debut"] > 0 and e["fin"] > 0]
        print("  BRAS C (setFormation natif) : resserrement median %.1f m sur %d essais" % (np.median(g) if g else 0, len(ct)))
    json.dump(R, open('/mnt/data/controle_assemblage.json', 'w'), indent=1)
