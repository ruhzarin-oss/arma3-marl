"""PORTE DE L ENREGISTREUR ( 26/09 ) : enregistrer ne change pas le monde, et l enregistrement est complet.

  E1  identite : l archipel enregistre ( sequentiel, puis parallele ) a les memes empreintes, jour par jour, que
      l archipel nu ;
  E2  argent et biens : les lignes enregistrees, sommees par ( motif, classe du payeur, classe du receveur ), retombent
      au centime et au nombre pres sur le grand livre de chaque ile ( ses clotures + le jour en cours ) ;
  E3  choix et notes : autant de choix enregistres que de decisions prises, autant de notes que de notes murees ;
  E4  evenements : autant de lignes que d evenements notes ( moteur et journal du socle ) ;
  E5  photos : une photo des habitants par jour, une ligne par habitant ;
  controle positif : une ligne d argent retiree de la lecture -> E2 echoue ; un choix retire -> E3 echoue.

   python -m monde.porte_enregistreur"""
import os, shutil, sys, tempfile
from collections import defaultdict
import pyarrow.parquet as pq
from . import config as C
from .archipel import Archipel
from .socle import comptes as CO, journal as JO

JOURS = 3
ECHELLE = 2.0
ILES = C.ILES_ARCHIPEL


def lire(dossier, ile, table):
    d = os.path.join(dossier, ile, table)
    if not os.path.isdir(d): return None
    return pq.read_table(d).to_pylist()


