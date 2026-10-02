"""Porte du lecteur hors ligne des configs d Arma ( HMT-191, etape 0a ). Criteres ecrits avant la mesure ( Plane ).

Premier verdict ( 02/10, 20 h 20 ) : REFUSEE, L1 24/37 : le lecteur ne lisait que le config.bin de la racine des PBO,
et le releve du 03/09 avait ACE charge ( le mode « ACE_Burst_far » de canal 2 ). Rejugement, criteres amendes AVANT la
nouvelle mesure :

L1' sur la fusion du jeu de base, des DLC, de CBA_A3 et d ACE, les 37 sondes de canal 1 ET les sondes de configuration
    de canal 2 ( modes du MX et leur ordre, les courbes de chaque mode, CfgAmmo audibleFire / visibleFire / hit /
    typicalSpeed / indirectHitRange ) rendent la meme existence et la meme valeur ( 1e-5 en relatif ) ; une seule
    fausse et la porte reste REFUSEE. Canal 2 est un controle NEUF ( valeurs jamais lues avant cette mesure ).
L2  au moins 5 valeurs presentes de canal 1 lues dans une classe PARENTE de la classe sondee.
L3  0 echec de lecture, compte par config.bin ; les dossiers a config.cpp seul sont comptes et declares.
L4  sur le jeu de base et ses DLC : entre 1 000 et 30 000 classes CfgVehicles, entre 500 et 20 000 CfgWeapons.
Information : les memes sondes sur la fusion SANS mods ( ce qu ACE change ).

python -m guerre.arsenal.porte_lecteur"""
import json
import os
import sys

from . import configs as CF

REFERENCE = "/home/younes/arma3-marl/config_arma3_canal.json"
REFERENCE2 = "/home/younes/arma3-marl/config_arma3_canal2.json"
SORTIE = "/mnt/data/hmt/arsenal/porte_lecteur.json"
SOLDAT, MUN, MX = "B_Soldier_F", "B_65x39_Caseless", "arifle_MX_F"
CLES_COURBE = ("minRange", "minRangeProbab", "midRange", "midRangeProbab", "maxRange", "maxRangeProbab")
EXCLUS2 = ("boundingBoxReal", "sizeOf", "rayon_sphere_m")      # des mesures de jeu, pas des lectures de config


def chemin_de(etiquette):
    """Le chemin configFile >> ... de chaque sonde de canal 1 ( lire_config_arma.SONDES )."""
    if etiquette == "TEMOIN+ hit munition": return ("CfgAmmo", MUN, "hit")
    if etiquette == "TEMOIN- chemin bidon": return ("CfgVehicles", SOLDAT, "ceci_nexiste_pas_du_tout")
    soldat = {"sensitivity": "sensitivity", "sensitivityEar": "sensitivityEar", "camouflage": "camouflage",
              "audible": "audible", "radius (CfgVehicles)": "radius", "armor": "armor",
              "armorStructural": "armorStructural", "threat/accuracy": "accuracy"}
    if etiquette in soldat: return ("CfgVehicles", SOLDAT, soldat[etiquette])
    for suffixe, fin in ((" audibleFire (arme)", ("audibleFire",)), (" audibleFire (Single)", ("Single", "audibleFire")),
                         (" visibleFire (arme)", ("visibleFire",))):
        if etiquette.endswith(suffixe): return ("CfgWeapons", etiquette[: -len(suffixe)]) + fin
    if etiquette.startswith("CfgAmmo "): return ("CfgAmmo", MUN, etiquette.split()[1])
    if etiquette.startswith("MX Single "): return ("CfgWeapons", MX, "Single", etiquette.split()[2])
    if etiquette.startswith("MX FullAuto "): return ("CfgWeapons", MX, "FullAuto", etiquette.split()[2])
    raise KeyError(etiquette)


def egal(a, b):
    return abs(a - b) <= max(1e-6, 1e-5 * abs(b))


def sondes_canal1():
    ref = json.load(open(REFERENCE))
    return [("c1 " + k, chemin_de(k), bool(v["existe"]), float(v["valeur"]), "isNumber")
            for k, v in ref.items() if isinstance(v, dict) and "existe" in v]


def sondes_canal2():
    """( etiquette, chemin, existe attendu, valeur attendue, genre ). Les courbes des modes ne gardent que getNumber
    ( 0 si absent ) : on les compare a getNumber. La liste des modes se compare a getArray, ordre compris."""
    ref = json.load(open(REFERENCE2))
    out = [("c2 modes", ("CfgWeapons", MX, "modes"), True, list(ref["modes"]), "getArray")]
    for md in ref["modes"]:
        for k in CLES_COURBE:
            ch = ("CfgWeapons", MX, k) if md == "this" else ("CfgWeapons", MX, md, k)
            out.append((f"c2 {md} {k}", ch, None, float(ref[md][k]), "getNumber"))
    for k, v in ref.items():
        if k.startswith("CfgAmmo_"):
            out.append(("c2 " + k, ("CfgAmmo", MUN, k[len("CfgAmmo_"):]), bool(v["existe"]), float(v["valeur"]),
                        "isNumber"))
    vus = {"modes"} | set(ref["modes"]) | {k for k in ref if k.startswith("CfgAmmo_")} | set(EXCLUS2)
    reste = [k for k in ref if k not in vus]
    if reste: raise ValueError(f"sondes de canal 2 non rangees : {reste}")
    return out


