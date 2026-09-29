"""La cause de chaque perte, lue dans le journal des messages de CMO ( HMT_journal ) et non estimée : « has been
destroyed! » après un coup au but, ou « has run out of fuel and crashed! ». 29/09 : l'estimation par la distance ( un
ennemi à moins de 150 km ) comptait comme « au combat » 18 avions de Malden tombés à sec.

    .venv312/bin/python cmo/causes_cmo.py <journal hmt_messages_*.txt>
"""
import collections
import json
import re
import sys

# Le camp entre crochets peut porter un tiret ou une espace : 29/09, « [Russie-Chine] » échappait à \w+ et les 11 pertes
# russes de la guerre des blocs manquaient au bilan.
_DETRUIT = re.compile(r"\[([^\]]+)\] HMT-(\d+) \([^)]*\) has been destroyed!")
_SEC = re.compile(r"\[([^\]]+)\] HMT-(\d+) \([^)]*\) has run out of fuel and crashed!")
_COUP = re.compile(r"Weapon: ([^#]+?) #\d+ is attacking HMT-(\d+)")


def causes(texte):
    """{ numéro CMO : « combat » | « carburant » | « autre » } et les armes des coups au but."""
    sec = {int(k) for _, k in _SEC.findall(texte)}
    touches = {int(k) for _, k in _COUP.findall(texte)}
    out = {}
    for _, k in _DETRUIT.findall(texte):
        k = int(k)
        out[k] = "carburant" if k in sec else "combat" if k in touches else "autre"
    for k in sec:
        out.setdefault(k, "carburant")
    armes = collections.Counter(a.strip() for a, _ in _COUP.findall(texte))
    return out, dict(armes)


def bilan(texte, decalage=10_000_000):
    c, armes = causes(texte)
    par = collections.defaultdict(collections.Counter)
    for k, cause in c.items():
        par[{1: "EAST", 2: "WEST"}.get(k // decalage, "?")][cause] += 1
    return {"pertes": {camp: dict(v) for camp, v in par.items()}, "armes_au_but": armes}


if __name__ == "__main__":
    print(json.dumps(bilan(open(sys.argv[1], errors="ignore").read()), ensure_ascii=False, indent=1))
