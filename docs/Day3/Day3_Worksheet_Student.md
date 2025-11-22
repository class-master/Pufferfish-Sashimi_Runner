# Day3：レーン切り替えと速度カーブの日（7人×3時間用シナリオ）

## 0. 今日のゴール（先生が最初に読む用）

3時間で、次を「クラス全体」として完成させます。

1. ランナーが **Up / Down キーで上下2レーンを切り替えられる**  
2. 障害物がそれぞれのレーンに出現し、**同じレーンにいるときだけ当たり判定が発生する**  
3. 時間がたつほど **少しずつスピードアップ** し、HUD に「スコア＋現在レーン＋速度」が表示される  

### 絶対ルール

- `main_day1.py` / `main_day2.py` は **書き換え禁止**
- 触るファイルは、基本的に `main_day3.py` と `docs/Day3_buglog.md`、必要なら `config.py` のみ
- 迷ったら先生かこのプリントに必ず戻る

---

## 1. 今日の7人の役割（先に割り当てる）

| No | 役割名                     | 触るファイル         | ざっくりやること                                   |
|----|----------------------------|----------------------|----------------------------------------------------|
| A  | レーン設計担当             | `main_day3.py`       | レーンの本数とY座標、プレイヤーのレーン番号を決める |
| B  | 入力＆レーン切替担当       | `main_day3.py`       | Up/Downキーでレーン変更＆Y座標を更新               |
| C  | 障害物レーン担当           | `main_day3.py`       | 障害物にレーン情報を持たせ、同じレーンだけ当たり判定|
| D  | 速度カーブ＆スコア担当     | `main_day3.py`       | `_speed()` を調整し、スコアや「距離」の計算を整える |
| E  | HUD表示＆デバッグ表示担当  | `main_day3.py`       | HUDにレーン・速度情報を表示する                    |
| F  | つなぎ込み担当             | `main_day3.py`       | A〜Eの変更を1つの `RunnerGame` に統合する          |
| G  | テスト＆バグログ担当       | `docs/Day3_buglog.md`| 動作確認とバグ／改善アイデアの記録                 |

> 先生へ：  
> A〜G に生徒の名前を書き込んで配ってください。  
> 例：A=太郎、B=花子、… のように。

---

## 2. 今日の時間割（板書用）

- 0:00〜0:10　Day1/Day2 の復習と、Day3のゴール説明
- 0:10〜0:20　役割分担と作戦会議（誰がどこを触るか）
- 0:20〜1:10　**個人作業タイム**（A〜E中心にコーディング）
- 1:10〜2:00　**結合タイム**（Fがハブになって `main_day3.py` を1本にまとめる）
- 2:00〜2:40　テスト＆デバッグ（G主導でバグ洗い出し）
- 2:40〜3:00　今日のまとめ・スクリーンショット撮影など

---

## 3. 各役割の「やることチェックリスト」

### 3-1. A：レーン設計担当

**目的**：上下2レーンの「高さ」と、プレイヤーがどのレーンにいるかを管理できるようにする。

- 触るファイル：`main_day3.py`
- 主に `RunnerGame` クラスの `__init__` 付近を編集

#### Aさんのチェックリスト

- [ ] レーンの本数を `self.lanes = [GROUND_Y, GROUND_Y + 80]` などのリストで決めた
- [ ] プレイヤーの現在のレーン番号 `self.lane_index`（0 or 1）を追加した
- [ ] プレイヤーの `y` 座標を、`self.lanes[self.lane_index]` から計算するようにした

#### サンプルコード（ほぼコピペOK）

```python
class RunnerGame(Widget):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.size = (WIDTH, HEIGHT)
        self.scroll = 0.0
        self.base_speed = SPEED
        self.time = 0.0

        # Day3: レーンの高さ（0: 下段, 1: 上段）
        self.lanes = [GROUND_Y, GROUND_Y + 80]
        self.lane_index = 0  # 最初は下段

        # プレイヤーの位置と大きさ
        self.x = 120; self.w = 32
        self.h = 32
        self.ground = self.lanes[self.lane_index]
        self.y = self.ground
```

