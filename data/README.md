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
