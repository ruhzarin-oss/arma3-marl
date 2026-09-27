"""PORTE DES DEVISES ( 27/09, HMT-131, ecrite avant la mesure ) : toute sortie d argent vers l etranger demande ses
devises a la banque centrale ( exterieur.payer_en_devises, ou les imports du domaine 7 ). Dans la guerre des iles, 21
paiements partaient sans elles : les reserves de Malden passaient de +126 a -11 millions d euros, les imports de
nourriture, eux controles, ne recevaient plus rien - 41 260 morts de faim ; 41 089 a Stratis.

D1 L INVARIANT : une Stratis de l archipel ( graine 1, echelle 20 ) dont la banque centrale n a plus un euro ( reserves
   mises a zero au jour 3 ), 30 jours : a CHAQUE pas, les reserves ( lues sans les ranger, _dispo_euros ) ne passent
   jamais sous le plancher du controle ( a un millieme d euro pres ) ; le controle a mordu ( devises_refusees > 0 ) ; la
   conservation tient ( registre : l argent, CHAQUE bien en stock et les objets du parc - elle prouve que rien ne nait
   ni ne disparait hors du grand livre, pas a elle seule qu un import non paye n arrive pas : c est D5 ).
D2 LE CONTROLE POSITIF : le meme monde, ou UN paiement repasse en direct ( le fioul des centrales du domaine 11 :
   payer_l_exterieur au lieu de payer_en_devises ) : les reserves passent sous le plancher. La porte sait echouer.
D3 RIEN NE CHANGE TANT QUE LES RESERVES SUFFISENT : la meme Stratis sans y toucher, 10 jours : aucune devise refusee.
D4 PLUSIEURS PAIEMENTS DU MEME PAS : reserves posees a 2,5 paiements, dix paiements a la suite ( sans pas entre eux ) :
   2,5 paiements passent, 7,5 sont refuses, les reserves ne passent pas sous le plancher.
D5 CE QUI N EST PAS PAYE N ARRIVE PAS : dans le monde de D1, la valeur du combustible entre aux cuves ( quantites du
   grand livre x prix d import du domaine 11 ) egale ce qui a ete paye a l etranger pour lui ( a 1e-6 pres ).

   python -m monde.porte_devises"""
import sys, time
from monde.archipel import creer_ile
from monde.pays import d07_exterieur as X

TOL = 1e-3


def _refusees(J, etat):
    c = J.comptes.get("devises_refusees")
    v = c[1] if c else 0.0
    if v < etat[1]: etat[0] += etat[1]                       # la cloture du jour a remis le compteur a zero
    etat[1] = v
    return etat[0] + etat[1]


def jouer(jours, stress, fuite=False, livraisons=None):
    from monde.socle import comptes as CP
    orig = X.payer_en_devises; imp0, pay0 = CP.GrandLivre.importer, CP.GrandLivre.payer_l_exterieur
    if livraisons is not None:
        def importer(self, stock, b, q, motif):
            r = imp0(self, stock, b, q, motif)
            if motif == "import_combustible" and "cat" in livraisons:          # au prix du moment : le prix mondial bouge
                livraisons["recu"].append(q * livraisons["cat"][livraisons["noms"][b]].prix_monde * (1.0 + livraisons["fret"]))
            return r
        def payer(self, de, montant, motif):
            r = pay0(self, de, montant, motif)
            if motif == "import_combustible": livraisons["paye"] += r
            return r
        CP.GrandLivre.importer, CP.GrandLivre.payer_l_exterieur = importer, payer
    if fuite:
        def direct(p, de, montant, motif, essentiel=False):
            if motif == "import_combustible": return p.socle.livre.payer_l_exterieur(de, montant, motif)
            return orig(p, de, montant, motif, essentiel)
        X.payer_en_devises = direct
    try:
        w = creer_ile("Stratis", 1, 20.0); p = w.pays; e = X._ext(p); J = p.socle.journal
        if livraisons is not None:
            from monde.pays import d11_energie as E11
            livraisons.update(cat=p.socle.catalogue, noms=p.domaine("energie").noms, fret=E11.FRET_IMPORT, paye=0.0)
        pire, refus, etat = float("inf"), 0.0, [0.0, 0.0]
        combustible = [0.0]
        for k in range(jours * 144):
            if stress and k == 3 * 144:
                X.reserves_de_change(p); e.reserves_euros = X.PLANCHER_RESERVES
            w.pas_suivant()
            if not stress or k >= 3 * 144:
                pire = min(pire, X._dispo_euros(p, e))
            refus = _refusees(J, etat)
        return {"pire_dispo_euros": round(pire, 3), "devises_refusees": round(refus, 1), "reserves_fin": round(float(X.reserves_de_change(p)[0]), 1),
                "conservation": bool(p.socle.conservation.tenue()[0])}
    finally:
        X.payer_en_devises = orig; CP.GrandLivre.importer, CP.GrandLivre.payer_l_exterieur = imp0, pay0


