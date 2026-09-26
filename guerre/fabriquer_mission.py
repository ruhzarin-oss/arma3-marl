"""FABRIQUER LA MISSION : le mission.sqm de GuerreIles.Malden est celui de Bohemia, lu dans le jeu installe.

On ne recopie pas la mission officielle dans le depot : on la relit dans missions_f_warlords.pbo a chaque
fabrication ( le jeu mis a jour = la mission a jour ) et on garde son empreinte. Les reglages propres a la guerre
sont dans description.ext ( Params ), jamais dans le mission.sqm : le fichier de Bohemia reste intact.

   python -m guerre.fabriquer_mission [ --pbo <missions_f_warlords.pbo> ]"""
import argparse, hashlib, os, struct

ICI = os.path.dirname(os.path.abspath(__file__))
PBO = "/mnt/c/Program Files (x86)/Steam/steamapps/common/Arma 3/Addons/missions_f_warlords.pbo"
SOURCE = "MPScenarios\\MP_Warlords_04_large.Malden\\mission.sqm"
MISSION = os.path.join(ICI, "mission", "GuerreIles.Malden")
VERS, CPRS = 0x56657273, 0x43707273


def _cstr(b, i):
    j = b.index(b"\0", i)
    return b[i:j].decode("latin-1"), j + 1


def _lzss(data, taille):
    """La compression des PBO ( LZSS de Bohemia ) : 8 drapeaux par octet, 1 = octet litteral, 0 = renvoi 12 bits + longueur 4 bits."""
    out, i = bytearray(), 0
    while len(out) < taille and i < len(data):
        drapeaux = data[i]; i += 1
        for bit in range(8):
            if len(out) >= taille: break
            if drapeaux & (1 << bit):
                out.append(data[i]); i += 1
            else:
                a, b = data[i], data[i + 1]; i += 2
                debut = len(out) - (a | ((b & 0xF0) << 4))
                for k in range((b & 0x0F) + 3):
                    out.append(out[debut + k] if debut + k >= 0 else 0x20)
    return bytes(out)


def lire_pbo(chemin):
    """{ nom : octets } de toutes les entrees d un PBO."""
    b = open(chemin, "rb").read()
    i, entrees = 0, []
    while True:
        nom, i = _cstr(b, i)
        meth, orig, _, _, taille = struct.unpack_from("<5I", b, i); i += 20
        if nom == "" and meth == VERS:
            while True:
                k, i = _cstr(b, i)
                if k == "": break
                _, i = _cstr(b, i)
            continue
        if nom == "": break
        entrees.append((nom, meth, orig, taille))
    out = {}
    for nom, meth, orig, taille in entrees:
        data = b[i:i + taille]; i += taille
        out[nom] = _lzss(data, orig) if meth == CPRS else data
    return out


def fabriquer(pbo=PBO, dest=MISSION):
    sqm = lire_pbo(pbo)[SOURCE]
    if not sqm.startswith(b"version="): raise ValueError(f"{SOURCE} n est pas un mission.sqm en texte")
    with open(os.path.join(dest, "mission.sqm"), "wb") as f: f.write(sqm)
    return hashlib.sha256(sqm).hexdigest()[:12]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--pbo", default=PBO)
    x = a.parse_args()
    print(f"mission.sqm de Bohemia ecrit dans {MISSION} ( empreinte {fabriquer(x.pbo)} )")


if __name__ == "__main__":
    main()
