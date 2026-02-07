from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.properties import NumericProperty, BooleanProperty, ListProperty
from kivy.core.audio import SoundLoader
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.graphics import Color, Rectangle, PushMatrix, PopMatrix, Rotate
from kivy.uix.video import Video
import os, sys, random, math

# --- 共通パス・フォント管理 ---
def get_path(filename):
    if getattr(sys, 'frozen', False): base = sys._MEIPASS
    else: base = os.path.dirname(os.path.abspath(__file__))
    paths = [os.path.join(base, "assets", filename), os.path.join(base, filename)]
    for p in paths:
        if os.path.exists(p): return p
    return filename

def get_font():
    f = get_path("GenShinGothic-Regular.ttf")
    return f if os.path.exists(f) else None

ORANGE_COLOR = (1, 0.5, 0, 1)

# --- ゲームオブジェクト ---

class Kirimi(Image):
    """ボス戦：クリックした方向に飛ぶ弾"""
    def __init__(self, start_pos, target_pos, **kwargs):
        super().__init__(**kwargs)
        self.source = get_path("kirimi.png")
        self.size = (60, 60); self.size_hint = (None, None)
        self.pos = (start_pos[0] - 30, start_pos[1] - 30)
        dx, dy = target_pos[0] - start_pos[0], target_pos[1] - start_pos[1]
        angle = math.atan2(dy, dx)
        speed = 22
        self.vx, self.vy = math.cos(angle) * speed, math.sin(angle) * speed
    def update(self):
        self.x += self.vx; self.y += self.vy

class Boss(Image):
    """ボスキャラクター"""
    hp = NumericProperty(10)
    target_pos = ListProperty([0, 0])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = get_path("boss.png")
        self.size = (320, 320); self.size_hint = (None, None)
        self.x, self.y, self.state = Window.width, Window.height / 2, "entering"
    def update(self, dt):
        if self.state == "entering":
            self.x -= 5
            if self.x <= Window.width - 400: self.state = "fighting"; self.pick_new_target()
        elif self.state == "fighting":
            dx, dy = self.target_pos[0] - self.x, self.target_pos[1] - self.y
            dist = math.sqrt(dx**2 + dy**2) or 1
            if dist < 20: self.pick_new_target()
            else: self.x += (dx/dist)*6; self.y += (dy/dist)*6
    def pick_new_target(self):
        self.target_pos = [random.uniform(Window.width/2, Window.width-320), random.uniform(100, Window.height-320)]

class Fugu(Image):
    """プレイヤーキャラクター"""
    vy = NumericProperty(0); on_ground = BooleanProperty(True); invincible = BooleanProperty(False); angle = NumericProperty(0)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source = get_path("fugu.png"); self.size = (110, 110); self.size_hint = (None, None)
        with self.canvas.before: PushMatrix(); self.rot = Rotate(angle=0, origin=self.center)
        with self.canvas.after: PopMatrix()
    def update(self, grav):
        self.y += self.vy; self.vy += grav
        if self.invincible:
            self.opacity = 0.6; self.angle = (self.angle + 25) % 360; self.rot.angle = self.angle
        else: self.opacity = 1.0; self.rot.angle = 0
        if self.y <= 110: self.y, self.vy, self.on_ground = 110, 0, True
        else: self.on_ground = False
        self.rot.origin = self.center
    def jump(self):
        if self.on_ground: self.vy = 18

# --- スクリーン管理 ---

