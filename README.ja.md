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

被験体行動シミュレーションは姉妹パッケージ `behavior-simulator` を
参照。

## インストール（開発）

```bash
mise exec -- python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
```

## CLI

```bash
schedule-visualizer --help
schedule-visualizer visualize "FI 30s" --duration 90 --output /tmp/fi.png
schedule-visualizer visualize "Conc(VI 30s, VI 60s)" --duration 120 \
    --output /tmp/conc.png --seed 7
```

## Python API

```python
from schedule_visualizer.stepper import step_schedule
from schedule_visualizer.render import render_timeline

timeline = step_schedule("FI 30s", duration_s=90.0)
render_timeline(timeline, "/tmp/fi.png")
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
