"""test_cibles — la dimension CIBLES est-elle enfin exercee ?

Criteres ecrits AVANT le run :
  T1 au moins UNE cible vitale doit tomber (sinon le levier n.1 de la doctrine reste mort).
  T2 la chute doit venir de la SAPE (ligne HARMATTAN_PB_CIBLE_TOMBEE), pas d'un hasard.
  T3 impact de score du terme cibles >= 0.125 (une cible = 0.125).
  T4 le pont doit survivre a l'episode.

Cible choisie : INTEL — une caisse (batiment, insensible aux balles) posee a ~97 m d'un FOB,
donc HORS du rayon de 40 m ou la garnison la protege. C'est exactement le cas ou l'ordre de
l'officier decide : laisser la garnison au FOB = la caisse tombe ; envoyer du monde = elle tient.
"""
import sys, time, subprocess
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import OfficerState, FOBS

LOG = "/mnt/data/harmattan-sandbox/logs/server_fob.out"
FOB_VISES = [3]                 # M4, le FOB qui porte une INTEL a ~97 m
N_PAR_FOB = 48
CIBLE = "INTEL"
DUREE = int(sys.argv[1]) if len(sys.argv) > 1 else 300


def nb(motif):
    try:
        return int(subprocess.check_output("grep -c '%s' %s || true" % (motif, LOG), shell=True).decode().strip() or 0)
    except Exception:
        return -1


b = NativeBridge(port=5816)
st = OfficerState(bridge=b)


def sitrep(tag):
    r = b.query('call HMT_SITREP;', r'HARMATTAN_SIT (.+)', want=1, timeout=25)
    if not r:
        print("  [%-9s] PONT MUET" % tag); return None
    s = st.parse(r[-1].group(1).rstrip('"').strip(), tick=0)
    print("  [%-9s] cibles %d/%d | menaces %s"
          % (tag, s["targets_intact"], s["targets_total"],
             [(f["name"], f["contacts"]) for f in s["fobs"] if f["contacts"] > 0] or "-"))
    return s


try:
    b.send('call compile preprocessFileLineNumbers "pressure_bench.sqf";')
    time.sleep(1.5)

    print("--- reset ---")
    b.send('[] spawn { call HMT_PB_RESET; };')
    b.query('', r'HARMATTAN_PB_RESET (.+)', want=1, timeout=200)
    time.sleep(8)
    b.send('HMT_PB_GEL = true;')
    b.query('call HMT_PB_COHORTE;', r'HARMATTAN_PB_COHORTE (.+)', want=1, timeout=30)
    tombees0 = nb("HARMATTAN_PB_CIBLE_TOMBEE")
    s0 = sitrep("depart")

    print("--- attaque %s + element de sape sur %s ---" % ([FOBS[i][0] for i in FOB_VISES], CIBLE))
    b.send('[%s, %d, "%s"] spawn HMT_PB_ATTACK;' % (str(FOB_VISES), N_PAR_FOB, CIBLE))
    r = b.query('', r'HARMATTAN_PB_ATTACK (.+)', want=1, timeout=120)
    print("  assaillants :", r[-1].group(1).strip().rstrip('"') if r else "AUCUN EMIT")

    t0 = time.time()
    while time.time() - t0 < DUREE:
        time.sleep(60)
        sitrep("t+%03ds" % int(time.time() - t0))

    print("--- mesure finale ---")
    r = b.query('call HMT_PB_PERTES;', r'HARMATTAN_PB_PERTES (.+)', want=1, timeout=30)
    pont_ok = bool(r)
    perdus = cibles = -1
    if r:
        ch = [int(float(x)) for x in r[-1].group(1).strip().rstrip('"').split("#")[:5]]
        perdus, n0, atk_perdus, atk_n, cibles = ch
        print("  pertes amies %d/%d | pertes ennemies %d/%d | cibles intactes %d"
              % (perdus, n0, atk_perdus, atk_n, cibles))
    tombees1 = nb("HARMATTAN_PB_CIBLE_TOMBEE")
    b.send('HMT_PB_GEL = false;')
    b.send('HMT_PB_SAPE_ON = false;')

    perdues = (s0["targets_intact"] - cibles) if (s0 and cibles >= 0) else -1
    print("\n=== VERDICT ===")
    print("  T1 cibles perdues            : %d   -> %s" % (perdues, "OK" if perdues >= 1 else "ECHEC"))
    print("  T2 chutes par SAPE (log)     : %d   -> %s" % (tombees1 - tombees0, "OK" if tombees1 > tombees0 else "ECHEC"))
    print("  T3 impact score du terme cibles : %.3f -> %s"
          % (max(0, perdues) * 0.125, "OK" if perdues >= 1 else "ECHEC"))
    print("  T4 pont vivant               : %s" % ("OK" if pont_ok else "ECHEC"))
    if perdus >= 0:
        print("  impact TOTAL : %.3f (morts) + %.3f (cibles) = %.3f"
              % (perdus * 0.025, max(0, perdues) * 0.125, perdus * 0.025 + max(0, perdues) * 0.125))
finally:
    try:
        b.send('HMT_PB_GEL = false;'); b.send('HMT_PB_SAPE_ON = false;'); b.close()
    except Exception:
        pass
