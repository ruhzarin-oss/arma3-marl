#!/usr/bin/env python3
"""officer_state.py — LE DISTILLEUR (les yeux de l'officier Qwen).

Lit l'état du théâtre via le pont en UN appel batch -> SITREP structuré (25 FOB : garnison, contacts,
menacé/tenu + cibles + jour/nuit). Le SITREP alimente : `embed_theatre` (RAG) ET `to_text` (prompt Qwen).
Fichier autonome (zéro collision)."""
import re

# Les 25 ancres FOB = le `_net` de fob_network.sqf (6 MAIN + 19 OUTPOST). Le comptage par rayon (250 m)
# tolère le décalage HMT_LAND des postes côtiers (les hommes restent dans le rayon).
FOBS = [
    ("M1", 4279, 3856, "MAIN"), ("M2", 2050, 5700, "MAIN"), ("M3", 3253, 2984, "MAIN"),
    ("M4", 6544, 4863, "MAIN"), ("M5", 4886, 5948, "MAIN"), ("M6", 2915, 6165, "MAIN"),
    ("O1", 1942, 3557, "OUTPOST"), ("O2", 4319, 4398, "OUTPOST"), ("O3", 4604, 5284, "OUTPOST"),
    ("O4", 3338, 5744, "OUTPOST"), ("O5", 3027, 2184, "OUTPOST"), ("O6", 4206, 2715, "OUTPOST"),
    ("O7", 1935, 2723, "OUTPOST"), ("O8", 6402, 5427, "OUTPOST"), ("O9", 2979, 1860, "OUTPOST"),
    ("O10", 2719, 1712, "OUTPOST"), ("O11", 2024, 1790, "OUTPOST"), ("O12", 6157, 4349, "OUTPOST"),
    ("O13", 5440, 3687, "OUTPOST"), ("O14", 1784, 4134, "OUTPOST"), ("O15", 1790, 3512, "OUTPOST"),
    ("O16", 2648, 5990, "OUTPOST"), ("O17", 4241, 2498, "OUTPOST"), ("O18", 5691, 6124, "OUTPOST"),
    ("O19", 1845, 2656, "OUTPOST"),
]

# SQF batch : compte est-vivants + ouest-CONNUS (fog : knowsAbout>1) par FOB, en UN appel.
SIT_SQF = (
    'private _east = allUnits select {side _x == east && alive _x};\n'
    'private _wk = allUnits select {side _x != east && side _x != civilian && alive _x && (east knowsAbout _x > 1)};\n'
    'private _s = "";\n'
    '{ private _c = [_x#0, _x#1, 0];\n'
    '  private _g = {private _u=_x; (_u distance _c) < 250} count _east;\n'
    '  private _k = {private _u=_x; (_u distance _c) < 350} count _wk;\n'
    '  _s = _s + format ["%1,%2;", _g, _k];\n'
    '} forEach HMT_FOB_ANCHORS;\n'
    'private _ti = {!isNull _x && alive _x} count HMT_TARGET;\n'
    '(format ["HARMATTAN_SIT %1#%2#%3#%4#%5", _s, _ti, count HMT_TARGET, dayTime, count _east]) call HMT_EMIT;\n'
)


