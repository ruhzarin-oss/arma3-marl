"""FORMER ET QUALIFIER TOUS LES GROUPES D AGENTS ( plans/plan-agents-partout.md, portes ecrites le 23/09 avant mesure ).

Chaque groupe est forme SEUL, les autres restant sur leurs regles, pour que l effet mesure soit le sien. Puis il passe
son examen sur des mondes jamais vus, contre la regle d origine et contre le hasard ( et contre le temoin aveugle pour
le commerce et les voyageurs ). La doctrine qualifiee est celle RELUE DU DISQUE, pas celle restee en memoire.

   python -m monde.former_tous                       # tous les groupes, en parallele
   python -m monde.former_tous --groupes armee,marches"""
import argparse, json, os, random, time
from multiprocessing import Pool
from . import monde as W, roles as R, carte as K, config as C, apprenti as AP, agents as A

DOSSIER = "/mnt/data/hmt/monde/doctrine"
ECOLE = list(range(1, 9))
EXAMEN = list(range(101, 111))

EPREUVE = {"travailleurs": "eco", "entreprises": "eco", "marches": "eco", "commerce": "eco",
           "armee": "armee", "voyageurs": "iles", "fraudeurs": "fraude"}


# ------------------------------------------------------------------ les mondes d epreuve
def construire(epreuve, graine, intensite=1.0):
    if epreuve == "eco":                  # secheresse sur deux capitales sur trois, epidemie de Pyrgos
        return AP.monde_epreuve(graine)
    if epreuve == "iles":                 # six iles, 2 000 habitants : la faim y est de 11,9 % avec les regles
        return W.Monde(graine=graine, iles=tuple(K.ILES), echelle=4)
    if epreuve == "armee":                # deux bases coupees du depot quatre jours, au hasard de la graine
        w = W.Monde(graine=graine)
        rng = random.Random(graine)
        bases = w.carte.de_type("base")
        w.coupures = [{"lieu": b.id, "debut": rng.randint(3, 10), "jours": 4} for b in rng.sample(bases, 2)]
        return w
    if epreuve == "fraude":
        w = W.Monde(graine=graine)
        w.intensite_controle = intensite
        return w
    raise ValueError(epreuve)


def intensite_ecole(graine):
    """A l ecole, les fraudeurs vivent sous des polices differentes : sinon ils ne pourraient rien apprendre du controle."""
    return (1.0, 2.0, 4.0)[graine % 3]


# ------------------------------------------------------------------ jouer un monde et le mesurer
def jouer(nom, epreuve, graine, mode, chemin=None, intensite=1.0, jours=20):
    w = construire(epreuve, graine, intensite)
    if mode in ("fige", "hasard"):
        doctrine = A.Doctrine.lire(chemin, epsilon=0.0) if mode == "fige" else None
        w.agents[nom] = R.groupe(nom, mode=mode, doctrine=doctrine)
    elif mode == "aveugle":
        if nom == "commerce": w.marchand = AP.marchand_aveugle
        elif nom == "voyageurs": w.fret_aveugle = True
    morts0 = sum(1 for h in w.habitants if not h.vivant)
    faim, pic = 0.0, 0.0
    for _ in range(jours):
        for _ in range(C.PAS_PAR_JOUR): w.pas_suivant()
        faim += w.stats_jour.get("menages_sans_nourriture", 0) / len(w.menages)
        vivants = [h for h in w.habitants if h.vivant]
        pic = max(pic, sum(1 for h in vivants if h.etat == "I") / max(1, len(vivants)))
    d_arg, d_b = w.verifier_conservation()
    morts = sum(1 for h in w.habitants if not h.vivant) - morts0
    faites, annulees = getattr(w, "patrouilles_faites", 0), getattr(w, "patrouilles_annulees", 0)
    return {"graine": graine, "mode": mode, "intensite": intensite,
            "faim": faim / jours, "morts": morts, "note": -100.0 * faim / jours - 5.0 * morts,
            "pic_infectes": pic,
            "patrouilles_tenues": faites / max(1, faites + annulees),
            "part_fraudee": w.tva_fraudee / max(1e-9, w.tva_fraudee + w.tva_percue),
            "conservation": abs(d_arg) / max(1.0, w.argent_total())}


def _jouer(args): return jouer(*args)


# ------------------------------------------------------------------ former un groupe
def former(nom, epoques, jours):
    epreuve = EPREUVE[nom]
    g = R.groupe(nom, mode="appris")
    journal = []
    for e in range(epoques):
        somme0, n0 = g.doctrine.somme_recompense, g.doctrine.n_lecons
        for graine in ECOLE:
            w = construire(epreuve, graine, intensite_ecole(graine))
            g.memoire, g.choix, g.etat = {}, {}, {}
            w.agents[nom] = g
            for _ in range(jours * C.PAS_PAR_JOUR): w.pas_suivant()
        dn = g.doctrine.n_lecons - n0
        journal.append({"epoque": e, "lecons": g.doctrine.n_lecons,
                        "recompense_de_l_epoque": round((g.doctrine.somme_recompense - somme0) / max(1, dn), 4)})
        g.doctrine.epsilon = max(0.02, g.doctrine.epsilon * 0.75)
    chemin = os.path.join(DOSSIER, f"{nom}.json")
    g.doctrine.ecrire(chemin)
    return nom, chemin, journal


