"""LE POINT DE DECISION : l etat n est pas la decision ( socle, choix 7 ).

Chaque decision du pays - stocker, embaucher, preter, patrouiller, prescrire - est un point nomme, declare une fois :
  - ses TRAITS : ce que l agent observe, bornes dans [0 ; 1], chacun avec sa source ( d ou l agent le sait ) ; jamais
    la verite cachee du monde, jamais l avenir ;
  - ses ACTIONS : un catalogue discret ;
  - sa REGLE de base : deterministe, calibree ;
  - son TEMOIN bete : ce qu un idiot ferait ( expedier sans condition, toujours attendre ) ;
  - sa NOTE : ce que mesure la consequence ; et son HORIZON : sur combien de jours elle se lit ( 3 par defaut ).

Trois lecons deja payees sont ecrites dans ce protocole :
  - une note lue le soir meme apprend a ne rien faire ( menages, 22/09 : 17 % de faim contre 8 % a trois jours ) :
    la note d un choix est la moyenne des consequences sur les `horizon_j` jours qui le suivent ;
  - une note surtout nationale ne bouge pas avec le choix, et l agent n apprend rien ( cinq groupes refuses le 23/09 ) :
    `part_du_choix()` mesure, a jour egal, la part de la note qui varie avec l action ( epsilon carre, corrige du biais
    des petits groupes ) et `p_permutation()` la compare au hasard. Zero : ce point ne peut rien apprendre ;
  - un temoin bete a battu trois fois une regle savante : chaque point en declare un, et le `Decideur` le fait vivre.

Le `Decideur` fait vivre un point dans l un de ses cinq modes : regle, appris ( il apprend en vivant ), fige ( il agit
sans apprendre : l examen ), hasard, temoin. La doctrine est celle du moteur ( agents.Doctrine, bandit lineaire,
partagee par le groupe ) ; le terme constant du bandit est ajoute ici, l observateur ne le fournit pas.

`Attente` generalise roles.Memoire a un horizon quelconque ( celle-ci tient HORIZON = 3 en dur ) : roles.py pourra
s appuyer sur elle quand il sera repris."""
import collections, math, re
import numpy as np
from ..agents import Doctrine

MODES = ("regle", "appris", "fige", "hasard", "temoin")
HORIZON_DEFAUT = 3
ECHANTILLON_MAX = 200_000   # notes murees gardees une a une pour le test par permutation ( memoire bornee )
HORIZON_MAX = 365           # un pret, une recolte, une grossesse se lisent en mois : 30 jours ne suffisaient pas ( banques, 23/09 )
# Un choix n avance que les jours ou son agent est note ( une machine : les jours ou son atelier ouvre ). Un agent qui
# decide chaque jour sans etre jamais note ( un atelier vide ) empilait ses choix sans fin : 47 000 machines par ile
# a un million, un choix par jour chacune, 0,11 Go de plus par jour sur l archipel ( sonde du 25/09 ). Au-dela de
# ATTENTE_MAX_HORIZONS fois l horizon, le plus ancien choix en attente est abandonne sans note : en regime normal
# ( 5 jours ouvres sur 7, 30 jours d horizon -> 42 choix ) la borne n est jamais atteinte.
ATTENTE_MAX_HORIZONS = 2
NOM_VALIDE = re.compile(r"^[a-z][a-z0-9_]{0,39}$")


class TraitHorsBornes(ValueError):
    pass


class ActionHorsCatalogue(ValueError):
    pass


class PointDeDecision:
    """La declaration d un point de decision.
      traits     tuple de ( nom, source ) : ce que l agent voit et d ou il le sait
      actions    tuple de noms
      observer   fonction ( contexte ) -> suite de valeurs dans [0 ; 1], une par trait
      regle      fonction ( x, contexte ) -> indice d action ( x : les traits observes )
      temoin     fonction ( x, contexte, rng ) -> indice d action
      note       ce que mesure la consequence : l effet de CE choix sur ceux qu il touche, pas la moyenne du pays
      horizon_j  jours sur lesquels la note se lit"""
    __slots__ = ("nom", "domaine", "traits", "actions", "observer", "regle", "temoin", "note", "horizon_j")

    def __init__(self, nom, domaine, traits, actions, observer, regle, temoin, note, horizon_j=HORIZON_DEFAUT):
        if not NOM_VALIDE.match(nom): raise ValueError(f"nom de point invalide : {nom!r}")
        traits, actions = tuple(traits), tuple(actions)
        if not 1 <= len(traits) <= 64 or any(len(t) != 2 or not NOM_VALIDE.match(t[0]) or not t[1] for t in traits):
            raise ValueError(f"{nom} : 1 a 64 traits, chacun ( nom, source ) avec sa source ecrite")
        if not 2 <= len(actions) <= 64 or any(not NOM_VALIDE.match(a) for a in actions) or len(set(actions)) != len(actions):
            raise ValueError(f"{nom} : 2 a 64 actions nommees, distinctes")
        if not (isinstance(horizon_j, int) and 1 <= horizon_j <= HORIZON_MAX):
            raise ValueError(f"{nom} : horizon hors [1 ; {HORIZON_MAX}] jours : {horizon_j!r}")
        for f, quoi in ((observer, "observer"), (regle, "regle"), (temoin, "temoin")):
            if not callable(f): raise ValueError(f"{nom} : {quoi} doit etre une fonction")
        if not note: raise ValueError(f"{nom} : la note doit dire ce qu elle mesure")
        self.nom, self.domaine, self.traits, self.actions = nom, domaine, traits, actions
        self.observer, self.regle, self.temoin, self.note, self.horizon_j = observer, regle, temoin, note, horizon_j


