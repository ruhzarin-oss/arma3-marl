"""reanalyze_trace — re-analyse les MEMES traces avec des features CIBLEES (zero nouvelle op).
Idee : distinguer 'objectif vide car ABANDONNE' (appat : vide alors que l'ennemi est encore vivant et loin
au nord) de 'objectif vide car GAGNE' (ennemi mort). + herisson = tient dense jusqu'au bout."""
import json
import numpy as np

rows = [json.loads(l) for l in open("recon_trace.jsonl") if "series" in json.loads(l)]
classes = ["M3", "M1", "M8", "M12"]
SH = {"M3": "M3", "M1": "M1(elast)", "M8": "M8(heris)", "M12": "M12(appat)"}


def feats(s):
    en0 = max(1, s[0]["en"])
    # ABANDON : a un moment, objectif vide MAIS ennemi encore une force (>=40%) et replie loin nord
    abandon = 0; back = 0.0
    for x in s:
        alive_force = x["en"] >= 0.4 * en0
        if x["obj_hold"] == 0 and alive_force:
            abandon = 1
            back = max(back, x["cy"] if x["cy"] > 0 else 0)   # recul nord pendant qu'il est vivant
    tail = s[max(0, len(s) - 6):]
    holds_end = float(np.mean([x["obj_hold"] for x in tail]))         # herisson tient
    disp_end = float(np.mean([x["core_disp"] for x in tail]))
    toward_mx = max(x["toward"] for x in s)
    # recul max du centroide TANT QU'il reste une force (evite l'artefact QRF/stragglers en fin)
    cy_alive = [x["cy"] for x in s if x["en"] >= 0.4 * en0]
    cy_pull = max(cy_alive) if cy_alive else 0.0
    return {"abandon": abandon, "back": round(back, 0), "holds_end": round(holds_end, 1),
            "disp_end": round(disp_end, 1), "toward_mx": toward_mx, "cy_pull": round(cy_pull, 0)}


data = [(r["label"], feats(r["series"])) for r in rows]
FK = ["abandon", "back", "holds_end", "disp_end", "toward_mx", "cy_pull"]
y = np.array([lab for lab, f in data]); X = np.array([[f[k] for k in FK] for lab, f in data])

print("=== features CIBLEES par classe ===")
print("%-12s " % "feat" + " ".join("%10s" % SH[c] for c in classes))
for j, k in enumerate(FK):
    print("%-12s " % k + " ".join("%10.2f" % (X[y == c, j].mean() if (y == c).any() else float("nan")) for c in classes))
print("n: " + " ".join("%s=%d" % (c, int((y == c).sum())) for c in classes))

# regle simple data-driven : abandon-vivant -> M12 ; sinon tient dense -> M8 ; sinon M3 (defaut)
print("\n=== regle simple : abandon(vivant)->M12 | tient_dense->M8 | defaut M3 ===")
pred = []
for lab, f in data:
    if f["abandon"] and f["cy_pull"] >= 120:
        pred.append("M12")
    elif f["holds_end"] >= 1.0 and f["disp_end"] >= 45:
        pred.append("M8")
    else:
        pred.append("M3")
pred = np.array(pred)
# on evalue surtout : detecte-t-on M12 (le switch a +25) sans fausse alarme sur M3 ?
for c in classes:
    sel = y == c
    if sel.any():
        from collections import Counter
        print("  vrai %-10s -> %s" % (SH[c], dict(Counter(pred[sel]))))
m12_recall = (pred[y == "M12"] == "M12").mean() if (y == "M12").any() else 0
m12_fp = (pred[y != "M12"] == "M12").mean() if (y != "M12").any() else 0
print("\nM12 : rappel=%.0f%% (on attrape l'appat/sortie) | fausses alarmes sur non-M12=%.0f%%" % (100 * m12_recall, 100 * m12_fp))
