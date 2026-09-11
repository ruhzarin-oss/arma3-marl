#!/usr/bin/env python3
"""mcp_arma — le serveur MCP du LABO Arma. Un TRANSPORT, rien de plus (verdict Fable du 11/09/2026).

Tout le travail est dans arma_labo.py. Ici : JSON-RPC 2.0 sur l'entrée et la sortie standard, un
message par ligne (transport stdio de MCP). Zéro dépendance : le SDK `mcp` n'est pas installé sur
la WS, et un transport de cette taille n'en a pas besoin.

⚠️ LA SORTIE STANDARD EST LE PROTOCOLE. Aucun print() ici : tout diagnostic part sur stderr, que
labo/mcp_arma.sh verse dans etat/mcp_arma.log. Une seule ligne parasite casse la session.
⚠️ MCP = LABO, JOB = MESURE. Rien de ce qui passe par ici ne fait un chiffre publiable.
⚠️ Le labo s'ouvre au PREMIER appel d'outil, pas au démarrage : une session Claude qui ne s'en sert
pas ne prend ni le verrou de l'instance 9 ni le pont.
"""
from __future__ import annotations

import atexit
import json
import logging
import os
import signal
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import arma_labo as al  # noqa: E402

log = logging.getLogger("mcp_arma")
VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26", "2024-11-05")
REPLI = "2025-06-18"

INSTRUCTIONS = (
    "Labo Arma 3 (instance 9, mission Labo.Altis). Outil de réglage de scène et de diagnostic, "
    "JAMAIS de mesure : un chiffre publiable naît d'un job de la file, avec ses graines. "
    "Toute absence de réponse est une PANNE, jamais « aucun ». Camps : rouge = east, bleu = west, "
    "vert = independent. Les groupes se désignent par l'indice rendu par etat, poser_groupe ou "
    "poser_scene ; relire etat avant d'ordonner si un doute existe. L'outil sqf (SQF brut) ne sert "
    "que si Younes le demande explicitement."
)

_XY = {"x": {"type": "number", "description": "abscisse Altis en mètres (0-31000)"},
       "y": {"type": "number", "description": "ordonnée Altis en mètres (0-31000)"}}

OUTILS = [
    {"name": "canari",
     "description": "Aller-retour à vide avec reçu : dit si le pont du labo répond, en combien de ms, "
                    "et si les fonctions du labo sont chargées. À lancer en premier.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "etat",
     "description": "Compte le monde relu dans Arma : hommes par camp, groupes, morts, position des "
                    "joueurs. detail>0 ajoute jusqu'à N hommes (camp, groupe, x, y, z, dégâts).",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
         "detail": {"type": "integer", "minimum": 0, "maximum": 200, "default": 0}}}},
    {"name": "poser_groupe",
     "description": "Pose un groupe d'infanterie à un point, sans ordre. Rend l'indice du groupe et "
                    "le nombre d'hommes RÉELLEMENT posés.",
     "inputSchema": {"type": "object", "additionalProperties": False,
                     "required": ["camp", "nombre", "x", "y"], "properties": {
         "camp": {"type": "string", "enum": ["rouge", "bleu", "vert"]},
         "nombre": {"type": "integer", "minimum": 1, "maximum": 24},
         **_XY,
         "skill": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.5}}}},
    {"name": "poser_scene",
     "description": "La scène qui combat : bleus contre rouges face à face à `distance` m autour du "
                    "point (défaut : ancre dégagée d'Altis). combat=true : COMBAT/RED/FULL, doMove "
                    "vers l'autre, reveal mutuel.",
     "inputSchema": {"type": "object", "additionalProperties": False, "properties": {
         "bleus": {"type": "integer", "minimum": 0, "maximum": 24, "default": 8},
         "rouges": {"type": "integer", "minimum": 0, "maximum": 24, "default": 8},
         "distance": {"type": "number", "minimum": 30, "maximum": 1500, "default": 220},
         **_XY,
         "skill": {"type": "number", "minimum": 0, "maximum": 1, "default": 0.5},
         "combat": {"type": "boolean", "default": True}}}},
    {"name": "ordonner",
     "description": "Donne un ordre à un groupe (indice). aller : x,y. comportement : careless|safe|"
                    "aware|combat|stealth. combat : blue|green|white|yellow|red. vitesse : limited|"
                    "normal|full. posture : up|middle|down|auto. arreter, reveler : sans valeur.",
     "inputSchema": {"type": "object", "additionalProperties": False,
                     "required": ["groupe", "ordre"], "properties": {
         "groupe": {"type": "integer", "minimum": 0},
         "ordre": {"type": "string", "enum": list(al.ORDRES)},
         **_XY,
         "valeur": {"type": "string"}}}},
    {"name": "nettoyer",
     "description": "Table rase : supprime tout homme non joueur, les morts, les armes au sol, les "
                    "groupes vides. Échoue si un seul homme reste.",
     "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False}},
    {"name": "sqf",
     "description": "SQF brut, UNE ligne, sans commentaire (// refusé), borné en taille. À n'utiliser "
                    "que sur demande explicite de Younes. Rend la valeur si elle est un nombre ou un "
                    "booléen, et les lignes émises par [\"CLE\", [nombres]] call LABO_R.",
     "inputSchema": {"type": "object", "additionalProperties": False, "required": ["code"],
                     "properties": {"code": {"type": "string"}}}},
]