class Attente:
    """Les choix d un agent qui attendent leur note : [ traits, action, jours ecoules, somme des consequences ]."""
    __slots__ = ("choix",)

    def __init__(self):
        self.choix = []

    def poser(self, x, a):
        self.choix.append([x, a, 0, 0.0])

    def ajouter(self, valeur):
        """Une consequence connue tout de suite ( une amende, une marge ) s ajoute au dernier choix."""
        if self.choix: self.choix[-1][3] += valeur

    def jour(self, r, horizon):
        """Une journee passe : chaque choix en attente encaisse `r`. Ceux qui ont vecu `horizon` jours rendent leur
        note - la moyenne de ce qu ils ont encaisse - et sortent."""
        murs, restent = [], []
        for e in self.choix:
            e[2] += 1; e[3] += r
            (murs if e[2] >= horizon else restent).append(e)
        self.choix = restent
        return [(x, a, s / horizon) for x, a, j, s in murs]


class Decideur:
    """Fait vivre un point de decision pour un groupe d agents ( une cle par agent )."""
    __slots__ = ("point", "mode", "doctrine", "rng", "attentes", "stats", "n_decisions", "echantillon", "abandonnes")

    def __init__(self, point, mode="regle", doctrine=None, rng=None, graine=0, epsilon=0.1, alpha=0.02):
        if mode not in MODES: raise ValueError(f"mode inconnu {mode!r} : {MODES}")
        n_traits = len(point.traits) + 1                     # + le terme constant du bandit
        if doctrine is None:
            doctrine = Doctrine(alpha=alpha, epsilon=epsilon, graine=graine, n_actions=len(point.actions),
                                n_traits=n_traits, nom=point.nom)
        elif (doctrine.n_actions, doctrine.n_traits) != (len(point.actions), n_traits):
            raise ValueError(f"{point.nom} : doctrine d une autre forme, refusee plutot que rabotee")
        if mode == "hasard": doctrine.epsilon = 1.0
        if mode == "fige": doctrine.epsilon = 0.0
        self.point, self.mode, self.doctrine = point, mode, doctrine
        self.rng = rng if rng is not None else np.random.default_rng(graine)
        self.attentes = {}      # cle d agent -> Attente
        self.stats = {}         # ( jour, action ) -> [ nombre, somme, somme des carres ] des notes murees ce jour-la
        self.n_decisions = 0
        self.abandonnes = 0     # choix jamais notes, abandonnes a la borne ATTENTE_MAX_HORIZONS x horizon
        self.echantillon = collections.deque(maxlen=ECHANTILLON_MAX)   # ( jour, action, note ) : pour la permutation

    @property
    def apprend(self):
        return self.mode == "appris"

    def observer(self, contexte):
        """Les traits de l agent, verifies : un trait hors [0 ; 1] ou non fini est une erreur de l observateur, et
        une erreur ne se rabote pas en silence."""
        x = self.point.observer(contexte)
        if len(x) != len(self.point.traits):
            raise TraitHorsBornes(f"{self.point.nom} : {len(x)} traits observes pour {len(self.point.traits)} declares")
        for (nom, _), v in zip(self.point.traits, x):
            if not 0.0 <= v <= 1.0: raise TraitHorsBornes(f"{self.point.nom}.{nom} = {v!r} hors [0 ; 1]")
        return [float(v) for v in x] + [1.0]

    def decider(self, cle, contexte):
        x = self.observer(contexte)
        if self.mode == "regle": a = self.point.regle(x[:-1], contexte)
        elif self.mode == "temoin": a = self.point.temoin(x[:-1], contexte, self.rng)
        else: a = self.doctrine.choisir(x, explorer=self.mode != "fige")
        if not (isinstance(a, (int, np.integer)) and 0 <= a < len(self.point.actions)):
            raise ActionHorsCatalogue(f"{self.point.nom} : action {a!r} hors des {len(self.point.actions)} du catalogue")
        att = self.attentes.get(cle)
        if att is None: att = self.attentes[cle] = Attente()
        att.poser(x, int(a))
        if len(att.choix) > ATTENTE_MAX_HORIZONS * self.point.horizon_j:
            del att.choix[0]; self.abandonnes += 1
        self.n_decisions += 1
        return int(a)

    def ajouter(self, cle, valeur):
        att = self.attentes.get(cle)
        if att is not None: att.ajouter(valeur)

    def noter(self, cle, valeur, jour):
        """La consequence du jour pour l agent `cle`. Les choix murs rendent leur note ; en mode appris, la doctrine
        en tire la lecon. Tous les modes tiennent leurs statistiques : un temoin se mesure comme un eleve."""
        att = self.attentes.get(cle)
        if att is None: return
        for x, a, note in att.jour(valeur, self.point.horizon_j):
            if self.apprend: self.doctrine.apprendre(x, a, note)
            s = self.stats.get((jour, a))
            if s is None: self.stats[(jour, a)] = [1, note, note * note]
            else: s[0] += 1; s[1] += note; s[2] += note * note
            self.echantillon.append((jour, a, note))

    def notes_par_action(self):
        """{ action : ( nombre de notes, note moyenne ) }."""
        acc = {}
        for (j, a), (n, s, q) in self.stats.items():
            t = acc.setdefault(a, [0, 0.0]); t[0] += n; t[1] += s
        return {self.point.actions[a]: (n, s / n) for a, (n, s) in sorted(acc.items())}

    def part_du_choix(self):
        """La part de la variance des notes que l action explique, A JOUR EGAL : epsilon carre, corrige du biais des
        petits groupes. L eta carre brut ( `part_du_choix_brute` ) tend vers 1 quand chaque jour ne compte qu une note
        par action, meme au hasard ( trouve par le domaine 6, 23/09 ) ; epsilon carre retire ce que le hasard seul
        explique ( ( k - 1 ) fois la variance intra-groupe ) et vaut 0 en esperance sans effet. Une note nationale donne
        la meme note a tous le meme jour : zero."""
        return _epsilon2(((j, a, n, s, q) for (j, a), (n, s, q) in self.stats.items()))

    def part_du_choix_brute(self):
        """L eta carre intra-jour, sans correction ( gardee pour comparer ; biaise vers le haut ). """
        par_jour = {}
        for (j, a), s in self.stats.items(): par_jour.setdefault(j, []).append(s)
        entre = total = 0.0
        for groupes in par_jour.values():
            n = sum(g[0] for g in groupes); somme = sum(g[1] for g in groupes)
            if n < 2: continue
            total += sum(g[2] for g in groupes) - somme * somme / n
            entre += sum(g[1] * g[1] / g[0] for g in groupes) - somme * somme / n
        return max(0.0, entre / total) if total > 1e-12 else 0.0

    def p_permutation(self, n=200, graine=0):
        """La probabilite que le hasard donne une part du choix au moins aussi grande : les actions sont permutees A
        L INTERIEUR de chaque jour ( la note du jour ne bouge pas ), n fois. Sur l echantillon des notes murees."""
        if len(self.echantillon) < 3: return 1.0
        d = np.array([e[0] for e in self.echantillon]); a = np.array([e[1] for e in self.echantillon])
        v = np.array([e[2] for e in self.echantillon], dtype=float)
        ordre = np.argsort(d, kind="stable"); d, a, v = d[ordre], a[ordre], v[ordre]
        coupes = np.flatnonzero(np.diff(d)) + 1
        debuts = np.concatenate(([0], coupes)); fins = np.concatenate((coupes, [len(d)]))
        obs = _epsilon2_tableaux(d, a, v)
        rng = np.random.default_rng(graine)
        plus = 0
        for _ in range(n):
            b = a.copy()
            for x, y in zip(debuts, fins):
                if y - x > 1: b[x:y] = b[x:y][rng.permutation(y - x)]
            plus += _epsilon2_tableaux(d, b, v) >= obs - 1e-15
        return (1 + plus) / (n + 1)


