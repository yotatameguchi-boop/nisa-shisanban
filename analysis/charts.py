"""回帰結果の作図。"""
import numpy as np, pandas as pd, warnings, pathlib
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import statsmodels.api as sm
from build_dataset import build, ensure_shiller
warnings.filterwarnings("ignore")

plt.rcParams.update({
    "font.family": ["YuGothic","Hiragino Maru Gothic Pro","Arial Unicode MS"],
    "axes.edgecolor":"#b3bec9","axes.linewidth":.8,"axes.labelcolor":"#4a5560",
    "xtick.color":"#4a5560","ytick.color":"#4a5560","text.color":"#121a22",
    "axes.grid":True,"grid.color":"#dde3e9","grid.linewidth":.7,
    "figure.facecolor":"white","axes.facecolor":"white","font.size":10,
})
BLUE, ORANGE, GREY = "#2a78d6", "#eb6834", "#78838f"
HERE = pathlib.Path(__file__).parent
df = build(ensure_shiller())

def frame(target, preds, h=1):
    d = df.loc[1972:2025].copy()
    if h == 1: d["y"] = d[target].shift(-1)
    else:
        g = np.log1p(d[target]/100)
        d["y"] = 100*np.expm1(g.rolling(h).sum().shift(-h)/h)
    return d[["y"]+preds].dropna()

fig, axes = plt.subplots(2, 2, figsize=(12.5, 9.5))

# (a) モデル1 予測 vs 実績
d = frame("STK_JPY", ["EY","DY","GS10","TERM","INFL","FXCHG","STK_JPY"])
m = sm.OLS(d["y"], sm.add_constant(d.drop(columns="y"))).fit()
ax = axes[0,0]
ax.axhline(0, color=GREY, lw=.8); ax.axvline(0, color=GREY, lw=.8)
lim = [-60, 70]
ax.plot(lim, lim, color=GREY, lw=1, ls="--", zorder=1)
ax.scatter(m.fittedvalues, d["y"], s=42, color=BLUE, alpha=.8,
           edgecolor="white", linewidth=1.4, zorder=3)
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("モデルの予測値（％）"); ax.set_ylabel("実際の翌年リターン（％）")
ax.set_title(f"① 1年先は予測できない\n7変数すべて使っても R²={m.rsquared:.3f}、"
             f"自由度調整済 R²={m.rsquared_adj:.3f}", loc="left", fontsize=11.5, pad=10)
ax.text(.03,.96,"点が破線に乗るほど当たっている", transform=ax.transAxes,
        va="top", fontsize=9, color=GREY)

# (b) 10年先モデルの見かけの説明力
P10 = ["EY","DY","GS10"]
d10 = frame("STK_JPY", P10, h=10)
ax = axes[0,1]
b10 = sm.OLS(d10["y"], sm.add_constant(d10[P10])).fit()
lim = [-5, 24]
ax.plot(lim, lim, color=GREY, lw=1, ls="--", zorder=1)
ax.axhline(0, color=GREY, lw=.8)
sc = ax.scatter(b10.fittedvalues, d10["y"], s=44, c=d10.index, cmap="Blues",
                vmin=1965, edgecolor="white", linewidth=1.4, zorder=3)
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel("モデルの予測値（％・年率）")
ax.set_ylabel("その後10年の年率リターン（％・円建て）")
ax.set_title(f"② 10年先の説明力も見せかけ\nR²={b10.rsquared:.3f} だが独立な観測は実質"
             f"{len(d10)/10:.1f}個しかない", loc="left", fontsize=11.5, pad=10)
solo = {p: sm.OLS(frame("STK_JPY",[p],h=10)["y"],
        sm.add_constant(frame("STK_JPY",[p],h=10)[[p]])).fit().rsquared for p in P10}
ax.text(.03,.97,"単変数だと R²＝"+"／".join(f"{k} {v:.3f}" for k,v in solo.items())+
        "\n相関0.98のCAPE益回りと配当利回りを\n符号を逆にして組み合わせた結果",
        transform=ax.transAxes, va="top", fontsize=8.8, color=GREY, linespacing=1.5)
plt.colorbar(sc, ax=ax, label="起点の年", pad=.02)

# (c) 分散分解
s = df.loc[1972:2025]
U, F = np.log1p(s["STK"]/100), np.log1p(s["FXCHG"]/100)
vU, vF, cv = U.var(), F.var(), np.cov(U,F)[0,1]; vJ = vU+vF+2*cv
ax = axes[1,0]
parts = [("米国株そのもの", vU/vJ*100, BLUE),
         ("為替そのもの", vF/vJ*100, ORANGE),
         ("両者の共分散×2", 2*cv/vJ*100, "#eda100")]
left = 0
for nm, v, c in parts:
    ax.barh([0], [v], left=left, height=.42, color=c, edgecolor="white", linewidth=2)
    ax.text(left+v/2, 0, f"{v:.1f}%", ha="center", va="center",
            color="white", fontsize=12, fontweight="bold")
    ax.text(left+v/2, -.32, nm, ha="center", va="top", fontsize=9.5, color="#4a5560")
    left += v
ax.set_xlim(0,100); ax.set_ylim(-.75,.55); ax.set_yticks([]); ax.grid(False)
ax.set_xlabel("円建てリターンの分散に占める割合（％）")
ax.set_title(f"③ 為替は円建て投資家のリスクの約4割\n"
             f"円建ての年率標準偏差 {np.sqrt(vJ)*100:.1f}％／"
             f"米国株と円安の相関 {np.corrcoef(U,F)[0,1]:+.2f}", loc="left", fontsize=11.5, pad=10)

# (d) 標本外：累積二乗誤差の差
PRED=["EY","DY","GS10","TERM","INFL","FXCHG","STK_JPY"]
ax = axes[1,1]
for nm, preds, col in [("7変数", PRED, ORANGE), ("3変数", ["EY","TERM","FXCHG"], "#eda100"),
                       ("CAPE益回りだけ", ["EY"], BLUE)]:
    d = frame("STK_JPY", preds); ys, dif = [], []
    for t in range(1992, int(d.index.max())+1):
        tr, te = d.loc[:t-1], d.loc[[t]]
        bb = sm.OLS(tr["y"], sm.add_constant(tr[preds])).fit()
        p = float(bb.predict(sm.add_constant(te[preds], has_constant="add")).iloc[0])
        a = te["y"].iloc[0]
        dif.append((a-tr["y"].mean())**2 - (a-p)**2); ys.append(t)
    ax.plot(ys, np.cumsum(dif), lw=2, color=col, label=nm)
    ax.annotate(nm, (ys[-1], np.cumsum(dif)[-1]), xytext=(6,0),
                textcoords="offset points", fontsize=9.5, color=col, va="center")
ax.axhline(0, color="#121a22", lw=1.2)
ax.set_xlim(1991, 2033)
ax.set_ylabel("累積二乗誤差の差（過去平均 − モデル）")
ax.set_xlabel("予測した年")
ax.set_title("④ どのモデルも「過去平均」に負ける\n"
             "線が0より下＝過去平均を使ったほうが当たる", loc="left", fontsize=11.5, pad=10)

fig.suptitle("円建て株式リターンの重回帰分析　1972–2025年",
             fontsize=15, x=.055, ha="left", y=.985)
fig.tight_layout(rect=[0,0,1,.965])
fig.savefig(HERE/"regression.png", dpi=155)
print("saved regression.png")