class Serveur:
    def __init__(self):
        self.labo = None
        self.version = REPLI

    # ---- le labo, ouvert à la demande
    def _labo(self):
        if self.labo is None:
            l = al.Labo(**al.config_env())
            l.ouvrir()                 # lève Occupe / PontMort ; ouvrir() rend tout en cas d'échec
            self.labo = l
            log.info("labo ouvert (pid %d)", os.getpid())
        return self.labo

    def fermer(self):
        if self.labo is not None:
            self.labo.fermer()
            self.labo = None
            log.info("labo fermé, verrous rendus")

    def _appeler(self, nom, a):
        l = self._labo()
        if nom == "canari":
            return l.canari()
        if nom == "etat":
            return l.etat(a.get("detail", 0))
        if nom == "poser_groupe":
            return l.poser_groupe(a.get("camp"), a.get("nombre"), a.get("x"), a.get("y"),
                                  a.get("skill", 0.5))
        if nom == "poser_scene":
            return l.poser_scene(a.get("bleus", 8), a.get("rouges", 8), a.get("distance", 220),
                                 a.get("x", al.ANCRE_ALTIS[0]), a.get("y", al.ANCRE_ALTIS[1]),
                                 a.get("skill", 0.5), a.get("combat", True))
        if nom == "ordonner":
            return l.ordonner(a.get("groupe"), a.get("ordre"), a.get("x"), a.get("y"), a.get("valeur"))
        if nom == "nettoyer":
            return l.nettoyer()
        if nom == "sqf":
            return l.sqf(a.get("code"), par_humain=True)
        raise al.Refus(f"outil inconnu : {nom}")

    def _outil(self, params):
        nom, a = params.get("name"), params.get("arguments") or {}
        if nom not in {o["name"] for o in OUTILS}:
            return None
        try:
            res = self._appeler(nom, a)
            texte, erreur = json.dumps(res, ensure_ascii=False), False
        except al.PontMort as e:
            res, erreur = None, True
            texte = f"PONT MORT : {e}"
        except al.Refus as e:
            res, erreur = None, True
            texte = f"REFUSÉ, rien n'est parti : {e}"
        except (al.SansRecu, al.Incomplet, al.Occupe, al.ErreurLabo) as e:
            res, erreur = None, True
            texte = f"{type(e).__name__.upper()} : {e}"
        except Exception as e:                                   # noqa: BLE001
            log.error("erreur interne sur %s : %s", nom, traceback.format_exc())
            res, erreur = None, True
            texte = f"ERREUR INTERNE ({type(e).__name__}) : {e}"
        if erreur:
            log.warning("outil %s en erreur : %s", nom, texte)
        out = {"content": [{"type": "text", "text": texte}], "isError": erreur}
        if res is not None and self.version >= "2025-06-18":
            out["structuredContent"] = res
        return out

    # ---- JSON-RPC
    def traiter(self, msg):
        if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
            return _err(msg.get("id") if isinstance(msg, dict) else None, -32600, "requête invalide")
        mid, meth, params = msg.get("id"), msg.get("method"), msg.get("params") or {}
        if meth is None:
            return None                                         # une réponse du client : ignorée
        if mid is None:
            return None                                         # notification : jamais de réponse
        if meth == "initialize":
            dem = params.get("protocolVersion", REPLI)
            self.version = dem if dem in VERSIONS else REPLI
            return _ok(mid, {"protocolVersion": self.version,
                             "capabilities": {"tools": {"listChanged": False}},
                             "serverInfo": {"name": "hmt-arma-labo", "version": "0.1.0"},
                             "instructions": INSTRUCTIONS})
        if meth == "ping":
            return _ok(mid, {})
        if meth == "tools/list":
            return _ok(mid, {"tools": OUTILS})
        if meth == "tools/call":
            r = self._outil(params)
            if r is None:
                return _err(mid, -32602, f"outil inconnu : {params.get('name')!r}")
            return _ok(mid, r)
        return _err(mid, -32601, f"méthode inconnue : {meth}")


def _ok(mid, res):
    return {"jsonrpc": "2.0", "id": mid, "result": res}

def _err(mid, code, message):
    return {"jsonrpc": "2.0", "id": mid, "error": {"code": code, "message": message}}

def _ecrire(obj):
    sys.stdout.write(json.dumps(obj, ensure_ascii=False, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def main():
    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format="%(asctime)s %(name)s %(levelname)s %(message)s")
    s = Serveur()
    atexit.register(s.fermer)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))      # atexit rend les verrous
    log.info("démarrage pid %d", os.getpid())
    for ligne in sys.stdin:
        ligne = ligne.strip()
        if not ligne:
            continue
        try:
            msg = json.loads(ligne)
        except json.JSONDecodeError:
            _ecrire(_err(None, -32700, "JSON illisible"))
            continue
        if isinstance(msg, list):                               # lot (versions 2025-03-26)
            reps = [r for r in (s.traiter(m) for m in msg) if r is not None]
            if reps:
                _ecrire(reps)
        else:
            r = s.traiter(msg)
            if r is not None:
                _ecrire(r)
    log.info("entrée fermée : arrêt")
    s.fermer()


if __name__ == "__main__":
    main()
