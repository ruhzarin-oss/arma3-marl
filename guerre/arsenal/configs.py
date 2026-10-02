"""Lecteur HORS LIGNE des configs d Arma 3 ( etape 0 d Arma a fond, HMT-191 ).

Arma n est pas allume : on lit les PBO sur le disque. D un PBO on ne lit que l en-tete et le config.bin ( le reste,
modeles et textures, peut peser des gigaoctets ). Le config.bin est au format rapifie de Bohemia ( raP ) ; on le
decode, on fusionne les classes de tous les addons dans l ordre de chargement ( requiredAddons de CfgPatches ), et on
resout l heritage comme le moteur du jeu :
  - une classe redefinie par un addon plus tard garde ses entrees et recoit les nouvelles ; sa classe de base devient
    celle de la derniere definition, meme vide ( le RPT d Arma le dit : « Updating base class 'Overcast'->'' » ) ;
  - un champ absent d une classe se cherche dans sa classe de base, puis dans la base de celle-ci ;
  - la classe de base se cherche d abord dans la classe qui contient la definition ( avec son heritage ), puis dans
    son conteneur, jusqu a la racine ;
  - une sous-classe absente ( le mode Single d un fusil ) s herite de la classe de base comme un champ.
Les noms sont insensibles a la casse, comme dans le jeu.

Format raP ( Bohemia, « Raw File Format - raP » ) : "\\0raP", deux entiers ( 0 et 8 ), l offset de la table des enums,
puis le corps de la racine a l offset 16. Un corps : la classe de base ( chaine ), un entier compresse ( le nombre
d entrees ), les entrees. Une entree commence par son type : 0 classe ( nom, offset du corps ), 1 valeur ( sous-type
0 chaine, 1 flottant 32 bits, 2 entier 32 bits, 6 entier 64 bits ; puis nom et valeur ), 2 tableau ( nom, tableau ),
3 classe externe ( nom ), 4 classe supprimee ( nom ), 5 tableau += ( 4 octets, nom, tableau ). Un tableau : un entier
compresse ( le nombre ), puis chaque element : 0 chaine, 1 flottant, 2 entier, 3 tableau, 4 variable ( chaine ).
Entier compresse : 7 bits par octet, poids faible d abord, le bit haut dit qu un octet suit.
Un PBO ( Bohemia ) : des entrees ( nom, puis 5 entiers : methode, taille d origine, reserve, date, taille des
donnees ) ; la premiere, de nom vide et de methode « Vers », est suivie de paires cle / valeur ( prefix ... ) closes
par une chaine vide ; l en-tete finit par une entree de nom vide et de methode 0 ; les donnees suivent dans l ordre.
Methode « Cprs » : compression LZSS de Bohemia."""
import os
import struct
import time

ARMA = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Arma 3"
ATELIER = "/mnt/c/Program Files (x86)/Steam/steamapps/workshop/content/107410"
# Le jeu de base et ses DLC, dans l ordre ou le jeu monte leurs dossiers ( le moteur trie ensuite par requiredAddons ).
DOSSIERS_JEU = ("Dta", "Addons", "Curator", "Kart", "Heli", "Mark", "Expansion", "Jets", "Argo", "Orange", "Tacops",
                "Tank", "Enoch", "Contact", "AoW")
MODS = {"cba": "450814997", "cup_armes": "497660133", "cup_unites": "497661914", "cup_vehicules": "541888371",
        "rhs_afrf": "843425103", "rhs_usaf": "843577117", "rhs_gref": "843593391", "rhs_saf": "843632231",
        "3cb_factions": "1673456286", "ace": "463939057"}
CPRS = 0x43707273
VERS = 0x56657273


# ================================================================== les PBO
def _cstr(b, i):
    j = b.index(b"\0", i)
    return b[i:j].decode("latin-1"), j + 1


