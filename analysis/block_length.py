"""ブートストラップのブロック長に根拠はあるのか。

ツールは「1年ずつ / 連続5年 / 連続10年」を選ばせ、既定を5年にしている。これは勘で決めた値だった。
(1) 年次リターンにそもそも保存すべき系列相関があるのか
(2) Politis & White (2004) の自動選択（arch の実装）はいくつと言うのか
(3) ブロック長を変えると積立の結果はどれだけ変わるのか
を順に確かめる。arch が無い環境では (2) を飛ばして残りを実行する。
"""
import numpy as np, warnings
from statsmodels.tsa.stattools import acf
from statsmodels.stats.diagnostic import acorr_ljungbox
from build_dataset import build, ensure_shiller
warnings.filterwarnings("ignore")

try:
    from arch.bootstrap import optimal_block_length
    HAS_ARCH = True
except ImportError:
    HAS_ARCH = False

df = build(ensure_shiller())
s = df.loc[1972:2025]
SER = {"円建て株式(S&P500)": s["STK_JPY"], "ドル建て株式(S&P500)": s["STK"],
       "米10年国債": s["TBOND"], "ドル円の変動": s["FXCHG"], "米国以外の株式": s["EXUS"]}

print("="*74)
print("【1】年次リターンに系列相関はあるのか  1972–2025")
print("-"*74)
print(f"{'系列':<22}{'ρ1':>7}{'ρ2':>7}{'ρ3':>7}{'ρ5':>7}{'Ljung-Box(5) p':>16}")
for nm, x in SER.items():
    v = (x.dropna()/100).values
    a = acf(v, nlags=5, fft=False)
    lb = acorr_ljungbox(v, lags=[5], return_df=True)["lb_pvalue"].iloc[0]
    print(f"{nm:<22}{a[1]:>7.3f}{a[2]:>7.3f}{a[3]:>7.3f}{a[5]:>7.3f}{lb:>16.3f}"
          + ("  ← 有意" if lb < 0.05 else ""))
print("\n  帰無仮説は「どのラグにも相関がない」。p>0.05 なら相関は検出されない。")

print("\n" + "="*74)
print("【2】Politis & White (2004) の自動ブロック長選択")
print("-"*74)
if HAS_ARCH:
    print(f"{'系列':<22}{'定常BS':>10}{'循環BS':>10}")
    for nm, x in SER.items():
        ob = optimal_block_length((x.dropna()/100).values)
        print(f"{nm:<22}{float(ob['stationary'].iloc[0]):>10.2f}{float(ob['circular'].iloc[0]):>10.2f}")
    print("\n  単位は年。1に近いほど、連ねる意味がない＝1年ずつ引いてよい。")
else:
    print("  arch が未導入のため省略。`pip install arch` 後に再実行すると出力される。")

print("\n" + "="*74)
print("【3】ブロック長は積立の結果を変えるのか")
print("-"*74)
MONTH, YEARS, FEE, N = 50_000, 25, 0.05775/100, 20_000
r = (s["STK_JPY"].dropna()/100).values
n = len(r)

def accumulate(R):
    """R: (paths, YEARS) の年次リターン → 25年後の残高"""
    G = (1+R)**(1/12) * (1 - FEE/12)
    bal = np.zeros(R.shape[0])
    for y in range(YEARS):
        g = G[:, y]
        for _ in range(12):
            bal = bal*g + MONTH
    return bal

def iid(rng):
    return r[rng.integers(0, n, (N, YEARS))]

def circular(rng, L):
    nb = int(np.ceil(YEARS/L))
    st = rng.integers(0, n, (N, nb))
    idx = (st[:, :, None] + np.arange(L)[None, None, :]) % n
    return r[idx.reshape(N, -1)[:, :YEARS]]

def stationary(rng, L):
    """Politis & Romano: ブロック長を平均Lの幾何分布にする"""
    p = 1.0/L
    idx = np.empty((N, YEARS), dtype=int)
    cur = rng.integers(0, n, N)
    for t in range(YEARS):
        idx[:, t] = cur
        newblk = rng.random(N) < p
        cur = np.where(newblk, rng.integers(0, n, N), (cur+1) % n)
    return r[idx]

rows = []
for nm, fn in [("1年ずつ（IID）", lambda g: iid(g)),
               ("循環BS 2年",      lambda g: circular(g, 2)),
               ("循環BS 5年（既定）", lambda g: circular(g, 5)),
               ("循環BS 10年",     lambda g: circular(g, 10)),
               ("定常BS 平均5年",   lambda g: stationary(g, 5))]:
    v = accumulate(fn(np.random.default_rng(20260923)))
    rows.append((nm, np.percentile(v,10), np.percentile(v,50), np.percentile(v,90)))

print(f"月{MONTH:,}円・{YEARS}年・信託報酬0.05775%・円建て株式100%。各{N:,}回。\n")
print(f"{'手法':<22}{'下位10%':>13}{'中央値':>13}{'上位10%':>13}")
for nm,a,b,c in rows:
    print(f"{nm:<22}{a/1e4:>11,.0f}万{b/1e4:>11,.0f}万{c/1e4:>11,.0f}万")
base = rows[0]
print("\n  1年ずつ（IID）との差:")
for nm,a,b,c in rows[1:]:
    print(f"    {nm:<20}下位10% {(a-base[1])/1e4:+6,.0f}万   中央値 {(b-base[2])/1e4:+6,.0f}万   "
          f"上位10% {(c-base[3])/1e4:+6,.0f}万")
print("\n  モンテカルロ誤差の目安: 同じ手法を別の乱数で回したときのばらつき")
v1 = accumulate(iid(np.random.default_rng(1))); v2 = accumulate(iid(np.random.default_rng(2)))
print(f"    IID同士（種違い）    下位10% {(np.percentile(v2,10)-np.percentile(v1,10))/1e4:+6,.0f}万   "
      f"中央値 {(np.percentile(v2,50)-np.percentile(v1,50))/1e4:+6,.0f}万   "
      f"上位10% {(np.percentile(v2,90)-np.percentile(v1,90))/1e4:+6,.0f}万")
