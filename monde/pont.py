"""Le pont, cote cerveau : un serveur TCP local auquel l extension Rust d Arma ( monde_x64.dll ) se connecte.
Une ligne = un tableau au format « tableau simple » d Arma, que Python lit et ecrit en JSON ( chiffres, chaines sans
guillemet interne, tableaux ). Les lots d ordres partent en lignes de 8 000 caracteres au plus."""
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


class Pont:
    def __init__(self, port=2350, hote="127.0.0.1"):
        self.port = port
        self.recus = queue.Queue()
        self.client = None
        self.n_lot = 0
        self.envoyes = 0; self.lus = 0; self.illisibles = 0
        self.serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serveur.bind((hote, port)); self.serveur.listen(1)
        threading.Thread(target=self._accepter, daemon=True).start()

    def _accepter(self):
        while True:
            c, _ = self.serveur.accept()
            c.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.client = c
            threading.Thread(target=self._lire, args=(c,), daemon=True).start()

    def _lire(self, c):
        tampon = b""
        while True:
            try: bloc = c.recv(65536)
            except OSError: break
            if not bloc: break
            tampon += bloc
            while b"\n" in tampon:
                ligne, tampon = tampon.split(b"\n", 1)
                try: self.recus.put(json.loads(ligne.decode("utf-8", "replace"))); self.lus += 1
                except json.JSONDecodeError: self.illisibles += 1
        if self.client is c: self.client = None

    def connecte(self): return self.client is not None

    def attendre(self, delai=120):
        t0 = time.time()
        while not self.connecte():
            if time.time() - t0 > delai: return False
            time.sleep(0.2)
        return True

    def envoyer(self, ordres):
        """Envoie une liste d ordres en un ou plusieurs lots. Rend les numeros de lot."""
        if not self.connecte(): raise ConnectionError("Arma n est pas connecte au pont")
        lots, courant = [], []
        for o in ordres:
            essai = courant + [o]
            if courant and len(vers_sqf([0, essai])) > LONGUEUR_MAX:
                lots.append(courant); courant = [o]
            else: courant = essai
        if courant: lots.append(courant)
        numeros = []
        for lot in lots:
            self.n_lot += 1
            self.client.sendall((vers_sqf([self.n_lot, lot]) + "\n").encode())
            self.envoyes += 1; numeros.append(self.n_lot)
        return numeros

    def messages(self, delai=0.0):
        """Tous les messages arrives ( attend au plus `delai` le premier )."""
        out = []
        try: out.append(self.recus.get(timeout=delai) if delai > 0 else self.recus.get_nowait())
        except queue.Empty: return out
        while True:
            try: out.append(self.recus.get_nowait())
            except queue.Empty: return out
