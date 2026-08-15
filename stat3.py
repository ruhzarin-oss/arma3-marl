import math
def fisher(a,b,c,d):
    """table 2x2 : [[a,b],[c,d]] — p bilateral exact"""
    from math import comb
    n = a+b+c+d; r1 = a+b; c1 = a+c
    def pr(x): return comb(r1,x)*comb(n-r1,c1-x)/comb(n,c1)
    p0 = pr(a); lo = max(0, c1-(n-r1)); hi = min(r1, c1)
    return sum(pr(x) for x in range(lo,hi+1) if pr(x) <= p0 + 1e-12)
def ic(k,n):
    p = k/n; s = 1.96*math.sqrt(p*(1-p)/n)
    return max(0,p-s), min(1,p+s)

print("─── LA REPARATION DU CORPS EST-ELLE ETABLIE ? ───")
print("  serie 2 (corps bride)  : 0 prise sur 20")
print("  serie 3 (corps repare) : 3 prises sur 20")
p = fisher(0,20,3,17)
print(f"  Fisher exact bilateral : p = {p:.3f}  →  " +
      ("ETABLI" if p < 0.05 else "NON ETABLI — l ecart tient au hasard a ce n"))
print(f"  il faudrait ~{math.ceil(3*(1.96+0.84)**2/ (3/20) /20)*0 or 60} episodes par bras pour trancher un ecart de cette taille\n")

print("─── L ECART AU GYMNASE SUBSISTE-T-IL ? ───")
lo, hi = ic(3,20)
print(f"  Arma    : 3/20 = 15,0 %   IC95 [{100*lo:.1f} ; {100*hi:.1f}]")
print(f"  gymnase : 59,4 %")
print(f"  59,4 % dans l intervalle d Arma ? " + ("OUI" if lo <= 0.594 <= hi else "NON — l ecart de transfert TIENT"))
p2 = fisher(3,17,int(round(0.594*256)),256-int(round(0.594*256)))
print(f"  Fisher contre le gymnase (n=256) : p = {p2:.2e}")

print("\n─── LE PRIX DE LA VITESSE ───")
print("  serie 2 : 9/20 tous morts, 11/20 survivent 60 pas sans prendre")
print("  serie 3 : 17/20 tous morts, 3/20 prennent, 1/20 survit 60 pas")
p3 = fisher(9,11,17,3)
print(f"  plus de morts ? Fisher p = {p3:.3f}  →  " + ("ETABLI" if p3 < 0.05 else "non etabli"))
print("  ⇒ le corps repare fait ARRIVER et fait MOURIR. C etait la reserve deposee avant mesure.")
