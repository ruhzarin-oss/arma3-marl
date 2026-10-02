"""Quatrieme jugement de la porte du lecteur ( HMT-191, R6 ) : un releve NEUF dans le jeu en marche, sans mods.

  python -m guerre.arsenal.releve_jeu sqf            ecrit la commande -init ( une ligne, guillemets simples )
  python -m guerre.arsenal.releve_jeu juger <rpt>    juge le lecteur contre le journal du jeu

Genres : n = isNumber / getNumber, t = isText / getText, a = isArray / getArray, c = isClass / configName."""
import json
import re
import sys

from . import configs as CF

SORTIE = "/mnt/data/hmt/arsenal/porte_releve.json"
JEU = tuple(d for d in CF.DOSSIERS_JEU if d != "Contact")
MODS_PAR_DEFAUT = {"a3", "curator", "kart", "heli", "mark", "expansion", "jets", "argo", "orange", "tacops", "tank",
                   "enoch", "aow"}


def _sondes():
    s = []
    armes = ("arifle_Katiba_F", "srifle_LRR_F", "LMG_Zafir_F", "launch_NLAW_F", "hgun_P07_F", "arifle_SPAR_01_blk_F",
             "srifle_DMR_06_camo_F", "arifle_AK12_F", "MMG_01_hex_F", "arifle_MSBS65_F")
    for w in armes:
        for k in ("inertia", "dexterity", "initSpeed", "maxZeroing"): s.append(("n", ("CfgWeapons", w, k)))
        s.append(("a", ("CfgWeapons", w, "magazines")))
    for w in ("arifle_Katiba_F", "LMG_Zafir_F", "arifle_AK12_F"):
        for md in ("Single", "FullAuto"):
            for k in ("reloadTime", "dispersion"): s.append(("n", ("CfgWeapons", w, md, k)))
    for m in ("30Rnd_65x39_caseless_green", "150Rnd_762x54_Box", "7Rnd_408_Mag", "NLAW_F", "16Rnd_9x21_Mag",
              "30Rnd_762x39_AK12_Mag_F"):
        for k in ("count", "initSpeed", "mass"): s.append(("n", ("CfgMagazines", m, k)))
        s.append(("t", ("CfgMagazines", m, "ammo")))
    for a in ("B_65x39_Caseless_green", "B_762x54_Ball", "B_408_Ball", "B_9x21_Ball"):
        for k in ("hit", "caliber", "typicalSpeed", "airFriction"): s.append(("n", ("CfgAmmo", a, k)))
    for k in ("hit", "indirectHit", "indirectHitRange"): s.append(("n", ("CfgAmmo", "M_NLAW_AT_F", k)))
    s.append(("t", ("CfgAmmo", "M_NLAW_AT_F", "simulation")))
    s.append(("t", ("CfgAmmo", "B_762x54_Ball", "simulation")))
    for v in ("B_MBT_01_cannon_F", "O_APC_Tracked_02_cannon_F", "B_Truck_01_transport_F", "I_MRAP_03_F",
              "B_Heli_Light_01_F", "B_T_LSV_01_armed_F", "O_MBT_04_cannon_F"):
        for k in ("maxSpeed", "fuelCapacity", "armor", "transportSoldier", "side"): s.append(("n", ("CfgVehicles", v, k)))
        s.append(("t", ("CfgVehicles", v, "faction")))
    for v in ("B_MBT_01_cannon_F", "O_MBT_04_cannon_F"):
        s.append(("a", ("CfgVehicles", v, "Turrets", "MainTurret", "weapons")))
        s.append(("a", ("CfgVehicles", v, "Turrets", "MainTurret", "magazines")))
        s.append(("n", ("CfgVehicles", v, "HitPoints", "HitHull", "armor")))
    for u in ("B_Soldier_F", "O_Soldier_F", "I_soldier_F"):
        for k in ("sensitivity", "camouflage", "audible", "armor"): s.append(("n", ("CfgVehicles", u, k)))
    s += [("n", ("CfgVehicles", "B_MBT_01_cannon_F", "radius")), ("n", ("CfgWeapons", "arifle_Katiba_F", "audibleFire")),
          ("n", ("CfgAmmo", "B_408_Ball", "minRange")), ("n", ("CfgMagazines", "7Rnd_408_Mag", "hmt_nexiste_pas")),
          ("c", ("CfgVehicles", "HMT_bidon_F")), ("c", ("CfgWeapons", "HMT_bidon_F")),
          ("c", ("CfgVehicles", "O_MBT_04_cannon_F")), ("c", ("CfgWeapons", "arifle_MSBS65_F", "Single"))]
    return s


