"""L ECHEANCIER : les echeances du monde rangees par pas ( socle, choix 5 ).

Un pret a une date de remboursement, une grossesse un terme, un vehicule un entretien, une peine une fin. Les trouver
en parcourant toute la population chaque jour couterait la population ; les ranger dans le seau de leur pas coute le
nombre d echeances. A 50 millions d habitants, c est la difference entre tenir et ne pas tenir.

Une echeance est une donnee, pas une fonction : ( ticket, type, cle, donnees ). Elle se pickle dans l instantane et
se porte en Rust telle quelle. Chaque domaine declare ses types et fournit ses gestionnaires a `traiter`.

Rien ne se perd :
  - `servir` rend TOUS les seaux depuis le dernier service, meme si l appelant a saute des pas ;
  - une echeance posee dans le passe est refusee, pas oubliee ;
  - une annulation vise un ticket precis, au pas ou il a ete pose ;
  - `ecart()` recompte : posees = servies + annulees + en attente, sinon quelque chose a disparu."""


class EcheancePassee(ValueError):
    pass


class EcheanceInconnue(KeyError):
    pass


class Echeancier:
    __slots__ = ("types", "seaux", "annulees", "pas_courant", "prochain_ticket", "n_pose", "n_servi", "n_annule")

    def __init__(self, pas_courant=0):
        self.types = set()
        self.seaux = {}              # pas -> [ ( ticket, type, cle, donnees ) ], dans l ordre de pose
        self.annulees = set()        # tickets annules, encore dans leur seau
        self.pas_courant = pas_courant   # premier pas pas encore servi
        self.prochain_ticket = 0
        self.n_pose = self.n_servi = self.n_annule = 0

    def declarer(self, type_):
        self.types.add(type_)

    def poser(self, pas, type_, cle, donnees=()):
        """Range une echeance au pas `pas` ; rend son ticket. `cle` : l entite concernee ( un identifiant ) ;
        `donnees` : un tuple de valeurs simples."""
        if type_ not in self.types: raise EcheanceInconnue(f"type d echeance non declare : {type_!r}")
        if pas < self.pas_courant:
            raise EcheancePassee(f"{type_} au pas {pas} : l echeancier a deja servi jusqu au pas {self.pas_courant - 1}")
        t = self.prochain_ticket
        self.prochain_ticket += 1
        s = self.seaux.get(pas)
        if s is None: self.seaux[pas] = [(t, type_, cle, donnees)]
        else: s.append((t, type_, cle, donnees))
        self.n_pose += 1
        return t

    def annuler(self, ticket, pas):
        """Annule l echeance `ticket` posee au pas `pas` ( un pret rembourse d avance, une peine remise )."""
        if (pas < self.pas_courant or ticket in self.annulees
                or not any(e[0] == ticket for e in self.seaux.get(pas, ()))):
            raise EcheanceInconnue(f"pas d echeance en attente au ticket {ticket}, pas {pas}")
        self.annulees.add(ticket)

    def servir(self, jusqu_au_pas):
        """Rend les echeances de tous les pas depuis le dernier service jusqu a `jusqu_au_pas` inclus, dans l ordre
        des pas puis de pose, sans les annulees."""
        rendues = []
        for p in range(self.pas_courant, jusqu_au_pas + 1):
            s = self.seaux.pop(p, None)
            if s is None: continue
            for e in s:
                if e[0] in self.annulees:
                    self.annulees.discard(e[0]); self.n_annule += 1
                else:
                    rendues.append(e)
        self.n_servi += len(rendues)
        self.pas_courant = max(self.pas_courant, jusqu_au_pas + 1)
        return rendues

    def traiter(self, jusqu_au_pas, gestionnaires):
        """Sert, puis appelle le gestionnaire de chaque type : gestionnaires[type]( cle, donnees )."""
        for t, type_, cle, donnees in self.servir(jusqu_au_pas): gestionnaires[type_](cle, donnees)

    def en_attente(self):
        return sum(len(s) for s in self.seaux.values()) - len(self.annulees)

    def ecart(self):
        """Posees - servies - annulees ecartees - presentes dans les seaux ( annulees comprises ). Zero, sinon une
        echeance a disparu."""
        return self.n_pose - self.n_servi - self.n_annule - sum(len(s) for s in self.seaux.values())
