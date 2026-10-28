import sys
inp,out,th,d=sys.argv[1],sys.argv[2],int(sys.argv[3]),int(sys.argv[4])
L=open(inp).read().splitlines(); o=[L[0]]
for l in L[1:]:
    f=l.split(','); 
    if int(f[0])>=th: f[0]=str(int(f[0])-d)
    o.append(','.join(f))
open(out,'w').write('\n'.join(o)+'\n')
