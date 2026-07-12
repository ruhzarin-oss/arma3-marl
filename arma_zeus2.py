"""arma_zeus2 — handler Zeus RENFORCE : boucle qui, pour chaque joueur, le rend INVULNERABLE et lui assigne
Zeus (maitre du jeu) dans la seconde, et garde toutes les unites editables (y compris celles spawnees apres)."""
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"

SQF = r'''
if (isNil "HMT_ZEUS2") then {
  HMT_ZEUS2 = true;
  [] spawn {
    while {true} do {
      {
        _x allowDamage false;
        if (isNull (getAssignedCuratorLogic _x)) then {
          private _cur = (createGroup sideLogic) createUnit ["ModuleCurator_F", [0,0,0], [], 0, "NONE"];
          _cur setVariable ["owner", owner _x, true];
          _x assignCurator _cur;
          HMT_CUR = _cur;
          diag_log "HARMATTAN_ZEUS2 curator assigne + invulnerable";
        };
        if (!isNil "HMT_CUR") then { HMT_CUR addCuratorEditableObjects [allUnits, true]; };
      } forEach allPlayers;
      sleep 1;
    };
  };
  diag_log "HARMATTAN_ZEUS2 handler actif";
};
'''

if __name__ == "__main__":
    env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
    env.b.send(SQF, wait=True)
    print("Zeus2 injecte : tout joueur devient invulnerable + maitre du jeu (Zeus) dans la seconde.")
