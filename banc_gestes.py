#!/usr/bin/env python3
"""banc_gestes — ETAPE 1, LE FILTRE GRATUIT DU CAHIER.

Regle du CAHIER_REPERTOIRE_GESTES.md : « un geste dont le PROFESSEUR ne bat pas son temoin ne
s enseigne pas ». Le temoin, nomme une fois pour toutes ⟨Fable⟩ : L ORDRE NAIF LE PLUS BETE
QUI VISE LE MEME POINT FINAL. Ici il s obtient en ETEIGNANT le levier du geste dans
`shamal_action` — la version naive de sa propre intention, tout le reste tenu constant.

⭐ LA SECONDE LAME, que l echec de la distillation vient de payer ⟨Fable⟩ :
   AVANT d entrainer, mesurer le taux de DESACCORD professeur <-> temoin.
   Sans desaccord frequent, il n y a PAS DE LECON. D1 suivait un signal redondant a 88 %
   avec le navigateur, et c etait mesurable avant le premier gradient.

Rien n est entraine ici. On deroule des DOCTRINES SCRIPTEES, on compte, on filtre.
"""
import sys, json, argparse, torch
sys.path.insert(0, "/home/younes/arma3-marl")
import boucle as B
from banc_raster import jouer_phi2
from shamal_teacher import shamal_action

DEV = "cuda:0"
# geste -> (levier, valeur du PROFESSEUR, valeur du TEMOIN, grandeur jugee, numero au cahier)
GESTES = {
    "bond_binome":   dict(levier="bounding", prof=True,  temoin=False, cahier=1,
                          quoi="Bond par binome — l un progresse, l autre couvre"),
    "debordement":   dict(levier="flank",    prof=True,  temoin=False, cahier=5,
                          quoi="Debordement par le flanc — deux pointes qui convergent"),
    "decrochage":    dict(levier="retreat",  prof=True,  temoin=False, cahier=6,
                          quoi="Decrochage sous le feu — rompre le contact si deborde"),
    "posture_basse": dict(levier="drop_to",  prof=2,     temoin=1,     cahier=4,
                          quoi="Baisser la posture — couche (2) plutot qu accroupi (1)"),
}


def doctrine(**kw):
    def f(e, t):
        return shamal_action(e, **kw)
    return f


def jouer(fn, graines, n=256):
    pr, tn, dh, sv, act = [], [], [], [], []
    for g in graines:
        e = B.monde(n, g)
        st, *_ = jouer_phi2(e, lambda o, t, _e=e: (fn(_e, t), None, None), w_phi=0.0)
        pr.append(st["prise"]); tn.append(st["metres_tenus"])
        dh.append(st["danger_homme_pas"]); sv.append(st["survivants"])
    m = lambda v: sum(v) / len(v)
    return dict(prise=m(pr), tenus=m(tn), danger=m(dh), survivants=m(sv), par_graine=pr)


def desaccord(kw_prof, kw_tem, graines, n=256):
    """LA SECONDE LAME : sur combien de pas le professeur et son temoin different-ils ?
    On deroule le PROFESSEUR (c est sa distribution d etats qui compte) et on demande au
    temoin ce qu il aurait fait au meme instant."""
    diff = tot = 0
    for g in graines[:3]:
        e = B.monde(n, g); e.reset()
        fini = torch.zeros(e.N, dtype=torch.bool, device=e.dev)
        for t in range(B.PAS):
            a_p = shamal_action(e, **kw_prof); a_t = shamal_action(e, **kw_tem)
            viv = e._aalive() & ~fini.unsqueeze(1)
            diff += int(((a_p != a_t) & viv).sum()); tot += int(viv.sum())
            o, _, done, _ = e.step(a_p, auto_reset=False)
            fini |= done.bool()
            if bool(fini.all()): break
    return 100.0 * diff / max(tot, 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=256)
    ap.add_argument("--sortie", default="/mnt/data/gestes.json")
    a = ap.parse_args()
    G = B.GRAINES_TEST
    print("=" * 96)
    print(" BANC DES GESTES — le filtre GRATUIT du cahier, avant tout entrainement")
    print(" porte : le professeur bat son temoin d au moins 5,0 points sur la PRISE")
    print(" seconde lame : desaccord professeur<->temoin >= 5 % des pas, sinon PAS DE LECON")
    print("=" * 96, flush=True)

    base = dict(drop_to=1, flank=True, retreat=True, mode="assault", bounding=True)
    print("\n  doctrines de reference du depot, memes graines :", flush=True)
    for nom, f in (("frontal", lambda e, t: B.frontal(e, t)), ("flanc", lambda e, t: B.flanc(e, t))):
        r = jouer(f, G, a.n)
        print("    %-10s prise %5.1f %%  tenus %6.1f m  survivants %.2f" % (nom, r["prise"], r["tenus"], r["survivants"]), flush=True)
    r0 = jouer(doctrine(**base), G, a.n)
    print("    %-10s prise %5.1f %%  tenus %6.1f m  survivants %.2f  <- SHAMAL complet"
          % ("shamal", r0["prise"], r0["tenus"], r0["survivants"]), flush=True)

    res = {}
    print("\n  %-14s %-9s %8s %8s %8s %10s %s" % ("geste", "levier", "prof", "temoin", "ecart", "desaccord", "verdict"), flush=True)
    for nom, d in GESTES.items():
        kp = dict(base); kp[d["levier"]] = d["prof"]
        kt = dict(base); kt[d["levier"]] = d["temoin"]
        rp = jouer(doctrine(**kp), G, a.n); rt = jouer(doctrine(**kt), G, a.n)
        des = desaccord(kp, kt, G, a.n)
        ec = rp["prise"] - rt["prise"]
        if des < 5.0:
            v = "PAS DE LECON (desaccord trop faible)"
        elif ec >= 5.0:
            v = "PASSE — s enseigne"
        elif ec <= -5.0:
            v = "NUIT — a retirer du repertoire"
        else:
            v = "ne bat pas son temoin — NE S ENSEIGNE PAS"
        print("  %-14s %-9s %7.1f %% %7.1f %% %+7.1f %9.1f %%  %s" % (nom, d["levier"], rp["prise"], rt["prise"], ec, des, v), flush=True)
        res[nom] = dict(cahier=d["cahier"], quoi=d["quoi"], levier=d["levier"],
                        prof=rp, temoin=rt, ecart=ec, desaccord=des, verdict=v)
        json.dump(res, open(a.sortie, "w"), indent=1)
    passent = [k for k, v in res.items() if v["verdict"].startswith("PASSE")]
    print("\n  GESTES QUI S ENSEIGNENT : %s" % (", ".join(passent) if passent else "AUCUN"))
    if not passent:
        print("  ⚠️ Le cahier a ecrit ce cas d avance : « si aucun geste ne passe sa porte, ce ne")
        print("     sont pas les gestes qui manquent — c est le RL ou la tache qu il faut regarder,")
        print("     PAS ajouter un onzieme geste. »")
