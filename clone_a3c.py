#!/usr/bin/env python3
"""clone_a3c — SORTIR LA COMPETENCE D A3C DE L ARMA. Clonage de la GEOMETRIE, pas du plan.

CE QU ON CLONE, ET POURQUOI CELUI-LA
------------------------------------
A3C tue 3,2x plus qu un `doMove` naif (p = 0,011) en faisant entrer LE MEME nombre d hommes
(p = 1,0000). Son avantage n est donc pas « combien entrent ». Ce qui EST mesure separable,
c est sa GEOMETRIE : AUC 0,930, p = 0,0100, sur 20 manches (verdict SAIN du 15/08).
On clone donc la geometrie.

On ne clone PAS son plan d affectation : `capteur_decisions.py` le documente comme un
glouton — binomes, piece libre la plus proche de l entree — et un glouton se calcule. Pire,
sur serveur DEDIE `fnc_actionClearBuilding.sqf` saute le tri des hommes par distance a
l entree, donc A3C tourne ici SANS cette affectation et garde son 3,2x.

POURQUOI APPRENDRE CE QUI EXISTE DEJA EN SQF. Parce qu A3C ne sort pas d Arma. C est une
bibliotheque SQF : elle ne tournera jamais dans la sandbox, ni dans Isaac, ni sur un corps
humanoide. Un clone en poids tourne partout. C est exactement le transfert inter-incarnation
du programme — et c est la SEULE raison valable de le faire. Si le clone ne sert qu a
rejouer A3C dans Arma, il ne vaut rien : `call A3C_...` est deja la, gratuit et parfait.

L ENTREE DU MODELE — CE QU IL A LE DROIT DE VOIR
------------------------------------------------
Tout est en repere BATIMENT (`worldToModel`), donc invariant en translation et en cap : c est
ce qui rend le clone transposable a un autre batiment et a un autre monde.
    . sa propre position (x, y, z) et sa posture
    . les positions des 7 autres hommes, vivants ou non, triees par distance a soi
    . les positions de station du batiment (`buildingPos`), tronquees/completees a 24, triees
      par distance a soi
    . le nombre de defenseurs encore vivants (le seul scalaire d etat du camp d en face,
      celui-la meme que le corpus enregistre)
Il NE voit PAS ou sont les defenseurs : A3C non plus au moment de planifier.

LA CIBLE — L ACTE, PAS L ETAT
-----------------------------
Pour chaque homme et chaque tick, la cible est SON DEPLACEMENT AU TICK SUIVANT, exprime comme
la position de station la plus proche de la ou il sera (donc un choix parmi les positions du
batiment), plus sa posture. On apprend un CHOIX DE POSITION, ce qui est directement
executable par un `doMove` — dans Arma, dans la sandbox, ou sur un corps.

LE CRITERE DE RECEPTION, ECRIT AVANT L ENTRAINEMENT
---------------------------------------------------
Le juge existe deja et il est calibre : `juge_corpus.py`, regression logistique sur traits
geometriques, decoupage PAR MANCHE, controle de permutation. On ne le modifie pas.
  C0  CONTROLE POSITIF DU JUGE — deja acquis : A3C contre SCRIPT = AUC 0,930, p = 0,0100.
      Le juge sait separer. Rien a refaire.
  C0b CONTROLE NUL — A3C contre A3C, corpus coupe en deux moities de manches : AUC doit
      tomber dans [0,35 ; 0,65]. Si le juge separe A3C d avec lui-meme, il lit la graine et
      tout le reste est illisible.
  C1  RECEPTION — CLONE contre SCRIPT : AUC >= 0,85. Le clone doit ecrire une geometrie
      aussi distincte du temoin que son maitre.
  C2  INDISCERNABILITE — CLONE contre A3C : AUC <= 0,65. On ne doit pas distinguer l eleve
      du maitre.
C1 SANS C2 = le clone a appris quelque chose, mais pas A3C. C2 SANS C1 = les deux sont
devenus le temoin, c est-a-dire que le clone a appris a ne rien faire — et le juge le dirait
en donnant AUC ~0,5 partout. LES DEUX SONT REQUIS.

CE QUI FERAIT ECHOUER CE CLONE, ECRIT AVANT
-------------------------------------------
  · corpus sur un seul batiment -> le clone apprend CE batiment. C est pour ca que
    `recolte_a3c.py` existe ; sous 15 batiments distincts, ne pas entrainer.
  · le clone rend toujours la meme position -> il a trouve le minimum paresseux. Le controle
    d entropie ci-dessous l attrape AVANT le juge, comme le jouet attrape la sandbox.
  · les hommes morts comptes comme des exemples -> on apprend a ne pas bouger. Ils sortent.
  · C1 et C2 passes mais sur un corpus ou A3C etait deja indistinguable -> C0 l interdit.

⚠️ NON TESTE A L ECRITURE : la machine tournait les campagnes `natif`/`flanc`. Passer
`--jouet` en premier ; il entraine 200 pas sur le corpus existant et verifie que le modele
sort du minimum paresseux.
"""
import sys, os, json, math, argparse, collections

