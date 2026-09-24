"""回帰の共通部品。regress.py と regress_acwi.py が使う。"""
import numpy as np, warnings
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.stats.stattools import durbin_watson, jarque_bera
from statsmodels.stats.diagnostic import het_breuschpagan
warnings.filterwarnings("ignore")

LABEL = {"const":"切片","EY":"CAPE益回り(100/CAPE)","DY":"配当利回り","GS10":"米10年金利",
         "TERM":"期間スプレッド(10年-短期)","INFL":"インフレ率","FXCHG":"当年の為替変動(+=円安)",
         "STK_JPY":"当年の円建てリターン","STK":"当年のドル建てリターン",
         "ACWI_JPY":"当年の円建てリターン(全世界)","EM":"当年の新興国リターン",
         "EM_JPY":"当年の円建て新興国リターン"}

def maker(df):
    """t年末の説明変数で、t+h年（h>1なら t+1..t+h の年率）のリターンを説明する枠を作る。"""
    def make(target, preds, h=1, lo=1972, hi=2025):
        d = df.loc[lo:hi].copy()
        if h == 1:
            d["y"] = d[target].shift(-1)
        else:
            g = np.log1p(d[target]/100)
            d["y"] = 100*(np.expm1(g.rolling(h).sum().shift(-h)/h))
        return d[["y"]+preds].dropna()
    return make

def fit(data, preds, lags=1, title=""):
    X = sm.add_constant(data[preds]); y = data["y"]
    m = sm.OLS(y, X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    print("\n" + "="*78); print(title)
    print(f"標本 {int(data.index.min())}–{int(data.index.max())}  n={int(m.nobs)}  "
          f"説明変数{len(preds)}個")
    print("-"*78)
    print(f"{'変数':<28}{'係数':>10}{'HAC標準誤差':>13}{'t値':>8}{'p値':>8}")
    for k in m.params.index:
        star = "***" if m.pvalues[k]<0.01 else "**" if m.pvalues[k]<0.05 else "*" if m.pvalues[k]<0.1 else ""
        print(f"{LABEL.get(k,k):<28}{m.params[k]:>10.3f}{m.bse[k]:>13.3f}"
              f"{m.tvalues[k]:>8.2f}{m.pvalues[k]:>8.3f} {star}")
    print("-"*78)
    print(f"R2={m.rsquared:.3f}  自由度調整済R2={m.rsquared_adj:.3f}  "
          f"F={m.fvalue:.2f} (p={m.f_pvalue:.3f})  残差標準偏差={np.sqrt(m.scale):.1f}%")
    resid = m.resid
    bp = het_breuschpagan(resid, X)
    print(f"Durbin-Watson={durbin_watson(resid):.2f}  "
          f"Jarque-Bera p={jarque_bera(resid)[1]:.3f}  "
          f"Breusch-Pagan p={bp[1]:.3f}  条件数={np.linalg.cond(X.values):.0f}")
    if len(preds) > 1:
        v = [variance_inflation_factor(X.values, i) for i in range(1, X.shape[1])]
        print("VIF: " + "  ".join(f"{p}={x:.1f}" for p, x in zip(preds, v)))
    return m

def oos_r2(make, target, preds, start, lo=1972):
    """Campbell-Thompson の標本外R2。過去平均を基準にする。"""
    d = make(target, preds, lo=lo); e_m, e_h = [], []
    for t in range(start, int(d.index.max())+1):
        tr, te = d.loc[:t-1], d.loc[[t]]
        if len(tr) < 15: continue
        b = sm.OLS(tr["y"], sm.add_constant(tr[preds])).fit()
        p = float(b.predict(sm.add_constant(te[preds], has_constant="add")).iloc[0])
        e_m.append((te["y"].iloc[0]-p)**2)
        e_h.append((te["y"].iloc[0]-tr["y"].mean())**2)
    return (1 - np.sum(e_m)/np.sum(e_h), len(e_m)) if e_m else (float("nan"), 0)