def _sondes_r7():
    """Cinquieme jugement ( R7 ) : des classes IMBRIQUEES et heritees jamais sondees ( points d impact, tourelles,
    protection des gilets et des casques )."""
    s = []
    vehicules = ("B_APC_Tracked_01_rcws_F", "B_APC_Wheeled_01_cannon_F", "O_APC_Wheeled_02_rcws_v2_F",
                 "I_APC_Wheeled_03_cannon_F", "I_MBT_03_cannon_F", "O_MBT_02_cannon_F", "B_AFV_Wheeled_01_cannon_F",
                 "O_APC_Tracked_02_AA_F", "B_MRAP_01_F", "C_Offroad_01_F")
    for v in vehicules:
        for h in ("HitHull", "HitEngine", "HitFuel", "HitLTrack", "HitRTrack", "HitBody"):
            for k in ("armor", "passThrough"): s.append(("n", ("CfgVehicles", v, "HitPoints", h, k)))
    for v in vehicules[:8]:
        s.append(("a", ("CfgVehicles", v, "Turrets", "MainTurret", "weapons")))
        s.append(("a", ("CfgVehicles", v, "Turrets", "MainTurret", "magazines")))
        for k in ("maxElev", "minElev"): s.append(("n", ("CfgVehicles", v, "Turrets", "MainTurret", k)))
        s.append(("n", ("CfgVehicles", v, "Turrets", "MainTurret", "Turrets", "CommanderOptics", "maxElev")))
    for g in ("V_PlateCarrier1_rgr", "V_PlateCarrierGL_rgr", "V_TacVest_oli", "V_Chestrig_khk", "V_PlateCarrierSpec_rgr"):
        for k in ("armor", "passThrough"): s.append(("n", ("CfgWeapons", g, "ItemInfo", "HitpointsProtectionInfo", "Chest", k)))
    for c in ("H_HelmetB", "H_HelmetSpecB", "H_HelmetO_ocamo", "H_HelmetIA"):
        for k in ("armor", "passThrough"): s.append(("n", ("CfgWeapons", c, "ItemInfo", "HitpointsProtectionInfo", "Head", k)))
    return s


