"""LE JOURNAL DU MONDE : des evenements declares, individuels ou comptes, en memoire bornee ( socle ).

Le moteur E1 range chaque evenement dans une liste qui ne se vide jamais ( `Monde.evenements` ) et rouvre le fichier
du journal a chaque ligne. A 500 habitants, c est invisible ; a un million, un achat par menage et par jour ferait
300 000 lignes par jour. Deux niveaux, donc, declares par chaque domaine :
  - « individuel » : un evenement rare, dont chaque occurrence compte ( une naissance, une faillite, un verdict ) ;
    il garde ses champs, entre dans une file bornee des plus recents et dans le fichier ;
  - « compte »     : un evenement frequent ( un achat, une patrouille ) ; seuls son nombre et la somme d une valeur
    sont gardes, et ecrits une fois par jour.
Un type non declare, un champ manquant, un champ au nom reserve ( jour, heure, type ) : refuses. Un journal ou chacun ecrit ce qu il veut ne se relit pas."""
import collections, json

NIVEAUX = ("individuel", "compte")
RESERVES = ("jour", "heure", "type")      # les cles du journal lui-meme : un champ de ce nom les ecraserait en silence
RECENTS_MAX = 10000


class TypeInconnu(KeyError):
    pass


class TypeEvenement:
    __slots__ = ("nom", "domaine", "niveau", "champs")

    def __init__(self, nom, domaine, niveau, champs):
        self.nom, self.domaine, self.niveau, self.champs = nom, domaine, niveau, tuple(champs)


class Journal:
    __slots__ = ("types", "recents", "comptes", "individuels_jour", "tampon", "fichier", "enregistreur")

    def __init__(self, fichier=None, recents_max=RECENTS_MAX):
        self.types = {}
        self.recents = collections.deque(maxlen=recents_max)
        self.comptes = {}              # type compte -> [ nombre, somme ], du jour
        self.individuels_jour = {}     # type individuel -> nombre, du jour
        self.tampon = []               # lignes a ecrire a la cloture : un seul acces au fichier par jour
        self.fichier = fichier
        self.enregistreur = None       # monde/enregistreur.py ( lit seulement )

    def declarer(self, nom, domaine, niveau="individuel", champs=()):
        if niveau not in NIVEAUX: raise ValueError(f"niveau inconnu {niveau!r} : {NIVEAUX}")
        if any(c in RESERVES for c in champs): raise ValueError(f"{nom} : champ reserve parmi {champs} ( {RESERVES} )")
        ancien = self.types.get(nom)
        if ancien is not None and (ancien.niveau, ancien.champs) != (niveau, tuple(champs)):
            raise ValueError(f"type {nom!r} deja declare autrement par {ancien.domaine}")
        self.types[nom] = TypeEvenement(nom, domaine, niveau, champs)

    def noter(self, jour, heure, type_, **champs):
        t = self.types.get(type_)
        if t is None or t.niveau != "individuel": raise TypeInconnu(f"evenement individuel non declare : {type_!r}")
        manquants = [c for c in t.champs if c not in champs]
        if manquants: raise ValueError(f"{type_} : champs manquants {manquants}")
        if any(c in champs for c in RESERVES):
            raise ValueError(f"{type_} : un champ nomme {RESERVES} ecraserait la cle du journal ( bogue du 23/09 )")
        e = {"jour": jour, "heure": round(heure, 2), "type": type_, **champs}
        self.recents.append(e)
        r = getattr(self, "enregistreur", None)
        if r is not None: r.evenement("journal", e)
        self.individuels_jour[type_] = self.individuels_jour.get(type_, 0) + 1
        if self.fichier: self.tampon.append(json.dumps(e, ensure_ascii=False))

    def compter(self, type_, valeur=1.0):
        c = self.comptes.get(type_)
        if c is None:
            t = self.types.get(type_)
            if t is None or t.niveau != "compte": raise TypeInconnu(f"evenement compte non declare : {type_!r}")
            c = self.comptes[type_] = [0, 0.0]
        c[0] += 1; c[1] += valeur

    def cloturer_jour(self, jour):
        """Rend { type : ( nombre, somme ) } pour les comptes et { type : nombre } pour les individuels du jour ;
        ecrit le tampon et une ligne de bilan ; remet les compteurs du jour a zero."""
        r = getattr(self, "enregistreur", None)
        if r is not None: r.comptes(jour, self.comptes)
        bilan = {"jour": jour, "comptes": {t: (n, s) for t, (n, s) in sorted(self.comptes.items())},
                 "individuels": dict(sorted(self.individuels_jour.items()))}
        if self.fichier:
            self.tampon.append(json.dumps({"jour": jour, "type": "bilan_du_jour", **bilan}, ensure_ascii=False))
            with open(self.fichier, "a") as f: f.write("\n".join(self.tampon) + "\n")
        self.tampon = []; self.comptes = {}; self.individuels_jour = {}
        return bilan

    def derniers(self, type_=None, n=100):
        es = [e for e in self.recents if type_ is None or e["type"] == type_]
        return es[-n:]
