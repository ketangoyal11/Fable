# MINERVINI SEPA ANALYZER v1.0
# Usage: python _minervini_sepa.py TICKER
# Example: python _minervini_sepa.py NETWEB
import csv,sys,os
T=sys.argv[1].upper() if len(sys.argv)>1 else exit(print("Usage: python _minervini_sepa.py TICKER"))
D=os.path.join(os.path.dirname(__file__),"..","data")
def S(a,n,i):
  if i<n-1: return None
  return sum(a[i-n+1:i+1])/n
def A(t):
  fp=os.path.join(D,t+"_ohlcv.csv")
  if not os.path.exists(fp): print("Not found:",fp); return
  f=open(fp);r=csv.reader(f);h=next(r);rows=list(r);f.close()
  da=[x[0] for x in rows]; c=[float(x[2]) for x in rows]
  hh=[float(x[3]) for x in rows]; ll=[float(x[4]) for x in rows]
  o=[float(x[5]) for x in rows]; v=[int(x[6]) if x[6] else 0 for x in rows]
  print(t+": "+str(len(rows))+" sessions, "+da[0]+" to "+da[-1]); print()
  print("ALL CANDIDATES (VR>=1.3, Chg>=2%):")
  cans=[]
  for i in range(100,len(rows)):
    v50=S(v,50,i); vr=v[i]/v50 if v50 and v50>0 else 0
    pchg=(c[i]/c[i-1]-1)*100
    if vr>=1.3 and pchg>=2:
      s=max(0,i-20); pr=(max(hh[s:i])-min(ll[s:i]))/min(ll[s:i])*100
      uwl=[(hh[j]-max(o[j],c[j]))/(hh[j]-ll[j])*100 for j in range(max(0,i-10),i) if hh[j]-ll[j]>0]
      uw=sum(uwl)/max(1,len(uwl))
      cans.append((da[i],c[i],vr,pchg,pr,uw,i))
  # Classify
  for ca in cans:
    date,price,vr,chg,pr,uw,idx=ca
    p=[]
    h80=max(hh[max(0,idx-80):idx])
    rt=sum([1 for j in range(max(0,idx-80),idx-3) if hh[j]>=h80*0.97])
    shake=False; coil=False
    for j in range(max(0,idx-12),idx-1):
      rng=(hh[j]-ll[j])/c[j]*100; v50j=S(v,50,j); vrj=v[j]/v50j if v50j and v50j>0 else 0
      if rng>5 and vrj>2: shake=True
      if rng<3 and vrj<0.6: coil=True
    labels=[]
    if pr<=12 and uw<35: labels.append("TIGHT("+str(round(pr,1))+"%)")
    if rt>=2: labels.append(str(rt)+"X-RESIST")
    if shake: labels.append("SHAKE")
    if coil: labels.append("COIL")
    if not labels: labels.append("NO-PATTERN")
    print("  "+date+" C:"+str(int(price))+" VR:"+str(round(vr,1))+" Chg:"+str(round(chg,1))+"% -> "+" ".join(labels))
  print(); print("Total: "+str(len(cans)))
A(T)
