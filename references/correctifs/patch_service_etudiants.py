"""29/09 ( d25, chef de projet et Classes ) : l etudiant SURSITAIRE.
A la sortie des etudes, le domaine 4 donnait la formation militaire a SERVICE_MILITAIRE ( 85 % des hommes ) sans aucun
service : un raccourci d avant le domaine 25. Dans un monde recense sur le reel ( table.recensement ) ou l armee est
installee, l etudiant est sursitaire ( loi 3421/2005, art. 18 par. 2 : jusqu a 28 ans pour les etudes superieures et le
master ) et le domaine 25 l appelle a sa sortie ; le domaine 4 ne lui donne plus la formation. Le tirage reste fait : les
suivants ( les titres de sortie ) ne bougent pas. Sans armee ni recensement ( l arbre des references, le monde E1 ), rien
ne change. Le meme texte pour le depot et l arbre des references. Idempotent ( chaque insertion a sa premiere ligne
propre ).
   python patch_service_etudiants.py racine_de_l_arbre"""
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


remplacer("monde/pays/d04_travail.py", [
    ('''def _sortir_des_etudes(p, d, h, rng):
''', '''def _service_par_l_armee(p):
    """( 29/09 ) Le service national est fait par le domaine 25 : l armee est installee dans un monde recense sur le reel
    ( table.recensement ). L etudiant y est sursitaire ( loi 3421/2005, art. 18 par. 2 ), appele a la sortie de ses
    etudes ; la formation militaire lui vient au terme de son service."""
    return p.a("armee") and getattr(p.w.table, "recensement", None) is not None


def _sortir_des_etudes(p, d, h, rng):
'''),
    ('''    if age >= 19 and rng.random() < SERVICE_MILITAIRE.get(sexe, 0.0): col["tr_qualifs"][i] |= BIT["formation_militaire"]
''', '''    # ( 29/09 ) sursitaire : le domaine 25 l appellera ; le tirage reste fait, les suivants ne bougent pas
    if age >= 19 and rng.random() < SERVICE_MILITAIRE.get(sexe, 0.0) and not _service_par_l_armee(p):
        col["tr_qualifs"][i] |= BIT["formation_militaire"]
'''),
])
