#!/usr/bin/env python3
"""test_labo — la plomberie du labo éprouvée contre le JOUET faux_arma.py. Aucun Arma, aucun
réseau, aucun fichier hors d'un dossier temporaire.

Chaque test des pannes est un test « doit savoir échouer » : il vérifie que la panne LÈVE, et
jamais qu'elle rend une réponse vide qu'on lirait comme « aucun ».

Lancer : python3 labo/test_labo.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import arma_labo as al  # noqa: E402
from faux_arma import FauxArma  # noqa: E402

RAPIDE = dict(battement_max=0.8, patience=2.0, patience_ouverture=2.0)


def lire(chemin):
    with open(chemin) as f:
        return f.read()


def ecrire(chemin, texte):
    with open(chemin, "w") as f:
        f.write(texte)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        r = self.tmp.name
        self.chemins = dict(profil=f"{r}/hmtech9", pont=f"{r}/pont_i9",
                            verrous=f"{r}/verrous", etat=f"{r}/etat")
        for d in ("verrous", "etat"):
            os.makedirs(self.chemins[d])
        self.arma = FauxArma(self.chemins["profil"], self.chemins["pont"]).demarrer()
        self.labos = []

    def tearDown(self):
        for l in self.labos:
            l.fermer()
        self.arma.arreter()
        if getattr(self, "err", None):
            self.err.close()
        self.tmp.cleanup()

    def labo(self, **kw):
        l = al.Labo(**self.chemins, **{**RAPIDE, **kw})
        self.labos.append(l)
        return l.ouvrir()


class Plomberie(Base):
    def test_canari_cent_allers_retours(self):
        l = self.labo()
        rtt, n = [], []
        for _ in range(100):
            r = l.canari()
            rtt.append(r["recu"]["rtt_ms"])
            n.append(r["recu"]["n_cmd"])
        self.assertEqual(n, list(range(n[0], n[0] + 100)), "le compteur doit avancer d'un en un")
        rtt.sort()
        self.assertLess(rtt[49], 1000)
        self.assertLess(rtt[98], 3000)
        self.assertEqual(self.arma.recus, 100)

    def test_etat_monde_connu(self):
        self.arma.ajouter(0, 3, 8000, 10000)
        self.arma.ajouter(1, 2, 8100, 10000)
        self.arma.ajouter(1, 1, 8200, 10000, joueur=True)
        e = self.labo().etat(detail=10)
        self.assertEqual((e["unites"], e["non_joueurs"], e["joueurs"]), (6, 5, 1))
        self.assertEqual(e["camps"]["rouge"]["vivants"], 3)
        self.assertEqual(e["camps"]["bleu"]["vivants"], 3)
        self.assertEqual(len(e["detail"]), 5)
        self.assertEqual(len(e["joueurs_pos"]), 1)

    def test_critere_fable_8_puis_11(self):
        """poser 8 -> etat = 8 en camp rouge, tous à moins de 20 m ; 3 à la main -> 11."""
        l = self.labo()
        g = l.poser_groupe("rouge", 8, 8300, 10070)
        self.assertEqual((g["poses"], g["complet"]), (8, True))
        e = l.etat(detail=50)
        self.assertEqual(e["camps"]["rouge"]["vivants"], 8)
        for u in e["detail"]:
            self.assertLess(((u["x"] - 8300) ** 2 + (u["y"] - 10070) ** 2) ** 0.5, 20)
        l.sqf('private _g = createGroup [east, true]; for "_i" from 1 to 3 do '
              '{ _g createUnit ["O_Soldier_F", [8300, 10070, 0], [], 5, "FORM"] };', par_humain=True)
        self.assertEqual(l.etat()["non_joueurs"], 11, "etat compte le monde, pas sa mémoire")
        self.assertEqual(l.sqf("count allUnits", par_humain=True)["valeur"], 11)

    def test_scene_ordre_nettoyage(self):
        l = self.labo()
        s = l.poser_scene(bleus=8, rouges=6, distance=220)
        self.assertEqual((s["bleu"]["poses"], s["rouge"]["poses"]), (8, 6))
        o = l.ordonner(s["bleu"]["groupe"], "aller", 8400, 10100)
        self.assertEqual((o["camp"], o["effectif"]), ("bleu", 8))
        o = l.ordonner(s["rouge"]["groupe"], "comportement", valeur="COMBAT")
        self.assertEqual(o["valeur"], "COMBAT")
        n = l.nettoyer()
        self.assertEqual((n["avant"]["hommes"], n["apres"]["hommes"]), (14, 0))
        self.assertEqual(l.etat()["non_joueurs"], 0)

    def test_groupe_inconnu_refuse_par_la_mission(self):
        with self.assertRaises(al.Refus):
            self.labo().ordonner(57, "arreter")


class Refus(Base):
    def test_commentaire_refuse_et_rien_ne_part(self):
        l = self.labo()
        n0 = l.canari()["recu"]["n_cmd"]
        for code in ("count allUnits // total", "1 /* x */", "a\nb", "#define X 1", "", "x" * 9000):
            with self.assertRaises(al.Refus, msg=code[:20]):
                l.sqf(code, par_humain=True)
        self.assertEqual(l.canari()["recu"]["n_cmd"], n0 + 1, "aucune commande refusée n'est partie")

    def test_sqf_brut_reserve_a_l_humain(self):
        with self.assertRaises(al.Refus):
            self.labo().sqf("1")

    def test_arguments_hors_bornes(self):
        l = self.labo()
        for appel in (lambda: l.poser_groupe("jaune", 3, 1, 1), lambda: l.poser_groupe("rouge", 99, 1, 1),
                      lambda: l.poser_groupe("rouge", 3, float("nan"), 1),
                      lambda: l.ordonner(0, "danser"), lambda: l.ordonner(0, "vitesse", valeur="warp"),
                      lambda: l.etat(detail=1000)):
            with self.assertRaises(al.Refus):
                appel()

    def test_autre_instance_refusee(self):
        with self.assertRaises(al.Refus):
            al.Labo(3, **self.chemins)


class Pannes(Base):
    def test_pont_mort_leve_jamais_vide(self):
        l = self.labo()
        l.canari()
        self.arma.muet()
        t0 = time.monotonic()
        with self.assertRaises(al.PontMort):
            l.etat()
        self.assertLess(time.monotonic() - t0, 10, "la panne se déclare en temps borné")
        self.assertEqual([f for f in os.listdir(self.chemins["pont"]) if f.startswith("cmd_")], [],
                         "une commande non prise est effacée : l'actuateur ne la jouera pas au réveil")

    def test_mission_relancee_dans_le_meme_rpt(self):
        """#restart : même serveur, même RPT, compteur à 0. Seul le battement le dit."""
        l = self.labo()
        for _ in range(4):
            l.canari()
        self.arma.redemarrer_mission()
        time.sleep(0.3)                                 # au moins un battement à n=0
        r = l.canari()
        self.assertEqual(r["recu"]["n_cmd"], 1)
        self.assertEqual(r["recu"]["recalages"], 1)

    def test_autre_ecrivain_fait_avancer_l_actuateur(self):
        l = self.labo()
        n = l.canari()["recu"]["n_cmd"]
        self.arma.sauter(3)
        time.sleep(0.3)
        r = l.canari()
        self.assertEqual(r["recu"]["n_cmd"], n + 4)
        self.assertEqual(r["recu"]["recalages"], 1)

    def test_sans_recu_puis_reprise(self):
        l = self.labo()
        with self.assertRaises(al.SansRecu):
            l.sqf("ERREUR_COMPILATION", par_humain=True)
        r = l.canari()                                  # le compteur a suivi l'actuateur
        self.assertEqual(r["recu"]["n_cmd"], self.arma.n)

    def test_redemarrage_serveur(self):
        l = self.labo()
        for _ in range(5):
            l.canari()
        self.arma.redemarrer()                          # nouveau RPT, compteur à 0
        time.sleep(1.2)                                 # le module ne regarde les RPT qu'une fois par seconde
        r = l.canari()
        self.assertEqual(r["recu"]["n_cmd"], 1)
        self.assertEqual(r["recu"]["redemarrages"], 1)

    def test_ligne_perdue_donne_incomplet(self):
        """La ligne avalée est la dernière (un homme du détail) : aucun analyseur ne l'exige, seul
        le compte du reçu la voit manquer."""
        l = self.labo()
        self.arma.ajouter(0, 2, 1000, 1000)
        self.arma.perdre_une_ligne = True
        with self.assertRaises(al.Incomplet):
            l.etat(detail=5)

    def test_mission_sans_fonctions(self):
        self.arma.fonctions = False
        with self.assertRaises(al.Incomplet):
            self.labo().canari()

    def test_mission_perimee(self):
        """Une vieille Labo.Altis restée dans MPMissions : le canari la refuse."""
        self.arma.version = al.VERSION_MISSION + 1
        with self.assertRaises(al.Incomplet):
            self.labo().canari()

    def test_aucun_rpt(self):
        self.arma.arreter()
        for f in os.listdir(self.chemins["profil"]):
            os.remove(os.path.join(self.chemins["profil"], f))
        with self.assertRaises(al.PontMort):
            self.labo()
        self.assertFalse(os.path.exists(os.path.join(self.chemins["etat"], "labo_i9.ecrivain")),
                         "une ouverture ratée rend ses verrous")


