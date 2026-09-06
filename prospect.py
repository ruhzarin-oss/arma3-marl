#!/usr/bin/env python3
"""prospect — CONSTRUIRE LE BASSIN DE SITES DU BARREAU B1.

Le banc B0 gelait UN site : le meilleur d'une grille 13x13 x 36 azimuts. B1 en tire.
Cette prospection rejoue EXACTEMENT le meme score que la mission (degagement de vue moins
0,4 x rugosite locale) sur une zone bien plus large, et garde TOUS les candidats au lieu
du seul vainqueur.

⚠️ ON MESURE AUSSI LA PENTE DANS LE SENS DE LA MARCHE, et on ne la borne pas encore.
Le projet sait deja que la pente dans le sens de la marche decide du regime. Mais borner
avant d'avoir mesure la doctrine sur le tirage, ce serait decreter la difficulte au lieu
de la dimensionner. On mesure, on regarde ce que la doctrine en fait, ET SEULEMENT ALORS
on borne si elle casse — on borne le tirage, jamais on n'excuse la doctrine.
"""
import sys, time, re
sys.path.insert(0, "/home/younes/arma3-marl")
from pont import Pont
from para import instance

inst = instance(1)
p = Pont(inst["profil"], pont_dir=inst["pont"])
print(f"pont instance 1, n={p.n}", flush=True)

SQF = r'''
[] spawn {
  HMT_fnc_clear2 = {
    params ["_from", "_to"];
    private _hF = (getTerrainHeightASL _from) + 1.6;
    private _hT = (getTerrainHeightASL _to) + 1.6;
    private _min = 1e9;
    for "_i" from 1 to 29 do {
      private _t = _i / 30;
      private _q = [(_from select 0) + ((_to select 0) - (_from select 0)) * _t,
                    (_from select 1) + ((_to select 1) - (_from select 1)) * _t, 0];
      _min = _min min ((_hF + (_hT - _hF) * _t) - (getTerrainHeightASL _q));
    };
    _min
  };
  private _anc = [8291.45, 10065.42, 0];
  private _n = 0; private _vus = 0;
  diag_log "[ECHP] BASSIN DEBUT";
  for "_gx" from -20 to 20 do {
    for "_gy" from -20 to 20 do {
      private _pp = [(_anc select 0) + _gx * 55, (_anc select 1) + _gy * 55, 0];
      if (!surfaceIsWater _pp && { (count (nearestObjects [_pp, ["House"], 110])) == 0 }) then {
        for "_b" from 0 to 350 step 10 do {
          private _q = _pp getPos [150, _b];
          if (!surfaceIsWater _q && { (count (nearestObjects [_q, ["House"], 80])) == 0 }) then {
            _vus = _vus + 1;
            private _m = [_pp, _q] call HMT_fnc_clear2;
            private _dev = 0;
            { private _h = getTerrainHeightASL _x;
              for "_k" from 0 to 3 do { _dev = _dev max (abs ((getTerrainHeightASL (_x getPos [14, _k * 90])) - _h)) };
            } forEach [_pp, _q];
            private _but = _pp getPos [30, _b];
            private _pente = ((getTerrainHeightASL _but) - (getTerrainHeightASL _pp)) / 30;
            private _hmin = 1e9;
            for "_j" from 0 to 30 do {
              _hmin = _hmin min (getTerrainHeightASL (_pp getPos [_j, _b]));
            };
            if (_m > -3 && _dev < 8) then {
              _n = _n + 1;
              diag_log format ["[ECHP] BASSIN %1 %2 %3 %4 %5 %6 %7",
                (_pp select 0) toFixed 2, (_pp select 1) toFixed 2, _b,
                _m toFixed 3, _dev toFixed 3, _pente toFixed 4, _hmin toFixed 2];
            };
          };
        };
      };
    };
    sleep 0.05;
  };
  diag_log format ["[ECHP] BASSIN FIN gardes=%1 evalues=%2", _n, _vus];
};
'''
p.envoyer(SQF)
print("prospection envoyee, on ecoute...", flush=True)
t0 = time.time()
lignes, fini = [], False
while time.time() - t0 < 1800 and not fini:
    l = p.attendre("[ECHP] BASSIN", 60)
    if l is None: break
    if "FIN" in l: print(l.strip()); fini = True; break
    if "DEBUT" in l: print("  scan demarre"); continue
    lignes.append(l)
    if len(lignes) % 100 == 0: print(f"  {len(lignes)} candidats...", flush=True)

with open("/home/younes/arma3-marl/bassin_v2.txt", "w") as f:
    for l in lignes: f.write(l + "\n")
print(f"{len(lignes)} candidats ecrits dans bassin_v2.txt  ({time.time()-t0:.0f} s)")
