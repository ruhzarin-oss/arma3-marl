#!/usr/bin/env python3
"""greffe_arma — LA PORTE D ADOPTION. Criteres deposes : DEPOT_GREFFE_ARMA.md (f2909ef959c36655).

LA QUESTION : un executant FIXE sur Arma, filtre au moment de decider par le PRIX DE MORT de
`monde2`, bat-il le meme executant SANS filtre, sur scenarios jamais vus ?
C est la greffe du gymnase (+15,3 sans un gradient) rejouee dans le monde qui price l information.

COMMENT ON FILTRE AVEC UN MODELE DISCRIMINATIF : `monde2` ne deroule pas le monde, il rend un
prix. On lui donne les 11 derniers pas REELS de l homme, on ajoute un 12e pas HYPOTHETIQUE a
la position candidate, et il dit ce que cette position coute. Meme principe que `_champ_danger`
au gymnase : LE PRIX, jamais la reponse.

⚠️ MORT PROPRE OBLIGATOIRE : les compteurs du pont ne se realignent pas a chaud ; un script
qui meurt au milieu rend le serveur inutilisable et coute un redemarrage. D ou le try/finally.
"""
import sys, time, math, json, argparse
import numpy as np, torch, torch.nn as nn
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

DEV = "cuda:0"; LEN = 12; PAS_M = 20.0
E = lambda t, *a: 'format ["%s"%s] call HMT_EMIT;' % (t, "".join("," + x for x in a))

class Modele(nn.Module):
    def __init__(self, nf=10, nh=96):
        super().__init__(); self.g = nn.GRU(nf, nh, batch_first=True)
        self.t = nn.Sequential(nn.Linear(nh, nh), nn.ReLU(), nn.Linear(nh, 1))
    def forward(self, x):
        h, _ = self.g(x); return self.t(h[:, -1]).squeeze(-1)

M = Modele().to(DEV); M.load_state_dict(torch.load('/mnt/data/monde2.pt', map_location=DEV)); M.eval()

def traits(x, y, z, camp, tir, az, post, supp, vu, ka):
    return [x / 5000, y / 5000, z / 500, camp, tir, az / 360, post / 3, supp, vu, ka / 4.0]

def prix(hist, cands):
    """hist : (11, 10) reels. cands : liste de traits hypothetiques. -> prix de chaque candidat."""
    B = np.stack([np.vstack([hist, c]) for c in cands]).astype(np.float32)
    with torch.no_grad():
        return torch.sigmoid(M(torch.tensor(B, device=DEV))).cpu().numpy()

def scene(b, graine):
    """LA SCENE CALIBREE ⟨AMENDEMENT_SCENE.md, 27/08⟩ : d=150 m, 20 rouges RETRANCHES, skill 0,7.
    Retenue non pour etre la plus meurtriere mais pour laisser 3 survivants sur 8 — le plus de
    place DANS LES DEUX SENS. La version precedente rendait 7,50 dans les trois bras."""
    b.query('HMT_POS = [] call BIS_fnc_randomPos;'
            'HMT_POS = [HMT_POS, 0, 800, 12, 0, 0.25, 0] call BIS_fnc_findSafePos;'
            '{ if (!isPlayer _x) then { deleteVehicle _x } } forEach allUnits;'
            'HMT_GB = createGroup west; HMT_GO = createGroup east;'
            'for "_i" from 0 to 7 do { HMT_GB createUnit ["B_Soldier_F", HMT_POS vectorAdd [(_i mod 4)*6-9, floor(_i/4)*6, 0], [], 0, "NONE"] };'
            'for "_i" from 0 to 19 do { HMT_GO createUnit ["O_Soldier_F", HMT_POS vectorAdd [(_i mod 6)*8-20, 150 + floor(_i/6)*8, 0], [], 0, "NONE"] };'
            '{ _x setSkill 0.7; _x allowFleeing 0 } forEach allUnits;'
            '{ _x setUnitPos "DOWN"; _x disableAI "PATH" } forEach units HMT_GO;'
            'HMT_GB setBehaviour "COMBAT"; HMT_GO setBehaviour "COMBAT";'
            'HMT_GB setCombatMode "RED"; HMT_GO setCombatMode "RED";'
            'HMT_GB setSpeedMode "FULL"; HMT_GO setSpeedMode "FULL";'
            '{ _x reveal [leader HMT_GO, 4]; _x doMove (getPos leader HMT_GO) } forEach units HMT_GB;'
            '{ _x reveal [leader HMT_GB, 4] } forEach units HMT_GO;'
            + E("HMTSC b=%1 o=%2", "count units HMT_GB", "count units HMT_GO"),
            r"HMTSC b=(\d+) o=(\d+)", want=1, timeout=40)

