"""全世界（オルカン相当）の回帰結果の作図。"""
import numpy as np, pandas as pd, warnings
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from build_dataset import build, ensure_shiller
from common import maker, oos_r2
warnings.filterwarnings("ignore")

plt.rcParams.update({
    "font.family": ["YuGothic","Hiragino Maru Gothic Pro","Arial Unicode MS"],
    "axes.edgecolor":"#b3bec9","axes.linewidth":.8,"axes.labelcolor":"#4a5560",
    "xtick.color":"#4a5560","ytick.color":"#4a5560","text.color":"#121a22",
    "axes.grid":True,"grid.color":"#dde3e9","grid.linewidth":.7,
    "figure.facecolor":"white","axes.facecolor":"white","font.size":10,
})
BLUE, ORANGE, AQUA, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#78838f"
LO, HI = 1990, 2025
df = build(ensure_shiller()); make = maker(df); s = df.loc[LO:HI]
PRED  = ["EY","DY","GS10","TERM","INFL","FXCHG","ACWI_JPY"]

fig, axes = plt.subplots(2, 2, figsize=(12.5, 9.5))

# (a) 予測 vs 実績
d = make("ACWI_JPY", PRED, lo=LO)
m = sm.OLS(d["y"], sm.add_constant(d[PRED])).fit()
ax = axes[0,0]; lim=[-60,70]
ax.plot(lim, lim, color=GREY, lw=1, ls="--", zorder=1)
ax.axhline(0,color=GREY,lw=.8); ax.axvline(0,color=GREY,lw=.8)
ax.scatter(m.fittedvalues, d["y"], s=44, color=BLUE, alpha=.85,
           edgecolor="white", linewidth=1.4, zorder=3)
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("モデルの予測値（％）"); ax.set_ylabel("実際の翌年リターン（％）")
ax.set_title(f"① 全世界でも1年先は予測できない\n7変数すべて使って R²={m.rsquared:.3f}、"
             f"自由度調整済 R²={m.rsquared_adj:.3f}", loc="left", fontsize=11.5, pad=10)

# (b) 当年の新興国 → 翌年の全世界
d2 = make("ACWI_JPY", ["EM"], lo=LO)
ax = axes[0,1]
b = sm.OLS(d2["y"], sm.add_constant(d2[["EM"]])).fit()
xs = np.linspace(d2["EM"].min(), d2["EM"].max(), 50)
ax.plot(xs, b.params["const"]+b.params["EM"]*xs, color=ORANGE, lw=2, zorder=2)
ax.axhline(0,color=GREY,lw=.8); ax.axvline(0,color=GREY,lw=.8)
ax.scatter(d2["EM"], d2["y"], s=46, color=BLUE, alpha=.85,
           edgecolor="white", linewidth=1.4, zorder=3)
p07 = d2.loc[2007]
ax.scatter([p07["EM"]],[p07["y"]], s=150, facecolor="none",
           edgecolor=ORANGE, linewidth=2.2, zorder=4)
ax.annotate("2007年→2008年\n（この1点の影響が最大）", (p07["EM"], p07["y"]),
            xytext=(-14,26), textcoords="offset points", fontsize=8.8, color=ORANGE,
            ha="right", linespacing=1.4)
ax.set_xlabel("その年の新興国リターン（％・ドル建て）")
ax.set_ylabel("翌年の全世界リターン（％・円建て）")
ax.set_title(f"② 唯一、標本外でも残った関係\n単変数で R²={b.rsquared:.3f}、係数 "
             f"{b.params['EM']:+.3f}（新興国が上げた翌年は下がりやすい）",
             loc="left", fontsize=11.5, pad=10)

# (c) 地域別リスク寄与
W = {"STK":0.65,"EXUS":0.23,"EM":0.12}
R = s[list(W)]/100; Rp = sum(W[c]*R[c] for c in W); vP = Rp.var()
names = [("米国","STK",BLUE),("先進国ex US","EXUS",AQUA),("新興国","EM",ORANGE)]
ax = axes[1,0]; y = np.arange(3)
wts  = [W[c]*100 for _,c,_ in names]
cont = [W[c]*np.cov(R[c],Rp)[0,1]/vP*100 for _,c,_ in names]
ax.barh(y+.19, wts,  height=.34, color=[c for _,_,c in names], alpha=.42,
        edgecolor="white", linewidth=1.5)
ax.barh(y-.19, cont, height=.34, color=[c for _,_,c in names],
        edgecolor="white", linewidth=1.5)
for i,(w,c) in enumerate(zip(wts,cont)):
    ax.text(w+1.2, i+.19, f"配分 {w:.0f}%", va="center", fontsize=9, color=GREY)
    ax.text(c+1.2, i-.19, f"リスク寄与 {c:.1f}%", va="center", fontsize=9.5,
            color="#121a22", fontweight="bold")
ax.set_yticks(y); ax.set_yticklabels([n for n,_,_ in names])
ax.set_xlim(0,78); ax.set_xlabel("％"); ax.invert_yaxis()
ax.set_title("③ 新興国は配分12％に対しリスク寄与15.1％\n単体の標準偏差は30.6％もあるのに、"
             "連動しないぶん薄まる", loc="left", fontsize=11.5, pad=10)

# (d) 標本外の累積比較
ax = axes[1,1]
for nm, preds, col in [("7変数", PRED, ORANGE),
                       ("CAPE益回りだけ", ["EY"], BLUE),
                       ("当年の新興国リターン", ["EM"], AQUA)]:
    dd = make("ACWI_JPY", preds, lo=LO); ys, dif = [], []
    for t in range(2006, int(dd.index.max())+1):
        tr, te = dd.loc[:t-1], dd.loc[[t]]
        bb = sm.OLS(tr["y"], sm.add_constant(tr[preds])).fit()
        pv = float(bb.predict(sm.add_constant(te[preds], has_constant="add")).iloc[0])
        a = te["y"].iloc[0]
        dif.append((a-tr["y"].mean())**2 - (a-pv)**2); ys.append(t)
    ax.plot(ys, np.cumsum(dif), lw=2, color=col)
    ax.annotate(nm, (ys[-1], np.cumsum(dif)[-1]), xytext=(6,0),
                textcoords="offset points", fontsize=9.5, color=col, va="center")
ax.axhline(0, color="#121a22", lw=1.2)
ax.set_xlim(2005, 2032)
ax.set_xlabel("予測した年"); ax.set_ylabel("累積二乗誤差の差（過去平均 − モデル）")
ax.set_title("④ 0より上なら過去平均に勝っている\n新興国リターン(+0.068)とCAPE益回り(+0.017)。"
             "7変数は大敗(-0.691)", loc="left", fontsize=11.5, pad=10)

fig.suptitle("全世界株式（オルカン相当 65/23/12）の重回帰分析　1990–2025年",
             fontsize=15, x=.055, ha="left", y=.985)
fig.tight_layout(rect=[0,0,1,.965])
fig.savefig("regression_acwi.png", dpi=155)
print("saved regression_acwi.png")
