#!/usr/bin/env python3
"""monde_fidele — LE MONDE DE LA SANDBOX, AUSSI PROCHE D ARMA QUE CE QUI A ETE MESURE.

Tout ce qui suit a ete MESURE sur Arma. Rien n est choisi, rien n est ajuste au jugement.
Chaque constante porte sa mesure et sa date ; celles qui n ont pas de mesure ne sont pas ici.

⚠️ POURQUOI CE FICHIER EXISTE. Les mecanismes fideles etaient tous ECRITS dans
`assault_terrain`, et presque tous ETEINTS PAR DEFAUT. Ils vivaient dispersés dans les entetes
de six scripts de `leviathan/`, chacun en allumant un sous-ensemble different. Il n existait
nulle part une reponse a la question « quel est le monde le plus fidele qu on sache
construire ». C est ce fichier.

LES DEUX GRANDEURS QU ARMA SEPARE, ET QUE LE GYMNASE CONFONDAIT :
  · ETRE DETECTE  — le camp apprend qu on existe. Monotone, jamais recuperee, portee 100 m
                    dans TOUTES les directions, et un homme couche disparait passe 120 m.
  · ETRE TOUCHE   — une fois connu, on est atteint selon la courbe distance x posture.
Le gymnase n avait que la seconde. D ou un contournement qui rendait litteralement invisible :
96 % de reussite au debordement la ou le juge externe en donne 0 %.
"""
import math, json, sys, os
sys.path.insert(0, "/home/younes/arma3-marl")

LEV = "/home/younes/arma3-marl/leviathan"
COURBE = LEV + "/courbe_toucher_monotone.json"   # la mesure du 26/07, monotonie reparee, alerte RESOLUE et non effacee

# ─── LES CONVERSIONS. Arma compte en SECONDES et en BALLES, la sandbox en PAS.
SEC_PAR_PAS      = 3.28    # duree reelle d un pas (move / vitesse mesuree)
TIR_PAR_PAS      = 1.15    # balles tirees par defenseur et par pas
DEGAT_PAR_IMPACT = 0.233   # part de la sante retiree par impact

MONDE_ARMA = dict(
    # ---- LE TOUCHER. Sans elle, hit=0.06 partout et une falaise a fire_range : un monde ou
    # se rapprocher ne coute rien. C EST LE PARAMETRE QUI A REFUSE DE TRANSFERER TROIS FOIS.
    courbe=COURBE, tir_par_pas=TIR_PAR_PAS, sec_par_pas=SEC_PAR_PAS,
    degat_par_impact=DEGAT_PAR_IMPACT,

    # ---- LA SUPPRESSION. Mesure du 28/07 : sous le feu il RESTE 8 % de capacite de nuire
    # (cadence x0,57, precision x0,14). L ancien tout-ou-rien rendait l attaquant INVULNERABLE
    # des qu on arrosait. `persist` : la cadence revient a 89 % en 2 s, report faible.
    supp_residuel=0.08, supp_persist=0.35,

    # ---- UN DEFENSEUR TIRE SUR UN HOMME. Sans ca un flanqueur isole encaisse le feu de trois
    # defenseurs dans le meme pas : la sandbox etait 4x trop letale, et cette seule correction
    # a fait DISPARAITRE l avantage du flanc qu on croyait avoir mesure.
    cible_unique=True,

    # ---- LE CLIQUET D ALERTE. Mesure du 30/07 : detection 4,00 a 30 m, 1,72 a 60 m, nulle a
    # 100 m, dans TOUTES les directions ; trois tirs depuis l invisibilite coutent +1,50 a tout
    # le groupe ; AUCUNE decroissance en 300 s. C est la grandeur que le gymnase n avait pas.
    alerte=True,

    # ---- L ARC EST UN SURSIS, PAS UNE PROTECTION. Mesure : le defenseur riposte a 100 % a
    # tous les angles ~4 s plus tard, ET SANS PIVOTER (jamais venu a moins de 25 deg de son
    # attaquant). Le cone ne tourne pas : il S OUVRE.
    arc_latence_s=4.0,
    # ⚠️ PAS de `def_arc` ici : `def_rand` le TIRE AU HASARD par episode et IGNORE la valeur
    # passee — le garde-fou du fichier le dit, trois bancs ont tourne des semaines en croyant
    # piloter un arc fixe. On randomise (la defense d Arma n a pas toujours le meme arc), donc
    # on ne pretend pas la regler.
    def_line=True, def_rand=True,

    # ---- LA POSTURE. Fraction de corps touchable debout/accroupi/couche, et le couche
    # disparait du REGARD passe 120 m (banc de l angle mort, 18/18 dans le cone contre 0/26).
    postures=True, hull=True,

    # ---- LE FREIN SOUS LE FEU. Sans lui la vitesse ne dependait jamais du feu recu : le
    # gymnase etait structurellement incapable de representer une halte sous le feu et
    # annoncait 94,6 % la ou le juge externe donne 0 %.
    frein_feu=0.35,

    # ---- LA MANOEUVRE. `nav_around` = doMove d Arma (longer le mur au lieu de s arreter net).
    nav_around=True,
    secure_task=True, secure_only=True,

    # ---- L OBSERVATION EST CELLE DU PONT, PAS CELLE DU GYMNASE ----
    # Mesure du 11/08 : cinq colonnes sur douze etaient hors distribution entre le gymnase et
    # Arma, et trois structurellement — `dcover` valait 0,02 au gymnase et 1,00 CONSTANT sur
    # Arma, `slope` 0,59 contre 0,01, `nd` 0,22 contre 0,78. Meme nom, meme ordre, meme forme,
    # AUTRE SENS. Une entree constante a 1,00 la ou le reseau a appris 0,02 sature ses tanh :
    # la politique rendait la meme action pour les huit hommes, et l escouade s eloignait.
    # `arma_obs` existait pour ca et je l avais ignore : il normalise `dcover` COMME LE PONT
    # (/30 m cape) et il RETIRE `slope` — precisement parce qu Arma ne sait pas la rendre
    # (surfaceNormal donne 0,01 la ou le gymnase genere 0,59).
    arma_obs=True,

    # ---- L ARC DU DEFENSEUR : DEUX NOMBRES, CERTIFIES DEPUIS JUILLET ----
    # L agent ne PERCOIT PAS ou regarde le defenseur. Son observation est identique dans
    # l angle mort et dans la ligne de mire — seuls les degats different, et il ne peut donc
    # pas contourner ce qu il ne voit pas. Mesure : lui donner ces deux nombres fait chuter
    # son exposition de 28 %, et il contourne a 132 m quand le bon crochet se fait a 184.
    # ⟨fiche `agent-percoit-pas-manoeuvre`⟩
    # C est le seul levier certifie qui n avait jamais ete branche — et c est aussi ce qui
    # explique qu il ne trouve pas le flanc : sans l arc, contourner est un detour gratuit
    # qui ne rapporte rien. Arma sait le fournir : la direction du defenseur le plus proche
    # est une ligne de SQF.
    arc_obs=True,
)

