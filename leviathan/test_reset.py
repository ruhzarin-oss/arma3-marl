"""test_reset — HMT_PB_RESET remet-il le theatre dans l'etat de reference ?

Critere ecrit AVANT : apres reset, le SITREP doit redonner 25/25 FOB tenus, une force a +-10 %
de la reference, et 8/8 cibles. Si la force derive a chaque reset, le banc est inutilisable :
deux episodes ne partiraient pas du meme monde.
"""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import OfficerState, FOBS

N_CYCLES = int(sys.argv[1]) if len(sys.argv) > 1 else 2

b = NativeBridge(port=5816)
st = OfficerState(bridge=b)


def sitrep(tag):
    r = b.query('call HMT_SITREP;', r'HARMATTAN_SIT (.+)', want=1, timeout=20)
    if not r:
        print("  [%s] SITREP illisible" % tag); return None
    s = st.parse(r[-1].group(1).rstrip('"').strip(), tick=0)
    tenus = sum(1 for f in s["fobs"] if f["held"])
    print("  [%-10s] FOB %2d/25 | force %3d | cibles %d/%d | menaces %d"
          % (tag, tenus, s["total_force"], s["targets_intact"], s["targets_total"],
             sum(1 for f in s["fobs"] if f["contacts"] > 0)))
    return s


try:
    b.send('call compile preprocessFileLineNumbers "pressure_bench.sqf";')
    time.sleep(1.5)
    ref = sitrep("reference")

    for c in range(N_CYCLES):
        print("\n--- cycle %d ---" % (c + 1))
        b.send('[] spawn { call HMT_PB_RESET; };')
        r = b.query('', r'HARMATTAN_PB_RESET (.+)', want=1, timeout=180)
        if r:
            print("  emit reset :", r[-1].group(1).strip().rstrip('"'))
        else:
            print("  PAS D'EMIT — reset probablement en echec")
        time.sleep(8)
        s = sitrep("apres reset")
        if ref and s:
            d = abs(s["total_force"] - ref["total_force"]) / max(1, ref["total_force"])
            ok = (sum(1 for f in s["fobs"] if f["held"]) == 25 and d <= 0.10
                  and s["targets_intact"] == s["targets_total"])
            print("  derive de force : %.1f %%  -> %s" % (100 * d, "OK" if ok else "HORS TOLERANCE"))
finally:
    b.close()