sys.path.insert(0, "/home/younes/arma3-marl")
import torch
import torch.nn as nn

CORPUS = os.environ.get("CORPUS", "/home/younes/arma3-marl/logs_train/corpus_a3c_multi.jsonl")
POIDS = os.environ.get("POIDS", "/home/younes/arma3-marl/logs_train/clone_a3c.pt")
NPOS = 24          # positions de station presentees au modele, tronquees/completees
NCAM = 7           # camarades
NBATS_MIN = 15     # sous ce nombre de batiments distincts, on n entraine pas


# ---------------------------------------------------------------- LE MODELE
class CloneA3C(nn.Module):
    """Choisit, pour un homme, LAQUELLE des positions de station rejoindre — et sa posture.

    Sortie = un score par position (donc un choix, pas une regression de coordonnees). Une
    regression rendrait la moyenne des positions, c est-a-dire le centre du batiment : le
    minimum paresseux exact que le controle d entropie surveille.
    """

    def __init__(self, npos=NPOS, ncam=NCAM):
        super().__init__()
        self.npos, self.ncam = npos, ncam
        d_soi = 4 + 1 + ncam * 4                      # soi (x,y,z,posture) + defvivants + camarades
        self.enc_soi = nn.Sequential(nn.Linear(d_soi, 128), nn.ReLU(), nn.Linear(128, 128))
        self.enc_pos = nn.Sequential(nn.Linear(4, 128), nn.ReLU(), nn.Linear(128, 128))
        self.tete = nn.Sequential(nn.Linear(256, 128), nn.ReLU(), nn.Linear(128, 1))
        self.posture = nn.Sequential(nn.Linear(128, 64), nn.ReLU(), nn.Linear(64, 3))

    def forward(self, soi, pos, masque):
        """soi (B, d_soi) · pos (B, npos, 4) · masque (B, npos) -> scores (B, npos), posture (B,3)"""
        h = self.enc_soi(soi)                                    # (B,128)
        p = self.enc_pos(pos)                                    # (B,npos,128)
        c = torch.cat([h.unsqueeze(1).expand(-1, p.shape[1], -1), p], -1)
        s = self.tete(c).squeeze(-1)
        s = s.masked_fill(masque < 0.5, -1e9)
        return s, self.posture(h)

    # ---- pilotage en jeu : rend une position monde-batiment par homme vivant
    def cibles(self, u, bpos=None):
        soi, pos, msk = traits_tick(u, bpos or self._bpos)
        s, _ = self.forward(soi, pos, msk)
        j = s.argmax(-1)
        return [pos[i, j[i], :3].tolist() for i in range(len(u))]

    def poser_batiment(self, bpos):
        self._bpos = bpos

    @staticmethod
    def charger(chemin):
        d = torch.load(chemin, map_location="cpu")
        m = CloneA3C(d["npos"], d["ncam"])
        m.load_state_dict(d["w"])
        m.eval()
        m.poser_batiment(d.get("bpos_defaut", []))
        return m


