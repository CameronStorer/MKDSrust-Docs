"""lead.py A B from to [regions]: for each offset d, how many A frames f in [from,to] have A[f]==B[f-d] in the regions."""
import sys, importlib.util
spec=importlib.util.spec_from_file_location('rc','C:/Users/cam/dev/wt/b5-finish/4_docs/masks/region_cmp.py')
import struct, os
def load(d):
    names=[l.split(',')[1] for l in open(os.path.join(d,'regions.csv')).read().splitlines()[1:]]
    b=open(os.path.join(d,'frames.bin'),'rb').read(); n=struct.unpack_from('<I',b,8)[0]; size=16+8*n; fr={}
    for o in range(12,len(b)-size+1,size):
        lf=struct.unpack_from('<I',b,o)[0]; fr[lf]=struct.unpack_from('<%dQ'%n,b,o+16)
    return names,fr
na,A=load(sys.argv[1]); nb,B=load(sys.argv[2]); lo,hi=int(sys.argv[3]),int(sys.argv[4])
regs=(sys.argv[5] if len(sys.argv)>5 else 'kart0,race_manager,object_rng').split(',')
ks=[na.index(r) for r in regs]
best=[]
for d in range(-20,800):
    c=sum(1 for f in range(lo,hi) if f in A and f-d in B and all(A[f][k]==B[f-d][k] for k in ks))
    best.append((c,d))
best.sort(reverse=True); print(best[:5])
