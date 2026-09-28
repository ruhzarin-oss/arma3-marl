"""PORTE DE LA FAIM DES MORTS ( HMT-136, 28/09 ). Seuils ecrits avant la mesure.

  M1  un menage dont tous les membres meurent de FAIM compte non nourri le soir suivant ( nourri_menage faux ), et la
      faim des essais ( T.faim ) le compte affame : elle MONTE au lieu de baisser ;
  M2  controle : un menage dont tous les membres meurent d une autre cause ( naturelle ) reste neutre ( nourri vrai ) ;
  M3  la version Python du repas et la version en colonnes rendent le meme verdict sur ces menages ;
  M4  controle positif : sans le correctif ( _eteints_par_la_faim neutralise ), M1 echoue : le menage mort de faim
      compte nourri et la faim baisse.

  Corrige apres la premiere mesure ( 28/09, 10 h 45 ), sur l ESSAI et non sur le critere : M1 demandait « au moins 2
  morts de faim comptes » dans le menage. Il en compte 1, parce que les mineurs d un menage qui perd son dernier adulte
  sont places dans une autre famille ( d01._placer ) avant de mourir. Le critere du comportement ( non nourri, T.faim
  qui monte ) est inchange ; le compte demande est ramene a >= 1.

   python -m monde.porte_faim_des_morts"""
import sys
import numpy as np
from .pays import essais as T, d01_population as PO

GRAINE = 5


def _essai(neutraliser=False, python=False):
    w, p = T.monde(["population"], graine=GRAINE)
    T.jours(w, 2)
    mgs = [m for m in T.menages_habites(w) if 2 <= len([x for x in m.membres if x.vivant]) <= 4]
    faim_m, autre_m = mgs[0], mgs[1]
    f0 = T.faim(w)
    orig = type(w)._eteints_par_la_faim
    if neutraliser: type(w)._eteints_par_la_faim = lambda self, v: np.zeros(len(v), bool)
    if python: w.utiliser_coeur = False
    try:
        for h in [x for x in faim_m.membres if x.vivant]: PO.deceder(p, h, "faim")
        for h in [x for x in autre_m.membres if x.vivant]: PO.deceder(p, h, "naturelle")
        T.jours(w, 1)
        r = dict(nourri_faim=bool(w.nourri_menage.get(faim_m.id, True)), nourri_autre=bool(w.nourri_menage.get(autre_m.id, True)),
                 eteints=int(w.stats_jour.get("menages_eteints_faim", 0)), f0=f0, f1=T.faim(w),
                 morts_faim=int(p.col("menage", "morts_faim")[faim_m.id]))
    finally:
        type(w)._eteints_par_la_faim = orig
    return r


def main():
    ok_tout = True
    def dire(ok, texte):
        nonlocal ok_tout
        ok_tout &= bool(ok); print(f"{'PASSE ' if ok else 'ECHOUE'} {texte}", flush=True)
    c = _essai()
    dire(not c["nourri_faim"] and c["eteints"] >= 1 and c["morts_faim"] >= 1 and c["f1"] > c["f0"],
         f"M1 menage mort de faim : nourri={c['nourri_faim']}, eteints={c['eteints']}, morts de faim comptes={c['morts_faim']}, "
         f"faim des essais {c['f0']:.4f} -> {c['f1']:.4f}")
    dire(c["nourri_autre"], f"M2 menage mort d autre cause : nourri={c['nourri_autre']} ( neutre )")
    py = _essai(python=True)
    dire(py["nourri_faim"] == c["nourri_faim"] and py["nourri_autre"] == c["nourri_autre"] and py["eteints"] == c["eteints"],
         f"M3 repas Python : nourri faim={py['nourri_faim']}, autre={py['nourri_autre']}, eteints={py['eteints']} ( colonnes : {c['eteints']} )")
    s = _essai(neutraliser=True)
    dire(s["nourri_faim"] and s["eteints"] == 0,
         f"M4 controle positif, correctif neutralise : le menage mort de faim compte nourri={s['nourri_faim']} ( l ancien defaut revient )")
    print(f"PORTE DE LA FAIM DES MORTS : {'FRANCHIE' if ok_tout else 'REFUSEE'}")
    return 0 if ok_tout else 1


if __name__ == "__main__":
    sys.exit(main())
