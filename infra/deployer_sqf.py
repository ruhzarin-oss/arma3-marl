#!/usr/bin/env python3
"""BRIQUE 3 — DEPLOIEMENT DU SQF DEPUIS GIT.

Le SQF ecrit dans `mpmissions/` vit HORS du depot : sept bancs de certification y sont
restes non versionnes toute une session (03/08). Desormais la source est dans le depot,
et `mpmissions/` n est plus qu une CIBLE. **On n edite plus jamais la-bas.**

Le script fait trois choses et rien d autre :
  1. PURGE les commentaires — `call compile` ne retire pas les `//`, et un seul fait
     echouer le bloc EN SILENCE (paye deux fois le 02/09) ;
  2. calcule l EMPREINTE de ce qui est reellement deploye, pour que le depot du matin
     puisse dire quel code a produit les chiffres ;
  3. copie, et refuse si la cible a ete editee a la main depuis le dernier deploiement.

⚠️ Il ne purge PAS les `//` a l interieur d une chaine : une URL ou un chemin y survit.
"""
import sys, os, re, json, hashlib, shutil, datetime

DEPOT = "/home/younes/arma3-marl/sqf"
MISSIONS = "/mnt/data/harmattan-sandbox/arma3server/mpmissions"
REGISTRE = "/home/younes/arma3-marl/infra/deploiements.json"


def purger(txt):
    """Retire `//...` et `/* ... */` en respectant les chaines "..." de SQF."""
    out = []
    i, n = 0, len(txt)
    dans_chaine = False
    while i < n:
        c = txt[i]
        if dans_chaine:
            out.append(c)
            if c == '"':
                dans_chaine = (i + 1 < n and txt[i + 1] == '"')   # "" = guillemet echappe
                if dans_chaine:
                    out.append(txt[i + 1]); i += 1
            i += 1
            continue
        if c == '"':
            dans_chaine = True; out.append(c); i += 1; continue
        if c == "/" and i + 1 < n and txt[i + 1] == "/":
            while i < n and txt[i] != "\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and txt[i + 1] == "*":
            j = txt.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        out.append(c); i += 1
    return "".join(out)


def sha(txt):
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()[:16]


def registre():
    try:
        return json.load(open(REGISTRE))
    except Exception:
        return {}


def deployer(nom, mission, force=False):
    src = "%s/%s.sqf" % (DEPOT, nom)
    if not os.path.exists(src):
        sys.exit("  source absente du depot : %s" % src)
    dst_dir = "%s/%s" % (MISSIONS, mission)
    if not os.path.isdir(dst_dir):
        sys.exit("  mission absente : %s" % dst_dir)
    dst = "%s/%s.sqf" % (dst_dir, nom)

    reg = registre()
    cle = "%s/%s" % (mission, nom)
    if os.path.exists(dst) and cle in reg and not force:
        actuel = sha(open(dst, encoding="utf-8").read())
        if actuel != reg[cle]["empreinte_deployee"]:
            sys.exit("  ⛔ LA CIBLE A ETE EDITEE A LA MAIN depuis le dernier deploiement.\n"
                     "     %s\n     attendu %s, trouve %s\n"
                     "     Rapatrier la modification dans %s, ou relancer avec --force."
                     % (dst, reg[cle]["empreinte_deployee"], actuel, src))

    brut = open(src, encoding="utf-8").read()
    net = purger(brut)
    if "//" in net:
        print("  ⚠ il reste des `//` apres purge (dans une chaine ?) — verifier", flush=True)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, "w", encoding="utf-8").write(net)
    reg[cle] = {"source": src, "empreinte_source": sha(brut), "empreinte_deployee": sha(net),
                "quand": datetime.datetime.now().isoformat(timespec="seconds"),
                "lignes_source": brut.count("\n") + 1, "lignes_deployees": net.count("\n") + 1}
    os.makedirs(os.path.dirname(REGISTRE), exist_ok=True)
    json.dump(reg, open(REGISTRE, "w"), indent=1, ensure_ascii=False)
    print("  deploye %s -> %s" % (src, dst))
    print("  empreinte source %s · deployee %s" % (reg[cle]["empreinte_source"], reg[cle]["empreinte_deployee"]))
    return reg[cle]["empreinte_deployee"]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        ex = 'private _a = 1; // commentaire\nprivate _u = "http://x//y"; /* bloc */ private _b = 2;\n'
        net = purger(ex)
        assert "commentaire" not in net and "bloc" not in net, net
        assert "http://x//y" in net, "une URL dans une chaine a ete mutilee : %r" % net
        print("  purge : commentaires retires, chaines intactes ✔")
        print("  registre :", REGISTRE)
        sys.exit(0)
    if len(sys.argv) < 3:
        sys.exit("  usage : deployer_sqf.py <nom> <Mission.Altis> [--force]")
    deployer(sys.argv[1], sys.argv[2], "--force" in sys.argv)
