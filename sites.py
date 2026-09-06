#!/usr/bin/env python3
"""sites — LE TIRAGE DE SITE DU BARREAU « SITE DEGELE ».

Le bassin a ete decoupe par bassin_b1.py avec une graine de tirage DEDIEE (313131),
disjointe des graines de mission. Deux lots disjoints : jugement et apprentissage.
Le site gele du barreau certifie est exclu, et tout ce qui est a moins de 200 m de lui.
Bande de score >= 1,00 : le site gele score 1,32 et tombe DANS la bande, donc seule
l'identite du site varie, pas la difficulte.
"""
import json

def charger(lot):
    p = f"/home/younes/arma3-marl/sites_{lot}.jsonl"
    with open(p) as f:
        return [json.loads(l) for l in f]
