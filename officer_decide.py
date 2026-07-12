"""officer_decide — l'OFFICIER-LLM (qwen2.5:14b) lit un rapport de contact -> estime la posture -> CHOISIT
une manoeuvre du repertoire -> JUSTIFIE. On affiche sa decision (a executer ensuite, tracee)."""
import json
import officer_op

REPORT = ("Objectif TENU par l'ennemi. Garnison statique d'environ 12 hommes massee dans le complexe, "
          "avec un ecran de patrouilles (~8 hommes) au nord. Pas de reserve mobile ni de manoeuvre "
          "offensive observee. Terrain : crete d'appui au sud-ouest, flancs ouest et est praticables.")

if __name__ == "__main__":
    print("RAPPORT DE CONTACT transmis a l'officier :")
    print("  " + REPORT)
    dec = officer_op.decide(REPORT)
    print("\n=== DECISION DE L'OFFICIER (qwen2.5:14b) ===")
    print("  posture estimee   : " + str(dec.get("posture", "?")))
    print("  MANOEUVRE choisie : " + str(dec.get("manoeuvre", "?")))
    print("  allocation        : " + str(dec.get("allocation", "?")))
    print("  justification     : " + str(dec.get("justification", "?")))
    # ecrit le choix pour l'execution
    with open("/tmp/officer_choice.json", "w") as f:
        json.dump(dec, f)
    print("\nMANOEUVRE_RETENUE=" + str(dec.get("manoeuvre", "?")))
