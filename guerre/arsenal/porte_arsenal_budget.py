"""Porte de l arsenal de depart paye par le budget ( HMT-191, etape 0c ). Criteres ecrits avant la mesure ( Plane ) :

B1  au jour 0, la valeur a neuf du materiel durable ( hors munitions et pieces ) <= enveloppe, et >= enveloppe - prix de
    l article le plus cher, sauf si toute la doctrine est payee.
B2  une categorie n a rien tant que la precedente n est pas complete ( lots individuels, camions, M1114, M113, mortiers,
    chars, reserve ).
B3  controle positif : duree de service forcee a 1e9 ans : memes comptes par base et par modele que sans l option.
B4  avec l option : anomalies() et Parc.verifier() vides aux jours 0 et 10 ; recoupement de l etat des lieux 0 ecart au
    jour 10.
B5  sans l option : identique au bit ( empreinte etendue, jours 0 a 3 ) au code du tronc bce9f31, arbre separe.

Stratis ( 1915 ), Malden ( 1916 ), echelle 20.
python -m guerre.arsenal.porte_arsenal_budget [--temoin /chemin/de/l/arbre/du/tronc]"""
import argparse
import json
import os
import subprocess
import sys
import time

from monde import archipel as AR, tests as T
from monde.pays import d25_armee as A
from . import etat_des_lieux as EL
from . import porte_etat_des_lieux as PE

ILES = (("Stratis", 1915), ("Malden", 1916))
ECHELLE = 20
SORTIE = "/mnt/data/hmt/arsenal/porte_arsenal_budget.json"
PY = sys.executable


def comptes(w):
    """{ ( lieu de l armurerie, modele ) : exemplaires vivants ( individus + cohortes ) } des modeles du domaine 25."""
    d = w.pays.domaines[A.DOMAINE]; parc = w.pays.socle.parc
    arm = {id(a): a.lieu for a in d.armureries}
    out = {}
    for o in parc.objets.values():
        if o.modele in d.idx_parc and id(o.proprietaire) in arm:
            k = (arm[id(o.proprietaire)], parc.modeles[o.modele].nom); out[k] = out.get(k, 0) + 1
    for (m, prop, _l), c in parc.cohortes.items():
        if m in d.idx_parc and id(prop) in arm:
            k = (arm[id(prop)], parc.modeles[m].nom); out[k] = out.get(k, 0) + c.nombre
    return out


def valeur_durable(w):
    d = w.pays.domaines[A.DOMAINE]; parc = w.pays.socle.parc
    return sum(parc.vivants[m] * parc.modeles[m].prix_monde for m in d.idx_parc)


def par_modele(c):
    out = {}
    for (_l, m), n in c.items(): out[m] = out.get(m, 0) + n
    return out


def reserve_individuelle(w):
    """Exemplaires de reserve : armes et optiques en cohorte ( les dotees sont des individus ) ; protections et radios
    en cohorte au-dela des dotees."""
    d = w.pays.domaines[A.DOMAINE]; parc = w.pays.socle.parc
    noms_ind = {a.nom for a in A.ARMES} | {o.nom for o in A.OPTIQUES}
    r = 0
    for (m, prop, _l), c in parc.cohortes.items():
        if m not in d.idx_parc: continue
        nom = parc.modeles[m].nom
        if nom in noms_ind: r += c.nombre
    for (b, nom), x in d.dotes.items():
        arm = d.armureries[d.par_base[b]]
        c = parc.cohortes.get((d.mids[nom], arm, arm.lieu))
        r += (c.nombre if c is not None else 0) - x
    return r


