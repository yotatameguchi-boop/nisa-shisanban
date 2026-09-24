"""円建てNISA投資家から見た株式リターンの重回帰分析。

問い：CAPE・配当利回り・金利・インフレ・為替といった「その年末に分かっている情報」で、
翌年のリターンをどこまで説明できるのか。
"""
import numpy as np, pandas as pd, warnings, pathlib
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson
from build_dataset import build, ensure_shiller
from common import LABEL, maker, fit
warnings.filterwarnings("ignore")

HERE = pathlib.Path(__file__).parent
df = build(ensure_shiller())
make = maker(df)

PRED = ["EY","DY","GS10","TERM","INFL","FXCHG","STK_JPY"]
print("#"*78)
print("# 円建て株式リターンの重回帰分析")
print("# データ: S&P500配当込み(Damodaran) / MSCI World ex USA / ドル円年末(FRED)")
print("#         CAPE・配当利回り・米10年金利・CPI(Shiller, 2026年9月更新)")
print("#"*78)

d1 = make("STK_JPY", PRED)
m1 = fit(d1, PRED, 1, "【モデル1】翌年の円建てS&P500リターン ← 年末時点で分かっている情報すべて")

d2 = make("STK", ["EY","DY","GS10","TERM","INFL","FXCHG","STK"])
m2 = fit(d2, ["EY","DY","GS10","TERM","INFL","FXCHG","STK"], 1,
         "【モデル2】比較：翌年のドル建てS&P500リターン（同じ説明変数）")

d3 = make("STK_JPY", ["EY","TERM","FXCHG"])
m3 = fit(d3, ["EY","TERM","FXCHG"], 1, "【モデル3】絞り込み：CAPE益回り・期間スプレッド・為替の3つだけ")

d4 = make("STK_JPY", ["EY","DY","GS10"], h=10)
m4 = fit(d4, ["EY","DY","GS10"], 10,
         "【モデル4】その後10年の年率リターン（円建て）※重複標本・Newey-West 10次")

# ---- モデル4は本物か ----
print("\n" + "="*78)
print("【モデル4の検証】10年先のR2=0.36はどこから来たのか")
print("-"*78)
print("  単変数だけで回すと:")
for p_ in ["EY","DY","GS10","INFL","TERM"]:
    dd = make("STK_JPY", [p_], h=10)
    rr = sm.OLS(dd["y"], sm.add_constant(dd[[p_]])).fit()
    print(f"    {LABEL.get(p_,p_):<28} R2={rr.rsquared:.3f}  係数={rr.params[p_]:+.2f}")
cr = df.loc[1972:2025, ["EY","DY"]].corr().iloc[0,1]
print(f"\n  CAPE益回りと配当利回りの相関 = {cr:.3f}（ほぼ同じものを測っている）")
print(f"  重複標本のため、n={len(d4)} でも独立な観測は実質 {len(d4)/10:.1f} 個")
print(f"  Durbin-Watson={durbin_watson(m4.resid):.2f}（2から大きく外れる＝残差が強く連なっている）")
print("  → 単独では無力な2変数を符号逆で組み合わせて出た数字。過剰適合とみるのが妥当。")

# ---- 分散分解（対数なら厳密に加法的） ----
print("\n" + "="*78)
print("【分散分解】円建てリターンのばらつきは何で出来ているか  1972–2025")
print("-"*78)
s = df.loc[1972:2025]
U, F = np.log1p(s["STK"]/100), np.log1p(s["FXCHG"]/100)
vU, vF, cov = U.var(), F.var(), np.cov(U, F)[0,1]
vJ = vU + vF + 2*cov
for nm, val in [("米国株そのもの", vU), ("為替そのもの", vF), ("両者の共分散×2", 2*cov)]:
    print(f"  {nm:<16}{val/vJ*100:>7.1f}%")
print(f"  {'合計':<16}{100.0:>7.1f}%   （円建ての年率標準偏差 {np.sqrt(vJ)*100:.1f}%）")
print(f"  米国株とドル円の相関 = {np.corrcoef(U,F)[0,1]:+.3f}")

# ---- 標本外検証（Campbell-Thompson の OOS R2） ----
print("\n" + "="*78)
print("【標本外検証】1992年以降を1年ずつ予測。過去平均に勝てるか")
print("-"*78)
def oos(preds, start=1992):
    d = make("STK_JPY", preds); e_m, e_h = [], []
    for t in range(start, int(d.index.max())+1):
        tr, te = d.loc[:t-1], d.loc[[t]]
        if len(tr) < 15: continue
        b = sm.OLS(tr["y"], sm.add_constant(tr[preds])).fit()
        p = float(b.predict(sm.add_constant(te[preds], has_constant="add")).iloc[0])
        e_m.append((te["y"].iloc[0]-p)**2)
        e_h.append((te["y"].iloc[0]-tr["y"].mean())**2)
    return 1 - np.sum(e_m)/np.sum(e_h), len(e_m)
for nm, p in [("全部入り(7変数)", PRED), ("絞り込み(3変数)", ["EY","TERM","FXCHG"]), ("CAPE益回りだけ", ["EY"])]:
    r, n = oos(p)
    print(f"  {nm:<18} 標本外R2 = {r:+.3f}   （n={n}） {'← 過去平均に負け' if r<0 else '← 過去平均に勝ち'}")

pd.concat([d1.assign(fit=m1.fittedvalues)], axis=1).to_csv(HERE/"model1_fit.csv")
print("\n" + "="*78)
print("注：*** p<0.01  ** p<0.05  * p<0.1。標準誤差はNewey-West（系列相関・不均一分散に頑健）。")
