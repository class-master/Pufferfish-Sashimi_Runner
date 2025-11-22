# Day4：エフェクトと演出で仕上げる日（7人×3時間用シナリオ）

## 0. 今日のゴール（先生が最初に読む用）

3時間で、次を「クラス全体」として完成させます。

1. ジャンプ／着地／ゲームオーバー時に **簡単なエフェクト（光・パーティクル）** が出る  
2. ゲームオーバー後に **Rキーでリスタート** できる  
3. HUD やメッセージで、プレイヤーに状況が分かりやすく表示される  

### 絶対ルール

- `main_day1.py` / `main_day2.py` / `main_day3.py` は **書き換え禁止**（参考に読むのはOK）
- 触るファイルは、基本的に `main_day4.py` と `docs/Day4_buglog.md`、必要なら `assets/` など
- 迷ったら先生かこのプリントに必ず戻る

---

## 1. 今日の7人の役割（先に割り当てる）

| No | 役割名                     | 触るファイル           | ざっくりやること                                      |
|----|----------------------------|------------------------|-------------------------------------------------------|
| A  | エフェクト設計担当         | `main_day4.py`         | エフェクトのデータ構造と更新ルールを考える           |
| B  | エフェクト描画担当         | `main_day4.py`         | エフェクトを画面に描画する処理を書く                 |
| C  | GameOver演出＆メッセージ担当| `main_day4.py`        | GAME OVER 表示と、再スタート案内メッセージを作る     |
| D  | リスタート処理担当         | `main_day4.py`         | 状態を初期化する `reset()` を作り、Rキーに結びつける |
| E  | サウンドフック担当（任意） | `main_day4.py`, `assets`| ジャンプ／ゲームオーバー時のSE/BGMを鳴らす          |
| F  | つなぎ込み担当             | `main_day4.py`         | A〜E のコードを1つの `RunnerGame` に統合する          |
| G  | テスト＆バグログ担当       | `docs/Day4_buglog.md`  | 動作確認とバグ／改善アイデアの記録                   |

> 先生へ：  
> E（サウンド）が難しそうであれば、A〜D＋F＋Gの6人制でもOKです。  
> その場合は、誰か1人に「エフェクト＋サウンド」をまとめて担当してもらってもよいです。

---

## 2. 今日の時間割（板書用）

- 0:00〜0:10　Day3の振り返りと、仕上げとしてのDay4のゴール説明
- 0:10〜0:20　役割分担と演出アイデア出し（どんな演出にしたいか）
- 0:20〜1:10　**個人作業タイム**（A〜E中心にコーディング）
- 1:10〜2:00　**結合タイム**（Fがハブになって `main_day4.py` を1本にまとめる）
- 2:00〜2:40　テスト＆デバッグ（G主導でゲームをひたすら遊ぶ）
- 2:40〜3:00　今日のまとめ・タイトル＆キャプチャ撮影など

---

## 3. 各役割の「やることチェックリスト」

### 3-1. A：エフェクト設計担当

**目的**：エフェクト（パーティクル）の「中身（データ構造）」と、「いつ生まれていつ消えるか」を決める。

- 触るファイル：`main_day4.py`
- 主に `RunnerGame` クラスの `__init__` と `update` 内

#### Aさんのチェックリスト

- [ ] `self.effects = []` のようなリストを用意した
- [ ] エフェクト1つを表すデータ（x, y, w, h, life など）を決めた
- [ ] ジャンプ開始時／着地時／ゲームオーバー時に、エフェクトを追加する関数を作った

#### サンプルコード（考え方）

```python
class RunnerGame(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        # ...
        self.effects = []  # [x, y, w, h, life]

    def add_jump_effect(self):
        # ジャンプ開始時に呼ぶ
        e = [self.x, self.y, 24, 24, 0.3]  # lifeは0.3秒くらい
        self.effects.append(e)

    def add_land_effect(self):
        # 着地時に呼ぶ
        e = [self.x, self.ground, 32, 12, 0.2]
        self.effects.append(e)
```

> ✅ Aさんは「**エフェクトのルールブックを作る人**」です。  
> どんな形に見えるかはBさんと相談しながら決めて大丈夫です。

---

### 3-2. B：エフェクト描画担当

**目的**：Aさんが作った `self.effects` を、実際に画面にカラフルに描画する。

- 触るファイル：`main_day4.py`
- 主に `draw` メソッドの中

#### Bさんのチェックリスト

- [ ] `self.effects` をループして、矩形や小さな光のように描画した
- [ ] life（残り時間）に応じて、透明度や大きさを変えるなど工夫した
- [ ] エフェクトが多すぎて重くならないように、一定時間で消している

#### サンプルコード（考え方）

```python
    def update(self, dt):
        # ...
        # エフェクトの寿命を更新
        alive = []
        for e in self.effects:
            e[4] -= dt  # life
            if e[4] > 0:
                alive.append(e)
        self.effects = alive
        self.draw()

    def draw(self):
        self.canvas.clear()
        with self.canvas:
            # 背景や地面、障害物、ランナー描画（Day2相当）
            # ...
            # エフェクト描画
            for (ex, ey, ew, eh, life) in self.effects:
                alpha = max(0.0, min(1.0, life * 3.0))
                Color(1.0, 1.0, 0.4, alpha)
                Rectangle(pos=(ex, ey), size=(ew, eh))
```

> ✅ Bさんは「**見た目のワクワク担当**」です。  
> あまり難しく考えず、「光る四角」からスタートしてOKです。

---

### 3-3. C：GameOver演出＆メッセージ担当

**目的**：ゲームオーバー時に、画面で分かりやすく「終わったこと」と「Rで再スタートできること」を伝える。

- 触るファイル：`main_day4.py`
- 主に `draw` と HUD 用の `Label`

