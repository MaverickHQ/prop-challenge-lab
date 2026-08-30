"""Is the setup zero-information, or does it carry signal that costs eat?"""
import pandas as pd, numpy as np
from zoneinfo import ZoneInfo
ET=ZoneInfo("America/New_York"); K,RISK,CAP=0.2,175.0,30
SPEC={"MES":(5.0,0.25,1.25),"MNQ":(2.0,0.25,1.25)}
def load(i):
    df=pd.read_csv(f"data/{i}.csv",usecols=["ts_event","open","high","low","close"])
    df["ts"]=pd.to_datetime(df["ts_event"],utc=True).dt.tz_convert(ET)
    hm=df["ts"].dt.hour*60+df["ts"].dt.minute
    df=df[(hm>=570)&(hm<960)]; df["d"]=df["ts"].dt.date; return df
def size(p,m,c,t): return min(int(RISK//((p+2*t)*m+2*c)),CAP)
for inst in ("MES","MNQ"):
    mult,tick,comm=SPEC[inst]; df=load(inst); F=[];S=[]
    for d,g in df.groupby("d",sort=True):
        hm=g["ts"].dt.hour*60+g["ts"].dt.minute
        rb=g[(hm>=570)&(hm<585)]
        if len(rb)<15: continue
        hi,lo=rb["high"].max(),rb["low"].min(); h=hi-lo
        if h<=0: continue
        s=g[hm>=585]
        if s.empty: continue
        H,L,C=s["high"].to_numpy(),s["low"].to_numpy(),s["close"].to_numpy()
        bi=next((i for i in range(len(s)) if H[i]>hi or L[i]<lo),None)
        if bi is None: continue
        up=H[bi]>hi
        fi=next((i for i in range(bi,len(s)) if (C[i]<hi if up else C[i]>lo)),None)
        if fi is None: continue
        ext=H[bi:fi+1].max() if up else L[bi:fi+1].min()
        b=hi if up else lo; hgt=h
        # --- FADE: against the break, entry at boundary
        fs=-1.0 if up else 1.0
        fstop=b-fs*((ext-hi if up else lo-ext)+K*h); ftgt=b+fs*hgt
        n=size(abs(fstop-b),mult,comm,tick)
        e0=next((i for i in range(fi+1,len(s)) if (L[i]<=b if fs>0 else H[i]>=b)),None)
        if n>=1 and e0 is not None and e0+1<len(s):
            ex=C[-1]
            for i in range(e0+1,len(s)):
                if (L[i]<=fstop if fs>0 else H[i]>=fstop): ex=fstop; break
                if (H[i]>=ftgt if fs>0 else L[i]<=ftgt): ex=ftgt; break
            F.append((n*(ex-b)*fs*mult, n*2*comm))
        # --- SECOND PUSH: with the break, entry at the fade's stop
        sg=1.0 if up else -1.0
        trig=ext+sg*K*h; sstop=b; stgt=trig+sg*hgt
        n2=size(abs(trig-sstop),mult,comm,tick)
        e2=next((i for i in range(fi+1,len(s)) if (H[i]>=trig if up else L[i]<=trig)),None)
        if n2>=1 and e2 is not None and e2+1<len(s):
            ex=C[-1]
            for i in range(e2+1,len(s)):
                if (L[i]<=sstop if up else H[i]>=sstop): ex=sstop; break
                if (H[i]>=stgt if up else L[i]<=stgt): ex=stgt; break
            S.append((n2*(ex-trig)*sg*mult, n2*2*comm))
    print(f"\n=== {inst} ===")
    for nm,arr in (("fade (against)",F),("second push (with)",S)):
        if not arr: continue
        g_=np.array([x[0] for x in arr]); c_=np.array([x[1] for x in arr])
        print(f"  {nm:<20} n={len(arr):>5}  GROSS {g_.mean()/RISK:>+7.3f}R  "
              f"costs {-c_.mean()/RISK:>+7.3f}R  NET {(g_-c_).mean()/RISK:>+7.3f}R")
