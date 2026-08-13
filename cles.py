"""cles — DES IDENTIFIANTS D ACCROCHAGE QUI SURVIVENT AUX REDEMARRAGES.

⚠️ LE PIEGE, VU LE 11/08. Les identifiants d accrochage repartent a 1 a chaque redemarrage de
serveur. Mettre deux journaux bout a bout fait donc FUSIONNER SILENCIEUSEMENT des accrochages
differents qui portent le meme numero — et un cumul naif rendait 9575 accrochages la ou
l archive en portait 3986.

C est la meme famille que tout le reste de la journee : un compteur qui ne sait pas qu il a
ete remis a zero.

LA CLE : (fichier, segment, id). Le SEGMENT s incremente des qu un identifiant REVIENT EN
ARRIERE — c est la signature d une remise a zero, et elle se lit sans rien changer aux bancs
en vol. Aucune journalisation supplementaire n est necessaire, donc aucune campagne n est
interrompue pour ca.
"""


def corpus_sain(fichiers):
    """⚠️ LA LIMITE DU SEGMENTEUR, TROUVEE LE 12/08 : il separe par FICHIER, donc il ne voit
    PAS le meme journal presente deux fois sous deux noms. C est arrive — l archive
    `pause_2026-08-11/serverBA.out` et la rotation `serverBA_215849.out` etaient le meme
    journal (3992 lignes LIEU, 54 563 lignes BOND, a l identique), et un glob `serverBA*` les
    a ramasses tous les deux. 3992 accrochages comptes DEUX FOIS.
    Ici le verdict n a pas bouge — l intervalle se calcule sur l ecart des huit couloirs, pas
    sur le nombre d accrochages, et dupliquer a l identique ne deplace aucun pourcentage. Mais
    c est une chance, pas une propriete : sur une grandeur qui se moyenne par accrochage, le
    doublon aurait retreci l intervalle et pu ouvrir une porte fermee.

    REGLE : un corpus se declare par LISTE EXPLICITE, jamais par glob. Et on le passe ici.
    Rend (liste_retenue, doublons) ; refuse silencieusement rien, nomme tout."""
    import hashlib
    vus, garde, doublons = {}, [], []
    for f in fichiers:
        try:
            h = hashlib.sha256()
            with open(f, "rb") as fh:
                for bloc in iter(lambda: fh.read(1 << 20), b""):
                    h.update(bloc)
            e = h.hexdigest()
        except OSError:
            continue
        if e in vus:
            doublons.append((f, vus[e]))
        else:
            vus[e] = f; garde.append(f)
    return garde, doublons


def empreinte_par_canal(fichiers, canaux=("LIEU", "BOND", "SANTE", "fin")):
    """Deux fichiers peuvent differer d un octet et porter LA MEME campagne — c est le cas
    reel du 12/08. On compare donc aussi le COMPTE PAR CANAL, qui ne ment pas."""
    import re
    out = {}
    for f in fichiers:
        c = {}
        try:
            texte = open(f, "rb").read()
        except OSError:
            continue
        for k in canaux:
            c[k] = texte.count(("HMT|G|%s|" % k).encode())
        out[f] = tuple(c[k] for k in canaux)
    jumeaux = {}
    for f, sig in out.items():
        jumeaux.setdefault(sig, []).append(f)
    return {s: v for s, v in jumeaux.items() if len(v) > 1 and any(s)}


class Segmenteur:
    """Rend une cle unique par accrochage, meme a travers les redemarrages."""

    def __init__(self):
        self.fichier = None
        self.segment = 0
        self.dernier = -1

    def cle_passive(self, fichier, ident):
        """Pour le flux SUIVEUR (les lignes de fin). Il ne fait PAS avancer le segment.

        ⚠️ FAUTE PAYEE IMMEDIATEMENT. Premiere version : un seul segmenteur pour les DEUX
        flux, debut et fin. Or les `debut` arrivent en ordre croissant mais les `fin`
        arrivent DANS LE DESORDRE — un accrochage ouvert tot peut se fermer tard. Chaque
        `fin` qui reculait faisait donc croire a un redemarrage, le segment s incrementait,
        et l appariement debut/fin se brisait : 1057 accrochages lus comme 11.
        Le flux MAITRE est celui des `debut`, monotone par construction. Les `fin` se
        contentent du segment courant — et c est juste, puisqu un redemarrage tue tous les
        accrochages ouverts : aucune fin ne peut appartenir a un segment anterieur.
        """
        if fichier != self.fichier:
            self.fichier, self.segment, self.dernier = fichier, 0, -1
        return (fichier, self.segment, ident)

    def cle(self, fichier, ident):
        if fichier != self.fichier:
            self.fichier, self.segment, self.dernier = fichier, 0, -1
        # un identifiant qui recule = le serveur a redemarre dans le meme fichier
        if ident < self.dernier:
            self.segment += 1
        self.dernier = ident
        return (fichier, self.segment, ident)


def controle_positif():
    """⚠️ Ce controle NE VOYAIT PAS la faute des deux flux : il ne testait qu un flux.
    On y ajoute donc le cas qui a mordu — des fins dans le desordre ne doivent RIEN couper."""
    """Le segmenteur doit SEPARER deux runs colles bout a bout, et NE PAS separer un run sain."""
    s = Segmenteur()
    sain = [s.cle("a", i) for i in (1, 2, 3, 4, 5)]
    ok1 = len(set(sain)) == 5 and len({c[1] for c in sain}) == 1
    s = Segmenteur()
    colle = [s.cle("a", i) for i in (1, 2, 3, 1, 2, 3)]
    ok2 = len(set(colle)) == 6
    s = Segmenteur()
    deux = [s.cle("a", 1), s.cle("b", 1)]
    ok3 = len(set(deux)) == 2
    print(f"    {'PASSE' if ok1 else 'TOMBE'}  un run sain n est PAS coupe")
    print(f"    {'PASSE' if ok2 else 'TOMBE'}  deux runs colles sont SEPARES (6 cles pour 1,2,3,1,2,3)")
    print(f"    {'PASSE' if ok3 else 'TOMBE'}  deux fichiers ne se melangent pas")
    # le cas qui a mordu : des FINS dans le desordre ne doivent pas incrementer le segment
    s = Segmenteur()
    for i in (1, 2, 3, 4, 5):
        s.cle("a", i)
    fins = [s.cle_passive("a", i) for i in (3, 1, 5, 2, 4)]
    ok4 = len({c[1] for c in fins}) == 1 and len(set(fins)) == 5
    print(f"    {'PASSE' if ok4 else 'TOMBE'}  des fins DANS LE DESORDRE ne coupent rien")
    return ok1 and ok2 and ok3 and ok4


if __name__ == "__main__":
    print("\n  CONTROLE POSITIF DU SEGMENTEUR")
    print("  " + "-" * 60)
    import sys
    sys.exit(0 if controle_positif() else 1)
