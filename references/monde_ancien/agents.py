"""LES AGENTS DU MONDE - point 1 des douze manques ( plans/plan-12-manques.md ).

Jusqu ici une regle decidait pour les 500 habitants : un menage visait toujours un jour et demi de nourriture.
Ici le menage CHOISIT combien stocker, et la conséquence lui revient le lendemain : il a mange, ou il a eu faim.

Deux choses separees, volontairement :
  - la DOCTRINE, commune a tous les menages : ce que le pays a appris, des poids partages, ecrits sur disque ;
  - la MEMOIRE, propre a chaque menage : son dernier choix, son dernier prix, sa faim d hier.
C est la difference entre former un peuple et dresser un individu : chacun vit son histoire, tous heritent de la lecon.

L apprentissage est un bandit contextuel lineaire : pour chaque action, une estimation de la recompense a partir de
ce que le menage voit. Pas de reseau profond - avec une decision par jour et par menage, il n y aurait rien a nourrir.
"""
import json, math, os, random
from . import config as C

CIBLES = (0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 8.0)      # en jours de nourriture visés
HORIZON = 3                                        # la note d un choix se lit sur trois jours, pas sur le soir meme
TRAITS = ("prix", "rarete", "reserve", "jours_payables", "tendance_prix", "faim_hier", "taille", "biais")
N_TRAITS = len(TRAITS)


class Doctrine:
    """Ce que le pays a appris. Des poids par action, partages par tous les menages, sauvegardes en JSON."""

    def __init__(self, alpha=0.02, epsilon=0.1, graine=0, n_actions=None, n_traits=None, nom="menages"):
        """Par defaut la doctrine des menages ( 7 cibles, 8 traits ) ; tout autre groupe donne sa propre forme."""
        self.n_actions = n_actions or len(CIBLES)
        self.n_traits = n_traits or N_TRAITS
        self.nom = nom
        self.poids = [[0.0] * self.n_traits for _ in range(self.n_actions)]
        self.alpha, self.epsilon = alpha, epsilon
        self.rng = random.Random(graine)
        self.n_choix = 0
        self.n_lecons = 0
        self.somme_recompense = 0.0

    # ------------------------------------------------------------------ decider
    def estimer(self, x):
        return [sum(w * v for w, v in zip(p, x)) for p in self.poids]

    def choisir(self, x, explorer=True):
        self.n_choix += 1
        if explorer and self.rng.random() < self.epsilon:
            return self.rng.randrange(self.n_actions)
        # une note non finie n est pas une opinion : l action redevient inconnue plutot que de decider par un NaN
        notes = [n if math.isfinite(n) else float("-inf") for n in self.estimer(x)]
        meilleure = max(notes)
        if not math.isfinite(meilleure): return self.rng.randrange(self.n_actions)
        candidats = [i for i, n in enumerate(notes) if n >= meilleure - 1e-12]
        return self.rng.choice(candidats)

    # ------------------------------------------------------------------ apprendre
    def apprendre(self, x, action, recompense):
        p = self.poids[action]
        estime = sum(w * v for w, v in zip(p, x))
        if not math.isfinite(estime): p[:] = [0.0] * self.n_traits; estime = 0.0     # une doctrine qui diverge se rejoue a neuf
        erreur = max(-2.0, min(2.0, recompense - estime))                       # un pas borne : pas d emballement
        for i, v in enumerate(x): p[i] += self.alpha * erreur * v
        self.n_lecons += 1
        self.somme_recompense += recompense

    # ------------------------------------------------------------------ durer
    def ecrire(self, chemin):
        os.makedirs(os.path.dirname(chemin), exist_ok=True)
        with open(chemin, "w") as f:
            json.dump({"nom": self.nom, "poids": self.poids, "n_actions": self.n_actions, "n_traits": self.n_traits,
                       "lecons": self.n_lecons, "recompense_moyenne": self.moyenne()}, f, indent=1)

    @classmethod
    def lire(cls, chemin, **kw):
        with open(chemin) as f: s = json.load(f)
        n_a, n_t = len(s["poids"]), len(s["poids"][0])
        attendu_a, attendu_t = kw.pop("n_actions", None), kw.pop("n_traits", None)
        if (attendu_a and attendu_a != n_a) or (attendu_t and attendu_t != n_t):
            raise ValueError("doctrine d une autre forme : refusee plutot que rabotee")
        d = cls(n_actions=n_a, n_traits=n_t, nom=s.get("nom", "menages"), **kw)
        d.poids = s["poids"]; d.n_lecons = s.get("lecons", 0)
        return d

    def moyenne(self):
        return self.somme_recompense / self.n_lecons if self.n_lecons else 0.0


class Menagier:
    """L agent d un menage : il regarde son marche et son garde-manger, choisit une cible de stock, et recoit sa note
    le lendemain. La doctrine est commune ; la memoire ci-dessous est la sienne."""

    __slots__ = ("dernier_x", "derniere_action", "dernier_prix", "depense", "faim_hier", "recompenses", "en_attente", "besoin_du_soir")

    def __init__(self):
        self.dernier_x = None; self.derniere_action = None; self.dernier_prix = None
        self.depense = 0.0; self.faim_hier = 0.0; self.recompenses = []
        self.besoin_du_soir = 1.0
        self.en_attente = []            # les choix dont la note n est pas encore complete : [x, action, jours, faim, cout]

    def regarder(self, w, mg, marche, besoin_jour):
        """Ce que le menage VOIT le soir. Jamais l avenir, jamais la verite du monde : des prix, un stock, sa faim."""
        prix = marche.prix["nourriture"] * (1 + w.gouv.tva)
        besoin_ville = max(1.0, sum(len(x.membres) for x in w.menages if x.domicile.marche is marche.lieu) * C.NOURRITURE_PAR_JOUR)
        tendance = prix / self.dernier_prix if self.dernier_prix else 1.0
        # tous les traits sont ramenes vers [0, 1] : un bandit lineaire n aime pas les echelles qui se melangent
        return [min(5.0, prix / C.PRIX_MONDE["nourriture"]) / 5.0,
                min(5.0, marche.stocks["nourriture"] / besoin_ville) / 5.0,
                min(5.0, mg.garde_manger / max(1e-6, besoin_jour)) / 5.0,
                min(10.0, mg.caisse / max(1e-6, prix * besoin_jour)) / 10.0,
                min(3.0, tendance) / 3.0,
                1.0 if self.faim_hier > 1e-6 else 0.0,
                len(mg.membres) / 5.0,
                1.0]

    def poser(self, x, action, cout, besoin_jour):
        """Le choix du soir entre en attente de sa note : elle ne sera lisible que dans trois jours."""
        self.en_attente.append([x, action, 0, 0.0, min(1.0, cout / max(1e-6, 20.0 * besoin_jour))])

    def journee(self, manque):
        """Le lendemain : chaque choix en attente encaisse la journee. Un choix mur rend sa note et sort.

        C est la correction du 22/09 : avec une note lue le soir meme, stocker ne coutait QUE de l argent et ne
        rapportait rien - les menages formes avaient appris a ne rien stocker, et un choix au hasard les battait."""
        assouvi = 0.0 if manque > 1e-6 else 1.0
        murs, restent = [], []
        for e in self.en_attente:
            e[2] += 1; e[3] += assouvi
            (murs if e[2] >= HORIZON else restent).append(e)
        self.en_attente = restent
        self.faim_hier = manque
        return [(x, a, faim / max(1, j) - 0.1 * cout) for x, a, j, faim, cout in murs]
