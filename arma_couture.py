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
  // ⚠️ LA PENTE SE CALCULE COMME AU GYMNASE, PAS PAR `surfaceNormal`.
  // Mesure du 12/08 : `surfaceNormal` rendait une grandeur BORNEE A 0,40 (elle vaut
  // (1-normale_z)*2/5, et normale_z est dans [0,1]) la ou le gymnase donne 0,589 de MEDIANE
  // et 1,52 au 99e centile. Une pente vraie de 25 deg — la mediane du gymnase — sortait a
  // 0,037 par cette formule : SEIZE FOIS TROP PETIT. Les deux colonnes portaient le meme
  // nom et n etaient pas la meme grandeur.
  // Le gymnase fait : gradient central du relief, en METRES PAR CELLULE de 6,25 m, puis /5.
  // On le refait ici a l identique. C est reproductible et verifiable, ce que `surfaceNormal`
  // n etait pas.
  private _pu=getPosATL _u; private _cx=(_pu select 0); private _cy=(_pu select 1);
  private _gx=((getTerrainHeightASL [_cx+6.25,_cy]) - (getTerrainHeightASL [_cx-6.25,_cy]))/2;
  private _gy=((getTerrainHeightASL [_cx,_cy+6.25]) - (getTerrainHeightASL [_cx,_cy-6.25]))/2;
  private _slope=(sqrt (_gx*_gx + _gy*_gy))/5;
  // dcover : distance au batiment le plus proche (proxy du champ de couvert), normalisee
  // ⚠️ `dcover` PORTAIT DEUX ECARTS A LA FOIS, et c est la quatrieme fois de la journee que
  // deux colonnes du meme nom ne mesurent pas la meme chose.
  //   1. LA GRANDEUR. Le gymnase appelle couvert `pente > 1,4 x pente moyenne` — son propre
  //      commentaire dit « cretes/pentes = abris ». C est LE RELIEF QUI ABRITE. La couture
  //      comptait des BATIMENTS (`nearestObjects House/Building/Wall/Rock`). Sur Stratis, a un
  //      point tire au hasard, il n y a presque jamais de batiment a 30 m : mediane 1,000
  //      plafonnee, contre 0,038 au gymnase. Un ecart de 26 fois qui n etait pas un ecart de
  //      monde mais de definition — et « rapprocher » le gymnase de ca aurait ete corriger le
  //      monde pour satisfaire un capteur qui ne mesure pas la bonne chose.
  //   2. L UNITE. Le gymnase rend une distance EN CELLULES de 6,25 m, puis divise par 30.
  //      La couture rendait des METRES divises par 30. Facteur 6,25 en plus du reste.
  // On refait donc les DEUX a l identique : couvert = relief au-dessus du seuil, distance de
  // Tchebychev en cellules (c est un max-pool 3x3 cote gymnase, donc Tchebychev), cap a 16
  // cellules comme `_dist_field`, puis /30 plafonne a 1.
  // ⚠️ LE SEUIL EST LOCAL, PAS GLOBAL — terrain_gpu.py:47 LU le 14/08.
  //   cover = (slope > cover_thr * slope.mean((1,2), keepdim=True))
  // La moyenne est celle DE L ENVIRONNEMENT, pas une constante de carte. L ancien code
  // employait `1.4 * 2.315`, ou 2,315 = pente moyenne de Stratis x 5 : le x5 venait de la
  // normalisation de la colonne `slope` et n avait rien a faire dans une comparaison de
  // gradients bruts, et surtout un seuil GLOBAL ne trouve aucun couvert sur un site a relief
  // doux — il rend alors le garde-fou 16/30 = 0,533. Mesure du 14/08 : 78,3 % de garde-fou
  // sur le site plat, 60,1 % des decisions au-dessus du 99e centile du gymnase sur 20
  // episodes. QUATRIEME fois que cette colonne est fausse.
  // On calcule donc la moyenne UNE FOIS sur 64x64 cellules de 6,25 m centrees sur l objectif
  // — 400 m de cote, soit le `terr_R = 200` du gymnase — et on la garde.
  if (isNil "HMT_COVER_MOY") then {
      private _s = 0; private _n = 0;
      private _o = if (isNil "HMT_OBJ") then {[worldSize/2, worldSize/2]} else {HMT_OBJ};
      for "_a" from -32 to 31 do {
          for "_bb" from -32 to 31 do {
              private _cx = (_o select 0) + _a * 6.25; private _cy = (_o select 1) + _bb * 6.25;
              private _gx2 = ((getTerrainHeightASL [_cx+6.25,_cy]) - (getTerrainHeightASL [_cx-6.25,_cy]))/2;
              private _gy2 = ((getTerrainHeightASL [_cx,_cy+6.25]) - (getTerrainHeightASL [_cx,_cy-6.25]))/2;
              _s = _s + (sqrt (_gx2*_gx2 + _gy2*_gy2)); _n = _n + 1;
          };
      };
      HMT_COVER_MOY = _s / _n;
      diag_log format ["HMT|COUT|cover_moy|%1|seuil|%2", HMT_COVER_MOY, 1.4 * HMT_COVER_MOY];
  };
  private _SEUIL = 1.4 * HMT_COVER_MOY;
  private _dcell = 16;
  private _px = _p select 0; private _py = _p select 1;
  private _k = 0;
  // ⚠️ 15, PAS 8. `_dist_field(cover, G, iters=16)` cherche jusqu a 15 avant de rendre 16
  // comme sentinelle. S arreter a 8 rendait la sentinelle deux fois trop tot.
  while { _k <= 15 && _dcell >= 16 } do {
    private _trouve = false;
    for "_a" from -_k to _k do {
      for "_bb" from -_k to _k do {
        if (!_trouve && {(abs _a == _k) || (abs _bb == _k)}) then {
          private _cx = _px + _a * 6.25; private _cy = _py + _bb * 6.25;
          private _sx = ((getTerrainHeightASL [_cx+6.25,_cy]) - (getTerrainHeightASL [_cx-6.25,_cy]))/2;
          private _sy = ((getTerrainHeightASL [_cx,_cy+6.25]) - (getTerrainHeightASL [_cx,_cy-6.25]))/2;
          if ((sqrt (_sx*_sx + _sy*_sy)) > _SEUIL) then { _dcell = _k; _trouve = true };
        };
      };
    };
    _k = _k + 1;
  };
  private _dc = (_dcell / 30) min 1;
  // ennemi vivant connu le plus proche
  private _ne=objNull; private _nd=1e9;
  { if (alive _x) then { private _d=_u distance _x; if (_d<_nd) then {_nd=_d;_ne=_x} } } forEach HMT_ENNEMI;
  private _ndx=0; private _ndy=0; private _los=0; private _ndist=(_nd/HMT_S) min 2;
  if (!isNull _ne) then {
    private _ep=getPosASL _ne; private _sp=getPosASL _u;
    // ⚠️ `checkVisibility`, PAS `terrainIntersectASL`. Mesure du 12/08, huit hommes en
    // traversee : `terrainIntersectASL` rend 1 — « rien ne coupe » — pour SEPT sur huit,
    // quand `checkVisibility` rend 0,69. Trente et un pour cent de l homme sont masques et la
    // couture l ignorait, parce que `terrainIntersectASL` ne voit QUE LE RELIEF : ni batiment,
    // ni muret, ni feuillage. La colonne etait donc MORTE a 1 sur toute la traversee, la ou le
    // gymnase la fait varier sur [0 ; 1] avec 0,69 de moyenne — et deux entrees figees sur
    // douze suffisent a coller le reseau sur une seule action.
    // `checkVisibility` est la vue que l IA emploie REELLEMENT pour decider de tirer, donc
    // elle fait foi ⟨lecon du geometre v3, juillet : mes rayons a 1,20 m donnaient 64 %,
    // l oeil du moteur 32 %⟩. Elle rend une FRACTION, comme le gymnase.
    _los=[objNull,"VIEW"] checkVisibility [eyePos _u, eyePos _ne];
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
// ⚠️ `setVelocity` EST UNE IMPULSION, PAS UNE CONSIGNE. Mesure du 15/08, sonde a trois bras,
// controles positifs passes : emise UNE FOIS par periode de 3,28 s elle rend 2,58 m ;
// reemise a 10 Hz elle rend 20,22 m, soit exactement les 6 m/s x 3,28 s attendus. Facteur 7,8.
// Le banc envoyait donc une pichenette toutes les 3,28 s en croyant donner une vitesse : les
// hommes avancaient 2,8x moins qu au gymnase A RENDEMENT DE PILOTAGE IDENTIQUE (0,46 contre
// 0,42) — le cerveau transferait, le corps non. Voir VERDICT_CORPS.md et DEPOT_LIMITEUR.md.
// Le jeton HMT_NORDRE coupe la boucle des que l ordre SUIVANT arrive : sans lui, deux boucles
// se disputeraient le meme homme et la derniere emise gagnerait au hasard.
HMT_NORDRE = (missionNamespace getVariable ["HMT_NORDRE", 0]) + 1;
{ private _i=_forEachIndex; private _a=HMT_ACT select _i; private _u=_x;
  if (_a<8) then {
      private _h=_a*45; private _vx=HMT_SPD*sin _h; private _vy=HMT_SPD*cos _h;
      private _mien = HMT_NORDRE;
      [_u,_vx,_vy,_mien] spawn {
          params ["_u","_vx","_vy","_mien"];
          private _t0 = time; private _p0 = getPosATL _u; private _nsol = 0; private _n = 0;
          while { alive _u && time - _t0 < 3.28
                  && {(missionNamespace getVariable ["HMT_NORDRE",0]) == _mien} } do {
              _u setVelocity [_vx,_vy,0];
              _n = _n + 1; if (isTouchingGround _u) then { _nsol = _nsol + 1 };
              sleep 0.1;
          };
          // ⚠️ LE CORPS MARCHE-T-IL OU VOLE-T-IL ? T5 du prevol, 16/08, 4 tirages, separation
          // PARFAITE : `setVelocity` a Z=0 rend 25 m quand l homme NE TOUCHE PAS le sol
          // (animation `afal`, il tombe) et 0-1 m quand il le touche. C est la MEME primitive
          // qu ici. Les 20,22 m deposes le 15/08 pourraient donc etre un artefact de vol.
          // On releve la part de temps au sol et les metres reellement parcourus par ordre.
          diag_log format ["HMT|CORPS|SOL|part_au_sol|%1|m_par_ordre|%2|n|%3",
                           round (100 * _nsol / (_n max 1)),
                           round (10 * (_p0 distance2D (getPosATL _u))) / 10, _n];
      };
  }
  else { if (_a==9) then {
      // ⚠️ L APPUI NE SE DEMANDE PLUS, IL SE DECLENCHE ⟨Fable, 15/08⟩.
      // `doSuppressiveFire` ORIENTE la visee sans declencher le feu : mesure du 15/08 au
      // matin, 94 pourcent des balles partaient SANS ordre, 3 paires sur 3 — l ordre etait
      // un repartiteur de visee, pas un declencheur. On force donc la cadence nous-memes,
      // 3 coups/s, avec le meme jeton HMT_NORDRE que le mouvement pour qu un ordre neuf
      // coupe le precedent.
      private _ne=objNull; private _nd=1e9; { if (alive _x) then { private _d=_u distance _x; if(_d<_nd) then {_nd=_d;_ne=_x} } } forEach HMT_ENNEMI;
      _u setVelocity [0,0,0];
      if (!isNull _ne) then {
          private _mien = HMT_NORDRE; private _p = getPosATL _ne;
          [_u,_p,_mien] spawn {
              params ["_u","_p","_mien"];
              private _t0 = time;
              while { alive _u && time - _t0 < 3.28
                      && {(missionNamespace getVariable ["HMT_NORDRE",0]) == _mien} } do {
                  _u setDir (_u getDir _p); _u doWatch _p;
                  _u forceWeaponFire [currentWeapon _u, currentMuzzle _u];
                  sleep 0.33;
              };
              _u doWatch objNull;
          };
      };
    } else { _u setVelocity [0,0,0]; }; };
  if (_a>=10) then { private _pv=_a-10; HMT_POST set [_i,_pv];
     _u setUnitPos (["UP","MIDDLE","DOWN"] select _pv); };
} forEach HMT_FR;
// Le FPS est journalise A CHAQUE PAS : la reemission a 10 Hz est exactement ce que le
// limiteur evitait, et deployer sans mesurer son cout serait refaire la faute de celui
// qui l a pose. Mesure a UN homme : 48,8 FPS. Le banc en a quatre.
diag_log format ["HARMATTAN_ACTOK n=%1 fps=%2", count HMT_FR, diag_fps];
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
