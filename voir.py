import re,pathlib
F='/mnt/data/harmattan-sandbox/logs/serverAP.out'
pat = re.compile(r'HMT\|AP\|essai\|(\d+)\|(\d+)\|terrain\|(-?\d+)\|delivre\|(\d+)\|armes\|(\d+)'
                 r'\|cap0\|([\d,]+)\|cap1\|([\d,]+)\|coupsdef\|(\d+)\|coupsapp\|(\d+)'
                 r'\|murs\|(\d+)\|corps\|(\d+)')
E=[]
for L in open(F,encoding='utf-8',errors='ignore'):
    m=pat.search(L)
    if m:
        b,r,te,dl,ar,c0,c1,cd,ca,mu,co=m.groups()
        E.append((int(b),int(r),int(te),int(dl),int(cd),int(ca),int(mu)))
E=[e for e in E if e[1]>0]
noms={0:'temoin',1:'scripte',2:'natif'}
def moy(v): return sum(v)/len(v) if v else 0
print("  %-9s%-10s%9s%10s%10s%8s" % ("terrain","bras","delivre","coupsdef","coupsapp","murs"))
for te in sorted(set(e[2] for e in E)):
    for b in (0,1,2):
        g=[e for e in E if e[2]==te and e[0]==b]
        print("  %-9d%-10s%9.0f%10.0f%10.0f%8.0f   n=%d" % (te,noms[b],moy([x[3] for x in g]),
              moy([x[4] for x in g]),moy([x[5] for x in g]),moy([x[6] for x in g]),len(g)))
    print()
print("  essais TEMOIN a zero delivre :")
for e in E:
    if e[0]==0 and e[3]==0: print("    terrain %d rep %d : coupsdef %d" % (e[2],e[1],e[4]))
