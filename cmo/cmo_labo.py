#!/usr/bin/env python3
"""cmo_labo — le module typé du pont HMT vers Command: Modern Operations 1.10 ( voie 2 : fichiers + événement Lua ).

LA CHAÎNE ( aucune automatisation d'interface, aucune pause : le jeu tourne en temps réel )
  ALLER     : on écrit <CMO>/Lua/hmt_pont/cmd_<n>.lua ; l'événement HMT_PONT ( 1 s de jeu ) le lit et l'exécute.
  RETOUR    : un reçu par commande, <CMO>/ImportExport/hmt_r_<n>.inst ( JSON de CMO, texte dans « Comments » ),
              écrit par ScenEdit_ExportInst : le moyen que PyCMO emploie sur la version Steam, où `io` est retirée.
  BATTEMENT : <CMO>/ImportExport/hmt_sync.inst toutes les 2 s.
  Le Lua vit dans cmo/lua/ ( hmt_pont.lua, installer.lua ), posé dans CMO par deployer.py.

CE QUE CE MODULE GARANTIT — les sept d'arma_labo, et deux qu'Arma ne permettait pas
  1. UN SEUL ÉCRIVAIN par dossier de pont ( VerrouEcrivain d'arma_labo ).
  2. UN REÇU PAR COMMANDE, terminé par FIN : un fichier lu pendant que CMO l'écrit n'est jamais pris pour une réponse.
  3. JAMAIS « AUCUN » À LA PLACE DE « PAS DE RÉPONSE » : PontMort, SansRecu, Incomplet, EchecLua.
  4. LE COMPTEUR SE RELIT DANS LE BATTEMENT. Un scénario rechargé repart à 0 ( les globales Lua ne survivent pas à
     une sauvegarde ) : on se recale, on ne fait jamais confiance à un n gardé en mémoire.
  5. QUE DES NOMBRES EN RETOUR. Seule la ligne ERR d'une commande en échec porte du texte, et elle va dans
     l'exception, pour un humain.
  6. UNE COMMANDE QUI N'A PAS ÉTÉ PRISE EST EFFACÉE, sinon l'événement la jouerait au réveil.
  7. LE LUA EST COMPILÉ AVANT D'ÊTRE ÉCRIT ( Lua 5.4 de lupa, la version de lua54.dll de CMO ), s'il est installé.
  NOUVEAU 8. L'ÉCHEC D'EXÉCUTION EST CERTAIN : le corps tourne sous pcall et le reçu porte son code ( 0 exécutée,
     1 erreur Lua, 2 ne compile pas, 3 refus ). Dans Arma, une erreur SQF au milieu laissait arriver le reçu.
  NOUVEAU 9. LE BUILD DE CMO EST CONTRÔLÉ À L'OUVERTURE : la branche bêta de Steam se met à jour seule ; un build
     que le banc pontcmo n'a pas certifié est refusé ( strict=False pour le banc lui-même ).

⚠️ LIMITE CONNUE : le battement suit le temps DU JEU. Jeu en pause = aucun battement = PontMort, et c'est juste :
en pause, rien ne bouge. Le banc pontcmo ( banc_pont.py ) est la seule preuve dans CMO ; porte_cmo.py prouve le
même Lua hors du jeu, face à faux_cmo.py.
"""
from __future__ import annotations

import glob
import json
import logging
import math
import os
import random
import re
import sys
import time

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(ICI), "labo"))
from arma_labo import (ErreurLabo, Refus, PontMort, SansRecu, Incomplet, Occupe,   # noqa: E402,F401
                       VerrouEcrivain, _num, _ent, _une, _effacer, _nombre)

log = logging.getLogger("cmo")

# --- OÙ VIT CMO SUR LA WS ( installé en natif le 12/08/2026, branche Steam public_beta_multiplayer ) --------------
CMO = "/mnt/e/SteamLibrary/steamapps/common/Command - Modern Operations"
BASE_WINDOWS = "E:/SteamLibrary/steamapps/common/Command - Modern Operations/"
PONT = f"{CMO}/Lua/hmt_pont"
SORTIE = f"{CMO}/ImportExport"
ETAT = "/mnt/data/hmt/etat"
FICHIER_CERTIF = "cmo_build_certifie.json"

VERSION_LUA = 8                     # = HMT_VERSION de lua/hmt_pont.lua
CAMPS = ("Stratis", "Malden")       # = HMT_CAMPS, même ordre ; index Lua = index Python + 1
GENRES = ("air", "navire", "sous_marin", "site", "vehicule")   # = HMT_GENRES ( Air, Ship, Submarine, Facility, Vehicle )
# = HMT_DOCTRINE : les réglages de doctrine qu'un outil peut toucher, par index ( le texte reste dans le Lua ).
DOCTRINE = ("quick_turnaround_for_aircraft", "air_operations_tempo", "bingo_threshold", "fuel_state_rtb",
            "weapon_state_rtb", "weapon_control_status_air", "weapon_control_status_surface",
            "weapon_control_status_subsurface", "weapon_control_status_land", "engage_opportunity_targets",
            "use_nuclear_weapons", "withdraw_on_damage", "withdraw_on_fuel")
TYPES_BILAN = {0: "autre", 1: "avion", 2: "navire", 3: "sous_marin", 4: "installation", 5: "arme", 6: "vehicule",
               7: "satellite"}                       # = HMT_TYPES
NUMERO_MAX = 99_999_999             # guerre_cmo décale les numéros de front par camp : chaque île numérote depuis 1
LECTEURS = {1: "loadfile", 2: "RunScript"}
REFUS_LUA = {1: "camp inconnu", 2: "genre inconnu", 3: "numéro déjà tenu par une unité vivante",
             4: "CMO refuse d'ajouter l'unité (dbid, loadout ou position)", 5: "numéro inconnu ou unité détruite",
             6: "CMO refuse la mission ou l'affectation", 7: "base inconnue ou détruite", 8: "base d'un autre camp",
             9: "réglage de doctrine inconnu", 10: "installation inconnue ( index hors de HMT_INSTALLATIONS )",
             11: "CMO refuse de renommer l'unité importée"}
# = SCRIPT de lua/installer.lua, au caractère près : c'est ce que l'événement exécute toutes les secondes.
ACTION_EVENEMENT = ("if HMT_tic == nil then ScenEdit_RunScript('hmt_pont/hmt_config.lua') "
                    "ScenEdit_RunScript('hmt_pont/hmt_pont.lua') end HMT_tic()")

BATTEMENT_MAX = 6.0                 # s ; l'événement bat toutes les 2 s de jeu
PATIENCE = 15.0                     # s ; après 30 s de silence l'événement ne cherche qu'une seconde sur dix
PLAFOND_OCTETS = 60000