# ---------------------------------------------------------------- LES TRAITS
def traits_tick(u, bpos):
    """(u = 8 hommes [x,y,z,posture,vivant,dedans], bpos = positions de station du batiment)
    -> soi (N,d) · pos (N,NPOS,4) · masque (N,NPOS). Tout en repere batiment."""
    n = len(u)
    soi, pos, msk = [], [], []
    for i, m in enumerate(u):
        autres = sorted([x for k, x in enumerate(u) if k != i],
                        key=lambda x: (x[0] - m[0]) ** 2 + (x[1] - m[1]) ** 2)[:NCAM]
        while len(autres) < NCAM:
            autres.append([0.0, 0.0, 0.0, 0, 0, 0])
        v = [m[0], m[1], m[2], float(m[3]), 0.0]
        for a in autres:
            v += [a[0] - m[0], a[1] - m[1], a[2] - m[2], float(a[4])]
        soi.append(v)
        pp = sorted(bpos, key=lambda p: (p[0] - m[0]) ** 2 + (p[1] - m[1]) ** 2)[:NPOS]
        k = len(pp)
        ligne = [[p[0], p[1], p[2], math.dist(p[:2], m[:2])] for p in pp]
        while len(ligne) < NPOS:
            ligne.append([0.0, 0.0, 0.0, 0.0])
        pos.append(ligne)
        msk.append([1.0] * k + [0.0] * (NPOS - k))
    return (torch.tensor(soi, dtype=torch.float32),
            torch.tensor(pos, dtype=torch.float32),
            torch.tensor(msk, dtype=torch.float32))


def charge(chemin, bras="A3C"):
    """Rend (soi, pos, masque, cible_pos, cible_posture) et le compte de batiments distincts.

    Les positions de station viennent du champ `bpos` que `recolte_a3c` ecrit au tick 0 de
    chaque manche. REPLI, pour le corpus ancien qui ne l a pas : on les reconstruit depuis
    les positions visitees. Ce repli est une approximation — le clone ne voit alors que les
    stations effectivement occupees, jamais celles qu A3C a choisi d IGNORER, ce qui fait
    pourtant partie de sa decision. Il est signale a l ecran quand il sert.
    """
    par_manche = collections.defaultdict(list)
    bats = {}
    for l in open(chemin):
        d = json.loads(l)
        if d["bras"] != bras:
            continue
        par_manche[d["rid"]].append(d)
        bats[d["rid"]] = d.get("bat", "?")
    S, P, M, Y, Q = [], [], [], [], []
    replis = 0
    for rid, ticks in par_manche.items():
        ticks.sort(key=lambda d: d["t"])
        stations = next((d["bpos"] for d in ticks if d.get("bpos")), None)
        if stations is None:
            replis += 1
            stations = [list(s) for s in sorted(
                {(round(x[0] * 2) / 2, round(x[1] * 2) / 2, round(x[2] * 2) / 2)
                 for d in ticks for x in d["u"] if x[4] == 1})]
        if len(stations) < 4:
            continue
        for a, b in zip(ticks, ticks[1:]):
            soi, pos, msk = traits_tick(a["u"], stations)
            for i, (m, nxt) in enumerate(zip(a["u"], b["u"])):
                if m[4] != 1 or nxt[4] != 1:          # mort : pas un exemple
                    continue
                d2 = ((pos[i, :, 0] - nxt[0]) ** 2 + (pos[i, :, 1] - nxt[1]) ** 2
                      + (pos[i, :, 2] - nxt[2]) ** 2)
                d2 = d2.masked_fill(msk[i] < 0.5, 1e9)
                S.append(soi[i]); P.append(pos[i]); M.append(msk[i])
                Y.append(int(d2.argmin())); Q.append(min(int(nxt[3]), 2))
    if not S:
        return None
    if replis:
        print(f"  ⚠ {replis} manches sans `bpos` : stations RECONSTRUITES depuis les"
              f" positions visitees (approximation declaree, cf. docstring de charge()).")
    return (torch.stack(S), torch.stack(P), torch.stack(M),
            torch.tensor(Y), torch.tensor(Q), len(set(bats.values())))


