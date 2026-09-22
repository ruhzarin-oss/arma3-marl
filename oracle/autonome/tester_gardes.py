"""Chaque garde-fou est teste CONTRE L INCIDENT REEL qu il doit attraper. Un garde-fou qui ne sait pas echouer ne
protege de rien ( regle 16 ).  python -m oracle.autonome.tester_gardes"""
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
print("== 10. l imagination boguee du 21/09 ( reseaux arretes sur la justesse ) doit etre INTERCEPTEE")
from sklearn.neural_network import MLPClassifier
Eh = Dn.utilisables(Dn.episodes(lambda c: not str(c).startswith(C.PREFIXES_HISTORIQUES)))


class MondeBogue(M.Monde):
    """La v1, reconstruite telle qu elle etait : 10 MLPClassifier, early_stopping=True."""
    def apprendre(self, E):
        X = M.encoder([{k: e[k] for k in C.ARMES} for e in E], [e["graine"] for e in E], [e["option"] for e in E])
        Y = np.array([e["compromis"] for e in E]); self.taux = float(Y.mean()); self.reseaux = []
        for s in range(10):
            idx = np.random.default_rng(C.GRAINE + s).integers(0, len(Y), len(Y))
            self.reseaux.append(MLPClassifier(hidden_layer_sizes=(64, 32), alpha=1e-3, early_stopping=True, validation_fraction=0.2,
                                              max_iter=500, random_state=C.GRAINE + s).fit(X[idx], Y[idx]))
        return self

    def predire(self, situations, graines, options):
        X = M.encoder(situations, graines, options)
        P = np.array([m.predict_proba(X)[:, 1] for m in self.reseaux]); return P.mean(0), P.std(0)


ok_b, raisons_b, m_b = G.imagination_saine(MondeBogue().apprendre(Eh), Eh)
verifie("la v1 boguee est interceptee", not ok_b, " ; ".join(raisons_b)[:200])
ok_c, raisons_c, m_c = G.imagination_saine(M.Monde().apprendre(Eh), Eh)
verifie("l imagination corrigee passe", ok_c, f"predit {m_c['prediction_moyenne']:.3f} pour {m_c['taux_reel']:.3f}, ecart-type {m_c['ecart_type']:.3f}")


class MondeFige(M.Monde):
    def predire(self, situations, graines, options):
        return np.full(len(situations), self.taux), np.zeros(len(situations))


ok_f, raisons_f, _ = G.imagination_saine(MondeFige().apprendre(Eh), Eh)
verifie("une imagination qui predit le taux de base partout est interceptee ( figee )", not ok_f, " ; ".join(raisons_f)[:160])
print("== 11. l epreuve des motifs est prospective et ne conclut pas trop tot")
from . import motifs as Mo
cle = ("menace_p2", 5, "attendre_sauve")
verifie("pas de verdict sous 20 episodes par option", Mo.epreuve(cle, dict(n_t=10, c_t=9, n_a=10, c_a=0))[0] == "en attente")
verifie("un vrai ecart dans le sens predit est confirme", Mo.epreuve(cle, dict(n_t=40, c_t=20, n_a=40, c_a=5))[0] == "CONFIRME")
verifie("un ecart dans le SENS CONTRAIRE n est pas confirme", Mo.epreuve(cle, dict(n_t=40, c_t=5, n_a=40, c_a=20))[0] == "non confirme")
print("== 12. la moitie Architecte : elle doit SAVOIR REUSSIR et SAVOIR ECHOUER ( regle 16 )")
import copy
from . import architecte_apprend as AA
base = [e for e in Dn.utilisables(Dn.episodes(lambda c: str(c).startswith(C.PREFIXES_HISTORIQUES)))
        if e.get("atteint_decision") and (e.get("p_compromis") or 0) == 0]
rng = np.random.default_rng(7)
def monde_synthetique(effet):
    E = copy.deepcopy(base)
    for e in E:
        poste = (e.get("p_moteur_entendu") or 0) == 0 and (e.get("p_n_vues_menace") or 0) > 0
        p = (0.60 if e["option_imposee"] == 1 else 0.15) if (effet and poste) else 0.20
        e["compromis"] = int(rng.random() < p)
    return E
r1 = AA.apprendre(monde_synthetique(True), {"type": "constante", "option": 1}, candidats=("logistique",))
verifie("un effet PERCEPTIBLE est trouve et la regle est adoptee", r1["adoptee"] and r1["meilleur"] == "logistique",
        f"meilleur {r1['meilleur']}, {r1['candidats'][r1['meilleur']]['valeur']:.3f} contre {r1['valeur_courante']:.3f}")
if r1["regle"]:
    Es = monde_synthetique(True); Es = AA.jeu(Es); c = A.choix(r1["regle"], Es)
    poste = np.array([(e.get("p_moteur_entendu") or 0) == 0 and (e.get("p_n_vues_menace") or 0) > 0 for e in Es])
    # ailleurs les deux options sont EQUIVALENTES dans ce monde de test : la regle a le droit d y etre indifferente
    verifie("la regle adoptee attend face au poste percu", np.mean(c[poste] == 2) > 0.8,
            f"attend {np.mean(c[poste] == 2):.0%} des fois face au poste ( ailleurs {np.mean(c[~poste] == 2):.0%}, options equivalentes )")
# le taux de FAUSSES adoptions, mesure sur 20 mondes sans effet, et la PUISSANCE sur 5 mondes avec effet
fausses = sum(AA.apprendre(monde_synthetique(False), {"type": "constante", "option": 1}, candidats=("logistique",))["adoptee"] for _ in range(20))
verifie("sans effet, au plus 1 fausse adoption sur 20 mondes", fausses <= 1, f"{fausses} / 20")
vraies = sum(AA.apprendre(monde_synthetique(True), {"type": "constante", "option": 1}, candidats=("logistique",))["adoptee"] for _ in range(5))
verifie("avec effet, adoptee dans au moins 4 mondes sur 5", vraies >= 4, f"{vraies} / 5")
try:
    A.colonne(base[:3], "moteur_allume"); verifie("une variable de verite est refusee a l Architecte", False)
except ValueError:
    verifie("une variable de verite est refusee a l Architecte", True)
print("== 13. une formule d EvoGP est relue EXACTEMENT ( 22/09 : 114 sur 400 seulement par l affichage d EvoGP )")
import torch
from evogp.tree import Forest, GenerateDescriptor
d = GenerateDescriptor(max_tree_len=48, input_len=4, output_len=1,
                       using_funcs=["+", "-", "*", "loose_div", "min", "max", "neg", ">", "<", "tanh", "abs"],
                       max_layer_cnt=5, const_samples=[-1.0, -0.5, -0.1, 0.0, 0.1, 0.5, 1.0])
torch.manual_seed(0); foret = Forest.random_generate(pop_size=400, descriptor=d)
Xt = np.random.default_rng(0).normal(size=(200, 4)).astype(np.float32)
fid = [AA.verifier_traduction(foret[i], AA.vers_python(foret[i], [f"v{j}" for j in range(4)]), Xt, [f"v{j}" for j in range(4)]) for i in range(400)]
verifie("au moins 398 formules sur 400 relues identiques sur 99 % des points", sum(f >= 0.99 for f in fid) >= 398,
        f"{sum(f >= 0.99 for f in fid)} / 400 ; fidelite moyenne {np.mean(fid):.4f}")
print(f"\n{sum(ok_total)} / {len(ok_total)} garde-fous testes contre leur incident : "
      f"{'TOUS PASSENT' if all(ok_total) else 'AU MOINS UN ECHOUE'}")