_RE_SYNC = re.compile(r"^SYNC (\d+) (\d+) (\d+) (\d+) ([0-9.]*)$", re.M)
_RE_ECHO = re.compile(r"^ECHO (\d+) (\d+) (\d+) (\d+) (\d+) (\d+)$")
_RE_R = re.compile(r"^R ([A-Z_]+)((?: [-+0-9.eE]+)*)$")


ARGS_MAX = 180                      # valeurs par appel Lua : au-delà de ~250, « function or expression needs too many
                                    # registers » ( guerre réelle du 02/10 : HMT_etats de 300 numéros ne compilait pas )


def _appels(nom, tete, valeurs, par=1):
    """Des appels « nom(R, tete, v1, v2…) » de ARGS_MAX valeurs au plus, sans couper un groupe de `par` valeurs."""
    taille = max(par, ARGS_MAX // par * par)
    tete = f", {tete}" if tete else ""
    return [f"{nom}(R{tete}, {', '.join(valeurs[i:i + taille])})" for i in range(0, len(valeurs), taille)]


def signature_camps(camps) -> int:
    """= HMT_signature_camps du Lua : somme des octets UTF-8 pondérés par leur place, modulo 1 000 000 007."""
    s = 0
    for i, nom in enumerate(camps, 1):
        for j, b in enumerate(nom.encode("utf-8"), 1):
            s = (s + b * (i * 31 + j)) % 1_000_000_007
    return s


class EchecLua(ErreurLabo):
    """La commande a été prise et exécutée, et le Lua a échoué ( ou ne compile pas ) : on sait lequel, et pourquoi."""


def lire_inst(chemin: str) -> str | None:
    """Le champ Comments d'un .inst de CMO, ou None s'il manque ou s'il est en cours d'écriture."""
    try:
        with open(chemin, encoding="utf-8-sig") as f:
            d = json.load(f)
    except (OSError, ValueError):
        # absent, verrouillé, JSON pas fini… et, par WSL, OSError 61 « No data available » quand Windows écrit le
        # fichier au même instant ( 29/09, sonde des aérodromes ) : pas encore lisible, jamais une panne.
        return None
    c = d.get("Comments") if isinstance(d, dict) else None
    return c if isinstance(c, str) else None


def lire_recu(texte: str):
    """Un reçu -> dict. Sans FIN final, {"tronque": octets} : lire_inst n'a rendu qu'un JSON COMPLET ( un fichier en
    cours d'écriture ne se décode pas ), donc un texte sans FIN a été coupé par CMO, pas surpris en route.
    Une ligne R illisible compte comme malformée."""
    lignes = [l.strip() for l in texte.replace("\r", "").split("\n") if l.strip()]
    if not lignes or lignes[-1] != "FIN":
        return {"tronque": len(texte.encode())}
    echos = [m for m in (_RE_ECHO.match(l) for l in lignes) if m]
    if len(echos) != 1:
        return {"illisible": f"{len(echos)} ligne(s) ECHO"}
    n, nonce, k, code, detail, coeur = (int(x) for x in echos[0].groups())
    r, malf = [], 0
    for l in lignes:
        if not l.startswith("R "):
            continue
        m = _RE_R.match(l)
        try:
            r.append((m.group(1), [_nombre(t) for t in m.group(2).split()]))
        except (AttributeError, ValueError):
            malf += 1
    err = next((l[4:] for l in lignes if l.startswith("ERR ")), "")
    return {"n": n, "nonce": nonce, "k": k, "code": code, "detail": detail, "coeur": coeur, "lignes": r,
            "malformees": malf, "err": err}


def _compilateur():
    """Le compilateur Lua 5.4 de lupa, ou None s'il n'est pas installé ( le Lua dira alors lui-même code 2 )."""
    try:
        from lupa import lua54
    except ImportError:
        return None
    L = lua54.LuaRuntime(unpack_returned_tuples=True)
    return L.eval("function(s) local f, e = load(s, 'cmd', 't') if f then return true, '' end return false, e end")


# --- LA LIAISON : écrire cmd_N, lire le battement, apparier les reçus ------------------------------------------------
class Liaison:
    """Le coeur de l'événement ordonne tout : un battement de coeur c est écrit APRÈS les commandes de ce passage,
    un reçu porte le coeur du passage qui l'a exécuté. Une « vie » est un chargement du scénario : le coeur y
    repart d'en bas, et le compteur n aussi."""

    def __init__(self, pont: str = PONT, sortie: str = SORTIE, *, battement_max: float = BATTEMENT_MAX,
                 patience: float = PATIENCE, compiler: bool = True):
        self.pont, self.sortie = pont, sortie
        self.battement_max, self.patience = battement_max, patience
        self.compiler = _compilateur() if compiler else None
        self.sync_n = None          # compteur de l'actuateur, lu dans le dernier battement
        self.sync_coeur = None
        self.sync_t = 0.0           # instant où l'on a vu le coeur changer
        self.vie = 0
        self.lecteur = None
        self.build = None
        self.n_confirme = None      # dernier n dont on a reçu l'ECHO, avec le coeur et la vie de ce reçu
        self.conf_coeur = -1
        self.conf_vie = -1
        self.recalages = 0
        self.redemarrages = 0

    def _sync(self):
        texte = lire_inst(os.path.join(self.sortie, "hmt_sync.inst"))
        if not texte or not texte.rstrip().endswith("FIN"):
            return
        m = _RE_SYNC.search(texte)
        if not m:
            return
        n, coeur, lecteur, build = int(m.group(1)), int(m.group(2)), int(m.group(4)), m.group(5)
        if coeur == self.sync_coeur:
            return
        if self.sync_coeur is not None and coeur < self.sync_coeur:
            # Le coeur repart d'en bas : scénario rechargé ou CMO relancé. Le compteur est reparti à 0.
            log.warning("BATTEMENT REPARTI (%s -> %s) : scénario rechargé, on se recale", self.sync_coeur, coeur)
            self.vie += 1
            self.n_confirme = None
            self.redemarrages += 1
        self.sync_n, self.sync_coeur, self.sync_t = n, coeur, time.monotonic()
        self.lecteur, self.build = lecteur, build

    def _attendre(self, patience, coeur_min, vie):
        """Attend un battement de coeur >= coeur_min dans la même vie, ou n'importe quel battement d'une vie neuve."""
        t0 = time.monotonic()
        while time.monotonic() - t0 < patience:
            self._sync()
            if self.sync_coeur is not None and (self.vie != vie or self.sync_coeur >= coeur_min):
                return
            time.sleep(0.05)
        raise PontMort(f"aucun battement neuf en {patience:.0f} s dans {self.sortie}/hmt_sync.inst : CMO fermé, "
                       "jeu en pause, ou scénario sans l'événement HMT_PONT ( lancer hmt_pont/installer.lua )")

    def _suivant(self):
        return -1 if self.sync_coeur is None else self.sync_coeur + 1

    def ouvrir(self, patience_ouverture: float = 8.0):
        self._sync()
        self._attendre(patience_ouverture, self._suivant(), self.vie)

    def fermer(self):
        pass

    def _battement_frais(self):
        self._sync()
        if self.sync_n is None or time.monotonic() - self.sync_t > self.battement_max:
            self._attendre(self.battement_max, self._suivant(), self.vie)

    def verifier(self, code: str):
        if self.compiler is None:
            return
        ok, err = self.compiler(code)
        if not ok:
            raise Refus(f"le Lua ne compile pas, rien n'est parti vers CMO : {err}")

    def executer(self, corps: str, patience: float | None = None) -> dict:
        patience = self.patience if patience is None else patience
        self._battement_frais()
        # ⚠️ Référence : le dernier reçu, SAUF si un battement POSTÉRIEUR à ce reçu ( même vie, coeur plus grand ) dit
        # autre chose ( un autre écrivain ) ; ou si la vie a changé ( n_confirme est alors remis à None ).
        if self.n_confirme is None:
            base = self.sync_n
        elif self.vie == self.conf_vie and self.sync_coeur > self.conf_coeur and self.sync_n != self.n_confirme:
            log.warning("RECALAGE : dernier reçu n=%s, battement n=%s", self.n_confirme, self.sync_n)
            base = self.sync_n
            self.recalages += 1
        else:
            base = self.n_confirme
        n = base + 1
        nonce = random.randrange(100000, 1000000)
        code = f"HMT_commande({n}, {nonce}, function(R) {corps} end)\n"
        if len(code.encode()) > PLAFOND_OCTETS:
            raise Refus(f"commande de {len(code.encode())} octets, plafond {PLAFOND_OCTETS}")
        self.verifier(code)
        cmd = os.path.join(self.pont, f"cmd_{n}.lua")
        tmp = os.path.join(self.pont, f".tmp_{n}")
        recu = os.path.join(self.sortie, f"hmt_r_{n}.inst")
        _effacer(recu)                              # un reçu d'une vie antérieure ne répond pas à cette commande
        with open(tmp, "w", encoding="utf-8") as g:
            g.write(code)
        coeur0, vie0 = self.sync_coeur, self.vie
        os.replace(tmp, cmd)                        # atomique
        t0 = time.monotonic()
        log.info("ENVOI n=%d nonce=%d : %s", n, nonce, corps[:200])
        try:
            while time.monotonic() - t0 < patience:
                texte = lire_inst(recu)
                r = lire_recu(texte) if texte else None
                if r is not None and "tronque" in r:
                    raise Incomplet(f"reçu n={n} tronqué à {r['tronque']} octets : CMO a coupé le champ Comments "
                                    "( trop de lignes dans une seule commande )")
                if r is not None and "illisible" in r:
                    raise Incomplet(f"reçu n={n} illisible : {r['illisible']}")
                if r is not None and r["n"] == n and (r["nonce"] == nonce or (r["nonce"] == 0 and r["code"] == 2)):
                    return self._recu(r, n, nonce, t0)
                time.sleep(0.05)
            self._diagnostiquer(n, coeur0, vie0)
            # Prise, et un reçu arrivé APRÈS la patience ( commande longue : 500 poses, 29/09 ) : c'est une réponse.
            r = lire_recu(lire_inst(recu) or "") if os.path.exists(recu) else None
            if r is not None and "tronque" not in r and "illisible" not in r and r["n"] == n and r["nonce"] == nonce:
                log.warning("REÇU TARDIF n=%d ( après %.1f s )", n, time.monotonic() - t0)
                return self._recu(r, n, nonce, t0)
            raise SansRecu(f"commande n={n} prise par l'événement mais sans reçu : ScenEdit_ExportInst a échoué "
                           f"( voir ImportExport/hmt_panne.inst )")
        finally:
            _effacer(cmd)                           # prise ou non, elle ne doit jamais être rejouée
            _effacer(recu)

    def _recu(self, r, n, nonce, t0):
        self._sync()
        self.n_confirme, self.conf_coeur, self.conf_vie = n, r["coeur"], self.vie
        rtt = int((time.monotonic() - t0) * 1000)
        recu = {"n_cmd": n, "n_sync_lu": self.sync_n, "coeur": r["coeur"], "rtt_ms": rtt, "nonce": nonce,
                "lignes": r["k"], "recalages": self.recalages, "redemarrages": self.redemarrages,
                "lecteur": self.lecteur, "build": self.build}
        log.info("REÇU n=%d rtt=%d ms lignes=%d code=%d", n, rtt, r["k"], r["code"])
        if r["code"] == 1:
            raise EchecLua(f"commande n={n} exécutée, le Lua a échoué : {r['err']}")
        if r["code"] == 2:
            raise EchecLua(f"commande n={n} : le fichier ne compile pas dans CMO : {r['err']}")
        if r["code"] == 3:
            raise Refus(f"CMO refuse : {REFUS_LUA.get(r['detail'], 'code ' + str(r['detail']))}")
        if r["code"] != 0:
            raise Incomplet(f"reçu n={n} au code inconnu {r['code']}")
        if r["malformees"] or len(r["lignes"]) != r["k"]:
            raise Incomplet(f"reçu n={n} annonce {r['k']} ligne(s), {len(r['lignes'])} lue(s), "
                            f"{r['malformees']} illisible(s)")
        return {"recu": recu, "lignes": r["lignes"]}

    def _diagnostiquer(self, n, coeur0, vie0):
        """Pas de reçu. Il faut un battement d'un passage ENTIER après l'envoi ( coeur0 + 2 : le passage coeur0 + 1 a
        pu commencer avant ) pour savoir si l'événement a pris la commande. Sans lui, on ne sait rien : c'est un pont
        mort, pas un « aucun »."""
        try:
            self._attendre(self.battement_max, (coeur0 or 0) + 2, vie0)
        except PontMort:
            raise PontMort(f"commande n={n} sans reçu et plus aucun battement : CMO fermé, figé ou en pause. "
                           "On ne sait RIEN de l'état du monde.") from None
        if self.vie != vie0:
            raise PontMort(f"commande n={n} sans reçu : le scénario a été rechargé pendant l'attente ; la commande a "
                           "été effacée, on ne sait pas si elle a joué avant.")
        if self.sync_n is not None and self.sync_n >= n:
            self.n_confirme, self.conf_coeur, self.conf_vie = self.sync_n, self.sync_coeur, self.vie
            return                                       # prise : l'appelant relit le reçu une dernière fois
        raise PontMort(f"commande n={n} jamais prise : l'événement est à n={self.sync_n}. Un autre écrivain, ou un "
                       "compteur décalé ; la commande a été effacée.")


# --- LA CERTIFICATION DU BUILD -------------------------------------------------------------------------------------
def build_certifie(etat: str = ETAT) -> str | None:
    try:
        with open(os.path.join(etat, FICHIER_CERTIF)) as f:
            return json.load(f).get("build")
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def certifier(build: str, verdict: dict, etat: str = ETAT):
    os.makedirs(etat, exist_ok=True)
    tmp = os.path.join(etat, FICHIER_CERTIF + ".tmp")
    with open(tmp, "w") as f:
        json.dump({"build": build, "date": time.strftime("%Y-%m-%d %H:%M:%S"), "verdict": verdict}, f, indent=1)
    os.replace(tmp, os.path.join(etat, FICHIER_CERTIF))


# --- LE RECHARGEMENT : après deployer.py, sans console -------------------------------------------------------------
def recharger(*, pont: str = PONT, sortie: str = SORTIE, etat: str = ETAT, **kw) -> int:
    """Fait relire hmt_pont.lua à CMO par le pont lui-même : l'événement ne relit le Lua que si HMT_tic manque, il
    jouerait sinon l'ancien jusqu'au prochain chargement du scénario. Pas de contrôle de version à l'ouverture ( c'est
    ce qu'on répare ) ; la version jouée ensuite est rendue, et doit être VERSION_LUA."""
    ecrivain = VerrouEcrivain(os.path.join(etat, "cmo_pont.ecrivain"))
    os.makedirs(etat, exist_ok=True)
    ecrivain.prendre()
    try:
        li = Liaison(pont, sortie, **kw)
        li.ouvrir()
        li.executer("ScenEdit_RunScript('hmt_pont/hmt_config.lua') ScenEdit_RunScript('hmt_pont/hmt_pont.lua')")
        version = int(_une(li.executer("HMT_canari(R)")["lignes"], "CANARI", 4)[1])
    finally:
        ecrivain.rendre()
    if version != VERSION_LUA:
        raise Incomplet(f"CMO joue encore hmt_pont.lua en version {version} après relecture ( attendu {VERSION_LUA} ) : "
                        "il garde le Lua compilé ; recharger le scénario")
    return version


# --- LE LABO : les outils typés --------------------------------------------------------------------------------------
class Labo:
    def __init__(self, *, pont: str = PONT, sortie: str = SORTIE, etat: str = ETAT, strict: bool = True,
                 battement_max: float = BATTEMENT_MAX, patience: float = PATIENCE, patience_ouverture: float = 8.0,
                 compiler: bool = True, camps=CAMPS, installations=()):
        self.pont, self.sortie, self.etat, self.strict = pont, sortie, etat, strict
        self.camps = tuple(camps)
        self.installations = tuple(installations)       # = HMT_INSTALLATIONS ( deployer.py --installations )
        self.patience_ouverture = patience_ouverture
        self.ecrivain = VerrouEcrivain(os.path.join(etat, "cmo_pont.ecrivain"))
        self.liaison = Liaison(pont, sortie, battement_max=battement_max, patience=patience, compiler=compiler)
        self.ouvert = False
        self.version = None

    def ouvrir(self):
        os.makedirs(self.etat, exist_ok=True)
        self.ecrivain.prendre()
        try:
            # Nous sommes le seul écrivain : ce qui traîne est un reste, que l'événement rejouerait.
            os.makedirs(self.pont, exist_ok=True)
            for vieux in glob.glob(os.path.join(self.pont, "cmd_*.lua")) + glob.glob(os.path.join(self.sortie, "hmt_r_*.inst")):
                _effacer(vieux)
            self.liaison.ouvrir(self.patience_ouverture)
            self.ouvert = True
            self.version = self.canari()
            # le registre des numéros refait depuis les noms du scénario ouvert ( voir HMT_recensement )
            self.version["recenses"] = int(_une(self._exec("HMT_recensement(R)", patience=max(30.0, self.liaison.patience))["lignes"],
                                                "RECENSE", 1)[0])
        except BaseException:
            self.fermer()
            raise
        return self

    def fermer(self):
        self.liaison.fermer()
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
        """Aller-retour à vide. Dit si le pont répond, en combien de ms, quel Lua joue et sur quel build."""
        r = self._exec("HMT_canari(R)")
        n_act, version, n_camps, lecteur = _une(r["lignes"], "CANARI", 4)
        build = ".".join(str(int(x)) for x in next((v for c, v in r["lignes"] if c == "BUILD"), []))
        if version != VERSION_LUA:
            raise Incomplet(f"hmt_pont.lua joué en version {version}, le module attend {VERSION_LUA} : relancer "
                            "deployer.py, puis recharger le scénario ( CMO garde le Lua compilé )")
        sig = _une(r["lignes"], "CAMPS_SIG", 1)[0]
        if n_camps != len(self.camps) or sig != signature_camps(self.camps):
            raise Incomplet(f"CMO joue {int(n_camps)} camps ( signature {int(sig)} ), le module attend {list(self.camps)} "
                            f"( signature {signature_camps(self.camps)} ) : redéployer avec ces camps ( deployer.py --camps )")
        self._verifier_installations(r)
        certifie = build_certifie(self.etat)
        if build != certifie and self.strict:
            raise Incomplet(f"CMO en build {build}, le banc pontcmo a certifié {certifie} : Steam a mis CMO à jour. "
                            "Relancer cmo/banc_pont.py avant toute guerre.")
        temps = next((v[0] for c, v in r["lignes"] if c == "TEMPS" and v), None)   # heure du scénario, UTC Unix
        return {"pont": "vivant", "actuateur_n": n_act, "version_lua": version, "build": build,
                "build_certifie": certifie, "lecteur": LECTEURS.get(int(lecteur), "?"), "temps": temps, "recu": r["recu"]}

    def _verifier_installations(self, r):
        n_inst, sig_inst = _une(r["lignes"], "INST_SIG", 2)
        if n_inst != len(self.installations) or sig_inst != signature_camps(self.installations):
            raise Incomplet(f"CMO connaît {int(n_inst)} installations ( signature {int(sig_inst)} ), le module en attend "
                            f"{len(self.installations)} ( signature {signature_camps(self.installations)} ) : redéployer avec "
                            "le même théâtre ( deployer.py ), sinon un index importerait la mauvaise base")

    def etat_camps(self) -> dict:
        """Compte le JEU, pas une mémoire : relu dans CMO à chaque appel. total = -1 si CMO ne rend pas la liste."""
        r = self._exec("HMT_etat(R)")
        camps = [v for c, v in r["lignes"] if c == "CAMP"]
        if len(camps) != len(self.camps) or any(len(v) != 3 for v in camps):
            raise Incomplet(f"attendu {len(self.camps)} lignes CAMP, lu {camps!r}")
        return {"camps": {self.camps[int(i) - 1]: {"hmt_vivants": int(v), "unites": int(t)} for i, v, t in camps},
                "recu": r["recu"]}

    def poser(self, camp: str, genre: str, dbid: int, numero: int, lat: float, lon: float,
              alt: float = 0.0, loadout: int = 0) -> dict:
        """Une unité du catalogue de CMO ( dbid ), nommée HMT-<numéro> : le numéro de front du moteur."""
        if camp not in self.camps:
            raise Refus(f"camp {camp!r} inconnu ; permis : {list(self.camps)}")
        if genre not in GENRES:
            raise Refus(f"genre {genre!r} inconnu ; permis : {list(GENRES)}")
        c, g = self.camps.index(camp) + 1, GENRES.index(genre) + 1
        d = _ent(dbid, 1, 10_000_000, "dbid")
        k = _ent(numero, 1, NUMERO_MAX, "numero")
        la, lo = _num(lat, -90, 90, "lat"), _num(lon, -180, 180, "lon")
        a = _num(alt, 0, 30000, "alt")
        lod = _ent(loadout, 0, 10_000_000, "loadout")
        r = self._exec(f"HMT_poser(R, {c}, {g}, {d}, {k}, {la:.7f}, {lo:.7f}, {a:.1f}, {lod})")
        k2, c2, la2, lo2 = _une(r["lignes"], "POSE", 4)
        return {"numero": int(k2), "camp": self.camps[int(c2) - 1], "lat": la2, "lon": lo2, "recu": r["recu"]}

    def hostiles(self, camp_a: str, camp_b: str) -> dict:
        """Les deux camps se voient hostiles dans CMO ( relu, pas supposé )."""
        if camp_a not in self.camps or camp_b not in self.camps or camp_a == camp_b:
            raise Refus(f"deux camps distincts parmi {list(self.camps)} : {camp_a!r}, {camp_b!r}")
        r = self._exec(f"HMT_hostiles(R, {self.camps.index(camp_a) + 1}, {self.camps.index(camp_b) + 1})")
        _, _, ab, ba = _une(r["lignes"], "HOSTILES", 4)
        if not (ab and ba):
            raise Incomplet(f"posture relue non hostile dans CMO ( {camp_a}->{camp_b} {ab}, {camp_b}->{camp_a} {ba} )")
        return {"hostiles": True, "recu": r["recu"]}

    def aller(self, numero: int, lat: float, lon: float) -> dict:
        k = _ent(numero, 1, NUMERO_MAX, "numero")
        la, lo = _num(lat, -90, 90, "lat"), _num(lon, -180, 180, "lon")
        r = self._exec(f"HMT_aller(R, {k}, {la:.7f}, {lo:.7f})")
        k2, la2, lo2 = _une(r["lignes"], "ORDRE", 3)
        return {"numero": int(k2), "lat": la2, "lon": lo2, "recu": r["recu"]}

    def poser_base_lots(self, lots) -> dict:
        """Des avions posés sur leur base, en UN envoi. lots : [ ( camp, dbid, loadout, numéro de la base, [ numéros ] ) ].
        La base est une installation HMT du même camp, posée avant ( poser, genre « site » )."""
        corps, n = [], 0
        for camp, dbid, loadout, base, ks in lots:
            if camp not in self.camps:
                raise Refus(f"camp {camp!r} inconnu")
            if not ks:
                continue
            corps += _appels("HMT_poser_base_lot", f"{self.camps.index(camp) + 1}, {_ent(dbid, 1, 10_000_000, 'dbid')}, "
                             f"{_ent(loadout, 0, 10_000_000, 'loadout')}, {_ent(base, 1, NUMERO_MAX, 'base')}",
                             [str(_ent(k, 1, NUMERO_MAX, 'numero')) for k in ks])
            n += len(ks)
        if not corps:
            return {"poses": [], "refus": {}}
        r = self._exec(" ".join(corps))
        out = {"poses": [int(v[0]) for k, v in r["lignes"] if k == "POSE"],
               "refus": {int(v[0]): int(v[1]) for k, v in r["lignes"] if k == "REFUSE"}, "recu": r["recu"]}
        if len(out["poses"]) + len(out["refus"]) != n:
            raise Incomplet(f"{n} avions à poser sur base : {len(out['poses'])} posés, {len(out['refus'])} refusés")
        return out

    def poser_lots(self, lots) -> dict:
        """Plusieurs lots ( un par camp, par exemple ) en UN envoi. lots : [ ( camp, genre, dbid, [ ( numéro, lat, lon ) ],
        alt, loadout ) ]. Rend les numéros posés et les refus { numéro : code REFUS_LUA, 0 = erreur Lua }."""
        corps, n = [], 0
        for camp, genre, dbid, poses, alt, loadout in lots:
            if camp not in self.camps or genre not in GENRES:
                raise Refus(f"camp {camp!r} ou genre {genre!r} inconnu")
            if not poses:
                continue
            c, g = self.camps.index(camp) + 1, GENRES.index(genre) + 1
            d, a = _ent(dbid, 1, 10_000_000, "dbid"), _num(alt, 0, 30000, "alt")
            lod = _ent(loadout, 0, 10_000_000, "loadout")
            args = []
            for k, la, lo in poses:
                args += [str(_ent(k, 1, NUMERO_MAX, "numero")), f"{_num(la, -90, 90, 'lat'):.7f}",
                         f"{_num(lo, -180, 180, 'lon'):.7f}"]
            corps += _appels("HMT_poser_lot", f"{c}, {g}, {d}, {a:.1f}, {lod}", args, par=3)
            n += len(poses)
        if not corps:
            return {"poses": [], "refus": {}}
        r = self._exec(" ".join(corps))
        poses_ok = [int(v[0]) for k, v in r["lignes"] if k == "POSE"]
        refus = {int(v[0]): int(v[1]) for k, v in r["lignes"] if k == "REFUSE"}
        if len(poses_ok) + len(refus) != n:
            raise Incomplet(f"lots de {n} unités : {len(poses_ok)} posées, {len(refus)} refusées")
        return {"poses": poses_ok, "refus": refus, "recu": r["recu"]}

    def poser_lot(self, camp: str, genre: str, dbid: int, poses, alt: float = 0.0, loadout: int = 0) -> dict:
        """Un lot du même type en UN envoi. poses : [ ( numéro, lat, lon ) ]."""
        return self.poser_lots([(camp, genre, dbid, poses, alt, loadout)])

    def aller_tous(self, ordres) -> dict:
        """Tous les ordres de déplacement d'un tour en UN envoi. ordres : [ ( lat, lon, [ numéros ] ) ]."""
        corps, n = [], 0
        for la, lo, ks in ordres:
            if not ks:
                continue
            ks = [str(_ent(k, 1, NUMERO_MAX, "numero")) for k in ks]
            corps += _appels("HMT_aller_tous", f"{_num(la, -90, 90, 'lat'):.7f}, {_num(lo, -180, 180, 'lon'):.7f}", ks)
            n += len(ks)
        if not corps:
            return {"ordonnes": [], "absents": []}
        r = self._exec(" ".join(corps))
        out = {"ordonnes": [int(v[0]) for k, v in r["lignes"] if k == "ORDRE"],
               "absents": [int(v[0]) for k, v in r["lignes"] if k == "ABSENT"], "recu": r["recu"]}
        if len(out["ordonnes"]) + len(out["absents"]) != n:
            raise Incomplet(f"{n} ordres envoyés, {len(out['ordonnes'])} faits, {len(out['absents'])} absents")
        return out

    def journal_messages(self, ident: int) -> str:
        """Le journal des messages de CMO part dans Logs/hmt_messages_<ident>.txt ( chemin rendu, vu d'ici ). C'est là que
        CMO dit qui a tiré sur qui, et pourquoi un avion est perdu."""
        k = _ent(ident, 1, 999_999_999_999, "ident")          # AAAAMMJJhhmm : 12 chiffres
        _une(self._exec(f"HMT_journal(R, {k})")["lignes"], "JOURNAL", 1)
        return os.path.join(CMO, "Logs", f"hmt_messages_{k}.txt")

    def missions(self, patrouilles=(), affectations=()) -> dict:
        """Toutes les missions d'un tour en UN envoi. patrouilles : [ ( id, camp, lat, lon, demi_km [ , tiers ] ) ] ( créée
        au premier appel, déplacée ensuite ; tiers 1 = règle du tiers de CMO, 0 = tout le paquet part ) ;
        affectations : [ ( id, [ numéros ] ) ]."""
        corps, n_pat, n_aff = [], 0, 0
        for i, camp, la, lo, dk, *tiers in patrouilles:
            if camp not in self.camps:
                raise Refus(f"camp {camp!r} inconnu")
            corps.append(f"HMT_patrouille(R, {_ent(i, 1, 9999, 'id')}, {self.camps.index(camp) + 1}, "
                         f"{_num(la, -90, 90, 'lat'):.7f}, {_num(lo, -180, 180, 'lon'):.7f}, {_num(dk, 1, 200, 'demi_km'):.2f}"
                         + (f", {1 if tiers[0] else 0})" if tiers else ")"))
            n_pat += 1
        for i, ks in affectations:
            if ks:
                corps += _appels("HMT_affecter", str(_ent(i, 1, 9999, 'id')), [str(_ent(k, 1, NUMERO_MAX, 'numero')) for k in ks])
                n_aff += len(ks)
        if not corps:
            return {"patrouilles": [], "affectes": [], "absents": [], "refus": []}
        r = self._exec(" ".join(corps))
        out = {"patrouilles": [(int(v[0]), bool(v[2])) for k, v in r["lignes"] if k == "PATROUILLE"],
               "affectes": [int(v[0]) for k, v in r["lignes"] if k == "AFFECTE"],
               "absents": [int(v[0]) for k, v in r["lignes"] if k == "ABSENT"],
               "refus": [int(v[0]) for k, v in r["lignes"] if k == "REFUSE"], "recu": r["recu"]}
        if len(out["patrouilles"]) != n_pat or len(out["affectes"]) + len(out["absents"]) + len(out["refus"]) != n_aff:
            raise Incomplet(f"missions : {n_pat} patrouilles et {n_aff} affectations envoyées, reçu {out}")
        return out

    def frappes(self, frappes=(), affectations=()) -> dict:
        """Les missions de frappe d'un tour en UN envoi. frappes : [ ( id, camp, [ numéros des cibles ennemies ] ) ] ( créée,
        activée et réglée en vols de deux au premier appel ; les cibles s'ajoutent ) ; affectations : [ ( id, [ numéros ] ) ]."""
        corps, n_f, n_c, n_a = [], 0, 0, 0
        for i, camp, cibles in frappes:
            if camp not in self.camps:
                raise Refus(f"camp {camp!r} inconnu")
            ks = [str(_ent(k, 1, NUMERO_MAX, "cible")) for k in cibles]
            corps += (_appels("HMT_frappe", f"{_ent(i, 1, 9999, 'id')}, {self.camps.index(camp) + 1}", ks) if ks
                      else [f"HMT_frappe(R, {_ent(i, 1, 9999, 'id')}, {self.camps.index(camp) + 1})"])
            n_f += 1
            n_c += len(ks)
        for i, ks in affectations:
            if ks:
                corps += _appels("HMT_affecter_frappe", str(_ent(i, 1, 9999, 'id')),
                                 [str(_ent(k, 1, NUMERO_MAX, 'numero')) for k in ks])
                n_a += len(ks)
        if not corps:
            return {"frappes": [], "cibles": [], "affectes": [], "absents": [], "refus": []}
        r = self._exec(" ".join(corps))
        par_id = {}
        for k, v in r["lignes"]:
            if k == "FRAPPE":                            # une ligne par appel : une frappe à beaucoup de cibles en fait plusieurs
                i0, neuve, n = int(v[0]), bool(v[2]), int(v[3])
                a = par_id.get(i0)
                par_id[i0] = (i0, neuve if a is None else a[1], n + (a[2] if a else 0))
        out = {"frappes": list(par_id.values()),
               "cibles": [int(v[0]) for k, v in r["lignes"] if k == "CIBLE"],
               "affectes": [int(v[0]) for k, v in r["lignes"] if k == "AFFECTE"],
               "absents": [int(v[0]) for k, v in r["lignes"] if k == "ABSENT"],
               "refus": [int(v[0]) for k, v in r["lignes"] if k == "REFUSE"], "recu": r["recu"]}
        if len(out["frappes"]) != n_f or len(out["cibles"]) + len(out["affectes"]) + len(out["absents"]) + len(out["refus"]) != n_c + n_a:
            raise Incomplet(f"frappes : {n_f} missions, {n_c} cibles, {n_a} affectations envoyées, reçu {out}")
        return out

    def escortes(self, lots) -> dict:
        """Des chasseurs en escorte de frappes, en UN envoi. lots : [ ( id de la frappe, [ numéros ] ) ]."""
        corps, n = [], 0
        for i, ks in lots:
            if ks:
                corps += _appels("HMT_escorter", str(_ent(i, 1, 9999, "id")), [str(_ent(k, 1, NUMERO_MAX, "numero")) for k in ks])
                n += len(ks)
        if not corps:
            return {"escortes": [], "absents": [], "refus": []}
        r = self._exec(" ".join(corps))
        out = {"escortes": [int(v[0]) for k, v in r["lignes"] if k == "ESCORTE"],
               "absents": [int(v[0]) for k, v in r["lignes"] if k == "ABSENT"],
               "refus": [int(v[0]) for k, v in r["lignes"] if k == "REFUSE"], "recu": r["recu"]}
        if len(out["escortes"]) + len(out["absents"]) + len(out["refus"]) != n:
            raise Incomplet(f"{n} escorteurs envoyés, reçu {out}")
        return out

    def vus(self, camp, numeros) -> dict:
        """Le brouillard de guerre : { numéro : ( classification 0-4, âge s, lat, lon, sommets d'incertitude ) } des unités
        adverses que `camp` voit dans CMO ; une unité absente du résultat n'est pas détectée."""
        if camp not in self.camps:
            raise Refus(f"camp {camp!r} inconnu")
        ks = [str(_ent(k, 1, NUMERO_MAX, "numero")) for k in numeros]
        if not ks:
            return {"vus": {}}
        appels = _appels("HMT_vus", str(self.camps.index(camp) + 1), ks)
        r = self._exec(" ".join(appels))
        out = {"vus": {int(v[0]): (int(v[1]), float(v[2]), float(v[3]), float(v[4]), int(v[5]))
                       for c, v in r["lignes"] if c == "VU"}, "recu": r["recu"]}
        if sum(1 for c, _ in r["lignes"] if c == "VUS") != len(appels):
            raise Incomplet(f"vus : {len(appels)} appels, reçu {r['lignes'][-3:]}")
        return out

    def clore(self, lots) -> dict:
        """Fermer des frappes, en UN envoi. lots : [ ( camp, id ) ]. Rend { id : 1 effacée, 2 désactivée, 0 absente }."""
        par_camp = {}
        for camp, i in lots:
            if camp not in self.camps:
                raise Refus(f"camp {camp!r} inconnu")
            par_camp.setdefault(camp, []).append(str(_ent(i, 1, 9999, "id")))
        if not par_camp:
            return {"clos": {}}
        corps = []
        for camp, ids in par_camp.items():
            corps += _appels("HMT_clore", str(self.camps.index(camp) + 1), ids)
        r = self._exec(" ".join(corps))
        out = {"clos": {int(v[0]): int(v[1]) for c, v in r["lignes"] if c == "CLOS"}, "recu": r["recu"]}
        if len(out["clos"]) != len({i for _, i in lots}):
            raise Incomplet(f"{len(lots)} frappes à fermer, reçu {out}")
        return out

    def charger(self, lots) -> dict:
        """Réarmer des avions posés, en UN envoi. lots : [ ( numéro, chargement, minutes de préparation ) ]. Rend
        { numéro : chargement relu } ( 3 = sans armes : le dépôt n'avait pas les armes ) et les absents."""
        args = []
        for k, lo, mn in lots:
            args += [str(_ent(k, 1, NUMERO_MAX, "numero")), str(_ent(lo, 1, 10_000_000, "chargement")), str(_ent(mn, 0, 10_000, "minutes"))]
        if not args:
            return {"charges": {}, "absents": []}
        r = self._exec(" ".join(_appels("HMT_charger", "", args, par=3)))
        out = {"charges": {int(v[0]): int(v[3]) for c, v in r["lignes"] if c == "CHARGE"},
               "absents": [int(v[0]) for c, v in r["lignes"] if c == "ABSENT"], "recu": r["recu"]}
        if len(out["charges"]) + len(out["absents"]) != len(lots):
            raise Incomplet(f"{len(lots)} réarmements envoyés, reçu {out}")
        return out

    def positions(self, mini: int | None = None, maxi: int | None = None) -> dict:
        """{ camp : [ ( numéro, lat, lon, alt ) ] } des vivants, et { camp : [ numéro ] } des morts depuis le dernier
        relevé, pour les numéros de [ mini, maxi ] ( tous sans bornes ). Un mort n'est rendu qu'une fois : c'est le moteur
        qui le garde. Les éléments fixes des vraies bases restent hors bornes : morts par le journal, dégâts par etats()."""
        bornes = ""
        if mini is not None or maxi is not None:
            bornes = f", {_ent(mini or 1, 1, NUMERO_MAX, 'mini')}, {_ent(maxi or NUMERO_MAX, 1, NUMERO_MAX, 'maxi')}"
        r = self._exec(f"HMT_positions(R{bornes})", patience=max(10.0, self.liaison.patience))
        vivants, morts = {c: [] for c in self.camps}, {c: [] for c in self.camps}
        for cle, v in r["lignes"]:
            if cle == "U":
                if len(v) != 5:
                    raise Incomplet(f"ligne U à {len(v)} nombres : {v!r}")
                vivants[self.camps[int(v[0]) - 1]].append((int(v[1]), v[2], v[3], v[4]))
            elif cle == "MORT":
                if len(v) != 2:
                    raise Incomplet(f"ligne MORT à {len(v)} nombres : {v!r}")
                morts[self.camps[int(v[0]) - 1]].append(int(v[1]))
        return {"vivants": vivants, "morts": morts, "recu": r["recu"]}

    def nettoyer(self) -> dict:
        """Table rase des unités HMT. Elle se PROUVE : une seule unité HMT restante est une erreur, pas un succès.
        CMO retire une unité supprimée au passage suivant ( sonde du 29/09 ) : le recompte est une AUTRE commande, et
        son reçu doit venir d'un passage ultérieur ( coeur plus grand ), sinon la preuve ne vaut rien."""
        r = self._exec("HMT_nettoyer(R)", patience=max(10.0, self.liaison.patience))
        avant, acceptees = _une(r["lignes"], "NETTOYE", 2)
        if acceptees != avant:
            raise ErreurLabo(f"CMO a refusé {int(avant - acceptees)} suppression(s) sur {int(avant)}")
        r2 = self._exec("HMT_recompter(R)")
        if r2["recu"]["coeur"] <= r["recu"]["coeur"]:
            raise Incomplet("recompte fait dans le passage de la suppression : CMO n'a pas encore retiré les unités")
        (restantes,) = _une(r2["lignes"], "RESTANTES", 1)
        if restantes != 0:
            raise ErreurLabo(f"table rase NON prouvée : {int(restantes)} unité(s) HMT restent sur {int(avant)}")
        return {"avant": int(avant), "apres": 0, "recu": r2["recu"]}

    # ---- v8 : la guerre réelle ( 02/10 ) -------------------------------------------------------------------------
    def armer(self, lots) -> dict:
        """Remplir des dépôts en UN envoi. lots : [ ( numéro du dépôt, loadout, packs ) ] ; un pack = les armes d'un
        chargement complet ( ScenEdit_FillMagsForLoadout ). Rend { numéro : armes ajoutées } et les absents."""
        args, n = [], 0
        for k, lo, p in lots:
            args += [str(_ent(k, 1, NUMERO_MAX, "numero")), str(_ent(lo, 1, 10_000_000, "loadout")), str(_ent(p, 1, 10_000, "packs"))]
            n += 1
        if not n:
            return {"armes": {}, "absents": []}
        r = self._exec(" ".join(_appels("HMT_armer", "", args, par=3)))
        out = {"armes": {int(v[0]): int(v[3]) for c, v in r["lignes"] if c == "ARME"},
               "absents": [int(v[0]) for c, v in r["lignes"] if c == "ABSENT"], "recu": r["recu"]}
        if len(out["armes"]) + len(out["absents"]) != len({k for k, _, _ in lots}):
            raise Incomplet(f"{n} dépôts à armer, reçu {out}")
        return out

    def stocks(self, numeros) -> dict:
        """{ numéro : { arme : ( courant, capacité ) } } relus dans les magasins de CMO, et les absents ( détruits )."""
        ks = [str(_ent(k, 1, NUMERO_MAX, "numero")) for k in numeros]
        if not ks:
            return {"stocks": {}, "absents": []}
        r = self._exec(" ".join(_appels("HMT_stocks", "", ks)))
        st, annonces = {}, {}
        for c, v in r["lignes"]:
            if c == "STOCK":
                st.setdefault(int(v[0]), {})[int(v[1])] = (int(v[2]), int(v[3]))
            elif c == "MAGASINS":
                annonces[int(v[0])] = int(v[1])
                st.setdefault(int(v[0]), {})
        absents = [int(v[0]) for c, v in r["lignes"] if c == "ABSENT"]
        for k, n in annonces.items():
            if len(st[k]) != n:
                raise Incomplet(f"dépôt {k} : {n} lignes de stock annoncées, {len(st[k])} lues")
        if len(annonces) + len(absents) != len(set(ks)):
            raise Incomplet(f"{len(ks)} dépôts relus, {len(annonces)} rendus, {len(absents)} absents")
        return {"stocks": st, "absents": absents, "recu": r["recu"]}

    def bilan(self, camp: str) -> dict:
        """Pertes et dépenses d'un camp telles que CMO les compte : { ( type, dbid ) : nombre }, type de TYPES_BILAN."""
        if camp not in self.camps:
            raise Refus(f"camp {camp!r} inconnu")
        r = self._exec(f"HMT_bilan(R, {self.camps.index(camp) + 1})")
        pertes = {(TYPES_BILAN.get(int(v[1]), "autre"), int(v[2])): int(v[3]) for c, v in r["lignes"] if c == "PERTE"}
        depenses = {(TYPES_BILAN.get(int(v[1]), "autre"), int(v[2])): int(v[3]) for c, v in r["lignes"] if c == "DEPENSE"}
        _, np, nd = _une(r["lignes"], "BILAN", 3)
        if len(pertes) != np or len(depenses) != nd:
            raise Incomplet(f"bilan de {camp} : {int(np)} pertes et {int(nd)} dépenses annoncées, {len(pertes)} et {len(depenses)} lues")
        return {"pertes": pertes, "depenses": depenses, "recu": r["recu"]}

    def doctrine(self, camp: str, cle: str, valeur: int) -> dict:
        """Un réglage de doctrine du camp ( cle dans DOCTRINE ), relu dans CMO après écriture."""
        if camp not in self.camps:
            raise Refus(f"camp {camp!r} inconnu")
        if cle not in DOCTRINE:
            raise Refus(f"réglage de doctrine {cle!r} hors de la liste permise {list(DOCTRINE)}")
        v = _ent(valeur, 0, 100, "valeur")
        r = self._exec(f"HMT_doctrine(R, {self.camps.index(camp) + 1}, {DOCTRINE.index(cle) + 1}, {v})")
        _, _, lu = _une(r["lignes"], "DOCTRINE", 3)
        if int(lu) != v:
            raise Incomplet(f"doctrine {cle} de {camp} : écrit {v}, relu {int(lu)} dans CMO")
        return {"cle": cle, "valeur": int(lu), "recu": r["recu"]}

    def importer(self, camp: str, fichier: str) -> dict:
        """Une vraie installation livrée avec CMO ( fichier de la liste du théâtre, déployée avec le Lua ), importée dans
        le camp sous ses noms d'origine. adopter() la numérote ensuite, dans une autre commande."""
        if camp not in self.camps:
            raise Refus(f"camp {camp!r} inconnu")
        if fichier not in self.installations:
            raise Refus(f"installation {fichier!r} hors de la liste du théâtre")
        r = self._exec(f"HMT_importer(R, {self.camps.index(camp) + 1}, {self.installations.index(fichier) + 1})")
        _, _, n = _une(r["lignes"], "IMPORTE", 3)
        if n < 1:
            raise Incomplet(f"CMO n'a importé aucun élément de {fichier!r} ( rendu {n} )")
        return {"fichier": fichier, "elements": int(n), "recu": r["recu"]}

    def adopter(self, camp: str, premier: int) -> dict:
        """Numérote HMT-<premier>… les unités du camp qui ne sont pas encore HMT ( l'installation qu'on vient d'importer ).
        Rend [ ( numéro, dbid, lat, lon, groupe ) ] : groupe = la base elle-même, qui accueille les avions."""
        if camp not in self.camps:
            raise Refus(f"camp {camp!r} inconnu")
        k0 = _ent(premier, 1, NUMERO_MAX, "premier")
        r = self._exec(f"HMT_adopter(R, {self.camps.index(camp) + 1}, {k0})", patience=max(20.0, self.liaison.patience))
        el = [(int(v[0]), int(v[1]), v[2], v[3], bool(v[4])) for c, v in r["lignes"] if c == "ADOPTE"]
        _, _, n = _une(r["lignes"], "ADOPTES", 3)
        if len(el) != n or [e[0] for e in el] != list(range(k0, k0 + int(n))):
            raise Incomplet(f"adoption : {int(n)} annoncées, {len(el)} lues, numéros {[e[0] for e in el][:5]}…")
        return {"elements": el, "recu": r["recu"]}

    def etats(self, numeros) -> dict:
        """{ numéro : ( dégâts en %, feu, inondation ) } relus dans CMO, et les absents ( détruits )."""
        ks = [str(_ent(k, 1, NUMERO_MAX, "numero")) for k in numeros]
        if not ks:
            return {"etats": {}, "absents": []}
        r = self._exec(" ".join(_appels("HMT_etats", "", ks)))
        out = {"etats": {int(v[0]): (v[1], bool(v[2]), bool(v[3])) for c, v in r["lignes"] if c == "ETAT"},
               "absents": [int(v[0]) for c, v in r["lignes"] if c == "ABSENT"], "recu": r["recu"]}
        if len(out["etats"]) + len(out["absents"]) != len(set(ks)):
            raise Incomplet(f"{len(ks)} états demandés, {len(out['etats'])} rendus, {len(out['absents'])} absents")
        return out

    def lua(self, code: str, *, par_humain: bool = False, patience: float | None = None) -> dict:
        """Lua brut, dans le corps d'une commande ( `R(CLE, {nombres})` pour rendre ). Réservé à une demande HUMAINE
        explicite : un agent qui écrit du Lua arbitraire dans CMO n'est plus instrumenté par rien."""
        if not par_humain:
            raise Refus("le Lua brut est réservé à une demande humaine explicite (par_humain=True)")
        if not isinstance(code, str) or not code.strip():
            raise Refus("code vide")
        log.warning("LUA BRUT (humain) : %s", code[:300])
        r = self._exec(code, patience)
        return {"lignes": [{"cle": k, "nombres": v} for k, v in r["lignes"]], "recu": r["recu"]}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    with Labo(strict=False) as l:
        print(json.dumps(l.version, ensure_ascii=False, indent=1))
        print(json.dumps(l.etat_camps(), ensure_ascii=False, indent=1))
