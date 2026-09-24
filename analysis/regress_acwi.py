"""全世界株式（オルカン相当）の円建てリターンは予測できるのか。

regress.py は S&P500 を対象にしていた。新興国データが入ったので、NISAで実際に
買われている「オルカン（MSCI ACWI）相当」の配分そのもので同じ検証をやり直す。
新興国は1990年開始なので、標本は1990〜2025年の36年に縮む。
"""
import numpy as np, pandas as pd, warnings
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson
from build_dataset import build, ensure_shiller
from common import LABEL, maker, fit, oos_r2
warnings.filterwarnings("ignore")

LO, HI = 1990, 2025
df = build(ensure_shiller())
make = maker(df)
s = df.loc[LO:HI]

print("#"*78)
print("# 全世界株式（オルカン相当 65/23/12）の円建てリターンの重回帰分析")
print(f"# 標本 {LO}–{HI}（新興国データが1990年開始のため）")
print("#"*78)

print("\n" + "="*78)
print(f"【0】まず素性  {LO}–{HI} 円建て")
print("-"*78)
print(f"{'系列':<26}{'年率':>9}{'標準偏差':>10}{'最悪の年':>12}{'マイナス年':>11}")
for nm, c in [("全世界(65/23/12)","ACWI_JPY"), ("米国(S&P500)","STK_JPY"),
              ("先進国ex US","EXUS_JPY"), ("新興国","EM_JPY")]:
    v = (s[c]/100).dropna()
    gm = (1+v).prod()**(1/len(v))-1
    lo = v.idxmin()
    print(f"{nm:<26}{gm*100:>8.2f}%{v.std()*100:>9.1f}%"
          f"{v.min()*100:>9.1f}% ({lo}){v.lt(0).sum():>6} / {len(v)}年")

PRED = ["EY","DY","GS10","TERM","INFL","FXCHG","ACWI_JPY"]
dA = make("ACWI_JPY", PRED, lo=LO)
mA = fit(dA, PRED, 1, "【モデルA】翌年の円建て全世界リターン ← 年末時点で分かっている情報すべて")

PRED_S = ["EY","DY","GS10","TERM","INFL","FXCHG","STK_JPY"]
dB = make("STK_JPY", PRED_S, lo=LO)
mB = fit(dB, PRED_S, 1, "【モデルB】比較：同じ期間で米国(S&P500)だけを対象にした場合")

dC = make("ACWI_JPY", ["EY","TERM","FXCHG"], lo=LO)
mC = fit(dC, ["EY","TERM","FXCHG"], 1, "【モデルC】絞り込み：CAPE益回り・期間スプレッド・為替の3つだけ")

PRED_E = ["EY","TERM","FXCHG","EM"]
dD = make("ACWI_JPY", PRED_E, lo=LO)
mD = fit(dD, PRED_E, 1, "【モデルD】当年の新興国リターンは翌年の手がかりになるか")

dE = make("ACWI_JPY", ["EY","DY","GS10"], h=10, lo=LO)
mE = fit(dE, ["EY","DY","GS10"], 10,
         "【モデルE】その後10年の年率リターン ※重複標本・Newey-West 10次")
print(f"  ※ n={len(dE)} の10年重複なので独立な観測は実質 {len(dE)/10:.1f} 個。ほぼ情報がない。")

print("\n" + "="*78)
print(f"【分散分解その1】円建てリターンのばらつき＝ドル建て分 ＋ 為替分  {LO}–{HI}")
print("-"*78)
U, F = np.log1p(s["ACWI"]/100), np.log1p(s["FXCHG"]/100)
vU, vF, cv = U.var(), F.var(), np.cov(U, F)[0,1]; vJ = vU+vF+2*cv
for nm, val in [("全世界株そのもの", vU), ("為替そのもの", vF), ("両者の共分散×2", 2*cv)]:
    print(f"  {nm:<18}{val/vJ*100:>7.1f}%")
print(f"  {'合計':<18}{100.0:>7.1f}%   （円建ての年率標準偏差 {np.sqrt(vJ)*100:.1f}%）")
print(f"  全世界株とドル円の相関 = {np.corrcoef(U,F)[0,1]:+.3f}")

