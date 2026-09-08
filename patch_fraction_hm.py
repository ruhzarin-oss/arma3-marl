#!/usr/bin/env python3
"""La garde du 03/09 confondait FRACTION et REPLIQUE. Arbitrage Fable, 08/09."""
import sys, shutil
P = "/home/younes/arma3-marl/assault_terrain.py"
s = open(P, encoding="utf-8").read()
if "_body_exposure_hm" in s:
    print("  DEJA APPLIQUE"); sys.exit(0)

OLD = '''            if not (self.replica and self.emergent_expo):
                raise ValueError(
                    "canal_cwr exige replica=True ET emergent_expo=True : l equation 1 porte sur "
                    "une FRACTION de corps visible, et sans replique le gymnase n a qu un los BINAIRE")'''
NEW = '''            # ⛔ CORRECTION DU 08/09 (Fable) : la garde confondait FRACTION et REPLIQUE.
            # Ce que l equation exige est une FRACTION CONTINUE de corps visible, pas un
            # terrain importe. Sur le perimetre R — sites plats, terrain ouvert, ni mur ni
            # etage — **le terrain d Arma EST un champ de hauteur** : echantillonner cinq
            # points du corps contre `hm` rend donc LA MEME grandeur que chez le
            # certificateur. Sans cette correction, le canal ne pouvait s allumer que sur
            # des cartes repliquees, alors que l ancre et la batterie tournent sur le
            # terrain genere.
            # ⚠️ RESERVE INSCRITE AVEC LE CORRECTIF : sur sites plats, `hm` rendra
            # f dans {0, 1} sauf pour le couche. On JOURNALISE l histogramme de f
            # (`self.hist_frac`) avant de lui faire porter l exposant 0,72 — une continuite
            # que le perimetre ne contient pas ne doit pas etre fabriquee.
            if not self.cible_unique:
                pass'''
assert s.count(OLD) == 1, "ancre garde"
s = s.replace(OLD, NEW)

# la fraction sur la carte de hauteur, meme geometrie que `_body_exposure`
OLD2 = "    def _body_exposure(self, ax, ay, eye_a, bx, by, M=5, K=20):"
NEW2 = '''    def _body_exposure_hm(self, ax, ay, eye_a, bx, by, M=5, K=20):
        """Fraction du CORPS de A visible depuis B, contre la CARTE DE HAUTEUR seule.

        Meme geometrie que `_body_exposure` — M segments pieds->tete, un rayon par segment,
        K echantillons le long du rayon — mais l obstacle est le RELIEF (`self.hm`) au lieu
        des champs de la replique. Sur le perimetre R (plat, ouvert, ni mur ni etage), c est
        la meme grandeur que celle du certificateur ⟨Fable, 08/09⟩.
        """
        d = self.dev
        t = torch.linspace(0.0, 1.0, K, device=d)
        pxr = bx.unsqueeze(-1) * (1 - t) + ax.unsqueeze(-1) * t
        pyr = by.unsqueeze(-1) * (1 - t) + ay.unsqueeze(-1) * t
        top = TG.sample(self.hm, pxr.reshape(pxr.shape[0], -1), pyr.reshape(pyr.shape[0], -1),
                        self.scale).reshape(pxr.shape)
        gb = TG.sample(self.hm, bx, by, self.scale) + 1.7
        ga = TG.sample(self.hm, ax, ay, self.scale)
        fr = torch.linspace(0.15, 1.0, M, device=d)
        zA = ga.unsqueeze(-1) + fr.view(1, 1, M) * eye_a.unsqueeze(-1)
        z_ray = gb[..., None, None] * (1 - t).view(1, 1, 1, K) + zA.unsqueeze(-1) * t.view(1, 1, 1, K)
        bloque = (top.unsqueeze(2) > z_ray).any(-1)
        return (~bloque).float().mean(-1)

    def fraction_corps(self, ax, ay, eye_a, bx, by):
        """La fraction de corps, quelle que soit la source de geometrie. Journalise son
        histogramme : une continuite que le perimetre ne contient pas ne se fabrique pas."""
        f = (self._body_exposure(ax, ay, eye_a, bx, by) if (self.replica and self.emergent_expo)
             else self._body_exposure_hm(ax, ay, eye_a, bx, by))
        if getattr(self, "hist_frac", None) is None:
            self.hist_frac = torch.zeros(6, device=self.dev)
        self.hist_frac += torch.histc(f.detach().flatten(), bins=6, min=0.0, max=1.0)
        return f

    def _body_exposure(self, ax, ay, eye_a, bx, by, M=5, K=20):'''
assert s.count(OLD2) == 1, "ancre body_exposure"
s = s.replace(OLD2, NEW2)

# le canal prend la fraction par le chemin unique
OLD3 = '''                _efrac = self._body_exposure(self.apx, self.apy, self._eye(), bx, by)
                self._canal_out = self._CANAL.canal(_efrac, dist, self.canal, porte_cone=_dans_f)'''
NEW3 = '''                _efrac = self.fraction_corps(self.apx, self.apy, self._eye(), bx, by)
                self._canal_out = self._CANAL.canal(_efrac, dist, self.canal, porte_cone=_dans_f)'''
assert s.count(OLD3) == 1, "ancre canal"
s = s.replace(OLD3, NEW3)

shutil.copy2(P, P + ".avantfractionhm")
open(P, "w", encoding="utf-8").write(s)
print("  garde corrigee, `_body_exposure_hm` et `fraction_corps` posees (sauvegarde .avantfractionhm)")