def juger(cat, sondes):
    R = cat.racine; lignes = []; fausses = 0; herite = 0
    for etiq, ch, ex_att, v_att, genre in sondes:
        v, defn = CF.chemin(R, *ch)
        sonde_c, _ = CF.chemin(R, *ch[:-1])
        if genre == "getArray":
            lu = ["VIDE" if x == "" else x for x in v] if isinstance(v, list) else None
            ok = lu == v_att; existe = lu is not None
        elif genre == "getNumber":
            existe = CF.est_nombre(v); lu = float(v) if existe else 0.0
            ok = egal(lu, v_att)
        else:
            existe = CF.est_nombre(v); lu = float(v) if existe else None
            ok = (existe == ex_att) and (not existe or egal(lu, v_att))
        par_heritage = bool(existe and genre == "isNumber" and etiq.startswith("c1") and defn is not None
                            and defn is not sonde_c)
        herite += par_heritage; fausses += not ok
        lignes.append({"sonde": etiq, "chemin": " >> ".join(ch), "attendu": [ex_att, v_att], "lu": [existe, lu],
                       "ok": ok, "defini_dans": None if defn is None else defn.nom,
                       "addon": None if defn is None else defn.origine, "par_heritage": par_heritage})
    return lignes, fausses, herite


def main():
    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    sondes = sondes_canal1() + sondes_canal2()
    n1 = sum(1 for s in sondes if s[0].startswith("c1")); n2 = len(sondes) - n1
    print(f"PORTE DU LECTEUR ( rejugement ) : {n1} sondes de canal 1, {n2} de canal 2", flush=True)
    jeu = CF.pbos_du_jeu()
    ebo = sum(1 for d in CF.DOSSIERS_JEU + ("WS",) for dp, _dn, fn in os.walk(os.path.join(CF.ARMA, d))
              for f in fn if f.lower().endswith(".ebo"))
    cat_ace = CF.lire_ensemble(jeu + CF.pbos_du_mod("cba") + CF.pbos_du_mod("ace"),
                               journal=lambda s: print("  lecture jeu + CBA + ACE :", s, flush=True))
    cat_nu = CF.lire_ensemble(jeu, journal=lambda s: print("  lecture jeu seul :", s, flush=True))
    lignes, fausses, herite = juger(cat_ace, sondes)
    lignes_nu, fausses_nu, _h = juger(cat_nu, sondes)
    for l, ln in zip(lignes, lignes_nu):
        print(f"  {'OK ' if l['ok'] else 'FAUX'} {l['sonde']:40s} attendu {str(l['attendu'][1])[:60]:<14} "
              f"lu {str(l['lu'][1])[:60]:<14} {'herite de ' + str(l['defini_dans']) if l['par_heritage'] else ''}"
              f"{'' if ln['ok'] == l['ok'] else '   [sans mods : ' + ('OK' if ln['ok'] else 'FAUX') + ']'}",
              flush=True)
    nv, nw = len(cat_nu.noms("CfgVehicles")), len(cat_nu.noms("CfgWeapons"))
    L1 = fausses == 0
    L2 = herite >= 5
    L3 = len(cat_ace.echecs) == 0 and len(cat_nu.echecs) == 0
    L4 = 1000 <= nv <= 30000 and 500 <= nw <= 20000
    print(f"L1' sondes justes {len(sondes) - fausses}/{len(sondes)} : {'OUI' if L1 else 'NON'}  "
          f"(information, sans mods : {len(sondes) - fausses_nu}/{len(sondes)})")
    print(f"L2 valeurs de canal 1 lues par heritage {herite} (>= 5) : {'OUI' if L2 else 'NON'}")
    for nom, c in (("jeu + CBA + ACE", cat_ace), ("jeu seul", cat_nu)):
        print(f"L3 {nom} : PBO {c.pbos}, config.bin {c.avec_bin}, dossiers a config.cpp seul {len(c.cpp_seul)}, "
              f"PBO sans config {c.sans_config}, echecs {len(c.echecs)}")
        for p, e in c.echecs[:10]: print("     echec", p, e)
    print(f"L3 : {'OUI' if L3 else 'NON'}")
    print(f"L4 jeu seul : CfgVehicles {nv}, CfgWeapons {nw} : {'OUI' if L4 else 'NON'}")
    print(f"info : jeu seul CfgMagazines {len(cat_nu.noms('CfgMagazines'))}, CfgAmmo {len(cat_nu.noms('CfgAmmo'))}, "
          f"{cat_nu.classes} classes ; avec CBA et ACE {cat_ace.classes} classes ; {ebo} .ebo chiffres non lus ; "
          f"{cat_nu.duree_s + cat_ace.duree_s:.0f} s")
    verdict = "FRANCHIE" if (L1 and L2 and L3 and L4) else "REFUSEE"
    json.dump({"verdict": verdict, "L1": L1, "L2": L2, "L3": L3, "L4": L4, "sondes": lignes, "sans_mods": lignes_nu,
               "jeu_ace": {"pbos": cat_ace.pbos, "config_bin": cat_ace.avec_bin, "cpp_seuls": cat_ace.cpp_seul,
                           "echecs": cat_ace.echecs, "classes": cat_ace.classes},
               "jeu": {"pbos": cat_nu.pbos, "config_bin": cat_nu.avec_bin, "cpp_seuls": cat_nu.cpp_seul,
                       "echecs": cat_nu.echecs, "classes": cat_nu.classes, "CfgVehicles": nv, "CfgWeapons": nw},
               "ebo": ebo}, open(SORTIE, "w"), indent=1, ensure_ascii=False, default=str)
    print(f"PORTE DU LECTEUR : {verdict}")
    print("FIN_PORTE_LECTEUR", flush=True)
    return 0 if verdict == "FRANCHIE" else 1


if __name__ == "__main__":
    sys.exit(main())
