"""Chaque garde-fou est teste CONTRE L INCIDENT REEL qu il doit attraper. Un garde-fou qui ne sait pas echouer ne
protege de rien ( regle 16 ).  python -m diable.tester_gardes"""
import numpy as np
from . import config as C, donnees as Dn, gardes as G, generateur as Gen, monde as M, architecte as A

ok_total = []


def verifie(nom, condition, detail=""):
    ok_total.append(bool(condition)); print(f"   {'PASSE ' if condition else 'ECHOUE'}  {nom}  {detail}")


print("== 1. deploiement rate du 20/09 16 h 17 ( CONTROLES-ORACLE-20-09 )")
ok, fautifs = G.deploiement_prouve("CONTROLES-ORACLE-20-09")
verifie("le deploiement non prouve est detecte", not ok, f"{len(fautifs)} run(s) fautif(s)")
sig = G.signature_seconde_graine("CONTROLES-ORACLE-20-09")
verifie("la signature « seconde graine sans resultat » est detectee", sig >= 2, f"{sig} job(s)")
E = Dn.episodes(lambda c: c == "CONTROLES-ORACLE-20-09", admissibles_seulement=False)
q, arret, raisons = G.verifier_apres_vol(E, "CONTROLES-ORACLE-20-09")
verifie("et la boucle s ARRETE", arret and q, " ; ".join(raisons)[:160])

print("== 2. erreurs SQF quand les dix sont morts ( CONTROLES-ORACLE-V2-20-09 )")
E = Dn.episodes(lambda c: c == "CONTROLES-ORACLE-V2-20-09", admissibles_seulement=False)
q, arret, raisons = G.verifier_apres_vol(E, "CONTROLES-ORACLE-V2-20-09")
verifie("l iteration est mise en quarantaine", q and any("SQF" in r for r in raisons), " ; ".join(raisons)[:160])

print("== 3. une campagne saine ne doit PAS etre refusee ( CALIBRATION-P2-V2-21-09 )")
E = Dn.episodes(lambda c: c == "CALIBRATION-P2-V2-21-09")
q, arret, raisons = G.verifier_apres_vol(E, "CALIBRATION-P2-V2-21-09")
verifie("pas de quarantaine, pas d arret", not q and not arret, " ; ".join(raisons) or "aucune raison")

print("== 4. option jouee differente de l option imposee")
faux = [dict(verdict="ACCEPTE", erreurs=0, fin=True, choix_joue=2, option_imposee=1)] * 3
q, _, raisons = G.verifier_apres_vol(faux, "AUCUNE")
verifie("detectee", q and any("option" in r for r in raisons))

print("== 5. cases vides : comptees en cases, reparables")
props = [{}, {}]
Ev = [dict(candidat=0, option_imposee=1, verdict="ACCEPTE", fin=True, erreurs=0),
      dict(candidat=0, option_imposee=2, verdict=None, fin=False, erreurs=0),
      dict(candidat=1, option_imposee=1, verdict="ACCEPTE", fin=True, erreurs=0),
      dict(candidat=1, option_imposee=1, verdict=None, fin=False, erreurs=0),            # exemplaire orphelin : case pleine quand meme
      dict(candidat=1, option_imposee=2, verdict="ACCEPTE", fin=True, erreurs=0)]
v = G.cases_vides(Ev, props)
verifie("seule la case ( 0, attendre ) est vide, l orphelin ne bloque rien", v == [(0, 2)], str(v))

print("== 6. armes hors des valeurs permises")
f = G.armes_permises(dict(situation={**{k: C.ARMES[k][0] for k in C.ARMES}, "palier": 9}, graines=[7, 7]))
verifie("palier 9 ( monde vide ) et graines identiques refuses", len(f) == 2, str(f))

print("== 7. budget")
verifie("80 episodes refuses", bool(G.budget(dict(historique=[], iteration=0), 80)))
verifie("64 episodes acceptes", not G.budget(dict(historique=[], iteration=0), 64))

print("== 8. empreinte de la mission stable, et sensible")
e1, e2 = G.empreinte_mission(), G.empreinte_mission()
verifie("deux calculs donnent la meme empreinte", e1 == e2, e1)
import os, shutil, tempfile
tmp = tempfile.mkdtemp(); copie = f"{tmp}/chacaloracle"
shutil.copytree(C.MISSION, copie, ignore=shutil.ignore_patterns("*.pbo"))
vrai = C.MISSION; C.MISSION = copie
avant = G.empreinte_mission()
with open(f"{copie}/mission.Altis/chacal/46_controles_oracle.sqf", "a") as f: f.write("\n// une ligne de plus\n")
apres = G.empreinte_mission(); C.MISSION = vrai; shutil.rmtree(tmp)
verifie("une seule ligne ajoutee a une COPIE de la mission change l empreinte", avant == e1 and apres != avant, f"{avant} -> {apres}")

print("== 9. jamais un rejeu a l identique")
E = Dn.utilisables(Dn.episodes(lambda c: c == "CALIBRATION-P2-V2-21-09"))[:300]
m = M.Monde().apprendre(E)
s0 = {k: E[0][k] for k in C.ARMES}
joue = {(Gen.cle(s0), g, o) for g in C.GRAINES for o in (1, 2)}
props, bilan = Gen.proposer(m, A.charger(), E, joue, [], np.random.default_rng(1))
verifie("aucune proposition ne rejoue une situation deja jouee", all(Gen.cle(p["situation"]) != Gen.cle(s0) for p in props),
        f"{len(props)} propositions")
verifie("diversite : deux propositions different d au moins 3 armes",
        all(Gen.distance(a["situation"], b["situation"]) >= C.DISTANCE_MIN_DIVERSITE for i, a in enumerate(props) for b in props[i + 1:]))
print(f"\n{sum(ok_total)} / {len(ok_total)} garde-fous testes contre leur incident : "
      f"{'TOUS PASSENT' if all(ok_total) else 'AU MOINS UN ECHOUE'}")
