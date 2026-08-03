#!/usr/bin/env python3
"""ON REPART DU BANC QUI TIRE, ET ON VA VERS LA SELECTION LIBRE, UN CRAN A LA FOIS.

Cinq tentatives ont echoue a mesurer « combien d'hommes un soldat engage-t-il en 3,28 s »,
et toutes les cinq etaient des DEVINETTES : munitions, autotarget, ordres, camp observe.
Le matin meme, la bissection avait resolu en vingt minutes un blocage de deux jours — en
partant de ce qui SURVIT et en ajoutant une piece a la fois. Je n'ai pas applique ma propre
lecon. On la reapplique ici.

Le point de depart est la configuration du banc de suppression, la seule dont on sache
qu'elle tire : `AUTOTARGET` DESACTIVE, plus `reveal` + `doTarget` + `doFire` repetes toutes
les 4 s. Elle a un defaut fatal pour notre question : **elle impose la cible**. On s'en
eloigne donc d'un cran a la fois.

  cran 0  la config du banc, telle quelle                   -> temoin, DOIT tirer
  cran 1  + AUTOTARGET reactive                             (le reste identique)
  cran 2  + ordres toutes les 10 s au lieu de 4              (on relache la laisse)
  cran 3  + une seule impulsion au depart, puis plus rien    (selection entierement libre)

Le premier cran qui eteint le feu est la reponse. Et tout cran qui tire ENCORE donne, lui,
le chiffre cherche : on compte a chaque tir la cible que l'unite a choisie elle-meme
(capteur `HitPart` sur les cibles : chaque impact donne victime+tireur ; `currentTarget`
n EXISTE PAS dans ce build, mesure du 2026-07-28), et on releve le nombre de cibles
DIFFERENTES par tireur et par fenetre de 3,28 s.

Placement en UNE requete, comme le banc de suppression : c'est ce qui marche. Le decoupage
en lots avait casse les variables `private`, qui ne survivent pas d'un envoi a l'autre.
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
PAS = 3.28

NOMS = {0: "config du banc (temoin)", 1: "+ AUTOTARGET reactive",
        2: "+ ordres toutes les 10 s", 3: "+ une seule impulsion"}

ap = argparse.ArgumentParser()
ap.add_argument("--cran", type=int, required=True, choices=[0, 1, 2, 3])
ap.add_argument("--N", type=int, default=4, help="duellistes de chaque cote")
ap.add_argument("--dist", type=int, default=100)
ap.add_argument("--fenetres", type=int, default=12)
ap.add_argument("--skill", type=float, default=0.5)
ap.add_argument("--theatre", default="altis")
a = ap.parse_args()


def fermer(b):
    try:
        b.close()
    except Exception:
        pass


def main():
    b = NativeBridge(port=theatre.use(a.theatre).PORT)
    cran = a.cran
    periode = 10.0 if cran >= 2 else 4.0
    print("=== CRAN %d : %s ===" % (cran, NOMS[cran]), flush=True)
    print("    %d vs %d a %d m | AUTOTARGET %s | ordres %s"
          % (a.N, a.N, a.dist,
             "ACTIF" if cran >= 1 else "coupe",
             "une seule fois" if cran >= 3 else ("toutes les %.0f s" % periode)), flush=True)

    ok = False
    for e in range(12):
        if b.query("(format [" + Q + "P " + P + "1" + Q + ", round diag_tickTime]) call HMT_EMIT;",
                   r"P (\d+)", want=1, timeout=20):
            ok = True
            break
        time.sleep(10)
    if not ok:
        print("  mission muette apres 12 essais"); fermer(b); sys.exit(2)

    cel = json.load(open(LEV + "/cellules_altis.json"))["serie"]
    x, y = cel[0][0], cel[0][1]

    # --- placement en UNE requete, exactement comme le banc de suppression ---
    c = ["if (!isNil " + Q + "HMT_BSX" + Q + ") then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_BSX }; "
         "HMT_BSX = []; HMT_BSD = []; HMT_BSC = []; HMT_BSS = []; HMT_BSG = []; "
         "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups; "]
    for k in range(a.N):
        K = str(k)
        dx = (k - (a.N - 1) / 2.0) * 25
        D = "[" + ("%.0f" % (x + dx)) + "," + str(y) + ",0]"
        C = "[" + ("%.0f" % (x + dx)) + "," + str(y + a.dist) + ",0]"
        c.append(
            "HMT_BSS pushBack 0; HMT_BSG pushBack []; "
            # LE DUELLISTE OBSERVE — reglages identiques a ceux du banc de suppression
            "private _g" + K + " = createGroup east; "
            "private _d" + K + " = _g" + K + " createUnit [" + Q + "O_Soldier_F" + Q + ", " + D + ", [], 0, " + Q + "NONE" + Q + "]; "
            "_d" + K + " setPosATL " + D + "; _d" + K + " setSkill " + ("%.2f" % a.skill) + "; "
            "_d" + K + " setUnitPos " + Q + "UP" + Q + "; _d" + K + " setBehaviour " + Q + "COMBAT" + Q + "; "
            "_d" + K + " setCombatMode " + Q + "RED" + Q + "; _d" + K + " disableAI " + Q + "PATH" + Q + "; "
            + ("" if cran >= 1 else "_d" + K + " disableAI " + Q + "AUTOTARGET" + Q + "; ")
            + "_d" + K + " allowDamage false; _d" + K + " setVehicleAmmo 1; "
            # le capteur : le tir ET la cible QUE L'UNITE a choisie
            "_d" + K + " addEventHandler [" + Q + "Fired" + Q + ", { "
            "  HMT_BSS set [" + K + ", (HMT_BSS select " + K + ") + 1]; "
            "}]; "
            # SA CIBLE, invulnerable et qui riposte : le duel doit durer
            "private _h" + K + " = createGroup west; "
            "private _c" + K + " = _h" + K + " createUnit [" + Q + "B_Soldier_F" + Q + ", " + C + ", [], 0, " + Q + "NONE" + Q + "]; "
            "_c" + K + " setPosATL " + C + "; _c" + K + " setSkill " + ("%.2f" % a.skill) + "; "
            "_c" + K + " setUnitPos " + Q + "UP" + Q + "; _c" + K + " setBehaviour " + Q + "COMBAT" + Q + "; "
            "_c" + K + " setCombatMode " + Q + "RED" + Q + "; _c" + K + " disableAI " + Q + "PATH" + Q + "; "
            "_c" + K + " disableAI " + Q + "AUTOTARGET" + Q + "; "
            "_c" + K + " allowDamage false; _c" + K + " setVehicleAmmo 1; "
            # LE CAPTEUR REEL : qui a touche qui. currentTarget n existe pas ici (MESURE 2026-07-28),
            # assignedTarget ne rend que la cible IMPOSEE -> on lit la selection dans les impacts.
            "_c" + K + " addEventHandler [" + Q + "HitPart" + Q + ", { "
            "  private _p = _this select 0; "
            "  private _v = _p select 0; private _s = _p select 1; "
            "  private _si = HMT_BSD find _s; private _vi = HMT_BSC find _v; "
            "  if (_si >= 0 && _vi >= 0) then { "
            "    if (!(_vi in (HMT_BSG select _si))) then { (HMT_BSG select _si) pushBack _vi }; "
            "  }; "
            "}]; "
            "HMT_BSX pushBack _d" + K + "; HMT_BSX pushBack _c" + K + "; "
            "HMT_BSD pushBack _d" + K + "; HMT_BSC pushBack _c" + K + "; ")
    c.append("(format [" + Q + "PRET " + P + "1 " + P + "2" + Q + ", count HMT_BSD, count HMT_BSC]) call HMT_EMIT;")
    r = b.query("".join(c), r"PRET (\d+) (\d+)", want=1, timeout=120)
    if not r:
        print("  MORT DES LA POSE"); fermer(b)
        print("VERDICT cran %d : MORT (pose)" % cran, flush=True)
        sys.exit(1)
    print("  poses : %s duellistes, %s cibles" % (r[-1].group(1), r[-1].group(2)), flush=True)

    # --- l'ordre : celui du banc de suppression, mot pour mot ---
    ordre = ("{ private _c = HMT_BSC select _forEachIndex; _x reveal [_c, 4]; _x doTarget _c; "
             "_x doFire _c; } forEach HMT_BSD; "
             "{ private _d = HMT_BSD select _forEachIndex; _x reveal [_d, 4]; _x doTarget _d; "
             "_x doFire _d; } forEach HMT_BSC;")
    # tout le monde voit tout le monde : sans ca, la selection n'a pas de choix a faire
    b.send("{ private _u = _x; { _u reveal [_x, 4] } forEach HMT_BSC; } forEach HMT_BSD; "
           "{ private _u = _x; { _u reveal [_x, 4] } forEach HMT_BSD; } forEach HMT_BSC;", wait=False)
    time.sleep(2)
    b.send(ordre, wait=False)
    time.sleep(6)

    n = 0
    for e in range(4):
        t = b.query("private _o = 0; { _o = _o + _x } forEach HMT_BSS; "
                    "(format [" + Q + "TOT " + P + "1" + Q + ", _o]) call HMT_EMIT;",
                    r"TOT (\d+)", want=1, timeout=20)
        n = int(t[-1].group(1)) if t else 0
        if n > 0:
            break
        print("  canari : 0 tir (essai %d)" % (e + 1), flush=True)
        b.send(ordre, wait=False)
        time.sleep(6)
    if n == 0:
        print("", flush=True)
        print("  >>> AUCUN TIR. Capteur non prouve : ON NE CONCLUT RIEN.", flush=True)
        fermer(b)
        print("VERDICT cran %d : MUET  <-- %s eteint le feu" % (cran, NOMS[cran]), flush=True)
        sys.exit(1)
    print("  canari : %d tir(s) -> capteur PROUVE" % n, flush=True)

    lire = ("private _s = " + Q + Q + "; { _s = _s + format [" + Q + P + "1," + Q + ", _x] } forEach HMT_BSS; "
            "private _g = " + Q + Q + "; { _g = _g + format [" + Q + P + "1," + Q + ", count _x] } forEach HMT_BSG; "
            "(format [" + Q + "W " + P + "1 " + P + "2" + Q + ", _s, _g]) call HMT_EMIT; "
            "{ HMT_BSS set [_forEachIndex, 0] } forEach HMT_BSS; "
            "{ HMT_BSG set [_forEachIndex, []] } forEach HMT_BSG;")

    print("", flush=True)
    print("  fenetre   balles/tireur   hommes differents/tireur   tireurs actifs", flush=True)
    fen = []
    muet = 0
    depuis = 0.0
    for w in range(a.fenetres):
        time.sleep(PAS)
        depuis += PAS
        if cran < 3 and depuis >= periode:      # cran 3 : plus AUCUN ordre apres l'impulsion
            b.send(ordre, wait=False)
            depuis = 0.0
        rr = b.query(lire, r"W ([\d,]+) ([\d,]+)", want=1, timeout=20)
        if not rr:
            muet += 1
            print("    %2d      pont MUET" % (w + 1), flush=True)
            if muet >= 3:
                break
            continue
        muet = 0
        sh = [int(v) for v in rr[-1].group(1).rstrip(",").split(",") if v.strip().isdigit()]
        tg = [int(v) for v in rr[-1].group(2).rstrip(",").split(",") if v.strip().isdigit()]
        act = [i for i in range(len(sh)) if sh[i] > 0]
        if not act:
            print("    %2d          aucun tireur actif" % (w + 1), flush=True)
            continue
        bal = sum(sh) / float(len(act))
        hom = sum(tg[i] for i in act) / float(len(act))
        print("    %2d          %6.2f                 %6.2f                %d/%d"
              % (w + 1, bal, hom, len(act), len(sh)), flush=True)
        if w > 0:
            fen.append({"balles": sh, "cibles": tg, "actifs": len(act)})

    b.send("{ if (!isNull _x) then {deleteVehicle _x} } forEach HMT_BSX; HMT_BSX = []; "
           "{ if (count units _x == 0) then { deleteGroup _x } } forEach allGroups;", wait=False)
    time.sleep(2)
    fermer(b)

    if not fen:
        print("", flush=True)
        print("VERDICT cran %d : TIRE mais aucune fenetre exploitable" % cran, flush=True)
        sys.exit(1)
    ta = sum(f["actifs"] for f in fen)
    bal_moy = sum(sum(f["balles"]) for f in fen) / float(ta)
    hom_moy = sum(sum(f["cibles"][i] for i in range(len(f["cibles"])) if f["balles"][i] > 0)
                  for f in fen) / float(ta)
    print("", flush=True)
    print("VERDICT cran %d : TIRE" % cran, flush=True)
    print("  balles par tireur actif et par pas : %.2f   (sandbox : tir_par_pas = 1,15)" % bal_moy, flush=True)
    print("  hommes DIFFERENTS par tireur       : %.2f   (sandbox actuel : tous, soit %d)"
          % (hom_moy, a.N), flush=True)
    if cran >= 1:
        print("  (AUTOTARGET actif : la cible est CHOISIE par l'unite, pas par moi)", flush=True)
    else:
        print("  (cran 0 : la cible est IMPOSEE — ce chiffre est un plancher, pas une mesure)", flush=True)
    json.dump({"cran": cran, "balles_par_tireur_par_pas": bal_moy,
               "hommes_par_tireur_par_pas": hom_moy, "N": a.N, "dist": a.dist,
               "pas_s": PAS, "autotarget": cran >= 1, "periode_ordre": (None if cran >= 3 else periode),
               "fenetres": fen},
              open(LEV + "/bissection_selection_%d.json" % cran, "w"), indent=1)
    print("-> %s/bissection_selection_%d.json" % (LEV, cran), flush=True)
    print("CRAN_DONE", flush=True)


if __name__ == "__main__":
    main()
