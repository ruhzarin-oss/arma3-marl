"""PORTE D IDENTITE DU MARCHE IMMOBILIER ACCELERE ( 27/09, ecrite avant la mesure ).

d13._apparier ( en tableaux ) doit rendre le MEME monde que d13._apparier_reference ( la version d origine ), au bit :
I1 un petit Stratis ( echelle 20 ) vit 30 jours avec chacune : les empreintes de tout le pays ( porte_domaines.empreinte,
   tous les domaines ) sont egales chaque jour. Controle positif : un milliardieme de drachme ajoute dans une des deux
   copies au jour 10 rend les empreintes differentes a partir de ce jour.
I2 le vrai cas : la sauvegarde de Stratis de la guerre ( 100 000 habitants ) ; le marche du jour joue par les deux
   versions sur deux copies : la table des batiments, le logement et le statut de chaque menage, les domiciles, les
   caisses sont identiques ; le temps de chacune est mesure.

   python -m guerre.porte_immobilier [ --instantane /mnt/data/hmt/guerre/essai12/instantane ]"""
import argparse, os, pickle, sys, time
import numpy as np
from monde.archipel import creer_ile
from monde import tests as T
from monde.pays import d13_immobilier as IM
from monde.porte_domaines import empreinte


RAPIDE = IM._apparier


def avec(version, f, *a):
    IM._apparier = IM._apparier_reference if version == "reference" else RAPIDE
    try: return f(*a)
    finally: IM._apparier = RAPIDE


def i1(jours=30, graine=1, echelle=20.0, perturber_au=None):
    ref, rap = creer_ile("Stratis", graine, echelle), creer_ile("Stratis", graine, echelle)
    ecarts = []
    for j in range(jours):
        if perturber_au is not None and j == perturber_au: rap.table.menages.caisse[0] += 1e-9
        avec("reference", T.jours, ref, 1); avec("rapide", T.jours, rap, 1)
        if empreinte(ref) != empreinte(rap): ecarts.append(j)
    return ecarts


def etat_immobilier(w):
    p = w.pays; d = p.domaine("immobilier"); B = d.B; n = B.n; nm = len(w.menages)
    return {"batiments": {c: B[c][:n].copy() for c in B.cols}, "logement": p.col("menage", "im_logement")[:nm].copy(),
            "statut": p.col("menage", "im_statut")[:nm].copy(), "domicile": w.table.menages.domicile[:nm].copy(),
            "caisse": w.table.menages.caisse[:nm].copy(), "stats": dict(d.stats)}


def egaux(a, b):
    diff = []
    for k in ("logement", "statut", "domicile", "caisse"):
        if a[k].shape != b[k].shape or not np.array_equal(a[k], b[k]): diff.append(k)
    for c in a["batiments"]:
        if not np.array_equal(a["batiments"][c], b["batiments"][c]): diff.append("batiments." + c)
    if a["stats"] != b["stats"]: diff.append("stats")
    return diff


def i2(dossier):
    brut = open(os.path.join(dossier, "Stratis.pkl"), "rb").read()
    res = {}
    for version in ("rapide", "reference"):
        w = pickle.loads(brut)
        t0 = time.time(); avec(version, IM._marche, w.pays); res[version] = (time.time() - t0, etat_immobilier(w))
        del w
    return res


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--instantane", default="/mnt/data/hmt/guerre/essai12/instantane")
    a.add_argument("--jours", type=int, default=30)
    x = a.parse_args()
    ok = {}
    t0 = time.time()
    e1 = i1(x.jours)
    e1c = i1(15, perturber_au=10)
    print(f"   I1 : {x.jours} jours, ecarts {e1} ; controle ( perturbation au jour 10 ) : ecarts {e1c[:3]}... ( {time.time() - t0:.0f} s )", flush=True)
    ok["I1 30 jours identiques au bit ( tous les domaines )"] = e1 == []
    ok["I1 controle positif : la perturbation du jour 10 est vue des le jour 10"] = bool(e1c) and e1c[0] == 10
    r = i2(x.instantane)
    d = egaux(r["rapide"][1], r["reference"][1])
    print(f"   I2 : marche du jour sur Stratis ( sauvegarde de la guerre ) : reference {r['reference'][0]:.1f} s, rapide {r['rapide'][0]:.1f} s "
          f"( x{r['reference'][0] / max(1e-9, r['rapide'][0]):.0f} ) ; differences {d or 'aucune'} ; stats {r['rapide'][1]['stats']}", flush=True)
    ok["I2 le vrai cas : batiments, logements, statuts, domiciles, caisses identiques"] = d == []
    for k, v in ok.items(): print(f"{'PASSE ' if v else 'ECHOUE'} {k}")
    passe = all(ok.values())
    print(f"PORTE D IDENTITE DE L IMMOBILIER : {'FRANCHIE' if passe else 'ECHOUEE'}")
    return 0 if passe else 1


if __name__ == "__main__":
    sys.exit(main())