> ✅ Aさんは「**世界の“線路”を決める人**」です。  
> ジャンプや当たり判定の中身は、B/C/Dと相談しながら決めてOK。

---

### 3-2. B：入力＆レーン切替担当

**目的**：Up/Downキーで `lane_index` を変え、プレイヤーのY座標を切り替える。

- 触るファイル：`main_day3.py`
- 主に `RunnerGame._kd`（キーが押されたとき）を編集

#### Bさんのチェックリスト

- [ ] Upキーで `lane_index` を1つ上げる（上限チェックあり）
- [ ] Downキーで `lane_index` を1つ下げる（下限チェックあり）
- [ ] レーンが変わったら `self.ground` と `self.y` を更新する
- [ ] Game Over 中はレーンが変わらないようにした

#### サンプルコード（キーコードは環境に合わせて調整）

```python
    def _kd(self, win, key, *a):
        self.keys.add(key)
        if self.gameover:
            return True

        # Space: ジャンプ（Day1/Day2 と同じ）
        if key == 32 and self.on_ground:
            self.vy = JUMP_VEL; self.on_ground = False

        # Up/Down でレーン変更（例：273=Up, 274=Down）
        if key == 273:
            if self.lane_index < len(self.lanes) - 1:
                self.lane_index += 1
        elif key == 274:
            if self.lane_index > 0:
                self.lane_index -= 1

        # レーン変更後に地面の高さを更新
        self.ground = self.lanes[self.lane_index]
        if self.on_ground:
            self.y = self.ground
        return True
```

> ✅ Bさんは「**プレイヤー操作の気持ちよさ担当**」です。  
> 細かい高さや操作感は、AさんやEさんと相談しながら調整しましょう。

---

### 3-3. C：障害物レーン担当

**目的**：障害物にもレーン情報を持たせ、同じレーンにいるときだけ当たり判定をする。

- 触るファイル：`main_day3.py`
- 主に `spawn_obstacle` と `update` の当たり判定部分を編集

#### Cさんのチェックリスト

- [ ] 障害物データに `lane_index`（0 or 1）を追加した  
      （例： `[x, y, w, h, lane]` のようにする）
- [ ] `spawn_obstacle` でランダムに 0 or 1 のレーンを選んでいる
- [ ] 当たり判定のとき、**プレイヤーと同じレーンの障害物だけ** 判定している

#### サンプルコード（考え方）

```python
    def spawn_obstacle(self):
        import random
        gap = random.choice([260, 320, 380])
        last_x = max([o[0] for o in self.obstacles], default=self.width + 100)
        x = max(self.width + 60, last_x + gap)
        w = random.choice([26, 32, 40])
        h = random.choice([26, 32, 44])

        lane = random.choice([0, 1])
        y = self.lanes[lane]
        self.obstacles.append([x, y, w, h, lane])
```

当たり判定側：

```python
        for (ox, oy, ow, oh, olane) in self.obstacles:
            if olane != self.lane_index:
                continue  # 別レーンの障害物は当たらない
            if self.aabb(self.x, self.y, self.w, self.h, ox, oy, ow, oh):
                self.gameover = True
```

> ✅ Cさんは「**敵の配置と理不尽さを決める人**」です。  
> クリア不能なパターンが出ないように、A/B/D/Eと相談してバランスを取りましょう。

---

### 3-4. D：速度カーブ＆スコア担当

**目的**：`_speed()` を時間で少しずつ上げていき、スコアの伸び方も気持ちよくする。

- 触るファイル：`main_day3.py`
- 主に `_speed` 関数と `update` 内の `self.score` 計算

#### Dさんのチェックリスト

- [ ] `self.time` を使って、ゲーム開始からの経過時間を秒単位で増やしている
- [ ] `_speed()` が、最初はゆっくり、少しずつ早くなる形になっている
- [ ] スコアが「距離」に近いイメージで増えていくようになっている

#### サンプルコード

