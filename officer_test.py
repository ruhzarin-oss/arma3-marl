"""officer_test — l'officier-LLM lit-il VRAIMENT la situation ? 4 postures differentes -> choisit-il
des manoeuvres differentes et coherentes ? (preuve qu'il discrimine, pas qu'il repete)."""
import officer_op

CAS = [
    ("Garnison statique massee dans le complexe + ecran de patrouilles au nord. Pas de reserve mobile.", "M3 attendu"),
    ("HERISSON : tout l'ennemi masse en perimetre dense DANS l'objectif, aucun ecran a l'exterieur, defense tres compacte.", "M8 attendu"),
    ("APPAT : l'ennemi ABANDONNE l'objectif des qu'on approche, puis contre-attaque violemment quand on l'occupe.", "M12 attendu"),
    ("Defense ELASTIQUE : l'ennemi recule par bonds sur des lignes successives sous la pression, il ne tient aucune position.", "M1 attendu"),
]

if __name__ == "__main__":
    print("=" * 74)
    print("L'OFFICIER-LLM (qwen2.5:14b) face a 4 situations differentes :")
    print("=" * 74)
    for rep, attendu in CAS:
        dec = officer_op.decide(rep)
        print("\nSITUATION : " + rep[:78])
        print("  -> posture lue : " + str(dec.get("posture", "?")))
        print("  -> MANOEUVRE   : %-4s   (%s)" % (str(dec.get("manoeuvre", "?")), attendu))
        print("  -> pourquoi    : " + str(dec.get("justification", "?"))[:150])
