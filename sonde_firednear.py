#!/usr/bin/env python3
"""sonde_firednear — le canal FROLEMENT existe-t-il vraiment sur Arma ?

Tout SIROCCO repose sur un pari : qu'un agent puisse savoir qu'on le VISE avant d'avoir
paye. Cote sandbox on peut toujours l'inventer. Cote Arma, ca tient a un evenement moteur,
`FiredNear`, que ton pont n'a jamais utilise (verifie : il n'apparait nulle part dans le repo,
qui n'emploie que Fired, Hit, HandleDamage et Suppressed).

Cette sonde repond a cinq questions, et rien d'autre. Elle ne mesure aucune tactique.

  Q1  l'evenement remonte-t-il jusqu'au pont ?
  Q2  a quelle DISTANCE se declenche-t-il ? (la constante moteur est reputee ~69 m, jamais
      verifiee ici — si elle est courte, le canal ne sert qu'au contact rapproche)
  Q3  donne-t-il le TIREUR et la distance, ou juste "quelque chose a tire" ?
  Q4  se declenche-t-il aussi quand l'unite tire ELLE-MEME ? (a filtrer, sinon chaque agent
      s'auto-alarme en tirant)
  Q5  quel DEBIT sous rafale ? (si le pont sature a 80 agents, le canal est mort en live)

Rien n'est branche. Aucun entrainement, aucun env. On cree quelques unites, on tire, on
compte, on nettoie.

    python sonde_firednear.py            # theatre par defaut : altis
    python sonde_firednear.py stratis
"""
import sys
import time

sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")

from native_bridge import NativeBridge          # noqa: E402
import theatre                                  # noqa: E402

Q = chr(34); P = chr(37)                        # guillemets/pourcent : le pont parse mal l'inline
DISTANCES = [5, 15, 30, 45, 60, 75, 90, 120]    # m — on veut la marche d'escalier, pas un oui/non
BASE = [23000, 17400, 0]                        # zone vide, loin de tout


def sqf(s):
    """Remplace ' par des guillemets doubles pour ne pas se battre avec le shell/SQF."""
    return s.replace("'", Q)


