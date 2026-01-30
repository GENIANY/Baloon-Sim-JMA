# スペースバルーン軌道シミュレータ（JMA GSM）開発計画書

> **このドキュメントは「毎回の会話で参照する、開発の現在地と次の一手」を一枚に集約するための“生きた計画書”です。**  
> 会話ごとに、最上部の「現在のステータス」と「次のアクション」だけ更新すれば、スレッドを遡らずに状況把握できます。

---

## ドキュメントメタ情報

- **版**: v0.1（初版ドラフト）
- **最終更新**: 2026-01-30（更新担当: _TBD_）
- **対象プロジェクト名（仮）**: `balloon-sim-jma`
- **目的**:
  - 気象庁 **JMA High-Resolution GSM**（GRIB2）を用いた、日本域スペースバルーン軌道シミュレーションの精度・運用性向上（参照: R-JMA-Product / R-JMA-Tutorial）
  - **落下地点を点ではなく確率領域（50%/90%など）**として提示（バルーン・パラメータ不確実性によるアンサンブル）
- **参照する設計事例**: Tawhiri（データ→内部形式→補間→物理モデル→RK4積分の分離。参照: R-Tawhiri-*）

---

## 現在のステータス（毎回更新する欄）

- **意思決定済み**
  - 気象データは **JMA High-Resolution GSM** を第一候補として採用（上層 1000–10hPa を含む。参照: R-JMA-Product）
  - Tawhiriを直接改造するより、Tawhiriの設計思想を参考に **独自実装**で進める
  - 出力は「単一路線」＋「パラメータ・アンサンブルの着地点分布（確率領域）」を標準にする
- **進捗**
  - 設計方針と計画書テンプレート作成（本書）
  - 参照資料の一次収集（JMA GSM、Tawhiri DeepWiki）
- **未解決の重要事項（Decision Pending）**
  - [ ] 内部保存形式: `memmap`（Tawhiri型） vs `zarr`（圧縮チャンク）
  - [ ] 高度の基準: MSL（海面基準）に統一するか／地形（DEM）を必須にするか
  - [ ] 予測インターフェース: まずCLIのみ → 後でHTTP API／最初からHTTP API
  - [ ] アンサンブル領域の手法: 楕円近似 → HDR等高線（KDE）へ段階導入

---

## 粒度・更新頻度のルール

この計画書は「粒度ごとに更新頻度を分けて」運用します。

### 1) 毎回の会話で更新（超高頻度）
- **現在のステータス**
- **次のアクション（最大3つ）**
- **ブロッカー（詰まり）**

### 2) まとまった作業単位で更新（中頻度）
- フェーズ別ステータス（Not started / In progress / Done）
- 主要タスクの完了チェック
- リスクと対策（発見・変更があれば追記）

### 3) 仕様が固まった段階で更新（低頻度）
- インターフェース仕様（I/O、単位、座標系）
- データセット仕様（格子、レベル、変数、時刻系）
- 運用要件（キャッシュ、保管、再取得、監視）

---

## 計画の概要

### ゴール（何ができたら「使える」か）
1. **決定論予測**: 入力（打上げ条件＋バルーン設定）→ 軌道（時系列）＋落下地点
2. **パラメータ・アンサンブル**: 同じ入力に対しN本の軌道を生成し、落下地点の点群を得る
3. **確率領域出力**: 点群から 50% / 90% 領域（GeoJSON/KML等）を生成する
4. **運用**: JMA GSMを定期取得し、予報要求で高速に参照できる（前処理＋キャッシュ）

### スコープ（当面やること）
- JMA GSM（GRIB2）から **U/V/Z（上層気圧面）** を取り込み、任意の (t, lat, lon, alt[m]) で風(u,v)を返す（参照: R-JMA-Product）
- Tawhiri同等の「モデル合成」＋「RK4」＋「終了点二分探索」を実装（参照: R-Tawhiri-Models / R-Tawhiri-Solver）
- バルーンのパラメータ分布からアンサンブルを生成し、確率領域を返す

### 非スコープ（後回し）
- リアルタイム観測同化（実況補正）
- 完全な空力・熱力学モデル（まずはTawhiri相当の簡易モデル）
- 極端気象向けの高度な不確実性推定（まずはパラメータ不確実性中心）

---

## 開発フェーズ（マイルストーン）

> ここが“最重要”の一覧です。毎回、ステータスを更新してください。

