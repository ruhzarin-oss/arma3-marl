"""LA BASE DE CONNAISSANCE DU MOTEUR, l extraction ( HMT-198, chantier K ) : tout ce que le code sait de lui-meme, en
fiches courtes qui gardent leur provenance ( fichier, ligne ).

Les sources : chaque module de monde/ et de guerre/ ( les FICHES des domaines, coupees a leurs sections numerotees ;
sinon par paragraphes ), chaque fonction, methode et classe qui a une docstring ( sa signature, sa docstring ), les
blocs de constantes en capitales avec leurs commentaires ( la ou le moteur ecrit ses sources et ses CHOIX ), et les
plans en Markdown ( plans/*.md, coupes a leurs titres ). Les portes ( tests_*.py, porte_*.py ) sont des fiches comme
les autres, marquees « porte ».

Une fiche : { id, fichier, ligne, type ( module, section, fonction, classe, constantes, plan ), nom, domaine, texte,
contexte }. Le contexte d une fonction ( le titre de son module et les lignes de la fiche du module qui la nomment ) est
indexe avec elle : une docstring pauvre est retrouvee par ce que son module dit d elle ( 03/10, porte K1 refusee ).

   python -m guerre.connaissance.extraire [ sortie.jsonl ]"""
import ast
import glob
import json
import os
import re
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SORTIE = "/mnt/data/hmt/connaissance/fiches.jsonl"
MOTIFS = ("monde/**/*.py", "guerre/**/*.py")
PLANS = ("plans/*.md",)
TAILLE_MAX = 2400                        # caracteres d une fiche ( un bloc plus long est coupe a ses paragraphes )
CONTEXTE_MAX = 800                       # caracteres du contexte d une fiche de fonction ( titre et lignes de la fiche du module )
SECTION = re.compile(r"^\s{0,3}(\d{1,2})\.\s+\S", re.M)


def domaine_de(fichier):
    m = re.search(r"/(d\d\d)_", fichier)
    if m: return m.group(1)
    if fichier.startswith("guerre/"): return "guerre"
    return "moteur"


def _couper(texte, taille=TAILLE_MAX):
    """Des morceaux de moins de `taille` caracteres, coupes aux lignes vides puis aux lignes."""
    if len(texte) <= taille: return [texte]
    out, cur = [], ""
    for para in re.split(r"\n\s*\n", texte):
        if len(cur) + len(para) + 2 <= taille: cur = (cur + "\n\n" + para) if cur else para; continue
        if cur: out.append(cur)
        while len(para) > taille:
            k = para.rfind("\n", 0, taille)
            if k <= 0: k = taille
            out.append(para[:k]); para = para[k:].lstrip("\n")
        cur = para
    if cur: out.append(cur)
    return out


def _signature(n):
    try: return f"{'class' if isinstance(n, ast.ClassDef) else 'def'} {n.name}({ast.unparse(n.args) if not isinstance(n, ast.ClassDef) else ', '.join(ast.unparse(b) for b in n.bases)})"
    except Exception: return n.name