def _lzss(data, taille):
    """La compression des PBO ( LZSS de Bohemia ) : 8 drapeaux par octet, 1 = octet litteral, 0 = renvoi 12 bits +
    longueur 4 bits ; une somme de controle de 4 octets suit."""
    out = bytearray(); i = 0
    while len(out) < taille:
        drapeaux = data[i]; i += 1
        for bit in range(8):
            if len(out) >= taille: break
            if drapeaux & (1 << bit):
                out.append(data[i]); i += 1
            else:
                b1, b2 = data[i], data[i + 1]; i += 2
                rpos = len(out) - (b1 + ((b2 & 0xF0) << 4))
                n = (b2 & 0x0F) + 3
                for k in range(n):
                    p = rpos + k
                    out.append(out[p] if p >= 0 else 0x20)
    return bytes(out)


def _analyser_entete(tete):
    entrees, prefixe, i = [], "", 0
    nom, i = _cstr(tete, i)
    methode, orig, _r, _d, taille = struct.unpack_from("<5I", tete, i); i += 20
    if nom == "" and methode == VERS:
        while True:
            cle, i = _cstr(tete, i)
            if cle == "": break
            val, i = _cstr(tete, i)
            if cle.lower() == "prefix": prefixe = val
    elif nom == "":
        return entrees, prefixe, i
    else:
        entrees.append((nom, methode, orig, taille))
    while True:
        nom, i = _cstr(tete, i)
        methode, orig, _r, _d, taille = struct.unpack_from("<5I", tete, i); i += 20
        if nom == "": return entrees, prefixe, i
        entrees.append((nom, methode, orig, taille))


def lire_entete_pbo(chemin):
    """( entrees, prefixe, offset des donnees ) ; entrees = [ ( nom, methode, taille d origine, taille ) ]. L en-tete
    est relu quatre fois plus grand tant qu il ne tient pas dans ce qui est lu."""
    lu = 1 << 18
    with open(chemin, "rb") as f:
        while True:
            f.seek(0); tete = f.read(lu)
            try:
                return _analyser_entete(tete)
            except (ValueError, struct.error, IndexError):
                if len(tete) < lu: raise ValueError(f"en-tete illisible : {chemin}")
                lu *= 4


def lire_configs_pbo(chemin):
    """Tous les config.bin d un PBO, a la racine ET dans les sous-dossiers : un PBO d Arma peut porter plusieurs
    addons ( weapons_f.pbo en a un par famille d armes ; la porte du 02/10 a ete REFUSEE faute de les lire ).
    Rend ( [ ( chemin interne, donnees ) ] tries par chemin, [ dossiers a config.cpp sans config.bin ] )."""
    entrees, _p, off = lire_entete_pbo(chemin)
    bins, cpps, pos = [], set(), {}
    for nom, methode, orig, taille in entrees:
        n = nom.lower().replace("/", "\\")
        d, _s, f = n.rpartition("\\")
        if f == "config.bin": pos[n] = (off, methode, orig, taille)
        elif f == "config.cpp": cpps.add(d)
        off += taille
    with open(chemin, "rb") as fh:
        for n in sorted(pos):
            o, methode, orig, taille = pos[n]
            fh.seek(o); data = fh.read(taille)
            if methode == CPRS and orig and orig != taille: data = _lzss(data, orig)
            bins.append((n, data))
    dossiers_bin = {n.rpartition("\\")[0] for n in pos}
    return bins, sorted(cpps - dossiers_bin)


# ================================================================== le format raP
class Classe:
    """Une classe de config fusionnee. entrees : nom en minuscules -> ( nom d origine, valeur ou Classe ).
    conteneur : la classe ou elle est definie ( pour chercher sa classe de base ). origine : le dernier addon qui l a
    definie."""
    __slots__ = ("nom", "base", "entrees", "conteneur", "origine")

    def __init__(self, nom, base, conteneur, origine):
        self.nom, self.base, self.conteneur, self.origine = nom, base, conteneur, origine
        self.entrees = {}

    def __repr__(self): return f"<Classe {self.nom} : {self.base}>"


