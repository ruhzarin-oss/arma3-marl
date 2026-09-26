"""L ENREGISTREUR DU MONDE ( 26/09, « enregistre tout » ) : chaque paiement, chaque mouvement de bien, chaque choix et
chaque note d un point de decision, chaque evenement, et chaque soir une photo de chaque habitant et de chaque menage,
en fichiers Parquet ( colonnes, zstd ) lus ensuite avec pyarrow ou DuckDB.

   <dossier>/<ile>/<table>/jour=00012/part-000.parquet

Tables :
  argent      pas, motif, payeur_classe, payeur_id, receveur_classe, receveur_id, montant ( le montant PAYE )
  biens       pas, nature, motif, bien, de_classe, de_id, vers_classe, vers_id, quantite
  decisions   pas, point, cle, action, traits ( liste de flottants, le terme constant compris )
  notes       pas, point, cle, action, note ( la note muree d un choix, a son horizon )
  evenements  pas, source ( moteur | journal ), type, json ( les champs )
  comptes     type, nombre, somme ( les evenements comptes du journal du socle, par jour )
  habitants   toutes les colonnes de la table des habitants ( photo du soir )
  menages     toutes les colonnes de la table des menages ( photo du soir )
Le jour est dans le nom du dossier ( jour=00012 ) : pyarrow et DuckDB le rendent comme une colonne.

L enregistreur LIT seulement : il ne tire aucun hasard et ne touche aucun etat ( porte_enregistreur : le monde
enregistre est identique au bit au monde nu, et les totaux enregistres retombent sur ceux du grand livre ). Il ne se
sauvegarde pas avec le monde : un instantane repris n a plus d enregistreur, on en rebranche un."""
import json, os
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

LOT_MAX = 400_000           # lignes gardees en memoire par table avant d ecrire une part ( ~40 Mo )
PHOTO_TRANCHE = 200_000     # lignes de la photo du soir copiees a la fois

SCHEMAS = {
    "argent": [("pas", pa.int64()), ("motif", pa.string()), ("payeur_classe", pa.string()), ("payeur_id", pa.string()),
               ("receveur_classe", pa.string()), ("receveur_id", pa.string()), ("montant", pa.float64())],
    "biens": [("pas", pa.int64()), ("nature", pa.string()), ("motif", pa.string()), ("bien", pa.string()),
              ("de_classe", pa.string()), ("de_id", pa.string()), ("vers_classe", pa.string()), ("vers_id", pa.string()),
              ("quantite", pa.float64())],
    "decisions": [("pas", pa.int64()), ("point", pa.string()), ("cle", pa.string()), ("action", pa.int16()),
                  ("traits", pa.list_(pa.float32()))],
    "notes": [("pas", pa.int64()), ("point", pa.string()), ("cle", pa.string()), ("action", pa.int16()),
              ("note", pa.float64())],
    "evenements": [("pas", pa.int64()), ("source", pa.string()), ("type", pa.string()), ("json", pa.string())],
    "comptes": [("type", pa.string()), ("nombre", pa.int64()), ("somme", pa.float64())],
}


def _rien(): return None


def _ident(o):
    """( classe, identifiant ) d un detenteur : les classes sont celles du grand livre ( type(o).__name__ ), les
    bornes du pays ( Exterieur, Emission ) sont des chaines."""
    if o is None: return "", ""
    if isinstance(o, str): return o, ""
    i = getattr(o, "id", None)
    if i is None:
        p = getattr(o, "proprietaire", None)
        i = getattr(p, "id", None) if p is not None else None
    return type(o).__name__, "" if i is None else str(i)