class Verrous(Base):
    def test_deuxieme_session_refusee_premiere_repond(self):
        a = self.labo()
        with self.assertRaises(al.Occupe):
            self.labo()
        self.assertEqual(a.canari()["pont"], "vivant")

    def test_ecrivain_exclusif_meme_sans_verrou_file(self):
        """Le verrou de la file ne doit pas masquer celui du pont : c'est lui qui empêche deux
        écrivains de se voler leurs cmd_N."""
        a = self.labo(prendre_verrou_file=False)
        with self.assertRaises(al.Occupe):
            self.labo(prendre_verrou_file=False)
        self.assertEqual(a.canari()["pont"], "vivant")

    def test_verrou_file_pose_et_rendu(self):
        a = self.labo()
        pidf = os.path.join(self.chemins["verrous"], "j9", "pid")
        self.assertEqual(lire(pidf).strip(), str(os.getpid()))
        a.fermer()
        self.assertFalse(os.path.exists(os.path.dirname(pidf)))

    def test_verrou_mort_repris(self):
        p = subprocess.Popen([sys.executable, "-c", "pass"])
        p.wait()                                        # un pid qui ne vit plus
        os.makedirs(os.path.join(self.chemins["verrous"], "j9"))
        ecrire(os.path.join(self.chemins["verrous"], "j9", "pid"), f"{p.pid}\n")
        ecrire(os.path.join(self.chemins["etat"], "labo_i9.ecrivain"), f"{p.pid}\n")
        self.assertEqual(self.labo().canari()["pont"], "vivant")

    def test_job_vivant_sur_j9_refuse(self):
        os.makedirs(os.path.join(self.chemins["verrous"], "j9"))
        ecrire(os.path.join(self.chemins["verrous"], "j9", "pid"), f"{os.getppid()}\n")
        with self.assertRaises(al.Occupe):
            self.labo()

    def test_sans_verrou_file_pour_un_job(self):
        """Dans un job de la file, file3.sh tient déjà j9 : le banc ouvre sans le reprendre."""
        l = self.labo(prendre_verrou_file=False)
        self.assertFalse(os.path.exists(os.path.join(self.chemins["verrous"], "j9")))
        self.assertEqual(l.canari()["pont"], "vivant")


