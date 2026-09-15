"""3つの実績データとShillerのデータを年次パネルに統合する。"""
import pandas as pd, numpy as np, warnings, pathlib
warnings.filterwarnings("ignore")

HERE = pathlib.Path(__file__).parent
REPO = HERE.parent/"data"

SHILLER_URL = ("https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/"
               "downloads/70fec4f5-727f-4e53-b5f1-179af109c5fa/ie_data.xls")

def ensure_shiller(path=None):
    """Shillerの元データ（1.6MB）は同梱せず、無ければ取ってくる。"""
    path = pathlib.Path(path or HERE/"shiller.xls")
    if not path.exists():
        import urllib.request
        print(f"Shillerのデータを取得中… {SHILLER_URL}")
        urllib.request.urlretrieve(SHILLER_URL, path)
    return path

def load_shiller(path):
    d = pd.read_excel(path, sheet_name="Data", header=None).iloc[8:, :13]
    d.columns = ["date","P","D","E","CPI","frac","GS10","rP","rD","rTR","rE","rTRse","CAPE"]
    d = d[pd.to_numeric(d["date"], errors="coerce").notna()].copy()
    for c in d.columns: d[c] = pd.to_numeric(d[c], errors="coerce")
    ym = (d["date"]*100).round().astype(int)
    d["year"], d["month"] = ym//100, ym%100
    # D・E は直近数か月が未確定で欠測。ゆっくり動く系列なので12か月までは前方補完する
    d[["D","E"]] = d[["D","E"]].ffill(limit=12)
    dec = d[d["month"]==12].set_index("year")
    ann = pd.DataFrame(index=dec.index)
    ann["CAPE"]  = dec["CAPE"]
    ann["EY"]    = 100.0/dec["CAPE"]          # CAPE益回り（％）
    ann["DY"]    = 100.0*dec["D"]/dec["P"]    # 配当利回り（％）
    ann["GS10"]  = dec["GS10"]                # 米10年金利（％）
    ann["CPI"]   = dec["CPI"]
    ann["INFL"]  = 100.0*(dec["CPI"]/dec["CPI"].shift(1) - 1)
    return ann

def load_repo():
    h = pd.read_csv(REPO/"histretSP-1928-2025.csv", header=None,
                    names=["year","TBILL","TBOND","STK"]).set_index("year")
    x = pd.read_csv(REPO/"msci-world-ex-usa-1970-2025.csv", header=None,
                    names=["year","EXUS"]).set_index("year")
    f = pd.read_csv(REPO/"usdjpy-yearend-1971-2025.csv", header=None,
                    names=["year","FX"]).set_index("year")
    f["FXCHG"] = 100.0*(f["FX"]/f["FX"].shift(1) - 1)   # ＋＝円安
    return h.join(x, how="outer").join(f, how="outer")

def build(shiller_path):
    df = load_repo().join(load_shiller(shiller_path), how="outer").sort_index()
    # 円建て＝(1+ドル建て)×(1+為替変動)-1
    df["STK_JPY"]  = 100*((1+df["STK"]/100)*(1+df["FXCHG"]/100) - 1)
    df["EXUS_JPY"] = 100*((1+df["EXUS"]/100)*(1+df["FXCHG"]/100) - 1)
    df["TERM"]     = df["GS10"] - df["TBILL"]           # 期間スプレッド
    df["REALR"]    = df["TBILL"] - df["INFL"]           # 実質短期金利
    return df

if __name__ == "__main__":
    df = build(ensure_shiller())
    df.to_csv(HERE/"panel.csv")
    # Shillerから抜き出した年次系列だけをリポジトリに残す（元の1.6MBは同梱しない）
    ann = df.loc[1871:2025, ["CAPE","DY","GS10","CPI"]].dropna(how="all")
    ann.round(4).to_csv(REPO/"shiller-annual-1871-2025.csv")
    cols = ["STK","EXUS","TBOND","TBILL","FXCHG","STK_JPY","CAPE","EY","DY","GS10","INFL"]
    sub = df.loc[1971:2025, cols]
    print(sub.round(2).to_string())
    print("\n欠測:\n", sub.isna().sum()[lambda s: s>0])