class InstructionScreen(Screen):
    """【アプリ起動時】操作説明画面"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        l = BoxLayout(orientation='vertical', padding=60, spacing=20)
        l.add_widget(Label(text="【フグ・ランナー 操作設定】", font_name=get_font(), font_size=40, color=ORANGE_COLOR))
        l.add_widget(Label(text="通常時：クリックでジャンプ\nボス戦：クリック方向に切り身を発射\nKキー：管理者メニューを開く", font_name=get_font(), font_size=28))
        btn = Button(text="了解しました", font_name=get_font(), size_hint=(0.4, 0.2), pos_hint={'center_x': 0.5})
        btn.bind(on_press=lambda x: setattr(self.manager, 'current', 'home'))
        l.add_widget(btn); self.add_widget(l)

class AdminPanel(Screen):
    """管理者パネル：全機能統合"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before: Color(0, 0, 0, 0.85); self.r1 = Rectangle(size=Window.size)
        main = BoxLayout(orientation='vertical', padding=40, spacing=15, size_hint=(0.7, 0.85), pos_hint={'center_x': 0.5, 'center_y': 0.5})
        main.add_widget(Label(text="管理者メニュー", font_name=get_font(), font_size=32, color=ORANGE_COLOR))
        
        hb = BoxLayout(spacing=10, size_hint_y=None, height=50)
        hb.add_widget(Label(text="スコア設定:", font_name=get_font())); self.si = TextInput(text="0", multiline=False, input_filter='int'); hb.add_widget(self.si); main.add_widget(hb)
        
        self.inv_btn = ToggleButton(text="無敵モード: OFF", font_name=get_font(), size_hint_y=None, height=60)
        self.inv_btn.bind(on_press=self._toggle_text); main.add_widget(self.inv_btn)
        
        btn_m = Button(text="特殊演出を強制発動", font_name=get_font(), size_hint_y=None, height=60)
        btn_m.bind(on_press=self.force_m); main.add_widget(btn_m)
        
        btn_r = Button(text="適用してゲームに戻る", font_name=get_font(), background_color=(0, 0.8, 0.2, 1), size_hint_y=None, height=80)
        btn_r.bind(on_press=self.apply); main.add_widget(btn_r)
        self.add_widget(main)

    def _toggle_text(self, btn): btn.text = "無敵モード: ON" if btn.state == 'down' else "無敵モード: OFF"
    def force_m(self, *args):
        gs = App.get_running_app().sm.get_screen("game")
        if gs: gs.game.start_michael()
        self.apply()
    def apply(self, *args):
        app = App.get_running_app(); gs = app.sm.get_screen("game")
        if gs:
            gs.game.set_score(int(self.si.text or 0))
            gs.game.fugu.invincible = (self.inv_btn.state == 'down')
            gs.game.resume_game()
        app.sm.current = 'game'

