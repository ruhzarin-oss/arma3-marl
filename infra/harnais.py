#!/usr/bin/env python3
"""BRIQUE 2 — HARNAIS UNIQUE DE BANC.

Ce que tout banc de nuit fait pareil, et qu on a reecrit a chaque fois cette semaine :
  · jouer le CONTROLE POSITIF en bloc 0, et ABANDONNER si il tombe ;
  · ecrire UNE LIGNE PAR EPISODE en bronze DES SA FIN — une nuit interrompue garde tout ;
  · survivre a la mort du pont : jeter le bloc en cours, se reconnecter, RESYNCHRONISER,
    reprendre au bloc suivant. Un bloc perdu ne desequilibre rien s il est court ;
  · relever le FPS serveur et compter les morts du pont ;
  · ecrire le DEPOT du matin depuis les CRITERES, avec les empreintes de ce qui a tourne.

⚠️ APRES UNE RELEVE, LE COMPTEUR DU PONT REPART A ZERO cote serveur. Les lignes d avant
sont encore dans le tampon du client. Le harnais emet donc un MARQUEUR unique et JETTE tout
ce qui precede son echo — sans ca, un banc relit les episodes de la vie precedente.
"""
import json, os, re, time, hashlib, datetime, random, sys
sys.path.insert(0, "/home/younes/arma3-marl/leviathan")
from native_bridge import NativeBridge

# ⚠️⚠️ `/mnt/data/lake/bronze` EST UN LIEN SYMBOLIQUE VERS `/mnt/data2/corpus`, ET
# `/mnt/data2` N EST PAS MONTE (constate le 04/09). La couche bronze du lac est donc MORTE :
# tout ce qui y ecrit echoue. On ne repare pas le lac de Younes a sa place — on ecrit dans un
# repertoire REEL, nomme sans ambiguite, sur le disque qui EST monte, et on le lui signale.
LAC = "/mnt/data/lake/bronze_certif"
RACINE = "/home/younes/arma3-marl"


def empreinte(chemin):
    try:
        return hashlib.sha256(open(chemin, "rb").read()).hexdigest()[:16]
    except OSError:
        return "absent"