#### Cさんのチェックリスト

- [ ] Game Over 時に画面中央に「GAME OVER」と大きく表示した
- [ ] 下の方に「Rキーでリスタート」とメッセージを出した
- [ ] プレイ中は、Day3相当のHUD（スコアなど）も残している

#### サンプルコード（考え方）

```python
        msg = ""
        if self.gameover:
            msg = "GAME OVER  -  Press R to Restart"

        self.hud.text = f"Score: {self.score}" + ("" if not msg else "\n" + msg)
```

> ✅ Cさんは「**プレイヤーへの声かけ担当**」です。  
> ちょっとした一言で、ゲームの印象が変わります。

---

### 3-4. D：リスタート処理担当

**目的**：Rキーが押されたときにゲームを最初からやり直せるようにする。

- 触るファイル：`main_day4.py`
- 主に `RunnerGame` に `reset()` メソッドを追加し、`_kd` で呼び出す

#### Dさんのチェックリスト

- [ ] `reset()` で、スコア／時間／スクロール／障害物／エフェクトなどを初期状態に戻した
- [ ] Rキーが押されたとき、`self.gameover` が True なら `reset()` を呼ぶようにした
- [ ] リスタート後にもう一度遊べることを確認した

#### サンプルコード（考え方）

```python
    def reset(self):
        self.scroll = 0.0
        self.time = 0.0
        self.score = 0
        self.gameover = False
        self.obstacles = []
        self.effects = []
        self.y = self.ground
        self.vy = 0.0
        self.on_ground = True

    def _kd(self, win, key, *a):
        self.keys.add(key)
        if self.gameover and key in (ord("r"), ord("R")):
            self.reset()
            return True
        # それ以外のキーは、Day3相当の処理へ（ジャンプなど）
```

> ✅ Dさんは「**何度でも遊べるようにする人**」です。  
> 初期化し忘れが無いか、Gさんと一緒にチェックしましょう。

---

### 3-5. E：サウンドフック担当（任意）

**目的**：ジャンプやゲームオーバーのタイミングで、サウンドを鳴らせるような“入り口”を作る。

- 触るファイル：`main_day4.py`, （必要なら）`assets/`
- Kivy の `SoundLoader` を使う想定（音源ファイルは先生と相談）

#### Eさんのチェックリスト

- [ ] `from kivy.core.audio import SoundLoader` を追加した
- [ ] `self.jump_sound` / `self.over_sound` などの変数を用意した
- [ ] ジャンプ開始時／ゲームオーバー時に `.play()` を呼び出している
- [ ] 音源ファイルが無い場合でもエラーで止まらないように try/except などを入れた

#### サンプルコード（考え方）

```python
from kivy.core.audio import SoundLoader

class RunnerGame(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        # ...
        self.jump_sound = SoundLoader.load("assets/jump.wav")
        self.over_sound = SoundLoader.load("assets/gameover.wav")

    def play_jump_sound(self):
        if self.jump_sound:
            self.jump_sound.play()

    def play_over_sound(self):
        if self.over_sound:
            self.over_sound.play()
```

> ✅ Eさんは「**耳からの気持ちよさ担当**」です。  
> 音源が用意できない場合は、「ここで音を鳴らしたい」というコメントだけでも十分価値があります。

---

### 3-6. F：つなぎ込み担当（今日のハブ）

**目的**：A〜Eの作った機能を `main_day4.py` に矛盾なく組み込み、最終的な「完成版」を作る。

- 触るファイル：`main_day4.py` 全体
- 必要に応じて、他の人のコードに小さな修正を加える（そのときは必ず相談）

#### Fさんのチェックリスト

- [ ] エフェクトリストの構造を、A/B/Eで共通化できている
- [ ] Game Over の判定タイミングと、Game Over 演出／サウンドの呼び出し順が自然
- [ ] `reset()` の中で、エフェクトやサウンドの状態が変になっていない
- [ ] エラーなく起動し、ひととおり遊べるレベルまで動作している

> ✅ Fさんは「**仕上げの監督**」です。  
> どこかが難しければ、「ここは次回の宿題に回そう」と決めるのも立派な判断です。

---

### 3-7. G：テスト＆バグログ担当

**目的**：ゲームを何度も遊んでみて、バグや「もっとこうしたい」を文章に残す。

- 触るファイル：`docs/Day4_buglog.md`（新規作成してOK）

#### Gさんのチェックリスト

- [ ] ジャンプ／着地のエフェクトが期待通りか確認した
- [ ] Game Over → Rキーでリスタートができることを確認した
- [ ] 「重くなる」「チカチカしすぎる」などの感想も含めてメモした

#### バグログのテンプレ

```text
【2025-xx-xx Day4 バグログ】

■バグ1：Rでリスタートしてもエフェクトが残る
内容：
    ゲームオーバー→Rキーでリスタートすると、古いエフェクトが画面に残っている。
原因（予想）：
    reset() で self.effects を空にしていない。
対策：
    reset() の中で self.effects = [] を追加したら直った。

■改善アイデア1：ゲーム開始前にカウントダウンを入れたい
内容：
    いきなり動き出すのではなく、「3,2,1,Go!」と表示したい。
メモ：
    次回以降の発展として、startフラグとタイマーを追加したい。
```

---

## 4. 全員共通のNGリスト

- `main_day1.py` / `main_day2.py` / `main_day3.py` は、参考にしてもよいが **保存しないこと**
- 他の人の担当コードを「全部書き換える」のはNG（相談のうえで小さな修正はOK）
- 動作が重くなったら、まず Gさんと相談してログに書いてから、どこを軽くするか考える

---

## 5. 今日のまとめメモ欄（クラス用）

- 今日できたこと：

- 次にやりたいこと（演出の発展案など）：
