"""L HORLOGE DE GUERRE : le moteur a pleine vitesse, Arma en temps reel, l horloge murale arbitre ( Younes, 26/09 ).

Une seule boucle, un seul fil : entre deux pas du moteur ( archipel, pleine vitesse ), des qu une periode d horloge
murale ( 60 s ) est ecoulee, un TOUR :
  1. chaque ile en guerre fait sa releve ( guerre/moteur.py ) et la bourse la convertit en points ( guerre/bourse.py ) ;
  2. un seul aller-retour avec Arma verse les points et relit les zones ( guerre/arma.py ) ;
  3. les zones de l ile champ de bataille tenues par l envahisseur sont occupees dans le moteur, les zones reprises
     liberees ;
  4. une ligne dans journal.jsonl.
Le moteur ne decide rien : il paie ce que son economie produit et subit ce qu Arma lui prend. Arma ne sait rien du
moteur : il recoit deux nombres par minute, et des numeros de front.

LES SOLDATS SUIVIS ( option 1 de Younes, 26/09 ) : chaque soldat d Arma est un habitant de son ile. A chaque tour,
chaque ile MOBILISE de quoi tenir RESERVE soldats designes et partis au front ( guerre/moteur.py ) ; Arma pose ses
escouades avec leurs numeros. Toutes les PERIODE_SUIVI_S secondes, un releve rend la position et les blessures de
chaque soldat vivant ( moteur : suivre ) et les morts ( moteur : morts au combat, cause « combat » ).

On l arrete en posant le fichier STOP dans le dossier.

   python -m guerre.horloge --dossier /mnt/data/hmt/guerre/essai --echelle 4 --arma faux [ --tours 5 --periode 2 ]"""
import argparse, json, os, sys, time
from . import bourse as B, zones as Z
from .arma import ArmaGuerre, FauxGuerre

CAMPS = {"WEST": "Malden", "EAST": "Stratis"}      # le defenseur tient la carte, l envahisseur debarque
CHAMP = "Malden"
RESERVE = 16                                       # soldats designes d avance par camp : deux escouades
GOUVERNEMENTS = "/mnt/data/hmt/guerre/gouvernements"   # le gouvernement adopte par le conseil de guerre ( guerre/conseil.py )
PERIODE_SUIVI_S = 10.0


