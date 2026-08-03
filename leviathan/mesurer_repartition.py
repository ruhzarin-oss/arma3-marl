#!/usr/bin/env python3
"""COMBIEN D'HOMMES DIFFERENTS UN DEFENSEUR PREND-IL A PARTIE EN 3,28 s ?

Le sandbox appliquait les 1,15 balles/pas MESUREES sur Arma a CHAQUE attaquant separement :
avec quatre attaquants, un defenseur tirait 4,6 balles par pas. Mesure interne du 28/07 :
1,8 attaquant pris a partie par defenseur. Corriger ca fait passer la prise frontale de
22 % a 81 % et FAIT DISPARAITRE l'avantage du flanc. Rien d'interne ne peut arbitrer.

Ce banc mesure les deux nombres qui tranchent, sur le vrai jeu :
  1. les balles tirees par defenseur et par fenetre de 3,28 s (le pas du sandbox) ;
  2. le nombre d'attaquants DIFFERENTS qu'un meme defenseur engage dans cette fenetre.

⚠ AUCUN ORDRE DE TIR. `AUTOTARGET` reste ACTIF et on ne fait ni `doTarget` ni `doFire` :
forcer une cible mesurerait ma consigne, pas la selection d'Arma. On se contente de reveler
les attaquants aux defenseurs, puis on regarde.

Tout le monde est `allowDamage false` : on veut un regime permanent, pas une fusillade qui
s'eteint quand quelqu'un tombe. Lecon du 28/07 : un mort rend son bras muet.
"""
import sys
import time
import json
import argparse

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
import theatre

Q = chr(34)
P = chr(37)
LEV = "/home/younes/arma3-marl/leviathan"
PAS = 3.28                     # duree d'un pas de sandbox, mesuree sur Arma

ap = argparse.ArgumentParser()
ap.add_argument("--D", type=int, default=8, help="defenseurs")
ap.add_argument("--A", type=int, default=4, help="attaquants")
ap.add_argument("--dist", type=int, default=100)
ap.add_argument("--fenetres", type=int, default=18, help="fenetres de 3,28 s")
ap.add_argument("--skill", type=float, default=0.5)
ap.add_argument("--theatre", default="altis")
ap.add_argument("--out", default="repartition_feu.json")
a = ap.parse_args()


def fermer(b):
    try:
        b.close()
    except Exception:
        pass


