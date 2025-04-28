# generate_gif.py  (J1 2025 版)
import json, pandas as pd, matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from pathlib import Path

YEAR      = 2025
JSON_FILE = Path(f"{YEAR}/jp.1.json")     # ← ここだけ年代で変わる
OUT_GIF   = Path(f"j1_{YEAR}_points.gif")

# --- 1. JSON 読み込み -------------------------------------------------
with open(JSON_FILE, encoding="utf-8") as f:
    data = json.load(f)

rows = []
for m in data["matches"]:
    if m["score"]["ft"] is None:          # 未開催（開幕前など）はスキップ
        continue
    rows.append({
        "round": int(m["round"].split()[-1]),
        "home" : m["team1"],
        "away" : m["team2"],
        "hg"   : m["score"]["ft"][0],
        "ag"   : m["score"]["ft"][1],
    })
df = pd.DataFrame(rows)
if df.empty:
    print("⚠️ まだ試合結果がありません。シーズン開幕後に再実行してください。")
    quit()

# --- 2. 勝ち点計算 ----------------------------------------------------
df["home_pts"] = (df.hg > df.ag)*3 + (df.hg == df.ag)
df["away_pts"] = (df.ag > df.hg)*3 + (df.hg == df.ag)

home = df[["round","home","home_pts"]].rename(columns={"home":"team","home_pts":"pts"})
away = df[["round","away","away_pts"]].rename(columns={"away":"team","away_pts":"pts"})

pts = (pd.concat([home, away])
         .groupby(["round","team"]).pts.sum()
         .unstack(fill_value=0)
         .cumsum()
         .sort_index())

# --- 3. GIF 描画 ------------------------------------------------------
fig, ax = plt.subplots(figsize=(10,7))
def draw(r):
    ax.clear()
    s = pts.loc[r].sort_values(ascending=False)
    ax.barh(s.index, s.values, color="#f5a623")
    ax.set_title(f"J1 {YEAR} 累積勝ち点 – 第{r}節")
    ax.set_xlim(0, pts.values.max()+5)
    ax.invert_yaxis()
ani = FuncAnimation(fig, draw, frames=pts.index, interval=600, repeat=False)
ani.save(OUT_GIF, writer=PillowWriter(fps=8))
print("✅ GIF saved:", OUT_GIF)
