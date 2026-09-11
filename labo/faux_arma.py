#!/usr/bin/env python3
"""faux_arma — un JOUET à réponse connue pour éprouver arma_labo.py sans Arma.

Il imite Labo.Altis à l'endroit exact où le module la touche, et nulle part ailleurs :
  · il lit cmd_<N>.sqf DANS L'ORDRE, comme l'actuateur (HMT_n avancé avant d'exécuter) ;
  · il écrit le battement « [LABO] HMT_SYNC n coeur k » et les lignes « [LABO] R … » /
    « [LABO] ECHO … » dans un RPT, entre guillemets comme diag_log, avec du bruit autour ;
  · il coupe parfois une ligne en deux écritures, comme un RPT qu'on lit pendant qu'il s'écrit.

⚠️ IL NE COMPREND PAS LE SQF. Il reconnaît les appels que le module fabrique et tient un petit
monde (une liste d'hommes) dont on connaît la réponse d'avance. Il prouve la PLOMBERIE (compteur,
reçus, pannes, verrous), jamais la justesse du SQF de fonctions.sqf : ça, seul Arma le prouve.

Pannes simulables : muet() (plus de battement ni d'actuateur), redemarrer() (nouveau RPT, compteur
à 0), perdre_une_ligne (une ligne R avalée), et tout code contenant ERREUR_COMPILATION produit
« Error Missing ; » sans reçu, comme un `call compile` qui échoue.
"""
from __future__ import annotations

import os
import random
import re
import threading
import time

_RE_ENV = re.compile(r'^private _labo_nonce = (\d+); private _labo_k = 0; (.*) '
                     r'diag_log format \["\[LABO\] ECHO %1 %2 %3", (\d+), _labo_nonce, _labo_k\];$')
_NUM = r"(-?[\d.]+)"


