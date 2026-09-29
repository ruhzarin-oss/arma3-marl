"""PORTE DE PROVOQUER ( HMT-146, seuils ecrits avant le code, Plane ) : une catastrophe provoquee est vue par les
domaines qui lisent les catastrophes du jour comme une naturelle, le catalogue appelle les API des domaines, l archipel
transmet l ordre. Le domaine 8 seul a sa porte ( tests_d08_territoire.test_provoquer ) ; celle-ci est la porte ENTRE
domaines.
  1. Deux mondes jumeaux ( Altis, graine 146, securite civile, services publics, exterieur et leurs dependances ) ; l un
     recoit un seisme M 6,5 sous un village. Au jour 1 : des batiments endommages ( domaine 13 ; 0 dans le jumeau ) ;
     la securite civile l a vu ( 18 : seismes_vus ) ; au moins une ligne coupee ou une centrale en panne par le seisme
     ( 11 : journal, cause seisme ; 0 dans le jumeau ) ; des routes abimees ( 12 : c_choc plus grand que le jumeau ).
  2. Le catalogue, sur le monde provoque : un feu de foret ouvert ( 18 : en_cours ), 5 cas d une maladie ( 16 ), un
     groupe en panne ( 11 ), la ligne d un lieu encore alimente coupee ( 11 : journal, cause provoquee, effet >= 1 ligne ),
     celle de la capitale deja coupee plus longtemps par le seisme rendue telle ( effet = les lignes vraiment allongees ), les prix mondiaux de l energie
     multiplies par 2 ( 7 : a 1e-9 ) ; chaque ordre est au journal avec son jour. Falsificateurs : une maladie inconnue,
     un choc de x50 ( borne de d07 ), un feu hors de l ile levent ValueError sans rien noter.
  3. L archipel ( sequentiel, Altis ) : Ile.commande( « provoquer », ... ) rend la provocation notee et le seisme tombe.
   python -m monde.porte_provoquer"""
import sys, time
import numpy as np
from .pays import essais as T, d08_territoire as TER
from . import provoquer as PV, config as C

DOMAINES = ["securite_civile", "services_publics", "exterieur"]


def _evts(p, type_, **k):
    return [e for e in p.socle.journal.recents if e["type"] == type_ and all(e.get(a) == b for a, b in k.items())]


def _endommages(p):
    from .pays import d13_immobilier as IM
    B = IM._dom(p).B
    return int((B["dommage"][:B.n] > 0).sum())


def _routes(p):
    from .pays import d12_services_publics as SP
    return float(SP._sp(p).routes.c_choc.sum())


def porte_consommateurs():
    w0, p0 = T.monde(DOMAINES, graine=146); w1, p1 = T.monde(DOMAINES, graine=146)
    T1 = p1.domaine("territoire"); i = T1.iles.index("Altis")
    v0 = sorted(l for l, k in zip(T1.parcelles.lieu_id, T1.parcelles.ile.tolist()) if k == i)[0]
    r = PV.provoquer(w1, "seisme", "Altis", magnitude=6.5, lieu=v0, par="porte")
    T.jours(w0, 1); T.jours(w1, 1)
    S1, S0 = p1.domaine("securite_civile"), p0.domaine("securite_civile")
    vu18 = any(k[0] == 1 and abs(k[3] - 6.5) < 1e-9 for k in S1.seismes_vus) and not any(k[0] == 1 for k in S0.seismes_vus)
    d11 = lambda p: len([e for e in _evts(p, "coupure_ligne", cause="seisme") + _evts(p, "panne_centrale", cause="seisme") if e["jour"] == 1])
    n13 = (_endommages(p1), _endommages(p0)); n11 = (d11(p1), d11(p0)); r12 = (_routes(p1), _routes(p0))
    ok = n13[0] > 0 and n13[1] == 0 and vu18 and n11[0] >= 1 and n11[1] == 0 and r12[0] > r12[1]
    msg = (f"seisme M6,5 sous {v0} ( provocation {r['numero']} ) : batiments endommages {n13[0]} ( jumeau {n13[1]} ), "
           f"securite civile {vu18}, lignes et centrales {n11[0]} ( jumeau {n11[1]} ), usure des routes par choc "
           f"{r12[0]:.3f} ( jumeau {r12[1]:.3f} )")
    return ok, msg, (w1, p1, v0)