def _epsilon2(groupes):
    """Epsilon carre intra-jour a partir de ( jour, action, nombre, somme, somme des carres )."""
    par_jour = {}
    for j, a, n, s, q in groupes: par_jour.setdefault(j, []).append((n, s, q))
    ssb = sst = 0.0; dfb = dfw = 0
    for gs in par_jour.values():
        n = sum(g[0] for g in gs)
        if n < 2: continue
        S = sum(g[1] for g in gs); Q = sum(g[2] for g in gs)
        sst += Q - S * S / n
        ssb += sum(g[1] * g[1] / g[0] for g in gs) - S * S / n
        dfb += len(gs) - 1; dfw += n - len(gs)
    if sst <= 1e-12 or dfw <= 0: return 0.0
    msw = max(0.0, sst - ssb) / dfw
    return max(0.0, (ssb - dfb * msw) / sst)


def _epsilon2_tableaux(d, a, v):
    cle = {}
    for j, x, y in zip(d.tolist(), a.tolist(), v.tolist()):
        g = cle.get((j, x))
        if g is None: cle[(j, x)] = [1, y, y * y]
        else: g[0] += 1; g[1] += y; g[2] += y * y
    return _epsilon2((j, x, n, s, q) for (j, x), (n, s, q) in cle.items())