class _Lecteur:
    __slots__ = ("b", "i")

    def __init__(self, b, i=0): self.b, self.i = b, i

    def cint(self):
        v = 0; dec = 0
        while True:
            c = self.b[self.i]; self.i += 1
            v |= (c & 0x7F) << dec
            if not c & 0x80: return v
            dec += 7

    def chaine(self):
        j = self.b.index(b"\0", self.i)
        s = self.b[self.i:j].decode("utf-8", "replace"); self.i = j + 1
        return s

    def u8(self):
        c = self.b[self.i]; self.i += 1
        return c

    def f32(self):
        v = struct.unpack_from("<f", self.b, self.i)[0]; self.i += 4
        return v

    def i32(self):
        v = struct.unpack_from("<i", self.b, self.i)[0]; self.i += 4
        return v

    def i64(self):
        v = struct.unpack_from("<q", self.b, self.i)[0]; self.i += 8
        return v

    def tableau(self):
        n = self.cint(); out = []
        for _ in range(n):
            t = self.u8()
            if t == 0 or t == 4: out.append(self.chaine())
            elif t == 1: out.append(self.f32())
            elif t == 2: out.append(self.i32())
            elif t == 3: out.append(self.tableau())
            elif t == 6: out.append(self.i64())
            else: raise ValueError(f"element de tableau inconnu {t} a {self.i}")
        return out


def _lire_corps(lec, classe, origine, compte):
    """Lit un corps a la position du lecteur et le FUSIONNE dans `classe`."""
    base = lec.chaine()
    classe.base = base
    n = lec.cint()
    enfants = []
    for _ in range(n):
        t = lec.u8()
        if t == 0:
            nom = lec.chaine(); off = struct.unpack_from("<I", lec.b, lec.i)[0]; lec.i += 4
            enfants.append((nom, off))
        elif t == 1:
            st = lec.u8(); nom = lec.chaine()
            if st == 0: v = lec.chaine()
            elif st == 1: v = lec.f32()
            elif st == 2: v = lec.i32()
            elif st == 6: v = lec.i64()
            else: raise ValueError(f"sous-type de valeur inconnu {st}")
            classe.entrees[nom.lower()] = (nom, v)
        elif t == 2:
            nom = lec.chaine(); classe.entrees[nom.lower()] = (nom, lec.tableau())
        elif t == 3:
            nom = lec.chaine()
            k = nom.lower()
            if k not in classe.entrees:          # une declaration externe ne change rien a une classe connue
                classe.entrees[k] = (nom, Classe(nom, None, classe, origine))
        elif t == 4:
            nom = lec.chaine(); classe.entrees.pop(nom.lower(), None)
        elif t == 5:
            lec.i += 4; nom = lec.chaine(); ajout = lec.tableau()
            k = nom.lower()
            ancien = classe.entrees.get(k)
            v = list(ancien[1]) if ancien and isinstance(ancien[1], list) else []
            classe.entrees[k] = (nom, v + ajout)
        else:
            raise ValueError(f"type d entree inconnu {t} a {lec.i}")
    for nom, off in enfants:
        k = nom.lower()
        e = classe.entrees.get(k)
        if e is None or not isinstance(e[1], Classe):
            sous = Classe(nom, "", classe, origine); classe.entrees[k] = (nom, sous)
        else:
            sous = e[1]; sous.origine = origine
        compte[0] += 1
        _lire_corps(_Lecteur(lec.b, off), sous, origine, compte)


def fusionner_config(racine, data, origine):
    """Fusionne un config.bin dans la racine ; rend le nombre de classes lues."""
    if data[:4] != b"\0raP": raise ValueError("pas un config.bin rapifie")
    compte = [0]
    lec = _Lecteur(data, 16)
    base = racine.base
    _lire_corps(lec, racine, origine, compte)
    racine.base = base
    return compte[0]