class CoherenceSQF(unittest.TestCase):
    """Le Python et fonctions.sqf se parlent par des listes et des clés recopiées des deux côtés.
    Le jouet ne lit pas le SQF : sans ce test, une dérive entre les deux ne se verrait qu'au banc."""

    @classmethod
    def setUpClass(cls):
        cls.fct = lire(os.path.join(ICI, "mission.Altis", "fonctions.sqf"))
        cls.init = lire(os.path.join(ICI, "mission.Altis", "initServer.sqf"))

    def test_version(self):
        import re
        self.assertEqual(re.findall(r"^LABO_VERSION = (\d+);", self.fct, re.M), [str(al.VERSION_MISSION)])

    def test_listes_de_valeurs_identiques(self):
        for ordre, valeurs in al.VALEURS.items():
            sqf = "[" + ", ".join(f'"{v.upper()}"' for v in valeurs) + "]"
            self.assertIn(sqf, self.fct, f"liste de l'ordre {ordre}")
        self.assertIn("LABO_CAMPS = [east, west, independent, civilian];", self.fct)
        self.assertEqual(al.CAMPS[:3], ["rouge", "bleu", "vert"])
        self.assertIn('["O_Soldier_F", "B_Soldier_F", "I_soldier_F"] select _camp', self.fct)

    def test_cles_emises_toutes_lues(self):
        import re
        emises = set(re.findall(r'\["([A-Z_]+)", \[', self.fct))
        lues = {"TOTAL", "CAMP", "JOUEUR", "U", "GROUPE", "REFUS", "BLEU", "ROUGE", "ORDRE", "AVANT", "APRES"}
        self.assertEqual(emises, lues)

    def test_fonctions_appelees_existent(self):
        import re
        src = lire(os.path.join(ICI, "arma_labo.py"))
        appelees = set(re.findall(r"call (LABO_fnc_\w+)", src))
        definies = set(re.findall(r"^(LABO_fnc_\w+) = \{", self.fct, re.M))
        self.assertTrue(appelees)
        self.assertLessEqual(appelees, definies)

    def test_parentheses_equilibrees(self):
        for nom, txt in (("fonctions.sqf", self.fct), ("initServer.sqf", self.init)):
            pile, ligne = [], 1
            i = 0
            while i < len(txt):
                c = txt[i]
                if c == "\n":
                    ligne += 1
                elif txt.startswith("//", i):
                    i = txt.find("\n", i) - 1 if "\n" in txt[i:] else len(txt)
                elif c == '"':
                    j = txt.find('"', i + 1)
                    i = j
                elif c in "([{":
                    pile.append((c, ligne))
                elif c in ")]}":
                    self.assertTrue(pile, f"{nom} l.{ligne} : {c} sans ouvrant")
                    o, lo = pile.pop()
                    self.assertEqual("([{".index(o), ")]}".index(c), f"{nom} l.{ligne} : {c} ferme {o} de l.{lo}")
                i += 1
            self.assertEqual(pile, [], f"{nom} : non fermés {pile}")


