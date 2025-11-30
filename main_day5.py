# -*- coding: utf-8 -*-
"""
Neon Runner C — Day5（生徒用）Kivy/KivyMD
到達：タイトル画面→カウントダウン→ランゲーム→GameOver→Rでリスタート
このファイルでは「ゲーム全体の流れ（状態遷移）」を練習します。
"""
import random

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label

from config import WIDTH, HEIGHT, GROUND_Y, SPEED, JUMP_VEL, GRAVITY, BG


class RunnerGame(Widget):
    """画面全体を管理するクラス（Day5 生徒用）。

    Day4 までは「ジャンプや障害物など、1つの場面の中の動き」が中心でした。
    Day5 では、さらに一段上の考え方として

        - タイトル画面
        - カウントダウン
        - ランゲーム本編
        - GameOver画面

    といった「場面（状態）」を `mode` という変数で切り替える、というアイデアを使います。
    """

    def __init__(self, **kw):
        super().__init__(**kw)

        # ウィンドウサイズをプロジェクト共通設定にそろえる
        Window.size = (WIDTH, HEIGHT)

        # ランゲーム部分の状態をまとめて初期化
        self.reset_core_state()

        # 画面左上：HUD（スコアなどの情報表示用）
        self.hud = Label(text="", pos=(12, HEIGHT - 28))
        self.add_widget(self.hud)

        # 画面中央：タイトル／カウントダウン／GameOver などのメッセージ表示用
        self.center_message = Label(
            text="",
            font_size="32sp",
            pos=(0, HEIGHT // 2 - 16),
            size=(WIDTH, 40),
            halign="center",
            valign="middle",
        )
        # text_size を横幅に合わせておくと、自動で折り返される
        self.center_message.text_size = (WIDTH, None)
        self.add_widget(self.center_message)

        # キーボード入力を受け取る（on_key_down / on_key_up をこのインスタンスに結びつける）
        Window.bind(on_key_down=self._on_key_down, on_key_up=self._on_key_up)

        # 毎フレーム update() を呼び出す（1/60 秒ごと）
        Clock.schedule_interval(self.update, 1 / 60)

        # ゲーム起動直後は「タイトル画面」からスタート
        self.enter_title()

    # ------------------------------------------------------------------
    #  状態（state）をまとめて初期化する場所
    # ------------------------------------------------------------------
    def reset_core_state(self):
        """ランゲーム部分だけを初期化する関数。

        R キーで「もう一度遊ぶ」ときにもこの関数だけを呼び出します。
        プレイヤーの座標・速度・スコア・障害物などをリセットする役割です。
        """
        # 経過時間とスクロール量（速度カーブを作るときに利用）
        self.time = 0.0
        self.scroll = 0.0
        self.base_speed = SPEED

        # プレイヤー（主人公）の基本情報
        self.x = 120
        self.w = 32
        self.ground = GROUND_Y
        self.y = self.ground
        self.h = 32
        self.vy = 0.0
        self.on_ground = True

        # 障害物のリスト（[x, y, w, h] の4つ組）
        self.obstacles = []

        # スコアとゲームオーバーフラグ
        self.score = 0
        self.gameover = False

        # 押されているキーの集合（複数キー同時押しのため）
        self.keys = set()

        # カウントダウン用の残り秒数（例：3.0秒からスタート）
        self.countdown = 3.0

    # ------------------------------------------------------------------
    #  場面切り替え用のメソッド群
    # ------------------------------------------------------------------
    def enter_title(self):
        """タイトル画面に入るときに呼ぶ。

        - mode を "title" にセットする
        - 中央メッセージにタイトルと操作説明を書く
        - スコアなどはリセットしない（前のスコアを表示してもよい）
        """
        # TODO: ここで mode を "title" にする
        # 例: self.mode = "title"

        # もう一度タイトルに戻ってきたときのためにフラグを戻しておく
        self.gameover = False
        self.countdown = 3.0

        # TODO: self.center_message.text にタイトル文字列を書く
        # 例: "Neon Runner C\n[Enter] でスタート"

    def start_countdown(self):
        """タイトルからカウントダウン状態に入る。

        Enter キーが押されたときなどに呼びます。
        ここでは

        - mode を "countdown" にする
        - countdown を 3.0 にリセットする
        - 画面中央に最初の数字（3）を表示する

        といった処理を入れてみましょう。
        """
        # TODO: ここで mode, countdown, center_message.text を設定する

    def start_gameplay(self):
        """カウントダウンが終わったら、実際のランゲームを開始する。"""
        # ランゲームの物理状態を初期化
        self.reset_core_state()
        # TODO: mode を "playing" にする
        # TODO: center_message を空文字列にして非表示にする

    def game_over(self):
        """プレイヤーが障害物にぶつかったときに呼ぶ。"""
        self.gameover = True
        # TODO: mode を "gameover" にする
        # TODO: center_message に GameOver メッセージを書く
        # 例: "GAME OVER\n[R]で再スタート / [Enter]でタイトルへ"

    # ------------------------------------------------------------------
    #  キーボード入力
    # ------------------------------------------------------------------
    def _on_key_down(self, win, key, scancode, codepoint, modifiers):
        """キーが押されたときに呼ばれる。

        - key には数値のキーコードが入る（例：Space=32, Enter=13, 'r'=ord('r')）
        - mode によって「同じキーでも意味が変わる」のがポイント
        """
        # 押されているキーを集合に記録しておく（長押し判定などに利用可能）
        self.keys.add(key)

        # TODO: mode ごとにキーの意味を切り替える
        # if self.mode == "title":
        #     if key == 13:  # Enter
        #         self.start_countdown()
        #
        # elif self.mode == "countdown":
        #     # カウントダウン中は誤操作防止のため、基本的に何もしない
        #     pass
        #
        # elif self.mode == "playing":
        #     # Space（32）でジャンプ
        #     if key == 32 and self.on_ground and not self.gameover:
        #         self.vy = JUMP_VEL
        #         self.on_ground = False
        #
        # elif self.mode == "gameover":
        #     if key == ord("r"):
        #         # もう一度あそぶ：カウントダウンからやり直し
        #         self.start_countdown()
        #     elif key == 13:
        #         # タイトルに戻る
        #         self.enter_title()

        return True

    def _on_key_up(self, win, key, *args):
        """キーが離されたときに呼ばれる。"""
        # 押されているキー集合から取り除く（長押し管理用）
        self.keys.discard(key)
        return True

    # ------------------------------------------------------------------
    #  ゲームロジック（速度・障害物・当たり判定など）
    # ------------------------------------------------------------------
    def _speed(self):
        """時間経過で少しずつ速くなるスクロール速度を計算する。

        Day1〜4 と同じように、time に応じて速度を上げていきます。
        """
        return self.base_speed + min(6.0, self.time * 0.05)

    def spawn_obstacle(self):
        """障害物を1つ追加する。

        gap（すきま）の値をランダムに変えることで、出現タイミングに変化をつけています。
        """
        gap = random.choice([260, 320, 380])
        last_x = max([o[0] for o in self.obstacles], default=self.width + 100)
        x = max(self.width + 60, last_x + gap)
        w = 40
        h = 40
        y = self.ground
        self.obstacles.append([x, y, w, h])

    def aabb(self, ax, ay, aw, ah, bx, by, bw, bh):
        """2つの長方形が重なっているかどうか（Axis Aligned Bounding Box）。

        - (ax, ay)〜(ax+aw, ay+ah) : プレイヤー
        - (bx, by)〜(bx+bw, by+bh) : 障害物
        """
        return not (ax + aw <= bx or bx + bw <= ax or ay + ah <= by or by + bh <= ay)

    # ------------------------------------------------------------------
    #  メインループ
    # ------------------------------------------------------------------
    def update(self, dt):
        """毎フレーム呼ばれるメインループ。

        `mode` によってやることを切り替えるのが Day5 の一番のテーマです。
        """
        # 1) タイトル中は物理シミュレーションを動かさず、画面だけ描いて終わり
        # TODO: if self.mode == "title": ... のように分岐を書いてみよう

        # 2) カウントダウン中は、残り時間 countdown を dt だけ減らす
        #    0 以下になったら start_gameplay() を呼び、return する。
        # TODO: "countdown" 用の分岐を追加してみよう

        # ここから下は「playing 中だけ動かす処理」というつもりで読んでください。
        if self.gameover:
            # GameOver 中は描画だけ行う
            self._draw()
            return

        # 経過時間と現在のスクロール速度
        self.time += dt
        spd = self._speed()

        # 重力・ジャンプ処理
        if not self.on_ground:
            self.vy -= GRAVITY
            self.y += self.vy
            if self.y <= self.ground:
                self.y = self.ground
                self.vy = 0
                self.on_ground = True

        # 障害物の生成と更新
        if not self.obstacles or (self.obstacles and self.obstacles[-1][0] < self.width):
            if random.random() < 0.04:
                self.spawn_obstacle()
        for o in self.obstacles:
            o[0] -= spd
        # 画面外に出た障害物を捨てる
        self.obstacles = [o for o in self.obstacles if o[0] + o[2] > -40]

        # 当たり判定とスコア加算
        for (ox, oy, ow, oh) in self.obstacles:
            if self.aabb(self.x, self.y, self.w, self.h, ox, oy, ow, oh):
                self.game_over()
                break
        if not self.gameover:
            self.score += int(spd)

        # 最後に描画
        self._draw()

    # ------------------------------------------------------------------
    #  描画処理
    # ------------------------------------------------------------------
    def _draw(self):
        """現在の状態をもとに画面を描き直す。"""
        self.canvas.clear()
        with self.canvas:
            # 背景
            Color(*BG)
            Rectangle(pos=self.pos, size=self.size)

            # 地面
            Color(0.25, 0.8, 0.9, 1)
            Rectangle(pos=(0, self.ground - 6), size=(self.width, 6))

            # タイトル／カウントダウン中にランナーや障害物を描くかどうかはお好み
            if hasattr(self, "mode") and self.mode in ("title", "countdown"):
                pass
            else:
                # 障害物
                Color(1.0, 0.45, 0.2, 1)
                for (ox, oy, ow, oh) in self.obstacles:
                    Rectangle(pos=(ox, oy), size=(ow, oh))
                # ランナー
                Color(0.95, 0.2, 0.6, 1)
                Rectangle(pos=(self.x, self.y), size=(self.w, self.h))

        # HUD（左上の文字）と中央メッセージを更新
        if hasattr(self, "mode"):
            if self.mode == "title":
                self.hud.text = "Neon Runner C — Day5 / [Enter]でスタート"
            elif self.mode == "countdown":
                # カウントダウンの残り秒数（だいたいの整数）を表示
                self.hud.text = f"Get Ready... {int(self.countdown) + 1}"
            elif self.mode == "playing":
                self.hud.text = f"Score: {self.score}"
            elif self.mode == "gameover":
                self.hud.text = f"Score: {self.score}  — GAME OVER"
        else:
            self.hud.text = f"Score: {self.score}"


class NeonRunnerDay5(App):
    def build(self):
        return RunnerGame()


if __name__ == "__main__":
    NeonRunnerDay5().run()
