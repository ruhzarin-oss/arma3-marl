"""Porte 3b des pensions de survivant et de guerre ( HMT-194 ). Criteres ecrits avant la mesure ( Plane, 03/10, et
leurs amendements d avant la mesure ) : Malden ( 2001 ), echelle 20, cas poses sur le monde.

R1  le pensionne marie mort de maladie : conjoint 70 %, enfants 25 % ( 50 % orphelin ), au prorata au-dela de 1 ; part
    nationale au prorata.
R2  conditions : marie depuis moins de 3 ans sans enfant commun, mort de maladie -> rien ; le meme mort d accident -> le
    conjoint ; un assure a moins de 1 500 jours -> rien ; a 1 500 et plus, base = calculer_pension( invalidite ).
R3  la fin et la reduction : la somme d une famille au-dela de 1 vaut exactement la base ; l enfant de 24 ans sort ; le
    conjoint remarie sort ; apres 3 ans, le conjoint qui a une pension passe a 50 %.
R4  la guerre : conscrit marie ( 48,76 % de la solde officier + 2 % par enfant ), conscrit seul ( ses parents a parts
    egales ), carriere ( 0,7 + 0,1 par enfant de la solde de son metier, plafond 1 ) ; mort de maladie -> pas de pension
    de guerre ; les deux ouvertes -> la plus forte.
R5  les comptes : 10 jours, ce que le grand livre verse ( pension_survivant de la caisse, pension de l Etat ) a chaque
    menage = les dus recalcules a part au moment du versement, a 1e-6.
R6  tests_d04_travail : les 14 autres portes passent, test_emploi_20_64 et test_inactifs_changent echouent comme avant.

python -m guerre.porte_pension_survivant [ graine ]"""
import json
import math
import pickle
import re
import sys
import time

from monde import archipel as AR, tests as T
from monde.pays import d01_population as POP, d04_travail as TR, d25_armee as A

SORTIE = "/mnt/data/hmt/arsenal/porte_pension_survivant.json"
LOG_TESTS = "/mnt/data/hmt/arsenal/tests_d04.log"
AN = 365.0


class Releve:
    """L enregistreur du grand livre : les versements de pension de survivant et de guerre, avec leur menage."""
    def __init__(self): self.lignes = []

    def argent(self, motif, de, vers, paye):
        if motif in ("pension_survivant", "pension"):
            self.lignes.append((motif, type(de).__name__, int(getattr(vers, "id", -1)), float(paye)))

    def __getattr__(self, nom):
        return lambda *a, **k: None


def age(p, i): return (p.jour - int(p.col("habitant", "naissance_j")[i])) / AN


def revs(w, defunt=None):
    rs = getattr(w.pays.domaine("travail"), "reversions", None) or []
    return [r for r in rs if defunt is None or r.defunt == defunt]


def mensuels(w, defunt):
    """{ ( beneficiaire, qualite, nature ) : mensuel } d une famille, par le code du domaine ( _montants )."""
    p = w.pays; d = p.domaine("travail"); rs = revs(w, defunt)
    out = {}
    for nat in ("survivant", "guerre"):
        for r, m in TR._montants(p, d, [r for r in rs if r.nature == nat]): out[(r.hid, r.qualite, r.nature)] = m
    return out


# ------------------------------------------------------------------ la loi, rejouee a part
def droit(p, r):
    col = p.colonnes["habitant"]
    if not p.w.table.vivant[r.hid]: return False
    if r.qualite == "conjoint": return int(col["conjoint"][r.hid]) < 0
    if r.qualite == "parent": return True
    if int(col["conjoint"][r.hid]) >= 0: return False
    if r.nature == "guerre": return int(col["sexe"][r.hid]) == POP.FEMME or age(p, r.hid) < 18.0
    return age(p, r.hid) < 24.0