class BancSurJouet(Base):
    """Le banc de Fable joué contre le jouet : il doit PASSER sur un pont sain et ÉCHOUER dès
    qu'un seul reçu manque. Un banc qui passe toujours ne juge rien."""

    def _banc(self):
        env = dict(os.environ, HMT_LABO_TEST="1", HMT_LABO_PROFIL=self.chemins["profil"],
                   HMT_LABO_PONT=self.chemins["pont"], HMT_LABO_VERROUS=self.chemins["verrous"],
                   HMT_LABO_ETAT=self.chemins["etat"], HMT_LABO_BATTEMENT_MAX="0.8",
                   HMT_LABO_PATIENCE="2", HMT_LABO_PATIENCE_OUVERTURE="2", HMT_LABO_TUER=self.tuer)
        r = subprocess.run([sys.executable, os.path.join(ICI, "banc_pontmcp.py")], env=env,
                           capture_output=True, text=True, timeout=180)
        return r.returncode, json.loads(r.stdout)

    def setUp(self):
        super().setUp()
        self.tuer = os.path.join(self.tmp.name, "tuer")
        self.arma.tuer = self.tuer

    def test_banc_passe_sur_pont_sain(self):
        rc, res = self._banc()
        self.assertEqual(res["verdict"], "PASSE", json.dumps(res, indent=1, ensure_ascii=False))
        self.assertEqual(rc, 0)
        self.assertEqual(len(res["criteres"]), 7)

    def test_banc_echoue_si_un_seul_recu_manque(self):
        self.arma.saboter_a = 7                      # la 7e commande s'exécute sans reçu
        rc, res = self._banc()
        self.assertEqual(res["verdict"], "ECHOUE")
        self.assertFalse(res["criteres"]["C1_canaris"])
        self.assertEqual(res["mesures"]["C1"]["perdus"], 1)
        self.assertEqual(rc, 1)


