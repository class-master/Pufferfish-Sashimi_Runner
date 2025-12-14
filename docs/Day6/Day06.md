# Day6：ディレクトリ矯正（パスを統一して“どこから実行しても壊れない”）（7人×3時間用シナリオ／生徒用）

## 0. 今日のゴール

3時間で、次の3つができるようになることを目指します。

1. 実行場所（カレントディレクトリ）が違っても、ゲームが壊れない  
2. 画像・音などの参照を「正しいパスの取り方」に統一できる  
3. `assets/...` のような“生文字列パス”をコード中に散らさないで済むようにする  

Day6は「新機能を増やす日」ではなく、**土台を正しい姿に矯正する日**です。  
この土台ができると、Day7以降の追加開発が一気に楽になります。

### 今日の達成条件（これだけでOK）
- **カレント（実行場所）に依存せず**素材が見つかる  
- 素材参照は **`utils/paths.py` 経由に統一**（生文字列は禁止）  
- `ふぐ刺身/` は“旧置き場”として残しても、**実行コードから参照しない**  

---

## 1. 今日触るファイル

- `main_day6.py`（今日のメイン。全員が開く）  
- `utils/paths.py`（パス矯正の核。最重要）  
- `docs/Day6/Day06.md`（このプリント）  
- `docs/Day6/Day6_buglog.md`（バグログ）

**重要：** Day1〜Day5（`main_day1.py`〜`main_day5.py`、既存docs）は原則変更しません。  
（読むのはOK。直したくなっても今日は我慢）

---

## 2. 今日のルール（事故防止）

- `os.getcwd()`（今いる場所）を基準にパスを作らない  
- `assets/xxx.png` を生文字列で書かない  
- 迷ったら「このコード、別フォルダから実行しても動く？」を確認する  
- `ふぐ刺身/` フォルダは“素材置き場になっている”が、Day6では **参照先を repo直下に統一**する  

---

## 3. 7人の役割（例）

| No | 役割名 | ざっくりやること |
|----|--------|------------------|
| A  | パス矯正担当 | `utils/paths.py` を完成させる（REPO_ROOT/ASSETS/BGM） |
| B  | 起動点担当 | `main_day6.py` を作り、起動時に `sanity_check()` する |
| C  | 画像担当 | `assets/neon_banner.png` を Day6で表示する（パスは統一関数経由） |
| D  | 音担当 | `bgm.ogg` を Day6で再生する（パスは統一関数経由） |
| E  | コード清掃担当 | “生文字列パス”が出てくる箇所を探し、置き換え方針をメモする |
| F  | つなぎ込み担当 | A〜Dの成果を衝突なく統合して動く状態にする |
| G  | テスト＆バグログ担当 | 実行場所を変えてテストし、`Day6_buglog.md` に記録する |

---

## 4. 今日の時間割（目安）

- 0:00〜0:10　今日の狙い共有（壊れる理由＝カレント依存）＋役割決め
- 0:10〜1:10　A/B：土台（paths + main_day6）を先に固める
- 1:10〜2:10　C/D：画像表示・BGM再生（paths経由で成功させる）
- 2:10〜2:40　F：統合＆小修正
- 2:40〜3:00　G：実行場所を変えてテスト＋バグログ＋まとめ

---

## 5. まず作る：`main_day6.py`（最小の動作確認）

**目的：** 「pathsが効いている」ことを一発で確認する。  
以下の2つができればDay6は成功です。

- バナー画像が表示される（neon_banner.png）
- BGMが鳴る（bgm.ogg）

（※ゲーム本編はDay7以降でOK）

### サンプル（例：Day6の最小起動）
```python
from kivy.app import App
from kivy.uix.image import Image
from kivy.core.audio import SoundLoader

from utils.paths import sanity_check, asset_path, repo_path

class Day6App(App):
    def build(self):
        sanity_check()

        banner = Image(source=asset_path("neon_banner.png"))

        sound = SoundLoader.load(repo_path("bgm.ogg"))
        if sound:
            sound.loop = True
            sound.play()

        return banner

if __name__ == "__main__":
    Day6App().run()
```

---

## 6. テスト（ここが本番）

次の“実行場所違い”で、同じように動けば勝ちです。

- ケース1：リポジトリ直下で実行  
  - `python main_day6.py`

- ケース2：`docs/Day6` に移動して実行（カレントをわざと変える）  
  - `python ../../main_day6.py`

- ケース3：`ふぐ刺身/` に移動して実行（さらに意地悪）  
  - `python ../main_day6.py`

---

## 7. 今日のまとめ（1行でOK）

- 今日の学び（1行）：
- 「壊れない土台」の条件は何だった？：
- 次（Day7）に進めたいこと（1つだけ）：
