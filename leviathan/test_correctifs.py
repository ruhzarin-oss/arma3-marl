"""test_correctifs — les trois correctifs tiennent-ils ENSEMBLE ?

Criteres ecrits AVANT le run :
  C1 COHORTE : les pertes amies doivent etre lues sur la liste figee, et etre >= 8
               (0.025/homme -> 0.20 de score, quatre fois le seuil de decision 0.05).
  C2 PRESSION : au moins 2 FOB avec des contacts VUS dans le SITREP.
  C3 GEL      : aucune ligne "HARMATTAN_LOG renfort" pendant l'episode.
  C4 PONT     : le pont repond encore a la fin (il etait mort au run precedent).
Si C1 echoue alors que des hommes sont morts, c'est la mesure qui est fausse, pas la pression.
"""
import sys, time, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import OfficerState, FOBS

LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"
FOB_VISES = [7, 9]              # O2 et O4 : des OUTPOSTS (garnison ~19), pas des MAIN (~40)
N_PAR_FOB = 48
DUREE = int(sys.argv[1]) if len(sys.argv) > 1 else 240


def nb_renforts():
    try:
        return int(subprocess.check_output(
            "grep -c 'HARMATTAN_LOG renfort' %s || true" % LOG, shell=True).decode().strip() or 0)
    except Exception:
        return -1


b = NativeBridge(port=5816)
st = OfficerState(bridge=b)


def sitrep(tag):
    r = b.query('call HMT_SITREP;', r'HARMATTAN_SIT (.+)', want=1, timeout=25)
    if not r:
        print("  [%-9s] PONT MUET" % tag); return None
    s = st.parse(r[-1].group(1).rstrip('"').strip(), tick=0)
    thr = [(f["name"], f["contacts"]) for f in s["fobs"] if f["contacts"] > 0]
    print("  [%-9s] force %3d | cibles %d/%d | menaces %s"
          % (tag, s["total_force"], s["targets_intact"], s["targets_total"], thr or "-"))
    return s


try:
    b.send('call compile preprocessFileLineNumbers "pressure_bench.sqf";')
    time.sleep(1.5)

    print("--- reset ---")
    b.send('[] spawn { call HMT_PB_RESET; };')
    b.query('', r'HARMATTAN_PB_RESET (.+)', want=1, timeout=200)
    time.sleep(8)

    print("--- gel du monde vivant ---")
    b.send('HMT_PB_GEL = true;')
    renf0 = nb_renforts()
    print("  HMT_PB_GEL = true (lignes 'renfort' au depart : %d)" % renf0)

    print("--- cohorte figee ---")
    r = b.query('call HMT_PB_COHORTE;', r'HARMATTAN_PB_COHORTE (.+)', want=1, timeout=30)
    print("  cohorte :", r[-1].group(1).strip().rstrip('"') if r else "ECHEC")

    s0 = sitrep("depart")

    print("--- attaque : %s, %d/FOB + 24 sur une cible vitale ---"
          % ([FOBS[i][0] for i in FOB_VISES], N_PAR_FOB))
    b.send('[%s, %d, true] spawn HMT_PB_ATTACK;' % (str(FOB_VISES), N_PAR_FOB))
    r = b.query('', r'HARMATTAN_PB_ATTACK (.+)', want=1, timeout=120)
    print("  assaillants :", r[-1].group(1).strip().rstrip('"') if r else "AUCUN EMIT")

    t0 = time.time()
    while time.time() - t0 < DUREE:
        time.sleep(60)
        sitrep("t+%03ds" % int(time.time() - t0))

    print("--- mesure finale ---")
    r = b.query('call HMT_PB_PERTES;', r'HARMATTAN_PB_PERTES (.+)', want=1, timeout=30)
    pont_ok = bool(r)
    if r:
        champs = r[-1].group(1).strip().rstrip('"').split("#")
        perdus, n0, atk_perdus, atk_n, cibles = [int(float(x)) for x in champs[:5]]
        print("  pertes amies (cohorte) : %d / %d" % (perdus, n0))
        print("  pertes ennemies        : %d / %d" % (atk_perdus, atk_n))
        print("  cibles intactes        : %d" % cibles)
    else:
        perdus = atk_perdus = cibles = -1
        print("  PONT MUET a la mesure finale")

    b.send('HMT_PB_GEL = false;')
    renf1 = nb_renforts()

    print("\n=== VERDICT ===")
    sN = sitrep("fin")
    menaces = sum(1 for f in sN["fobs"] if f["contacts"] > 0) if sN else -1
    print("  C1 pertes amies lues sur la cohorte : %d   -> %s"
          % (perdus, "OK" if perdus >= 8 else "ECHEC"))
    print("  C2 FOB menaces vus                  : %d   -> %s"
          % (menaces, "OK" if menaces >= 2 else "ECHEC"))
    print("  C3 renforts pendant l'episode       : %d   -> %s"
          % (renf1 - renf0, "OK (gel actif)" if renf1 == renf0 else "ECHEC (gel inoperant)"))
    print("  C4 pont vivant a la fin             : %s" % ("OK" if pont_ok else "ECHEC"))
    if perdus >= 0:
        print("  impact score : %.3f (morts) + %.3f (cibles) = %.3f"
              % (perdus * 0.025, (8 - cibles) * 0.125, perdus * 0.025 + (8 - cibles) * 0.125))
finally:
    try:
        b.send('HMT_PB_GEL = false;')
        b.close()
    except Exception:
        pass