class TransportMCP(Base):
    """Le serveur MCP en vrai sous-processus, parlé en JSON-RPC ligne à ligne."""

    def _mcp(self):
        env = dict(os.environ, HMT_LABO_TEST="1", HMT_LABO_PROFIL=self.chemins["profil"],
                   HMT_LABO_PONT=self.chemins["pont"], HMT_LABO_VERROUS=self.chemins["verrous"],
                   HMT_LABO_ETAT=self.chemins["etat"], HMT_LABO_BATTEMENT_MAX="0.8",
                   HMT_LABO_PATIENCE="2", HMT_LABO_PATIENCE_OUVERTURE="2")
        self.err = open(os.path.join(self.tmp.name, "mcp.err"), "w")
        return subprocess.Popen([sys.executable, os.path.join(ICI, "mcp_arma.py")], env=env,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.err,
                                text=True, bufsize=1)

    def _dire(self, p, msg):
        p.stdin.write(json.dumps(msg) + "\n")
        p.stdin.flush()
        if "id" not in msg:
            return None
        ligne = p.stdout.readline()
        return json.loads(ligne)                        # toute ligne parasite ferait échouer ici

    def test_session_complete(self):
        p = self._mcp()
        try:
            r = self._dire(p, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                "protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "0"}}})
            self.assertEqual(r["result"]["protocolVersion"], "2025-06-18")
            self.assertIn("tools", r["result"]["capabilities"])
            self._dire(p, {"jsonrpc": "2.0", "method": "notifications/initialized"})
            self.assertFalse(os.path.exists(os.path.join(self.chemins["verrous"], "j9")),
                             "le labo ne s'ouvre pas avant le premier outil")
            outils = self._dire(p, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})["result"]["tools"]
            self.assertEqual({o["name"] for o in outils},
                             {"canari", "etat", "poser_groupe", "poser_scene", "ordonner", "nettoyer", "sqf"})
            c = self._dire(p, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                               "params": {"name": "canari", "arguments": {}}})["result"]
            self.assertFalse(c["isError"])
            self.assertEqual(c["structuredContent"]["pont"], "vivant")
            self.assertTrue(os.path.exists(os.path.join(self.chemins["verrous"], "j9")))
            g = self._dire(p, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {
                "name": "poser_groupe", "arguments": {"camp": "bleu", "nombre": 4, "x": 8000, "y": 9000}}})
            self.assertEqual(g["result"]["structuredContent"]["poses"], 4)
            s = self._dire(p, {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {
                "name": "sqf", "arguments": {"code": "count allUnits // commentaire"}}})["result"]
            self.assertTrue(s["isError"])
            self.assertIn("REFUSÉ", s["content"][0]["text"])
            e = self._dire(p, {"jsonrpc": "2.0", "id": 6, "method": "nimporte"})
            self.assertEqual(e["error"]["code"], -32601)
            e = self._dire(p, {"jsonrpc": "2.0", "id": 7, "method": "tools/call",
                               "params": {"name": "inconnu", "arguments": {}}})
            self.assertEqual(e["error"]["code"], -32602)
            self.arma.muet()
            m = self._dire(p, {"jsonrpc": "2.0", "id": 8, "method": "tools/call",
                               "params": {"name": "etat", "arguments": {}}})["result"]
            self.assertTrue(m["isError"])
            self.assertIn("PONT MORT", m["content"][0]["text"])
        finally:
            p.stdin.close()
            p.wait(10)
        reste = p.stdout.read()
        p.stdout.close()
        self.assertEqual(reste, "", "rien d'autre que des réponses sur la sortie standard")
        self.assertFalse(os.path.exists(os.path.join(self.chemins["verrous"], "j9")),
                         "fin de session = verrou de l'instance rendu")
        self.assertFalse(os.path.exists(os.path.join(self.chemins["etat"], "labo_i9.ecrivain")))

    def test_ouverture_ratee_puis_reussie(self):
        """Pas de serveur : l'outil dit PONT MORT et rend les verrous ; le serveur revient : ça marche."""
        self.arma.muet()
        p = self._mcp()
        try:
            self._dire(p, {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                           "params": {"protocolVersion": "2099-01-01"}})
            r = self._dire(p, {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                               "params": {"name": "canari", "arguments": {}}})["result"]
            self.assertTrue(r["isError"])
            self.assertFalse(os.path.exists(os.path.join(self.chemins["verrous"], "j9")))
            self.arma.muet_ = False
            r = self._dire(p, {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                               "params": {"name": "canari", "arguments": {}}})["result"]
            self.assertFalse(r["isError"], r)
        finally:
            p.stdin.close()
            p.wait(10)
            p.stdout.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
