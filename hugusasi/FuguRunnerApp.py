from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.core.audio import SoundLoader
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle
from kivy.uix.video import Video
import os, random, sys
from pathlib import Path

# --- 画面サイズ ---
Window.size = (1000, 600)

# --- パスヘルパー (PyInstaller対応) ---
def get_base_path():
    """アプリケーションのベースパスを取得する。"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

def assets_path(*parts):
    return os.path.join(get_base_path(), "assets", *parts)

def get_font_path():
    p = assets_path("GenShinGothic-Regular.ttf")
    return p if os.path.exists(p) else ""

def safe_asset(path):
    """アセットの存在をチェックし、なければ空文字列を返す"""
    return path if os.path.exists(path) else ""

# ====================================================================
# --- ゲームオブジェクト ---
# ====================================================================

class Fugu(Image):
    velocity_y = NumericProperty(0)
    gravity = NumericProperty(-0.5)
    jump_power = 10 
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = safe_asset(assets_path("fugu.png"))
        self.size = (80, 80) # ★修正: Fuguのサイズを大きく (80, 80) に変更
        self.pos = (100, 120) # ★修正: Fuguの初期位置をY=120に変更
        self.is_jumping = False
        
    def update(self, blocks):
        self.velocity_y += self.gravity
        self.y += self.velocity_y
        
        # 地面との衝突
        if self.y < 0:
            self.y = 0
            self.velocity_y = 0
            self.is_jumping = False
            
        # ブロックとの衝突
        for block in blocks:
            if self.collide_widget(block):
                # ブロックの上に乗る判定を調整。Fuguがブロックの上面にいるか、
                # かつ下降中（またはほぼ停止中）の場合に足場とする。
                fugu_on_top_of_block = (
                    self.y >= block.top - 5 and # Fuguの底がブロックの上面より少し上にある
                    self.y < block.top + 15 and # Fuguの底がブロックの上面から少し上まで
                    self.velocity_y <= 0 # 下降中または停止中
                )
                
                if fugu_on_top_of_block:
                    self.y = block.top 
                    self.velocity_y = 0
                    self.is_jumping = False
                    return
                # ブロックの横や下との衝突はここでは無視（通常の横スクロールアクションの挙動に合わせる）
                
        # 天井との衝突
        if self.y > Window.height - self.size[1]:
            self.y = Window.height - self.size[1]
            self.velocity_y = 0

    def jump(self):
        if not self.is_jumping:
            self.velocity_y = self.jump_power
            self.is_jumping = True

    def check_hit(self, other_widget):
        if not self.collide_widget(other_widget):
            return "MISS"
            
        fugu_bottom = self.y + self.size[1] * 0.2 
        fugu_top = self.y + self.size[1] * 0.8
        
        other_top = other_widget.top
        other_y = other_widget.y

        if isinstance(other_widget, Boss):
            # ボスの頭上に着地（踏みつけ）判定
            if (fugu_bottom > other_top - 20) and (fugu_bottom < other_top + 10) and (self.velocity_y < 0):
                self.velocity_y = self.jump_power * 0.7 # 再ジャンプ
                return "BOSS_HIT"
            
            # ボスへの体当たり判定（即ゲームオーバー）
            if fugu_top > other_y + 10: # Fuguの上がボスの下より高い位置にある（=体当たり）
                return "GAME_OVER"
            return "MISS"

        if isinstance(other_widget, Obstacle):
            return "GAME_OVER"
            
        return "MISS" 

class Obstacle(Image):
    speed = NumericProperty(5) 

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = safe_asset(assets_path(random.choice(["block.png", "bom.png"])))
        self.size = (80, 80)
        # ★修正: Y座標を地面付近に限定 (0〜10)
        self.pos = (Window.width, random.randint(0, 10)) 
        
    def update(self, dt):
        self.x -= self.speed
        if self.right < 0:
            if self.parent:
                self.parent.remove_widget(self)
            
class Boss(Image):
    speed = NumericProperty(2) 
    hits_required = 5
    current_hits = 0
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = safe_asset(assets_path("boss.png"))
        self.size = (150, 150)
        self.y = Window.height / 2 - self.size[1] / 2
        self.x = Window.width + 10 
        self.target_x = Window.width - 200
        self.is_moving = True

    def update(self, dt):
        if self.current_hits >= self.hits_required:
            # ボス撃破後の消滅
            self.x -= self.speed * 5 # より速く画面外へ
            if self.right < 0:
                return "CLEARED" 

        if self.is_moving:
            if self.x > self.target_x:
                self.x -= self.speed * 2
            else:
                self.x = self.target_x
                self.is_moving = False
        else:
            # ターゲット位置に達した後、左右に揺れるなどの動きを加えても良いが、今回は静止
            pass

        # ボスがターゲット位置に到達できなかった場合（画面左端を通過しそうになった場合）
        if self.x < 0 and not self.current_hits >= self.hits_required:
            return "FAILED" 
            
        return "CONTINUE"

class Block(Widget):
    speed = NumericProperty(5) 
    
    def __init__(self, block_width, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.width = block_width 
        self.height = 30 # ★修正: ブロックの高さを 30 に減らす
        
        # ブロックのy座標をランダムに設定
        min_y = 50 
        max_y = Window.height / 2 - self.height 
        self.y = random.randint(min_y, int(max_y))
        
        self.x = Window.width 

        with self.canvas:
            Color(0.5, 0.5, 0.5, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)

        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        
    def update(self, dt):
        self.x -= self.speed
        if self.right < 0:
            if self.parent:
                self.parent.remove_widget(self)

# ====================================================================
# --- ゲーム本体 (Game) ---
# ====================================================================
class Game(Widget):
    obstacles = ListProperty([])
    blocks = ListProperty([])
    bosses = ListProperty([])
    
    is_game_over = False
    BOSS_SCORE_THRESHOLD = 10
    is_boss_time = False 

    def __init__(self, spawn_min=1.0, spawn_max=3.0, gravity=-0.5, block_width=150, bgm_volume=0.5, sfx_volume=0.5, **kwargs):
        super().__init__(**kwargs)
        self.spawn_min = max(0.2, float(spawn_min))
        self.spawn_max = max(self.spawn_min, float(spawn_max))
        self.gravity = float(gravity)
        self.block_width = float(block_width)
        self.font_path = get_font_path()
        self.is_boss_time = False
        self.boss_cleared = False
        self.bgm_volume = bgm_volume
        self.sfx_volume = sfx_volume
        self.bgm = None 
        self.final_score_value = 0 # ゲームオーバー/クリア時のスコアを保持するための変数

        # 背景
        self.background = Image(
            source=safe_asset(assets_path("game.png")),
            allow_stretch=True,
            keep_ratio=False,
            size=Window.size,
            pos=(0, 0)
        )
        self.add_widget(self.background)

        # プレイヤー
        self.fugu = Fugu()
        self.fugu.gravity = self.gravity 
        self.add_widget(self.fugu)

        # スコア
        self.score = 0
        self.score_label = Label(
            text="Score: 0",
            size_hint=(None, None),
            pos=(Window.width - 200, Window.height - 50),
            font_size=28,
            font_name=self.font_path,
            color=(1, 1, 1, 1)
        )
        self.add_widget(self.score_label)
        
        # ボスライフ/ヒット表示ラベル
        self.boss_hit_label = Label(
            text="",
            size_hint=(None, None),
            pos=(Window.width / 2 - 100, Window.height - 50),
            font_size=28,
            font_name=self.font_path,
            color=(1, 0, 0, 1)
        )
        self.add_widget(self.boss_hit_label)


        # BGM 
        self.bgm = SoundLoader.load(assets_path("bgm.ogg"))
        if self.bgm:
            try:
                self.bgm.volume = self.bgm_volume
                self.bgm.loop = True
                if self.bgm_volume > 0.0: 
                    self.bgm.play()
            except Exception:
                self.bgm = None

        Clock.schedule_interval(self.update, 1/60.0)
        self.schedule_next_item()

    def _load_sfx(self, filename):
        path = assets_path(filename)
        if not os.path.exists(path):
            return None
        snd = SoundLoader.load(path)
        if snd:
            try:
                snd.volume = self.sfx_volume 
            except Exception:
                pass
        return snd

    def play_sfx(self, filename):
        if self.sfx_volume > 0.0:
            snd = self._load_sfx(filename)
            if snd:
                try:
                    snd.play()
                except Exception:
                    pass

    def stop_all(self):
        if self.is_game_over: return
        self.is_game_over = True
        Clock.unschedule(self.update)
        Clock.unschedule(self.spawn_item)
        
        if self.bgm:
            try:
                self.bgm.stop()
            except Exception:
                pass

        # 全てのゲームオブジェクトを削除
        for o in list(self.obstacles) + list(self.blocks) + list(self.bosses):
            if o.parent:
                o.parent.remove_widget(o)
        self.obstacles.clear()
        self.blocks.clear()
        self.bosses.clear()
        self.boss_hit_label.text = ""
        
        # スコアを確定
        self.final_score_value = self.score

    def update(self, dt):
        if self.is_game_over: return

        self.fugu.update(self.blocks)
        
        # 障害物・ブロックの更新と衝突判定
        for obs in list(self.obstacles):
            obs.update(dt)
            if self.fugu.check_hit(obs) == "GAME_OVER":
                self.game_over_sequence()
                return
            if obs.right < 0:
                if obs in self.obstacles:
                    self.obstacles.remove(obs)
                    self.remove_widget(obs)
                    # ボス戦中でない、かつクリア済みでない場合のみスコア加算
                    if not self.is_boss_time and not self.boss_cleared:
                        self.score += 1
                        self.score_label.text = f"Score: {self.score}"
        
        for block in list(self.blocks):
            block.update(dt)
            if block.right < 0:
                if block in self.blocks:
                    self.blocks.remove(block)
                    self.remove_widget(block)


        # ボスの更新と衝突判定
        for boss in list(self.bosses):
            update_result = boss.update(dt) 
            
            if update_result == "FAILED":
                # ボスが逃げ切った場合
                self.game_over_sequence() 
                if boss.parent: boss.parent.remove_widget(boss)
                self.bosses.remove(boss)
                return
            
            if update_result == "CLEARED":
                # ボス撃破後の画面外退場
                self.game_clear_sequence() 
                if boss.parent: boss.parent.remove_widget(boss)
                self.bosses.remove(boss)
                return # ゲームクリアシーケンスへ移行したのでここでreturn
            
            hit_result = self.fugu.check_hit(boss)
            
            if hit_result == "GAME_OVER":
                self.game_over_sequence()
                return
            
            elif hit_result == "BOSS_HIT":
                self.play_sfx("hit.ogg")
                boss.current_hits += 1
                self.boss_hit_label.text = f"Boss HP: {boss.hits_required - boss.current_hits}"
                
                # ボスが撃破された場合
                if boss.current_hits >= boss.hits_required:
                    # ボスが退場を開始。updateの次の呼び出しで CLEARED になる
                    self.boss_hit_label.text = "BOSS DOWN!"
                    

        # ボス戦開始判定
        if not self.is_boss_time and not self.boss_cleared and self.score >= self.BOSS_SCORE_THRESHOLD:
            self.start_boss_sequence()


    def game_over_sequence(self):
        if self.is_game_over: return
        self.stop_all() # 最終スコアを確定
        
        self.play_sfx("GB__.ogg")
        Clock.schedule_once(lambda _dt: self.play_sfx("叫ぶ.ogg"), 2.0)
        Clock.schedule_once(lambda _dt: self.play_sfx("meme.ogg"), 2.5)
        Clock.schedule_once(self._go_gameover, 2.6)

    def _go_gameover(self, dt):
        app = App.get_running_app()
        if app and hasattr(app, "sm"):
            if not app.sm.has_screen("gameover"):
                # ここに来ることは稀だが、念のため追加
                app.sm.add_widget(GameOverScreen(name="gameover"))
                
            # GameOverScreenにスコアを渡すために on_pre_enter を呼び出す
            app.sm.get_screen("gameover").on_pre_enter()
            app.sm.current = "gameover"

    def game_clear_sequence(self):
        self.boss_cleared = True
        self.stop_all() # 最終スコアを確定
        
        self.play_sfx("clear.ogg")
        # ゲームクリア画面に移行する前にスコア表示を更新
        self.score_label.text = f"クリア！ 最終スコア: {self.final_score_value}"
        
        Clock.schedule_once(self._go_gameover, 5.0) # 5秒後にGameOverScreenへ（GameClear表示のため）
    
    def start_boss_sequence(self):
        self.is_boss_time = True
        
        Clock.unschedule(self.spawn_item) # アイテム出現を停止
        
        # 画面上の障害物・ブロックを全て削除
        for o in list(self.obstacles) + list(self.blocks):
            if o.parent:
                o.parent.remove_widget(o)
        self.obstacles.clear()
        self.blocks.clear()
        
        Clock.schedule_once(self._spawn_boss, 1.0) # 1秒後にボス出現
        
        # ボス戦開始時にフグを大きくジャンプさせる
        self.fugu.velocity_y = self.fugu.jump_power * 1.5

    def _spawn_boss(self, dt):
        if self.is_game_over or self.boss_cleared: return
        
        if len(self.bosses) > 0: 
            return

        boss = Boss()
        self.bosses.append(boss)
        self.add_widget(boss)
        
        self.play_sfx("boss_appear.ogg")
        
        self.boss_hit_label.text = f"Boss HP: {boss.hits_required - boss.current_hits}"


    def spawn_item(self, dt):
        if self.is_game_over: return
        
        if self.is_boss_time:
            # ボス戦中はアイテムは出さない（ボスの退場ロジックに任せる）
            return 
        
        # アイテム出現ロジック（ランダムに障害物かブロックを生成）
        if random.random() < 0.7: 
            item = Obstacle()
            self.obstacles.append(item)
        else: 
            item = Block(block_width=self.block_width) 
            self.blocks.append(item)
        
        self.add_widget(item)
        self.schedule_next_item()


    def schedule_next_item(self):
        if self.is_game_over or self.is_boss_time: return
        
        delay = random.uniform(self.spawn_min, self.spawn_max) 
        Clock.schedule_once(self.spawn_item, delay)

    def on_touch_down(self, touch):
        if not self.is_game_over:
            self.fugu.jump()

# ====================================================================
# --- スクリーン管理 ---
# ====================================================================

class VideoBackground(Video):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = 'play'
        self.options = {'loop': True}
        self.allow_stretch = True
        self.keep_ratio = False # 縦横比を維持しない
        self.size_hint = (1, 1)
        self.pos = (0, 0)
        
        if 'source' in kwargs:
             self.source = kwargs['source']
        
    def play_video(self):
        # sourceが設定されていることを確認してから再生
        if self.source and self.state != 'play':
            self.state = 'play'

    def stop_video(self):
        if self.state != 'stop':
            self.state = 'stop'

# --- HomeScreen（ホーム画面） --- 
class HomeScreen(Screen):
    HOME_VIDEO_FILENAME = "kabe.mp4" 
    HOME_IMAGE_FILENAME = "game.png"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_path = get_font_path()
        
        self.video_source = safe_asset(assets_path(self.HOME_VIDEO_FILENAME))
        self.image_source = safe_asset(assets_path(self.HOME_IMAGE_FILENAME))
        
        self.video_bg = None
        self.image_bg = None

        # --- 背景のセットアップ ---
        if self.video_source:
            # 動画ファイルを背景として使用
            self.video_bg = VideoBackground(source=self.video_source)
            self.add_widget(self.video_bg)
        else:
            # 動画ファイルがない場合、画像を使用
            self.image_bg = Image(
                source=self.image_source, # safe_assetはクラス外部で処理済み
                allow_stretch=True,
                keep_ratio=False,
                size=Window.size,
                pos=(0, 0)
            )
            self.add_widget(self.image_bg)


        # --- メニューUIのセットアップ (BoxLayoutで中央に配置) ---
        root = BoxLayout(orientation='vertical', padding=50, spacing=30, size_hint=(0.8, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        # 黒い半透明の背景を追加して文字を見やすくする
        with root.canvas.before:
            Color(0, 0, 0, 0.5)
            self.root_rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=self._update_root_rect, pos=self._update_root_rect)


        root.add_widget(Label(
            text="🐡 フグ・ランナー 🐡",
            font_size=60,
            font_name=font_path,
            size_hint=(1, None),
            height=80,
            color=(1, 1, 1, 1) # 白に変更
        ))
        
        root.add_widget(Widget(size_hint_y=None, height=50))
        
        # --- メニューボタン ---
        
        btn_start = Button(
            text="ゲーム開始",
            font_size=40,
            font_name=font_path,
            size_hint=(1, None),
            height=80
        )
        btn_start.bind(on_press=self.start_game)
        root.add_widget(btn_start)

        btn_option = Button(
            text="ゲーム設定・音量調節 (オプション)",
            font_size=40,
            font_name=font_path,
            size_hint=(1, None),
            height=80
        )
        btn_option.bind(on_press=self.go_options)
        root.add_widget(btn_option)

        # UI要素を最前面に表示するため、rootウィジェットを最後に加える
        self.add_widget(root)

    def _update_root_rect(self, instance, value):
        self.root_rect.pos = instance.pos
        self.root_rect.size = instance.size

    # BGM関連のメソッドは、前回の修正どおり無効化を維持
    def play_menu_bgm(self):
        """メニューBGMの再生を無効化"""
        pass
                
    def stop_menu_bgm(self):
        """メニューBGMの停止を無効化"""
        pass
            
    def on_pre_enter(self, *args):
        # 動画再生を再開
        if self.video_bg:
            self.video_bg.play_video()

    def on_leave(self, *args):
        # 動画再生を停止
        if self.video_bg:
            self.video_bg.stop_video()
            
    def start_game(self, *args):
        self.stop_menu_bgm() 
        
        app = App.get_running_app()
        sm = app.sm
        
        # オプション画面から最新の設定値を取得
        option_screen = sm.get_screen("options")
        
        spawn_min = float(option_screen.spawn_min_slider.value)
        spawn_max = float(option_screen.spawn_max_slider.value)
        gravity = float(option_screen.gravity_slider.value)
        block_width = float(option_screen.block_width_slider.value)
        
        if spawn_min > spawn_max:
            spawn_min, spawn_max = spawn_max, spawn_min 

        bgm_volume = app.bgm_volume
        sfx_volume = app.sfx_volume

        if sm.has_screen("game"):
            sm.remove_widget(sm.get_screen("game"))
            
        # 取得した設定値を GameScreen に渡す
        game_screen = GameScreen(name="game", spawn_min=spawn_min, spawn_max=spawn_max, gravity=gravity, block_width=block_width, bgm_volume=bgm_volume, sfx_volume=sfx_volume)
        sm.add_widget(game_screen)
        sm.current = "game"

    def go_options(self, *args):
        app = App.get_running_app()
        app.sm.current = "options"


# --- GameOver/GameClear画面 --- 
class GameOverScreen(Screen):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_path = get_font_path()
        self.final_score = 0
        self.is_cleared = False
        
        # 半透明の黒いオーバーレイ
        with self.canvas:
            Color(0.2, 0.2, 0.2, 0.8)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)
        
        root = BoxLayout(orientation='vertical', padding=20, spacing=20, size_hint=(0.6, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        self.title_label = Label(
            text="Game Over",
            font_size=50,
            font_name=font_path,
            size_hint=(1, None),
            height=80,
            color=(1, 1, 1, 1)
        )
        root.add_widget(self.title_label)
        
        self.final_score_label = Label(
            text="最終スコア: 0",
            font_size=35,
            font_name=font_path,
            size_hint=(1, None),
            height=60,
            color=(1, 1, 1, 1)
        )
        root.add_widget(self.final_score_label)
        
        root.add_widget(Widget(size_hint_y=None, height=20))

        btn_reset = Button(
            text="リセットして再挑戦",
            font_size=30,
            font_name=font_path,
            size_hint=(1, None),
            height=60
        )
        btn_reset.bind(on_press=self.reset_game)
        root.add_widget(btn_reset)

        btn_option = Button(
            text="ホームへ戻る",
            font_size=30,
            font_name=font_path,
            size_hint=(1, None),
            height=60
        )
        btn_option.bind(on_press=self.go_home)
        root.add_widget(btn_option)

        self.add_widget(root)

    def _update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        
    def on_pre_enter(self, *args):
        app = App.get_running_app()
        
        if app.sm.has_screen("game"):
            game_screen = app.sm.get_screen("game")
            if hasattr(game_screen, 'game'):
                # stop_allで確定した最終スコアとクリアフラグを取得
                self.final_score = game_screen.game.final_score_value
                self.is_cleared = game_screen.game.boss_cleared
                
                self.final_score_label.text = f"最終スコア: {self.final_score}"
                
                if self.is_cleared:
                    self.title_label.text = "Game Clear! (ゲームクリア！)"
                    self.title_label.color = (0, 1, 0, 1)
                else:
                    self.title_label.text = "Game Over (ゲームオーバー)"
                    self.title_label.color = (1, 0, 0, 1)


    def reset_game(self, *args):
        app = App.get_running_app()
            
        sm = app.sm
        
        # オプション画面から最新の設定値を取得
        option_screen = sm.get_screen("options")
        spawn_min = float(option_screen.spawn_min_slider.value)
        spawn_max = float(option_screen.spawn_max_slider.value)
        gravity = float(option_screen.gravity_slider.value)
        block_width = float(option_screen.block_width_slider.value)
        
        if spawn_min > spawn_max:
            spawn_min, spawn_max = spawn_max, spawn_min 
        
        bgm_volume = app.bgm_volume
        sfx_volume = app.sfx_volume

        if sm.has_screen("game"):
            sm.remove_widget(sm.get_screen("game"))
            
        # 取得した設定値を GameScreen に渡す
        game_screen = GameScreen(name="game", spawn_min=spawn_min, spawn_max=spawn_max, gravity=gravity, block_width=block_width, bgm_volume=bgm_volume, sfx_volume=sfx_volume)
        sm.add_widget(game_screen)
        sm.current = "game"


    def go_home(self, *args):
        app = App.get_running_app()
        app.sm.current = "home"

# --- Option画面 (OptionScreen) --- 
class OptionScreen(Screen):
    # ホーム画面から背景の設定を流用
    HOME_VIDEO_FILENAME = "kabe.mp4" 
    HOME_IMAGE_FILENAME = "game.png"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        font_path = get_font_path()
        app = App.get_running_app()
        
        self.video_source = safe_asset(assets_path(self.HOME_VIDEO_FILENAME))
        self.image_source = safe_asset(assets_path(self.HOME_IMAGE_FILENAME))
        
        self.video_bg = None
        self.image_bg = None
        
        # 背景のセットアップ (HomeScreenと同じロジック) 
        if self.video_source:
            self.video_bg = VideoBackground(source=self.video_source)
            self.add_widget(self.video_bg)
        else:
            self.image_bg = Image(
                source=self.image_source,
                allow_stretch=True,
                keep_ratio=False,
                size=Window.size,
                pos=(0, 0)
            )
            self.add_widget(self.image_bg)


        root = BoxLayout(orientation='vertical', padding=30, spacing=15, size_hint=(0.8, 0.9), pos_hint={'center_x': 0.5, 'center_y': 0.5})

        # 黒い半透明の背景を追加して文字を見やすくする
        with root.canvas.before:
            Color(0, 0, 0, 0.5)
            self.root_rect = Rectangle(size=root.size, pos=root.pos)
        root.bind(size=self._update_root_rect, pos=self._update_root_rect)

        root.add_widget(Label(text="⚙️ ゲーム設定・音量調節", font_size=40, font_name=font_path, size_hint=(1, None), height=60, color=(1, 1, 1, 1)))
        root.add_widget(Widget(size_hint_y=None, height=10))

        # --- BGM 音量調節 ---
        root.add_widget(Label(text=f"🎵 BGM音量: {app.bgm_volume:.2f}", font_size=25, font_name=font_path, size_hint=(1, None), height=30, color=(1, 1, 1, 1)))
        self.bgm_volume_slider = Slider(min=0.0, max=1.0, value=app.bgm_volume, step=0.05)
        self.bgm_volume_slider.bind(value=self.update_bgm_volume)
        root.add_widget(self.bgm_volume_slider)

        # --- 効果音 (SE) 音量調節 ---
        root.add_widget(Label(text=f"🔊 効果音 (SE) 音量: {app.sfx_volume:.2f}", font_size=25, font_name=font_path, size_hint=(1, None), height=30, color=(1, 1, 1, 1)))
        self.sfx_volume_slider = Slider(min=0.0, max=1.0, value=app.sfx_volume, step=0.05)
        self.sfx_volume_slider.bind(value=self.update_sfx_volume)
        root.add_widget(self.sfx_volume_slider)
        
        root.add_widget(Widget(size_hint_y=None, height=20))
        
        # --- ゲーム設定 ---
        
        # 敵の出現間隔 最小
        self.spawn_min_label = Label(text=f"👾 敵の出現間隔 最小(秒): {1.0:.1f}", font_size=25, font_name=font_path, size_hint=(1, None), height=30, color=(1, 1, 1, 1))
        root.add_widget(self.spawn_min_label)
        self.spawn_min_slider = Slider(min=0.2, max=5.0, value=1.0, step=0.1)
        self.spawn_min_slider.bind(value=lambda instance, value: self._update_label_text(self.spawn_min_label, "👾 敵の出現間隔 最小(秒)", value))
        root.add_widget(self.spawn_min_slider)

        # 敵の出現間隔 最大
        self.spawn_max_label = Label(text=f"👾 敵の出現間隔 最大(秒): {3.0:.1f}", font_size=25, font_name=font_path, size_hint=(1, None), height=30, color=(1, 1, 1, 1))
        root.add_widget(self.spawn_max_label)
        self.spawn_max_slider = Slider(min=0.5, max=8.0, value=3.0, step=0.1)
        self.spawn_max_slider.bind(value=lambda instance, value: self._update_label_text(self.spawn_max_label, "👾 敵の出現間隔 最大(秒)", value))
        root.add_widget(self.spawn_max_slider)

        # 重力
        self.gravity_label = Label(text=f"⬇️ 重力: {-0.5:.1f}", font_size=25, font_name=font_path, size_hint=(1, None), height=30, color=(1, 1, 1, 1))
        root.add_widget(self.gravity_label)
        self.gravity_slider = Slider(min=-2.0, max=-0.1, value=-0.5, step=0.1)
        self.gravity_slider.bind(value=lambda instance, value: self._update_label_text(self.gravity_label, "⬇️ 重力", value))
        root.add_widget(self.gravity_slider)
        
        # ブロックの幅
        self.block_width_label = Label(text=f"🧱 ブロックの幅 (ピクセル): {150:.0f}", font_size=25, font_name=font_path, size_hint=(1, None), height=30, color=(1, 1, 1, 1))
        root.add_widget(self.block_width_label)
        self.block_width_slider = Slider(min=50, max=300, value=150, step=10)
        self.block_width_slider.bind(value=lambda instance, value: self._update_label_text(self.block_width_label, "🧱 ブロックの幅 (ピクセル)", value, is_int=True))
        root.add_widget(self.block_width_slider)
        
        root.add_widget(Widget(size_hint_y=None, height=10))

        start_btn = Button(
            text="設定を保存してゲーム開始",
            size_hint=(1, None),
            height=60,
            font_size=30,
            font_name=font_path
        )
        start_btn.bind(on_press=self.start_game)
        root.add_widget(start_btn)
        
        back_btn = Button(
            text="設定を保存してホームへ戻る",
            size_hint=(1, None),
            height=60,
            font_size=30,
            font_name=font_path
        )
        back_btn.bind(on_press=self.go_home)
        root.add_widget(back_btn)


        self.add_widget(root)
        
    def _update_root_rect(self, instance, value):
        self.root_rect.pos = instance.pos
        self.root_rect.size = instance.size
        
    def _update_label_text(self, label, prefix, value, is_int=False):
        """スライダーの値に応じてラベルのテキストを更新するヘルパー"""
        format_str = ": {:.0f}" if is_int else ": {:.1f}"
        label.text = prefix + format_str.format(value)

        
    def update_bgm_volume(self, instance, value):
        app = App.get_running_app()
        app.bgm_volume = value
        
        # ラベルも更新
        # BGM音量ラベルの位置は、BoxLayoutの子ウィジェットの順序に依存
        try:
             # children[0]がrootのBoxLayout, そのchildrenのリストを逆順に見た時の要素番号で取得
            bgm_label_index = 9 
            if len(self.children[0].children) > bgm_label_index:
                 label = self.children[0].children[bgm_label_index]
                 label.text = f"🎵 BGM音量: {value:.2f}"
        except IndexError:
            # 順序が変更された場合のフォールバック
            pass
        except AttributeError:
             pass
        
        # 再生中のBGMの音量を更新
        sm = App.get_running_app().sm
        if sm.has_screen("game"):
            game_screen = sm.get_screen("game")
            if hasattr(game_screen, 'game') and game_screen.game and game_screen.game.bgm:
                game_screen.game.bgm.volume = value

    def update_sfx_volume(self, instance, value):
        app = App.get_running_app()
        app.sfx_volume = value
        
        # ラベルも更新
        try:
            sfx_label_index = 7
            if len(self.children[0].children) > sfx_label_index:
                 label = self.children[0].children[sfx_label_index]
                 label.text = f"🔊 効果音 (SE) 音量: {value:.2f}"
        except IndexError:
             pass
        except AttributeError:
             pass


    def _get_validated_settings(self):
        # スライダーから値を取得し、最小値と最大値が逆転していたら入れ替える
        spawn_min = float(self.spawn_min_slider.value)
        spawn_max = float(self.spawn_max_slider.value)
        
        if spawn_min > spawn_max:
            # スライダーの値を強制的に入れ替える
            # これにより、UI上のスライダーの位置も変更される
            self.spawn_min_slider.value = spawn_max
            self.spawn_max_slider.value = spawn_min
            # 値を入れ替えた後で再取得
            spawn_min, spawn_max = self.spawn_min_slider.value, self.spawn_max_slider.value
            
        gravity = float(self.gravity_slider.value)
        block_width = float(self.block_width_slider.value)
        
        return spawn_min, spawn_max, gravity, block_width

    def on_pre_enter(self, *args):
        app = App.get_running_app()
        # ボリュームスライダーをアプリの現在の値に設定
        self.bgm_volume_slider.value = app.bgm_volume
        self.sfx_volume_slider.value = app.sfx_volume
        
        # 動画再生を再開
        if self.video_bg:
            self.video_bg.play_video()

        # ラベルの初期値をスライダーの値で更新する（on_pre_enterで再設定）
        self.update_bgm_volume(self.bgm_volume_slider, self.bgm_volume_slider.value) 
        self.update_sfx_volume(self.sfx_volume_slider, self.sfx_volume_slider.value) 
        
        self._update_label_text(self.spawn_min_label, "👾 敵の出現間隔 最小(秒)", self.spawn_min_slider.value)
        self._update_label_text(self.spawn_max_label, "👾 敵の出現間隔 最大(秒)", self.spawn_max_slider.value)
        self._update_label_text(self.gravity_label, "⬇️ 重力", self.gravity_slider.value)
        self._update_label_text(self.block_width_label, "🧱 ブロックの幅 (ピクセル)", self.block_width_slider.value, is_int=True)
        
        
    def on_leave(self, *args):
        # 動画再生を停止
        if self.video_bg:
            self.video_bg.stop_video()


    def start_game(self, *args):
        app = App.get_running_app()
        
        if app.sm.has_screen("home"):
            app.sm.get_screen("home").stop_menu_bgm()

        sm = app.sm

        spawn_min, spawn_max, gravity, block_width = self._get_validated_settings()
        
        if sm.has_screen("game"):
            sm.remove_widget(sm.get_screen("game"))
            
        bgm_volume = app.bgm_volume
        sfx_volume = app.sfx_volume

        game_screen = GameScreen(name="game", spawn_min=spawn_min, spawn_max=spawn_max, gravity=gravity, block_width=block_width, bgm_volume=bgm_volume, sfx_volume=sfx_volume)
        sm.add_widget(game_screen)
        sm.current = "game"
        
    def go_home(self, *args):
        app = App.get_running_app()
        self._get_validated_settings() # 設定のバリデーションと保存（スライダー値の入れ替え）
        app.sm.current = "home"

# --- Game画面ラッパー (GameScreen) --- 
class GameScreen(Screen):
    def __init__(self, spawn_min, spawn_max, gravity, block_width, bgm_volume, sfx_volume, **kwargs):
        super().__init__(**kwargs)
        # 渡された設定値を使って Game インスタンスを作成
        self.game = Game(spawn_min=spawn_min, spawn_max=spawn_max, gravity=gravity, block_width=block_width, bgm_volume=bgm_volume, sfx_volume=sfx_volume)
        self.add_widget(self.game)
        
    def on_enter(self, *args):
        app = App.get_running_app()
        if app.sm.has_screen("home"):
            # ホーム画面の動画を停止させるためにon_leaveを呼ぶ
            app.sm.get_screen("home").on_leave() 

# --- アプリ本体 (FuguRunnerApp) --- 
class FuguRunnerApp(App):
    # BGM音量の初期値を 0.5 に変更し、音が鳴るようにする 
    bgm_volume = NumericProperty(0.5) 
    sfx_volume = NumericProperty(0.5) 

    def build(self):
        self.sm = ScreenManager(transition=NoTransition())
        
        # オプション画面を最初に作成し、他の画面が参照できるようにする
        self.sm.add_widget(OptionScreen(name="options"))
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(GameOverScreen(name="gameover"))

        self.sm.current = "home"
        Window.bind(on_key_down=self.on_key_down)
        return self.sm

    def on_key_down(self, window, key, scancode, codepoint, modifiers):
        if self.sm.current == "game" and key == 32: # Spaceキー
            gs = self.sm.get_screen("game")
            if hasattr(gs, "game") and gs.game and not gs.game.is_game_over:
                gs.game.fugu.jump()
                return True

        if key == 27: # Escキー
            if self.sm.current == "game":
                try:
                    gs = self.sm.get_screen("game")
                    if hasattr(gs, "game") and gs.game and not gs.game.is_game_over:
                        gs.game.stop_all() # ゲームを停止
                except Exception:
                    pass
                # GameOverScreenへ移行し、スコアを更新
                self.sm.get_screen("gameover").on_pre_enter()
                self.sm.current = "gameover" 
                return True
            elif self.sm.current == "options" or self.sm.current == "gameover":
                self.sm.current = "home"
                return True
        return False

if __name__ == "__main__":
    
    # ----------------------------------------------------
    # ★ 実行前の準備:
    # ----------------------------------------------------
    # 1. プロジェクトフォルダ内に 'assets' フォルダがあることを確認してください。
    # 2. 'assets' フォルダ内に以下のファイルを用意してください:
    #    - ホーム画面の動画: kabe.mp4 (ファイル名が正しくないと再生されません)
    #    - ゲーム中の背景: game.png
    #    - キャラクター画像: fugu.png, shark.png, stone.png, boss.png
    #    - フォント: GenShinGothic-Regular.ttf
    #    - ゲームBGM: bgm.ogg (メニューBGMは停止)
    #    - 効果音: hit.ogg, GB__.ogg, 叫ぶ.ogg, meme.ogg, clear.ogg, boss_appear.ogg
    # ----------------------------------------------------
    
    # Kivyの動画再生には、環境によってはFFmpeg関連のライブラリが必要になることがあります。
    # 特にWindowsでPyInstallerを使用する場合、動画ファイルの格納場所やKivyのビルドオプションに注意が必要です。
    
    FuguRunnerApp().run()