class FauxArma:
    def __init__(self, profil, pont, periode=0.1, fonctions=True, version=1, tuer=None):
        self.profil, self.pont, self.periode = profil, pont, periode
        self.fonctions = fonctions
        self.version = version            # LABO_VERSION de la mission imitée
        self.tuer = tuer                  # fichier dont l'apparition « tue le serveur » (banc, E5)
        self.saboter_a = None             # numéro de commande exécutée SANS reçu
        self.n = 0
        self.k = 0
        self.unites = []          # dicts : camp (0 rouge 1 bleu 2 vert 3 civil), g, x, y, joueur
        self.groupes = 0
        self.muet_ = False
        self.perdre_une_ligne = False
        self.recus = 0
        self._stop = threading.Event()
        self._verrou = threading.Lock()
        os.makedirs(profil, exist_ok=True)
        os.makedirs(pont, exist_ok=True)
        self._nouveau_rpt()
        self.t = threading.Thread(target=self._boucle, daemon=True)

    # ---- pilotage par le test
    def demarrer(self):
        self.t.start()
        return self

    def arreter(self):
        self._stop.set()
        self.t.join(2)

    def muet(self):
        self.muet_ = True

    def redemarrer(self):
        with self._verrou:
            self.n = 0
            self.k = 0
            time.sleep(0.02)
            self._nouveau_rpt()

    def redemarrer_mission(self):
        """La mission redémarre DANS le même serveur : même RPT, compteur à 0."""
        with self._verrou:
            self.n = 0

    def sauter(self, k):
        """Un AUTRE écrivain a fait avancer l'actuateur de k commandes."""
        with self._verrou:
            self.n += k

    def ajouter(self, camp, nombre, x, y, joueur=False):
        with self._verrou:
            g = self.groupes
            self.groupes += 1
            for _ in range(nombre):
                self.unites.append({"camp": camp, "g": g, "x": x + random.uniform(-5, 5),
                                    "y": y + random.uniform(-5, 5), "joueur": joueur})
            return g

    # ---- le RPT
    def _nouveau_rpt(self):
        ts = time.strftime("%Y-%m-%d_%H-%M-%S") + f"_{random.randrange(10**6)}"
        self.rpt = os.path.join(self.profil, f"arma3server_x64_{ts}.rpt")
        with open(self.rpt, "w") as f:
            f.write("=====================================================================\n")
            f.write("== C:\\Program Files (x86)\\Steam\\steamapps\\common\\Arma 3\\arma3server_x64.exe\n")

    def _ecrire(self, texte, citer=True):
        l = f'{time.strftime("%H:%M:%S")} ' + (f'"{texte}"' if citer else texte) + "\r\n"
        with open(self.rpt, "a") as f:
            if random.random() < 0.2:                     # ligne coupée en deux écritures
                c = len(l) // 2
                f.write(l[:c]); f.flush(); time.sleep(0.003); f.write(l[c:])
            else:
                f.write(l)

    # ---- l'actuateur et le battement
    def _boucle(self):
        t_bat = 0.0
        while not self._stop.is_set():
            if self.tuer and os.path.exists(self.tuer):
                self.muet_ = True
            if self.muet_:
                time.sleep(0.02)
                continue
            now = time.monotonic()
            with self._verrou:
                if now - t_bat >= self.periode:
                    self.k += 1
                    self._ecrire(f"[LABO] HMT_SYNC {self.n} coeur {self.k}")
                    t_bat = now
                    if random.random() < 0.3:
                        self._ecrire("Warning Message: No entry 'bin\\config.bin/CfgVehicles.bruit'.", citer=False)
                cmd = os.path.join(self.pont, f"cmd_{self.n + 1}.sqf")
                if os.path.exists(cmd):
                    with open(cmd) as f:
                        code = f.read().strip()
                    self.n += 1
                    self._executer(code)
            time.sleep(0.01)

    def _executer(self, code):
        if self.saboter_a == self.n:
            self._ecrire("Error in expression <sabotage du jouet>", citer=False)
            return
        if "ERREUR_COMPILATION" in code:
            self._ecrire("Error in expression <ERREUR_COMPILATION>", citer=False)
            self._ecrire("  Error position: <ERREUR_COMPILATION>", citer=False)
            self._ecrire("  Error Missing ;", citer=False)
            return
        m = _RE_ENV.match(code)
        if not m:
            self._ecrire("Error in expression <enveloppe inconnue>", citer=False)
            return
        nonce, corps, n = int(m.group(1)), m.group(2), int(m.group(3))
        lignes = self._corps(corps) if self.fonctions or '"CANARI"' in corps else []
        if self.perdre_une_ligne and lignes:
            # On avale la DERNIÈRE ligne : celle qu'aucun analyseur n'exige. Seul le compte k du
            # reçu peut voir qu'elle manque.
            self.perdre_une_ligne = False
            ecrites = lignes[:-1]
        else:
            ecrites = lignes
        for cle, vals in ecrites:
            self._ecrire(f"[LABO] R {nonce} {cle} " + " ".join(_str_sqf(v) for v in vals))
        self._ecrire(f"[LABO] ECHO {n} {nonce} {len(lignes)}")
        self.recus += 1

    def _corps(self, c):
        if '"CANARI"' in c:
            return [("CANARI", [self.n, self.version if self.fonctions else 0])]
        m = re.fullmatch(r"\[(\d+)\] call LABO_fnc_etat;", c)
        if m:
            return self._etat(int(m.group(1)))
        m = re.fullmatch(rf"\[(\d), (\d+), {_NUM}, {_NUM}, {_NUM}\] call LABO_fnc_poser_groupe;", c)
        if m:
            camp, nb, x, y = int(m.group(1)), int(m.group(2)), float(m.group(3)), float(m.group(4))
            g = self._ajouter_sans_verrou(camp, nb, x, y)
            u = [v for v in self.unites if v["g"] == g]
            return [("GROUPE", [g, camp, len(u), u[0]["x"], u[0]["y"]])]
        m = re.fullmatch(rf"\[(\d+), (\d+), {_NUM}, {_NUM}, {_NUM}, {_NUM}, (\d)\] call LABO_fnc_poser_scene;", c)
        if m:
            nb, nr, d = int(m.group(1)), int(m.group(2)), float(m.group(3))
            x, y = float(m.group(4)), float(m.group(5))
            gb = self._ajouter_sans_verrou(1, nb, x, y - d / 2) if nb else -1
            gr = self._ajouter_sans_verrou(0, nr, x, y + d / 2) if nr else -1
            return [("BLEU", [gb, nb, x, y - d / 2]), ("ROUGE", [gr, nr, x, y + d / 2])]
        m = re.fullmatch(rf"\[(-?\d+), (\d), {_NUM}, {_NUM}, (\d)\] call LABO_fnc_ordonner;", c)
        if m:
            gi, o = int(m.group(1)), int(m.group(2))
            u = [v for v in self.unites if v["g"] == gi]
            if gi < 0 or gi >= self.groupes:
                return [("REFUS", [3])]
            if not u:
                return [("REFUS", [4])]
            if o == 0:
                for v in u:
                    v["x"], v["y"] = float(m.group(3)), float(m.group(4))
            return [("ORDRE", [gi, u[0]["camp"], len(u), o, u[0]["x"], u[0]["y"]])]
        if c == "[] call LABO_fnc_nettoyer;":
            nj = [v for v in self.unites if not v["joueur"]]
            av = [len(nj), 0, self.groupes]
            self.unites = [v for v in self.unites if v["joueur"]]
            return [("AVANT", av), ("APRES", [0, 0, len({v["g"] for v in self.unites})])]
        m = re.fullmatch(r"private _labo_v = call \{ (.*?) \}; if \(!isNil .*", c)
        if m:
            return self._brut(m.group(1))
        return []

    def _ajouter_sans_verrou(self, camp, nombre, x, y):
        g = self.groupes
        self.groupes += 1
        for _ in range(nombre):
            self.unites.append({"camp": camp, "g": g, "x": x + random.uniform(-7, 7),
                                "y": y + random.uniform(-7, 7), "joueur": False})
        return g

    def _etat(self, detail):
        nj = [v for v in self.unites if not v["joueur"]]
        j = [v for v in self.unites if v["joueur"]]
        L = [("TOTAL", [len(self.unites), len(nj), 0, len(j), self.groupes])]
        for i in range(4):
            u = [v for v in self.unites if v["camp"] == i]
            L.append(("CAMP", [i, len(u), len({v["g"] for v in u})]))
        for v in j:
            L.append(("JOUEUR", [v["x"], v["y"], 0.01, 90]))
        for v in nj[:detail]:
            L.append(("U", [v["camp"], v["g"], v["x"], v["y"], 0.02, 0]))
        return L

    def _brut(self, code):
        """Le sous-ensemble de SQF brut que le jouet sait jouer — le reste ne rend rien."""
        if code == "count allUnits":
            return [("VAL", [len(self.unites)])]
        if re.fullmatch(r"-?\d+(\.\d+)?", code):
            return [("VAL", [float(code)])]
        m = re.search(rf'from 1 to (\d+) do \{{ _g createUnit \["([OBI])_\w+", \[{_NUM}, {_NUM}', code)
        if m:
            camp = {"O": 0, "B": 1, "I": 2}[m.group(2)]
            self._ajouter_sans_verrou(camp, int(m.group(1)), float(m.group(3)), float(m.group(4)))
            return []
        m = re.fullmatch(r'\["(\w+)", \[([-\d., ]*)\]\] call LABO_R', code)
        if m:
            return [(m.group(1), [float(t) for t in m.group(2).split(",") if t.strip()])]
        return []


def _str_sqf(v):
    """`str` de SQF : six chiffres significatifs."""
    if isinstance(v, int) or float(v).is_integer():
        return str(int(v))
    return f"{v:.6g}"