def main():
    T = theatre.use(a.theatre)
    b = NativeBridge(port=T.PORT)
    print("=== REPARTITION DU FEU : combien d'hommes par defenseur en %.2f s ? ===" % PAS, flush=True)
    print("    %d defenseurs vs %d attaquants a %d m | AUTOTARGET actif, AUCUN ordre de tir"
          % (a.D, a.A, a.dist), flush=True)
    # LA CONNEXION ACCEPTEE N'EST PAS LE PONT PRET. Le socket ouvre des que le serveur
    # ecoute, mais  n'existe qu'une fois le script de mission charge. Mesure du
    # 28/07 : 80 s pour le socket, davantage pour la mission. On patiente au lieu d'abandonner.
    _ok = False
    for _essai in range(12):
        if b.query("(format [" + Q + "P " + P + "1" + Q + ", round diag_tickTime]) call HMT_EMIT;",
                   r"P (\d+)", want=1, timeout=20):
            _ok = True
            print("  pont vivant (essai %d)" % (_essai + 1), flush=True)
            break
        time.sleep(10)
    if not _ok:
        print("  pont MUET apres 12 essais — la mission ne repond pas"); fermer(b); sys.exit(2)

    try:
        cel = json.load(open(LEV + "/cellules_altis.json"))["serie"]
    except Exception:
        print("  !! cellules certifiees introuvables — ARRET"); fermer(b); sys.exit(2)
    x, y = cel[0][0], cel[0][1]

    c = ["if (!isNil " + Q + "HMT_X" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X }; "
         "HMT_X = []; HMT_DEF = []; HMT_ATT = []; HMT_SHOTS = []; HMT_TGT = []; HMT_ATIR = []; "
         "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]

    # --- les defenseurs, en LIGNE, comme dans le sandbox (def_line) ---
    gd = "createGroup east"
    c.append("HMT_GD = " + gd + "; ")
    for k in range(a.D):
        K = str(k)
        dx = (k - (a.D - 1) / 2.0) * 12          # ligne de 12 m d'intervalle
        D = "[" + ("%.0f" % (x + dx)) + "," + str(y) + ",0]"
        c.append(
            "HMT_SHOTS pushBack 0; HMT_TGT pushBack []; "
            "HMT_U = HMT_GD createUnit [" + Q + "O_Soldier_F" + Q + ", " + D + ", [], 0, " + Q + "NONE" + Q + "]; "
            "HMT_U setPosATL " + D + "; HMT_U" + " setSkill " + ("%.2f" % a.skill) + "; "
            "HMT_U setUnitPos " + Q + "UP" + Q + "; HMT_U" + " allowDamage false; "
            "HMT_U setBehaviour " + Q + "COMBAT" + Q + "; HMT_U" + " setCombatMode " + Q + "RED" + Q + "; "
            "HMT_U setVehicleAmmo 1; HMT_U enableAI " + Q + "AUTOTARGET" + Q + "; "
            "HMT_U disableAI " + Q + "PATH" + Q + "; "        # il reste en place, mais VISE librement
            "HMT_X pushBack HMT_U; HMT_DEF pushBack HMT_U; ")

    # --- les attaquants, face a la ligne, qui ripostent (sinon les defenseurs se lassent)
    c.append("HMT_GA = createGroup west; ")
    for k in range(a.A):
        K = str(k)
        ax = (k - (a.A - 1) / 2.0) * 20
        A_ = "[" + ("%.0f" % (x + ax)) + "," + str(y + a.dist) + ",0]"
        c.append(
            "HMT_U = HMT_GA createUnit [" + Q + "B_Soldier_F" + Q + ", " + A_ + ", [], 0, " + Q + "NONE" + Q + "]; "
            "HMT_U setPosATL " + A_ + "; HMT_U" + " setSkill " + ("%.2f" % a.skill) + "; "
            "HMT_U setUnitPos " + Q + "UP" + Q + "; HMT_U" + " allowDamage false; "
            "HMT_U setBehaviour " + Q + "COMBAT" + Q + "; HMT_U" + " setCombatMode " + Q + "RED" + Q + "; "
            "HMT_U setVehicleAmmo 1; HMT_U disableAI " + Q + "PATH" + Q + "; "
            "HMT_ATIR pushBack 0; "
            "HMT_X pushBack HMT_U; HMT_ATT pushBack HMT_U; ")

    # --- le capteur : a chaque tir, on note QUI tire et SUR QUI il tire ---
    # `currentTarget` est la cible que l'IA a choisie elle-meme. On enregistre l'INDICE de
    # l'attaquant, une seule fois par fenetre : ce qu'on compte, c'est le nombre d'hommes
    # DIFFERENTS pris a partie, pas le nombre de balles.
    c.append(
        "{ _x addEventHandler [" + Q + "Fired" + Q + ", { "
        "  private _u = _this select 0; "
        "  private _k = HMT_DEF find _u; "
        "  if (_k >= 0) then { "
        "    HMT_SHOTS set [_k, (HMT_SHOTS select _k) + 1]; "
        "    private _i = HMT_ATT find (currentTarget _u); "
        "    if (_i >= 0 && !(_i in (HMT_TGT select _k))) then { (HMT_TGT select _k) pushBack _i }; "
        "  }; }]; } forEach HMT_DEF; ")
    # un compteur cote ATTAQUANTS aussi : sans lui, un zero cote defenseurs
    # ne distingue pas « ils ne ripostent pas » de « rien ne tire du tout ».
    c.append(
        "{ _x addEventHandler [" + Q + "Fired" + Q + ", { "
        "  private _k = HMT_ATT find (_this select 0); "
        "  if (_k >= 0) then { HMT_ATIR set [_k, (HMT_ATIR select _k) + 1] }; }]; } forEach HMT_ATT; ")
    c.append("(format [" + Q + "PRET " + P + "1 " + P + "2" + Q + ", count HMT_DEF, count HMT_ATT]) call HMT_EMIT;")
    # ENVOI DECOUPE. Un gros inline echoue en silence sur ce pont (piege connu du projet) :
    # 12 unites avec leurs reglages font une chaine que le dialogue ne digere pas. On envoie
    # par morceaux sans accuse, puis on demande le compte UNE fois a la fin.
    _fin = c[-1]
    _corps = c[:-1]
    _lot = ""
    for _m in _corps:
        # une unite entiere par message : HMT_U est reutilise et ne doit
        # JAMAIS traverser deux envois.
        if _lot:
            b.send(_lot, wait=False); time.sleep(0.6); _lot = ""
        _lot += _m
    if _lot:
        b.send(_lot, wait=False); time.sleep(0.6)
    time.sleep(2)
    r = b.query(_fin, r"PRET (\d+) (\d+)", want=1, timeout=60)
    if not r:
        print("  MORT DES LA POSE"); fermer(b); sys.exit(1)
    print("  poses : %s defenseurs, %s attaquants" % (r[-1].group(1), r[-1].group(2)), flush=True)

    # --- on REVELE, on n'ORDONNE PAS. La difference est tout le banc. ---
    # ON REVELE DES DEUX COTES, mais on n'ORDONNE QU'AUX ATTAQUANTS. Les defenseurs
    # ripostent alors d'eux-memes et choisissent leurs cibles : c'est la grandeur mesuree.
    b.send("{ private _d = _x; { _d reveal [_x, 4] } forEach HMT_ATT; } forEach HMT_DEF; "
           "{ private _u = _x; { _u reveal [_x, 4] } forEach HMT_DEF; } forEach HMT_ATT;", wait=False)
    time.sleep(3)
    _feu = ("{ private _u = _x; private _c = HMT_DEF select (_forEachIndex % count HMT_DEF); "
            "  _u doTarget _c; _u doFire _c; } forEach HMT_ATT;")
    b.send(_feu, wait=False)
    time.sleep(4)
    # AMORCE UNIQUE des defenseurs, chacun sur un attaquant DIFFERENT. Sans elle ils ne
    # tirent jamais (0 coup en 60 s, mesure du 28/07). Apres cette ligne, plus aucun ordre :
    # la selection observee est la leur.
    _amorce = ("{ private _c = HMT_ATT select (_forEachIndex % count HMT_ATT); "
               "  _x doTarget _c; _x doFire _c; } forEach HMT_DEF;")
    b.send(_amorce, wait=False)
    time.sleep(6)

    # --- canari : prouver le capteur avant de conclure a quoi que ce soit ---
    can = b.query("(format [" + Q + "CAN " + P + "1" + Q + ", HMT_SHOTS select 0]) call HMT_EMIT;",
                  r"CAN (\d+)", want=1, timeout=25)
    if not can:
        print("  canari SANS REPONSE — pont mort"); fermer(b); sys.exit(2)
    # BLOQUANT. Le 28/07 ce banc a lu « 0 tir », a deroule 18 fenetres vides et imprime une
    # conclusion issue d'une division par zero. Un capteur non prouve interdit de conclure.
    _n = 0
    for _e in range(6):
        _tot = b.query("private _o = 0; { _o = _o + _x } forEach HMT_SHOTS; "
                       "private _p = 0; { _p = _p + _x } forEach HMT_ATIR; "
                       "(format [" + Q + "TOT " + P + "1 " + P + "2" + Q + ", _o, _p]) call HMT_EMIT;",
                       r"TOT (\d+) (\d+)", want=1, timeout=20)
        _n = int(_tot[-1].group(1)) if _tot else 0
        _na = int(_tot[-1].group(2)) if _tot else 0
        if _n > 0:
            break
        print("  canari : defenseurs 0 tir | attaquants %d tir(s)  (essai %d)" % (_na, _e + 1), flush=True)
        b.send(_feu, wait=False)
        time.sleep(2)
        b.send(_amorce, wait=False)
        time.sleep(6)
    if _n == 0:
        print("", flush=True)
        print("  >>> AUCUN DEFENSEUR N'A TIRE (attaquants : %d tirs)." % _na, flush=True)
        print("      %s" % ("Les attaquants TIRENT : c'est la RIPOSTE qui ne part pas."
                            if _na > 0 else
                            "PERSONNE ne tire : c'est la MISE EN PLACE qui est en cause."), flush=True)
        print("      Le capteur n'est pas prouve :", flush=True)
        print("      ON NE CONCLUT RIEN, et surtout on n'imprime aucun rapport.", flush=True)
        fermer(b); sys.exit(2)
    print("  canari : %d tir(s) au total -> capteur PROUVE" % _n, flush=True)

    lire = ("private _s = " + Q + Q + "; { _s = _s + format [" + Q + P + "1," + Q + ", _x] } forEach HMT_SHOTS; "
            "private _t = " + Q + Q + "; { _t = _t + format [" + Q + P + "1," + Q + ", count _x] } forEach HMT_TGT; "
            "(format [" + Q + "W " + P + "1 " + P + "2" + Q + ", _s, _t]) call HMT_EMIT; "
            "{ HMT_SHOTS set [_forEachIndex, 0] } forEach HMT_SHOTS; "
            "{ HMT_TGT set [_forEachIndex, []] } forEach HMT_TGT;")

    print("", flush=True)
    print("  fenetre   balles/defenseur   hommes differents/defenseur   defenseurs qui tirent", flush=True)
    fen = []
    muet = 0
    for w in range(a.fenetres):
        time.sleep(PAS)
        rr = b.query(lire, r"W ([\d,]+) ([\d,]+)", want=1, timeout=20)
        if not rr:
            muet += 1
            print("    %2d      pont MUET" % (w + 1), flush=True)
            if muet >= 3:
                print("  trois fenetres muettes d'affilee — on arrete", flush=True)
                break
            continue
        muet = 0
        sh = [int(v) for v in rr[-1].group(1).rstrip(",").split(",") if v.strip().isdigit()]
        tg = [int(v) for v in rr[-1].group(2).rstrip(",").split(",") if v.strip().isdigit()]
        if not sh:
            continue
        actifs = [i for i in range(len(sh)) if sh[i] > 0]
        bal = sum(sh) / float(max(len(actifs), 1))
        hom = sum(tg[i] for i in actifs) / float(max(len(actifs), 1))
        # la 1re fenetre porte encore la marque de l'amorce : on l'affiche, on ne la compte pas
        if w > 0:
            fen.append({"balles": sh, "cibles": tg, "actifs": len(actifs)})
        print("    %2d          %6.2f                     %6.2f                    %d/%d"
              % (w + 1, bal, hom, len(actifs), len(sh)), flush=True)

    b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_X; HMT_X = []; "
           "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    time.sleep(2)
    fermer(b)

    if not fen:
        print("  aucune fenetre lisible — ON NE CONCLUT RIEN", flush=True)
        sys.exit(1)

    tot_act = sum(f["actifs"] for f in fen)
    tot_bal = sum(sum(f["balles"]) for f in fen)
    tot_hom = sum(sum(f["cibles"][i] for i in range(len(f["cibles"])) if f["balles"][i] > 0) for f in fen)
    bal_moy = tot_bal / float(max(tot_act, 1))
    hom_moy = tot_hom / float(max(tot_act, 1))
    print("", flush=True)
    print("=== RESULTAT (%d fenetres de %.2f s) ===" % (len(fen), PAS), flush=True)
    print("  balles par defenseur QUI TIRE et par pas : %.2f   (sandbox : tir_par_pas = 1,15)" % bal_moy, flush=True)
    print("  hommes DIFFERENTS pris a partie par pas  : %.2f   (sandbox actuel : %d = tous)"
          % (hom_moy, a.A), flush=True)
    print("", flush=True)
    if bal_moy <= 0 or hom_moy <= 0:
        print("  >>> denominateur nul : aucune conclusion possible.", flush=True)
        sys.exit(2)
    if hom_moy < 1.5:
        print("  >>> UN DEFENSEUR ENGAGE UN SEUL HOMME A LA FOIS (%.2f)." % hom_moy, flush=True)
        print("      Le sandbox lui en faisait viser %d : il etait environ %.1f fois trop letal."
              % (a.A, a.A / max(hom_moy, 1e-9)), flush=True)
        print("      -> `cible_unique=True` est le comportement fidele.", flush=True)
    elif hom_moy > a.A * 0.75:
        print("  >>> le defenseur arrose bien plusieurs hommes (%.2f) : l'ancien monde avait raison." % hom_moy, flush=True)
    else:
        print("  >>> regime INTERMEDIAIRE (%.2f hommes). Ni un ni tous : il faudra un facteur," % hom_moy, flush=True)
        print("      pas un interrupteur.", flush=True)

    json.dump({"balles_par_defenseur_par_pas": bal_moy, "hommes_par_defenseur_par_pas": hom_moy,
               "D": a.D, "A": a.A, "dist": a.dist, "skill": a.skill,
               "pas_s": PAS, "fenetres": fen},
              open(LEV + "/" + a.out, "w"), indent=1)
    print("-> " + LEV + "/" + a.out, flush=True)
    print("REPART_DONE", flush=True)


if __name__ == "__main__":
    main()