class Game(Widget):
    """ゲーム本体"""
    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs)
        self.spawn_interval, self.gravity = settings[0], settings[1]
        self.score, self.is_game_over, self.is_michael, self.is_boss = 0, False, False, False
        self.obstacles, self.bullets, self.boss, self.fever_v = [], [], None, None
        
        self.bg = Image(source=get_path("stage1_bg.png"), allow_stretch=True, keep_ratio=False, size=Window.size); self.add_widget(self.bg)
        self.fugu = Fugu(); self.add_widget(self.fugu)
        self.score_label = Label(text="Score: 0", font_size=45, font_name=get_font(), color=ORANGE_COLOR, pos=(130, Window.height - 80)); self.add_widget(self.score_label)
        
        with self.canvas.after: self.fc = Color(0, 0, 0, 0); self.fr = Rectangle(size=Window.size, pos=(0,0))
        self.bgm = SoundLoader.load(get_path("bgm.ogg"))
        if self.bgm: self.bgm.loop = True; self.bgm.play()
        self.upd_ev = Clock.schedule_interval(self.update, 1/60.0)
        self.spw_ev = Clock.schedule_once(self.spawn_loop, self.spawn_interval)

        # 【1/3の確率で即演出】
        if random.randint(1, 3) == 1: Clock.schedule_once(lambda dt: self.start_michael(), 0.5)

    def on_touch_down(self, touch):
        if self.is_game_over: return
        if self.is_boss: self.fire_kirimi(touch.pos)
        else: self.fugu.jump()

    def set_score(self, val):
        self.score = val; self.score_label.text = f"Score: {self.score}"
        if self.score in [10, 20, 29]: self.start_fever()
        if self.score >= 31 and not self.is_boss: self.start_boss()
        if self.score % 100 == 0 and self.score > 0: self.start_michael()

    def start_fever(self):
        self.fugu.invincible = True
        Clock.schedule_once(lambda dt: setattr(self.fugu, 'invincible', False), 5.0)
        if self.score == 10 and not self.fever_v:
            vp = get_path("fever_bg.mp4")
            if os.path.exists(vp):
                self.fever_v = Video(source=vp, state='play', options={'eos': 'loop'}, allow_stretch=True, keep_ratio=False, size=Window.size); self.add_widget(self.fever_v, index=10)

    def start_boss(self):
        self.is_boss = True; Clock.unschedule(self.spw_ev)
        for o in self.obstacles: self.remove_widget(o)
        self.obstacles.clear(); self.boss = Boss(); self.add_widget(self.boss)
        self.score_label.text = f"BOSS HP: {self.boss.hp}"

    def fire_kirimi(self, t_pos):
        nb = Kirimi(start_pos=(self.fugu.center_x, self.fugu.center_y), target_pos=t_pos)
        self.add_widget(nb); self.bullets.append(nb)

    def start_michael(self):
        if self.is_game_over or self.is_michael: return
        self.is_michael = True; 
        if self.bgm: self.bgm.stop()
        self.gravity = -5.0; s1 = SoundLoader.load(get_path("特殊演出.ogg"))
        if s1: s1.play(); Clock.schedule_once(self.play_m2, s1.length or 3.0)
        else: self.play_m2(0)

    def play_m2(self, dt):
        s2 = SoundLoader.load(get_path("特殊演出2.ogg")); 
        if s2: s2.play()
        wall = Image(source=get_path("bom.png"), size=(500, 500), size_hint=(None, None), pos=(Window.width * 0.7, 100))
        self.add_widget(wall); self.obstacles.append(wall)
        Clock.schedule_interval(self.fade, 1/30.0); Clock.schedule_once(lambda d: self.die(), 2.8)

    def fade(self, dt): self.fc.a = min(1.0, self.fc.a + 0.012); return self.fc.a < 1.0

    def update(self, dt):
        if self.is_game_over: return
        self.fugu.update(self.gravity)
        if self.boss:
            self.boss.update(dt)
            if self.boss.collide_widget(self.fugu) and not self.fugu.invincible: self.die()
        for b in list(self.bullets):
            b.update()
            if self.boss and b.collide_widget(self.boss):
                self.boss.hp -= 1; self.score_label.text = f"BOSS HP: {self.boss.hp}"
                self.boss.opacity = 0.4; Clock.schedule_once(lambda d: setattr(self.boss, 'opacity', 1.0), 0.1)
                self.remove_widget(b); self.bullets.remove(b)
                if self.boss.hp <= 0: self.win()
            elif not Window.collide_point(*b.pos): self.remove_widget(b); self.bullets.remove(b)
        if not self.is_boss:
            for o in list(self.obstacles):
                if o.collide_widget(self.fugu) and not self.fugu.invincible: self.die()
                o.x -= 13
                if o.right < 0: self.remove_widget(o); self.obstacles.remove(o); self.set_score(self.score + 1)

    def spawn_loop(self, dt):
        if self.is_game_over or self.is_boss or self.is_michael: return
        o = Image(source=get_path("bom.png"), size=(110,110), size_hint=(None,None), pos=(Window.width, 110))
        self.add_widget(o); self.obstacles.append(o)
        self.spw_ev = Clock.schedule_once(self.spawn_loop, self.spawn_interval)

    def win(self): self.is_game_over = True; Clock.schedule_once(lambda dt: setattr(App.get_running_app().sm, 'current', 'gameover'), 2.0)
    def die(self):
        if self.is_game_over: return
        self.is_game_over = True; 
        if self.bgm: self.bgm.stop()
        if self.fever_v: self.fever_v.state = 'stop'
        Clock.schedule_once(lambda dt: setattr(App.get_running_app().sm, 'current', 'gameover'), 1.5)
    def pause_game(self): Clock.unschedule(self.upd_ev); Clock.unschedule(self.spw_ev)
    def resume_game(self):
        self.upd_ev = Clock.schedule_interval(self.update, 1/60.0)
        if not self.is_boss and not self.is_michael: self.spw_ev = Clock.schedule_once(self.spawn_loop, self.spawn_interval)