def empreintes_sans_option(racine, ile, graine, jours=3):
    """Empreintes etendues jour par jour d une ile SANS l option, calculees dans l arbre `racine` ( sous-processus )."""
    code = ("import json, sys\n"
            "from monde import archipel as AR, tests as T\n"
            "from guerre.arsenal import porte_etat_des_lieux as PE\n"
            f"w = AR.creer_ile({ile!r}, {graine}, {ECHELLE})\n"
            "out = [PE.empreinte_etendue(w)]\n"
            f"for _ in range({jours}):\n"
            "    T.jours(w, 1); out.append(PE.empreinte_etendue(w))\n"
            "print('EMPREINTES ' + json.dumps(out))\n")
    env = dict(os.environ, PYTHONPATH=racine, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    r = subprocess.run([PY, "-c", code], cwd=racine, env=env, capture_output=True, text=True)
    for l in r.stdout.splitlines():
        if l.startswith("EMPREINTES "): return json.loads(l[len("EMPREINTES "):])
    raise RuntimeError(f"{racine} : {r.stderr[-2000:]}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--temoin", default="/mnt/data/hmt/arsenal/temoin_bce9f31")
    a = ap.parse_args()
    t0 = time.time(); res = {"iles": {}}
    B1 = B2 = B3 = B4 = B5 = True
    ici = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for ile, graine in ILES:
        print(f"PORTE DE L ARSENAL PAR LE BUDGET : {ile}, graine {graine}, echelle {ECHELLE}", flush=True)
        wB = AR.creer_ile(ile, graine, ECHELLE, arsenal_budget=True)
        wD = AR.creer_ile(ile, graine, ECHELLE)
        bil = wB.arsenal_budget_bilan
        cB, cD = comptes(wB), comptes(wD)
        mB, mD = par_modele(cB), par_modele(cD)
        # B1
        v = valeur_durable(wB); env = bil["enveloppe_dr"]
        pmax = max(A.prix_dr(n) for n in set(mD))
        b1 = v <= env * (1 + 1e-9) and (bil["complet"] or v >= env - pmax)
        # B2 : l ordre
        cat = ["lots"] + list(A.ORDRE_VEHICULES) + ["reserve"]
        fait = {"lots": bil["equipes"] == bil["militaires"]}
        n_cat = {"lots": bil["equipes"]}
        for nom in A.ORDRE_VEHICULES:
            n_cat[nom] = mB.get(nom, 0); fait[nom] = mB.get(nom, 0) >= mD.get(nom, 0)
        n_cat["reserve"] = reserve_individuelle(wB); fait["reserve"] = True
        b2 = True
        for i, c in enumerate(cat[:-1]):
            if not fait[c] and any(n_cat[x] > 0 for x in cat[i + 1:]): b2 = False
        # B3 : controle positif ( enveloppe sans limite )
        sauve = A.DUREE_SERVICE_ANS; A.DUREE_SERVICE_ANS = 1e9
        try:
            wI = AR.creer_ile(ile, graine, ECHELLE, arsenal_budget=True)
        finally:
            A.DUREE_SERVICE_ANS = sauve
        cI = comptes(wI)
        diff = sorted(k for k in set(cI) | set(cD) if cI.get(k, 0) != cD.get(k, 0))
        b3 = not diff and wI.arsenal_budget_bilan["complet"]
        # B4 : la conservation, jours 0 et 10
        an0 = A.anomalies(wB.pays); ve0 = {k: x for k, x in wB.pays.socle.parc.verifier().items() if x}
        T.jours(wB, 10)
        an10 = A.anomalies(wB.pays); ve10 = {k: x for k, x in wB.pays.socle.parc.verifier().items() if x}
        ecarts, e10 = PE.recouper(wB)
        b4 = not an0 and not ve0 and not an10 and not ve10 and not ecarts
        # B5 : l identite sans l option, contre le tronc
        if os.path.isdir(a.temoin):
            eT = empreintes_sans_option(a.temoin, ile, graine)
            eA = empreintes_sans_option(ici, ile, graine)
            jours_faux = [j for j, (x, y) in enumerate(zip(eT, eA)) if x != y]
            b5 = not jours_faux and len(eT) == len(eA) == 4
        else:
            jours_faux = ["temoin absent"]; b5 = False
        B1 &= b1; B2 &= b2; B3 &= b3; B4 &= b4; B5 &= b5
        info = {"enveloppe_dr": env, "valeur_durable_dr": v, "valeur_doctrine_dr": valeur_durable(wD),
                "militaires": bil["militaires"], "equipes": bil["equipes"], "vehicules": bil["vehicules"],
                "reserve": bil["reserve"], "complet": bil["complet"], "par_modele_budget": mB, "par_modele_doctrine": mD,
                "B1": b1, "B2": b2, "n_categories": n_cat, "B3": b3, "B3_ecarts": diff[:20], "B4": b4,
                "B4_detail": {"anomalies0": an0[:5], "verifier0": ve0, "anomalies10": an10[:5], "verifier10": ve10,
                              "recoupement10": ecarts[:10]},
                "B5": b5, "B5_jours_faux": jours_faux,
                "valeur_sur_achats_an_budget": e10.get("valeur_sur_achats_an"),
                "valeur_eur_budget_j10": e10["valeur_eur"]}
        res["iles"][ile] = info
        print(f"  enveloppe {env:,.0f} dr ; materiel durable {v:,.0f} dr ( doctrine {info['valeur_doctrine_dr']:,.0f} ) ; "
              f"{bil['equipes']}/{bil['militaires']} militaires equipes ; vehicules {bil['vehicules']} ; "
              f"reserve {bil['reserve']}".replace(",", " "), flush=True)
        print(f"  B1 {'OUI' if b1 else 'NON'} | B2 {'OUI' if b2 else 'NON'} {n_cat} | B3 {'OUI' if b3 else 'NON'} {diff[:3]} "
              f"| B4 {'OUI' if b4 else 'NON'} | B5 {'OUI' if b5 else 'NON'} {jours_faux}", flush=True)
    verdict = "FRANCHIE" if (B1 and B2 and B3 and B4 and B5) else "REFUSEE"
    res.update(verdict=verdict, B1=B1, B2=B2, B3=B3, B4=B4, B5=B5, duree_s=round(time.time() - t0))
    json.dump(res, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"B1 {B1} B2 {B2} B3 {B3} B4 {B4} B5 {B5}")
    print(f"PORTE DE L ARSENAL PAR LE BUDGET : {verdict} ( {res['duree_s']} s )")
    print("FIN_PORTE_ARSENAL_BUDGET", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
