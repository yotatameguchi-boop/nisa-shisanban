# データの出典

## histretSP-1928-2025.csv

Aswath Damodaran（ニューヨーク大学スターン経営大学院）が公開している
[Historical Returns on Stocks, Bonds and Bills](https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/histretSP.html)
の年次系列を、必要な3列だけ抜き出したもの。取得日 2026-09-03。

列は左から：

| 列 | 内容 |
|---|---|
| 1 | 年（1928〜2025、98行） |
| 2 | 3ヶ月 T-Bill の年間リターン（%） |
| 3 | 米10年国債の年間リターン（%） |
| 4 | S&P500 のトータルリターン（配当込み、%） |

**すべて米ドル建て。** 円で投資する場合の為替変動は含まれていない。

このCSVは `src/page.html` の中に JavaScript の配列リテラルとして直接埋め込まれている
（Artifact として配信するページは外部へのデータ取得ができないため）。
データを更新するときは、このCSVを差し替えた上で `src/page.html` 内の `var HIST=[...]` も
同じ内容に書き換えること。

## usdjpy-yearend-1971-2025.csv

セントルイス連銀 FRED の [DEXJPUS](https://fred.stlouisfed.org/series/DEXJPUS)（ドル円の為替レート）を
年次・期末値に集計したもの。取得日 2026-09-03。列は `年, その年の年末レート（円／ドル）`、55行。

1971年8月まで1ドル＝360円の固定相場だったため、為替が意味を持つのは変動相場制に移った後だけ。
円建ての換算に前年末レートが必要なので、**実際に使えるのは1972年以降の54年分**。

換算式：

```
円建てリターン =（1 ＋ ドル建てリターン）×（その年末のレート ÷ 前年末のレート）− 1
```

株式・債券・為替はすべて同じ年をまとめて抽出するので、三者の実際の連動関係が保たれる。

## msci-world-ex-usa-1970-2025.csv

MSCI World ex USA（米国を除く先進国、**グロス・配当込み、米ドル建て**）の年次リターン。
列は `年, リターン（％）`、56行。

出典が2つに分かれている：

- **1970〜2011年** — [upmyinterest.com](https://www.upmyinterest.com/msci-world-ex-us/)（取得日 2026-09-03）
- **2012〜2025年** — [MSCI公式ファクトシート](https://www.msci.com/documents/10199/255599/msci-world-ex-usa-index.pdf) の
  ANNUAL PERFORMANCE 表（2026年7月末版、GROSS RETURNS）

upmyinterest は総収益かグロス／ネットかを明記していないため、両者が重なる期間で突き合わせた。
**2012〜2023年の12年分が小数第2位まで一致**（17.02 / 21.57 / -3.88 / -2.60 / 3.29 / 24.81 /
-13.64 / 23.16 / 8.09 / 13.17 / -13.82 / 18.60）したので、同じ系列＝グロス総収益と判断した。
2024・2025年だけ差がある（4.7 対 5.26、31.9 対 32.55）ので、公式値を採用している。

### 新興国について

当初は「無料の出典から確認できない」として入れていなかったが、
[Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
から取れることが分かったので `ff-emerging-1990-2025.csv` として追加した（下記）。

## ff-emerging-1990-2025.csv

新興国株式の年次リターン（**米ドル建て、配当込み**）1990〜2025年の36行。
列は `年, リターン（％）`。

出典は [Kenneth R. French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)
の `Emerging_5_Factors_CSV.zip`（202607 Bloomberg database 版、取得日 2026-09-23）。
ファイル内の "Annual Factors: January-December" 表から、

```
新興国リターン = Mkt-RF + RF
```

として復元した。超過リターンに無リスク金利を戻すと総収益になる。

### MSCI新興国指数ではないことに注意

これは Fama-French が独自に構築した新興国マーケット・ポートフォリオ（時価総額加重）で、
MSCI Emerging Markets とは構成銘柄も加重も異なる。ただし照合できた年は近い：

| 年 | Fama-French | MSCI EM（グロス） |
|---|---:|---:|
| 2000 | -32.00% | -30.61% |
| 2003 | +55.47% | +56.28% |
| 2008 | **-53.76%** | **-53.18%** |
| 2009 | +81.87% | +79.02% |
| 2017 | +35.67% | +37.75% |

1993年は +89.3% 対 +74.8% と開きが大きい。初期ほど指数の構成差が出る。

1990年開始なので、**新興国を混ぜると使える期間は1990年以降**に限られる。