# ---------------------------------------------------------------- L ENTRAINEMENT
def entraine(chemin, pas, dev, jouet=False):
    d = charge(chemin)
    if d is None:
        print("  corpus vide pour le bras A3C."); sys.exit(1)
    S, P, M, Y, Q, nbats = d
    print(f"  exemples {len(S)}  ·  batiments distincts {nbats}")
    if nbats < NBATS_MIN and not jouet:
        print(f"  MOINS DE {NBATS_MIN} BATIMENTS — on n entraine pas : le clone apprendrait")
        print(f"  ce batiment-la. Lancer `recolte_a3c.py` d abord.")
        sys.exit(2)
    n = len(S)
    perm = torch.randperm(n, generator=torch.Generator().manual_seed(7))
    coupe = int(n * 0.85)
    tr, te = perm[:coupe], perm[coupe:]
    m = CloneA3C().to(dev)
    opt = torch.optim.Adam(m.parameters(), 1e-3)
    S, P, M, Y, Q = S.to(dev), P.to(dev), M.to(dev), Y.to(dev), Q.to(dev)
    for it in range(pas):
        b = tr[torch.randint(0, len(tr), (256,))]
        s, q = m(S[b], P[b], M[b])
        perte = nn.functional.cross_entropy(s, Y[b]) + 0.3 * nn.functional.cross_entropy(q, Q[b])
        opt.zero_grad(); perte.backward(); opt.step()
        if it % max(1, pas // 6) == 0 or it == pas - 1:
            with torch.no_grad():
                s2, q2 = m(S[te], P[te], M[te])
                acc = (s2.argmax(-1) == Y[te]).float().mean().item()
                # CONTROLE DU MINIMUM PARESSEUX : si le clone rend toujours le meme indice,
                # l entropie de ses choix s effondre et l accuracy peut rester flatteuse.
                pr = torch.bincount(s2.argmax(-1), minlength=NPOS).float()
                pr = pr / pr.sum()
                ent = float(-(pr[pr > 0] * pr[pr > 0].log()).sum())
            print(f"    pas {it:5d}  perte {perte.item():.3f}  justesse {acc:.3f}  "
                  f"entropie des choix {ent:.2f} / {math.log(NPOS):.2f}")
    torch.save({"w": m.state_dict(), "npos": NPOS, "ncam": NCAM}, POIDS)
    print(f"  poids : {POIDS}")
    with torch.no_grad():
        s2, _ = m(S[te], P[te], M[te])
        pr = torch.bincount(s2.argmax(-1), minlength=NPOS).float(); pr = pr / pr.sum()
        ent = float(-(pr[pr > 0] * pr[pr > 0].log()).sum())
    seuil = 0.5 * math.log(NPOS)
    ok = ent > seuil
    print("\n  " + ("CONTROLE DU MINIMUM PARESSEUX PASSE (entropie %.2f > %.2f)" % (ent, seuil)
                    if ok else
                    "TOMBE — le clone rend toujours la meme position (entropie %.2f <= %.2f)."
                    % (ent, seuil) + " NE PAS LE PRESENTER AU JUGE."))
    return ok


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", default=CORPUS)
    ap.add_argument("--pas", type=int, default=6000)
    ap.add_argument("--jouet", action="store_true")
    ap.add_argument("--device", default="cuda:0")
    a = ap.parse_args()
    if a.jouet:
        a.corpus = "/home/younes/arma3-marl/logs_train/corpus_a3c_lambs.jsonl"
        a.pas = 200
        print("  JOUET — corpus existant (1 batiment), 200 pas. On ne verifie QUE la")
        print("  mecanique et le minimum paresseux, pas la competence.\n")
    sys.exit(0 if entraine(a.corpus, a.pas, a.device, a.jouet) else 1)