def loi_famille(p, rs):
    """[ mensuel ] d une famille ( meme defunt, meme nature ), d apres la loi."""
    d = p.domaine("travail"); col = p.colonnes["habitant"]
    if rs[0].nature == "survivant":
        t = []
        for r in rs:
            if r.qualite == "conjoint":
                actif = int(col["tr_statut"][r.hid]) in TR.EN_EMPLOI or r.hid in d.pensions
                t.append(0.5 if p.jour - r.jour >= 3 * 365 and actif else 0.7)
            else: t.append(0.5 if r.qualite == "orphelin" else 0.25)
        k = min(1.0, 1.0 / sum(t))
        return [r.base * x * k for r, x in zip(rs, t)]
    if rs[0].conscrit: S, a, b, cap = A.solde_annuelle(p, "officier") / 12.0, 40 * 0.01219, 0.02, math.inf
    else: S, a, b, cap = A.solde_annuelle(p, rs[0].role) / 12.0, 0.7, 0.1, 1.0
    par = [r for r in rs if r.qualite == "parent"]
    if par: t = [a / len(par) if r.qualite == "parent" else 0.0 for r in rs]
    else:
        tete = next((r for r in rs if r.qualite == "conjoint"), rs[0])
        t = [a if r is tete else b for r in rs]
    k = min(1.0, cap / sum(t)) if sum(t) > 0 else 1.0
    return [S * x * k for x in t]


def attendus(w):
    """{ ( motif, menage ) : du du jour } recalcule a part depuis les pensions en cours."""
    p = w.pays; tb = w.table; fam = {}
    for r in revs(w):
        if droit(p, r): fam.setdefault((r.defunt, r.nature), []).append(r)
    out = {}
    for (_, nat), rs in sorted(fam.items()):
        for r, m in zip(rs, loi_famille(p, rs)):
            k = ("pension_survivant" if nat == "survivant" else "pension", int(tb.menage[r.hid]))
            out[k] = out.get(k, 0.0) + m * 12.0 / AN
    return out


def total_civil(p, i, conj, enfants):
    """La pension de survivant que i ouvrirait ( mensuelle totale ), a part."""
    col = p.colonnes["habitant"]; d = p.domaine("travail")
    pn = d.pensions.get(i)
    base = pn.mensuelle if pn else TR.calculer_pension(float(col["tr_jours_cotises"][i]), float(col["tr_assiette"][i]), age(p, i), True)[0]
    if base <= 0: return 0.0
    t = ([0.7] if conj >= 0 else []) + [0.25] * len([k for k in enfants if int(col["conjoint"][k]) < 0 and age(p, k) < 24])
    return base * min(1.0, sum(t)) if t else 0.0


