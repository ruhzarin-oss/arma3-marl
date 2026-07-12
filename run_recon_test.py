"""run_recon_test — 1.1-bis : RECONNAISSANCE live, version DATA-DRIVEN.
Pour chaque posture : settle -> s0 -> poussee -> s1. On AFFICHE les features brutes (delta) pour voir
ce qui distingue reellement les postures, + ce que l'officier en deduit. 1 op/posture, parallele."""
import threading
import officer_live

POSTURES = officer_live.POSTURES
EXPECT = {"skilled": "M3", "skilled_react": "M3", "skilled_react_depth": "M3", "skilled_mobile": "M3",
          "skilled_elastic": "M1", "skilled_herisson": "M8", "skilled_appat": "M12", "skilled_sortie": "M12"}
SH = {"skilled": "sk", "skilled_react": "react", "skilled_react_depth": "depth", "skilled_mobile": "mobile",
      "skilled_elastic": "elast", "skilled_herisson": "heris", "skilled_appat": "appat", "skilled_sortie": "sortie"}

results = {}; lock = threading.Lock()

def work(srv, post):
    try:
        rep, pe, man, s0, s1 = officer_live.recon_only(srv, 300 + srv, post)
    except Exception as e:
        rep, pe, man, s0, s1 = "ERREUR " + type(e).__name__, "?", "?", None, None
    with lock:
        results[post] = (rep, pe, man, s0, s1)

th = [threading.Thread(target=work, args=(i, POSTURES[i])) for i in range(len(POSTURES))]
for t in th: t.start()
for t in th: t.join()

print("=== FEATURES BRUTES par posture (settle s0 -> poussee s1) ===")
print("%-7s | in_obj s0->s1 | dy(cy1-cy0) | dx | disp1 | out60_1 | n s0->s1 | -> man (att.)" % "posture")
ok = 0
for post in POSTURES:
    rep, pe, man, s0, s1 = results.get(post, ("?", "?", "?", None, None))
    exp = EXPECT[post]; good = man == exp; ok += good
    if s0 and s1:
        print("%-7s |   %2d -> %2d    |   %+6.0f    | %+5.0f | %5.0f |   %2d    | %2d->%2d  | %s (%s) %s"
              % (SH[post], s0["in_obj"], s1["in_obj"], s1["cy"] - s0["cy"], s1["cx"] - s0["cx"],
                 s1["disp"], s1["out60"], s0["n"], s1["n"], man, exp, "OK" if good else "x"))
    else:
        print("%-7s | (pas de stats) -> %s" % (SH[post], rep[:60]))
print("\nSCORE manoeuvre : %d/8 (objectif : voir si les features DISTINGUENT appat/heris/elast/sortie)" % ok)
