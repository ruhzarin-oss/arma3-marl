"""PORTE DU CODE A LA DEMANDE ( 27/09, etape 1 de plans/plan-code-a-la-demande.md ; point « importer » du domaine 7 ).
Seuils ecrits avant la mesure.

  Q0  jamais bloque, rien de change : un pays branche sur une bibliotheque VIDE est identique au bit, jour apres jour,
      au meme pays sans branchement ;
  Q1  un code faux est refuse par le service : import, action hors catalogue, boucle sans fin, pas de decider ; et un
      Qwen qui ne rend que du code faux voit sa version publiee « refuse », avec la raison ;
  Q2  un code bon est publie « en_epreuve », avec son essai hors ligne ( >= 200 entrees, toutes des actions ) ;
  Q3  CONTROLE POSITIF d adoption : la regle rendue mauvaise ( toujours trois jours d import ), un candidat « attendre »
      sur la moitie des cles, 16 jours : le verdict l ADOPTE ( meilleur, p < 0,05 ), la bibliotheque et le journal le
      disent, et il decide ensuite pour tous ;
  Q4  CONTROLE INVERSE : la regle « attendre », un candidat « trois jours » : RETIRE, et une nouvelle demande part a Qwen
      avec le verdict chiffre ;
  Q5  Ollama coupe : le service laisse la demande dans la file, ne publie rien, ne plante pas.

   python -m monde.porte_code_a_la_demande"""
import glob, json, os, shutil, sys, tempfile
from . import code_a_la_demande as CAD
from .pays import essais as T, d07_exterieur as EXT
from .porte_domaines import empreinte

GRAINE = 11
BON = "def decider(t):\n    if t['couverture_marche'] < 0.2 and t['tresorerie'] > 0.1:\n        return 'un_jour'\n    return 'attendre'\n"


def _toujours(action):
    return f"def decider(t):\n    return {action!r}\n"


def _epreuve(regle_action, candidat_action, jours=16):
    """Un pays « exterieur », la regle forcee a `regle_action`, un candidat `candidat_action` sur la moitie des cles.
    Rend ( etat publie, verdict, evenements code_verdict, fichiers de la file, part du bras apres le verdict )."""
    biblio = tempfile.mkdtemp(prefix="biblio_", dir="/mnt/data/hmt/qwen"); file = tempfile.mkdtemp(prefix="file_", dir="/mnt/data/hmt/qwen")
    d = CAD.contrat(EXT.POINT_IMPORT)
    v = CAD.publier("importer", _toujours(candidat_action), d, CAD.essayer(_toujours(candidat_action), d), "en_epreuve", biblio)
    regle0, j0, file0 = EXT.POINT_IMPORT.regle, CAD.JOURS_EPREUVE, CAD.FILE
    k = EXT.ACTIONS.index(regle_action)
    try:
        EXT.POINT_IMPORT.regle = lambda x, ctx, k=k: k
        CAD.JOURS_EPREUVE, CAD.FILE = jours - 1, file
        w, p = T.monde(["exterieur"], graine=GRAINE)
        CAD.brancher(p, biblio, part=0.5)
        T.jours(w, jours)
        etat = CAD.versions("importer", biblio)[-1][1]
        ev = [e for e in p.socle.journal.recents if e.get("type") == "code_verdict"]
        dec = p.domaine("exterieur").decideur
        part = dec.bras.part if dec.bras is not None else None
        demandes = glob.glob(os.path.join(file, "*.json"))
    finally:
        EXT.POINT_IMPORT.regle, CAD.JOURS_EPREUVE, CAD.FILE = regle0, j0, file0
    shutil.rmtree(biblio, ignore_errors=True)
    r = (etat.get("etat"), etat.get("verdict", {}), ev, [json.load(open(f)) for f in demandes], part)
    shutil.rmtree(file, ignore_errors=True)
    return r