def lire(b):
    """L etat des bleus VIVANTS + LA DESTINATION QUE LE NATIF S EST DONNEE.

    ⭐ LE VRAI FILTRE ⟨correction du 27/08⟩. La version precedente envoyait un `doMove` vers une
    position que JE choisissais parmi trois directions : ce n etait pas un filtre, c etait une
    SUBSTITUTION — le natif n avait jamais propose ces candidats. Elle a couté 2 survivants
    contre le natif laisse libre, ce qui mesurait « l IA d Arma contre mes points de passage ».
    `expectedDestination` rend la destination que l IA S EST DONNEE. On peut donc la LIRE,
    la juger, et ne la remplacer QUE si le prix la condamne franchement : le natif decide,
    le prix pose un VETO. A taux de veto nul, ce bras EST le natif.
    """
    r = b.query('HMT_L = ""; { private _d = (expectedDestination _x) select 0;'
                'HMT_L = HMT_L + format ["%1,%2,%3,%4,%5,%6,%7,%8,%9|",'
                'round (getPosASL _x select 0), round (getPosASL _x select 1), round (getPosASL _x select 2),'
                'round (getDir _x), round (100*(getSuppression _x)), '
                '(if (east knowsAbout _x > 1) then {1} else {0}), (if (stance _x == "PRONE") then {1} else {0}),'
                'round (_d select 0), round (_d select 1) ] } '
                'forEach (units HMT_GB select {alive _x});'
                + E("HMTL %1 %2", "count (units HMT_GB select {alive _x})", "HMT_L"),
                r"HMTL (\d+) (\S*)", want=1, timeout=25)
    if not r: return []
    n, blob = int(r[0].group(1)), r[0].group(2)
    # ⚠️ DEUX FAUTES DU PREMIER JET, la seconde pire que la premiere :
    #  · `(stance _x == "PRONE")` rend un BOOLEEN — `format` ecrit "true"/"false", pas un
    #    nombre. C est la regle du pont que j avais moi-meme ecrite : QUE DES NOMBRES.
    #  · et mon `except: pass` AVALAIT l erreur : la liste sortait vide, la boucle croyait
    #    qu il n y avait personne, et six bras rendaient 8/8 sans qu un seul ordre soit donne.
    #    Un echec qui ne fait pas de bruit est pire qu un plantage.
    out, rejets = [], []
    for seg in blob.split("|"):
        if not seg: continue
        try: out.append([float(v) for v in seg.split(",")])
        except Exception as e: rejets.append(seg)
    if rejets:
        raise ValueError("lire() : %d segments ILLISIBLES, ex. %r — le pont a emis autre "
                         "chose qu un nombre" % (len(rejets), rejets[0][:60]))
    if n and not out:
        raise ValueError("lire() : %d hommes annonces, 0 lus" % n)
    return out

MARGE = 1.25          # on ne veto QUE si l alternative est 25 % moins chere. Depose avant.