| フェーズ | 目的 | 主成果物 | Exit Criteria（完了条件） | ステータス |
|---|---|---|---|---|
| A | JMA GSM 取得・デコード・保存 | `meteo.fetch`, `meteo.decode`, `meteo.store` | 1runのU/V/Z（上層 1000–10hPa）を取り込み、再利用できる形で保存（参照: R-JMA-Product） | Not started |
| B | 風場サンプラ（補間） | `meteo.windfield` | 単点/ベクトル入力で (t,lat,lon,alt)→(u,v) が返る | Not started |
| C | 物理モデル（合成可能） | `physics.models`, `physics.termination` | 上昇→バースト→降下→着地 の2ステージが組める（参照: R-Tawhiri-Models） | Not started |
| D | RK4ソルバ | `solver.rk4`, `solver.solve` | dt固定RK4＋終了点二分探索で軌道が出る（参照: R-Tawhiri-Solver） | Not started |
| E | アンサンブル予測 | `ensemble.runner`, `ensemble.sampler` | N本の軌道生成、着地点点群が出る | Not started |
| F | 確率領域推定 | `outputs.regions` | 50/90%領域（楕円→HDRへ段階導入）が出る | Not started |
| G | インターフェース/運用 | `cli`, `api`, `ops` | 予測要求を“手元/サーバ”で回せる（キャッシュ含む） | Not started |
| H | 検証・性能 | `tests`, `benchmarks`, `validation` | バックテスト・性能測定が自動化され、改善が追える | Not started |

---

## 実装レベルの計画（タスク粒度）

### フェーズA: JMA GSM ingestion（取得→デコード→内部保存）
- [ ] `RunLocator`: 最新run候補（00/06/12/18等）を探索し、揃ったrunを決定
- [ ] `Downloader`: 必要ファイルのみダウンロード（再試行、部分欠損検知）
- [ ] `Decoder`: GRIB2から U/V/Z を抽出（気圧面・時刻・格子を解釈）
- [ ] `Store`: 保存（memmap or zarr）＋メタデータ（run、格子、レベル、単位）
- [ ] `open_latest()` 相当の検索API（TawhiriのDataset discoverを参考。参照: R-Tawhiri-WindData）
- [ ] 最小E2E: 「1run取り込み → 1点サンプル（Bの仮実装でも可）」まで通す

参照: JMA GSMのディレクトリアクセス方法（R-JMA-Tutorial）

---

### フェーズB: 風場サンプラ（4D補間）
- [ ] インターフェース固定: `sample_uv(t_unix, lat_deg, lon_deg, alt_m)` と `sample_uv_batch(...)`
- [ ] 時間・緯度・経度: 線形補間（経度wrap）
- [ ] 鉛直: Z（geopotential height）配列に対し、**二分探索＋線形補間**（Tawhiri方式。参照: R-Tawhiri-Interp）
- [ ] 範囲外の扱い（warning/exception）を設計（TawhiriのRangeError/Warningに倣う）
- [ ] 性能: まずPython→必要ならCython/Numba等で置換可能な構造にする（参照: R-Tawhiri-Interp）

---

### フェーズC: 物理モデル（合成）
- [ ] `make_constant_ascent(rate_mps)`
- [ ] `make_drag_descent(params)`（まずはTawhiri相当の簡易モデル）
- [ ] `make_wind_velocity(windfield)`（u/v→dlat/dlon変換）
- [ ] 終了条件:
  - [ ] バースト高度
  - [ ] 海面（alt<=0）
  - [ ] （任意）DEM地形到達
  - [ ] 最大時間
- [ ] 合成:
  - [ ] `make_linear_model([models...])`
  - [ ] `make_any_terminator([terms...])`
- [ ] 標準プロファイル:
  - [ ] `standard_profile(ascent, burst_alt, descent_params)`（参照: R-Tawhiri-Models）

---

### フェーズD: RK4ソルバ
- [ ] `rk4_step(state, dt, model)`（地理座標を安全に扱う）
- [ ] 終了跨ぎ時の**二分探索で終了点を詰める**（参照: R-Tawhiri-Solver）
- [ ] ステージ連結（上昇→降下）
- [ ] 出力フォーマット（時刻、lat,lon,alt、警告）

---

### フェーズE/F: アンサンブル＋確率領域
- [ ] `ParameterSampler`（seed管理、分布定義）
- [ ] `EnsembleRunner`（N軌道を効率よく回す。可能ならバッチ化）
- [ ] 領域推定（段階導入）:
  - [ ] **Stage-1**: 共分散楕円（50/90%）
  - [ ] **Stage-2**: 2D KDE→HDR等高線ポリゴン
- [ ] 出力:
  - [ ] 代表軌道（中央値等）
  - [ ] 点群
  - [ ] 領域ポリゴン（GeoJSON/KML）

---

### フェーズG/H: 運用・検証・性能
- [ ] CLI（例: `balloon-sim run --launch ... --n 500`）
- [ ] API（必要なら）: 入力→JSON応答（軌道＋領域）
- [ ] 取得の自動化（cron / systemd timer / CI）
- [ ] テスト:
  - [ ] 単体（補間、座標変換、終了条件）
  - [ ] 統合（1run ingestion→予測）
  - [ ] 退行（固定seedで結果が変わらない）
- [ ] ベンチマーク:
  - [ ] 1軌道
  - [ ] N本アンサンブル
  - [ ] 風サンプル/秒

---

## 開発成果物（コード/モジュール構成）リスト

