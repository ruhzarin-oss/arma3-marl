#!/usr/bin/env python3
"""fuite — LE SERVEUR S'ENCRASSE-T-IL AU FIL D'UN LONG RUN ?

⚠️ L'ENIGME QU'ON INSTRUIT. Pendant la sonde de vacance du 02/09, la graine 1 declinait
serie apres serie (94,1 -> 72,5) alors que les series sont independantes et sans gradient.
La doctrine rejouee sur les deux instances rendait 51/51 : le MONDE etait intact.
⟨Fable⟩ « Ton controle de sante a certifie le mauvais objet : la doctrine prouve que le
monde est intact, pas que le TEMPO du run l'est. Un doMove scripte est indifferent a une
latence qui grandit ; une politique qui agit a chaque pas sous un budget ne l'est pas. »

L'enquete sur journaux a montre que ce ne sont PAS les budgets qui declinent, mais les
episodes ou le soldat NE BOUGE PAS : 0 -> 2 -> 2 -> 5 -> 9 sur les cinq series, avec la
duree murale qui monte (14,8 -> 16,0 s/ep) alors qu'elle est plate sur l'autre instance.
Hypothese : des entites s'accumulent, et les nouveaux soldats apparaissent dessus.

⚠️ ON NE PEUT PLUS L'INSTRUIRE SUR LES CADAVRES : les deux serveurs sont morts a 20:30,
tues par l'ordonnanceur, emportant leur etat. Le test est donc PROSPECTIF, sur un serveur
neuf : on injecte un compteur d'entites dans la mission, puis on la fait tourner longtemps.

CE QUI FERAIT ECHOUER L'HYPOTHESE : des compteurs plats sur un long run. Ce serait un
resultat, pas un echec — il faudrait alors chercher ailleurs, et le declin resterait ouvert.
"""
import sys, time
sys.path.insert(0, "/home/younes/arma3-marl")
from pont import Pont
from para import instance

COMPTEUR = '''
[] spawn {
  private _k = 0;
  while { true } do {
    _k = _k + 1;
    diag_log format ["[ECHP] JAUGE %1 unites=%2 groupes=%3 morts=%4 objets=%5 fps=%6",
      _k, count allUnits, count allGroups, count allDead, count (entities ""), diag_fps];
    sleep 60;
  };
};
'''

inst = instance(2)
p = Pont(inst["profil"], pont_dir=inst["pont"], patience_sync=60)
if p.attendre("ETAT PRET", 90) is None:
    print("la mission ne dit jamais PRET"); sys.exit(2)
p.envoyer(COMPTEUR)
l = p.attendre("[ECHP] JAUGE", 20)
print("compteur injecte :", l.strip() if l else "SILENCE — le compteur n'a pas demarre")
p.fermer()