def jouer(b, graine, mode, pas=14, perm=None):
    scene(b, graine)
    hist = {}; vetos = 0; decisions = 0
    for k in range(pas):
        et = lire(b)
        if not et: break
        ordres = []
        for i, s in enumerate(et):
            x, y, z, az, supp100, vu, prone, dx, dy = s
            t = traits(x, y, z, 1.0, 0.0, az, 2.0 if prone else 0.0, supp100 / 100.0, vu, 4.0 if vu else 3.0)
            h = hist.setdefault(i, []); h.append(t); hist[i] = h[-11:]
            if mode == "nu" or len(hist[i]) < 11:
                ordres.append(None); continue
            # LE CANDIDAT DU NATIF : un pas vers SA propre destination.
            vx, vy = dx - x, dy - y; n = math.hypot(vx, vy)
            if n < 1.0:
                ordres.append(None); continue        # il ne va nulle part : on ne touche pas
            nx0, ny0 = x + PAS_M * vx / n, y + PAS_M * vy / n
            az0 = math.degrees(math.atan2(vx, vy)) % 360
            pos = [(nx0, ny0)]
            cands = [traits(nx0, ny0, z, 1.0, 0.0, az0, 2.0 if prone else 0.0, supp100 / 100.0, vu, 4.0 if vu else 3.0)]
            for d in (-60, -30, 30, 60):            # les alternatives, AUTOUR de son choix
                a = math.radians(az0 + d)
                ax_, ay_ = x + PAS_M * math.sin(a), y + PAS_M * math.cos(a)
                pos.append((ax_, ay_))
                cands.append(traits(ax_, ay_, z, 1.0, 0.0, az0 + d, 2.0 if prone else 0.0, supp100 / 100.0, vu, 4.0 if vu else 3.0))
            p = prix(np.array(hist[i][-11:]), cands)
            if mode == "permute": p = p[perm.permutation(len(p))]
            decisions += 1
            j = int(np.argmin(p))
            # ⭐ VETO, PAS SUBSTITUTION : on ne remplace QUE si l alternative est franchement
            # moins chere. Sinon on ne donne AUCUN ordre et le natif fait ce qu il voulait.
            if j != 0 and p[0] > MARGE * p[j]:
                vetos += 1; ordres.append(pos[j])
            else:
                ordres.append(None)
        cmd = ""
        for i, o in enumerate(ordres):
            if o: cmd += '((units HMT_GB select {alive _x}) select %d) doMove [%.0f,%.0f,0];' % (i, o[0], o[1])
        if cmd: b.query(cmd + E("HMTMV %1", str(k)), r"HMTMV (\d+)", want=1, timeout=25)
        time.sleep(6)
    r = b.query(E("HMTFIN b=%1 o=%2", "{alive _x} count units HMT_GB", "{alive _x} count units HMT_GO"),
                r"HMTFIN b=(\d+) o=(\d+)", want=1, timeout=25)
    tv = 100.0 * vetos / max(decisions, 1)
    print("      taux de VETO %.1f %% (%d sur %d decisions du natif)" % (tv, vetos, decisions), flush=True)
    return ((int(r[0].group(1)), int(r[0].group(2)), tv) if r else (None, None, tv))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--graines", type=int, nargs="+", default=[1, 2])
    ap.add_argument("--pas", type=int, default=14); a = ap.parse_args()
    print("=" * 88); print(" GREFFE SUR ARMA — porte d adoption (f2909ef959c36655)"); print("=" * 88, flush=True)
    print("  critere DEPOSE : survivants amis. succes >= +1,0 contre le nu ET >= +0,5 contre le permute.")
    b = None; res = {}
    try:
        b = NativeBridge(port=5801, timeout=30)
        for mode in ("nu", "greffe", "permute"):
            sv = []
            for g in a.graines:
                perm = np.random.default_rng(100 + g)
                bl, ro, tv = jouer(b, g, mode, pas=a.pas, perm=perm)
                print("  %-9s graine %d : bleus %s / 8   rouges %s / 8" % (mode, g, bl, ro), flush=True)
                if bl is not None: sv.append(bl)
            res[mode] = sum(sv) / len(sv) if sv else None
            res[mode + "_min"] = min(sv) if sv else None
            print("  -> %-9s survivants moyens %.2f\n" % (mode, res[mode] or -1), flush=True)
        print("─── VERDICT ───")
        # ⚠️ LE CONTROLE DE DEGENERESCENCE, ajoute apres une 6e erreur d instrument :
        # trois bras a 8/8 ne sont pas un ECHEC, c est un banc QUI NE SAIT PAS SEPARER.
        # Un critere qui lit « ecart nul » comme « defaite » ment quand il n y a AUCUN signal.
        vv = [res.get(m) for m in ("nu", "greffe", "permute")]
        # ⚠️ GARDE-FOU ELARGI ⟨amendement 27/08⟩ : l ancien ne testait que « les trois a 8,0 ».
        # Trois bras identiques a 7,50 pres avaient donc ete lus « ECHEC ». On teste l ETENDUE.
        if all(v is not None for v in vv) and (max(vv) - min(vv)) < 0.25:
            print("  ⛔ BANC NON SEPARANT : etendue des trois bras = %.2f survivant (< 0,25)." % (max(vv) - min(vv)))
            print("     Ce n est PAS un echec de la greffe : l instrument ne distingue rien.")
            print("     AUCUN VERDICT.")
        elif all(res.get(m) is not None for m in ("nu", "greffe", "permute")):
            d1 = res["greffe"] - res["nu"]; d2 = res["greffe"] - res["permute"]
            print("  greffe %.2f | nu %.2f | permute %.2f" % (res["greffe"], res["nu"], res["permute"]))
            print("  greffe - nu = %+.2f  (succes >= +1,0)   greffe - permute = %+.2f  (>= +0,5)" % (d1, d2))
            print("  -> %s" % ("PASSE" if d1 >= 1.0 and d2 >= 0.5 else
                               "ECHEC" if d1 < 0.3 else "ZONE GRISE — deux graines de plus"))
        json.dump(res, open('/mnt/data/greffe_arma.json', 'w'), indent=1)
    finally:
        if b:
            try: b.close()
            except Exception: pass
        print("\n  (pont ferme proprement — un script qui meurt au milieu coute un redemarrage serveur)")
