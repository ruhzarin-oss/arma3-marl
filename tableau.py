#!/usr/bin/env python3
"""tableau.py — UN SEUL ECRAN POUR TOUS LES BANCS. Lequel ment ?

⟨Younes, 09/08⟩ On instruit un geste a la fois sur une machine qui pourrait en instruire dix.
Trois serveurs, charge 3,5 sur 24 coeurs. Le goulot n etait pas les nuits de serveur : c est
qu on n a jamais lance plus de trois bancs. Mais dix bancs, c est dix fois plus de pannes
silencieuses a surveiller — et hier j en ai attrape cinq sur UN SEUL banc.

CE QUE CE TABLEAU FAIT, ET RIEN D AUTRE : il dit, pour chaque banc, s il est VIVANT, MUET,
EN PANNE ou TERMINE. Il ne juge aucun geste, ne rend aucun verdict, ne calcule aucun ecart
entre bras — ces lectures-la appartiennent aux depouillements, sous leurs protocoles deposes.

LES QUATRE PANNES QU IL DOIT ATTRAPER, tirees de celles qui ont reellement coute une nuit :
  1. LE JOURNAL S ARRETE — serveur mort, ou pont muet (« muet apres 20-40 min », fiche du pont)
  2. LES ERREURS DE SCRIPT — silencieuses dans Arma, fatales pour la mesure
  3. LA FUITE DE GROUPES — 144 par camp, degenerescence silencieuse au 235e accrochage
  4. LES ZEROS CREDIBLES — le banc tourne, journalise, et ne mesure plus rien. C est la
     panne la plus chere : fusils a sec au 3e essai, dix-huit zeros parfaitement formes.
"""
import re, os, glob, subprocess, time, sys

LOGS = '/mnt/data/harmattan-sandbox/logs'
MAINTENANT = time.time()

# ─────────────────────────────────────────── quels serveurs tournent, sur quel port
def ports_vivants():
    out = {}
    try:
        r = subprocess.run(['pgrep', '-a', '-f', 'arma3server_x64'],
                           capture_output=True, text=True, timeout=10).stdout
    except Exception:
        return out
    for L in r.splitlines():
        m = re.search(r'port=(\d+)', L)
        p = re.search(r'profiles=\S*?profiles(\w+)', L)
        if m:
            out[m.group(1)] = p.group(1) if p else '?'
    return out

# ─────────────────────────────────────────── ce que chaque banc journalise
BANCS = [
    # (fichier, nom, port, etiquette d essai, champ juge pour les « zeros credibles »)
    # ⚠️ `[0-9]` ET NON `\d` : grep -E est POSIX et ne connait pas `\d`. Le motif ne matchait
    # jamais, et le tableau affichait 0 essai pour un banc qui en avait 670. Deuxieme fois que
    # ce compteur ment ; ecrit ici pour qu il n y ait pas de troisieme.
    ('serverBA.out', 'n°1 bond par binome', '6002', r'HMT\|G\|LIEU\|[0-9]+', 'ARR'),
    ('serverAP.out', 'n°2 appui (etage 1)', '6012', r'HMT\|AP\|essai\|', 'delivre'),
    ('serverGC.out', 'n°3 geometre',        '6022', r'HMT\|GA\|RETENU\|', None),
    # le banc de MISSION du geste n°2, monte le 09/08 sur une copie du generateur du n°1
    ('serverA2.out', 'n°2 porte 0 du lieu', '6032', r'HMT\|G\|LIEUAP\|[0-9]+', 'ARR'),
    # le banc de MISSION du geste n°3, monte le 10/08 sur sept lieux certifies
    ('serverC3.out', 'n°3 porte 0 du lieu', '6042', r'HMT\|G\|LIEUC3\|[0-9]+', 'ARR'),
]

def lire(f, n=400000):
    """les dernieres lignes seulement : les journaux font des dizaines de Mo"""
    try:
        t = os.path.getsize(f)
        with open(f, 'rb') as h:
            h.seek(max(0, t - n))
            return h.read().decode('utf-8', errors='ignore')
    except Exception:
        return ''

def horodatage(txt):
    """derniere heure vue dans le journal, en secondes depuis minuit"""
    d = re.findall(r'^\s*(\d{1,2}):(\d{2}):(\d{2})', txt, re.M)
    if not d:
        return None
    h, m, s = d[-1]
    return int(h) * 3600 + int(m) * 60 + int(s)

vivants = ports_vivants()
lt = time.localtime(MAINTENANT)
maintenant_s = lt.tm_hour * 3600 + lt.tm_min * 60 + lt.tm_sec

