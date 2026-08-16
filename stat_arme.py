import math
from math import comb
def fisher(a,b,c,d):
    n=a+b+c+d; r1=a+b; c1=a+c
    pr=lambda x: comb(r1,x)*comb(n-r1,c1-x)/comb(n,c1)
    p0=pr(a); lo=max(0,c1-(n-r1)); hi=min(r1,c1)
    return sum(pr(x) for x in range(lo,hi+1) if pr(x)<=p0+1e-12)
print("─── L ARMEMENT A-T-IL CHANGE QUELQUE CHOSE ? ───")
print(f"  prise      : 8/67 desarmes contre 30/67 armes   Fisher p = {fisher(8,59,30,37):.2e}")
print(f"  mortalite  : 57/67 contre 27/67 aneantis        Fisher p = {fisher(57,10,27,40):.2e}")
print(f"  gel        : 17/67 contre 5/67 figes            Fisher p = {fisher(17,50,5,62):.3f}")
print("\n─── L ECART AU GYMNASE ───")
k,n=30,67; p=k/n; s=1.96*math.sqrt(p*(1-p)/n)
print(f"  Arma 44,8 %  IC95 [{100*(p-s):.1f} ; {100*(p+s):.1f}]   gymnase 59,4 %")
print(f"  59,4 dans l intervalle ? " + ("OUI" if p-s<=0.594<=p+s else "NON — mais de peu"))
g=int(round(0.594*256))
print(f"  Fisher contre le gymnase (n=256) : p = {fisher(30,37,g,256-g):.4f}")