```python
    def _speed(self):
        # Day2 のコメントにあった「時間で少しずつ加速」をちゃんと作る
        t = self.time
        base = self.base_speed
        extra = min(6.0, t * 0.05)  # 0秒で+0、120秒で+6 くらい
        return base + extra
```

`update` 内の一部：

```python
        if not self.gameover:
            spd = self._speed()
            self.scroll += spd
            self.time += dt
            self.score += int(spd)
```

> ✅ Dさんは「**ゲームのテンポ担当**」です。  
> 速すぎて一瞬で死ぬようなら、係数を下げてみてください。

---

### 3-5. E：HUD表示＆デバッグ表示担当

**目的**：画面左上のHUDに「スコア＋レーン＋速度」を表示して、調整しやすくする。

- 触るファイル：`main_day3.py`
- 主に `__init__` の `Label` と `draw` の最後あたり

#### Eさんのチェックリスト

- [ ] HUDのテキストに「Score」「Lane」「Speed」を含めた
- [ ] レーン番号は 1/2 のように、人間に分かりやすく表示している
- [ ] 速度は小数第1位くらいまで表示している

#### サンプルコード

```python
        self.hud = Label(text="", pos=(12, HEIGHT-28))
        self.add_widget(self.hud)
```

`draw` の最後：

```python
        lane_no = self.lane_index + 1
        spd = self._speed()
        self.hud.text = f"Score: {self.score}  Lane: {lane_no}  Speed: {spd:.1f}"             + ("  — GAME OVER" if self.gameover else "")
```

> ✅ Eさんは「**見える化担当**」です。  
> A〜Dが調整しやすいように、知りたい数字を表示してあげましょう。

---

### 3-6. F：つなぎ込み担当（今日のハブ）

**目的**：A〜Eが作った変更を `main_day3.py` で矛盾なく動くように整える。

- 触るファイル：`main_day3.py`（全体）
- 他の人のコードも編集する可能性あり（必ず相談してから）

#### Fさんのチェックリスト

- [ ] `self.lanes` / `self.lane_index` / `self.ground` / `self.y` の関係が破綻していない
- [ ] 障害物リストの形（要素数）が全ての処理で一致している
- [ ] `_speed()` の使い方が `update` と HUD 内で同じ
- [ ] エラーが出ないところまで 全員のコードを接続できた

> ✅ Fさんは「**プロジェクトマネージャー兼エンジニア**」の役割です。  
> 分からない点があれば、先生と一緒に「どの担当の仕事か」を整理していきましょう。

---

### 3-7. G：テスト＆バグログ担当

**目的**：いろいろなパターンでプレイして、バグと改善アイデアを文章に残す。

- 触るファイル：`docs/Day3_buglog.md`（新規作成してOK）

#### Gさんのチェックリスト

- [ ] `python main_day3.py` でゲームが起動するか確認した
- [ ] レーン切り替えが期待通りに動くか試した
- [ ] 「絶対よけられない障害物」など、気になる点を見つけた
- [ ] バグや改善点を 1件ずつ `Day3_buglog.md` に書いた

#### バグログのテンプレ

```text
【2025-xx-xx Day3 バグログ】

■気づき1：レーンの高さが近すぎて違いが分かりにくい
内容：
    上下レーンがほぼ同じに見えてしまう。
提案：
    lanesの値を [GROUND_Y, GROUND_Y + 120] にしてみる。

■バグ1：Up/Downを連打するとキャラが空中で止まる
内容：
    ジャンプ中にレーン変更すると y がずれる。
提案：
    on_ground のときだけレーン変更を許可する。
```

---

## 4. 全員共通のNGリスト

- `main_day1.py` / `main_day2.py` は開いて読んでもよいが **保存しないこと**
- 他の人の担当部分を勝手に削除しない（修正するときは声をかける）
- 意味の分からないエラーを「無かったこと」にしない  
  → Gさんと一緒にバグログにメモしてから、先生に相談する

---

## 5. 今日のまとめメモ欄（クラス用）

- 今日できたこと：

- 次にやりたいこと（Day4 への宿題案など）：
