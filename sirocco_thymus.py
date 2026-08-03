"""sirocco_thymus — LA DOUBLE SELECTION. Brique ISOLEE, rien n'est branche.

Le fait le plus contre-intuitif de l'immunologie : environ 95 % des lymphocytes T fabriques
sont DETRUITS avant de servir. Pas parce qu'ils sont mauvais contre l'ennemi — parce qu'ils
reagissent au SOI. L'immunite ne consacre pas l'essentiel de son effort a reconnaitre
l'ennemi, mais a ne PAS reagir a ce qui n'est pas une menace.

Le thymus fait DEUX selections, et l'ordre compte :

  POSITIVE   le lymphocyte doit savoir reconnaitre. Celui qui ne reagit a rien est inutile.
  NEGATIVE   puis il ne doit pas reagir au soi. Celui qui attaque l'hote est detruit.

Ne garder que la negative selectionnerait des SOURDS — une politique avec un seuil enorme
passe l'epreuve du soi haut la main, et ne sert a rien. C'est l'anergie, une des quatre
pathologies du banc. Les deux epreuves ensemble, pas l'une sans l'autre.

CE QUE CA TRAITE, CONCRETEMENT — et ce n'est pas theorique :

`FiredNear` se declenche sur TOUT tir proche, y compris celui de ton propre binome. Un agent
dont le camarade tire a trois metres recevra un FROLEMENT a chaque coup. S'il se plaque a
chaque fois, l'escouade est inutilisable des le premier contact. C'est l'auto-immunite
canonique de SIROCCO, et elle est CERTAINE de se produire — pas hypothetique.

Le remede n'est pas une penalite dans une recompense : une politique qui se plaque parfois
sur son binome reste une politique qui se plaque sur son binome. Le thymus l'elimine par
construction, avant l'entrainement.

smoke : python sirocco_thymus.py smoke
"""
import sys
import torch

from sirocco import AlarmeLocale, BRUIT, CONTACT, FROLEMENT, IMPACT, PERTE
from sirocco_cascade import Cascade, REFLEXE

SITUATIONS = ["calme", "ami_tire_pres", "ami_tire_loin", "bruit_lointain", "ami_touche"]


class Candidat:
    """Une politique candidate : des parametres de cascade + une regle de SIGNALEMENT.

    `filtre_iff` est la variable qu'on met a l'epreuve : la politique ignore-t-elle un
    frolement dont le tireur est un ami ? C'est un seul booleen, et il decide si l'escouade
    tient debout ou se couche des que quelqu'un ouvre le feu."""

    def __init__(self, nom, s1=0.25, filtre_iff=True, attenuation_ami=0.0):
        self.nom = nom; self.s1 = float(s1)
        self.filtre_iff = bool(filtre_iff)
        self.att = float(attenuation_ami)      # si pas de filtre franc : part du signal gardee

    def _neuf(self, dev, spp):
        al = AlarmeLocale(1, 1, dev, sec_par_pas=spp)
        cas = Cascade(1, 1, dev, sec_par_pas=spp, s1=self.s1)
        return al, cas

    def signaler(self, al, canal, moi, srcx, srcy, inten, amie):
        """Le seul endroit ou la politique decide quelque chose avant la cascade."""
        if amie:
            if self.filtre_iff: return               # on ignore franchement
            inten = inten * self.att                 # sinon on ne fait qu'attenuer
            if inten <= 0.0: return
        al.signaler(canal, moi, moi, srcx, srcy, inten)

    def __repr__(self):
        return "<%s s1=%.2f iff=%s att=%.2f>" % (self.nom, self.s1, self.filtre_iff, self.att)