def _sauter_entrees_racine(lec):
    """[ ( nom, offset ) ] des classes de la racine ; les valeurs et tableaux sont lus pour etre sautes."""
    lec.chaine(); n = lec.cint(); out = []
    for _ in range(n):
        t = lec.u8()
        if t == 0:
            nom = lec.chaine(); off = struct.unpack_from("<I", lec.b, lec.i)[0]; lec.i += 4; out.append((nom, off))
        elif t == 1:
            st = lec.u8(); lec.chaine()
            if st == 0: lec.chaine()
            elif st in (1, 2): lec.i += 4
            elif st == 6: lec.i += 8
            else: raise ValueError(f"sous-type de valeur inconnu {st}")
        elif t == 2: lec.chaine(); lec.tableau()
        elif t in (3, 4): lec.chaine()
        elif t == 5: lec.i += 4; lec.chaine(); lec.tableau()
        else: raise ValueError(f"type d entree inconnu {t}")
    return out


def lire_cfgpatches(data):
    """{ addon : [ requiredAddons ] } d un config.bin, sans le fusionner."""
    if data[:4] != b"\0raP": raise ValueError("pas un config.bin rapifie")
    out = {}
    for nom, off in _sauter_entrees_racine(_Lecteur(data, 16)):
        if nom.lower() != "cfgpatches": continue
        r = Classe(nom, "", None, None)
        _lire_corps(_Lecteur(data, off), r, None, [0])
        for k, (n, c) in r.entrees.items():
            if isinstance(c, Classe):
                req = c.entrees.get("requiredaddons")
                out[n] = [x for x in (req[1] if req and isinstance(req[1], list) else []) if isinstance(x, str)]
    return out


# ================================================================== la resolution de l heritage
def _externe(v):
    """Une declaration « class X; » jamais definie : elle renvoie a la classe heritee ou exterieure, elle ne la masque
    pas ( la porte du 02/10 a 21 h 04 a ete REFUSEE pour HitPoints >> HitHull du Slammer, masque ainsi )."""
    return isinstance(v, Classe) and v.base is None


def membre(c, nom, _vus=None):
    """( valeur ou Classe, classe ou l entree est definie ) en suivant l heritage ; ( None, None ) si absent. Une
    declaration externe ne compte pas : on cherche plus haut."""
    k = nom.lower(); vus = _vus if _vus is not None else set()
    while c is not None:
        if id(c) in vus: return None, None       # boucle d heritage : on s arrete
        vus.add(id(c))
        e = c.entrees.get(k)
        if e is not None and not _externe(e[1]): return e[1], c
        c = classe_de_base(c)
    return None, None


def classe_de_base(c):
    """La classe de base de c : cherchee parmi les entrees du conteneur de sa definition, puis parmi celles que ce
    conteneur herite ( « class Single: Single » prend le Single de la base ), puis plus haut, jusqu a la racine."""
    if not c.base: return None
    k = c.base.lower()
    cont = c.conteneur
    while cont is not None:
        e = cont.entrees.get(k)
        if e is not None and isinstance(e[1], Classe) and e[1] is not c and not _externe(e[1]): return e[1]
        b = classe_de_base(cont)
        if b is not None:
            v, _ = membre(b, k)
            if isinstance(v, Classe) and v is not c: return v
        cont = cont.conteneur
    return None


def chemin(racine, *noms):
    """( valeur, classe de definition ) au bout d un chemin configFile >> a >> b >> c ; ( None, None ) si absent."""
    c = racine; defn = None
    for n in noms:
        if not isinstance(c, Classe): return None, None
        c, defn = membre(c, n)
        if c is None: return None, None
    return c, defn


def est_nombre(v): return isinstance(v, (int, float)) and not isinstance(v, bool)


# ================================================================== l ensemble des addons
def pbos_du_jeu(dossiers=DOSSIERS_JEU, racine_jeu=ARMA):
    out = []
    for d in dossiers:
        base = os.path.join(racine_jeu, d)
        for dp, _dn, fn in sorted(os.walk(base)):
            for f in sorted(fn):
                if f.lower().endswith(".pbo"): out.append(os.path.join(dp, f))
    return out


