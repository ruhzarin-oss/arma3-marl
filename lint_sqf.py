#!/usr/bin/env python3
"""lint_sqf.py — ATTRAPER EN DIX SECONDES CE QUI COUTE QUATRE MINUTES DE DEMARRAGE.

⟨Younes, 09/08 : « apporte les corrections necessaires »⟩

NEUF PANNES EN VINGT-QUATRE HEURES, ET AUCUNE NE VENAIT DU MONDE. Toutes de ma main, toutes
decouvertes en production, a quatre minutes de demarrage la piece :

  · `exitWith` employe comme un `if` — il quitte TOUT LE BLOC englobant. La phase 2 a charge
    ses sept terrains puis s est arretee net, muette, treize minutes.
  · `magazinesAmmo` employe comme commande BINAIRE alors qu elle est UNAIRE. Deux erreurs de
    script, zero essai, une heure perdue.
  · `suppressFor` recopiee d Antistasi sans etre lue — elle SUPPRIME celui a qui on l applique.
    Mes propres tireurs supprimes, le natif passe de 414 coups a zero.
  · `someAmmo` pris pour « son fusil est charge » — il repond oui pour une grenade.
  · `Hit` pose sur un homme `allowDamage false` — l evenement ne se declenche jamais.

CE LINTEUR NE COMPREND PAS LE SQF. Il attrape les FAMILLES de fautes que j ai reellement
commises, et rien d autre. C est un filet a mailles connues, pas un compilateur — et il vaut
mieux qu un filet parfait qui n existe pas.
"""
import re, sys, pathlib

# ── les commandes UNAIRES que j ai employees ou risque d employer comme binaires
# ⚠️ LISTE CURETEE APRES TROIS FAUX POSITIFS. `getDir` existe AUSSI en forme binaire
# (`_u getDir _cible`), et `allGroups` ne prend AUCUN argument — c est `count` devant lui qui
# declenchait l alerte. Ma liste melangeait trois familles : unaires strictes, unaires qui ont
# aussi une forme binaire, et nullaires. On ne garde que les UNAIRES STRICTES.
UNAIRES = """magazinesAmmo someAmmo canFire canMove unitReady primaryWeapon secondaryWeapon
handgunWeapon currentWeapon currentMagazine assignedItems lifeState behaviour combatMode
speedMode formation getSuppression getUnitLoadout isDamageAllowed unitPos stance
simulationEnabled roleDescription""".split()

# les mots qui peuvent legitimement preceder une commande unaire : ce sont des operateurs, pas
# l argument de gauche d une binaire.
DEVANT = set("""count forEach select apply in then else do call spawn exitWith isEqualTo
isEqualType pushBack append params private max min and or not if while case default
findIf sort reverse toArray str format hint diag_log""".split())

# ── les evenements qui ne se declenchent PAS dans certaines conditions
PIEGES = [
    (r'addEventHandler\s*\[\s*"Hit"',
     'l evenement `Hit` ne se declenche pas sur un homme `allowDamage false` — '
     'il comptait 0 quand `HitPart` comptait 80. Employer `HandleDamage` rendant 0.'),
    (r'\bsuppressFor\b',
     '`suppressFor` SUPPRIME celui a qui on l applique. Appliquee au tireur, elle le fait '
     'taire : le natif est passe de 414 coups a zero.'),
    (r'\bsomeAmmo\b',
     '`someAmmo` repond oui pour une grenade ou un pistolet. Pour « son fusil est charge », '
     'employer `_u ammo (primaryWeapon _u) > 0`.'),
    (r'setVehicleAmmo\s+1',
     '`setVehicleAmmo 1` ne remet pas le fusil en etat de facon fiable : le banc s est eteint '
     'au 4e essai avec 9 hommes « armes » sur 9. Employer `setUnitLoadout`.'),
]