def main():
    ok_tout = True
    def dire(ok, texte):
        nonlocal ok_tout
        ok_tout &= bool(ok); print(f"{'PASSE ' if ok else 'ECHOUE'} {texte}", flush=True)
    os.makedirs("/mnt/data/hmt/qwen", exist_ok=True)
    d = CAD.contrat(EXT.POINT_IMPORT)

    # Q0 : une bibliotheque vide ne change rien
    vide = tempfile.mkdtemp(prefix="biblio_vide_", dir="/mnt/data/hmt/qwen")
    w1, p1 = T.monde(["exterieur"], graine=GRAINE)
    w2, p2 = T.monde(["exterieur"], graine=GRAINE); n = CAD.brancher(p2, vide)
    ecarts = []
    for j in range(8):
        T.jours(w1, 1); T.jours(w2, 1)
        e1, e2 = empreinte(w1), empreinte(w2)
        if e1 != e2: ecarts.append((j + 1, sorted(k for k in e1 if e1[k] != e2.get(k))[:4]))
    shutil.rmtree(vide, ignore_errors=True)
    dire(not ecarts and n == 0, f"Q0 bibliotheque vide : aucun bras ( {n} ), 8 jours identiques au bit {ecarts[:2]}")

    # Q1 : les codes faux sont refuses
    faux = {"import": "import os\ndef decider(t):\n    return 'attendre'\n",
            "hors catalogue": "def decider(t):\n    return 'voler_la_cargaison'\n",
            "boucle sans fin": "def decider(t):\n    while True:\n        pass\n",
            "pas de decider": "def choisir(t):\n    return 'attendre'\n",
            "attribut prive": "def decider(t):\n    return t.__class__\n"}
    refuses = {}
    for nom, src in faux.items():
        try: CAD.essayer(src, d); refuses[nom] = False
        except Exception: refuses[nom] = True
    biblio = tempfile.mkdtemp(prefix="biblio_q1_", dir="/mnt/data/hmt/qwen"); file = tempfile.mkdtemp(prefix="file_q1_", dir="/mnt/data/hmt/qwen")
    f = CAD.demander("importer", "porte Q1", file=file)
    v, etat = CAD.traiter(f, biblio, appel=lambda prompt, penser=True: {"response": "```python\n" + faux["hors catalogue"] + "```"})
    raison = json.load(open(os.path.join(biblio, "importer", v, "essai.json"))).get("erreur", "")
    dire(all(refuses.values()) and etat == "refuse" and "voler" in raison,
         f"Q1 codes faux refuses {refuses} ; un Qwen qui insiste : {v} {etat} ( {raison[:70]} )")

    # Q2 : un code bon est publie en epreuve
    f = CAD.demander("importer", "porte Q2", file=file)
    v2, etat2 = CAD.traiter(f, biblio, appel=lambda prompt, penser=True: {"response": "Mon idee :\n```python\n" + BON + "```\nvoila."})
    essai = json.load(open(os.path.join(biblio, "importer", v2, "essai.json")))
    dire(etat2 == "en_epreuve" and essai.get("essais", 0) >= CAD.ESSAIS_HORS_LIGNE and CAD.en_service("importer", biblio)[0] == v2,
         f"Q2 code bon : {v2} {etat2}, essai {essai}")
    shutil.rmtree(biblio, ignore_errors=True); shutil.rmtree(file, ignore_errors=True)

    # Q3 : controle positif d adoption
    etat3, vd3, ev3, dem3, part3 = _epreuve("trois_jours", "attendre")
    dire(etat3 == "adopte" and ev3 and ev3[-1]["decision"] == "adopte" and part3 == 1.0,
         f"Q3 regle mauvaise ( trois jours ), candidat attendre : {etat3} ( notes {vd3.get('notes_candidat')}/{vd3.get('notes_regle')}, "
         f"moyennes {vd3.get('moyenne_candidat', 0):+.4f} / {vd3.get('moyenne_regle', 0):+.4f}, p {vd3.get('p_meilleur')} ), "
         f"decide ensuite pour tous : {part3 == 1.0}")

    # Q4 : controle inverse
    etat4, vd4, ev4, dem4, part4 = _epreuve("attendre", "trois_jours")
    dire(etat4 == "retire" and part4 is None and len(dem4) == 1 and dem4[0].get("retour", {}).get("decision") == "retire",
         f"Q4 regle attendre, candidat trois jours : {etat4} ( {vd4.get('raison')}, moyennes {vd4.get('moyenne_candidat', 0):+.4f} / "
         f"{vd4.get('moyenne_regle', 0):+.4f}, p pire {vd4.get('p_pire')} ) ; nouvelle demande a Qwen : {len(dem4)}")

    # Q5 : Ollama coupe
    biblio = tempfile.mkdtemp(prefix="biblio_q5_", dir="/mnt/data/hmt/qwen"); file = tempfile.mkdtemp(prefix="file_q5_", dir="/mnt/data/hmt/qwen")
    CAD.demander("importer", "porte Q5", file=file)
    hote0 = CAD.HOTE
    try:
        CAD.HOTE = "http://127.0.0.1:9"
        CAD.veiller(file, biblio, une_fois=True)
    finally:
        CAD.HOTE = hote0
    reste = len(glob.glob(os.path.join(file, "*.json"))); publie = len(CAD.versions("importer", biblio))
    shutil.rmtree(biblio, ignore_errors=True); shutil.rmtree(file, ignore_errors=True)
    dire(reste == 1 and publie == 0, f"Q5 Ollama coupe : la demande reste dans la file ( {reste} ), rien de publie ( {publie} )")
    print(f"PORTE DU CODE A LA DEMANDE : {'FRANCHIE' if ok_tout else 'REFUSEE'}")
    return 0 if ok_tout else 1


if __name__ == "__main__":
    sys.exit(main())