def meme_pas(n=10, part=2.5):
    """D4 : dix paiements a la suite, sans pas entre eux, reserves posees a 2,5 paiements."""
    w = creer_ile("Stratis", 1, 20.0); p = w.pays; e = X._ext(p); g = w.gouv
    for _ in range(144): w.pas_suivant()
    un = g.caisse / (4.0 * n)                                    # en monnaie de l ile ; la caisse les paie tous
    X.reserves_de_change(p); e.reserves_euros = X.PLANCHER_RESERVES + part * un * e.taux
    payes = [X.payer_en_devises(p, g, un, "import_combustible") for _ in range(n)]
    return {"payes_en_paiements": round(sum(payes) / un, 6), "pire_dispo_euros": round(X._dispo_euros(p, e), 6),
            "entiers": sum(1 for x in payes if x >= un * (1 - 1e-12)), "partiels": sum(1 for x in payes if 1e-9 * un < x < un * (1 - 1e-12)),          # un reste d arrondi n est pas un paiement
            "restes": sum(1 for x in payes if 0 < x <= 1e-9 * un)}


def main():
    t0 = time.time(); ok = {}
    liv = {"recu": [], "paye": 0.0}
    d1 = jouer(30, True, livraisons=liv); print("   D1 invariant :", d1, flush=True)
    ok["D1 les reserves ne passent jamais sous le plancher, a chaque pas ; le controle a mordu ; conservation"] = (
        d1["pire_dispo_euros"] >= -TOL and d1["devises_refusees"] > 0 and d1["conservation"])
    d2 = jouer(30, True, fuite=True); print("   D2 controle positif ( le fioul en direct ) :", d2, flush=True)
    ok["D2 controle positif : un paiement direct fait passer les reserves sous le plancher"] = d2["pire_dispo_euros"] < -TOL
    d3 = jouer(10, False); print("   D3 sans stress :", d3, flush=True)
    ok["D3 reserves suffisantes : aucune devise refusee ; conservation"] = d3["devises_refusees"] == 0 and d3["conservation"]
    d4 = meme_pas(); print("   D4 dix paiements du meme pas :", d4, flush=True)
    ok["D4 dix paiements du meme pas : 2,5 passent ( 2 entiers, 1 partiel ), reserves au plancher"] = (
        abs(d4["payes_en_paiements"] - 2.5) < 1e-6 and d4["entiers"] == 2 and d4["partiels"] == 1 and d4["pire_dispo_euros"] >= -TOL)
    valeur = sum(liv["recu"])                 # les cuves comptent a l index du domaine 11 ( E.ids ), au prix du moment
    print(f"   D5 combustible : recu {valeur:,.2f} , paye {liv['paye']:,.2f} ( {len(liv['recu'])} livraisons )", flush=True)
    ok["D5 le combustible recu vaut ce qui a ete paye ( rien n arrive sans devises )"] = (
        len(liv["recu"]) > 0 and abs(valeur - liv["paye"]) <= 1e-6 * max(1.0, liv["paye"]))
    for k, v in ok.items(): print(("PASSE  " if v else "ECHOUE ") + k)
    print(f"PORTE DES DEVISES : {'FRANCHIE' if all(ok.values()) else 'REFUSEE'} ( {time.time() - t0:.0f} s )")
    return 0 if all(ok.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