class HorlogeDeGuerre:
    def __init__(self, arc, arma, carte, camps=CAMPS, champ=CHAMP, periode_s=60.0, dossier=None, horloge=time.monotonic,
                 suivre=True, periode_suivi_s=PERIODE_SUIVI_S):
        self.arc, self.arma, self.carte = arc, arma, carte
        self.camps, self.champ, self.periode = dict(camps), champ, float(periode_s)
        self.envahisseurs = {c for c, ile in self.camps.items() if ile != champ}
        self.lieux = {z["n"]: z["lieux"] for z in carte["zones"]}
        self.dossier, self.horloge = dossier, horloge
        self.occupees = set()
        self.tours = 0
        self.t0 = self.prochain = None
        self.derniere = None
        self.suivre, self.periode_suivi = suivre, float(periode_suivi_s)
        self.prochain_suivi = None
        self.suivis = 0
        self.dernier_suivi = None
        self.impayes = {}              # ile -> points d armes livres et pas encore payes ( dette_points du dernier paiement )

    def ouvrir(self):
        """La guerre commence : la premiere releve de chaque ile ne paie pas le passe. Apres une reprise, les zones
        deja occupees dans le moteur sont reprises telles quelles."""
        self.gouvernements = {ile: self.arc.commande(ile, "guerre_voir") for ile in self.camps.values()}
        self.adoptes = {}
        self.relever_gouvernements()
        for ile in self.camps.values():
            r = self.arc.commande(ile, "guerre_releve")
            if ile == self.champ:
                self.occupees = set(r["occupees"])
                for n in sorted(self.occupees): self.arc.commande(ile, "occuper", n, self.lieux[n], True)   # a jour ( villes )
        if self.suivre and hasattr(self.arma, "identifier"): self.identifies = self.identifier()
        self.t0 = self.horloge()
        self.prochain = self.t0 + self.periode
        self.prochain_suivi = self.t0 + self.periode_suivi
        return self

    def identifier(self):
        """Branchement en cours de bataille : les hommes deja poses sans numero recoivent chacun un soldat de leur ile.
        Un premier appel a vide les compte ; chaque ile mobilise autant ; le second les numerote."""
        vide = {c: [] for c in self.camps}
        compte = self.arma.identifier(vide)
        ids = {c: self.arc.commande(ile, "guerre_mobiliser", compte[c]["sans_numero"]) if compte[c]["sans_numero"] else []
               for c, ile in self.camps.items()}
        r = self.arma.identifier(ids) if any(ids.values()) else compte
        if self.dossier:
            with open(os.path.join(self.dossier, "identification.json"), "w") as f:
                json.dump({"sans_numero": compte, "mobilises": {c: len(v) for c, v in ids.items()}, "resultat": r}, f)
        return r

    def relever_gouvernements(self, dossier=GOUVERNEMENTS):
        """Le conseil de guerre a adopte un nouveau gouvernement ( GOUVERNEMENTS/<Ile>.py ) : il entre dans l ile
        vivante, sans arreter la guerre. Rend les iles changees."""
        changees = []
        for ile in self.camps.values():
            f = os.path.join(dossier, f"{ile}.py")
            if not os.path.exists(f): continue
            t = os.path.getmtime(f)
            if self.adoptes.get(ile) == t: continue
            try:
                self.gouvernements[ile] = self.arc.commande(ile, "guerre_gouverner", open(f).read(), f"conseil:{ile}")
                changees.append(ile)
            except Exception as ex:
                print(f"gouvernement de {ile} refuse : {ex}", flush=True)
            self.adoptes[ile] = t
        if changees and self.dossier:
            with open(os.path.join(self.dossier, "gouvernements.jsonl"), "a") as g:
                g.write(json.dumps({"t_mur_s": round(self.horloge() - (self.t0 or self.horloge()), 1), "iles": changees,
                                    "modeles": self.gouvernements}) + "\n")
        return changees

    def reserves(self, releves):
        """Chaque ile mobilise de quoi tenir RESERVE soldats designes pas encore poses dans Arma."""
        out = {}
        for camp, ile in self.camps.items():
            manque = RESERVE - releves[ile]["front"]["reserve"]
            out[camp] = self.arc.commande(ile, "guerre_mobiliser", manque) if manque > 0 else []
        return out

    def suivre_soldats(self):
        """Un releve d Arma : positions et blessures des vivants, et les morts, rendus a leurs iles."""
        vivants, morts = self.arma.positions()
        l = {"t_mur_s": round(self.horloge() - self.t0, 3), "vivants": {}, "morts": {}}
        for camp, ile in self.camps.items():
            l["vivants"][camp] = self.arc.commande(ile, "guerre_suivre", vivants[camp])
            l["morts"][camp] = self.arc.commande(ile, "guerre_morts", morts[camp]) if morts[camp] else 0
        self.suivis += 1
        self.dernier_suivi = l
        if self.dossier and any(l["morts"].values()):
            with open(os.path.join(self.dossier, "morts.jsonl"), "a") as f:
                f.write(json.dumps({"t_mur_s": l["t_mur_s"], "morts": morts}, ensure_ascii=False) + "\n")
        return l

    def tour(self):
        nouveaux = self.relever_gouvernements()
        t = self.horloge()
        ligne = {"tour": self.tours + 1, "t_mur_s": round(t - self.t0, 3), "iles": {}, "points": {}}
        for camp, ile in self.camps.items():
            r = self.arc.commande(ile, "guerre_releve")
            pts, f, euros = B.points_de_la_minute(r["recettes"], r["part_defense"], r["euros_par_unite"], r["militaires"])
            # un fournisseur impaye ne livre plus ( 27/09 ) : tant que des armes deja livrees ne sont pas payees ( pas de
            # devises a la banque centrale, ou pas de caisse ), l ile ne recoit plus de credit d achat dans Arma
            imp = self.impayes.get(ile, 0.0)
            if imp > 0: pts = 0.0
            ligne["iles"][ile] = dict(r, camp=camp, f=f, euros=euros, points=pts, impayes_points=imp)
            ligne["points"][camp] = pts
        a = self.arma.tour(ligne["points"], self.reserves(ligne["iles"]) if self.suivre else None)
        for camp, ile in self.camps.items():             # l argent ne sort du Tresor qu a l achat
            dep = a["camps"].get(camp, {}).get("depense")
            if dep is not None:
                pa = ligne["iles"][ile]["paiement"] = self.arc.commande(ile, "guerre_payer", dep, B.EUROS_PAR_POINT)
                self.impayes[ile] = float(pa.get("dette_points", 0.0))
        tenues = {n for n, camp in a["zones"].items() if camp in self.envahisseurs and self.lieux.get(n)}
        for n in sorted(tenues - self.occupees): self.arc.commande(self.champ, "occuper", n, self.lieux[n], True)
        for n in sorted(self.occupees - tenues): self.arc.commande(self.champ, "occuper", n, self.lieux[n], False)
        ligne["gouvernements_changes"] = nouveaux
        ligne["occupations"] = {"prises": sorted(tenues - self.occupees), "liberees": sorted(self.occupees - tenues),
                                "tenues": sorted(tenues)}
        self.occupees = tenues
        ligne["arma"] = {"zones_par_camp": {c: sum(1 for v in a["zones"].values() if v == c) for c in ("EAST", "WEST", "RESISTANCE")},
                         "camps": a["camps"], "temps": a["temps"], "rtt_ms": a.get("recu", {}).get("rtt_ms")}
        self.tours += 1
        self.derniere = ligne
        if self.dossier:
            with open(os.path.join(self.dossier, "journal.jsonl"), "a") as f: f.write(json.dumps(ligne, ensure_ascii=False) + "\n")
        return ligne

    def boucle(self, tours=None, stop=None):
        """Le moteur a pleine vitesse ; un tour a chaque periode murale. Un tour en retard ne se rattrape pas en
        rafale : l horloge murale est la seule verite, on repart de maintenant."""
        while (tours is None or self.tours < tours) and not (stop and os.path.exists(stop)):
            if self.suivre and self.horloge() >= self.prochain_suivi:
                self.suivre_soldats()
                self.prochain_suivi = max(self.prochain_suivi + self.periode_suivi, self.horloge())
            if self.horloge() >= self.prochain:
                self.tour()
                self.prochain = max(self.prochain + self.periode, self.horloge() + 0.5 * self.periode)   # un tour en retard : le suivant pas avant une demi-periode
            else:
                self.arc.un_pas()
        return self.tours