# --- ホーム画面（MP4停止修正済み） ---

class HomeScreen(Screen):
    def on_enter(self):
        p = get_path("background.mp4")
        if os.path.exists(p):
            self.bv = Video(source=p, state='play', options={'eos': 'loop'}, allow_stretch=True, keep_ratio=False, size=Window.size)
            self.add_widget(self.bv, index=100)
            
    def _stop_video(self):
        """動画を裏で流さないために確実に停止・アンロード"""
        if hasattr(self, 'bv'):
            self.bv.state = 'stop'; self.bv.unload(); self.remove_widget(self.bv); del self.bv

    def on_pre_leave(self): self._stop_video()
    def on_leave(self): self._stop_video()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        l = BoxLayout(orientation='vertical', padding=80, spacing=25)
        l.add_widget(Label(text="フグ・ランナー", font_size=85, font_name=get_font(), color=ORANGE_COLOR))
        
        b1 = Button(text="ゲーム開始", font_name=get_font(), size_hint=(0.45, 0.2), pos_hint={'center_x': 0.5})
        b1.bind(on_press=lambda x: setattr(self.manager, 'current', 'game_init')); l.add_widget(b1)
        
        b2 = Button(text="詳細設定", font_name=get_font(), size_hint=(0.45, 0.2), pos_hint={'center_x': 0.5})
        b2.bind(on_press=lambda x: setattr(self.manager, 'current', 'admin')); l.add_widget(b2)
        
        self.add_widget(l)

class GameInitScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        if app.sm.has_screen("game"): app.sm.remove_widget(app.sm.get_screen("game"))
        app.sm.add_widget(GameScreen(name="game", settings=[2.4, -0.28]))
        app.sm.current = "game"

class GameScreen(Screen):
    def __init__(self, settings, **kwargs):
        super().__init__(**kwargs); self.game = Game(settings); self.add_widget(self.game)

class GameOverScreen(Screen):
    def on_pre_enter(self):
        self.clear_widgets()
        l = BoxLayout(orientation='vertical', padding=100, spacing=30)
        l.add_widget(Label(text="RESULT", font_size=70, font_name=get_font(), color=ORANGE_COLOR))
        b = Button(text="ホーム画面へ戻る", font_name=get_font(), size_hint=(.5,.2), pos_hint={'center_x':.5})
        b.bind(on_press=lambda x: setattr(self.manager, 'current', 'home')); l.add_widget(b)
        self.add_widget(l)

class FuguRunnerApp(App):
    def build(self):
        self.sm = ScreenManager(transition=NoTransition())
        self.sm.add_widget(InstructionScreen(name="instructions"))
        self.sm.add_widget(HomeScreen(name="home"))
        self.sm.add_widget(GameInitScreen(name="game_init"))
        self.sm.add_widget(AdminPanel(name="admin"))
        self.sm.add_widget(GameOverScreen(name="gameover"))
        Window.bind(on_key_down=self._key)
        return self.sm
    def _key(self, win, key, *args):
        if key == 107 and self.sm.current == "game": # Kキー
            self.sm.get_screen("game").game.pause_game(); self.sm.current = 'admin'

if __name__ == "__main__":
    FuguRunnerApp().run()