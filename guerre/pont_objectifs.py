"""LE PONT DES OBJECTIFS ( Arma a fond, etape 1d, HMT-192 ) : les degats des VRAIS objets du terrain d Arma deviennent
des frappes dans le moteur ( guerre/frappes.py ).

Cote Arma ( guerre/mission/GuerreIles.Malden/objectifs.sqf, sans commentaire : le meme texte s envoie par le pont ) :
  GUERRE_fnc_objectifs_poser  [ [ k, x, y, sol ], ... ] : pour chaque composant, l objet du terrain a moins de 3 m
                              ( nearestTerrainObjects ) dont la surface au sol ( boundingBoxReal, arrondie, la mesure de
                              l inventaire ) vaut `sol`, sinon le plus proche ; ligne OBJ k trouve distance surface ;
                              OBJFIN n. Deux chemins : le composant n est TROUVE que si la surface relue est celle de
                              l inventaire, a moins de 3 m ;
  GUERRE_fnc_objectifs_degats aucune entree : ligne DEG k dommage pour chaque objet dont le dommage a change ( un objet
                              detruit, alive faux, vaut 1 ) ; DEGFIN n changes.
Rien que des nombres ne passe : aucun texte du moteur n entre dans Arma ( regle du pont, guerre/arma.py ).
Cote moteur : PontObjectifs pose les composants de l ile en commandes de moins de TAILLE_MAX octets, relit les degats,
et frappe chaque objectif dont un composant a change. Un composant introuvable dans Arma est liste ( jamais lu comme
« intact » ). FauxLiaison est le jouet a reponse connue des portes : il ne prouve que la plomberie cote Python ; le SQF,
seul Arma le prouve.

   p = PontObjectifs( w, "malden", liaison ) ; p.poser( ) ; p.relever( )"""
import math
import re

from . import frappes as FR, objectifs as OB

TAILLE_MAX = 8500                     # octets d une commande ( le pont refuse au-dela de ~ 9 Ko, 26/09 )
TOLERANCE_M = 3.0


class Incomplet(Exception):
    pass


def lignes_de(r):
    """Les lignes d une reponse du pont ( { lignes : [ ( cle, [ nombres ] ) ] } ou la liste elle-meme )."""
    return r["lignes"] if isinstance(r, dict) else r


class PontObjectifs:
    def __init__(self, w, ile, liaison):
        self.w, self.ile, self.liaison = w, ile, liaison
        self.objectifs = [o for o in OB.objectifs_carte(ile) if o["composants"]]
        self.index = []                                   # k -> ( objectif, composant )
        for o in self.objectifs:
            for c in o["composants"]: self.index.append((o, c))
        self.trouves = {}                                 # k -> distance
        self.introuvables = []
        self.dommage = {}                                 # k -> dernier dommage lu

    def commandes_poser(self):
        """Les commandes SQF qui posent tous les composants, chacune sous TAILLE_MAX octets."""
        out, cur = [], []
        def texte(lst): return "[[" + ",".join(f"[{k},{x:.1f},{y:.1f},{s}]" for k, x, y, s in lst) + "]] call GUERRE_fnc_objectifs_poser;"
        for k, (o, c) in enumerate(self.index):
            un = (k, float(c["x"]), float(c["y"]), int(round(c["sol_m2"])))
            essai = cur + [un]
            if cur and len(texte(essai).encode()) > TAILLE_MAX:
                out.append(texte(cur)); cur = [un]
            else:
                cur = essai
        if cur: out.append(texte(cur))
        return out

    def poser(self):
        vus = set()
        for cmd in self.commandes_poser():
            n_attendu = cmd.count("],[") + 1
            lg = lignes_de(self.liaison.executer(cmd))
            fin = [v for cle, v in lg if cle == "OBJFIN"]
            if not fin or int(fin[0][0]) != n_attendu: raise Incomplet(f"OBJFIN absent ou faux : {fin!r} pour {n_attendu}")
            for cle, v in lg:
                if cle != "OBJ": continue
                k, trouve, dist, sol = int(v[0]), int(v[1]), float(v[2]), int(round(v[3]))
                vus.add(k)
                attendu = int(round(self.index[k][1]["sol_m2"]))
                if trouve and dist <= TOLERANCE_M and sol == attendu: self.trouves[k] = dist
                else: self.introuvables.append((k, "absent" if not trouve else ("loin" if dist > TOLERANCE_M else "autre surface")))
        manquent = [k for k in range(len(self.index)) if k not in vus]
        if manquent: raise Incomplet(f"{len(manquent)} composants sans reponse : {manquent[:10]}")
        return {"composants": len(self.index), "trouves": len(self.trouves), "introuvables": len(self.introuvables)}

    def relever(self):
        """Relit les degats et frappe les objectifs touches. Rend [ ( objectif, degats, effets ) ]."""
        lg = lignes_de(self.liaison.executer("[] call GUERRE_fnc_objectifs_degats;"))
        fin = [v for cle, v in lg if cle == "DEGFIN"]
        if not fin: raise Incomplet("DEGFIN absent")
        touches = {}
        for cle, v in lg:
            if cle != "DEG": continue
            k, dg = int(v[0]), float(v[1])
            if not 0 <= k < len(self.index): raise Incomplet(f"composant inconnu {k}")
            if k not in self.trouves: continue            # un introuvable ne parle pas : rien n est lu de lui
            self.dommage[k] = min(1.0, max(0.0, dg))
            touches[self.index[k][0]["id"]] = self.index[k][0]
        out = []
        for oid, o in touches.items():
            dom = {self.index[k][1]["i"]: d for k, d in self.dommage.items() if self.index[k][0]["id"] == oid}
            d, eff = FR.frapper(self.w, o, dom)
            out.append((oid, d, eff))
        return out


class FauxLiaison:
    """Le jouet a reponse connue : des objets du terrain aux positions de l inventaire ( moins ceux de `absents` ),
    dont on regle le dommage a la main ( `endommager` ). Il lit les commandes comme le ferait la mission."""

    def __init__(self, absents=()):
        self.objets = {}                                  # k -> [ trouve, dommage, rapporte ]
        self.absents = set(absents)
        self.tailles = []

    def endommager(self, k, d): self.objets[k][1] = float(d)

    def executer(self, sqf):
        self.tailles.append(len(sqf.encode()))
        if "GUERRE_fnc_objectifs_poser" in sqf:
            out = []
            for k, x, y, sol in re.findall(r"\[(\d+),(-?[\d.]+),(-?[\d.]+),(\d+)\]", sqf):
                k = int(k)
                trouve = k not in self.absents
                self.objets[k] = [trouve, 0.0, 0.0]
                out.append(("OBJ", [k, 1 if trouve else 0, 0.0 if trouve else -1.0, int(sol) if trouve else -1]))
            out.append(("OBJFIN", [len(out)]))
            return {"lignes": out}
        if "GUERRE_fnc_objectifs_degats" in sqf:
            out = []
            for k, v in sorted(self.objets.items()):
                if v[0] and abs(v[1] - v[2]) > 0.001: v[2] = v[1]; out.append(("DEG", [k, v[1]]))
            out.append(("DEGFIN", [len(self.objets), len(out)]))
            return {"lignes": out}
        raise ValueError(f"commande inconnue du faux pont : {sqf[:60]}")