def _sondes_r8():
    """Sixieme jugement ( R8 ) : des classes FEUILLES ( variantes ) qui heritent presque tout de leur base."""
    s = []
    for u in ("B_Soldier_GL_F", "B_soldier_AA_F", "O_Soldier_TL_F", "I_Soldier_AT_F", "B_recon_F", "O_sniper_F",
              "I_crew_F", "B_Pilot_F", "C_man_1", "B_diver_F"):
        for k in ("camouflage", "sensitivityEar", "audible", "armorStructural"): s.append(("n", ("CfgVehicles", u, k)))
    for v in ("B_MBT_01_TUSK_F", "B_APC_Tracked_01_CRV_F", "B_APC_Tracked_01_AA_F", "O_MRAP_02_hmg_F", "I_MRAP_03_hmg_F",
              "B_Truck_01_ammo_F", "O_Truck_02_fuel_F", "B_Heli_Transport_01_F", "O_Heli_Light_02_unarmed_F",
              "I_Heli_light_03_unarmed_F"):
        for k in ("fuelCapacity", "maxSpeed", "armor"): s.append(("n", ("CfgVehicles", v, k)))
        s.append(("t", ("CfgVehicles", v, "crew")))
    for w in ("arifle_MX_Black_F", "arifle_MXC_khk_F", "arifle_TRG21_F", "arifle_Mk20_plain_F", "srifle_EBR_F",
              "srifle_GM6_camo_F", "LMG_Mk200_F", "hgun_ACPC2_F", "arifle_CTAR_blk_F", "launch_RPG32_F"):
        for k in ("inertia", "dexterity", "maxZeroing"): s.append(("n", ("CfgWeapons", w, k)))
        s.append(("a", ("CfgWeapons", w, "magazines")))
    for m in ("30Rnd_65x39_caseless_mag_Tracer", "30Rnd_556x45_Stanag_Tracer_Red", "20Rnd_762x51_Mag",
              "200Rnd_65x39_cased_Box_Tracer", "9Rnd_45ACP_Mag"):
        for k in ("count", "initSpeed", "mass"): s.append(("n", ("CfgMagazines", m, k)))
    s += [("n", ("CfgVehicles", "B_Pilot_F", "hmt_nexiste_pas")), ("n", ("CfgWeapons", "arifle_TRG21_F", "hmt_bidon")),
          ("c", ("CfgVehicles", "HMT_variante_bidon_F")), ("c", ("CfgMagazines", "HMT_chargeur_bidon")),
          ("t", ("CfgVehicles", "C_man_1", "hmt_texte_bidon")), ("a", ("CfgWeapons", "hgun_ACPC2_F", "hmt_tableau_bidon"))]
    return s


JEUX = {"r6": _sondes, "r7": _sondes_r7, "r8": _sondes_r8}

SONDES = _sondes()
JEU_COURANT = "r6"


def sqf():
    """La commande -init : une ligne, guillemets simples seulement ( la ligne de commande garde les doubles )."""
    lst = ",".join("['%s',[%s]]" % (g, ",".join("'%s'" % x for x in ch)) for g, ch in SONDES)
    return ("{private _g=_x select 0;private _e=configFile;{_e=_e>>_x}forEach(_x select 1);"
            "private _r=switch(_g)do{case 'n':{[isNumber _e,getNumber _e]};case 't':{[isText _e,getText _e]};"
            "case 'a':{[isArray _e,getArray _e]};default{[isClass _e,configName _e]}};"
            "diag_log format['HMTCFG|%1|%2|%3|%4',_forEachIndex,_g,_r select 0,_r select 1]}forEach[" + lst + "];"
            "diag_log 'HMTCFG_FIN';")         # le jeu coupe le dernier caractere de -init ( vu le 02/10 )


def _lire_tableau_sqf(s):
    """[ "a","b" ] tel que format %1 l ecrit -> liste python ( chaines et nombres, tableaux imbriques )."""
    s = s.strip()
    if not s.startswith("["): return None
    if '""' in s: s = s.replace('""', '"')          # diag_log double les guillemets d une chaine
    try:
        return json.loads(s)
    except ValueError:
        return None


def lire_rpt(chemin):
    txt = open(chemin, encoding="latin-1", errors="replace").read()
    lignes = {}
    for m in re.finditer(r'"?HMTCFG\|(\d+)\|([ntac])\|(true|false)\|(.*?)"?\s*$', txt, re.M):
        lignes[int(m.group(1))] = (m.group(2), m.group(3) == "true", m.group(4))
    fin = "HMTCFG_FIN" in txt
    mods = set()
    for m in re.finditer(r"^\s*[0-9:]+\s+.+?\|\s*(\S+)\s*\|\s*(true|false)\s*\|\s*(true|false)\s*\|", txt, re.M):
        if m.group(1) != "modDir": mods.add(m.group(1).lower())
    return lignes, fin, mods


def _egal_nombre(a, b): return abs(a - b) <= max(1e-6, 1e-5 * abs(b))


