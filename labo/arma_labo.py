#!/usr/bin/env python3
"""arma_labo — le module typé du LABO Arma (verdict de Fable du 11/09/2026).

⭐ LE LABO N'EST PAS UN BANC. Il sert à regarder et à régler une scène à la main, et à trouver une
panne vite. Il ne produit AUCUN chiffre publiable : un verdict naît d'un job de la file, avec ses
graines. MCP = labo, job = mesure, rien ne traverse.

Le MCP (mcp_arma.py) n'est qu'un transport posé sur ce module. Un script ou un CLI l'appelle de la
même façon : `with Labo() as l: print(l.etat())`.

LA CHAÎNE (le pont fichier de la ferme Windows, le même que pont.py)
  ALLER  : on écrit C:\\hmt_bridge\\i9\\cmd_<N>.sqf ; la DLL hmt_ext le lit au niveau OS ;
           l'actuateur de Labo.Altis l'exécute dans son propre fil (spawn).
  RETOUR : diag_log -> RPT du profil hmtech9, suivi depuis WSL.

CE QUE CE MODULE GARANTIT — chaque point est une panne déjà payée par un script jetable
  1. UN SEUL ÉCRIVAIN PAR DOSSIER DE PONT. Deux écrivains se volent leurs cmd_N et s'effacent au
     démarrage, sans une erreur (R2-bis, 30/08). Verrou etat/labo_i9.ecrivain.
  2. UN REÇU PAR COMMANDE, émis par la commande elle-même en dernière instruction :
     « [LABO] ECHO <n> <nonce> <k> ». Pas de reçu = la commande ne s'est pas compilée.
     k = nombre de lignes de résultat émises : on vérifie qu'on les a toutes lues.
  3. JAMAIS « AUCUN » À LA PLACE DE « PAS DE RÉPONSE ». Une absence de reçu lève une exception
     (PontMort, SansRecu, Incomplet). Aucune méthode ne rend une liste vide pour dire « panne ».
  4. LE COMPTEUR SE RELIT DANS LE RPT. Le battement « [LABO] HMT_SYNC n » (toutes les 2 s) dit où
     en est l'actuateur. Un serveur relancé ouvre un nouveau RPT et repart à 0 : on se recale, on
     ne fait jamais confiance à un n gardé en mémoire.
  5. QUE DES NOMBRES EN RETOUR. Le RPT est une entrée non fiable pour un LLM : aucun texte du monde
     ne remonte, seulement des clés écrites dans fonctions.sqf suivies de nombres.
  6. LE SQF EST VÉRIFIÉ AVANT D'ÊTRE ÉCRIT. `call compile` ne retire pas les commentaires : un seul
     `//` tue la commande entière en silence. Refusé, pas nettoyé. Taille bornée sous le plafond
     de la DLL (au-delà, elle rend __TOOBIG__).
  7. UNE COMMANDE QUI N'A PAS ÉTÉ PRISE EST EFFACÉE. Sinon l'actuateur la jouerait plus tard, au
     réveil — une scène posée dix minutes après qu'on l'a crue perdue.

⚠️ LIMITE CONNUE : le reçu prouve que la commande s'est COMPILÉE et que son exécution a atteint la
dernière ligne. Une erreur d'exécution au milieu (variable indéfinie…) laisse SQF continuer : le
reçu arrive quand même. `erreurs_rpt` compte les lignes « Error » vues pendant la commande, toutes
sources confondues (LAMBS compris) — un indice, pas une preuve.
"""
from __future__ import annotations

import glob
import logging
import math
import os
import random
import re
import shutil
import time

log = logging.getLogger("labo")

# --- L'INSTANCE DU LABO ------------------------------------------------------------------------
# ⚠️ Aucun banc n'emploie l'instance 9 ni la mission Labo.Altis. Le module REFUSE toute autre
# instance : pointé sur le dossier de pont d'un job, il effacerait ses commandes en s'ouvrant.
INSTANCE = 9
H = "/mnt/data/hmt"
PROFIL = f"/mnt/c/Users/Younes/hmtech{INSTANCE}"
PONT = f"/mnt/c/hmt_bridge/i{INSTANCE}"
VERROUS = f"{H}/queue/verrous"
ETAT = f"{H}/etat"