print("\n  " + time.strftime('%d/%m %H:%M:%S', lt) + "   TABLEAU DES BANCS")
print("  " + "─" * 92)
print("  %-22s%-7s%-9s%-11s%-9s%-8s%s" %
      ("banc", "port", "etat", "silence", "essais", "erreurs", "alerte"))
print("  " + "─" * 92)

for fichier, nom, port, motif, champ in BANCS:
    f = os.path.join(LOGS, fichier)
    if not os.path.exists(f):
        print("  %-22s%-7s%-9s%s" % (nom, port, "absent", "aucun journal"))
        continue
    txt = lire(f)
    tail = txt[-200000:]
    proc = port in vivants
    dern = horodatage(tail)
    silence = (maintenant_s - dern) if dern is not None else None
    # ⚠️ UN ECART NEGATIF D UNE SECONDE N EST PAS UN PASSAGE DE MINUIT. Le premier jet
    # ajoutait 24 h des que le silence etait negatif : un banc qui venait d ecrire s affichait
    # « MUET depuis 86399 s ». Une fausse alerte est aussi dangereuse qu une alerte manquee —
    # elle apprend a ne plus regarder le tableau. On ne recale que les vrais passages de minuit.
    if silence is not None:
        if silence < -3600:
            silence += 86400                 # vrai passage de minuit
        elif silence < 0:
            silence = 0                      # simple decalage d horloge

    # ⚠️ ON COMPTE SUR LE FICHIER ENTIER, PAS SUR SA QUEUE. Le premier jet comptait sur les
    # derniers 400 Ko et affichait 0 essai pour un banc qui en avait 670 : les journaux font
    # des dizaines de Mo, et la queue n en voit qu une minute. Un tableau qui sous-compte est
    # pire que pas de tableau — il donne le sentiment d avoir regarde.
    def compter(mot):
        try:
            r = subprocess.run(['grep', '-c', '-E', mot, f],
                               capture_output=True, text=True, timeout=30)
            return int(r.stdout.strip() or 0)
        except Exception:
            return -1
    essais = compter(motif)
    err = compter(r'(?i)script error|Error in expression|Undefined variable')
    fini = bool(re.search(r'HMT\|\w+\|TERMINE', tail))

    # ── LES ZEROS CREDIBLES : le banc tourne et ne mesure plus rien
    alerte = ''
    if champ and champ != 'ARR':
        val = [int(x) for x in re.findall(champ + r'\|(\d+)', tail)][-8:]
        if len(val) >= 4 and sum(val[-4:]) == 0:
            alerte = 'ZEROS CREDIBLES sur les 4 derniers essais'
    if champ == 'ARR':
        # le binome : des accrochages qui s ouvrent mais dont plus personne n arrive
        ouv = len(re.findall(r'HMT\|G\|LIEU\|', tail))
        arr = len(re.findall(r'HMT\|G\|ARR\|', tail))
        if ouv >= 10 and arr == 0:
            alerte = 'plus aucune ARRIVEE sur %d accrochages' % ouv
    # ── LA FUITE DE GROUPES
    grp = re.findall(r'HMT\|G\|SANTE\|\d+\|(\d+)\|(\d+)', tail)
    if grp:
        pire = max(max(int(a), int(b)) for a, b in grp[-20:])
        if pire > 100:
            alerte = 'GROUPES a %d (limite 144)' % pire
    if err:
        alerte = '%d erreurs de script' % err

    # un banc qui a dit TERMINE est fini, que son serveur tourne encore ou non — sinon on
    # le compte « muet » alors qu il a simplement fait son travail.
    if fini:                   etat = 'termine'
    elif not proc:             etat = 'MORT'
    elif silence is None:      etat = 'vide'
    elif silence > 300:        etat = 'MUET'
    elif alerte:               etat = 'PANNE'
    else:                      etat = 'vivant'

    print("  %-22s%-7s%-9s%-11s%-9d%-8d%s" %
          (nom, port, etat,
           ("%d s" % silence) if silence is not None else "—",
           essais, err, alerte))

print("  " + "─" * 92)
print("  charge : ", end='')
try:
    print(open('/proc/loadavg').read().split()[0], "sur", os.cpu_count(), "coeurs", end='')
except Exception:
    pass
print("   ·  serveurs Arma vivants :", len(vivants),
      "(" + ", ".join(sorted(vivants)) + ")" if vivants else "")
print("""
  CE QUE CE TABLEAU NE DIT PAS : si un banc MESURE ce qu il pretend. Un banc « vivant » peut
  mesurer un endroit au lieu d une mecanique, ou compter dans la mauvaise monnaie. Cela se lit
  au depouillement, sous protocole depose — pas ici.""")
