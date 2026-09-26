"""26/09 : la demande d un bien durable ( outils ) se lisse sur un mois, pas sur quatre jours. Idempotent.
   python patch_alpha.py chemin/d03_economie.py"""
import sys
p = sys.argv[1]; s = open(p).read()
if "ALPHA_DEMANDE_BIEN" in s: print("deja :", p); sys.exit(0)
a = "ALPHA_DEMANDE = 0.25            # demande lissee sur ~ 4 jours\n"
assert s.count(a) == 1, "constante introuvable"
s = s.replace(a, a + """# un bien durable s achete par a-coups ( un renouvellement d un coup, le meme jour pour beaucoup de menages ) : lisse
# sur quatre jours, le pic du jour 10 ( 109 millions d outils a Malden a un million d habitants ) devenait dix jours de
# stock a racheter, le marche et le negoce vidaient leur caisse en importations, et le carburant n etait plus achete
# ( faim au jour 16, 26/09 ). Comme un vrai commercant pour un bien durable : la demande se lit sur un mois
ALPHA_DEMANDE_BIEN = {"outils": 1.0 / 30.0}
""")
a = "            em.demande_lisse[b] = (1.0 - ALPHA_DEMANDE) * em.demande_lisse[b] + ALPHA_DEMANDE * m.demande[b]\n"
assert s.count(a) == 1, "lissage introuvable"
s = s.replace(a, """            al = ALPHA_DEMANDE_BIEN.get(b, ALPHA_DEMANDE)
            em.demande_lisse[b] = (1.0 - al) * em.demande_lisse[b] + al * m.demande[b]
""")
open(p, "w").write(s); print("corrige :", p)
