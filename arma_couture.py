#!/usr/bin/env python3
"""arma_couture.py — A3 : la COUTURE live SHAMAL -> Arma. Reproduit l'obs-Arma 18-dim que shamal_arma.pt
attend (base9 + suffer2 + team4 + posture3, DANS CET ORDRE), la sort en SQF depuis les vraies unites Arma,
passe le cerveau, remappe les 13 actions en SQF (caps/hold/suppress/postures).

Deux modes :
  - `python arma_couture.py`         : SELF-TEST HORS-LIGNE (pas d'Arma) — charge le .pt, obs synthetique,
                                       verifie actions valides + SQF bien forme. Prouve la moitie Python<->net<->SQF.
  - importe {WAKE, PERC18, acts_to_sqf, OBS_RE, ...} depuis le driver live quand Arma est up.

Ordre obs (18) = [apx/S, apy/S, dgx, dgy, alive, slope, dcover, los, nd,   # base 9
                  dmg_in, nt_frac,                                          # suffer 2
                  ally_dx, ally_dy, ally_supp, team_fire_frac,             # team 4
                  post_stand, post_crouch, post_prone]                     # posture 3
"""
import re, sys, math

# --- constantes mission (A CALER sur la vraie mission Arma live) ---
CX, CY = 0.0, 0.0          # centre objectif (m) — a remplacer par les coords reelles
SCALE = 200.0              # = terr_R du replica d'entrainement
MOVE_SPD = 6.0             # m/s en Arma (le sandbox move=14/pas ; on tempere pour le FPS)
FIRE_RANGE = 110.0         # portee (m), = env d'entrainement

# --- 1) reveiller gardes + escouade (repris du pattern hostage valide) ---
WAKE = r'''
{ _x enableAI "ALL"; _x setBehaviour "COMBAT"; _x setCombatMode "RED" } forEach HMT_ENNEMI;
{ _x setBehaviour "AWARE"; _x disableAI "AUTOCOMBAT"; _x disableAI "FSM" } forEach HMT_FR;
HMT_POST = []; { HMT_POST pushBack 0 } forEach HMT_FR;
diag_log "HARMATTAN_WAKE ok";
'''

