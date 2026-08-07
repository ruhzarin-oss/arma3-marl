#!/usr/bin/env python3
"""fix_expo.py — remplacer ma reconstitution d expo par la VRAIE formule, lue dans le code.

Mon controle negatif avait echoue parce que j avais REECRIT expo a la main : ce que j avais
ecrit etait un detecteur de cone, d ou son score de +3,68 % — exactement celui de la paire du
cone, au centieme pres. Le controle a fait son travail : il a attrape que ma reconstitution
n etait pas ce qu elle pretendait etre.

LA VRAIE FORMULE, recopiee de agent_complet.py lignes 195-215, sans une virgule de plus :

    dans = sigmoid((CHAMP - ec) * 1.2)
    base = 0,45 * (1 - clamp(d/400))
    e    = (base + (1-base) * dans) * (1 - clamp(d/450))
    e    = e * facteur_posture           # le couche ne paie qu au-dela de 120 m
    expo = MAX sur les defenseurs        # PAS la moyenne : il suffit d UN homme qui vous voit

⟨regle 6, amendee : un chiffre se lit dans l artefact en service, et une propriete du monde
 se lit dans son code avant qu on ne batisse dessus. Je viens de l enfreindre une fois de
 plus — cette fois sur une FONCTION, pas sur une propriete.⟩
"""
import pathlib

P = pathlib.Path('/home/younes/arma3-marl/banc_matrice2.py')
t = P.read_text(encoding='utf-8')

ANC = '''def expo_analytique():
    """la fonction de cout de la sandbox, AUC 0,5005 — le hasard, mesure. Reconstituee ici
    sur les memes entrees : elle DOIT echouer toutes les portes."""
    e = np.zeros(len(Y), np.float32)
    for k in range(ENN.shape[1]):
        m = viv[:, k]
        dd = np.where(m, d_e[:, k], 1e9)
        dans = (a_lui[:, k] < DEMI_CONE) & m
        e += np.where(dans, np.clip(1.0 - dd / 400.0, 0, 1), 0.0)
    return e'''
NEUF = '''SEUIL_COUCHE, PENTE_COUCHE = 120.0, 12.0

def expo_analytique():
    """expo, la fonction de cout de la sandbox — AUC 0,5005 sur ce corpus, MESURE.

    RECOPIEE de agent_complet.py lignes 195-215, pas reecrite. Ma premiere version etait un
    detecteur de cone deguise, et le controle negatif l a attrapee."""
    dd = np.where(viv, d_e, 1e9).clip(min=1.0)
    dans = 1.0 / (1.0 + np.exp(-(DEMI_CONE - a_lui) * 1.2))
    base = 0.45 * (1.0 - np.clip(dd / 400.0, 0, 1))
    e = (base + (1.0 - base) * dans) * (1.0 - np.clip(dd / 450.0, 0, 1))
    # facteur de posture : le couche ne paie qu au-dela de 120 m, par observateur
    couche = 1.0 - 1.0 / (1.0 + np.exp(-(dd - SEUIL_COUCHE) / PENTE_COUCHE))
    est_couche = (SOI[:, 4] > 0.6)[:, None]          # posture/3 : 2/3 = couche
    e = e * np.where(est_couche, couche, 1.0)
    e = np.where(viv, e, 0.0)
    return e.max(axis=1)                              # LE MAXIMUM, pas la moyenne'''
assert t.count(ANC) == 1, "ancre expo_analytique introuvable"
t = t.replace(ANC, NEUF, 1)
P.write_text(t, encoding='utf-8')
print("expo remplacee par la vraie formule, lue dans le code")