# ------------------------------------------------------------------ les cas
def candidats(w):
    p = w.pays; d = p.domaine("travail"); col = p.colonnes["habitant"]; tb = w.table; n = tb.n
    ed = p.domaine("population").enfants_de
    viv = lambda i: bool(tb.vivant[i])
    conj = lambda i: int(col["conjoint"][i])
    role = lambda i: TR._role_de(tb, i)
    jc = col["tr_jours_cotises"]
    enf24 = lambda i: [k for k in sorted(ed.get(i, ())) if viv(k) and conj(k) < 0 and age(p, k) < 24]
    pris = set()
    def libre(*ids): return all(x not in pris for x in ids)
    C = {}
    C["r1"] = next(i for i in sorted(d.pensions) if viv(i) and age(p, i) >= 67 and conj(i) >= 0 and viv(conj(i))
                   and int(col["union_j"][i]) <= 0 and conj(i) in d.pensions and role(i) not in ("soldat", "officier"))
    pris |= {C["r1"], conj(C["r1"])}
    C["r3"] = next(i for i in range(n) if viv(i) and i not in d.pensions and jc[i] >= 1500 and conj(i) >= 0 and viv(conj(i))
                   and len(enf24(i)) >= 2 and role(i) not in ("soldat", "officier") and libre(i, conj(i)))
    pris |= {C["r3"], conj(C["r3"])} | set(enf24(C["r3"]))
    E = A._dom(p).eff; rows = A._lignes_actives(A._dom(p)).tolist()
    sold = [(int(E["hid"][r]), r) for r in rows if role(int(E["hid"][r])) == "soldat" and viv(int(E["hid"][r]))]
    C["r4a"] = next((i, r) for i, r in sold if conj(i) >= 0 and viv(conj(i)) and i not in d.pensions and libre(i, conj(i)))
    pris |= {C["r4a"][0], conj(C["r4a"][0])}
    C["r4b"] = next((i, r) for i, r in sold if conj(i) < 0 and not ed.get(i) and libre(i))
    pris.add(C["r4b"][0])
    C["parents"] = next((h, conj(h)) for h in range(n) if viv(h) and int(col["sexe"][h]) == POP.HOMME and conj(h) >= 0
                        and viv(conj(h)) and 40 <= age(p, h) <= 65 and libre(h, conj(h)) and role(h) not in ("soldat", "officier"))
    pris |= set(C["parents"])
    car = []
    for i, r in [(int(E["hid"][r]), r) for r in rows if E["conscrit"][r] == 0]:
        if not (viv(i) and conj(i) >= 0 and viv(conj(i)) and libre(i, conj(i))): continue
        ke = [k for k in sorted(ed.get(i, ())) if viv(k) and conj(k) < 0 and (int(col["sexe"][k]) == POP.FEMME or age(p, k) < 18)]
        if not ke: continue
        S = A.solde_annuelle(p, role(i)) / 12.0
        guerre = S * min(1.0, 0.7 + 0.1 * len(ke))
        car.append((i, r, guerre, total_civil(p, i, conj(i), sorted(ed.get(i, ())))))
    C["r4c"] = next((i, r) for i, r, g, c in car if g >= c)
    C["r4e"] = next((i, r) for i, r, g, c in car if i != C["r4c"][0])
    C["r2a"] = next(i for i in range(n) if viv(i) and i not in d.pensions and jc[i] >= 1500 and conj(i) >= 0 and viv(conj(i))
                    and not ed.get(i) and not ed.get(conj(i)) and role(i) not in ("soldat", "officier") and libre(i, conj(i)))
    C["r2b"] = next(i for i in range(n) if viv(i) and i not in d.pensions and 0 < jc[i] < 1500 and conj(i) >= 0 and viv(conj(i))
                    and role(i) not in ("soldat", "officier") and libre(i, conj(i)))
    return C


def tuer(w, i, cause): POP.deceder(w.pays, w.habitants[i], cause)