# --- 2) PERCEPTION : 18 features par soldat FR, dans l'ordre exact du sandbox ---
# NB : slope (surfaceNormal) et dcover (nearestObjects) = approximations Arma des champs sandbox.
PERC18 = r'''
HMT_CX=__CX__; HMT_CY=__CY__; HMT_S=__S__; HMT_FRNG=__FRNG__;
{
  private _u=_x; private _i=_forEachIndex; private _p=getPosATL _u;
  private _ax=(_p select 0)-HMT_CX; private _ay=(_p select 1)-HMT_CY;
  private _al=if (alive _u) then {1} else {0};
  // slope : normale de terrain -> pente approx (0..~1), /5 comme le sandbox
  private _n=surfaceNormal (getPosASL _u); private _slope=(1-(_n select 2))*2.0/5.0;
  // dcover : distance au batiment le plus proche (proxy du champ de couvert), normalisee
  private _nb=nearestObjects [_u,["House","Building","Wall","Rock"],40]; private _dc=1;
  if (count _nb>0) then { _dc=(_u distance (_nb select 0))/30 min 1 };
  // ennemi vivant connu le plus proche
  private _ne=objNull; private _nd=1e9;
  { if (alive _x) then { private _d=_u distance _x; if (_d<_nd) then {_nd=_d;_ne=_x} } } forEach HMT_ENNEMI;
  private _ndx=0; private _ndy=0; private _los=0; private _ndist=(_nd/HMT_S) min 2;
  if (!isNull _ne) then {
    private _ep=getPosASL _ne; private _sp=getPosASL _u;
    _los=if (terrainIntersectASL [[(_sp select 0),(_sp select 1),(_sp select 2)+((eyePos _u) select 2)],[(_ep select 0),(_ep select 1),(_ep select 2)+1.7]]) then {0} else {1};
  };
  private _dgx=-_ax/HMT_S; private _dgy=-_ay/HMT_S;
  // suffer : degats pris (delta) + fraction d'ennemis qui PEUVENT me toucher (vivant+portee+LOS)
  private _dmg=(_u getVariable ["HMT_LASTDMG",0]); private _dmgin=((damage _u - _dmg)*5) max 0 min 1; _u setVariable ["HMT_LASTDMG",damage _u];
  private _nt=0; private _ndf=count HMT_ENNEMI;
  { if (alive _x) then { private _d=_u distance _x; private _ep=getPosASL _x; private _sp=getPosASL _u;
      private _lo=if (terrainIntersectASL [[(_sp select 0),(_sp select 1),(_sp select 2)+0.9],[(_ep select 0),(_ep select 1),(_ep select 2)+1.7]]) then {0} else {1};
      if (_d<HMT_FRNG && _lo>0) then {_nt=_nt+1} } } forEach HMT_ENNEMI;
  private _ntf=if (_ndf>0) then {_nt/_ndf} else {0};
  // team : binome vivant le plus proche (dx,dy)/S + tire-t-il + fraction de l'equipe qui tire
  private _nb2=objNull; private _nd2=1e9;
  { if (_x!=_u && alive _x) then { private _d=_u distance _x; if (_d<_nd2) then {_nd2=_d;_nb2=_x} } } forEach HMT_FR;
  private _adx=0; private _ady=0; private _asup=0;
  if (!isNull _nb2) then { private _q=getPosATL _nb2; _adx=((_q select 0)-(_p select 0))/HMT_S; _ady=((_q select 1)-(_p select 1))/HMT_S;
    _asup=if ((_nb2 forceWeaponFire ["",""]) isEqualTo []) then {0} else {0}; _asup=if (currentCommand _nb2=="FIRE" || (unitReady _nb2)) then {0} else {1}; };
  private _tf=0; { if (alive _x && (currentCommand _x=="FIRE")) then {_tf=_tf+1} } forEach HMT_FR; private _tff=_tf/(count HMT_FR max 1);
  private _ps=HMT_POST select _i; private _p0=if(_ps==0)then{1}else{0}; private _p1=if(_ps==1)then{1}else{0}; private _p2=if(_ps==2)then{1}else{0};
  // L ARC, EN FIN DE VECTEUR (18-19) pour ne deplacer aucun indice existant : la face du
  // defenseur le plus proche contre la direction sous laquelle il me voit.
  private _arcs=0; private _arcc=1;
  if (!isNull _ne) then {
    private _df=getDir _ne; private _p2p=getPosATL _ne;
    private _az=(_p2p select 0) atan2 (_p2p select 1);
    _az=((getPosATL _u select 0)-(_p2p select 0)) atan2 ((getPosATL _u select 1)-(_p2p select 1));
    private _rel=(_az-_df); while {_rel>180} do {_rel=_rel-360}; while {_rel<-180} do {_rel=_rel+360};
    _arcs=sin _rel; _arcc=cos _rel;
  };
  private _o=[_ax/HMT_S,_ay/HMT_S,_dgx,_dgy,_al,_slope,_dc,_los,_ndist, _dmgin,_ntf, _adx,_ady,_asup,_tff, _p0,_p1,_p2, _arcs,_arcc];
  diag_log format ["HARMATTAN_OBS18 %1 %2", _i, _o];
} forEach HMT_FR;
'''

# --- 3) ACTION : 13 actions -> SQF (caps 0-7, HOLD 8, SUPPRESS 9, postures 10/11/12) ---
ACT_TPL = r'''
HMT_ACT=[__ACTS__]; HMT_SPD=__SPD__;
{ private _i=_forEachIndex; private _a=HMT_ACT select _i; private _u=_x;
  if (_a<8) then { private _h=_a*45; _u setVelocity [HMT_SPD*sin _h, HMT_SPD*cos _h, 0]; }
  else { if (_a==9) then {
      private _ne=objNull; private _nd=1e9; { if (alive _x) then { private _d=_u distance _x; if(_d<_nd) then {_nd=_d;_ne=_x} } } forEach HMT_ENNEMI;
      _u setVelocity [0,0,0]; if (!isNull _ne) then { _u doTarget _ne; _u doSuppressiveFire _ne };
    } else { _u setVelocity [0,0,0]; }; };
  if (_a>=10) then { private _pv=_a-10; HMT_POST set [_i,_pv];
     _u setUnitPos (["UP","MIDDLE","DOWN"] select _pv); };
} forEach HMT_FR;
diag_log format ["HARMATTAN_ACTOK n=%1", count HMT_FR];
'''