def juger(rpt):
    lignes, fin, mods = lire_rpt(rpt)
    cat = CF.lire_ensemble(CF.pbos_du_jeu(JEU), journal=lambda s: print("  lecture jeu :", s, flush=True))
    R = cat.racine
    res = []; fausses = 0; herite = 0; absents_jeu = 0
    for i, (g, ch) in enumerate(SONDES):
        jeu = lignes.get(i)
        v, defn = CF.chemin(R, *ch)
        sonde_c, _ = CF.chemin(R, *ch[:-1])
        if g == "n":
            ex = CF.est_nombre(v); lu = float(v) if ex else 0.0
        elif g == "t":
            ex = isinstance(v, str); lu = v if ex else ""
        elif g == "a":
            ex = isinstance(v, list); lu = v if ex else []
        else:
            ex = isinstance(v, CF.Classe) and v.base is not None; lu = v.nom if ex else ""
        if jeu is None:
            ok = False; att = None
        else:
            gj, exj, valj = jeu
            absents_jeu += not exj
            if exj != ex: ok = False
            elif not ex: ok = True
            elif g == "n": ok = _egal_nombre(lu, float(valj))
            elif g == "t": ok = lu == valj
            elif g == "a":
                t = _lire_tableau_sqf(valj)
                norm = lambda L: [x.lower() if isinstance(x, str) else (round(x, 4) if isinstance(x, float) else x) for x in L]
                ok = t is not None and norm(t) == norm(lu)
            else: ok = lu.lower() == valj.lower()
            att = [exj, valj]
        par_heritage = bool(ex and g in "nta" and defn is not None and defn is not sonde_c)
        herite += par_heritage; fausses += not ok
        res.append({"i": i, "genre": g, "chemin": " >> ".join(ch), "jeu": att, "lecteur": [ex, lu if g != "a" else lu[:20]],
                    "ok": ok, "par_heritage": par_heritage, "defini_dans": None if defn is None else defn.nom})
        print(f"  {'OK ' if ok else 'FAUX'} {i:3d} {g} {' >> '.join(ch):62s} jeu {str(att)[:46]:46s} lecteur "
              f"{str([ex, lu])[:46]}{'  (herite)' if par_heritage else ''}", flush=True)
    n = len(SONDES)
    presentes = sum(1 for i in range(n) if i in lignes)
    autres_mods = sorted(mods - MODS_PAR_DEFAUT)
    I1 = presentes == n and fin
    I2 = not autres_mods
    P = n >= 60 and herite >= 10 and absents_jeu >= 5
    if JEU_COURANT in ("r7", "r8"): P = P and n >= 120 and herite >= 30   # R7, R8 : criteres ecrits le 02/10 avant la mesure
    R6 = fausses == 0
    print(f"instrument : {presentes}/{n} lignes, fin {'vue' if fin else 'ABSENTE'} : {'OUI' if I1 else 'NON'}")
    print(f"instrument : mods du journal {sorted(mods)} ; hors defaut {autres_mods} : {'OUI' if I2 else 'NON'}")
    print(f"puissance : {n} sondes, {herite} par heritage, {absents_jeu} absentes dans le jeu : {'OUI' if P else 'NON'}")
    print(f"R6 : {n - fausses}/{n} justes : {'OUI' if R6 else 'NON'}")
    verdict = "FRANCHIE" if (I1 and I2 and P and R6) else "REFUSEE"
    json.dump({"verdict": verdict, "R6": R6, "instrument": [I1, I2], "puissance": P, "sondes": res,
               "mods": sorted(mods), "rpt": rpt}, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE DU LECTEUR ( releve neuf ) : {verdict}")
    print("FIN_PORTE_RELEVE", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    # python -m guerre.arsenal.releve_jeu sqf|juger [rpt] [r6|r7]
    jeu = sys.argv[-1] if sys.argv[-1] in JEUX else "r6"
    SONDES = JEUX[jeu](); JEU_COURANT = jeu
    if jeu != "r6": SORTIE = SORTIE.replace(".json", f"_{jeu}.json")
    if sys.argv[1] == "sqf":
        print(sqf())
    else:
        sys.exit(juger(sys.argv[2]))