class Thymus:
    def __init__(self, device, sec_par_pas=None, taux_max=0.02, pas_par_situation=40,
                 delai_positif_s=2.0):
        if sec_par_pas is None or sec_par_pas <= 0:
            raise ValueError("sec_par_pas manquant (les epreuves sont chronometrees en SECONDES).")
        self.dev = device; self.spp = float(sec_par_pas)
        self.taux_max = float(taux_max); self.T = int(pas_par_situation)
        self.p_positif = max(1, int(round(delai_positif_s / self.spp)))

    # ---- les epreuves -------------------------------------------------------------------
    @torch.no_grad()
    def _jouer(self, cand, scenario):
        """Joue un scenario et rend (taux de reaction, premier pas de reaction ou -1)."""
        dev = self.dev
        al, cas = cand._neuf(dev, self.spp)
        moi = torch.zeros(1, 1, device=dev)
        n_reac = 0; premier = -1
        for t in range(self.T):
            al.pas()
            for (canal, sx, sy, inten, amie) in scenario(t):
                cand.signaler(al, canal, moi,
                              torch.full((1, 1), float(sx), device=dev),
                              torch.full((1, 1), float(sy), device=dev), inten, amie)
            r = cas.pas(al.danger(), moi, moi, al.menace()[..., :2])
            if int(r["etat"][0, 0]) == REFLEXE:
                n_reac += 1
                if premier < 0: premier = t
        return n_reac / self.T, premier

    def _scenario(self, nom):
        """Scenarios BENINS : aucune menace reelle pour l'agent. Toute reaction est une faute."""
        if nom == "calme":
            # controle : si un candidat reagit ICI, c'est le banc qu'il faut suspecter
            return lambda t: []
        if nom == "ami_tire_pres":
            # LE cas critique : le binome tire a 3 m. FiredNear se declenche a chaque coup,
            # fort, et la source est un ami. C'est la faute qui couche une escouade entiere.
            return lambda t: [(FROLEMENT, 3.0, 0.0, 0.35, True)] if t % 2 == 0 else []
        if nom == "ami_tire_loin":
            # plus insidieux : un ami a 40 m, signal faible mais repete. Une attenuation
            # partielle laisse passer exactement ce cas-la.
            return lambda t: [(FROLEMENT, 40.0, 0.0, 0.14, True)] if t % 2 == 0 else []
        if nom == "bruit_lointain":
            # un accrochage a 300 m : ca s'entend, ca ne me concerne pas
            return lambda t: [(BRUIT, 300.0, 0.0, 0.20, False)] if t % 3 == 0 else []
        if nom == "ami_touche":
            # un camarade tombe a 80 m, hors de portee de ce qui l'a touche
            return lambda t: ([(PERTE, 80.0, 0.0, 1.0, True)] if t == 10 else
                              ([(BRUIT, 200.0, 0.0, 0.15, False)] if t % 4 == 0 else []))
        raise ValueError("scenario inconnu : %s" % nom)

    def _menace_reelle(self):
        """L'epreuve POSITIVE : on tire VRAIMENT sur l'agent. Ne pas reagir est une faute.

        La menace est FRANCHE mais pas saturante, et c'est deliberé. Une menace qui pousse
        l'alarme a 1.0 finit par reveiller meme une politique sourde — l'epreuve ne
        discriminerait plus rien. On demande de reagir a ce qu'un soldat doit percevoir :
        des balles qui passent, puis des impacts. Pas d'etre crible."""
        return lambda t: ([(FROLEMENT, -40.0, 0.0, 0.15, False)] +
                          ([(IMPACT, -40.0, 0.0, 0.25, False)] if t >= 6 else []))

    # ---- le verdict ---------------------------------------------------------------------
    @torch.no_grad()
    def eprouver(self, cand):
        """Rend le detail des deux epreuves pour un candidat."""
        neg = {}
        for nom in SITUATIONS:
            taux, _ = self._jouer(cand, self._scenario(nom))
            neg[nom] = taux
        _, premier = self._jouer(cand, self._menace_reelle())
        pire = max(neg.values())
        passe_pos = 0 <= premier <= 2 + self.p_positif
        passe_neg = pire <= self.taux_max
        return {"negatif": neg, "pire": pire, "premier_reflexe": premier,
                "passe_positive": passe_pos, "passe_negative": passe_neg,
                "survit": passe_pos and passe_neg}

    @torch.no_grad()
    def selectionner(self, candidats):
        """Rend (survivants, rapport). Un seul echec suffit a eliminer."""
        survivants = []; lignes = []
        lignes.append("  %-26s %-9s %-9s %-22s %s"
                      % ("candidat", "positive", "negative", "pire faute", "verdict"))
        for c in candidats:
            r = self.eprouver(c)
            pire_nom = max(r["negatif"], key=r["negatif"].get)
            if r["survit"]: survivants.append(c)
            lignes.append("  %-26s %-9s %-9s %-22s %s" % (
                c.nom,
                "OK" if r["passe_positive"] else "SOURD",
                "OK" if r["passe_negative"] else "AUTO-IMM",
                "%s %.0f%%" % (pire_nom, 100 * r["pire"]),
                "SURVIT" if r["survit"] else "DETRUIT"))
        taux = len(survivants) / max(len(candidats), 1)
        lignes.append("  -> %d/%d survivent (%.0f%%)" % (len(survivants), len(candidats), 100 * taux))
        return survivants, "\n".join(lignes)


