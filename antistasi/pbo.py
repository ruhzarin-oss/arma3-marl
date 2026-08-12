"""Lecteur PBO minimal (liste / extrait). Format BI : entetes puis blocs de donnees."""
import struct, sys, os

def _cstr(b, i):
    j = b.index(b"\x00", i)
    return b[i:j].decode("utf-8", "replace"), j + 1

def read_pbo(path):
    b = open(path, "rb").read()
    i = 0
    entries = []
    while True:
        name, i = _cstr(b, i)
        method, osize, res, ts, dsize = struct.unpack_from("<5I", b, i)
        i += 20
        if name == "" and method == 0x56657273:          # entete Vers : proprietes
            while True:
                k, i = _cstr(b, i)
                if k == "": break
                v, i = _cstr(b, i)
            continue
        if name == "" and dsize == 0 and method == 0:     # fin de la liste
            break
        entries.append({"name": name.replace("\\", "/"), "method": method,
                        "osize": osize, "dsize": dsize})
    off = i
    for e in entries:
        e["off"] = off
        off += e["dsize"]
    return b, entries

def extract(path, prefix, dest):
    b, entries = read_pbo(path)
    n = 0
    pfx = prefix.replace("\\", "/").lower()
    for e in entries:
        if not e["name"].lower().startswith(pfx): continue
        if e["method"] not in (0, 0x43707273):
            print("METHODE INCONNUE", hex(e["method"]), e["name"]); continue
        if e["method"] == 0x43707273:
            print("COMPRESSE (non gere)", e["name"]); continue
        rel = e["name"][len(prefix):].lstrip("/")
        out = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "wb").write(b[e["off"]:e["off"] + e["dsize"]])
        n += 1
    return n

if __name__ == "__main__":
    if sys.argv[1] == "ls":
        _, es = read_pbo(sys.argv[2])
        pat = sys.argv[3] if len(sys.argv) > 3 else ""
        for e in es:
            if pat.lower() in e["name"].lower():
                print("%-70s m=%s %8d" % (e["name"], hex(e["method"]), e["dsize"]))
    else:
        print(extract(sys.argv[2], sys.argv[3], sys.argv[4]), "fichiers extraits")


# ---------- ecriture ----------
import hashlib

def pack(srcdir, out, prefix):
    """Empaquette un dossier en PBO non compresse, non signe."""
    files = []
    for root, dirs, fns in os.walk(srcdir):
        for fn in sorted(fns):
            if fn == "$PBOPREFIX$": continue
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, srcdir).replace("/", "\\")
            files.append((rel, open(full, "rb").read()))
    h = b"\x00" + struct.pack("<5I", 0x56657273, 0, 0, 0, 0)
    h += b"prefix\x00" + prefix.encode() + b"\x00" + b"\x00"
    for rel, data in files:
        h += rel.encode() + b"\x00" + struct.pack("<5I", 0, len(data), 0, 0, len(data))
    h += b"\x00" + struct.pack("<5I", 0, 0, 0, 0, 0)
    blob = h + b"".join(d for _, d in files)
    open(out, "wb").write(blob + b"\x00" + hashlib.sha1(blob).digest())
    return len(files)