VERSION_MISSION = 1                 # = LABO_VERSION, dernière ligne de mission.Altis/fonctions.sqf
ANCRE_ALTIS = (8291.45, 10065.42)   # l'ancre d'EchellePol : terrain dégagé connu
PLAFOND_OCTETS = 9000               # la DLL rend au plus ~10 239 octets ; on garde de la marge
BATTEMENT_MAX = 6.0                 # s ; la mission bat toutes les 2 s
PATIENCE = 6.0                      # s ; latence mesurée 0,516 s médiane, 0,566 s p99 (30/08)

CAMPS = ["rouge", "bleu", "vert", "civil"]          # = LABO_CAMPS [east, west, independent, civilian]
CAMPS_POSABLES = {"rouge": 0, "bleu": 1, "vert": 2}
ORDRES = {"aller": 0, "arreter": 1, "comportement": 2, "combat": 3,
          "vitesse": 4, "posture": 5, "reveler": 6}
VALEURS = {"comportement": ["careless", "safe", "aware", "combat", "stealth"],
           "combat": ["blue", "green", "white", "yellow", "red"],
           "vitesse": ["limited", "normal", "full"],
           "posture": ["up", "middle", "down", "auto"]}
REFUS_MISSION = {1: "position dans l'eau", 2: "aucun lieu sûr trouvé près du point demandé",
                 3: "groupe inconnu (l'indice ne désigne aucun groupe)", 4: "groupe vide"}

_RE_SYNC = re.compile(r"\[LABO\] HMT_SYNC (\d+) coeur (\d+)")
_RE_ECHO = re.compile(r"\[LABO\] ECHO (\d+) (\d+) (\d+)")
_RE_R = re.compile(r"\[LABO\] R (\d+) ([A-Z_]+)((?: [-+0-9.eE]+)*)")
_RE_ERREUR = re.compile(r"\bError\b")


# --- LES ERREURS : chacune dit ce qu'on sait, et ce qu'on ne sait pas ---------------------------
class ErreurLabo(Exception):
    pass

class Refus(ErreurLabo):
    """Refusé AVANT l'écriture : rien n'est parti vers Arma."""

class PontMort(ErreurLabo):
    """Pas de battement, ou commande jamais prise. On ne sait RIEN de l'état du monde."""

class SansRecu(ErreurLabo):
    """L'actuateur a pris la commande, aucun reçu n'est revenu : erreur SQF probable."""

class Incomplet(ErreurLabo):
    """Reçu présent, mais des lignes de résultat manquent ou ne se lisent pas."""

class Occupe(ErreurLabo):
    """L'instance ou le pont sont tenus par un autre processus vivant."""