# ---- smoke ------------------------------------------------------------------------------
def _smoke():
    from sirocco import device_defaut
    dev = device_defaut()
    ok = True

    def dire(nom, cond, detail=""):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %-46s %s %s" % (nom, "OK " if cond else "ECHEC", detail), flush=True)

    print("=== sirocco_thymus : smoke isole (device %s) ===" % dev, flush=True)
    SPP = 0.7
    th = Thymus(dev, sec_par_pas=SPP)

    try:
        Thymus(dev); dire("sec_par_pas obligatoire", False)
    except ValueError:
        dire("sec_par_pas obligatoire (refus explicite)", True)

    naif = Candidat("naif (aucun IFF)", s1=0.25, filtre_iff=False, attenuation_ami=1.0)
    demi = Candidat("demi-mesure (att. 50%)", s1=0.25, filtre_iff=False, attenuation_ami=0.5)
    sain = Candidat("filtre IFF franc", s1=0.25, filtre_iff=True)
    sourd = Candidat("sourd (seuil 0.95)", s1=0.95, filtre_iff=True)

    r_naif = th.eprouver(naif)
    dire("le naif se plaque sur les tirs de son binome",
         r_naif["negatif"]["ami_tire_pres"] > 0.5 and not r_naif["passe_negative"],
         "%.0f%% du temps" % (100 * r_naif["negatif"]["ami_tire_pres"]))

    r_sain = th.eprouver(sain)
    dire("le filtre IFF supprime la faute", r_sain["negatif"]["ami_tire_pres"] == 0.0)
    dire("...sans le rendre sourd a une vraie menace", r_sain["passe_positive"],
         "reagit au pas %d" % r_sain["premier_reflexe"])

    r_sourd = th.eprouver(sourd)
    dire("le sourd passe la NEGATIVE (piege classique)", r_sourd["passe_negative"])
    dire("...mais la POSITIVE l'elimine", not r_sourd["passe_positive"] and not r_sourd["survit"],
         "premier reflexe : %d" % r_sourd["premier_reflexe"])

    r_demi = th.eprouver(demi)
    dire("la demi-mesure ne suffit pas non plus", not r_demi["survit"],
         "ami pres : %.0f%%" % (100 * r_demi["negatif"]["ami_tire_pres"]))

    surv, rapport = th.selectionner([naif, demi, sain, sourd])
    print(rapport)
    dire("un seul survivant, le bon", len(surv) == 1 and surv[0] is sain)

    # le calme ne doit JAMAIS declencher personne : sinon le banc lui-meme est faux
    dire("aucun candidat ne reagit au calme",
         all(th.eprouver(c)["negatif"]["calme"] == 0.0 for c in (naif, demi, sain, sourd)))

    print("=== sirocco_thymus : %s ===" % ("TOUT PASSE" if ok else "AU MOINS UN ECHEC"), flush=True)
    return ok


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "smoke":
        sys.exit(0 if _smoke() else 1)
    print(__doc__)
