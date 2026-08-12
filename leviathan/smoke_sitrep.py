"""smoke_sitrep — le serveur repond-il un SITREP exploitable ? (test avant tout banc)"""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl")
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge
from officer_state import OfficerState, FOBS

b = NativeBridge(port=5816)
print("[pont] natif 5816 OK")
try:
    b.send('if (isNil "HMT_TARGET") then { HMT_TARGET = HMT_TARGETS apply {_x select 1}; };')
    coords = "[" + ",".join("[%d,%d]" % (f[1], f[2]) for f in FOBS) + "]"
    b.send("HMT_FOB_ANCHORS = %s;" % coords)
    b.send('call compile preprocessFileLineNumbers "officer_sit.sqf";')
    time.sleep(1.5)

    st = OfficerState(bridge=b)
    r = b.query('call HMT_SITREP;', r'HARMATTAN_SIT (.+)', want=1, timeout=15)
    if not r:
        print("SITREP ILLISIBLE — HMT_SITREP n'a rien emis")
        sys.exit(1)
    sit = st.parse(r[-1].group(1).rstrip('"').strip(), tick=0)

    gar = [f["garrison"] for f in sit["fobs"]]
    tenus = sum(1 for f in sit["fobs"] if f["held"])
    menaces = [(f["name"], f["contacts"]) for f in sit["fobs"] if f["contacts"] > 0]
    print("  FOB lus            : %d" % len(sit["fobs"]))
    print("  FOB tenus          : %d / %d" % (tenus, len(sit["fobs"])))
    print("  garnison min/med/max : %d / %d / %d" % (min(gar), sorted(gar)[len(gar) // 2], max(gar)))
    print("  force totale       : %d hommes" % sit["total_force"])
    print("  cibles vitales     : %d / %d intactes" % (sit["targets_intact"], sit["targets_total"]))
    print("  heure              : %.2f (%s)" % (sit["daytime"], "NUIT" if sit["is_night"] else "JOUR"))
    print("  menaces            : %s" % (menaces or "aucune"))

    ok = (len(sit["fobs"]) == 25 and tenus >= 20 and sit["total_force"] > 200
          and sit["targets_total"] > 0)
    print("\n  -> %s" % ("THEATRE PRET : le banc peut s'y poser." if ok else
                         "THEATRE INCOMPLET : garnisons ou cibles manquantes, ne pas lancer le banc."))
finally:
    try:
        b.close()
    except Exception:
        pass