def porte_catalogue(w, p, v0):
    from .pays import d18_securite_civile as SC, d16_medecine as MD, d11_energie as EN
    cat = p.socle.catalogue
    en = [b for b in cat if b.famille == "energie" and b.nom != "electricite"]
    avant = {b.nom: b.prix_monde for b in en}
    cap = TER.provocations_en_attente  # ( lecture seule : rien en attente pour les natures immediates )
    feu = PV.provoquer(w, "incendie_foret", "Altis", lieu=v0, par="porte")
    ouvert = any(s[0] == feu["effet"] and s[1] == "foret" for s in SC.en_cours(p))
    epi = PV.provoquer(w, "epidemie", "Altis", maladie=MD.INFECTIEUSES[0], cas=5, par="porte")
    pan = PV.provoquer(w, "panne_centrales", "Altis", groupes=1, heures=48, par="porte")
    # 29/09, premiere passe : la ligne de la capitale, deja coupee ~5 jours par le seisme provoque, ne pouvait pas montrer
    # une coupure de 2 jours ( d11 garde la plus longue et ne note rien ). Le controle se fait sur un lieu ENCORE alimente ;
    # la capitale sert a voir que l effet rendu dit « deja coupee » ( 0 ligne allongee ).
    R = p.domaine("energie").par_ile["Altis"]; fin = w.pas + int(round(2 * C.PAS_PAR_JOUR))
    avec = {c.lieu for c in R.charges if c.lieu is not None}
    alimente = sorted(avec - {c.lieu for c in R.charges if c.lieu is not None and c.coupe_jusqu > w.pas})[0]
    lig = PV.provoquer(w, "coupure_ligne", "Altis", lieu=alimente, jours=2, par="porte")
    coupee = lig["effet"] >= 1 and len(_evts(p, "coupure_ligne", lieu=alimente, cause="provoquee")) >= 1
    capitale = p.domaine("territoire").capitale_ile[0]
    attendu = sum(1 for c in R.charges if c.lieu == capitale and c.coupe_jusqu < fin)
    deja = PV.provoquer(w, "coupure_ligne", "Altis", lieu=capitale, jours=2, par="porte")
    deja_vu = deja["effet"] == attendu and (attendu > 0) == bool(_evts(p, "coupure_ligne", lieu=capitale, cause="provoquee"))
    cho = PV.provoquer(w, "choc_prix", None, famille="energie", facteur=2.0, par="porte")
    rapport = max(abs(b.prix_monde / avant[b.nom] - 2.0) for b in en if avant[b.nom] > 0)
    n_avant = len(_evts(p, "provocation"))
    fautes = [("epidemie", "Altis", {"maladie": "peste_noire_inventee"}, "maladie inconnue"),
              ("choc_prix", None, {"famille": "energie", "facteur": 50.0}, "facteur"),
              ("incendie_foret", "Altis", {"lieu": "lieu_qui_n_existe_pas"}, "hors de Altis")]
    refus = 0
    for nat, ile, kw, motif in fautes:
        try: PV.provoquer(w, nat, ile, **kw)
        except ValueError as e: refus += motif in str(e)
    rien = len(_evts(p, "provocation")) == n_avant
    jours = all(e["jour_effet"] == p.jour for e in _evts(p, "provocation") if e["nature"] not in TER.NATURES_PROVOQUEES)
    ok = (ouvert and epi["effet"] == 5 and pan["effet"] == 1 and coupee and deja_vu and rapport <= 1e-9 and refus == len(fautes)
          and rien and jours and not cap(p))
    return ok, (f"feu de foret {feu['effet']} ouvert {ouvert} ; epidemie {epi['effet']} cas ; groupes en panne {pan['effet']} ; "
                f"ligne de {alimente} coupee {coupee} ( {lig['effet']} ) ; ligne de {capitale} deja coupee par le seisme : effet {deja['effet']} "
                f"pour {attendu} attendu(s) {deja_vu} ; prix de l energie x2 a {rapport:.1e} pres | falsificateurs "
                f"{refus}/{len(fautes)}, rien note {rien} ; jour d effet des ordres immediats {jours}")


def porte_archipel():
    from .archipel import Archipel
    arc = Archipel(iles=("Altis",), graine=146, echelle=1.0, parallele=False)
    try:
        r = arc.commande("Altis", "provoquer", "seisme", "Altis", {"magnitude": 6.0, "par": "porte"})
        arc.jours(1)
        p = arc.iles["Altis"].w.pays
        tombe = len(_evts(p, "seisme", provoque=r["numero"])) >= 1
        ok = r["nature"] == "seisme" and r["par"] == "porte" and tombe
        return ok, f"commande de l archipel : provocation {r['numero']} ( jour d effet {r['jour_effet']} ), le seisme tombe {tombe}"
    finally:
        arc.fermer()


def main():
    t0 = time.perf_counter(); res = []
    ok1, m1, (w, p, v0) = porte_consommateurs(); res.append(ok1); print(f"{'PASSE' if ok1 else 'ECHOUE'}  consommateurs : {m1}", flush=True)
    ok2, m2 = porte_catalogue(w, p, v0); res.append(ok2); print(f"{'PASSE' if ok2 else 'ECHOUE'}  catalogue : {m2}", flush=True)
    ok3, m3 = porte_archipel(); res.append(ok3); print(f"{'PASSE' if ok3 else 'ECHOUE'}  archipel : {m3}", flush=True)
    print(f"PORTE DE PROVOQUER : {'FRANCHIE' if all(res) else 'REFUSEE'} ( {sum(res)}/{len(res)}, {time.perf_counter() - t0:.0f} s )")
    return 0 if all(res) else 1


if __name__ == "__main__":
    sys.exit(main())
