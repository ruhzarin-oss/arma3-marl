"""arma_zeus — injecte un slot ZEUS en direct sur le serveur 0 (sans redemarrage). Le 1er joueur qui rejoint
devient maitre du jeu (camera libre, voit toutes les unites, y compris celles spawnees apres)."""
from op_arma import OpArma
SB = "/mnt/data/harmattan-sandbox"

ZEUS = '''
if (isNil "HMT_ZEUS") then {
  HMT_ZEUS = true;
  [] spawn {
    waitUntil { sleep 2; count allPlayers > 0 };
    private _p = allPlayers select 0;
    private _cur = (createGroup sideLogic) createUnit ["ModuleCurator_F", [0,0,0], [], 0, "NONE"];
    _cur setVariable ["owner", owner _p, true];
    _p assignCurator _cur;
    HMT_CUR = _cur;
    diag_log "HARMATTAN_ZEUS curator pret pour le joueur";
    while {true} do { sleep 3; if (!isNull HMT_CUR) then { HMT_CUR addCuratorEditableObjects [allUnits, true]; }; };
  };
  diag_log "HARMATTAN_ZEUS handler injecte";
};
'''

if __name__ == "__main__":
    env = OpArma(squads=(("SQ_ASSAUT", 8),), mission=SB + "/arma3server/mpmissions/HarmattanBridge0.Altis", log=SB + "/logs/server0.out", seed=0)
    env.b.send(ZEUS, wait=True)
    print("Zeus injecte sur server0 (port 2402). Le 1er joueur qui rejoint devient maitre du jeu.")