# --- LES VERROUS ---------------------------------------------------------------------------------
def _vivant(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True

def _lire_pid(chemin: str) -> int | None:
    # Un fichier de pid vide peut être un verrou EN TRAIN de naître : on relit avant de conclure.
    for _ in range(3):
        try:
            with open(chemin) as f:
                txt = f.read().strip()
        except OSError:
            return None
        if txt.isdigit():
            return int(txt)
        time.sleep(0.2)
    return None


class VerrouFile:
    """`queue/verrous/j<N>/pid`, le format que file3.sh lit. Tant qu'il vit, la file ne prend aucun
    job sur l'instance N, et il compte dans son plafond de jobs en vol : le labo consomme une place
    et ça se voit. file3.sh retire lui-même un verrou dont le pid est mort."""

    def __init__(self, verrous: str, instance: int):
        self.d = os.path.join(verrous, f"j{instance}")
        self.ancien = os.path.join(verrous, f"i{instance}")
        self.pris = False

    def prendre(self):
        if os.path.isdir(self.ancien):
            raise Occupe(f"verrou ancien format {self.ancien} présent : instance occupée")
        for _ in range(2):
            try:
                os.mkdir(self.d)
            except FileExistsError:
                pid = _lire_pid(os.path.join(self.d, "pid"))
                if pid and _vivant(pid):
                    raise Occupe(f"instance tenue par le pid {pid} ({self.d})")
                log.warning("VERROU MORT %s (pid %s absent) — retiré", self.d, pid)
                shutil.rmtree(self.d, ignore_errors=True)
                continue
            with open(os.path.join(self.d, "pid"), "w") as f:
                f.write(f"{os.getpid()}\n")
            self.pris = True
            return
        raise Occupe(f"impossible de prendre {self.d}")

    def rendre(self):
        # On ne rend que le verrou qu'on a posé : le pid inscrit doit être le nôtre.
        if self.pris and _lire_pid(os.path.join(self.d, "pid")) == os.getpid():
            shutil.rmtree(self.d, ignore_errors=True)
        self.pris = False


class VerrouEcrivain:
    """Un seul écrivain par dossier de pont. Fichier créé en O_EXCL : atomique."""

    def __init__(self, chemin: str):
        self.chemin = chemin
        self.pris = False

    def prendre(self):
        for _ in range(2):
            try:
                fd = os.open(self.chemin, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                pid = _lire_pid(self.chemin)
                if pid and _vivant(pid):
                    raise Occupe(f"le pont du labo a déjà un écrivain : pid {pid}")
                log.warning("ÉCRIVAIN MORT %s (pid %s absent) — retiré", self.chemin, pid)
                try:
                    os.remove(self.chemin)
                except FileNotFoundError:
                    pass
                continue
            os.write(fd, f"{os.getpid()}\n".encode())
            os.close(fd)
            self.pris = True
            return
        raise Occupe(f"impossible de prendre {self.chemin}")

    def rendre(self):
        if self.pris and _lire_pid(self.chemin) == os.getpid():
            try:
                os.remove(self.chemin)
            except FileNotFoundError:
                pass
        self.pris = False


# --- LA LIAISON : écrire cmd_N, suivre le RPT, apparier les reçus --------------------------------
class Liaison:
    def __init__(self, profil: str, pont: str, *, instance: int = INSTANCE,
                 battement_max: float = BATTEMENT_MAX, patience: float = PATIENCE):
        self.profil, self.pont, self.instance = profil, pont, instance
        self.battement_max, self.patience = battement_max, patience
        self.chemin = None          # RPT suivi
        self.f = None
        self.tampon = ""            # ligne coupée en cours d'écriture
        self.seq = 0                # numéro de ligne lue, pour ordonner battements et reçus
        self.sync_n = None          # compteur de l'actuateur, lu dans le dernier battement
        self.sync_t = 0.0
        self.sync_seq = -1
        self.n_confirme = None      # dernier n dont on a reçu l'ECHO
        self.conf_seq = -1
        self.recalages = 0
        self.redemarrages = 0
        self.echos = {}             # nonce -> (n, k, seq)
        self.lignes_r = {}          # nonce -> [(cle, [nombres])]
        self.malformees = {}        # nonce -> nombre de lignes R illisibles
        self.erreurs_seq = []       # seq des lignes « Error »
        self._t_rotation = 0.0

    # ---- lecture du RPT
    def _dernier_rpt(self):
        # Le lanceur efface les RPT : un fichier peut disparaître entre glob et getmtime.
        meilleur, t = None, -1.0
        for f in glob.glob(os.path.join(self.profil, "*.rpt")):
            try:
                m = os.path.getmtime(f)
            except OSError:
                continue
            if m > t:
                meilleur, t = f, m
        return meilleur

    def _basculer(self, chemin, depuis_debut):
        if self.f:
            try:
                self.f.close()
            except Exception:
                pass
        self.chemin, self.tampon = chemin, ""
        self.f = open(chemin, "r", errors="ignore")
        if not depuis_debut:
            self.f.seek(0, os.SEEK_END)

    def _rotation(self):
        """Un RPT plus récent = le serveur a redémarré. On le lit depuis le début et on oublie le
        compteur : il est reparti à 0."""
        now = time.monotonic()
        if now - self._t_rotation < 1.0 and self.chemin and os.path.exists(self.chemin):
            return
        self._t_rotation = now
        dernier = self._dernier_rpt()
        if dernier and dernier != self.chemin:
            log.warning("NOUVEAU RPT %s (ancien %s) : serveur relancé, on se recale", dernier, self.chemin)
            self._basculer(dernier, depuis_debut=True)
            self.sync_n, self.n_confirme = None, None
            self.redemarrages += 1

    def _lire(self):
        self._rotation()
        if not self.f:
            return
        morceau = self.f.read()
        if not morceau:
            return
        self.tampon += morceau
        *lignes, self.tampon = self.tampon.split("\n")
        for l in lignes:
            self._ligne(l.rstrip("\r"))

    def _ligne(self, l):
        self.seq += 1
        if "[LABO]" not in l:
            if _RE_ERREUR.search(l):
                self.erreurs_seq.append(self.seq)
            return
        m = _RE_SYNC.search(l)
        if m:
            self.sync_n, self.sync_t, self.sync_seq = int(m.group(1)), time.monotonic(), self.seq
            return
        m = _RE_ECHO.search(l)
        if m:
            self.echos[int(m.group(2))] = (int(m.group(1)), int(m.group(3)), self.seq)
            return
        m = _RE_R.search(l)
        if m:
            nonce, cle = int(m.group(1)), m.group(2)
            try:
                nombres = [_nombre(t) for t in m.group(3).split()]
            except ValueError:
                self.malformees[nonce] = self.malformees.get(nonce, 0) + 1
                return
            self.lignes_r.setdefault(nonce, []).append((cle, nombres))

    # ---- ouverture
    def ouvrir(self, patience_ouverture: float = 8.0):
        dernier = self._dernier_rpt()
        if dernier is None:
            raise PontMort(f"aucun RPT dans {self.profil} : le serveur du labo ne tourne pas")
        self._basculer(dernier, depuis_debut=False)
        self._attendre_battement(patience_ouverture, apres_seq=self.seq)

    def fermer(self):
        if self.f:
            try:
                self.f.close()
            except Exception:
                pass
        self.f = None

    def _attendre_battement(self, patience, apres_seq):
        t0 = time.monotonic()
        while time.monotonic() - t0 < patience:
            self._lire()
            if self.sync_seq > apres_seq:
                return
            time.sleep(0.02)
        raise PontMort(f"aucun battement « [LABO] HMT_SYNC » en {patience:.0f} s dans {self.chemin} : "
                       "la mission Labo ne tourne pas, ou le serveur est mort")

    def _battement_frais(self):
        self._lire()
        if self.sync_n is None or time.monotonic() - self.sync_t > self.battement_max:
            self._attendre_battement(self.battement_max, apres_seq=self.seq)

    # ---- une commande
    def executer(self, corps: str, patience: float | None = None) -> dict:
        patience = self.patience if patience is None else patience
        self._battement_frais()
        # ⚠️ Le compteur de référence : le dernier reçu, SAUF si un battement postérieur dit autre
        # chose (serveur relancé -> 0 ; un autre écrivain -> plus loin). Alors on se recale.
        if self.n_confirme is None:
            base = self.sync_n
        elif self.sync_seq > self.conf_seq and self.sync_n != self.n_confirme:
            log.warning("RECALAGE : dernier reçu n=%s, battement n=%s", self.n_confirme, self.sync_n)
            base = self.sync_n
            self.recalages += 1
        else:
            base = self.n_confirme
        n = base + 1
        nonce = random.randrange(100000, 1000000)   # 6 chiffres : SQF écrit 1e+006 au-delà
        code = (f"private _labo_nonce = {nonce}; private _labo_k = 0; {corps} "
                f'diag_log format ["[LABO] ECHO %1 %2 %3", {n}, _labo_nonce, _labo_k];')
        if len(code.encode()) > PLAFOND_OCTETS:
            raise Refus(f"commande de {len(code.encode())} octets, plafond {PLAFOND_OCTETS}")
        cmd = os.path.join(self.pont, f"cmd_{n}.sqf")
        tmp = os.path.join(self.pont, f".tmp_{n}")
        seq0 = self.seq
        # Les commandes sont séquentielles : ce qui traîne d'une commande abandonnée ne nous
        # concerne plus (et ne doit pas être compté contre celle-ci).
        self.echos.clear()
        self.lignes_r.clear()
        self.malformees.clear()
        self.erreurs_seq.clear()
        with open(tmp, "w") as g:
            g.write(code + "\n")
        os.replace(tmp, cmd)                       # atomique
        t0 = time.monotonic()
        log.info("ENVOI n=%d nonce=%d : %s", n, nonce, corps)
        try:
            while time.monotonic() - t0 < patience:
                self._lire()
                if nonce in self.echos and self.echos[nonce][0] == n:
                    return self._recu(n, nonce, t0, seq0)
                time.sleep(0.02)
            self._diagnostiquer(n, t0, seq0)
        finally:
            _effacer(cmd)                          # prise ou non, elle ne doit jamais être rejouée

    def _recu(self, n, nonce, t0, seq0):
        _, k, seq_echo = self.echos.pop(nonce)
        lignes = self.lignes_r.pop(nonce, [])
        malf = self.malformees.pop(nonce, 0)
        self.n_confirme, self.conf_seq = n, seq_echo
        rtt = int((time.monotonic() - t0) * 1000)
        erreurs = sum(1 for s in self.erreurs_seq if seq0 < s <= seq_echo)
        self.erreurs_seq = [s for s in self.erreurs_seq if s > seq_echo]
        recu = {"instance": self.instance, "n_cmd": n, "n_sync_lu": self.sync_n, "rtt_ms": rtt,
                "nonce": nonce, "lignes": k, "erreurs_rpt": erreurs, "recalages": self.recalages,
                "redemarrages": self.redemarrages}
        log.info("REÇU n=%d rtt=%d ms lignes=%d erreurs=%d", n, rtt, k, erreurs)
        if malf or len(lignes) != k:
            raise Incomplet(f"reçu n={n} annonce {k} ligne(s), {len(lignes)} lue(s), {malf} illisible(s)")
        return {"recu": recu, "lignes": lignes}

    def _diagnostiquer(self, n, t0, seq0):
        """Pas de reçu. On attend un battement POSTÉRIEUR à l'envoi pour savoir si l'actuateur a
        pris la commande. Sans lui, on ne sait rien : c'est un pont mort, pas un « aucun »."""
        seq_envoi = self.seq
        try:
            self._attendre_battement(self.battement_max, apres_seq=seq_envoi)
        except PontMort:
            raise PontMort(f"commande n={n} sans reçu et plus aucun battement : le serveur du labo "
                           "est mort ou figé. On ne sait RIEN de l'état du monde.") from None
        erreurs = sum(1 for s in self.erreurs_seq if s > seq0)
        if self.sync_n is not None and self.sync_n >= n:
            self.n_confirme, self.conf_seq = self.sync_n, self.sync_seq
            raise SansRecu(f"commande n={n} prise par l'actuateur mais sans reçu : erreur SQF probable "
                           f"({erreurs} ligne(s) « Error » dans le RPT pendant la commande)")
        raise PontMort(f"commande n={n} jamais prise : l'actuateur est à n={self.sync_n}. Un autre "
                       "écrivain, ou un compteur décalé ; la commande a été effacée.")


def _effacer(chemin):
    try:
        os.remove(chemin)
    except FileNotFoundError:
        pass

def _nombre(t: str):
    v = float(t)
    if not math.isfinite(v):
        raise ValueError(t)
    return int(v) if v.is_integer() and abs(v) < 1e15 else v


# --- LA VÉRIFICATION DU SQF ----------------------------------------------------------------------
def verifier_sqf(code: str) -> str:
    """Refuse — ne nettoie jamais. Un SQF « réparé » en silence n'est plus celui qu'on a demandé."""
    if not isinstance(code, str) or not code.strip():
        raise Refus("code vide")
    if "\n" in code or "\r" in code:
        raise Refus("une seule ligne : le SQF brut ne passe pas par le préprocesseur")
    if "//" in code or "/*" in code:
        raise Refus("commentaire refusé : `call compile` ne retire pas les commentaires, "
                    "un seul `//` tue la commande entière sans une erreur visible")
    if code.lstrip().startswith("#"):
        raise Refus("directive de préprocesseur refusée : `call compile` ne la connaît pas")
    if "\x00" in code:
        raise Refus("octet nul refusé")
    if len(code.encode()) > PLAFOND_OCTETS - 600:
        raise Refus(f"code de {len(code.encode())} octets : plafond {PLAFOND_OCTETS - 600} "
                    "(au-delà la DLL rend __TOOBIG__). Un gros script va dans un fichier de la mission.")
    return code.strip()


def _num(v, lo, hi, nom):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise Refus(f"{nom} doit être un nombre, reçu {v!r}") from None
    if not math.isfinite(x) or not lo <= x <= hi:
        raise Refus(f"{nom} = {v!r} hors de [{lo} ; {hi}]")
    return x

def _ent(v, lo, hi, nom):
    x = _num(v, lo, hi, nom)
    if not float(x).is_integer():
        raise Refus(f"{nom} doit être entier, reçu {v!r}")
    return int(x)

def _une(lignes, cle, n_nombres):
    t = [v for c, v in lignes if c == cle]
    if len(t) != 1 or len(t[0]) != n_nombres:
        raise Incomplet(f"attendu une ligne {cle} à {n_nombres} nombres, lu {t!r}")
    return t[0]

def _refus_mission(lignes):
    for c, v in lignes:
        if c == "REFUS":
            code = int(v[0]) if v else 0
            raise Refus(f"la mission refuse : {REFUS_MISSION.get(code, f'code {code}')}")


def config_env() -> dict:
    """Surcharges de chemins et de délais, lues dans l'environnement SEULEMENT si HMT_LABO_TEST=1
    (le jouet). En service le labo parle à l'instance 9 et à rien d'autre."""
    e = os.environ
    if e.get("HMT_LABO_TEST") != "1":
        return {}
    cfg = {k: e[v] for k, v in (("profil", "HMT_LABO_PROFIL"), ("pont", "HMT_LABO_PONT"),
                                ("verrous", "HMT_LABO_VERROUS"), ("etat", "HMT_LABO_ETAT")) if v in e}
    for k, v in (("battement_max", "HMT_LABO_BATTEMENT_MAX"), ("patience", "HMT_LABO_PATIENCE"),
                 ("patience_ouverture", "HMT_LABO_PATIENCE_OUVERTURE")):
        if v in e:
            cfg[k] = float(e[v])
    return cfg


# --- LE LABO : les outils typés ------------------------------------------------------------------
class Labo:
    def __init__(self, instance: int = INSTANCE, *, profil: str = PROFIL, pont: str = PONT,
                 verrous: str = VERROUS, etat: str = ETAT, prendre_verrou_file: bool = True,
                 battement_max: float = BATTEMENT_MAX, patience: float = PATIENCE,
                 patience_ouverture: float = 8.0):
        if instance != INSTANCE:
            raise Refus(f"le labo ne parle qu'à l'instance {INSTANCE} ; {instance} appartient aux jobs")
        self.instance = instance
        self.pont = pont
        self.patience_ouverture = patience_ouverture
        self.ecrivain = VerrouEcrivain(os.path.join(etat, f"labo_i{instance}.ecrivain"))
        self.verrou = VerrouFile(verrous, instance) if prendre_verrou_file else None
        self.liaison = Liaison(profil, pont, instance=instance,
                               battement_max=battement_max, patience=patience)
        self.ouvert = False

    def ouvrir(self):
        self.ecrivain.prendre()
        try:
            if self.verrou:
                self.verrou.prendre()
            # Nous sommes le seul écrivain : ce qui traîne dans le dossier est un reste, qu'un
            # actuateur relancé rejouerait depuis cmd_1.
            os.makedirs(self.pont, exist_ok=True)
            for vieux in glob.glob(os.path.join(self.pont, "cmd_*.sqf")):
                _effacer(vieux)
            self.liaison.ouvrir(self.patience_ouverture)
        except BaseException:
            self.fermer()
            raise
        self.ouvert = True
        return self

    def fermer(self):
        self.liaison.fermer()
        if self.verrou:
            self.verrou.rendre()
        self.ecrivain.rendre()
        self.ouvert = False

    def __enter__(self):
        return self.ouvrir()

    def __exit__(self, *exc):
        self.fermer()

    def _exec(self, corps, patience=None):
        if not self.ouvert:
            raise ErreurLabo("labo non ouvert")
        return self.liaison.executer(corps, patience)

    # ---- outils
    def canari(self) -> dict:
        """Aller-retour à vide. Dit si le pont répond, en combien de ms, et si la mission jouée est
        bien la version de fonctions.sqf que ce module attend."""
        r = self._exec('["CANARI", [HMT_n, (if (isNil "LABO_VERSION") then {0} else {LABO_VERSION})]] '
                       "call LABO_R;")
        n_act, version = _une(r["lignes"], "CANARI", 2)
        if version == 0:
            raise Incomplet("la mission répond mais sans les fonctions du labo : ce n'est pas "
                            "Labo.Altis, ou fonctions.sqf n'a pas compilé (voir le RPT)")
        if version != VERSION_MISSION:
            raise Incomplet(f"mission en version {version}, le module attend {VERSION_MISSION} : "
                            "la mission jouée n'est pas celle du dépôt, relancer lancer_labo.sh")
        return {"pont": "vivant", "actuateur_n": n_act, "version_mission": version, "recu": r["recu"]}

    def etat(self, detail: int = 0) -> dict:
        """Compte le MONDE, pas une mémoire : TOTAL et CAMP sont relus dans Arma à chaque appel."""
        d = _ent(detail, 0, 200, "detail")
        r = self._exec(f"[{d}] call LABO_fnc_etat;")
        L = r["lignes"]
        tot = _une(L, "TOTAL", 5)
        camps = [v for c, v in L if c == "CAMP"]
        if len(camps) != 4 or any(len(v) != 3 for v in camps):
            raise Incomplet(f"attendu 4 lignes CAMP, lu {camps!r}")
        out = {"unites": tot[0], "non_joueurs": tot[1], "morts": tot[2], "joueurs": tot[3],
               "groupes": tot[4],
               "camps": {CAMPS[int(i)]: {"vivants": u, "groupes": g} for i, u, g in camps},
               "joueurs_pos": [{"x": v[0], "y": v[1], "z": v[2], "cap": v[3]}
                               for c, v in L if c == "JOUEUR" and len(v) == 4],
               "recu": r["recu"]}
        if d:
            out["detail"] = [{"camp": CAMPS[int(v[0])] if 0 <= v[0] < 4 else "?", "groupe": v[1],
                              "x": v[2], "y": v[3], "z": v[4], "degats": v[5]}
                             for c, v in L if c == "U" and len(v) == 6]
        return out

    def poser_groupe(self, camp: str, nombre: int, x: float, y: float, skill: float = 0.5) -> dict:
        if camp not in CAMPS_POSABLES:
            raise Refus(f"camp {camp!r} inconnu ; permis : {sorted(CAMPS_POSABLES)}")
        c = CAMPS_POSABLES[camp]
        n = _ent(nombre, 1, 24, "nombre")
        x, y = _num(x, 0, 31000, "x"), _num(y, 0, 31000, "y")
        s = _num(skill, 0, 1, "skill")
        r = self._exec(f"[{c}, {n}, {x:.2f}, {y:.2f}, {s:.3f}] call LABO_fnc_poser_groupe;")
        _refus_mission(r["lignes"])
        gi, cc, poses, lx, ly = _une(r["lignes"], "GROUPE", 5)
        if poses == 0:
            raise ErreurLabo(f"aucun homme posé sur {n} demandés (plafond de groupes du camp ?)")
        return {"groupe": gi, "camp": CAMPS[int(cc)], "poses": poses, "demandes": n,
                "complet": poses == n, "chef": {"x": lx, "y": ly}, "recu": r["recu"]}

    def poser_scene(self, bleus: int = 8, rouges: int = 8, distance: float = 220,
                    x: float = ANCRE_ALTIS[0], y: float = ANCRE_ALTIS[1],
                    skill: float = 0.5, combat: bool = True) -> dict:
        """La recette qui combat (26/08) : deux groupes face à face, COMBAT/RED/FULL, doMove par
        homme, `reveal` mutuel. Sans `reveal`, deux groupes à 220 m se tournent autour."""
        b, ro = _ent(bleus, 0, 24, "bleus"), _ent(rouges, 0, 24, "rouges")
        if b + ro == 0:
            raise Refus("scène vide : bleus + rouges = 0")
        d = _num(distance, 30, 1500, "distance")
        x, y = _num(x, 0, 31000, "x"), _num(y, 0, 31000, "y")
        s = _num(skill, 0, 1, "skill")
        r = self._exec(f"[{b}, {ro}, {d:.1f}, {x:.2f}, {y:.2f}, {s:.3f}, {1 if combat else 0}] "
                       "call LABO_fnc_poser_scene;")
        _refus_mission(r["lignes"])
        gb = _une(r["lignes"], "BLEU", 4)
        gr = _une(r["lignes"], "ROUGE", 4)
        return {"bleu": {"groupe": gb[0], "poses": gb[1], "demandes": b, "x": gb[2], "y": gb[3]},
                "rouge": {"groupe": gr[0], "poses": gr[1], "demandes": ro, "x": gr[2], "y": gr[3]},
                "distance": d, "combat": bool(combat), "recu": r["recu"]}

    def ordonner(self, groupe: int, ordre: str, x: float | None = None, y: float | None = None,
                 valeur: str | None = None) -> dict:
        gi = _ent(groupe, 0, 10000, "groupe")
        if ordre not in ORDRES:
            raise Refus(f"ordre {ordre!r} inconnu ; permis : {list(ORDRES)}")
        a = b = 0.0
        v = 0
        if ordre == "aller":
            if x is None or y is None:
                raise Refus("l'ordre « aller » veut x et y")
            a, b = _num(x, 0, 31000, "x"), _num(y, 0, 31000, "y")
        elif ordre in VALEURS:
            permis = VALEURS[ordre]
            if valeur is None or str(valeur).lower() not in permis:
                raise Refus(f"l'ordre « {ordre} » veut une valeur parmi {permis}")
            v = permis.index(str(valeur).lower())
        r = self._exec(f"[{gi}, {ORDRES[ordre]}, {a:.2f}, {b:.2f}, {v}] call LABO_fnc_ordonner;")
        _refus_mission(r["lignes"])
        g, cc, eff, o, lx, ly = _une(r["lignes"], "ORDRE", 6)
        return {"groupe": g, "camp": CAMPS[int(cc)] if 0 <= cc < 4 else "?", "effectif": eff,
                "ordre": ordre, "valeur": valeur, "chef": {"x": lx, "y": ly}, "recu": r["recu"]}

    def nettoyer(self) -> dict:
        """Table rase : tout homme non joueur, les morts, les armes au sol, les groupes vides.
        La table rase se PROUVE : si un seul homme reste, c'est une erreur, pas un succès."""
        r = self._exec("[] call LABO_fnc_nettoyer;", patience=max(12.0, self.liaison.patience))
        av = _une(r["lignes"], "AVANT", 3)
        ap = _une(r["lignes"], "APRES", 3)
        res = {"avant": {"hommes": av[0], "morts": av[1], "groupes": av[2]},
               "apres": {"hommes": ap[0], "morts": ap[1], "groupes": ap[2]}, "recu": r["recu"]}
        if ap[0] != 0:
            raise ErreurLabo(f"table rase NON prouvée : {ap[0]} homme(s) non joueur(s) restent ({res})")
        return res

    def sqf(self, code: str, *, par_humain: bool = False) -> dict:
        """SQF brut, une ligne. Réservé à une demande HUMAINE explicite : un agent qui écrit du SQF
        arbitraire dans Arma n'est plus instrumenté par rien."""
        if not par_humain:
            raise Refus("le SQF brut est réservé à une demande humaine explicite (par_humain=True)")
        c = verifier_sqf(code)
        corps = (f"private _labo_v = call {{ {c} }}; "
                 'if (!isNil "_labo_v") then { '
                 'if (_labo_v isEqualType 0) then { ["VAL", [_labo_v]] call LABO_R; }; '
                 'if (_labo_v isEqualType true) then { ["VAL", [[0, 1] select _labo_v]] call LABO_R; }; };')
        log.warning("SQF BRUT (humain) : %s", c)
        r = self._exec(corps)
        vals = [v for k, v in r["lignes"] if k == "VAL"]
        return {"valeur": vals[0][0] if vals and vals[0] else None,
                "lignes": [{"cle": k, "nombres": v} for k, v in r["lignes"] if k != "VAL"],
                "recu": r["recu"]}
