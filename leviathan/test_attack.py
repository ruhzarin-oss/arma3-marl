"""test_attack — la pression FRAPPE-T-ELLE ce que le score sait mesurer ?

Criteres ecrits AVANT le run (l'audit de la recompense les impose) :
  P1. la menace doit etre VUE : au moins 2 FOB avec des contacts dans le SITREP.
  P2. il doit y avoir des MORTS : >= 8 hommes perdus en 3 min (0.025/homme -> 0.2 de score).
  P3. les CIBLES doivent etre en danger : au moins une cible touchee ou approchee a < 300 m.
Si P2 echoue, aucun ordre ne pourra se distinguer d'un autre : perdre du terrain ne pese que
0.010 par FOB, sous le bruit.
"""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import OfficerState, FOBS

FOB_VISES = [0, 2]          # M1 et M3
N_PAR_FOB = 16
DUREE = int(sys.argv[1]) if len(sys.argv) > 1 else 180

b = NativeBridge(port=5816)
st = OfficerState(bridge=b)


def sitrep(tag):
    r = b.query('call HMT_SITREP;', r'HARMATTAN_SIT (.+)', want=1, timeout=20)
    if not r:
        print("  [%s] SITREP illisible" % tag); return None
    s = st.parse(r[-1].group(1).rstrip('"').strip(), tick=0)
    thr = [(f["name"], f["contacts"]) for f in s["fobs"] if f["contacts"] > 0]
    print("  [%-9s] force %3d | cibles %d/%d | FOB tenus %2d | menaces %s"
          % (tag, s["total_force"], s["targets_intact"], s["targets_total"],
             sum(1 for f in s["fobs"] if f["held"]), thr or "-"))
    return s


try:
    b.send('call compile preprocessFileLineNumbers "pressure_bench.sqf";')
    time.sleep(1.5)

    print("--- reset ---")
    b.send('[] spawn { call HMT_PB_RESET; };')
    b.query('', r'HARMATTAN_PB_RESET (.+)', want=1, timeout=180)
    time.sleep(8)
    s0 = sitrep("depart")

    print("--- attaque sur %s, %d assaillants/FOB ---" % ([FOBS[i][0] for i in FOB_VISES], N_PAR_FOB))
    b.send('[%s, %d, true] spawn HMT_PB_ATTACK;' % (str(FOB_VISES), N_PAR_FOB))
    r = b.query('', r'HARMATTAN_PB_ATTACK (.+)', want=1, timeout=90)
    print("  assaillants crees :", r[-1].group(1).strip().rstrip('"') if r else "AUCUN EMIT")

    t0 = time.time()
    while time.time() - t0 < DUREE:
        time.sleep(45)
        sitrep("t+%02ds" % int(time.time() - t0))

    sN = sitrep("fin")

    print("\n=== VERDICT ===")
    if s0 and sN:
        menaces = sum(1 for f in sN["fobs"] if f["contacts"] > 0)
        morts = max(0, s0["total_force"] - sN["total_force"])
        cibles_perdues = s0["targets_intact"] - sN["targets_intact"]
        print("  P1 FOB menaces vus       : %d      -> %s" % (menaces, "OK" if menaces >= 2 else "ECHEC"))
        print("  P2 hommes perdus         : %d      -> %s" % (morts, "OK" if morts >= 8 else "ECHEC (pression trop faible)"))
        print("  P3 cibles perdues        : %d" % cibles_perdues)
        print("  impact score potentiel   : %.3f (morts) + %.3f (cibles) = %.3f"
              % (morts * 0.025, cibles_perdues * 0.125, morts * 0.025 + cibles_perdues * 0.125))
finally:
    b.close()
