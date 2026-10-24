# schedule-visualizer

:gb: [English README](README.md)

schedule-visualizer は、`Conc(FI 30s, VI 60s)` のようなスケジュールの式から、各成分がいつ強化子を利用可能にするかを時間軸の図にします。実験の設計やスケジュールの授業に使うもので、何も走らせる前に強化の利用可能になる間隔を目で確かめられます。[OperantKit](https://github.com/OperantKit) の中では、[schedule-writer](https://github.com/OperantKit/schedule-writer) が組み立て [contingency-py](https://github.com/OperantKit/contingency-py) が実行する式を、前もって見せる役目を持ちます。

- **文字列から図まで 2 回の呼び出し。** 成分ごとに 1 本のレーンです。
- **作り話の時刻を置かない。** 比率スケジュールは反応に依存するので、時間軸に置かずに注記で示します。
- **同じ `seed` なら毎回同じ図。**

## インストール

Python 3.11 以上。schedule-visualizer はまだ PyPI に公開されていないので、GitHub から入れます。依存するのは matplotlib だけで、pip が PyPI から入れます。

```bash
pip install git+https://github.com/OperantKit/schedule-visualizer
```

## 例

`Conc(FI 30s, VI 60s)` の各成分が最初の 2 分間に強化子を利用可能にする時刻を並べ、時間軸の図を描きます。

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
render_timeline(timeline, "conc.png")  # 成分ごとに 1 本のレーン
```

コマンドラインでは次のとおりです。

```bash
schedule-visualizer visualize "Conc(FI 30s, VI 60s)" --duration 120 --seed 7 --output conc.png
```

## 何が描かれるか

| スケジュール | 時間軸での表示 |
|---|---|
| `FI t`、`FT t` | t、2t、3t、… に印 |
| `VI t`、`VT t` | 平均 t の指数分布から引いた間隔で印（`seed` で固定されます） |
| `RI t`、`RT t` | 1 秒ごとの刻みに、確率 1/t で印 |
| `FR n`、`VR n`、`RR n`、`CRF` | 注記（`rf_after_response_n=n`）。強化子が反応に依存するため |
| `EXT` | 「強化なし」の注記 |
| `Conc(...)`、`Mult(...)`、`Chain(...)` | 成分ごとに 1 本のレーン |

時間の単位は `s`、`ms`、`min` です（`FI 30s`、`VI 2min`）。それ以外は `ScheduleParseError` になります。

## 制限

- **シミュレーションではありません。** 被験体も反応もありません。FI の印は、強化子が利用可能になった瞬間に受け取られたとみなした時刻です。実際のセッションでは強化子の提示の後に次の間隔が始まるので、実際の時刻はこれより遅れます。反応と提示された強化子を見るには、contingency-py と [experiment-io](https://github.com/OperantKit/experiment-io) の仮想被験体、または [operantkit-cli](https://github.com/OperantKit/operantkit-cli) でスケジュールを走らせてください。
- **VI と VT の時刻はセッションの時刻ではありません。** contingency-py が使う Fleshler–Hoffman (1962) の数列ではなく、指数分布から引いています。
- **`Mult` と `Chain` のレーンは順序を表しません。** どの成分も全区間にわたって並べており、成分が提示される順にはなっていません。
- **読めるのは contingency-dsl の書き方の一部だけです。** `Tand`、`Alt`、切替遅延（`COD=2s`）、ハイフン付きの単位（`30-s`）、注釈、複数の段階からなる実験計画は拒否されます。`RR n` は平均比率 n として読みます。比率の値が整数でないもの（schedule-writer が書く確率の形 `RR 0.2` など）はエラーとして拒否されます。

## AI のコーディングエージェント向け

AI のコーディングエージェント向けの案内は [AGENTS.md](AGENTS.md) にあります。

## 開発

```bash
python -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/pytest
```

両方の README の `python` ブロックはすべて `tests/test_readme_examples.py` が実行します。

## 参考文献

Fleshler, M., & Hoffman, H. S. (1962). A progression for generating variable-interval schedules. *Journal of the Experimental Analysis of Behavior, 5*(4), 529–530. https://doi.org/10.1901/jeab.1962.5-529

## ライセンス

MIT（`pyproject.toml` に記載）。
