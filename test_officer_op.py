"""test_officer_op — TEST A BLANC de l'officier operatif (sans Arma).
8 rapports de contact (un par posture defensive), SANS nommer la posture : l'officier doit la DEDUIRE
puis choisir une manoeuvre. On verifie qu'il colle au champion mesure dans la matrice propre, et on lit
sa justification (critere L2/L3 : ordres explicables, comportement de vrai commandement)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from officer_op import decide

# situations = (rapport observable SANS le nom de la posture, manoeuvre-champion attendue d'apres la matrice propre)
SITUATIONS = [
    ("La garnison reste figee dans l'objectif, un ecran de patrouilles tient le nord. Aucune manoeuvre ennemie au contact.", "M3", "statique"),
    ("Des que l'on pousse a l'ouest, les patrouilles ennemies se redeploient et se massent sur ce flanc pour le bloquer.", "M3", "anti-flanc"),
    ("Un bloc ennemi avance au centre stoppe net notre axe frontal ; les deux flancs paraissent degarnis.", "M3", "anti-centre"),
    ("Sous notre pression l'ennemi ne tient pas sa ligne : il decroche par bonds sur des positions successives vers l'arriere.", "M1", "elastique"),
    ("Approche sans le moindre contact. Aucune patrouille dehors : tout l'ennemi est masse en perimetre dense a l'interieur de l'objectif.", "M8", "herisson"),
    ("L'ennemi a quitte l'objectif sans combattre et s'est replie sur les surplombs au nord ; l'objectif est vide mais domine.", "M12", "appat"),
    ("A peine au contact, l'ennemi sort de ses positions et vient attaquer nos zones de rassemblement au sud.", "M12", "sortie"),
    ("Une reserve mobile ennemie surgit du nord et fonce sur nos points de concentration des qu'on se regroupe.", "M3", "mobile"),
]

ok = 0
for i, (rapport, attendu, nom) in enumerate(SITUATIONS, 1):
    try:
        d = decide(rapport)
    except Exception as e:
        print("%d. [%s] ERREUR: %s" % (i, nom, e)); continue
    man = str(d.get("manoeuvre", "")).upper().replace(" ", "")[:3].rstrip("-")
    match = man == attendu
    ok += match
    print("%d. [%-10s] choisi=%-4s attendu=%-4s %s" % (i, nom, man, attendu, "OK" if match else "x"))
    print("     posture estimee : %s" % d.get("posture", "?"))
    print("     allocation      : %s" % str(d.get("allocation", "?"))[:110])
    print("     justification   : %s" % str(d.get("justification", "?"))[:160])
    print()

print("===== SCORE DOCTRINAL : %d/%d manoeuvres = champion mesure =====" % (ok, len(SITUATIONS)))
print("(L'essentiel du Jalon 1.2 : (a) l'officier DEDUIT la posture, (b) il EXPLIQUE en clair. Le match exact")
print(" est un bonus ; meme une manoeuvre proche bien justifiee = comportement de commandement valide.)")
