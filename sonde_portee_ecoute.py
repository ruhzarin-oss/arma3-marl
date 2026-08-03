#!/usr/bin/env python3
"""sonde_portee_ecoute — A QUELLE DISTANCE UN TIR SE FAIT-IL REMARQUER ?

`sirocco_ouie` refuse de demarrer sans sa portee d'ecoute. C'est LE nombre qui decide si
l'oreille couvre les 170 m ou le probleme se joue : l'agent contourne a 132 m quand le bon
soldat le fait a 184 m, parce que rien ne lui dit qu'il paie deja en arrivant.

METHODE — A/B, parce qu'on ne peut pas isoler le son a coup sur.
Un ecoutant peut voir son tireur ; on ne saurait pas dire ce qui l'a alerte. Alors on
compare DEUX BRAS identiques a une chose pres :
    bras SILENCE  le tireur se tait
    bras TIR      le meme tireur tire
La DIFFERENCE de connaissance est ce que le coup a apporte. C'est tout ce qu'on pretend
mesurer : la contribution du TIR a la detection — son et lueur confondus, on ne les separe
pas ici et on ne fera pas semblant.

`knowsAbout` va de 0 (rien) a 4 (identifie). On releve avant, puis apres.
Les cellules sont ecartees de 3 km : aucune ne doit entendre celle d'a cote.
"""
import sys
import time

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
DISTANCES = [100, 200, 350, 500, 800, 1200]
ZX, ZY = 20000, 17000
DUREE = 30


def _fermer(b):
    try:
        b.close()
    except Exception:
        pass


def poser(b):
    """une cellule par distance : un tireur east, un ecoutant west a `d` metres au nord"""
    c = ["if (!isNil " + Q + "HMT_E" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_E }; "
         "HMT_E = []; HMT_TIR = []; HMT_ECO = []; "
         "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]
    for i, d in enumerate(DISTANCES):
        K = str(i)
        x = ZX + i * 3000
        T = "[" + str(x) + "," + str(ZY) + ",0]"
        E = "[" + str(x) + "," + str(ZY + d) + ",0]"
        c.append(
            "private _gt" + K + " = createGroup east; "
            "private _t" + K + " = _gt" + K + " createUnit [" + Q + "O_Soldier_F" + Q + ", " + T + ", [], 0, " + Q + "NONE" + Q + "]; "
            "_t" + K + " setPosATL " + T + "; _t" + K + " allowDamage false; "
            "_t" + K + " disableAI " + Q + "PATH" + Q + "; _t" + K + " setUnitPos " + Q + "UP" + Q + "; "
            "_t" + K + " setVehicleAmmo 1; _t" + K + " setDir 0; "
            "private _ge" + K + " = createGroup west; "
            "private _e" + K + " = _ge" + K + " createUnit [" + Q + "B_Soldier_F" + Q + ", " + E + ", [], 0, " + Q + "NONE" + Q + "]; "
            "_e" + K + " setPosATL " + E + "; _e" + K + " allowDamage false; "
            "_e" + K + " disableAI " + Q + "PATH" + Q + "; _e" + K + " setBehaviour " + Q + "AWARE" + Q + "; "
            "_e" + K + " setDir 180; "
            "HMT_E pushBack _t" + K + "; HMT_E pushBack _e" + K + "; "
            "HMT_TIR pushBack _t" + K + "; HMT_ECO pushBack _e" + K + "; ")
    c.append("(format [" + Q + "PRET " + P + "1" + Q + ", count HMT_ECO]) call HMT_EMIT;")
    return b.query("".join(c), r"PRET (\d+)", want=1, timeout=90)


def savoir(b):
    """ce que chaque ecoutant sait de SON tireur, x100 pour rester en entiers"""
    q = ("private _o = " + Q + Q + "; "
         "{ _o = _o + format [" + Q + P + "1," + Q + ", round (100 * (_x knowsAbout (HMT_TIR select _forEachIndex)))] } "
         "forEach HMT_ECO; "
         "(format [" + Q + "K " + P + "1" + Q + ", _o]) call HMT_EMIT;")
    r = b.query(q, r"K ([\d,]*)", want=1, timeout=25)
    if not r:
        return None
    return [int(x) / 100.0 for x in r[-1].group(1).rstrip(",").split(",") if x.strip().isdigit()]


def bras(b, tirer):
    if not poser(b):
        return None
    time.sleep(4)
    avant = savoir(b)
    n = 0
    while n < DUREE:
        if tirer:
            b.send("{ _x setVehicleAmmo 1; _x forceWeaponFire [currentMuzzle _x, currentWeaponMode _x] } forEach HMT_TIR;",
                   wait=False)
        time.sleep(2)
        n += 2
    apres = savoir(b)
    b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_E; HMT_E = []; "
           "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    time.sleep(2)
    return avant, apres


def main(nom="altis"):
    T = theatre.use(nom)
    b = NativeBridge(port=T.PORT)
    print("=== portee d'ecoute — theatre %s ===" % nom, flush=True)
    print("    A/B : meme dispositif, le tireur tire ou se tait. La difference EST le tir.", flush=True)
    if not b.query("(format [" + Q + "P " + P + "1" + Q + ", round diag_tickTime]) call HMT_EMIT;",
                   r"P (\d+)", want=1, timeout=20):
        print("  pont MUET")
        _fermer(b)
        return
    print("  pont OK | %d distances | %d s par bras" % (len(DISTANCES), DUREE), flush=True)

    print("", flush=True)
    print("  -- bras SILENCE --", flush=True)
    sil = bras(b, False)
    print("     %s" % ("releve" if sil else "ECHEC"), flush=True)
    time.sleep(3)
    print("  -- bras TIR --", flush=True)
    tir = bras(b, True)
    print("     %s" % ("releve" if tir else "ECHEC"), flush=True)
    _fermer(b)
    if not sil or not tir:
        return

    print("", flush=True)
    print("  %-10s %12s %12s %14s" % ("distance", "silence", "tir", "apport du tir"), flush=True)
    portee = None
    for i, d in enumerate(DISTANCES):
        s = sil[1][i] if i < len(sil[1]) else float("nan")
        t = tir[1][i] if i < len(tir[1]) else float("nan")
        delta = t - s
        marque = ""
        if delta >= 0.05:
            marque = "  <-- entendu"
            portee = d
        print("  %7d m %12.2f %12.2f %14.2f%s" % (d, s, t, delta, marque), flush=True)

    print("", flush=True)
    print("  === ce que ca decide ===", flush=True)
    if portee is None:
        print("  Aucun apport du tir, a aucune distance. Soit l'IA d'Arma n'entend pas, soit", flush=True)
        print("  knowsAbout ne le reflete pas. Dans les deux cas la portee ne se mesure PAS", flush=True)
        print("  ainsi — il faudra la choisir explicitement, et le dire.", flush=True)
    else:
        print("  Le tir se fait remarquer jusqu'a %d m." % portee, flush=True)
        if portee >= 170:
            print("  C'est AU-DELA des 170 m ou se joue le virage : l'oreille peut apprendre a", flush=True)
            print("  l'agent qu'il paie deja en arrivant.  -> portee_m = %d" % portee, flush=True)
        else:
            print("  C'est EN DECA des 170 m. L'oreille ne resoudra pas le virage tardif ;", flush=True)
            print("  elle servira au contact, comme le frolement.", flush=True)
    print("SONDE_PORTEE_DONE", flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "altis")