class OfficerState:
    """Lit le théâtre -> SITREP structuré. `read(tick)` (live, via le pont) ; `parse()` (testable à vide)."""
    def __init__(self, bridge=None):
        self.b = bridge
        self._anchors_set = False

    def _ensure_anchors(self):
        if self._anchors_set: return
        coords = "[" + ",".join("[%d,%d]" % (f[1], f[2]) for f in FOBS) + "]"
        self.b.send("HMT_FOB_ANCHORS = %s;" % coords)
        self._anchors_set = True

    def read(self, tick):
        """Live : interroge Arma -> SITREP (dict) ou None."""
        self._ensure_anchors()
        r = self.b.query(SIT_SQF, r'HARMATTAN_SIT (.+)', want=1, timeout=12)
        return self.parse(r[-1].group(1).rstrip('"').strip(), tick) if r else None  # .out entoure la chaîne de " -> strip

    def parse(self, payload, tick):
        """`gar,con;...#intact#total#daytime#eastcount` -> SITREP structuré."""
        p = payload.split("#")
        toks = [t for t in p[0].strip().rstrip(";").split(";") if t]
        fobs = []
        for i, tok in enumerate(toks[:len(FOBS)]):
            g, c = tok.split(","); g = int(g); c = int(c)
            nm, x, y, tier = FOBS[i]
            fobs.append({"name": nm, "pos": [x, y], "tier": tier,
                         "held": 1 if g > 0 else 0, "garrison": g, "contacts": c,
                         "threatened": 1 if c > 0 else 0})
        ti = int(p[1]) if len(p) > 1 else len(fobs)
        tt = int(p[2]) if len(p) > 2 else 0
        try: daytime = float(p[3])
        except Exception: daytime = 12.0
        force = int(p[4]) if len(p) > 4 else sum(f["garrison"] for f in fobs)
        return {"tick": tick, "fobs": fobs,
                "targets_intact": ti, "targets_total": tt,
                "daytime": daytime, "is_night": daytime < 5.0 or daytime > 20.0,
                "total_force": force, "total_threat": sum(f["contacts"] for f in fobs)}

    @staticmethod
    def to_text(sit):
        """SITREP structuré -> texte COMPACT pour Qwen (les FOB menacés en détail, le reste résumé)."""
        thr = [f for f in sit["fobs"] if f["contacts"] > 0]
        lost = [f for f in sit["fobs"] if f["held"] == 0]
        h = int(sit["daytime"]); m = int((sit["daytime"] - h) * 60)
        L = ["SITREP tick %d, %02dh%02d %s." % (sit["tick"], h, m, "NUIT" if sit["is_night"] else "JOUR"),
             "Force: %d hommes / %d FOB. Cibles vitales: %d/%d intactes." %
             (sit["total_force"], len(sit["fobs"]), sit["targets_intact"], sit["targets_total"])]
        if thr:
            L.append("MENACÉS:")
            for f in sorted(thr, key=lambda f: -f["contacts"]):
                L.append("  %s (%d,%d) [%s]: garnison %d, %d contacts" %
                         (f["name"], f["pos"][0], f["pos"][1], f["tier"], f["garrison"], f["contacts"]))
        if lost:
            L.append("PERDUS: " + ", ".join(f["name"] for f in lost))
        L.append("Calmes: %d FOB." % (len(sit["fobs"]) - len(thr)))
        return "\n".join(L)


# ===================== SELF-TEST (sans Arma) : parse -> sitrep -> embed + texte =====================
def _selftest():
    import sys
    sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
    # SITREP synthétique : M3 sous forte menace, O5 sous menace légère, le reste calme.
    toks = []
    for i, (nm, x, y, tier) in enumerate(FOBS):
        g = 12 if tier == "MAIN" else 6
        c = 8 if nm == "M3" else (3 if nm == "O5" else 0)
        toks.append("%d,%d" % (g, c))
    payload = ";".join(toks) + ";#7#8#1.70#480"            # cibles 7/8, nuit 01h42, 480 hommes
    st = OfficerState()
    sit = st.parse(payload, tick=142)
    assert len(sit["fobs"]) == 25 and sit["is_night"] and sit["targets_intact"] == 7
    thr = [f for f in sit["fobs"] if f["threatened"]]
    assert len(thr) == 2 and sit["total_threat"] == 11
    print("[test] SITREP : 25 FOB, %d menacés, %d contacts, cibles %d/%d, nuit=%s, force=%d" %
          (len(thr), sit["total_threat"], sit["targets_intact"], sit["targets_total"], sit["is_night"], sit["total_force"]))
    # alimente le RAG ?
    from officer_memory import embed_theatre
    emb = embed_theatre(sit)
    assert len(emb) == 25 * 4 + 2
    print("[test] embed_theatre(sit) -> vecteur de %d features (alimente le RAG) OK" % len(emb))
    # le texte pour Qwen
    print("---- TEXTE POUR QWEN ----")
    print(OfficerState.to_text(sit))
    print("=== officer_state OK : lit -> SITREP -> nourrit RAG (embed) ET Qwen (texte) ===")


if __name__ == "__main__":
    _selftest()
