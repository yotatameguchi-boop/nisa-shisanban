#!/bin/sh
# src/page.html は Claude Artifacts に公開する本体（<!doctype> や <head> はホスト側が付ける）。
# GitHub Pages などで単体配信するために、ここで最小限のラッパを被せて index.html を作る。
set -e
cd "$(dirname "$0")"
{
  printf '<!doctype html>\n<html lang="ja">\n<head>\n<meta charset="utf-8">\n'
  printf '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
  printf '<style>html{color-scheme:light dark}body{margin:0}img{max-width:100%%}[hidden]{display:none!important}</style>\n'
  printf '</head>\n<body>\n'
  cat src/page.html
  printf '\n</body>\n</html>\n'
} > index.html
echo "built index.html"