def fiches_python(chemin, rel):
    src = open(chemin, encoding="utf-8").read()
    try: m = ast.parse(src)
    except SyntaxError: return []
    lignes = src.splitlines(); dom = domaine_de(rel)
    porte = os.path.basename(rel).startswith(("tests_", "porte_"))
    out = []

    def fiche(type_, nom, ligne, texte, contexte=""):
        for k, morceau in enumerate(_couper(texte)):
            out.append({"id": f"{rel}::{nom}" + (f"#{k}" if k else ""), "fichier": rel, "ligne": int(ligne), "type": type_,
                        "nom": nom, "domaine": dom, "porte": porte, "texte": morceau, "contexte": contexte})

    doc = ast.get_docstring(m)
    titre_module = (doc or "").strip().splitlines()[0][:200] if doc else ""
    lignes_doc = (doc or "").splitlines()

    def contexte_de(nom):
        """( HMT-198 K1 ) Le titre du module et les lignes de sa fiche qui nomment la fonction : l expansion d une fiche
        pauvre par son contexte ( indexee, jamais montree comme la fiche )."""
        if not nom: return titre_module
        motif = re.compile(rf"\b{re.escape(nom)}\b")
        vues = [l.strip() for l in lignes_doc if motif.search(l)]
        return (titre_module + " " + " ".join(vues))[:CONTEXTE_MAX]
    if doc:
        titre = doc.splitlines()[0]
        pos = [x.start() for x in SECTION.finditer(doc)]
        if "FICHE" in doc and len(pos) >= 3:
            fiche("module", "module", 1, doc[:pos[0]].strip())
            for a, b in zip(pos, pos[1:] + [len(doc)]):
                sec = doc[a:b].strip(); num = SECTION.match(doc[a:b]).group(1)
                fiche("section", f"FICHE.{num}", 1, f"{titre}\n{sec}")
        else:
            fiche("module", "module", 1, doc)
    def visiter(noeuds, prefixe):
        for n in noeuds:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                d = ast.get_docstring(n); q = prefixe + n.name
                if d: fiche("classe" if isinstance(n, ast.ClassDef) else "fonction", q, n.lineno, f"{_signature(n)}\n{d}",
                            contexte_de(n.name))
                visiter(n.body, q + ".")
    visiter(m.body, "")
    # les blocs de constantes en capitales, avec les commentaires qui les entourent
    bloc, debut = [], None
    def fermer():
        nonlocal bloc, debut
        if bloc:
            texte = "\n".join(bloc).strip()
            if len(texte) > 40: fiche("constantes", f"constantes@{debut}", debut, texte)
        bloc, debut = [], None
    i = 0
    while i < len(m.body):
        n = m.body[i]
        cible = n.targets[0] if isinstance(n, ast.Assign) and len(n.targets) == 1 else (n.target if isinstance(n, ast.AnnAssign) else None)
        if isinstance(cible, ast.Name) and cible.id.isupper() or (isinstance(cible, ast.Tuple) and all(isinstance(e, ast.Name) and e.id.isupper() for e in cible.elts)):
            a = n.lineno
            while a - 2 >= 0 and lignes[a - 2].lstrip().startswith("#"): a -= 1          # les commentaires d avant
            if debut is None: debut = a
            for x in range(a, n.end_lineno + 1):
                l = lignes[x - 1]
                if not bloc or l not in bloc[-3:]: bloc.append(l)
            if sum(len(x) for x in bloc) > TAILLE_MAX: fermer()
        else:
            fermer()
        i += 1
    fermer()
    return out


def fiches_markdown(chemin, rel):
    src = open(chemin, encoding="utf-8").read(); out = []
    parts = re.split(r"(?m)^(#{1,3} .*)$", src)
    titre, ligne, cur = os.path.basename(rel), 1, parts[0]
    blocs = []
    if cur.strip(): blocs.append((titre, 1, cur))
    for k in range(1, len(parts), 2):
        t = parts[k].strip("# ").strip(); corps = parts[k + 1] if k + 1 < len(parts) else ""
        blocs.append((t, src[:src.find(parts[k])].count("\n") + 1, parts[k] + corps))
    for t, l, texte in blocs:
        for j, morceau in enumerate(_couper(texte.strip())):
            if not morceau.strip(): continue
            out.append({"id": f"{rel}::{t}" + (f"#{j}" if j else ""), "fichier": rel, "ligne": l, "type": "plan", "nom": t,
                        "domaine": "plan", "porte": False, "texte": morceau})
    return out


def extraire(racine=RACINE):
    out = []
    for motif in MOTIFS:
        for f in sorted(glob.glob(os.path.join(racine, motif), recursive=True)):
            rel = os.path.relpath(f, racine)
            if "/__pycache__/" in rel or "/connaissance/" in rel: continue
            out += fiches_python(f, rel)
    for motif in PLANS:
        for f in sorted(glob.glob(os.path.join(racine, motif))):
            out += fiches_markdown(f, os.path.relpath(f, racine))
    vus = set()
    for x in out:                                         # des identifiants uniques
        b = x["id"]; k = 1
        while x["id"] in vus: k += 1; x["id"] = f"{b}~{k}"
        vus.add(x["id"])
    return out


def main(sortie=SORTIE):
    fs = extraire()
    os.makedirs(os.path.dirname(sortie), exist_ok=True)
    with open(sortie, "w", encoding="utf-8") as f:
        for x in fs: f.write(json.dumps(x, ensure_ascii=False) + "\n")
    from collections import Counter
    print(len(fs), "fiches", dict(Counter(x["type"] for x in fs)), sum(len(x["texte"]) for x in fs), "caracteres")
    return fs


if __name__ == "__main__":
    main(*sys.argv[1:])
