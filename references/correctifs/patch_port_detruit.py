"""02/10 ( HMT-192, etape 1b d Arma a fond ) : un port DETRUIT par une frappe ne sert plus, comme un port tenu par
l ennemi. guerre/frappes.py pose w.ports_hors_service ( lieu -> pas de fin de la reparation ) ; le domaine 7 le relit a
chaque appel de sous_blocus. Sans frappe, rien ne change. Le meme texte pour le depot et l arbre des references ( le
domaine 7 y est ). Idempotent ( chaque insertion a sa premiere ligne propre ).
   python patch_port_detruit.py racine_de_l_arbre"""
import os, sys
R = sys.argv[1]


def _nouveau(a, b):
    return next((l for l in b.splitlines() if l.strip() and l not in a.splitlines()), None)


def remplacer(chemin, paires):
    f = os.path.join(R, chemin)
    if not os.path.exists(f): print("absent :", f); return
    s = open(f).read(); n = 0
    for a, b in paires:
        m = _nouveau(a, b)
        if b in s or (m is not None and m in s): continue
        if s.count(a) != 1: raise SystemExit(f"{chemin} : {s.count(a)} fois {a!r}")
        s = s.replace(a, b); n += 1
    open(f, "w").write(s); print("corrige :" if n else "deja :", f)


remplacer("monde/pays/d07_exterieur.py", [
    ('''def sous_blocus(p):''', '''def ports_hors_service(p):
    """( 02/10, HMT-192 1b ) Les ports de l ile detruits par une frappe ( guerre/frappes.py : w.ports_hors_service, lieu ->
    pas de fin de la reparation ), tant que la reparation n est pas finie ; la regle se relit a chaque appel."""
    w = p.w; hs = getattr(w, "ports_hors_service", None)
    if not hs: return ()
    return tuple(sorted(l for l, fin in hs.items() if fin > w.pas and l in w.carte.lieux))


def sous_blocus(p):'''),
    ('''    w = p.w
    if not getattr(w, "occupations", None): return False
    ports = [l for l, x in w.carte.lieux.items() if x.type == "port"]
    return bool(ports) and set(ports) <= set(ports_tenus(p))''', '''    w = p.w
    hs = ports_hors_service(p)                        # ( 02/10, HMT-192 1b ) un port detruit ne sert plus
    if not getattr(w, "occupations", None) and not hs: return False
    ports = [l for l, x in w.carte.lieux.items() if x.type == "port"]
    return bool(ports) and set(ports) <= set(ports_tenus(p)) | set(hs)'''),
])
