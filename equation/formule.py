"""
Formules EvoGP -> codes entiers pour la mission CHACAL ( parametres CHACAL_F0..F31 ) et evaluation Python identique
a l'interprete SQF ( CHACAL_fnc_evalNoeud, 60_phases.sqf ).
Codes, en ordre prefixe ( operateur, puis operande gauche, puis operande droit ) :
  101 +   102 -   103 *   104 min   105 max   106 neg ( unaire )   107 > ( vaut +1 si a > b, sinon -1 : mesure sur EvoGP )
  201.. variable x0.. ( perception d'indice code - 201 )
  301.. constante CONSTANTES[code - 301]
"""
import re

FONCTIONS = {"+": 101, "−": 102, "-": 102, "*": 103, "min": 104, "max": 105, "neg": 106, ">": 107}
CONSTANTES = [-1.0, -0.5, -0.25, 0.0, 0.25, 0.5, 1.0]
MAX_NOEUDS = 32
RX_JETON = re.compile(r"\s*(neg\(|\(|\)|min\b|max\b|[+*>−]|-(?=\s)|-?\d+(?:\.\d+)?|[A-Za-z_]\w*)")


def jetons(texte):
    pos, out = 0, []
    texte = texte.strip()
    while pos < len(texte):
        m = RX_JETON.match(texte, pos)
        if not m:
            raise ValueError(f"jeton illisible a {pos} : {texte[pos:pos + 20]!r}")
        out.append(m.group(1))
        pos = m.end()
    return out


def analyser(texte, noms):
    """Infix EvoGP ( '(a op b)', 'neg(a)', variables par nom ou xN, constantes ) -> arbre ( op, gauche, droite ) ou feuille."""
    t = jetons(texte)
    i = 0

    def terme():
        nonlocal i
        j = t[i]
        if j == "neg(":
            i += 1
            a = expr_parenthese_fin()
            return ("neg", a)
        if j == "(":
            i += 1
            a = terme()
            op = t[i]; i += 1
            if op not in FONCTIONS:
                raise ValueError(f"operateur inconnu {op!r}")
            b = terme()
            if t[i] != ")":
                raise ValueError(f"')' attendu, lu {t[i]!r}")
            i += 1
            return (op if op != "-" else "−", a, b)
        i += 1
        if re.fullmatch(r"-?\d+(?:\.\d+)?", j):
            return ("const", float(j))
        if re.fullmatch(r"x\d+", j):
            return ("var", int(j[1:]))
        if j in noms:
            return ("var", noms.index(j))
        raise ValueError(f"feuille inconnue {j!r}")

    def expr_parenthese_fin():
        nonlocal i
        a = terme()
        if t[i] != ")":
            raise ValueError(f"')' attendu apres neg, lu {t[i]!r}")
        i += 1
        return a

    arbre = terme()
    if i != len(t):
        raise ValueError(f"jetons restants : {t[i:]}")
    return arbre


def evaluer(arbre, x):
    k = arbre[0]
    if k == "const": return arbre[1]
    if k == "var": return float(x[arbre[1]])
    if k == "neg": return -evaluer(arbre[1], x)
    a, b = evaluer(arbre[1], x), evaluer(arbre[2], x)
    if k == "+": return a + b
    if k == "−": return a - b
    if k == "*": return a * b
    if k == "min": return min(a, b)
    if k == "max": return max(a, b)
    if k == ">": return 1.0 if a > b else -1.0
    raise ValueError(k)


def encoder(arbre):
    codes = []

    def visite(n):
        k = n[0]
        if k == "const":
            proches = [c for c in CONSTANTES if abs(c - n[1]) < 1e-6]
            if not proches:
                raise ValueError(f"constante hors liste : {n[1]}")
            codes.append(301 + CONSTANTES.index(proches[0]))
        elif k == "var":
            codes.append(201 + n[1])
        elif k == "neg":
            codes.append(106); visite(n[1])
        else:
            codes.append(FONCTIONS[k]); visite(n[1]); visite(n[2])

    visite(arbre)
    if len(codes) > MAX_NOEUDS:
        raise ValueError(f"{len(codes)} noeuds, {MAX_NOEUDS} au plus")
    return codes


def evaluer_codes(codes, x):
    """Evaluation par pile, EXACTEMENT comme l'interprete SQF ( recursif en prefixe )."""
    def noeud(i):
        c = codes[i]
        if c >= 301: return CONSTANTES[c - 301], i + 1
        if c >= 201: return float(x[c - 201]), i + 1
        if c == 106:
            a, j = noeud(i + 1); return -a, j
        a, j = noeud(i + 1)
        b, k = noeud(j)
        r = {101: a + b, 102: a - b, 103: a * b, 104: min(a, b), 105: max(a, b), 107: 1.0 if a > b else -1.0}[c]
        return r, k
    v, fin = noeud(0)
    if fin != len(codes):
        raise ValueError(f"codes non consommes : {fin} sur {len(codes)}")
    return v


def texte_lisible(arbre, noms):
    k = arbre[0]
    if k == "const": return f"{arbre[1]:g}"
    if k == "var": return noms[arbre[1]]
    if k == "neg": return f"-({texte_lisible(arbre[1], noms)})"
    return f"({texte_lisible(arbre[1], noms)} {k} {texte_lisible(arbre[2], noms)})"
