"""PORTE DE L IDENTITE ( archipel, phase C ; ecrite avant la mesure ) : carte d identite et passeport.

1. Unicite : apres 30 jours de vie ( naissances comprises ), chaque numero d archipel est unique, porte le code de l
   ile, et la nationalite est celle de l ile ; controle positif : un numero duplique a la main est vu.
2. Deux iles ne donnent jamais le meme numero.
3. Le passeport : demande -> paye par le menage a l Etat ( au centime ), pas valide avant le delai, valide apres,
   expiration a la date prevue ; une deuxieme demande rend « valide ».
4. Refus : un menage qui ne peut pas payer n est pas debite.
5. Au depart, une part des adultes proche de PART_PASSEPORT_DEPART a un passeport valide.
6. Avec le socle et tous les domaines : la conservation tient apres des demandes, et le motif est declare.

   python -m monde.porte_identite"""
import sys
import numpy as np
from . import monde as W, tests as T, config as C, carte as K
from .pays import pays as P
from .porte_domaines import LIVRES


def unicite(w):
    t, n = w.table, w.table.n
    nia = t.nia[:n]
    return (len(np.unique(nia)) == n and (nia >= 0).all() and ((nia >> C.BITS_NUMERO_LOCAL) == t.code_ile).all()
            and (t.nationalite[:n] == t.code_ile).all())


def main():
    ok = {}
    w = W.Monde(iles=("Tanoa",), echelle=4); P.installer(w, LIVRES)
    n0 = w.table.n
    T.jours(w, 30)
    ok["1 unicite apres 30 jours"] = unicite(w) and w.table.n > n0
    nes = w.table.n - n0
    t = w.table
    sauve = int(t.nia[1]); t.nia[1] = t.nia[0]
    ok["1 controle positif : doublon vu"] = not unicite(w)
    t.nia[1] = sauve
    m = W.Monde(iles=("Malden",), echelle=1)
    ok["2 deux iles, aucun numero commun"] = not (set(m.table.nia[:m.table.n].tolist()) & set(t.nia[:t.n].tolist()))
    # 3. le passeport
    cands = [i for i in range(t.n) if t.vivant[i] and t.passeport[i] < 0 and t.age[i] >= 18
             and w.habitants[i].menage is not None and w.habitants[i].menage.caisse > 10 * C.FRAIS_PASSEPORT]
    h = w.habitants[cands[0]]
    mg = h.menage
    c0, g0 = mg.caisse, w.gouv.caisse
    r1 = w.demander_passeport(h)
    paye = abs((c0 - mg.caisse) - C.FRAIS_PASSEPORT) < 1e-9 and abs((w.gouv.caisse - g0) - C.FRAIS_PASSEPORT) < 1e-9
    avant = w.passeport_valide(h)
    T.jours(w, C.DELAI_PASSEPORT_J + 1)
    apres = w.passeport_valide(h)
    fin = int(t.passeport_fin_j[h.id]) - int(t.passeport_emis_j[h.id])
    ok["3 passeport paye, attendu, valide"] = (r1 == "demande" and paye and not avant and apres
                                              and fin == C.VALIDITE_PASSEPORT_ANS[1] * 365
                                              and w.demander_passeport(h) == "valide")
    # 4. le refus
    pauvres = [i for i in range(t.n) if t.vivant[i] and t.passeport[i] < 0 and w.habitants[i].menage is not None
               and w.habitants[i].menage.caisse < C.FRAIS_PASSEPORT and i not in w.passeports_en_cours]
    if pauvres:
        p = w.habitants[pauvres[0]]; c = p.menage.caisse
        ok["4 refus sans debit"] = w.demander_passeport(p) == "refuse" and p.menage.caisse == c
    else:
        ok["4 refus sans debit"] = True; print("   ( aucun menage sous le prix du passeport dans ce monde : refus non exerce )")
    # 5. la part de depart
    z = W.Monde(iles=("Sara",), echelle=4)
    tz, nz = z.table, z.table.n
    adultes = (tz.vivant[:nz] == 1) & (tz.age[:nz] >= 18)
    part = float(((tz.passeport[:nz] >= 0) & (tz.passeport_fin_j[:nz] > 0) & adultes).sum() / adultes.sum())
    ok["5 part de depart"] = abs(part - C.PART_PASSEPORT_DEPART) < 0.05
    # 6. conservation et motif, avec le socle
    for i in cands[1:40]: w.demander_passeport(w.habitants[i])
    T.jours(w, C.DELAI_PASSEPORT_J + 1)
    tenue, msg = w.pays.socle.conservation.tenue()
    ok["6 conservation et motif declare"] = tenue and "passeport" not in w.pays.socle.livre.non_declares
    for k, v in ok.items(): print(f"{'PASSE ' if v else 'ECHOUE'} {k}")
    print(f"   ( {nes} naissances en 30 jours ; part de depart mesuree {part:.1%} ; conservation : {msg[:80]} )")
    passe = all(ok.values())
    print(f"PORTE DE L IDENTITE : {'FRANCHIE' if passe else 'ECHOUEE'}")
    return 0 if passe else 1


if __name__ == "__main__":
    sys.exit(main())
