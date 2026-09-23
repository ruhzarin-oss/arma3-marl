"""LE HASARD DU MONDE : un flux par domaine, derive de la graine ( socle, choix 6 ).

Pourquoi pas un seul generateur, comme `Monde.rng` ? Parce qu un tirage ajoute dans un domaine decale TOUS les
tirages qui le suivent, dans tous les autres domaines. Le monde se rejoue toujours a l identique ; mais deux variantes
d un meme monde ( une regle contre un agent, une loi contre une autre ) ne tirent plus les memes malades, les memes
pannes, les memes recoltes, et la comparaison appariee est perdue sans que rien ne le signale.

Ici chaque domaine a son flux : ajouter un tirage aux banques ne change rien a la meteo. Et `sous_flux` donne un flux
neuf pour une cle entiere ( un jour, un objet ) : ce qu un domaine tire pour le jour 12 ne depend pas de ce qu il a
tire le jour 11. Deux variantes restent appariees meme quand leurs comportements divergent.

`Monde.rng` reste en service pour le moteur E1 ; les nouveaux domaines n y touchent pas."""
import zlib
import numpy as np

SOUS_FLUX_JOUR = 1       # premier entier de la cle d un flux journalier
SOUS_FLUX_OBJET = 2      # premier entier de la cle d un flux propre a un objet ( objets.Parc.materialiser )
GRAINE_MAX = 2 ** 63


def code_domaine(nom):
    """Un entier stable pour un nom de domaine : le crc32 de son nom. Jamais `hash()`, que Python sale a chaque
    lancement : le meme monde tirerait autre chose d une execution a l autre."""
    if not isinstance(nom, str) or not nom or not nom.isascii():
        raise ValueError(f"nom de domaine vide ou non ASCII : {nom!r}")
    return zlib.crc32(nom.encode("ascii"))


class Hasard:
    """Les generateurs d un monde. Il entre dans l instantane comme le reste : un monde repris tire la suite exacte."""
    __slots__ = ("graine", "_flux", "_codes")

    def __init__(self, graine):
        graine = int(graine)
        if not 0 <= graine < GRAINE_MAX: raise ValueError(f"graine hors [0 ; 2^63[ : {graine}")
        self.graine = graine
        self._flux = {}          # domaine -> Generator, cree a la premiere demande
        self._codes = {}         # code -> domaine : deux noms qui tomberaient sur le meme code sont refuses

    def _code(self, domaine):
        c = code_domaine(domaine)
        deja = self._codes.setdefault(c, domaine)
        if deja != domaine: raise ValueError(f"collision de codes entre {deja!r} et {domaine!r} : renommer l un")
        return c

    def _generateur(self, cle):
        return np.random.Generator(np.random.PCG64(np.random.SeedSequence(self.graine, spawn_key=cle)))

    def flux(self, domaine):
        """Le flux continu d un domaine : chaque appel reprend la ou le precedent s est arrete."""
        g = self._flux.get(domaine)
        if g is None: g = self._flux[domaine] = self._generateur((self._code(domaine),))
        return g

    def sous_flux(self, domaine, *cle):
        """Un flux neuf, fonction seulement de ( graine, domaine, cle ) ; la cle : un ou plusieurs entiers >= 0.
        Sa creation coute des microsecondes ( python -m monde.socle.cout ) : pour un evenement rare - un jour, un
        objet materialise - jamais pour chaque habitant."""
        if not cle or any(isinstance(k, bool) or not isinstance(k, (int, np.integer)) or k < 0 for k in cle):
            raise ValueError(f"cle de sous-flux invalide : {cle!r}")
        return self._generateur((self._code(domaine),) + tuple(int(k) for k in cle))

    def du_jour(self, domaine, jour):
        """Le flux d un domaine pour un jour : le meme, quoi qu il ait ete tire les jours precedents."""
        return self.sous_flux(domaine, SOUS_FLUX_JOUR, jour)

    def etat(self):
        return {d: g.bit_generator.state for d, g in self._flux.items()}

    def restaurer(self, etat):
        for d, s in etat.items(): self.flux(d).bit_generator.state = s
