"""Sonde de l etape 0b ( HMT-191 ), EN INFORMATION : les classes Arma du domaine 25 existent-elles, et dans quel
ensemble de mods ? Pour chaque arme, ses chargeurs ( magazines[] et magazineWell[] ) et la vitesse initiale de son
premier chargeur, a cote de la vitesse a la bouche que le moteur lui donne. Aucun verdict : la porte du lecteur est
fermee ( 78/79, voir Plane ).

python -m guerre.arsenal.sonde_registre"""
import json

from . import configs as CF
from monde.pays import d25_armee as A

SORTIE = "/mnt/data/hmt/arsenal/sonde_registre.json"
JEU = tuple(d for d in CF.DOSSIERS_JEU if d != "Contact")     # le jeu ne charge pas « Contact » par defaut


def registre():
    """( famille, nom du moteur, classe Arma, table attendue )."""
    out = []
    for a in A.ARMES:
        out.append(("arme", a.nom, a.arma, "CfgVehicles" if a.nom in A.COLLECTIVES else "CfgWeapons"))
    for o in A.OPTIQUES:
        if o.arma: out.append(("optique", o.nom, o.arma, "CfgWeapons"))
    for x in A.PROTECTIONS: out.append(("protection", x.nom, x.arma, "CfgWeapons"))
    for x in A.RADIOS:
        out.append(("radio", x.nom, x.arma, "CfgVehicles" if x.arma.startswith("B_RadioBag") else "CfgWeapons"))
    for v in A.VEHICULES: out.append(("vehicule", v.nom, v.arma, "CfgVehicles"))
    for sp, cl in sorted(A.ARMA_SOLDAT.items()): out.append(("soldat", A.SPECIALITES[sp], cl, "CfgVehicles"))
    return out


def chargeurs(R, arme):
    v, _ = CF.chemin(R, "CfgWeapons", arme, "magazines")
    mags = [m for m in (v or []) if isinstance(m, str)]
    puits, _ = CF.chemin(R, "CfgWeapons", arme, "magazineWell")
    for p in (puits or []):
        cls, _ = CF.chemin(R, "CfgMagazineWells", p)
        if isinstance(cls, CF.Classe):
            for _k, (_n, lst) in cls.entrees.items():
                if isinstance(lst, list): mags += [m for m in lst if isinstance(m, str) and m not in mags]
    return mags


def main():
    ensembles = {
        "jeu": CF.pbos_du_jeu(JEU),
        "jeu+CBA+CUP": CF.pbos_du_jeu(JEU) + CF.pbos_du_mod("cba") + CF.pbos_du_mod("cup_armes")
                       + CF.pbos_du_mod("cup_unites") + CF.pbos_du_mod("cup_vehicules"),
    }
    cats = {k: CF.lire_ensemble(p, journal=lambda s, k=k: print(f"  lecture {k} : {s}", flush=True))
            for k, p in ensembles.items()}
    lignes = []
    for fam, nom, cl, table in registre():
        l = {"famille": fam, "moteur": nom, "arma": cl, "table": table}
        for k, cat in cats.items():
            c, _ = CF.chemin(cat.racine, table, cl)
            ok = isinstance(c, CF.Classe) and c.base is not None
            scope, _ = CF.chemin(cat.racine, table, cl, "scope") if ok else (None, None)
            l[k] = {"existe": ok, "scope": scope, "addon": c.origine if ok else None}
        R = cats["jeu+CBA+CUP"].racine
        if fam == "arme" and table == "CfgWeapons" and l["jeu+CBA+CUP"]["existe"]:
            mags = chargeurs(R, cl)
            v0 = None
            if mags:
                v0, _ = CF.chemin(R, "CfgMagazines", mags[0], "initSpeed")
            moteur = A.ARME[nom].v0_ms
            l["chargeurs"] = mags[:6]; l["initSpeed_arma"] = v0; l["v0_moteur"] = moteur
        lignes.append(l)
        txt = "  ".join(f"{k}:{'OUI' if l[k]['existe'] else 'non'}" for k in cats)
        extra = ""
        if "chargeurs" in l:
            extra = f"  chargeur {l['chargeurs'][:1]} initSpeed {l['initSpeed_arma']} / moteur {l['v0_moteur']}"
        print(f"  {fam:10s} {nom:16s} {cl:34s} {txt}{extra}", flush=True)
    for k in cats:
        n = sum(1 for l in lignes if l[k]["existe"])
        print(f"BILAN {k} : {n}/{len(lignes)} classes du registre existent")
    json.dump(lignes, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print("FIN_SONDE_REGISTRE", flush=True)


if __name__ == "__main__":
    main()
