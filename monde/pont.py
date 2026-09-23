"""Le pont, cote cerveau : un serveur TCP local auquel les extensions Rust d Arma ( monde_x64.dll ) se connectent.

PLUSIEURS serveurs a la fois ( point 13 ) : chaque Arma annonce son ile en se connectant ( ["bonjour", "Altis", ...] )
et le cerveau range ses corps par ile. Une ligne = un tableau au format « tableau simple » d Arma, que Python lit et
ecrit en JSON ( chiffres, chaines sans guillemet interne, tableaux ). Les lots partent en lignes de 8 000 caracteres."""
import json, queue, socket, threading, time

LONGUEUR_MAX = 8000


def vers_sqf(x):
    """Python -> tableau simple d Arma. Les chaines ne doivent pas contenir de guillemet ( refuse, jamais tronque )."""
    def verifier(v):
        if isinstance(v, str) and '"' in v: raise ValueError(f"guillemet interdit dans une chaine du pont : {v!r}")
        if isinstance(v, (list, tuple)):
            for w in v: verifier(w)
    verifier(x)
    return json.dumps(x, ensure_ascii=True, separators=(",", ":"))


class Client:
    """Un serveur Arma au bout du fil. Tant qu il n a pas dit son ile, il s appelle « inconnue »."""

    def __init__(self, prise):
        self.prise = prise
        self.ile = "inconnue"
        self.n_lot = 0
        self.envoyes = 0


class Pont:
    def __init__(self, port=2350, hote="127.0.0.1"):
        self.port = port
        self.recus = queue.Queue()
        self.clients = []
        self.envoyes = 0; self.lus = 0; self.illisibles = 0
        self.verrou = threading.Lock()
        self.serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serveur.bind((hote, port)); self.serveur.listen(8)
        threading.Thread(target=self._accepter, daemon=True).start()

    # ------------------------------------------------------------------ les connexions
    def _accepter(self):
        while True:
            p, _ = self.serveur.accept()
            p.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            c = Client(p)
            with self.verrou: self.clients.append(c)
            threading.Thread(target=self._lire, args=(c,), daemon=True).start()

    def _lire(self, c):
        tampon = b""
        while True:
            try: bloc = c.prise.recv(65536)
            except OSError: break
            if not bloc: break
            tampon += bloc
            while b"\n" in tampon:
                ligne, tampon = tampon.split(b"\n", 1)
                try: m = json.loads(ligne.decode("utf-8", "replace"))
                except json.JSONDecodeError: self.illisibles += 1; continue
                self.lus += 1
                if isinstance(m, list) and m and m[0] == "bonjour" and len(m) > 1:
                    c.ile = str(m[1])                    # le serveur dit quelle ile il fait tourner
                self.recus.put((c.ile, m))
        with self.verrou:
            if c in self.clients: self.clients.remove(c)

    # ------------------------------------------------------------------ l etat
    def connecte(self, ile=None, exact=False):
        """Une ile est connectee quand un serveur l a NOMMEE. Un serveur anonyme ne compte que s il est le seul :
        sinon le cerveau parlerait a tout le monde a la fois et creerait le meme corps sur deux cartes ( 22/09 )."""
        with self.verrou:
            if ile is None: return bool(self.clients)
            if any(c.ile == ile for c in self.clients): return True
            if exact: return False                    # au demarrage d un monde a plusieurs iles, on veut des NOMS
            return len(self.clients) == 1 and self.clients[0].ile == "inconnue"

    def iles(self):
        with self.verrou: return sorted({c.ile for c in self.clients})

    def attendre(self, delai=120, ile=None, exact=False):
        t0 = time.time()
        while not self.connecte(ile, exact):
            if time.time() - t0 > delai: return False
            time.sleep(0.2)
        return True

    # ------------------------------------------------------------------ parler
    def _destinataires(self, ile):
        with self.verrou:
            if ile is None: return list(self.clients)
            exacts = [c for c in self.clients if c.ile == ile]
            if exacts: return exacts
            # un seul serveur, encore anonyme : c est forcement lui. Plusieurs : on n envoie rien plutot que partout.
            return list(self.clients) if len(self.clients) == 1 and self.clients[0].ile == "inconnue" else []

    def envoyer(self, ordres, ile=None):
        """Envoie une liste d ordres a l ile demandee ( ou au seul serveur connecte ). Rend les numeros de lot."""
        cibles = self._destinataires(ile)
        if not cibles: raise ConnectionError(f"aucun serveur Arma pour l ile {ile}")
        lots, courant = [], []
        for o in ordres:
            essai = courant + [o]
            if courant and len(vers_sqf([0, essai])) > LONGUEUR_MAX:
                lots.append(courant); courant = [o]
            else: courant = essai
        if courant: lots.append(courant)
        numeros = []
        for c in cibles:
            for lot in lots:
                c.n_lot += 1
                c.prise.sendall((vers_sqf([c.n_lot, lot]) + "\n").encode())
                c.envoyes += 1; self.envoyes += 1
                numeros.append(c.n_lot)
        return numeros

    def messages(self, delai=0.0):
        """Tous les messages arrives, sans leur ile ( compatibilite ). Voir `messages_iles` pour savoir d ou ils viennent."""
        return [m for _, m in self.messages_iles(delai)]

    def messages_iles(self, delai=0.0):
        out = []
        try: out.append(self.recus.get(timeout=delai) if delai > 0 else self.recus.get_nowait())
        except queue.Empty: return out
        while True:
            try: out.append(self.recus.get_nowait())
            except queue.Empty: return out