# Ce qui exige une REPLIQUE de terrain reel et n a donc pas sa place dans le defaut :
#   replica=True, emergent_expo=True  -> exposition = fraction de corps touchable, par rayons
MONDE_ARMA_REPLIQUE = dict(MONDE_ARMA, replica=True, emergent_expo=True)


def monde(replique=None, **kw):
    """Construit le monde le plus fidele qu on sache batir. `kw` ecrase, et le DIT."""
    from assault_terrain import AssaultTerrain
    base = dict(MONDE_ARMA_REPLIQUE if replique else MONDE_ARMA)
    if replique:
        base["replica_path"] = replique
    ecrases = {k: (base.get(k), v) for k, v in kw.items() if k in base and base[k] != v}
    if ecrases:
        print("  ⚠ le monde fidele est ECRASE sur : "
              + ", ".join(f"{k} {a} -> {b}" for k, (a, b) in ecrases.items()))
    base.update(kw)
    return AssaultTerrain(**base)


def inventaire():
    """Ce qui est mesure et allume, et ce qui manque encore — nomme, pas tu."""
    print("\n  LE MONDE FIDELE — ce qui est MESURE et ALLUME")
    print("  " + "=" * 72)
    for k, v in MONDE_ARMA.items():
        print(f"    {k:<20} {v}")
    print("\n  CE QUI MANQUE ENCORE, ET QU ON NE SIMULE PAS EN L INVENTANT")
    print("  " + "=" * 72)
    for quoi, pourquoi in [
        ("la verticalite", "LOS en 2,5D ne rend rien ; phenomene physique, pas un reglage"),
        ("le son", "Arma porte le tir a plusieurs centaines de metres ; jamais mesure ici"),
        ("la fumee", "mesuree sur Arma mais pas encore portee dans le gymnase"),
        ("le blesse", "Arma a des etats intermediaires ; ici on est vivant ou mort"),
        ("la munition", "personne ne s asseche dans le gymnase ; Arma si"),
    ]:
        print(f"    {quoi:<20} {pourquoi}")


if __name__ == "__main__":
    inventaire()
    print("\n  CONSTRUCTION D ESSAI")
    print("  " + "=" * 72)
    e = monde(num_envs=64, device="cuda:0", seed=7)
    print(f"    monde bati : {e.N} environnements, A={e.A} contre D={e.D}")
    print(f"    courbe chargee : {e.courbe is not None}"
          f" · cliquet : {e.alerte} · sursis : {e.arc_latence_pas} pas"
          f" · couche invisible au-dela de {e.COUCHE_INVISIBLE_M} m")
    o = e.reset()
    print(f"    observation : {tuple(o.shape)}")