def main():
    ok = True
    def dire(passe, texte):
        nonlocal ok
        ok &= passe
        print(f"{'PASSE ' if passe else 'ECHOUE'} {texte}", flush=True)

    # --- les clotures du grand livre et du journal, captees pendant le monde enregistre
    clotures = defaultdict(list); bilans = defaultdict(list)
    o_livre, o_journal = CO.GrandLivre.cloturer_jour, JO.Journal.cloturer_jour
    def livre_(self):
        r = o_livre(self); clotures[id(self)].append(r); return r
    def journal_(self, jour):
        r = o_journal(self, jour); bilans[id(self)].append(r); return r

    # E1 : nu, puis enregistre ( sequentiel )
    nu = Archipel(echelle=ECHELLE, ouvert=True, parallele=False)
    emp_nu = []
    for _ in range(JOURS): nu.jours(1); emp_nu.append(nu.empreintes())
    nu.fermer()

    dossier = tempfile.mkdtemp(prefix="porte_enreg_", dir="/mnt/data/hmt")
    CO.GrandLivre.cloturer_jour, JO.Journal.cloturer_jour = livre_, journal_
    try:
        arc = Archipel(echelle=ECHELLE, ouvert=True, parallele=False, enregistrer=dossier)
        base = {}
        for n, i in arc.iles.items():
            p = i.w.pays
            base[n] = {"dec": {k: d.n_decisions for k, d in p.decideurs.items()},
                       "notes": {k: sum(s[0] for s in d.stats.values()) for k, d in p.decideurs.items()},
                       "ev": len(i.w.evenements),
                       # ce que l installation a deja range avant le branchement ( compte dans la premiere cloture )
                       "argent": {k: list(v) for k, v in p.socle.livre.jour_argent.items()},
                       "biens": dict(p.socle.livre.jour_biens),
                       "journal": sum(p.socle.journal.individuels_jour.values())}
        emp_enr = []
        for _ in range(JOURS): arc.jours(1); emp_enr.append(arc.empreintes())
        arc.fermer()
    finally:
        CO.GrandLivre.cloturer_jour, JO.Journal.cloturer_jour = o_livre, o_journal
    ecarts = [(j + 1, n) for j in range(JOURS) for n in ILES if emp_nu[j][n] != emp_enr[j][n]]
    dire(not ecarts, f"E1 enregistrer ne change pas le monde ( sequentiel, {JOURS} jours, six iles ) : ecarts {ecarts[:4]}")

    # E1 bis : parallele enregistre = nu
    dossier_p = tempfile.mkdtemp(prefix="porte_enreg_p_", dir="/mnt/data/hmt")
    par = Archipel(echelle=ECHELLE, ouvert=True, parallele=True, enregistrer=dossier_p)
    emp_par = []
    for _ in range(JOURS): par.jours(1); emp_par.append(par.empreintes())
    par.fermer()
    ecarts = [(j + 1, n) for j in range(JOURS) for n in ILES if emp_nu[j][n] != emp_par[j][n]]
    dire(not ecarts, f"E1 parallele enregistre = nu : ecarts {ecarts[:4]}")
    dire(all(os.path.isdir(os.path.join(dossier_p, n, "argent")) for n in ILES), "E1 chaque processus d ile ecrit son dossier")

    def verifier(sabot_argent=False, sabot_choix=False, bavard=True):
        bon = True
        for n, i in arc.iles.items():
            w = i.w; p = w.pays; L = p.socle.livre
            # E2 argent
            attendu = defaultdict(lambda: [0.0, 0])
            for r in clotures[id(L)]:
                for m, pa, re, s, k in r["argent"]: attendu[(m, pa, re)][0] += s; attendu[(m, pa, re)][1] += k
            for (m, pa, re), (s, k) in L.jour_argent.items(): attendu[(m, pa, re)][0] += s; attendu[(m, pa, re)][1] += k
            for key, (s, k) in base[n]["argent"].items(): attendu[key][0] -= s; attendu[key][1] -= k
            lu = lire(dossier, n, "argent") or []
            if sabot_argent and lu: lu = lu[1:]
            vu = defaultdict(lambda: [0.0, 0])
            for r in lu: v = vu[(r["motif"], r["payeur_classe"], r["receveur_classe"])]; v[0] += r["montant"]; v[1] += 1
            mauvais = [k for k in set(attendu) | set(vu)
                       if attendu[k][1] != vu[k][1] or abs(attendu[k][0] - vu[k][0]) > 1e-6 * max(1.0, abs(attendu[k][0]))]
            if bavard and mauvais: print(f"      argent : {[(k, attendu[k], vu[k]) for k in mauvais[:3]]}")
            # E2 biens
            att_b = defaultdict(float)
            for r in clotures[id(L)]:
                for nat, m, b, q in r["biens"]: att_b[(nat, m, b)] += q
            for (nat, m, b), q in L.jour_biens.items(): att_b[(nat, m, L.catalogue.biens[b].nom)] += q
            for (nat, m, b), q in base[n]["biens"].items(): att_b[(nat, m, L.catalogue.biens[b].nom)] -= q
            vu_b = defaultdict(float)
            for r in lire(dossier, n, "biens") or []:
                b = r["bien"]; nom = L.catalogue.biens[int(b)].nom if b.isdigit() else b
                vu_b[(r["nature"], r["motif"], nom)] += r["quantite"]
            mauvais_b = [k for k in set(att_b) | set(vu_b) if abs(att_b[k] - vu_b[k]) > 1e-6 * max(1.0, abs(att_b[k]))]
            if bavard and mauvais_b: print(f"      biens : {[(k, att_b[k], vu_b[k]) for k in mauvais_b[:3]]}")
            # E3 choix et notes
            dec = lire(dossier, n, "decisions") or []
            if sabot_choix and dec: dec = dec[1:]
            nd = defaultdict(int)
            for r in dec: nd[r["point"]] += 1
            att_d = {d.point.nom: d.n_decisions - base[n]["dec"][k] for k, d in p.decideurs.items()}
            mauvais_d = [k for k in set(att_d) | set(nd) if att_d.get(k, 0) != nd.get(k, 0)]
            nn = defaultdict(int)
            for r in lire(dossier, n, "notes") or []: nn[r["point"]] += 1
            att_n = {d.point.nom: sum(s[0] for s in d.stats.values()) - base[n]["notes"][k] for k, d in p.decideurs.items()}
            mauvais_n = [k for k in set(att_n) | set(nn) if att_n.get(k, 0) != nn.get(k, 0)]
            # E4 evenements
            ev = lire(dossier, n, "evenements") or []
            n_mot = sum(1 for r in ev if r["source"] == "moteur"); n_jou = sum(1 for r in ev if r["source"] == "journal")
            J = p.socle.journal
            att_jou = sum(sum(b["individuels"].values()) for b in bilans[id(J)]) + sum(J.individuels_jour.values()) - base[n]["journal"]
            att_mot = len(w.evenements) - base[n]["ev"]
            # E5 photos
            ph = pq.read_table(os.path.join(dossier, n, "habitants")).select(["jour"]).to_pydict()["jour"] if os.path.isdir(os.path.join(dossier, n, "habitants")) else []
            jours_ph = sorted(set(ph))
            dm = os.path.join(dossier, n, "marches")
            ok_eco = os.path.isdir(dm) and all(
                pq.read_table(os.path.join(dm, f"jour={j:05d}")).num_rows == len(w.marches) for j in range(JOURS)) \
                and all(os.path.isdir(os.path.join(dossier, n, t, f"jour={j:05d}")) for t in ("entreprises", "etat") for j in range(JOURS))
            if bavard:
                print(f"   {n:8s} argent {len(lu):7,} lignes, {len(attendu)} cles, ecarts {len(mauvais)} | biens ecarts {len(mauvais_b)} | "
                      f"choix {len(dec):7,} ecarts {mauvais_d[:3]} | notes {sum(nn.values()):6,} ecarts {mauvais_n[:3]} | "
                      f"evenements moteur {n_mot}/{att_mot} journal {n_jou}/{att_jou} | photos jours {jours_ph} | economie {ok_eco}", flush=True)
            bon &= not mauvais and not mauvais_b and not mauvais_d and not mauvais_n and n_mot == att_mot \
                and n_jou == att_jou and jours_ph == list(range(JOURS)) and len(ph) >= JOURS * 1 and ok_eco
        return bon

    dire(verifier(), "E2-E5 l enregistrement retombe sur le grand livre, les decideurs, les journaux et les photos")
    dire(not verifier(sabot_argent=True, bavard=False), "controle positif : une ligne d argent en moins -> la porte echoue")
    dire(not verifier(sabot_choix=True, bavard=False), "controle positif : un choix en moins -> la porte echoue")
    taille = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(dossier) for f in fs)
    print(f"   ( {taille / 1e6:.1f} Mo pour six iles de {int(ECHELLE * 500)} habitants sur {JOURS} jours )")
    shutil.rmtree(dossier, ignore_errors=True); shutil.rmtree(dossier_p, ignore_errors=True)
    print(f"PORTE DE L ENREGISTREUR : {'FRANCHIE' if ok else 'REFUSEE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
