import os
from kivy.config import Config
# 1. 起動時に画面を最大化 (Windowインポート前に行う)
Config.set('graphics', 'window_state', 'maximized')

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, BooleanProperty
from kivy.core.audio import SoundLoader
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.slider import Slider
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate
from kivy.uix.video import Video
import os, random, sys

# --- 定数 ---
ORANGE_COLOR = (1, 0.5, 0, 1)

MODE_PRESETS = {
    "Easy": [2.5, -0.25, 250],
    "Normal": [1.8, -0.35, 180],
    "Hard": [1.2, -0.50, 120]
}

def get_path(filename):
    if getattr(sys, 'frozen', False): base = sys._MEIPASS
    else: base = os.path.dirname(os.path.abspath(__file__))
    paths = [os.path.join(base, "assets", filename), os.path.join(base, filename)]
    for p in paths:
        if os.path.exists(p): return p
    return filename

def get_font():
    f = get_path("GenShinGothic-Regular.ttf")
    # ファイルが存在すればそのパスを返し、なければNoneではなく空文字を返す
    if os.path.exists(f):
        return f
    return "" # Noneを返すとLabelがエラーを吐くので、空文字にする

# --- 攻撃用切り身 ---
class KirimiProjectile(Image):
    def __init__(self, start_pos, target_pos, **kwargs):
        super().__init__(**kwargs)
        self.source = get_path("Kirimi.png")
        self.size = (80, 80)
        self.size_hint = (None, None)
        self.pos = start_pos
        self.target_pos = target_pos
        self.speed = 20

    def update(self):
        dx = self.target_pos[0] - self.center_x
        dy = self.target_pos[1] - self.center_y
        dist = (dx**2 + dy**2)**0.5
        if dist > 10:
            self.x += (dx / dist) * self.speed
            self.y += (dy / dist) * self.speed
            return False
        return True 

# --- オブジェクト ---
class Fugu(Image):
    velocity_y = NumericProperty(0)
    on_ground = BooleanProperty(True)
    invincible = BooleanProperty(False)
    angle = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = get_path("fugu.png")
        self.size = (110, 110)
        self.size_hint = (None, None)
        self.hammer = Image(source=get_path("hammer.png"), size=(80, 80), size_hint=(None, None), opacity=0)
        with self.canvas.before:
            PushMatrix()
            self.rot = Rotate(angle=0, origin=self.center)
        with self.canvas.after:
            PopMatrix()

    def update(self, blocks, grav):
        self.y += self.velocity_y
        self.velocity_y += grav
        
        if self.invincible:
            self.angle = (self.angle + 25) % 360
            self.rot.angle = self.angle
            self.hammer.pos = (self.right - 20, self.y + 15)
        else:
            self.rot.angle = 0
            self.hammer.opacity = 0
            
        landed = False
        for b in blocks:
            if (self.right > b.x and self.x < b.right and 
                self.y <= b.top and self.y > b.top - 30 and self.velocity_y < 0):
                self.y, self.velocity_y, self.on_ground = b.top, 0, True
                landed = True; break
        if not landed and self.y <= 100:
            self.y, self.velocity_y, self.on_ground = 100, 0, True
            landed = True
        if not landed: self.on_ground = False
        self.rot.origin = self.center

    def jump(self):
        if self.on_ground: self.velocity_y = 15

# --- 画面ベース ---
class VideoBGScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bg_video = None
        Window.bind(on_size=self._update_rect)

    def on_enter(self):
        src = get_path("background.mp4")
        if os.path.exists(src):
            self.bg_video = Video(source=src, state='play', options={'eos': 'loop'},
                                  allow_stretch=True, keep_ratio=False, size=Window.size, pos=(0,0), volume=1.0)
            self.add_widget(self.bg_video, index=1000)

    def _update_rect(self, *args):
        if self.bg_video: 
            self.bg_video.size = Window.size
            self.bg_video.pos = (0,0)

    def on_leave(self):
        if self.bg_video:
            self.bg_video.state = 'stop'; self.bg_video.unload(); self.remove_widget(self.bg_video); self.bg_video = None