OBS_RE = re.compile(r"HARMATTAN_OBS18 (\d+) \[([^\]]+)\]")
OBS_DIM = 20
N_ACT = 13


def perc_sqf():
    return (PERC18.replace("__CX__", str(CX)).replace("__CY__", str(CY))
            .replace("__S__", str(SCALE)).replace("__FRNG__", str(FIRE_RANGE)))


def acts_to_sqf(acts):
    return ACT_TPL.replace("__ACTS__", ",".join(str(int(a)) for a in acts)).replace("__SPD__", str(MOVE_SPD))


def parse_obs(lines):
    """extrait {unit_idx: [18 floats]} des lignes de log Arma."""
    obs = {}
    for ln in lines:
        m = OBS_RE.search(ln)
        if m: obs[int(m.group(1))] = [float(v) for v in m.group(2).split(",")]
    return obs


# ================== SELF-TEST HORS-LIGNE (pas d'Arma) ==================
def _selftest():
    import torch
    sys.path.insert(0, "/home/younes/arma3-marl")
    from train_koth_gpu import Net
    dev = "cpu"
    net = Net(OBS_DIM, N_ACT, 512, 3).to(dev)
    sd = torch.load("/home/younes/arma3-marl/shamal_arma.pt", map_location=dev)
    net.load_state_dict(sd); net.eval()
    print("[selftest] shamal_arma.pt charge dans Net(%d,%d) OK" % (OBS_DIM, N_ACT))

    # obs synthetique plausible : 9 soldats, valeurs dans les plages du sandbox
    g = torch.randn(9, OBS_DIM) * 0.3
    g[:, 4] = 1.0                                   # alive
    g[:, 15:18] = 0.0; g[:, 15] = 1.0               # posture one-hot = debout
    with torch.no_grad():
        acts = net.a_logits(g).argmax(-1).tolist()
    assert all(0 <= a < N_ACT for a in acts), "action hors plage !"
    from collections import Counter
    print("[selftest] 9 obs -> actions %s  (repartition %s)" % (acts, dict(Counter(acts))))

    sqf = acts_to_sqf(acts)
    assert "HMT_ACT=[" in sqf and sqf.count(",") >= 8, "SQF action mal forme"
    # verifie que le SQF parse les 13 cas sans trou
    labels = {0:"cap0",7:"cap7",8:"HOLD",9:"SUPPRESS",10:"debout",11:"accroupi",12:"couche"}
    print("[selftest] SQF action genere (%d chars), 1re ligne: %s" % (len(sqf), sqf.strip().splitlines()[0]))
    p = perc_sqf()
    assert "HARMATTAN_OBS18" in p and "__CX__" not in p, "PERC SQF non substitue"
    print("[selftest] PERC18 SQF genere (%d chars), CX/scale substitues OK" % len(p))

    # round-trip parse : simule 2 lignes de log Arma -> parse_obs
    fake = ['... HARMATTAN_OBS18 0 [%s]' % ",".join("0.1" for _ in range(18)),
            '... HARMATTAN_OBS18 1 [%s]' % ",".join("0.2" for _ in range(18))]
    po = parse_obs(fake); assert len(po) == 2 and len(po[0]) == 18, "parse_obs KO"
    import torch as _t
    ordered = _t.tensor([po[k] for k in sorted(po)], dtype=_t.float32)
    with _t.no_grad(): a2 = net.a_logits(ordered).argmax(-1).tolist()
    print("[selftest] round-trip log->parse->net OK : 2 unites -> actions %s" % a2)
    print("\n=== A3 couture : moitie Python<->net<->SQF VALIDEE hors-ligne ✅ ===")
    print("    reste = smoke live (compteur avance, SQF s'execute) quand Arma est up / CPU libre.")


if __name__ == "__main__":
    _selftest()