print("\n" + "="*78)
print("【分散分解その2】ドル建て部分の中で、どの地域がリスクを持ち込んでいるか")
print("-"*78)
W = {"STK":0.65, "EXUS":0.23, "EM":0.12}
R = s[list(W)]/100
Rp = sum(W[c]*R[c] for c in W)
vP = Rp.var()
print(f"{'資産':<16}{'配分':>7}{'単体の標準偏差':>15}{'リスク寄与':>11}")
for c, nm in [("STK","米国"), ("EXUS","先進国ex US"), ("EM","新興国")]:
    contrib = W[c]*np.cov(R[c], Rp)[0,1]/vP
    print(f"{nm:<16}{W[c]*100:>6.0f}%{R[c].std()*100:>14.1f}%{contrib*100:>10.1f}%")
print(f"  ドル建てポートフォリオの標準偏差 {np.sqrt(vP)*100:.1f}%")
print("  ※リスク寄与＝配分×そのポートフォリオとの共分散÷分散。合計100%になる。")

print("\n" + "="*78)
print(f"【標本外検証】2006年以降を1年ずつ予測。過去平均に勝てるか")
print("-"*78)
for nm, tgt, pr in [("全世界・全部入り(7変数)","ACWI_JPY",PRED),
                    ("全世界・絞り込み(3変数)","ACWI_JPY",["EY","TERM","FXCHG"]),
                    ("全世界・CAPE益回りだけ","ACWI_JPY",["EY"]),
                    ("米国・全部入り(7変数)","STK_JPY",PRED_S)]:
    r, n = oos_r2(make, tgt, pr, 2006, lo=LO)
    print(f"  {nm:<24} 標本外R2 = {r:+.3f}  （n={n}） "
          f"{'← 過去平均に負け' if r<0 else '← 過去平均に勝ち'}")

print("\n" + "="*78)
print("【モデルDの検証】新興国リターンの符号(-0.244, p=0.013)は本物か")
print("-"*78)

d1 = make("ACWI_JPY", ["EM"], lo=LO)
m1 = sm.OLS(d1["y"], sm.add_constant(d1[["EM"]])).fit(cov_type="HAC", cov_kwds={"maxlags":1})
print(f"  単変数だけ:         係数={m1.params['EM']:+.3f}  p={m1.pvalues['EM']:.3f}  "
      f"R2={m1.rsquared:.3f}")

mD_ols = sm.OLS(dD["y"], sm.add_constant(dD[PRED_E])).fit()
cook = mD_ols.get_influence().cooks_distance[0]
top = pd.Series(cook, index=dD.index).nlargest(4)
print("\n  Cookの距離が大きい年（1つの年がどれだけ結果を動かしているか）:")
for y, c in top.items():
    print(f"    {int(y)}年  D={c:.3f}   その年の新興国リターン {dD.loc[y,'EM']:+.1f}%  "
          f"翌年の全世界 {dD.loc[y,'y']:+.1f}%")

print("\n  影響の大きい年を外すとどうなるか:")
for drop in [[int(top.index[0])], list(map(int, top.index[:2])), [2008, 2009], [1993]]:
    dd = dD.drop(index=drop)
    mm = sm.OLS(dd["y"], sm.add_constant(dd[PRED_E])).fit(cov_type="HAC", cov_kwds={"maxlags":1})
    print(f"    {str(drop)+'を除外':<22} 係数={mm.params['EM']:+.3f}  p={mm.pvalues['EM']:.3f}  "
          f"n={int(mm.nobs)}" + ("  ← 有意性を失う" if mm.pvalues['EM'] >= 0.05 else ""))

r, n = oos_r2(make, "ACWI_JPY", PRED_E, 2006, lo=LO)
print(f"\n  標本外R2 = {r:+.3f}（n={n}） "
      f"{'← 過去平均に負け' if r<0 else '← 過去平均に勝ち'}")

print("\n" + "="*78)
print("注：*** p<0.01  ** p<0.05  * p<0.1。標準誤差はNewey-West。")
print(f"　　標本は{len(dA)}年しかなく、説明変数7個に対して余裕がない。")
print("　　regress.py の1972–2024（n=53）と比べて、係数はいっそう当てにならない。")