def _former(args): return former(*args)


# ------------------------------------------------------------------ la porte
def mediane(v):
    v = sorted(v); n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def juger(nom, res):
    """La porte ecrite le 23/09 : battre la regle ( mediane et 7 mondes sur 10 ) ET le hasard ( mediane )."""
    if nom == "fraudeurs":
        f1 = [r["part_fraudee"] for r in res["fige@1"]]
        f4 = [r["part_fraudee"] for r in res["fige@4"]]
        gagnes = sum(1 for a, b in zip(f1, f4) if b < a)
        ok = mediane(f4) < mediane(f1) and gagnes >= 7
        return ok, (f"fraude a police x1 : {mediane(f1):.0%} ; a police x4 : {mediane(f4):.0%} ; "
                    f"elle baisse dans {gagnes}/10 mondes")
    cle = "patrouilles_tenues" if nom == "armee" else "note"
    regle, hasard, fige = ([r[cle] for r in res[m]] for m in ("regle", "hasard", "fige"))
    gagnes = sum(1 for a, b in zip(regle, fige) if b > a)
    ok = mediane(fige) > mediane(regle) and gagnes >= 7 and mediane(fige) > mediane(hasard)
    texte = (f"{cle} mediane : regle {mediane(regle):.3f} | hasard {mediane(hasard):.3f} | forme {mediane(fige):.3f} "
             f"| {gagnes}/10 mondes gagnes contre la regle")
    if "aveugle" in res:
        av = mediane([r[cle] for r in res["aveugle"]])
        texte += f" | aveugle {av:.3f}"
        if nom == "commerce": ok = ok and mediane(fige) > av       # porte du commerce : battre aussi l aveugle
    if nom == "travailleurs":
        pr, pf = mediane([r["pic_infectes"] for r in res["regle"]]), mediane([r["pic_infectes"] for r in res["fige"]])
        texte += f" | pic d infectes : regle {pr:.1%}, forme {pf:.1%}"
        ok = ok and pf <= pr
    return ok, texte


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--groupes", default=",".join(EPREUVE))
    p.add_argument("--epoques", type=int, default=6)
    p.add_argument("--jours", type=int, default=20)
    p.add_argument("--procs", type=int, default=14)
    a = p.parse_args()
    noms = a.groupes.split(",")
    os.makedirs(DOSSIER, exist_ok=True)
    t0 = time.time()
    print(f"formation de {len(noms)} groupes en parallele : {noms}", flush=True)
    with Pool(min(len(noms), a.procs)) as pool:
        formes = pool.map(_former, [(n, a.epoques, a.jours) for n in noms])
    for nom, chemin, journal in formes:
        print(f"{nom:13s} forme en {time.time() - t0:5.0f} s | " +
              " ".join(f"e{j['epoque']}:{j['recompense_de_l_epoque']}" for j in journal), flush=True)

    taches = []
    for nom, chemin, _ in formes:
        ep = EPREUVE[nom]
        if nom == "fraudeurs":
            for g in EXAMEN:
                taches += [(nom, ep, g, "fige", chemin, 1.0), (nom, ep, g, "fige", chemin, 4.0),
                           (nom, ep, g, "regle", None, 1.0)]
            continue
        for g in EXAMEN:
            taches += [(nom, ep, g, "regle"), (nom, ep, g, "hasard"), (nom, ep, g, "fige", chemin)]
            if nom in ("commerce", "voyageurs"): taches.append((nom, ep, g, "aveugle"))
    with Pool(a.procs) as pool:
        resultats = pool.map(_jouer, taches)
    par_groupe = {}
    for t, r in zip(taches, resultats):
        cle = r["mode"] + (f"@{int(r['intensite'])}" if t[0] == "fraudeurs" and r["mode"] == "fige" else "")
        par_groupe.setdefault(t[0], {}).setdefault(cle, []).append(r)
    verdicts = {}
    for nom in noms:
        ok, texte = juger(nom, par_groupe[nom])
        verdicts[nom] = {"retenu": ok, "detail": texte}
        cons = max(r["conservation"] for m in par_groupe[nom].values() for r in m)
        print(f"{'RETENU ' if ok else 'REFUSE '} {nom:13s} {texte} | conservation {cons:.1e}", flush=True)
    with open(os.path.join(DOSSIER, "qualification_tous.json"), "w") as f:
        json.dump({"verdicts": verdicts, "resultats": par_groupe}, f, indent=1, default=str)
    print(f"termine en {time.time() - t0:.0f} s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