def analyser(f):
    src = pathlib.Path(f).read_text(encoding='utf-8', errors='ignore')
    lignes = src.split('\n')
    faits = []

    # ── equilibre des accolades et parentheses, hors commentaires et chaines
    net = re.sub(r'//.*', '', src)
    net = re.sub(r'/\*.*?\*/', '', net, flags=re.S)
    net = re.sub(r'"[^"\n]*"', '""', net)
    for o, c, nom in (('{', '}', 'accolades'), ('(', ')', 'parentheses'), ('[', ']', 'crochets')):
        if net.count(o) != net.count(c):
            faits.append((0, 'GRAVE', f'{nom} desequilibrees : {net.count(o)} ouvrantes, {net.count(c)} fermantes'))

    # ── UNE FONCTION HMT_ APPELEE AVANT D ETRE DEFINIE. Faute banale, et le SQF ne la
    # signale qu a l EXECUTION : 18 erreurs de script, un banc en panne, une heure. Le linteur
    # ne la connaissait pas — il l apprend maintenant, comme il apprend chacune de mes fautes.
    defs = {}
    for i, L in enumerate(lignes, 1):
        m = re.match(r'\s*(HMT_\w+)\s*=\s*\{', L)
        if m and m.group(1) not in defs:
            defs[m.group(1)] = i
    for i, L in enumerate(lignes, 1):
        c = re.sub(r'//.*', '', L)
        for m in re.finditer(r'call\s+(HMT_\w+)', c):
            n = m.group(1)
            if n in defs and defs[n] > i:
                faits.append((i, 'GRAVE',
                              f'`{n}` est appelee ici mais definie ligne {defs[n]} — '
                              f'le SQF ne le signale qu a l execution'))

    for i, L in enumerate(lignes, 1):
        # ⚠️ DEUX VERSIONS DE LA LIGNE, et ce n est pas un detail. Le controle positif a montre
        # que je neutralisais les chaines AVANT de chercher les pieges — donc `"Hit"` devenait
        # `""` et le piege le plus subtil etait invisible a mon propre filet. Les commandes se
        # cherchent sans les chaines (pour ne pas confondre du texte avec du code) ; les pieges
        # se cherchent AVEC, puisqu ils portent justement sur des noms d evenements.
        brut = re.sub(r'//.*', '', L)
        code = re.sub(r'"[^"]*"', '""', brut)

        # ── une commande unaire employee comme binaire : `_x commande`
        for c in UNAIRES:
            m = re.search(r'([\w\)\]]+)\s+' + c + r'\b', code)
            if m and m.group(1) not in DEVANT:
                faits.append((i, 'GRAVE', f'`{c}` est UNAIRE — ecrire `{c} _u`, pas `{m.group(1)} {c}`'))

        # ── `exitWith` employe comme un BRANCHEMENT, pas comme un abandon.
        # ⚠️ `if (...) exitWith { log }` est LEGITIME quand on veut vraiment abandonner — c est
        # l idiome de garde. Ce qui m a morde, c est un `exitWith` dont le corps AFFECTE une
        # variable destinee a servir PLUS TARD : la, on voulait brancher, et le script s est
        # arrete net apres avoir charge ses sept terrains. On ne signale que cette forme-la.
        if re.search(r'\bif\s*\(.*\)\s*exitWith\s*\{', code):
            bloc = src[src.index(L):][:600] if L in src else ''
            if re.search(r'\n\s*(HMT_\w+|_\w+)\s*=\s*[^=]', bloc.split('};')[0]):
                faits.append((i, 'GRAVE',
                              '`exitWith` dont le corps AFFECTE une variable : il quitte TOUT le '
                              'bloc englobant, donc l affectation ne servira jamais. '
                              'Employer `if ... then {} else {}`'))

        # ── UNE EXCEPTION SE DECLARE DANS LE CODE, PAS DANS LE LINTEUR. `// lint:ok` sur la
        # ligne dit « je sais ce que je fais et voici pourquoi » — l exception reste visible a
        # la lecture, au lieu de disparaitre dans une liste de motifs desarmes.
        if 'lint:ok' in L:
            continue
        for motif, msg in PIEGES:
            if re.search(motif, brut):
                faits.append((i, 'ATTENTION', msg))
    return faits

if __name__ == '__main__':
    cibles = sys.argv[1:] or sorted(
        str(p) for p in pathlib.Path('/mnt/data/harmattan-sandbox/arma3server/mpmissions').rglob('*.sqf')
        if 'Banc' in str(p))
    total = 0
    for f in cibles:
        faits = analyser(f)
        if faits:
            print(f"\n  {f}")
            for n, grav, msg in faits:
                print(f"    {grav:<10} ligne {n:>4}  {msg}")
            total += len(faits)
    print(f"\n  {len(cibles)} fichiers analyses · {total} signalements")
    print("  ⚠️ CE LINTEUR NE COMPREND PAS LE SQF. Il attrape les familles de fautes deja")
    print("     commises. Un silence de sa part ne prouve rien — il reduit seulement le nombre")
    print("     de fois ou l on paie quatre minutes de demarrage pour l apprendre.")