class Enregistreur:
    def __init__(self, dossier, ile, w):
        self.dossier, self.ile, self.w = os.path.join(dossier, ile), ile, w
        self.lignes = {t: [] for t in SCHEMAS}
        self.lots = []              # decisions posees en colonnes : ( pas, point, cles, traits 2D, actions )
        self.parts = {}             # ( table, jour ) -> numero de la prochaine part
        self.n = {t: 0 for t in SCHEMAS}
        self.n["decisions_lot"] = 0

    def __reduce__(self):           # un instantane du monde n emporte pas l enregistreur
        return (_rien, ())

    # ------------------------------------------------------------------ les crochets ( appeles par le socle et le moteur )
    def argent(self, motif, de, vers, montant):
        a, b = _ident(de); c, d = _ident(vers)
        self.lignes["argent"].append((self.w.pas, motif, a, b, c, d, float(montant)))
        if len(self.lignes["argent"]) >= LOT_MAX: self._ecrire("argent")

    def bien(self, nature, motif, bien, q, de=None, vers=None):
        a, b = _ident(de); c, d = _ident(vers)
        self.lignes["biens"].append((self.w.pas, nature, motif, str(bien), a, b, c, d, float(q)))
        if len(self.lignes["biens"]) >= LOT_MAX: self._ecrire("biens")

    def decision(self, point, cle, x, a):
        self.lignes["decisions"].append((self.w.pas, point, str(cle), int(a), list(x)))
        if len(self.lignes["decisions"]) >= LOT_MAX: self._ecrire("decisions")

    def decisions_lot(self, point, cles, traits, actions):
        self.lots.append((self.w.pas, point, np.asarray(cles), np.asarray(traits, np.float32), np.asarray(actions)))
        self.n["decisions_lot"] += len(cles)

    def note(self, point, cle, a, note):
        self.lignes["notes"].append((self.w.pas, point, str(cle), int(a), float(note)))
        if len(self.lignes["notes"]) >= LOT_MAX: self._ecrire("notes")

    def evenement(self, source, e):
        self.lignes["evenements"].append((self.w.pas, source, e.get("type", ""), json.dumps(e, ensure_ascii=False, default=str)))
        if len(self.lignes["evenements"]) >= LOT_MAX: self._ecrire("evenements")

    def comptes(self, jour, comptes):
        self._jour_comptes = int(jour)
        for t, (n, s) in comptes.items(): self.lignes["comptes"].append((t, int(n), float(s)))

    # ------------------------------------------------------------------ l ecriture
    def _chemin(self, table, jour):
        k = self.parts.get((table, jour), 0); self.parts[(table, jour)] = k + 1
        d = os.path.join(self.dossier, table, f"jour={jour:05d}")
        os.makedirs(d, exist_ok=True)
        return os.path.join(d, f"part-{k:03d}.parquet")

    def _ecrire(self, table):
        L = self.lignes[table]
        if not L: return
        noms = [n for n, _ in SCHEMAS[table]]
        cols = list(zip(*L))
        t = pa.table({n: pa.array(c, type=ty) for n, (_, ty), c in zip(noms, SCHEMAS[table], cols)})
        jour = int(L[0][0] // PAS_PAR_JOUR()) if table != "comptes" else self._jour_comptes
        pq.write_table(t, self._chemin(table, jour), compression="zstd")
        self.n[table] += len(L)
        self.lignes[table] = []

    def _ecrire_lots(self):
        if not self.lots: return
        for pas, point, cles, X, act in self.lots:
            n, k = X.shape if X.ndim == 2 else (len(cles), 0)
            traits = pa.FixedSizeListArray.from_arrays(pa.array(X.reshape(-1)), k).cast(pa.list_(pa.float32()))
            t = pa.table({"pas": pa.array(np.full(n, pas, np.int64)), "point": pa.array([point] * n, pa.string()),
                          "cle": pa.array(cles.astype(str)), "action": pa.array(act.astype(np.int16)), "traits": traits})
            pq.write_table(t, self._chemin("decisions", pas // PAS_PAR_JOUR()), compression="zstd")
        self.lots = []

    def photo(self, jour, suffixe=""):
        """Les colonnes des habitants et des menages, telles quelles ( une photo du soir )."""
        tb = self.w.table
        for nom, obj, n in (("habitants", tb, tb.n), ("menages", getattr(tb, "menages", None), None)):
            if obj is None: continue
            if n is None: n = getattr(obj, "n", None)
            cols = {}
            for c in getattr(type(obj), "CHAMPS", {}):
                v = getattr(obj, c, None)
                if isinstance(v, np.ndarray) and v.ndim == 1 and len(v) >= n: cols[c] = v
            if not cols: continue
            # par tranches de PHOTO_TRANCHE lignes : a un million d habitants, six iles photographiees au meme pas ne
            # doivent pas doubler la memoire ( une tranche copiee a la fois )
            ecrivain = None
            for a in range(0, max(n, 1), PHOTO_TRANCHE):
                t = pa.table({c: pa.array(v[a:min(n, a + PHOTO_TRANCHE)]) for c, v in cols.items()})
                if ecrivain is None: ecrivain = pq.ParquetWriter(self._chemin(nom + suffixe, jour), t.schema, compression="zstd")
                ecrivain.write_table(t)
            if ecrivain is not None: ecrivain.close()

    def fin_de_jour(self, jour):
        for t in SCHEMAS: self._ecrire(t)
        self._ecrire_lots()
        self.photo(jour)

    def fermer(self):
        for t in SCHEMAS: self._ecrire(t)
        self._ecrire_lots()


def PAS_PAR_JOUR():
    from . import config as C
    return C.PAS_PAR_JOUR


# ------------------------------------------------------------------ brancher sur un monde
def brancher(w, dossier, ile=None):
    """Branche un enregistreur sur le monde `w` et son pays : grand livre, journal du socle, points de decision."""
    ile = ile or w.carte.iles[0]
    e = Enregistreur(dossier, ile, w)
    w.enregistreur = e
    p = getattr(w, "pays", None)
    if p is not None:
        p.socle.livre.enregistreur = e
        if hasattr(p.socle, "journal"): p.socle.journal.enregistreur = e
        for dec in _decideurs(p): dec.enregistreur = e
    e.photo(w.jour, suffixe="_debut")       # l etat au branchement : ce que l installation a deja fait
    return e


def _decideurs(p):
    vus = set()
    for dec in getattr(p, "decideurs", {}).values():
        if id(dec) not in vus: vus.add(id(dec)); yield dec