# --- 各画面定義 ---
class HomeScreen(VideoBGScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_mode = "Easy"
        l = BoxLayout(orientation='vertical', padding=50, spacing=10)
        l.add_widget(Label(text="フグ・ランナー", font_size=70, font_name=get_font(), color=ORANGE_COLOR))
        
        ml = BoxLayout(size_hint=(0.8, 0.1), pos_hint={'center_x': 0.5}, spacing=10)
        for mode in ["Easy", "Normal", "Hard"]:
            btn = ToggleButton(text=mode, group='mode', state=('down' if mode=="Easy" else 'normal'), font_name=get_font())
            btn.bind(on_press=self.set_mode)
            ml.add_widget(btn)
        l.add_widget(ml)

        self.freq_slider = Slider(min=0.5, max=5.0, value=2.5, size_hint=(0.8, 0.1), pos_hint={'center_x': 0.5})
        self.freq_label = Label(text=f"出現間隔: {self.freq_slider.value}秒", font_name=get_font())
        self.freq_slider.bind(value=lambda i, v: setattr(self.freq_label, 'text', f"出現間隔: {round(v, 2)}秒"))
        l.add_widget(self.freq_label); l.add_widget(self.freq_slider)

        for t, s in [("開始", "game"), ("設定", "options")]:
            btn = Button(text=t, font_name=get_font(), size_hint=(0.4, 0.12), pos_hint={'center_x': 0.5})
            if s == "game": btn.bind(on_press=self.go)
            else: btn.bind(on_press=lambda i, target=s: setattr(self.manager, 'current', target))
            l.add_widget(btn)
        self.add_widget(l)

    def set_mode(self, instance):
        self.current_mode = instance.text
        vals = MODE_PRESETS[self.current_mode]
        self.freq_slider.value = vals[0]
        opt = self.manager.get_screen("options")
        opt.s_f.value, opt.s_g.value, opt.s_w.value = vals

    def go(self, *args):
        app = App.get_running_app()
        opt = app.sm.get_screen("options")
        # settings: [spawn_interval, gravity, block_width, dummy, hit_ratio, dummy]
        s = [self.freq_slider.value, opt.s_g.value, opt.s_w.value, 5.0, 0.8, 1]
        if app.sm.has_screen("game"): app.sm.remove_widget(app.sm.get_screen("game"))
        app.sm.add_widget(GameScreen(name="game", settings=s))
        app.sm.current = "game"

class AdminPanel(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(0, 0, 0, 0); self.r1 = Rectangle(size=Window.size)
        main = BoxLayout(orientation='vertical', padding=20, spacing=10, size_hint=(0.5, 0.6), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        with main.canvas.before:
            Color(0.1, 0.1, 0.1, 0.85); self.r2 = Rectangle(size=main.size, pos=main.pos)
        main.bind(pos=self._upd, size=self._upd)
        main.add_widget(Label(text="ADMIN PANEL", font_name=get_font(), font_size=24, color=ORANGE_COLOR))
        self.score_slider = Slider(min=0, max=31, value=0, step=1)
        self.score_label = Label(text=f"設定スコア: {int(self.score_slider.value)}", font_name=get_font())
        self.score_slider.bind(value=lambda i, v: setattr(self.score_label, 'text', f"設定スコア: {int(v)}"))
        main.add_widget(self.score_label); main.add_widget(self.score_slider)
        main.add_widget(Button(text="スコアを適用", font_name=get_font(), on_press=self._apply_score))
        main.add_widget(Button(text="特殊演出 発動", font_name=get_font(), background_color=(1, 0, 0, 1), on_press=self._trigger_special))
        main.add_widget(Button(text="閉じる", font_name=get_font(), on_press=self.close))
        self.add_widget(main)

    def _upd(self, i, v): self.r1.size=Window.size; self.r2.pos, self.r2.size = i.pos, i.size
    def _apply_score(self, instance):
        gs = App.get_running_app().sm.get_screen("game")
        if gs: gs.game.add_score(int(self.score_slider.value) - gs.game.score)
    def _trigger_special(self, instance):
        gs = App.get_running_app().sm.get_screen("game")
        if gs: gs.game.trigger_special_event()
        self.close()
    def close(self, *args):
        App.get_running_app().sm.current = 'game'
        gs = App.get_running_app().sm.get_screen("game")
        if gs: gs.game.resume_game()

# --- ゲーム本体 ---
class Game(Widget):
    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs)
        self.spawn_interval, self.gravity, self.block_width, _, _, _ = settings
        self.score, self.is_game_over, self.is_fever, self.boss_spawned = 0, False, False, False
        self.is_cleared = False
        self.boss_hp = 100
        self.obstacles, self.blocks, self.dead_effects, self.projectiles = [], [], [], []

        # 背景画像 (リサイズ対応)
        self.bg = Image(source=get_path("stage1_bg.png"), allow_stretch=True, keep_ratio=False, size=Window.size, pos=(0,0))
        self.add_widget(self.bg)
        Window.bind(on_size=self._on_resize)

        # キャラクター
        self.fugu = Fugu(pos=(100, 100))
        self.add_widget(self.fugu)
        self.add_widget(self.fugu.hammer)
        
        # スコア表示 (左端)
        self.score_label = Label(text="Score: 0", font_size=45, font_name=get_font(), color=ORANGE_COLOR)
        self.add_widget(self.score_label)
        
        # ボスHP表示 (中央上)
        self.hp_label = Label(text="", font_size=40, font_name=get_font(), color=(1,0,0,1))
        self.add_widget(self.hp_label)

        self._update_ui_pos()

        # サウンド
        self.bgm = SoundLoader.load(get_path("bgm.ogg"))
        if self.bgm: self.bgm.loop = True; self.bgm.play()
        self.fever_sound = SoundLoader.load(get_path("fever_bg.mp3"))

        self.update_event = Clock.schedule_interval(self.update, 1/60.0)
        self.spawn_event = Clock.schedule_once(self.spawn_loop, self.spawn_interval)

    def _on_resize(self, *args):
        self.bg.size = Window.size
        self.bg.pos = (0,0)
        self._update_ui_pos()

    def _update_ui_pos(self):
        # スコアを左端に
        self.score_label.x = 50
        self.score_label.top = Window.height - 20
        # HPバーを中央上に
        self.hp_label.center_x = Window.width / 2
        self.hp_label.top = Window.height - 20

    def on_touch_down(self, touch):
        if self.is_game_over or self.is_cleared: return super().on_touch_down(touch)
        # ボス戦中はKirimi発射
        if self.boss_spawned:
            p = KirimiProjectile(start_pos=self.fugu.center, target_pos=touch.pos)
            self.add_widget(p); self.projectiles.append(p)
        self.fugu.jump()
        return super().on_touch_down(touch)

    def add_score(self, p):
        if self.boss_spawned or self.is_cleared: return
        self.score += p
        self.score_label.text = f"Score: {self.score}"
        # フィーバー条件: 10, 20
        if self.score in [10, 20] and not self.is_fever: self.start_fever()
        # ボス出現条件: 30
        if self.score >= 30 and not self.boss_spawned: self.spawn_boss()
        
        if self.score >= 20: self.bg.source = get_path("stage3_bg.png")
        elif self.score >= 10: self.bg.source = get_path("stage2_bg.png")

    def start_fever(self):
        self.is_fever = True; self.fugu.invincible = True; self.fugu.hammer.opacity = 1
        if self.bgm: self.bgm.stop()
        if self.fever_sound: self.fever_sound.play()
        Clock.schedule_once(self.stop_fever, 8.0)

    def stop_fever(self, dt):
        self.is_fever = False; self.fugu.invincible = False; self.fugu.hammer.opacity = 0
        if self.fever_sound: self.fever_sound.stop()
        if self.bgm and not self.is_game_over: self.bgm.play()

    def spawn_boss(self):
        self.boss_spawned = True
        self.hp_label.text = f"BOSS HP: {self.boss_hp}"
        Clock.unschedule(self.spawn_event)
        for o in self.obstacles: self.remove_widget(o)
        for b in self.blocks: self.remove_widget(b)
        self.obstacles.clear(); self.blocks.clear()
        self.boss = Image(source=get_path("boss.png"), size=(400, 400), size_hint=(None, None))
        self.boss.pos = (Window.width, Window.height / 2)
        self.boss.target_y = self.boss.y
        self.boss.target_x = Window.width - 450
        self.add_widget(self.boss)

    def trigger_special_event(self):
        self.gravity = -2.0
        s1 = SoundLoader.load(get_path("特殊演出.ogg"))
        if s1: s1.play()
        giant = Image(source=get_path("bom.png"), size=(800, 800), size_hint=(None, None), pos=(Window.width, 0))
        self.add_widget(giant); self.obstacles.append(giant)
        Clock.schedule_once(self._spec2, 2.0)

    def _spec2(self, dt):
        s2 = SoundLoader.load(get_path("特殊演出2.ogg"))
        if s2: s2.play()
        self.game_over_sequence()

    def update(self, dt):
        if self.is_game_over or self.is_cleared: return
        self.fugu.update(self.blocks, self.gravity)

        if self.boss_spawned:
            # ボスのランダム移動
            if abs(self.boss.y - self.boss.target_y) < 5 and abs(self.boss.x - self.boss.target_x) < 5:
                self.boss.target_y = random.randint(100, Window.height - 400)
                self.boss.target_x = random.randint(Window.width // 2, Window.width - 450)
            self.boss.y += (self.boss.target_y - self.boss.y) * 0.05
            self.boss.x += (self.boss.target_x - self.boss.x) * 0.05

        # Kirimi攻撃更新
        for p in list(self.projectiles):
            if p.update():
                self.remove_widget(p); self.projectiles.remove(p)
            elif self.boss_spawned and p.collide_widget(self.boss):
                self.boss_hp -= 1 # ダメージ1
                self.hp_label.text = f"BOSS HP: {max(0, self.boss_hp)}"
                self.remove_widget(p); self.projectiles.remove(p)
                if self.boss_hp <= 0: self.win_sequence()

        for d in list(self.dead_effects):
            d['obj'].x += 5; d['obj'].y += d['vy']; d['vy'] -= 0.5; d['rot'].angle += 15
            if d['obj'].top < 0: self.remove_widget(d['obj']); self.dead_effects.remove(d)

        for obs in list(self.obstacles):
            if not getattr(obs, 'passed', False) and obs.right < self.fugu.x:
                obs.passed = True; self.add_score(1)
            if self.is_fever and obs.collide_widget(self.fugu.hammer):
                if obs.size[0] < 500:
                    self.obstacles.remove(obs); self._blast_away(obs); self.add_score(1); continue
            if obs.collide_widget(self.fugu) and not self.fugu.invincible:
                self.game_over_sequence()
            obs.x -= 8
            if obs.right < 0: self.remove_widget(obs); self.obstacles.remove(obs)
            
        for b in list(self.blocks):
            b.x -= 8
            if b.right < 0: self.remove_widget(b); self.blocks.remove(b)

    def _blast_away(self, obj):
        with obj.canvas.before: PushMatrix(); rot = Rotate(angle=0, origin=obj.center)
        with obj.canvas.after: PopMatrix()
        self.dead_effects.append({'obj': obj, 'rot': rot, 'vy': 15})

    def spawn_loop(self, dt):
        if self.is_game_over or self.boss_spawned: return
        if random.random() < 0.6:
            o = Image(source=get_path("bom.png"), size=(100,100), size_hint=(None,None), pos=(Window.width, 100))
            o.passed = False; self.add_widget(o); self.obstacles.append(o)
        else:
            bl = Image(source=get_path("block.png"), size=(self.block_width, 50), size_hint=(None,None), 
                       pos=(Window.width, 150+random.randint(0,150)), allow_stretch=True, keep_ratio=False)
            self.add_widget(bl); self.blocks.append(bl)
        self.spawn_event = Clock.schedule_once(self.spawn_loop, 0.3 if self.is_fever else self.spawn_interval)

    def win_sequence(self):
        self.is_cleared = True; self.hp_label.text = "GAME CLEAR!"
        if self.bgm: self.bgm.stop()
        if hasattr(self, 'boss'): self.remove_widget(self.boss)
        Clock.schedule_once(lambda dt: setattr(App.get_running_app().sm, 'current', 'gameover'), 3.0)

    def game_over_sequence(self):
        self.is_game_over = True; self.pause_game()
        s = SoundLoader.load(get_path("GB__.ogg"))
        if s: s.play()
        Clock.schedule_once(lambda dt: setattr(App.get_running_app().sm, 'current', 'gameover'), 1.5)

    def pause_game(self):
        Clock.unschedule(self.update_event); Clock.unschedule(self.spawn_event)
        if self.bgm: self.bgm.stop()
        if self.fever_sound: self.fever_sound.stop()

    def resume_game(self):
        self.update_event = Clock.schedule_interval(self.update, 1/60.0)
        if not self.boss_spawned: self.spawn_event = Clock.schedule_once(self.spawn_loop, self.spawn_interval)
        if self.is_fever:
            if self.fever_sound: self.fever_sound.play()
        elif self.bgm: self.bgm.play()

# --- 各種画面 ---
class OptionScreen(VideoBGScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        l = BoxLayout(orientation='vertical', padding=40, spacing=5)
        l.add_widget(Label(text="詳細設定", font_size=30, font_name=get_font()))
        self.s_f = Slider(min=0.5, max=5.0, value=2.5); self.s_g = Slider(min=-1.5, max=-0.1, value=-0.25); self.s_w = Slider(min=50, max=500, value=250)
        for s, t in [(self.s_f, "出現間隔"), (self.s_g, "重力"), (self.s_w, "ブロック幅")]:
            lbl = Label(text=f"{t}: {round(s.value, 2)}", font_name=get_font())
            s.bind(value=lambda i, v, lb=lbl, tt=t: setattr(lb, 'text', f"{tt}: {round(v, 2)}"))
            l.add_widget(lbl); l.add_widget(s)
        l.add_widget(Button(text="戻る", font_name=get_font(), size_hint=(0.3, 0.15), pos_hint={'center_x':0.5}, on_press=lambda x: setattr(self.manager, 'current', 'home')))
        self.add_widget(l)

class GameScreen(Screen):
    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs); self.game = Game(settings=settings); self.add_widget(self.game)

class GameOverScreen(Screen):
    def on_enter(self):
        self.clear_widgets(); l = BoxLayout(orientation='vertical', padding=100, spacing=30)
        gs = App.get_running_app().sm.get_screen("game")
        txt = "GAME CLEAR" if gs and getattr(gs.game, 'is_cleared', False) else "GAME OVER"
        color = (0, 1, 0, 1) if txt == "GAME CLEAR" else (1, 0, 0, 1)
        l.add_widget(Label(text=txt, font_size=80, font_name=get_font(), color=color))
        btn = Button(text="ホームに戻る", font_name=get_font(), size_hint=(.4,.2), pos_hint={'center_x':.5})
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home')); l.add_widget(btn)
        self.add_widget(l)

class FuguRunnerApp(App):
    def build(self):
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(OptionScreen(name="options"))
        self.sm.add_widget(AdminPanel(name="admin"))
        self.sm.add_widget(GameOverScreen(name="gameover"))
        Window.bind(on_key_down=self._on_key)
        Clock.schedule_once(self.show_intro, 0.5)
        return self.sm

    def show_intro(self, dt):
        content = BoxLayout(orientation='vertical', padding=20, spacing=10)
        text = ("ふぐ刺身製作者：ふぐ刺身株式会社一同\n\n"
                "操作方法：画面タップ（クリック）でジャンプ。\n"
                "スコア10, 20でフィーバータイム！敵を吹き飛ばせます。\n"
                "スコア30でボス戦！クリックで切り身を飛ばして攻撃してください。\n"
                "ボスのHPを0にすれば勝利です。")
        lbl = Label(text=text, font_name=get_font(), font_size=16, halign='left', valign='top')
        lbl.bind(size=lbl.setter('text_size')); content.add_widget(lbl)
        btn = Button(text="閉じる", size_hint_y=0.2, font_name=get_font()); content.add_widget(btn)
        popup = Popup(title="ゲーム解説", content=content, size_hint=(0.8, 0.8), auto_dismiss=False)
        btn.bind(on_press=popup.dismiss); popup.open()

    def _on_key(self, win, key, *args):
        if key == 107: # 'k' キーで管理者パネル
            if self.sm.current == "game":
                gs = self.sm.get_screen("game")
                if gs: gs.game.pause_game(); self.sm.current = 'admin'
                return True
        if self.sm.current == "game":
            gs = self.sm.get_screen("game")
            if gs and gs.game and gs.game.fugu: gs.game.fugu.jump()

if __name__ == "__main__":
    FuguRunnerApp().run()