def pbos_du_mod(cle_ou_dossier):
    d = cle_ou_dossier if os.path.isdir(cle_ou_dossier) else os.path.join(ATELIER, MODS[cle_ou_dossier])
    out = []
    for dp, _dn, fn in sorted(os.walk(d)):
        for f in sorted(fn):
            if f.lower().endswith(".pbo"): out.append(os.path.join(dp, f))
    return out


def _ordre_de_chargement(lus):
    """lus : [ ( pbo, data, { addon : requis } ) ] dans l ordre des dossiers ; rend la liste triee : un addon apres
    tous ses requiredAddons connus ( tri topologique stable )."""
    par_addon = {}
    for k, (_p, _d, patches) in enumerate(lus):
        for a in patches: par_addon.setdefault(a.lower(), k)
    requis = []
    for k, (_p, _d, patches) in enumerate(lus):
        r = set()
        for a, req in patches.items():
            for x in req:
                j = par_addon.get(x.lower())
                if j is not None and j != k: r.add(j)
        requis.append(r)
    fait, ordre, etat = set(), [], {}

    def visiter(k):
        pile = [(k, iter(sorted(requis[k])))]
        etat[k] = 1
        while pile:
            n, it = pile[-1]
            suivant = next(it, None)
            if suivant is None:
                pile.pop(); etat[n] = 2; ordre.append(n); continue
            if etat.get(suivant) is None:
                etat[suivant] = 1; pile.append((suivant, iter(sorted(requis[suivant]))))
    for k in range(len(lus)):
        if etat.get(k) is None: visiter(k)
    return [lus[k] for k in ordre]


class Catalogue:
    """La config fusionnee d un ensemble d addons, et ce que la lecture a rencontre."""

    def __init__(self):
        self.racine = Classe("", "", None, None)
        # avec_bin : le nombre de config.bin lus ( plusieurs par PBO )
        self.pbos = 0; self.avec_bin = 0; self.cpp_seul = []; self.sans_config = 0; self.echecs = []
        self.classes = 0; self.duree_s = 0.0; self.ebo = 0

    def cfg(self, nom):
        e = self.racine.entrees.get(nom.lower())
        return e[1] if e and isinstance(e[1], Classe) else None

    def noms(self, cfg):
        c = self.cfg(cfg)
        return [] if c is None else [n for n, v in c.entrees.values() if isinstance(v, Classe)]


def lire_ensemble(pbos, journal=None):
    """Lit les config.bin d une liste de PBO ( dans l ordre des dossiers ), les trie par requiredAddons et les fusionne."""
    t0 = time.time(); cat = Catalogue(); lus = []
    for p in pbos:
        cat.pbos += 1
        try:
            bins, cpps = lire_configs_pbo(p)
            for interne, data in bins:
                lus.append((p + "::" + interne, data, lire_cfgpatches(data))); cat.avec_bin += 1
            cat.cpp_seul += [p + "::" + d for d in cpps]
            if not bins and not cpps: cat.sans_config += 1
        except Exception as ex:                    # compte et nomme, ne cache pas
            cat.echecs.append((p, repr(ex)))
    for p, data, _patches in _ordre_de_chargement(lus):
        try:
            pbo, _s, interne = p.partition("::")
            cat.classes += fusionner_config(cat.racine, data, os.path.basename(pbo) + ("::" + interne if interne != "config.bin" else ""))
        except Exception as ex:
            cat.echecs.append((p, "fusion " + repr(ex)))
    cat.duree_s = time.time() - t0
    if journal: journal(f"{cat.pbos} PBO, {cat.avec_bin} config.bin, {len(cat.cpp_seul)} config.cpp seuls, "
                        f"{cat.sans_config} sans config, {len(cat.echecs)} echecs, {cat.classes} classes, "
                        f"{cat.duree_s:.0f} s")
    return cat
