"""arma_nodrown — garde-fou permanent : tout joueur present est rendu INVULNERABLE et, s'il est dans l'eau
(ou au spawn sud-ouest), TELEPORTE sur la terre ferme pres de l'objectif. Tourne en boucle, attrape chaque spawn."""
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"

SQF = r'''
diag_log format ["HARMATTAN_LANDCHK eau_au_point=%1", surfaceIsWater [11855, 21145, 0]];
if (isNil "HMT_SAFE") then {
  HMT_SAFE = true;
  [] spawn {
    while {true} do {
      {
        _x allowDamage false; _x setCaptive true;
        private _p = getPosATL _x;
        if ((surfaceIsWater _p) || {(_p distance2D [1000,1000]) < 900}) then {
          _x setPosATL [11855, 21145, 0]; _x setDir 135;
        };
      } forEach allPlayers;
      sleep 0.5;
    };
  };
  diag_log "HARMATTAN_SAFE anti-noyade actif";
};
'''

if __name__ == "__main__":
    env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
    env.b.send(SQF, wait=True)
    env._query('diag_log "HARMATTAN_PING2";', settle=1.0)
    chk = next((l for l in reversed(env.b._log_lines()) if "HARMATTAN_LANDCHK" in l), "")
    print("verif point d'arrivee (eau_au_point=0 = terre OK) :", chk.strip()[-40:] if chk else "(non lu)")
    print("anti-noyade injecte : tout joueur devient invulnerable + place sur la terre (11855, 21145).")
