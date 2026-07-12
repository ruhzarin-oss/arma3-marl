"""arma_officer — boucle PERCEPTION->DECISION sur le VRAI terrain Altis : on calcule l'exposition par axe
sur le relief reel (terrainIntersectASL), on en fait une carte tactique, et l'OFFICIER-LLM (qwen) la lit ->
choisit l'axe -> justifie en clair. On verifie qu'il choisit le defile reel. Pas de combat ici : c'est le
pont perception+decision sim->reel de l'officier-axe, ferme bout-en-bout sur Arma. (combat = jalon 2)."""
import json
import re
import urllib.request
from op_arma import OpArma

OLLAMA = "http://localhost:11434/api/chat"; MODEL = "qwen2.5:14b"
NAMES = ["Nord", "Nord-Est", "Est", "Sud-Est", "Sud", "Sud-Ouest", "Ouest", "Nord-Ouest"]
OBJ = (12000, 21000)   # objectif a defile fort trouve par le scan (h=123m, spread 70)
R_SPAWN = 170.0; NPATH = 12

SYS = ("Tu es un officier d'infanterie qui commande une escouade a l'assaut d'un point tenu par des defenseurs. "
       "Tu dois choisir l'AXE D'APPROCHE qui expose le moins ton escouade au feu : un FAIBLE pourcentage du trajet "
       "a decouvert est meilleur (l'escouade reste en defile, hors de vue). Choisis l'axe le moins expose. "
       'Reponds en JSON : {"axe":"<un des 8 noms exacts>","justification":"<1 phrase claire citant le %>"}.')


def expo_sqf(ox, oy):
    return (
        'HMT_OX=%d; HMT_OY=%d; HMT_DEF=[]; { HMT_DEF pushBack [HMT_OX+12*cos _x, HMT_OY+12*sin _x] } forEach [0,90,180,270];\n'
        'for "_k" from 0 to 7 do {\n'
        '  private _th=_k*45; private _sx=HMT_OX+%f*cos _th; private _sy=HMT_OY+%f*sin _th; private _seen=0;\n'
        '  for "_i" from 1 to %d do {\n'
        '    private _t=_i/%d; private _px=_sx+(HMT_OX-_sx)*_t; private _py=_sy+(HMT_OY-_sy)*_t;\n'
        '    private _pz=(getTerrainHeightASL [_px,_py])+1.5; private _vis=false;\n'
        '    { private _dz=(getTerrainHeightASL [_x#0,_x#1])+1.5;\n'
        '      if (!(terrainIntersectASL [[_px,_py,_pz],[_x#0,_x#1,_dz]])) then { _vis=true }; } forEach HMT_DEF;\n'
        '    if (_vis) then { _seen=_seen+1 };\n'
        '  };\n'
        '  diag_log format ["HARMATTAN_EXPO %%1 %%2", _k, round (100*_seen/%d)];\n'
        '};\n' % (ox, oy, R_SPAWN, R_SPAWN, NPATH, NPATH, NPATH)
    )


def ask_llm(carte):
    body = json.dumps({"model": MODEL, "stream": False, "format": "json", "options": {"temperature": 0.2},
                       "messages": [{"role": "system", "content": SYS},
                                    {"role": "user", "content": "Carte tactique (8 axes), terrain reel d'Altis :\n" + carte + "\n\nQuel axe et pourquoi ?"}]}).encode()
    req = urllib.request.Request(OLLAMA, body, {"Content-Type": "application/json"})
    return json.loads(json.load(urllib.request.urlopen(req, timeout=120))["message"]["content"])


if __name__ == "__main__":
    env = OpArma()
    lines = env._query(expo_sqf(*OBJ), settle=1.5)
    ex = {int(m.group(1)): int(m.group(2)) for ln in lines for m in [re.search(r"HARMATTAN_EXPO (\d+) (\d+)", ln)] if m}
    if len(ex) != 8:
        print("exposition incomplete (%d/8) -> pont sous charge" % len(ex)); raise SystemExit(1)
    vals = [ex[k] for k in range(8)]
    carte = "\n".join("  - axe %-11s : %3d%% du trajet a decouvert (sous le feu)" % (NAMES[k], vals[k]) for k in range(8))
    print("=" * 70)
    print("OFFICIER sur le VRAI terrain Altis | objectif (%d,%d)" % OBJ)
    print("=" * 70)
    print(carte)
    ans = ask_llm(carte); axe = ans.get("axe", "?"); just = ans.get("justification", "")
    ki = NAMES.index(axe) if axe in NAMES else -1
    defile = vals.index(min(vals))
    print("\n  >> OFFICIER-LLM choisit : %s (%d%% expose)" % (axe, vals[ki] if ki >= 0 else -1))
    print("     justification : %s" % just)
    print("     [verif terrain reel] defile = %s (%d%%) | choix %s"
          % (NAMES[defile], min(vals), "= LE DEFILE (correct)" if ki == defile else ("dans le top-2" if ki >= 0 and sum(v < vals[ki] for v in vals) <= 1 else "sous-optimal")))
    print(">>> BOUCLE PERCEPTION->DECISION FERMEE SUR LE VRAI TERRAIN ARMA")