def main(graine=2001):
    t0 = time.time(); R = {}
    print(f"PORTE 3b DES PENSIONS DE SURVIVANT ET DE GUERRE : Malden {graine}", flush=True)
    w0 = AR.creer_ile("Malden", graine, 20); T.jours(w0, 1)
    C = candidats(w0)
    R["cas"] = {k: v for k, v in C.items()}
    print(f"  cas : {R['cas']}", flush=True)
    oct_ = pickle.dumps(w0, protocol=4)
    # ------------------------------------------------ le monde des cas R1, R3, R4 et des comptes R5
    w = pickle.loads(oct_); p = w.pays; d = p.domaine("travail"); col = p.colonnes["habitant"]; tb = w.table
    E = A._dom(p).eff; ed = p.domaine("population").enfants_de
    i4a, r4a = C["r4a"]; E["conscrit"][r4a] = 1; col["tr_jours_cotises"][i4a] = 0.0; col["tr_assiette"][i4a] = 0.0
    i4b, r4b = C["r4b"]; E["conscrit"][r4b] = 1; col["tr_jours_cotises"][i4b] = 0.0; col["tr_assiette"][i4b] = 0.0
    col["pere"][i4b], col["mere"][i4b] = C["parents"]
    i4c = C["r4c"][0]
    conj = {i: int(col["conjoint"][i]) for i in (C["r1"], C["r3"], i4a, i4c)}
    pn1 = d.pensions[C["r1"]]
    base3 = TR.calculer_pension(float(col["tr_jours_cotises"][C["r3"]]), float(col["tr_assiette"][C["r3"]]), age(p, C["r3"]), True)[0]
    civil4c = total_civil(p, i4c, conj[i4c], sorted(ed.get(i4c, ())))
    rel = Releve(); p.socle.livre.enregistreur = rel
    orig = TR._prestations
    jours = []
    def enveloppe(p_, d_, agg):
        att = attendus(w); avant = len(rel.lignes)
        orig(p_, d_, agg)
        vu = {}
        for mot, de, m, x in rel.lignes[avant:]:
            vu[(mot, m)] = vu.get((mot, m), 0.0) + x
        ecarts = {f"{k[0]}:{k[1]}": (vu.get(k, 0.0), att.get(k, 0.0)) for k in set(vu) | set(att)
                  if abs(vu.get(k, 0.0) - att.get(k, 0.0)) > 1e-6}
        jours.append({"jour": int(p_.jour), "menages": len(set(vu) | set(att)), "verse": round(sum(vu.values()), 6),
                      "attendu": round(sum(att.values()), 6), "ecarts": ecarts})
    TR._prestations = enveloppe
    try:
        for i, cause in ((C["r1"], "maladie"), (C["r3"], "maladie"), (i4a, "combat"), (i4b, "combat"), (i4c, "combat")):
            tuer(w, i, cause)
        T.jours(w, 1)
        # R1
        m1 = mensuels(w, C["r1"]); rs1 = revs(w, C["r1"])
        enf1 = [k for k in sorted(ed.get(C["r1"], ())) if tb.vivant[k] and int(col["conjoint"][k]) < 0 and age(p, k) < 24]
        att1 = {(conj[C["r1"]], "conjoint")} | {(k, "enfant") for k in enf1}
        t1 = 0.7 + 0.25 * len(enf1); k1 = min(1.0, 1.0 / t1)
        ok1 = {(r.hid, r.qualite) for r in rs1} == att1 and all(r.nature == "survivant" for r in rs1) \
            and abs(m1[(conj[C["r1"]], "conjoint", "survivant")] - pn1.mensuelle * 0.7 * k1) <= 1e-9 \
            and all(abs(r.nationale / r.base - pn1.nationale / pn1.mensuelle) <= 1e-12 for r in rs1)
        R["R1"] = {"ok": ok1, "pension": pn1.mensuelle, "beneficiaires": sorted(att1), "mensuels": {str(k): v for k, v in m1.items()}}
        print(f"  R1 pensionne : {'OUI' if ok1 else 'NON'} {R['R1']}", flush=True)
        # R3 ( reduction )
        m3 = mensuels(w, C["r3"]); rs3 = revs(w, C["r3"])
        somme3 = sum(m3.values()); nominal3 = 0.7 + sum(0.5 if r.qualite == "orphelin" else 0.25 for r in rs3 if r.qualite != "conjoint")
        ok3a = nominal3 > 1.0 and abs(somme3 - base3) <= 1e-9 and abs(rs3[0].base - base3) <= 1e-9
        # R4
        S_off = A.solde_annuelle(p, "officier") / 12.0
        m4a = mensuels(w, i4a); e4a = [k for k in sorted(ed.get(i4a, ())) if tb.vivant[k] and int(col["conjoint"][k]) < 0
                                       and (int(col["sexe"][k]) == POP.FEMME or age(p, k) < 18)]
        ok4a = all(k[2] == "guerre" for k in m4a) and abs(m4a.get((conj[i4a], "conjoint", "guerre"), -1) - 40 * 0.01219 * S_off) <= 1e-9 \
            and all(abs(m4a.get((k, "enfant", "guerre"), -1) - 0.02 * S_off) <= 1e-9 for k in e4a) and len(m4a) == 1 + len(e4a)
        m4b = mensuels(w, i4b)
        ok4b = set(m4b) == {(C["parents"][0], "parent", "guerre"), (C["parents"][1], "parent", "guerre")} \
            and all(abs(v - 40 * 0.01219 * S_off / 2) <= 1e-9 for v in m4b.values())
        m4c = mensuels(w, i4c); role4c = TR._role_de(tb, i4c); S4c = A.solde_annuelle(p, role4c) / 12.0
        e4c = [k for k in sorted(ed.get(i4c, ())) if tb.vivant[k] and int(col["conjoint"][k]) < 0
               and (int(col["sexe"][k]) == POP.FEMME or age(p, k) < 18)]
        k4c = min(1.0, 1.0 / (0.7 + 0.1 * len(e4c)))
        ok4c = all(k[2] == "guerre" for k in m4c) and abs(m4c.get((conj[i4c], "conjoint", "guerre"), -1) - 0.7 * k4c * S4c) <= 1e-9 \
            and all(abs(m4c.get((k, "enfant", "guerre"), -1) - 0.1 * k4c * S4c) <= 1e-9 for k in e4c) \
            and abs(sum(m4c.values()) - S4c * min(1.0, 0.7 + 0.1 * len(e4c))) <= 1e-9 and sum(m4c.values()) >= civil4c - 1e-9
        # R3 ( la fin ) : un enfant a 24 ans, le conjoint de r3 remarie ; apres 3 ans, le conjoint pensionne de r1 a 50 %
        enfant_sort = next(r.hid for r in rs3 if r.qualite != "conjoint")
        col["naissance_j"][enfant_sort] = p.jour - int(24 * AN)          # 24 ans des aujourd hui ( la paie est a 18 h )
        nouveau = next(h for h in range(tb.n) if tb.vivant[h] and int(col["conjoint"][h]) < 0 and age(p, h) >= 30
                       and int(col["sexe"][h]) != int(col["sexe"][conj[C["r3"]]]) and h not in {r.hid for r in revs(w)})
        col["conjoint"][conj[C["r3"]]] = nouveau; col["conjoint"][nouveau] = conj[C["r3"]]
        for r in rs1:
            if r.qualite == "conjoint": r.jour = p.jour - 3 * 365 - 1
        T.jours(w, 1)
        rs3b = revs(w, C["r3"])
        sortis = enfant_sort not in {r.hid for r in rs3b} and conj[C["r3"]] not in {r.hid for r in rs3b} and bool(rs3b)
        m1b = mensuels(w, C["r1"])
        k1b = min(1.0, 1.0 / (0.5 + 0.25 * len(enf1)))
        ok3b = sortis and abs(m1b[(conj[C["r1"]], "conjoint", "survivant")] - pn1.mensuelle * 0.5 * k1b) <= 1e-9
        R["R3"] = {"ok": ok3a and ok3b, "nominal": nominal3, "somme": somme3, "base": base3, "sortis": sortis,
                   "avant": [(r.hid, r.qualite) for r in rs3], "apres": [(r.hid, r.qualite) for r in rs3b],
                   "enfant_24_ans": enfant_sort, "conjoint_remarie": conj[C["r3"]],
                   "conjoint_r1_apres_3_ans": m1b.get((conj[C["r1"]], "conjoint", "survivant"))}
        print(f"  R3 fin et reduction : {'OUI' if R['R3']['ok'] else 'NON'} {R['R3']}", flush=True)
        # R5 : 8 jours de plus
        T.jours(w, 8)
    finally:
        TR._prestations = orig; p.socle.livre.enregistreur = None
    ok5 = len(jours) == 10 and all(not j["ecarts"] for j in jours) and all(j["verse"] > 0 for j in jours)
    R["R5"] = {"ok": ok5, "jours": jours}
    print(f"  R5 comptes : {'OUI' if ok5 else 'NON'} {[(j['jour'], j['verse'], j['attendu'], len(j['ecarts'])) for j in jours]}", flush=True)
    # ------------------------------------------------ R2 : les conditions ( copies )
    out2 = {}
    for cause in ("maladie", "accident"):
        w2 = pickle.loads(oct_); p2 = w2.pays; c2 = p2.colonnes["habitant"]; i = C["r2a"]; cj = int(c2["conjoint"][i])
        c2["union_j"][i] = c2["union_j"][cj] = p2.jour
        base = TR.calculer_pension(float(c2["tr_jours_cotises"][i]), float(c2["tr_assiette"][i]), age(p2, i), True)[0]
        tuer(w2, i, cause); T.jours(w2, 1)
        out2[cause] = {"mensuels": {str(k): v for k, v in mensuels(w2, i).items()}, "base": base, "conjoint": cj}
    w2 = pickle.loads(oct_); i = C["r2b"]; tuer(w2, i, "maladie"); T.jours(w2, 1)
    out2["moins_1500"] = {"jours": float(w2.pays.colonnes["habitant"]["tr_jours_cotises"][i]), "reversions": len(revs(w2, i))}
    acc = out2["accident"]
    ok2 = not out2["maladie"]["mensuels"] and len(acc["mensuels"]) == 1 and acc["base"] > 0 \
        and abs(list(acc["mensuels"].values())[0] - 0.7 * acc["base"]) <= 1e-9 and out2["moins_1500"]["reversions"] == 0
    R["R2"] = {"ok": ok2, **out2}
    print(f"  R2 conditions : {'OUI' if ok2 else 'NON'} {R['R2']}", flush=True)
    # ------------------------------------------------ R4 : mort de maladie ; la plus forte
    w4 = pickle.loads(oct_); tuer(w4, i4c, "maladie"); T.jours(w4, 1)
    ok4d = not any(r.nature == "guerre" for r in revs(w4, i4c))
    w5 = pickle.loads(oct_); p5 = w5.pays; c5 = p5.colonnes["habitant"]; i4e = C["r4e"][0]; ed5 = p5.domaine("population").enfants_de
    c5["tr_jours_cotises"][i4e] = 12000.0; c5["tr_assiette"][i4e] = 12000.0 / TR.JOURS_ASSURANCE_MOIS * 1e5   # pose : une forte carriere
    cj5 = int(c5["conjoint"][i4e]); kids5 = sorted(ed5.get(i4e, ()))
    civil = total_civil(p5, i4e, cj5, kids5)
    ke5 = [k for k in kids5 if w5.table.vivant[k] and int(c5["conjoint"][k]) < 0 and (int(c5["sexe"][k]) == POP.FEMME or age(p5, k) < 18)]
    guerre = A.solde_annuelle(p5, TR._role_de(w5.table, i4e)) / 12.0 * min(1.0, 0.7 + 0.1 * len(ke5))
    tuer(w5, i4e, "combat"); T.jours(w5, 1)
    m5 = mensuels(w5, i4e)
    natures5 = {k[2] for k in m5}
    ok4e = civil > guerre and natures5 == {"survivant"} and abs(sum(m5.values()) - civil) <= 1e-6 * civil
    R["R4"] = {"ok": ok4a and ok4b and ok4c and ok4d and ok4e, "solde_officier": S_off,
               "conscrit_marie": {"ok": ok4a, "mensuels": {str(k): v for k, v in m4a.items()}, "enfants": e4a},
               "conscrit_seul": {"ok": ok4b, "mensuels": {str(k): v for k, v in m4b.items()}},
               "carriere": {"ok": ok4c, "role": role4c, "solde": S4c, "enfants": e4c, "civil": civil4c,
                            "mensuels": {str(k): v for k, v in m4c.items()}},
               "maladie": {"ok": ok4d}, "plus_forte": {"ok": ok4e, "civil": civil, "guerre": guerre, "natures": sorted(natures5)}}
    print(f"  R4 guerre : {'OUI' if R['R4']['ok'] else 'NON'} {R['R4']}", flush=True)
    # ------------------------------------------------ R6 : les portes du domaine 4
    try: lignes = open(LOG_TESTS).read().splitlines()
    except OSError: lignes = []
    res = {m.group(2): m.group(1) for m in (re.match(r"(PASSE|ECHOUE)\s+travail\s+(\S+)", l) for l in lignes) if m}
    attendus_ko = {"test_emploi_20_64", "test_inactifs_changent"}
    ok6 = len(res) == 16 and {t for t, v in res.items() if v == "ECHOUE"} == attendus_ko
    R["R6"] = {"ok": ok6, "portes": res}
    print(f"  R6 tests_d04 : {'OUI' if ok6 else 'NON'} {res}", flush=True)
    oks = [R[k]["ok"] for k in ("R1", "R2", "R3", "R4", "R5", "R6")]
    verdict = "FRANCHIE" if all(oks) else "REFUSEE"
    R.update(verdict=verdict, graine=graine, duree_s=round(time.time() - t0))
    json.dump(R, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE 3b DES PENSIONS DE SURVIVANT ET DE GUERRE : {verdict} ( {R['duree_s']} s )")
    print("FIN_PORTE_PENSION", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 2001))