def texte_du_tour(l):
    iles = " | ".join(f"{i} jour {r['jour']} +{r['jours_clos']} j faim {r.get('faim', 0):.1%} {str(r.get('gouvernement', ''))[:17]}, {r['points']:.0f} pts ( f {r['f']:.3f} ) front "
                      f"{r['front']['reserve']}/{r['front']['front']}/{r['front']['mort']}" for i, r in l["iles"].items())
    z = l["arma"]["zones_par_camp"]
    em = " ".join(f"{c} {'ASSAUT' if e.get('assaut') else 'ralliement'} {e.get('reunis')}/{e.get('defenseurs')} garnison {e.get('garnison')}"
                  for c, e in ((c, v.get("em") or {}) for c, v in l["arma"]["camps"].items()) if e)
    paye = " ".join(f"{i} paye {r['paiement']['paye']:.0f}" + (f" IMPAYE {r['paiement']['dette_points']:.0f} pts" if r['paiement'].get('dette_points') else "")
                    for i, r in l["iles"].items() if r.get("paiement"))
    return (f"tour {l['tour']} a {l['t_mur_s']:.0f} s : {iles} | zones W {z['WEST']} E {z['EAST']} N {z['RESISTANCE']} | "
            f"occupees {l['occupations']['tenues']} | {em} | {paye}")


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--dossier", required=True)
    a.add_argument("--echelle", type=float, default=4.0)
    a.add_argument("--periode", type=float, default=60.0)
    a.add_argument("--tours", type=int, default=None)
    a.add_argument("--arma", choices=("faux", "vrai"), default="faux")
    a.add_argument("--mission", default=os.path.join(Z.ICI, "mission", "GuerreIles.Malden", "mission.sqm"))
    a.add_argument("--gouvernement", default=None, help="le code qui gouverne chaque ile ( un dossier <Ile>.py, l agent codeur ) ; sans : les regles")
    a.add_argument("--reprise", default=None, help="un instantane de l archipel ( --instantane d une guerre precedente )")
    a.add_argument("--instantane", default=None, help="ou sauver l archipel en fin de guerre, pour la reprendre")
    x = a.parse_args()
    from monde.archipel import Archipel
    os.makedirs(x.dossier, exist_ok=True)
    carte = Z.carte_de_guerre(open(x.mission, encoding="latin-1").read(), CHAMP)
    json.dump(carte, open(os.path.join(x.dossier, "carte.json"), "w"), ensure_ascii=False, indent=1)
    arma = (ArmaGuerre(carte["zones"]) if x.arma == "vrai" else FauxGuerre(carte["zones"])).ouvrir()
    t0 = time.time()
    arc = Archipel(iles=tuple(CAMPS.values()), echelle=x.echelle, parallele=True, reprise=x.reprise, gouvernement=x.gouvernement)
    print(f"archipel {tuple(CAMPS.values())} pret en {time.time() - t0:.1f} s", flush=True)
    h = HorlogeDeGuerre(arc, arma, carte, periode_s=x.periode, dossier=x.dossier).ouvrir()
    print(f"gouvernements : {h.gouvernements}", flush=True)
    stop = os.path.join(x.dossier, "STOP")
    try:
        while (x.tours is None or h.tours < x.tours) and not os.path.exists(stop):
            n = h.tours
            h.boucle(tours=n + 1, stop=stop)
            if h.tours > n: print(texte_du_tour(h.derniere), flush=True)
    finally:
        arma.fermer()
        if x.instantane:
            arc.instantane(x.instantane); print(f"archipel sauve dans {x.instantane} ( pas {arc.pas} )", flush=True)
        arc.fermer()
    return 0


if __name__ == "__main__":
    sys.exit(main())
