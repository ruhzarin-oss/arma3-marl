"""PORTE DE L AGENT CODEUR ( 26/09 ) : le bac a sable refuse et coupe ce qu il doit, et un gouvernement en code
change vraiment le pays.
  A1  `import os` refuse avant execution ; `x.__class__` refuse ;
  A2  une boucle sans fin est coupee en une seconde : ce jour-la est joue par les regles et compte ;
  A3  une action hors bornes est refusee par le domaine 6 et comptee ;
  A4  controle positif : un gouvernement qui ne fait rien et les regles ne donnent pas le meme pays ;
  A5  un code qui recopie les regles donne EXACTEMENT le pays des regles ( le branchement ne change rien d autre ).
   python -m monde.porte_agent_codeur"""
import sys
from . import agent_codeur as AC
from .pays import d06_etat as ET

JOURS, ECH = 6, 4.0


def main():
    ok = True
    def dire(passe, texte):
        nonlocal ok; ok &= passe; print(f"{'PASSE ' if passe else 'ECHOUE'} {texte}", flush=True)
    refus = []
    for src in ("import os\ndef gouverner(b, memoire):\n    return []\n", "def gouverner(b, memoire):\n    return b.__class__\n"):
        try: AC.CerveauCode(src); refus.append(False)
        except AC.CodeRefuse: refus.append(True)
    dire(all(refus), f"A1 import et dunder refuses avant execution {refus}")
    boucle = "def gouverner(b, memoire):\n    while True:\n        pass\n"
    m = AC.evaluer(boucle, "Malden", ECH, 3)
    dire(m["jours_joues_par_les_regles"] >= 3, f"A2 boucle sans fin coupee : {m['jours_joues_par_les_regles']} jours joues par les regles sur 3")
    hors = "def gouverner(b, memoire):\n    return [{'type': 'fixer_is', 'valeur': 0.9}]\n"
    m = AC.evaluer(hors, "Malden", ECH, 3)
    dire(m["refus"] >= 3 and any("hors" in r for r in m["raisons_refus"]), f"A3 action hors bornes refusee : {m['refus']} refus {m['raisons_refus']}")
    regles = AC.evaluer(AC.REGLES, "Malden", ECH, JOURS)
    rien = AC.evaluer(AC.RIEN, "Malden", ECH, JOURS)
    dire(regles["faim_par_jour"] != rien["faim_par_jour"] or regles["caisse_etat"] != rien["caisse_etat"],
         f"A4 rien != regles ( caisse de l Etat {rien['caisse_etat']} contre {regles['caisse_etat']} )")
    copie = "def gouverner(b, memoire):\n    return REGLES(b)\n"
    AC.BUILTINS["REGLES"] = ET.decider_regles_etat          # le temoin exact, expose au seul code de cette porte
    try: m = AC.evaluer(copie, "Malden", ECH, JOURS)
    finally: AC.BUILTINS.pop("REGLES", None)
    dire(m["faim_par_jour"] == regles["faim_par_jour"] and m["caisse_etat"] == regles["caisse_etat"] and m["morts_nets"] == regles["morts_nets"],
         f"A5 le code qui recopie les regles = les regles ( caisse {m['caisse_etat']} / {regles['caisse_etat']} )")
    # A6 : un archipel gouverne par du code ( option gouvernement de l Archipel, comme la nuit ) tourne, tient sa
    # conservation et journalise que c est le code qui decide
    from .archipel import Archipel
    code = "def gouverner(b, memoire):\n    memoire['n'] = memoire.get('n', 0) + 1\n    return [{'type': 'rien'}]\n"
    arc = Archipel(iles=("Malden", "Tanoa"), echelle=2.0, ouvert=True, parallele=True, gouvernement={"Malden": code})
    arc.jours(2)
    e = arc._envoyer_a_tous(lambda n: ("etat",))
    tenue = all(arc.commande(n, "tenue")[0] for n in ("Malden", "Tanoa"))
    arc.fermer()
    dire(tenue and str(e["Malden"]["gouvernement"]["cerveau"]).startswith("code:") and e["Tanoa"]["gouvernement"]["cerveau"] == "regles",
         f"A6 archipel : Malden gouverne par {e['Malden']['gouvernement']['cerveau']}, Tanoa par {e['Tanoa']['gouvernement']['cerveau']}, conservation {tenue}")
    print(f"PORTE DE L AGENT CODEUR : {'FRANCHIE' if ok else 'REFUSEE'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