class Harnais:
    def __init__(self, banc, criteres, port=5801, bloc_max_s=1200):
        self.banc = banc
        self.criteres = criteres
        self.port = port
        self.bloc_max_s = bloc_max_s          # 20 min : un bloc perdu coute peu
        self.nuit = datetime.date.today().isoformat()
        self.dossier = "%s/nuit=%s/banc=%s" % (LAC, self.nuit, banc)
        os.makedirs(self.dossier, exist_ok=True)
        self.fic = open("%s/episodes.jsonl" % self.dossier, "a", buffering=1)
        self.morts_pont = 0
        self.blocs_jetes = 0
        self.fps = []
        self.t0 = time.time()
        self.b = NativeBridge(port=port, timeout=20)
        self._resync("ouverture")

    # ---------- pont ----------
    def _resync(self, motif):
        """Jette tout ce qui precede l echo du marqueur. Sans ca on relit la vie d avant."""
        tag = "HMTRS%d" % random.randint(10 ** 6, 10 ** 7 - 1)
        with self.b._lock:
            self.b.lines.clear()
        try:
            self.b.query('format ["%s"] call HMT_EMIT;' % tag, tag, want=1, timeout=30)
            return True
        except Exception:
            print("  [harnais] resync %s SANS ECHO — le pont accepte mais la mission ne repond pas" % motif,
                  flush=True)
            return False

    def _reconnecter(self):
        self.morts_pont += 1
        for essai in range(60):                      # la sentinelle a 10 min pour relever
            time.sleep(10)
            try:
                self.b = NativeBridge(port=self.port, timeout=20)
                if self._resync("apres releve"):
                    print("  [harnais] pont repris apres %d s" % (10 * (essai + 1)), flush=True)
                    return True
            except Exception:
                continue
        print("  [harnais] pont IRRECUPERABLE", flush=True)
        return False

    def query(self, sqf, motif, want=1, timeout=180):
        """Interroge. Rend None si le pont est mort — l appelant JETTE son bloc."""
        try:
            return self.b.query(sqf, motif, want=want, timeout=timeout)
        except Exception as e:
            print("  [harnais] pont %s pendant un bloc" % type(e).__name__, flush=True)
            self.blocs_jetes += 1
            return None if self._reconnecter() else False

    # ---------- mesure ----------
    def episode(self, **champs):
        """UNE ligne, ecrite DES la fin de l episode. Rien n attend la fin de la nuit."""
        self.fic.write(json.dumps(dict(t=time.time(), **champs)) + "\n")

    def releve_fps(self):
        r = self.query('format ["HMTFPS %1", round (diag_fps * 10)] call HMT_EMIT;',
                       r"HMTFPS (\d+)", timeout=40)
        if r:
            self.fps.append(int(r[0].group(1)) / 10.0)

    def bloc0(self, fn_controle):
        """Le controle positif. S il tombe, la nuit est ⛔ instrument et le banc s arrete."""
        print("  [harnais] BLOC 0 — controle positif", flush=True)
        ok, detail = fn_controle(self)
        self.episode(bloc=0, controle=bool(ok), detail=detail)
        if not ok:
            print("  [harnais] ⛔ CONTROLE POSITIF TOMBE : %s" % detail, flush=True)
        return ok

    def blocs(self, fn_bloc, n):
        """Boucle de blocs. Un bloc qui rend None a perdu le pont : il est JETE, pas rejoue."""
        rendus = 0
        for k in range(n):
            t = time.time()
            r = fn_bloc(self, k)
            if r is False:
                print("  [harnais] arret : pont irrecuperable au bloc %d" % k, flush=True); break
            if r is None:
                print("  [harnais] bloc %d JETE (pont)" % k, flush=True); continue
            rendus += 1
            self.episode(bloc=k + 1, duree_s=round(time.time() - t, 1), **r)
            self.releve_fps()
        return rendus

    # ---------- depot ----------
    def depot(self, verdicts, tableaux="", ouvert=""):
        """Le DEPOT du matin. Younes lit ca, jamais le bronze."""
        chem = "%s/DEPOT_%s_%s.md" % (RACINE, self.nuit, self.banc)
        fps = ("%.1f" % (sum(self.fps) / len(self.fps))) if self.fps else "non releve"
        with open(chem, "w") as f:
            f.write("# DEPOT %s — %s\n\n" % (self.nuit, self.banc))
            f.write("Criteres : `%s` (ecrits avant les chiffres).\n" % self.criteres)
            f.write("Bronze : `%s/episodes.jsonl`.\n\n" % self.dossier)
            f.write("## VERDICT PAR CRITERE\n\n")
            for nom, (etat, txt) in verdicts.items():
                f.write("- **%s** : %s — %s\n" % (nom, etat, txt))
            if tableaux:
                f.write("\n## MESURE\n\n%s\n" % tableaux)
            f.write("\n## CONDITIONS DE LA NUIT\n\n")
            f.write("- duree : %.0f min · FPS serveur moyen : %s\n" % ((time.time() - self.t0) / 60, fps))
            f.write("- morts du pont : **%d** · blocs jetes : **%d**\n" % (self.morts_pont, self.blocs_jetes))
            f.write("- empreinte `canal_cwr.py` : `%s`\n" % empreinte(RACINE + "/canal_cwr.py"))
            f.write("- empreinte `assault_terrain.py` : `%s`\n" % empreinte(RACINE + "/assault_terrain.py"))
            e = empreinte("%s/%s.py" % (RACINE, self.banc))
            if e == "absent":
                e = empreinte("%s/infra/%s.py" % (RACINE, self.banc))
            f.write("- empreinte du banc : `%s`\n" % e)
            if ouvert:
                f.write("\n## CE QUI RESTE OUVERT\n\n%s\n" % ouvert)
        print("  [harnais] depot : %s" % chem, flush=True)
        return chem

    def fermer(self):
        try:
            self.fic.close(); self.b.sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    # BANC D ESSAI DU HARNAIS LUI-MEME : il doit ecrire du bronze, relever le FPS,
    # produire un depot, et son controle positif doit pouvoir ECHOUER.
    h = Harnais("essai_harnais", "CRITERES_ESSAI.md", port=int(sys.argv[1]) if len(sys.argv) > 1 else 5801)

    def controle(h):
        r = h.query('format ["HMTC %1", 6*7] call HMT_EMIT;', r"HMTC (\d+)", timeout=40)
        if not r:
            return False, "pas de reponse"
        v = int(r[0].group(1))
        return v == 42, "6*7 rend %d (attendu 42)" % v

    ok = h.bloc0(controle)
    # ⚠️ JAMAIS de formatage `%` sur du SQF : `%1` y est une balise de `format`, pas une
    # conversion Python. Le projet a deja paye ce piege (`_i%%4` -> boucle morte en silence).
    # On substitue par jeton, toujours.
    def bloc(h, k):
        sqf = 'format ["HMTB __K__"] call HMT_EMIT;'.replace("__K__", str(k))
        return {"n": 1} if h.query(sqf, r"HMTB (\d+)", timeout=40) else None
    n = h.blocs(bloc, 3) if ok else 0
    h.depot({"controle positif": ("✔" if ok else "⛔", "le harnais parle au monde"),
             "blocs rendus": ("✔" if n == 3 else "⛔", "%d sur 3" % n)},
            ouvert="Banc d essai : ne mesure rien du monde, teste le harnais.")
    h.fermer()
    print("  essai : controle %s · blocs %d/3" % ("OK" if ok else "ECHEC", n))