### リポジトリ構成案（Python想定）
```
balloon_sim/
  __init__.py
  config.py              # 設定（データ格納先、領域、レベル等）
  meteo/
    __init__.py
    run_locator.py       # run探索（latest解決）
    fetch.py             # ダウンロード
    decode.py            # GRIB2 decode（U/V/Z抽出）
    store.py             # memmap/zarr保存＋メタデータ
    windfield.py         # (t,lat,lon,alt)->(u,v) 補間
  physics/
    __init__.py
    models.py            # 上昇/降下/風モデル
    termination.py       # 終了条件
    atmosphere.py        # 簡易標準大気（必要なら）
  solver/
    __init__.py
    rk4.py               # RK4ステップ
    solve.py             # ステージ連結、終了点二分探索
  ensemble/
    __init__.py
    sampler.py           # パラメータ分布
    runner.py            # アンサンブル実行
  outputs/
    __init__.py
    formats.py           # JSON/KML/GeoJSON
    regions.py           # 楕円/HDR等高線
  cli/
    __init__.py
    main.py              # 入口（argparse/typer等）
tests/
benchmarks/
docs/
  DEVELOPMENT_PLAN.md    # ←この計画書
```

### 主要成果物リスト（チェック用）
- [ ] `DEVELOPMENT_PLAN.md`（本書）運用開始
- [ ] `DATASET_SPEC.md`（JMA GSM→内部形式の仕様）
- [ ] ingestionパイプライン（A）
- [ ] 風場補間（B）
- [ ] 物理モデル（C）
- [ ] RK4ソルバ（D）
- [ ] アンサンブル（E）
- [ ] 領域推定（F）
- [ ] CLI / API（G）
- [ ] テスト・ベンチ（H）

---

## 関連する外部情報源のリスト（更新: 必要時）

### Reference IDs
- R-JMA-Top
- R-JMA-Product
- R-JMA-Tutorial
- R-Tawhiri-Arch
- R-Tawhiri-WindData
- R-Tawhiri-Interp
- R-Tawhiri-Models
- R-Tawhiri-Solver
- R-Tawhiri-Downloader-GS

---

## 現在の進捗（詳細）

- 設計の方向性確定: **JMA GSM採用 + 独自実装 + パラメータ・アンサンブル**
- 外部情報源の確保: JMA GSMの仕様ページ、Tawhiri DeepWiki主要章を確認
- 実装: まだ（Not started）

---

## 今後の見通し（次のアクション）

### 直近の「次のアクション」（最大3つ）
1. **フェーズAの最小E2E**: 1runのU/V/Zを取得→保存→読み直し  
2. **内部保存形式の決定**（memmap vs zarr）  
3. **WindFieldの単点サンプル**（まずは補間なしのnearestでも良い）

### リスクと対策（随時更新）
- **GRIB2デコード差**（ライブラリ差・要素名差）  
  → まずは “必要変数だけ” を小さく取り込み、メタデータで単位・レベルを固定化
- **運用でのrun欠損/遅延**  
  → latest探索は「候補runを遡る」方式にする（参考: R-Tawhiri-Downloader-GS）
- **性能**（アンサンブルで補間回数が増える）  
  → 風場サンプラは最初から `batch` APIを用意、最適化可能な境界を作る（参考: R-Tawhiri-Interp）

---

## 変更履歴（Changelog）

| 日付 | 版 | 変更内容 | 変更者 |
|---|---|---|---|
| 2026-01-30 | v0.1 | 初版ドラフト作成 | _TBD_ |

---

## 決定ログ（Decision Log）

| ID | 日付 | 決定 | 理由 | 影響範囲 |
|---|---|---|---|---|
| D-001 | 2026-01-30 | 気象データにJMA GSMを採用 | 上層(1000–10hPa)を含み日本用途で合理性が高い（参照: R-JMA-Product） | ingestion/補間/検証 |

---

## URL（コピペ用）

> ※会話本文にはURL直書きを避けるため、ここだけコードブロックでまとめます。

```text
# DeepWiki（ユーザー提示）
R-Tawhiri-Downloader-GS https://deepwiki.com/projecthorus/tawhiri-downloader-container/2-getting-started
R-Tawhiri-Arch          https://deepwiki.com/cuspaceflight/tawhiri/1.1-system-architecture
R-Tawhiri-WindData      https://deepwiki.com/cuspaceflight/tawhiri/2.1-wind-data-management
R-Tawhiri-Interp        https://deepwiki.com/cuspaceflight/tawhiri/2.2-wind-interpolation-system
R-Tawhiri-Models        https://deepwiki.com/cuspaceflight/tawhiri/2.3-flight-physics-models
R-Tawhiri-Solver        https://deepwiki.com/cuspaceflight/tawhiri/2.4-numerical-integration-solver

# JMA GSM
R-JMA-Top               https://www.wis-jma.go.jp/cms/gsm/
R-JMA-Product           https://www.wis-jma.go.jp/cms/gsm/product_information.html
R-JMA-Tutorial          https://www.wis-jma.go.jp/cms/gsm/tutorial.html
```
