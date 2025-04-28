# generate_gif.py  –  J1 2025 累積勝ち点バーチャートレース
#
# リポジトリ: openfootball/football.json（Fork 版）
#  - 2025/jp.1.json を読み込む
#  - 試合結果から勝ち点を計算し節ごとに累積
#  - Matplotlib + FuncAnimation で GIF を出力
#
# 事前準備:
#   requirements.txt に
#     pandas
#     matplotlib
#   を記載しておくこと
#
# GitHub Actions で自動実行する想定
#   - まだ結果の無い試合はスキップ（KeyError 対策）
#   - 未開催の場合は警告だけ出して正常終了

import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from pathlib import Path

YEAR = 2025                                         # ← 来季以降はここだけ変更
JSON_FILE = Path(f"{YEAR}/jp.1.json")               # 2025/jp.1.json
OUT_GIF   = Path(f"j1_{YEAR}_points.gif")           # 出力 GIF ファイル名

# -------------------------------------------------------------------
# 1. JSON 読み込み
# -------------------------------------------------------------------
try:
    with open(JSON_FILE, encoding="utf-8") as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"❌ {JSON_FILE} が見つかりません。フォルダとファイル名を確認してください。")
    raise SystemExit(1)

rows = []
for m in data["matches"]:
    # スコアが未確定（開幕前 or 未開催）の試合はスキップ
    ft = m.get("score", {}).get("ft")
    if not ft:
        continue

    rows.append({
        "round": int(m["round"].split()[-1]),   # "Matchday 14" → 14
        "home" : m["team1"],
        "away" : m["team2"],
        "hg"   : ft[0],                         # home goals
        "ag"   : ft[1],                         # away goals
    })

df = pd.DataFrame(rows)

if df.empty:
    print("⚠️ まだ試合結果がありません。シーズン開幕後に自動で再実行されます。")
    raise SystemExit(0)

# -------------------------------------------------------------------
# 2. 勝ち点計算（ホーム/アウェイ） → 節ごとに累積
# -------------------------------------------------------------------
df["home_pts"] = (df.hg > df.ag)*3 + (df.hg == df.ag)
df["away_pts"] = (df.ag > df.hg)*3 + (df.hg == df.ag)

home = df[["round","home","home_pts"]].rename(columns={"home":"team","home_pts":"pts"})
away = df[["round","away","away_pts"]].rename(columns={"away":"team","away_pts":"pts"})

pts = (
    pd.concat([home, away])
      .groupby(["round","team"]).pts.sum()
      .unstack(fill_value=0)
      .cumsum()
      .sort_index()          # round の昇順
)

# -------------------------------------------------------------------
# 3. GIF 描画
# -------------------------------------------------------------------
plt.rcParams["font.family"] = "DejaVu Sans"         # GitHub Actions 標準フォント

fig, ax = plt.subplots(figsize=(10, 7))

def draw(round_no: int) -> None:
    ax.clear()
    series = pts.loc[round_no].sort_values(ascending=False)
    ax.barh(series.index, series.values, color="#f5a623")
    ax.set_title(f"J1 {YEAR}  累積勝ち点  –  第{round_no}節")
    ax.set_xlim(0, pts.values.max() + 5)
    ax.set_xlabel("Points (累積)")
    ax.invert_yaxis()        # 1位を上に

ani = FuncAnimation(
    fig,
    draw,
    frames=pts.index,        # 節ごとに更新
    interval=1000,            # 0.6 秒／フレーム ≒ 5 秒で 8 節分
    repeat=False
)

ani.save(OUT_GIF, writer=PillowWriter(fps=1))
print(f"✅ GIF saved: {OUT_GIF}")
