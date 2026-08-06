#!/usr/bin/env python3
"""hors_cone.py — Y AVAIT-IL UN FLANC ?

⟨Fable, 06/08 : « si le crochet ne sort jamais des cones, la sandbox n a pas rendu un verdict
 faux — elle a rendu un verdict JUSTE sur un monde MAL POSE. »⟩

Le flanc certifie sur Arma a ete mesure contre une LIGNE de defenseurs avec des arcs orientes
(banc FIBUA). Notre sandbox pose 6,5 defenseurs a des azimuts ALEATOIRES : leur couverture est
presque circulaire. Dans un cercle, il n y a pas de dos.

ON MESURE DONC, avant toute autre chose :
  1. la part du trajet passee HORS DE TOUT CONE, pour la droite et pour le crochet ;
  2. la geometrie du scenario : les azimuts des defenseurs couvrent-ils tout le tour ?

CRITERE, ecrit avant de lancer :
  - si le crochet ne gagne pas au moins 10 POINTS de part hors-cone sur la droite, alors il n a
    RIEN ACHETE, et le verdict de la PORTE 0 juge le SCENARIO, pas l instrument ;
  - si les azimuts des defenseurs couvrent plus de 270 degres de tour d horizon en mediane,
    la configuration n a PAS de flanc et ne peut pas reproduire la condition certifiee.
"""
import sys, math, numpy as np, torch

sys.argv = [sys.argv[0]]
src = open('/home/younes/arma3-marl/agent_complet.py', encoding='utf-8').read()
h = {'__name__': '__horscone__'}
exec(compile(src[:src.index("def percevoir")], 'agent_complet.py', 'exec'), h)
t = h['torch']; dev = h['dev']
POS, AZI, MSK, NC = h['POS'], h['AZI'], h['MSK'], h['NC']
ALLURES, POSTURES_V, CHAMP = h['ALLURES'], h['POSTURES_V'], h['CHAMP']

B, NPAS, PORTEE = 2048, 80, 400.0
t.manual_seed(0)
idx = t.randint(0, NC, (B,), device=dev)


def trajet(mode):
    ang = t.rand(B, device=dev) * 2 * math.pi
    p = t.stack([t.sin(ang), t.cos(ang)], -1) * 250.0
    cote = None
    hors, total = t.zeros(B, device=dev), t.zeros(B, device=dev)
    for _ in range(NPAS):
        v = p.unsqueeze(1) - POS[idx]
        d = v.norm(dim=-1)
        gis = t.rad2deg(t.atan2(v[..., 0], v[..., 1])) % 360
        ec = ((gis - AZI[idx] + 180) % 360 - 180).abs()
        dans = ((MSK[idx] > 0.5) & (ec < CHAMP) & (d < PORTEE)).any(dim=1)
        vivant = (p.norm(dim=-1) > 40.0).float()
        hors = hors + (~dans).float() * vivant
        total = total + vivant
        vers = -p / p.norm(dim=-1, keepdim=True).clamp(min=1e-6)
        if mode == 'crochet':
            perp = t.stack([-vers[..., 1], vers[..., 0]], -1)
            if cote is None:
                post = t.zeros(B, dtype=t.long, device=dev)
                rg = h['risque'](p + perp * 100.0, post, idx)
                rd = h['risque'](p - perp * 100.0, post, idx)
                cote = t.where(rg < rd, 1.0, -1.0).unsqueeze(-1)
            w = ((p.norm(dim=-1, keepdim=True) - 90.0) / 160.0).clamp(0, 1)
            dr = vers + perp * cote * w * 1.2
            dr = dr / dr.norm(dim=-1, keepdim=True).clamp(min=1e-6)
        else:
            dr = vers
        p = p + dr * ALLURES[2] * POSTURES_V[0] * vivant.unsqueeze(-1)
    return (hors / total.clamp(min=1)).mean().item()


print("\n" + "=" * 74)
print("  1. LA PART DU TRAJET PASSÉE HORS DE TOUT CÔNE")
print("  " + "-" * 72)
h_dr, h_cr = trajet('droite'), trajet('crochet')
print(f"     DROITE    {h_dr:6.1%} du trajet hors de tout cône")
print(f"     CROCHET   {h_cr:6.1%}")
print(f"     le crochet achète {h_cr - h_dr:+.1%}   (exige >= +10 points pour avoir ACHETÉ)")
achete = (h_cr - h_dr) >= 0.10

print("\n" + "=" * 74)
print("  2. LA GÉOMÉTRIE DU SCÉNARIO — y a-t-il un dos ?")
print("  " + "-" * 72)
# pour chaque configuration : quelle part du tour d horizon est couverte par au moins un cone ?
tours = []
pas = t.arange(0, 360, 5.0, device=dev)
for i in range(0, min(NC, 400)):
    m = MSK[i] > 0.5
    if m.sum() == 0:
        continue
    a = AZI[i][m]
    ec = ((pas.unsqueeze(1) - a.unsqueeze(0) + 180) % 360 - 180).abs()
    couvert = (ec < CHAMP).any(dim=1).float().mean().item()
    tours.append(couvert * 360.0)
tours = np.array(tours)
med = float(np.median(tours))
print(f"     défenseurs par configuration : {MSK.sum(1).mean().item():.1f}")
print(f"     tour d'horizon couvert par au moins un cône : médiane {med:.0f}°"
      f"  (min {tours.min():.0f}° · max {tours.max():.0f}°)")
print(f"     configurations couvrant plus de 270° : {(tours > 270).mean():.1%}")
sans_flanc = med > 270

print("\n" + "=" * 74)
if not achete and sans_flanc:
    print("  LE SCÉNARIO N'A PAS DE FLANC. Les défenseurs couvrent presque tout le tour, et le")
    print("  crochet n'achète pas de temps hors des cônes. La PORTE 0 de ce soir jugeait donc")
    print("  LE SCÉNARIO, pas l'instrument — et la sandbox disait vrai : dans un cercle, il")
    print("  n'y a pas de dos. À rejouer sur la géométrie certifiée : LIGNE + arcs orientés.")
elif not achete:
    print("  LE CROCHET N'ACHÈTE RIEN, alors que la configuration laisse un flanc. Le problème")
    print("  est alors dans la DOCTRINE scriptée, pas dans le scénario.")
else:
    print("  LE CROCHET ACHÈTE BIEN DU TEMPS HORS DES CÔNES, et il perd quand même. Mon")
    print("  hypothèse tombe : le scénario avait un flanc, et le contourner ne paie pas ici.")
print("  " + "=" * 72)
