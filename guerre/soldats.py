"""LES SOLDATS, HABITANTS JUSQU AU BOUT ( Arma a fond, etape 3, HMT-194 ).

3a, les blesses : un soldat au front dont le dommage relu dans Arma ( guerre/moteur.suivre ) atteint SEUIL_EVAC ( CHOIX )
est EVACUE : il rentre sur son ile ( n est plus absent, chez lui ), et le domaine 16 le blesse ( balistique, cause
combat, ISS = 9 + ( dommage - 0,5 ) / 0,5 x 66, CHOIX : 9 au seuil d hospitalisation du domaine 16, 75 au maximum ) ;
le soin, la mort de la phase aigue ou la guerison suivent les regles du domaine 16. Ses munitions restent au front, dans
le stock de son unite ( guerre/logistique ). Un blesse n est evacue qu une fois."""
from monde import population as PO
from . import logistique as LO, moteur as GM

SEUIL_EVAC = 0.5


def iss_de(degats):
    """L ISS d un dommage d Arma ( CHOIX, lineaire de 9 au seuil a 75 a 1 )."""
    return int(round(min(75.0, max(9.0, 9.0 + (float(degats) - SEUIL_EVAC) / (1.0 - SEUIL_EVAC) * 66.0))))


def evacuer_blesses(w, releves=None):
    """releves : [ ( numero, dommage ) ] ; sans eux, le dommage suivi au front. Rend [ ( numero, ISS, cle d affection ) ]."""
    p = w.pays; f = GM._front(w); t = w.table; out = []
    items = releves if releves is not None else [(k, s.get("degats", 0.0) or 0.0) for k, s in sorted(f.items())]
    for num, dg in items:
        s = f.get(int(num))
        if s is None or s["etat"] in ("mort", "blesse") or float(dg) < SEUIL_EVAC: continue
        i = s["i"]; h = w.habitants[i]
        if not h.vivant: continue
        w.absents.pop(i, None); t.statut[i] = PO.RESIDENT; t.poste[i] = PO.CODE_POSTE["maison"]
        dom = getattr(h, "domicile", None)
        if dom is not None: t.lieu[i] = dom.n
        iss = iss_de(dg)
        cle = None
        if p is not None and p.a("medecine"):
            from monde.pays import d16_medecine as MED
            cle = MED.blesser(p, h, "balistique", iss, "combat")
        LO._L(w)["porte"].pop(int(num), None)            # ses munitions restent au front, sans porteur
        s.update(etat="blesse", blesse_pas=int(w.pas), iss=iss)
        out.append((int(num), iss, cle))
    if out: w.noter("evacuation", blesses=len(out))
    return out
