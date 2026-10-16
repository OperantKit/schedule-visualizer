# schedule-visualizer

:gb: [English README](README.md)

強化スケジュール DSL プログラム用のドライラン・タイムライン可視化
ツール。スケジュール式（例: `"FI 30s"`, `"Conc(VI 30s, VI 60s)"`）と
持続時間を受け取り、**そのスケジュール下で強化がいつ利用可能になるか**
を示す水平タイムラインをレンダリングする。

## このツールの位置付け

- **するもの**: スケジュール利用可能性の *ドライラン* 可視化。時間
  ベース・スケジュール (FI, VI, FT, VT) は強化が利用可能になる時刻
  にマーカーを配置する。複合スケジュール (`Conc`, `Mult`, `Chain`)
  は各コンポーネントを別レーンに並べる。
- **しないもの**: 行動シミュレータではない。仮想被験体・反応ストリ
  ーム・強化子消費は存在しない。比率スケジュール (FR, VR) は本質的
  に反応依存のため、時刻配置マーカーではなくアノテーション
  (`rf_after_response_n=N`) としてレンダリングされる。

仮想被験体の反応を見たいときは、contingency-py と experiment-io の
仮想被験体でスケジュールを動かす（下の例を参照）。

変動時隔・変動時間の値は、指定した平均の指数分布から引く。
contingency-py が使う Fleshler-Hoffman の数列ではないので、
プレビューが示すのは間隔のおおよその様子で、セッションの
正確な時刻ではない。

## 30 秒で動く例

```bash
pip install git+https://github.com/OperantKit/schedule-visualizer
```

並立スケジュールの各成分が、最初の 2 分間のどの時刻に強化子を利用可能にするかを列挙し、時間軸の図を描く:

```python
from schedule_visualizer.render import render_timeline
from schedule_visualizer.stepper import step_schedule

timeline = step_schedule("Conc(FI 30s, VI 60s)", duration_s=120.0, seed=7)
for event in timeline.events():
    if event.event_type == "rf_available":
        print(round(event.timestamp, 1), event.component)
# 23.5 comp2: VI 60s
# 30.0 comp1: FI 30s
# 33.3 comp2: VI 60s
# 60.0 comp1: FI 30s
# 90.0 comp1: FI 30s
# 96.4 comp2: VI 60s
# 101.0 comp2: VI 60s
# 120.0 comp1: FI 30s
render_timeline(timeline, "conc.png")  # 成分ごとに 1 レーン
```

FI 成分は 30 秒ごとに強化子を設定する。VI 60 s の時刻は `seed=7` で引くので、毎回同じ出力になる。利用可能時刻ではなく反応と提示された強化子を見たいときは、[contingency-py](https://github.com/OperantKit/contingency-py) と [experiment-io](https://github.com/OperantKit/experiment-io) の仮想被験体、または [operantkit-cli](https://github.com/OperantKit/operantkit-cli) でスケジュールを動かす。

## スケジュールを手で図にしない理由

- **スケジュールの文字列から図まで 1 回の呼び出し.** `step_schedule` は contingency-dsl と同じ表層構文（単一の FR・VR・RR・FI・VI・RI・FT・VT・RT・CRF・EXT、複合の `Conc`・`Mult`・`Chain`）を読み、`render_timeline` は成分ごとに 1 レーンを描く。
- **反応に依存するスケジュールをごまかさない.** 比率スケジュールは時刻ではなく注記（`rf_after_response_n=N`）で示す。その強化子はドライランには無い反応に依存するからである。`EXT` は「強化なし」と示す。
- **再現できる.** 変動・確率スケジュールは `seed` を取る。CLI には `--seed` がある。
- **軽い.** 実行時の依存は matplotlib だけで、このサブセットのパーサは内蔵している。

## インストール（開発）

```bash
mise exec -- python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## CLI

```bash
schedule-visualizer --help
schedule-visualizer visualize "FI 30s" --duration 90 --output fi.png
schedule-visualizer visualize "Conc(VI 30s, VI 60s)" --duration 120 \
    --output conc.png --seed 7
```

## Python API

```python
from schedule_visualizer.stepper import step_schedule
from schedule_visualizer.render import render_timeline

timeline = step_schedule("FI 30s", duration_s=90.0)
render_timeline(timeline, "fi.png")
```

## サポートされるスケジュール・サブセット

Atomic: `FR n`, `VR n`, `RR n`, `FI t`, `VI t`, `RI t`, `FT t`,
`VT t`, `RT t`, `CRF`, `EXT`。Compound: `Conc(...)`, `Mult(...)`,
`Chain(...)`。

パーサは本パッケージにローカルなため、可視化ツールは `contingency-py`
や `contingency-dsl` へのランタイム依存を持たない。このサブセット外の
構文を使うプログラムは `ScheduleParseError` を送出する。

## ステータス

Alpha。
