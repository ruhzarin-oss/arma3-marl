"""LES SOLDATS, HABITANTS JUSQU AU BOUT ( Arma a fond, etape 3, HMT-194 ).

3a, les blesses, ALIGNEE le 02/10 sur le chemin du domaine 27 ( `_traiter_pertes` ) : un soldat au front dont le
dommage relu dans Arma ( guerre/moteur.suivre ) atteint SEUIL_EVAC ( CHOIX ) est EVACUE par le domaine 26 AVANT que sa
lesion soit posee ( sinon le soin civil du moteur le prendrait ) :
  1. le lieu de l evacuation est le lieu de la carte le plus proche de sa derniere position dans Arma ( d26._lieu_proche ;
     a defaut, sa base ) ; il n est plus absent ( resident, poste maison pour sa sortie de l hopital ) ;
  2. s il peut survivre ( ISS < 75 ), d26.evacuer : l helicoptere libre et son kerosene, sinon l ambulance militaire de
     sa base, vers l hopital militaire du domaine 17 ;
  3. le domaine 16 le blesse : balistique, cause combat, ISS = 9 + ( dommage - 0,5 ) / 0,5 x 66 ( CHOIX : 9 au seuil
     d hospitalisation du domaine 16, 75 au maximum ; tant qu Arma ne rend pas la zone touchee, on ne passe pas par
     d25.blesser_soldat ) ; le soin, la mort de la phase aigue ou la guerison suivent le domaine 16 ;
  4. son tri d admission est recalcule ( domaine 17 : ESI, ISS ), comme au domaine 27 ;
  5. l unite ramasse ses coups ( guerre/logistique.rendre : la reserve du domaine 27 est rendue ).
Un blesse n est evacue qu une fois."""
from monde import population as PO
from monde.pays import d16_medecine as MED, d17_hopitaux as HM, d25_armee as A, d26_armee_soutien as S
from . import logistique as LO, moteur as GM

SEUIL_EVAC = 0.5


def iss_de(degats):
    """L ISS d un dommage d Arma ( CHOIX, lineaire de 9 au seuil a 75 a 1 )."""
    return int(round(min(75.0, max(9.0, 9.0 + (float(degats) - SEUIL_EVAC) / (1.0 - SEUIL_EVAC) * 66.0))))


def lieu_du_front(w, s):
    """Le lieu d ou part l evacuation : le plus proche de sa derniere position vue, sinon sa base, sinon son domicile."""
    p = w.pays; carte = w.carte; i = int(s["i"])
    r = int(p.col("habitant", "ar_rang")[i]) if p.a("armee") else -1
    base = carte.par_n[int(A._dom(p).eff["base"][r])] if r >= 0 else None
    if s.get("x") is not None and p.a("armee_soutien"):
        ile = carte.iles.index((base or carte.gouvernement).ile)
        return carte.par_n[S._lieu_proche(p, S._dom(p), float(s["x"]), float(s["y"]), ile)].id
    if base is not None: return base.id
    dom = getattr(w.habitants[i], "domicile", None)
    return dom.id if dom is not None else carte.gouvernement.id


def evacuer_blesses(w, releves=None):
    """releves : [ ( numero, dommage ) ] ; sans eux, le dommage suivi au front. Rend [ ( numero, ISS, cle d affection,
    moyen d evacuation ou None ) ]."""
    p = w.pays; f = GM._front(w); t = w.table; carte = w.carte; out = []
    items = releves if releves is not None else [(k, s.get("degats", 0.0) or 0.0) for k, s in sorted(f.items())]
    for num, dg in items:
        s = f.get(int(num))
        if s is None or s["etat"] in ("mort", "blesse") or float(dg) < SEUIL_EVAC: continue
        i = int(s["i"]); h = w.habitants[i]
        if not h.vivant: continue
        iss = iss_de(dg)
        lieu = lieu_du_front(w, s)
        w.absents.pop(i, None); t.statut[i] = PO.RESIDENT; t.poste[i] = PO.CODE_POSTE["maison"]
        t.lieu[i] = carte.lieux[lieu].n
        ev = S.evacuer(p, i, lieu=lieu) if iss < 75 and p.a("armee_soutien") else None
        cle = MED.blesser(p, h, "balistique", iss, "combat") if p.a("medecine") else None
        if ev is not None and t.vivant[i]:
            ps = ev["passage"]; hab = PO.Habitant(t, i)
            ps.esi = HM.esi(p, hab); ps.iss = HM._iss(p, hab)
            p.compter("evacuation_tactique")
        p.compter("blesse_au_combat")
        LO.rendre(w, num)
        moyen = ev["moyen"] if ev else None
        s.update(etat="blesse", blesse_pas=int(w.pas), iss=iss, evacuation=moyen, lieu_evacuation=lieu)
        out.append((int(num), iss, cle, moyen))
    if out: w.noter("evacuation", blesses=len(out))
    return out
