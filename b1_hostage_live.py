"""B1 — episode otage LIVE dans Arma (serveur dedie 14). Construit par etapes.
Etape 2 : spawn du scenario (9 amis + otage + 6 gardes) et confirmation via read_obs."""
import time
from collections import Counter
from arma_bridge import ArmaBridge

b = ArmaBridge()
print("bridge:", b.bridge, flush=True)

SPAWN = r'''
[] spawn {
  createCenter west; createCenter east; createCenter civilian;
  private _c = [3500, 13000, 0];
  HMT_OBJ = _c;
  HMT_INS = [_c select 0, (_c select 1) - 200, 0];
  HMT_EXT = HMT_INS;
  // otage = civil captif au centre
  private _civg = createGroup civilian;
  HMT_HOSTAGE = _civg createUnit ["C_man_1_F", _c, [], 0, "NONE"];
  HMT_HOSTAGE setCaptive true; HMT_HOSTAGE disableAI "ALL"; HMT_HOSTAGE setBehaviour "CARELESS";
  // gardes OPFOR en cercle autour de l'otage
  private _gg = createGroup east; HMT_GUARDS = [];
  for "_i" from 0 to 5 do {
    private _a = _i * 60;
    private _gp = [(_c select 0) + 30*cos _a, (_c select 1) + 30*sin _a, 0];
    private _u = _gg createUnit ["O_Soldier_F", _gp, [], 0, "FORM"]; HMT_GUARDS pushBack _u;
  };
  // escouade BLUFOR a l'insertion (200 m au sud)
  private _bg = createGroup west; HMT_FR = [];
  for "_i" from 0 to 8 do {
    private _sp = [(HMT_INS select 0) + (_i mod 3)*5, (HMT_INS select 1) + (floor(_i/3))*5, 0];
    private _u = _bg createUnit ["B_Soldier_F", _sp, [], 0, "NONE"]; HMT_FR pushBack _u;
  };
  diag_log format ["HARMATTAN_SPAWN fr=%1 guards=%2 hostage=%3", count HMT_FR, count HMT_GUARDS, !isNull HMT_HOSTAGE];
};
'''

n = b.send(SPAWN, wait=True, timeout=20)
print("spawn cmd recue:", n, flush=True)
time.sleep(4)
u = b.read_obs(timeout=15)
print("unites vues:", len(u), "| par side:", dict(Counter(x["side"] for x in u)), flush=True)
for x in u[:20]:
    print(x, flush=True)