def main(nom_theatre="altis"):
    T = theatre.use(nom_theatre)
    b = NativeBridge(port=T.PORT)
    try:
        print("=== sonde FiredNear — theatre %s, port %d ===" % (nom_theatre, T.PORT), flush=True)

        # --- Q0 : le pont parle-t-il ? (sinon tout le reste est du bruit) ---
        r = b.query(sqf("(format ['PING %1', round diag_tickTime]) call HMT_EMIT;"), r"PING (\d+)",
                    want=1, timeout=8)
        if not r:
            print("  pont MUET — rien d'autre n'a de sens. (zombie ? relancer le serveur)")
            return 1
        print("  pont OK", flush=True)

        # --- mise en place : 1 tireur + N cibles alignees, TOUTES du meme camp, IA coupee ---
        # meme camp = pas de combat parasite. IA coupee = personne ne bouge ni ne riposte.
        # On mesure la PORTEE de l'evenement, pas un duel.
        pose = ["if (!isNil 'HMT_FN' ) then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_FN };",
                "HMT_FN = []; HMT_FN_D = []; HMT_FN_EV = [];",
                "HMT_G = createGroup west;",
                "HMT_TIR = HMT_G createUnit ['B_Soldier_F', %s, [], 0, 'NONE'];" % str(BASE),
                "HMT_TIR setPosATL %s; HMT_TIR setDir 0;" % str(BASE),
                "{ HMT_TIR disableAI _x } forEach ['MOVE','AUTOTARGET','TARGET','FSM','SUPPRESSION'];",
                "HMT_FN pushBack HMT_TIR;"]
        for i, d in enumerate(DISTANCES):
            p = "[%d, %d, 0]" % (BASE[0] + d, BASE[1])
            pose += [
                "private _u%d = HMT_G createUnit ['B_Soldier_F', %s, [], 0, 'NONE'];" % (i, p),
                "_u%d setPosATL %s;" % (i, p),
                "{ _u%d disableAI _x } forEach ['MOVE','AUTOTARGET','TARGET','FSM','SUPPRESSION'];" % i,
                "HMT_FN pushBack _u%d; HMT_FN_D pushBack %d;" % (i, d),
                # L'EVENEMENT. _this = [unit, firer, distance, weapon, muzzle, mode, ammo, gunner]
                "_u%d addEventHandler ['FiredNear', {" % i,
                "  params ['_u','_firer','_dist','_w','_m','_mo','_ammo'];",
                "  private _i = HMT_FN_D select ((HMT_FN find _u) - 1);",
                "  private _soi = if (_firer isEqualTo _u) then {1} else {0};",
                "  HMT_FN_EV pushBack [_i, round _dist, _soi];",
                "  (format ['FN %1 %2 %3 %4', _i, round _dist, _soi, _ammo]) call HMT_EMIT;",
                "}];"]
        b.send(sqf(" ".join(pose)), wait=True, timeout=20)
        time.sleep(2.0)
        r = b.query(sqf("(format ['NB %1', count HMT_FN]) call HMT_EMIT;"), r"NB (\d+)", want=1, timeout=8)
        print("  unites en place : %s (attendu %d)"
              % (r[-1].group(1) if r else "?", len(DISTANCES) + 1), flush=True)

        # --- Q1..Q4 : un tir, on ecoute qui s'alarme ---
        print("\n  -- un tir unique --", flush=True)
        b.send(sqf("HMT_FN_EV = []; HMT_TIR setDir 0; "
                   "HMT_TIR forceWeaponFire [currentMuzzle HMT_TIR, 'Single'];"), wait=True, timeout=10)
        time.sleep(1.5)
        ev = b.query(sqf("{ (format ['FNR %1 %2 %3', _x select 0, _x select 1, _x select 2]) call HMT_EMIT "
                         "} forEach HMT_FN_EV; (format ['FNTOT %1', count HMT_FN_EV]) call HMT_EMIT;"),
                     r"FNR (\d+) (\d+) (\d+)", timeout=10)
        vus = sorted({int(m.group(1)) for m in ev})
        soi = any(int(m.group(3)) == 1 for m in ev)
        print("  Q1  l'evenement remonte           : %s" % ("OUI (%d)" % len(ev) if ev else "NON"))
        print("  Q2  distances alertees (m)        : %s" % (vus if vus else "aucune"))
        print("      -> portee de declenchement    : %s"
              % ("~%d m" % max(vus) if vus else "nulle — le canal FROLEMENT n'existe pas ici"))
        print("  Q3  distance fournie par l'EH     : %s"
              % ("OUI" if ev else "non observable"))
        print("  Q4  se declenche sur son PROPRE tir : %s (a filtrer cote pont)"
              % ("OUI" if soi else "non"))

        # --- Q5 : debit sous rafale ---
        print("\n  -- rafale : 20 tirs --", flush=True)
        b.send(sqf("HMT_FN_EV = []; HMT_CNT = 0; "
                   "[] spawn { for '_i' from 1 to 20 do { "
                   "HMT_TIR forceWeaponFire [currentMuzzle HMT_TIR, 'Single']; sleep 0.15; } };"),
               wait=True, timeout=10)
        t0 = time.time(); time.sleep(6.0)
        r = b.query(sqf("(format ['TOT %1', count HMT_FN_EV]) call HMT_EMIT;"), r"TOT (\d+)",
                    want=1, timeout=10)
        n = int(r[-1].group(1)) if r else 0
        att = 20 * len(vus) if vus else 0
        print("  Q5  evenements recus              : %d en %.1f s (attendu ~%d)"
              % (n, time.time() - t0, att))
        print("      taux de perte                 : %s"
              % ("%.0f%%" % (100 * (1 - n / att)) if att else "n/a"))

        # --- verdict, sans complaisance ---
        print("\n  === ce que ca decide ===")
        if not vus:
            print("  FiredNear ne remonte pas : le canal FROLEMENT n'est pas gratuit sur Arma.")
            print("  Repli a evaluer : deriver le frolement du 'Fired' des ennemis + une regle de")
            print("  distance/arc cote pont. Plus cher, moins fidele, mais faisable.")
        else:
            print("  Le canal FROLEMENT existe jusqu'a ~%d m, avec la distance et le tireur." % max(vus))
            print("  C'est la portee utile de la brique B1 en live. Au-dela, il faudra le BRUIT.")
        return 0
    finally:
        try:
            b.send(sqf("if (!isNil 'HMT_FN') then { { if (!isNull _x) then {deleteVehicle _x} } forEach HMT_FN };"
                       "if (!isNil 'HMT_G') then { deleteGroup HMT_G };"), wait=False)
        except Exception:
            pass
        b.close()          # le pont ne parle qu'a UN client : ne jamais partir sans fermer


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "altis"))
