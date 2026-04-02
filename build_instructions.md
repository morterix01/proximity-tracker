# 📱 Guida alla Creazione dell'APK (V4.6 - FIX WAKELOCK E SCHERMO NERO)

Questa versione **4.6** aggiunge il supporto vitale al tracciamento in background a schermo spento con WakeLock e risolve il bug dello schermo nero al rientro dalla selezione file audio!

## 🚀 Istruzioni per Colab

### 1. Incolla ed Esegui lo Script
Copia tutto questo blocco in una cella di Colab e avvialo. Genererà l'APK finale V4.6 funzionante.

```python
# --- STEP 1: main.py (V4.6) ---
content = r'''
import os
import json
import math
import time
import pickle
import threading
import traceback
from datetime import datetime
from pathlib import Path

# Kivy Imports
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.utils import get_color_from_hex, platform
from kivy.core.audio import SoundLoader
from kivy.uix.button import Button

# Logic & Utils
import requests
import pickle
import threading
import math
from datetime import datetime
from pathlib import Path

# LOGGING & PATHS
BASE_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = Path(os.environ.get('ANDROID_PRIVATE_STORAGE', str(BASE_DIR)))
CONFIG_FILE = DATA_DIR / "config.json"
COOKIES_FILE = DATA_DIR / "google_cookies.pkl"
LOG_FILE = DATA_DIR / "crash_log.txt"
ALARM_FILE = BASE_DIR / "Star Labs alarm.mp3"

def log_debug(msg):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
    except: pass

# ──────────────────────────────────────────────────────────
#  SISTEMA UI (KV UNIFICATO & PULITO)
# ──────────────────────────────────────────────────────────
KV = """
#:import FadeTransition kivy.uix.screenmanager.FadeTransition

<GlassCard@BoxLayout>:
    orientation: 'vertical'
    padding: 20
    spacing: 12
    canvas.before:
        Color:
            rgba: 1, 1, 1, 0.04
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [20]
        Color:
            rgba: 0, 0.95, 1, 0.2
        Line:
            rounded_rectangle: [self.x, self.y, self.width, self.height, 20]
            width: 1.1

<NeonButton@ButtonBehavior+Label>:
    text: ''
    bg_color: [0, 0.95, 1, 1]
    size_hint_y: None
    height: dp(70)
    canvas.before:
        Color:
            rgba: self.bg_color if self.state == 'normal' else [c*0.8 for c in self.bg_color[:3]] + [1]
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [18]
    bold: True
    color: 0.05, 0.05, 0.05, 1

<PremiumTextInput@TextInput>:
    background_color: 1, 1, 1, 0.05
    foreground_color: 1, 1, 1, 1
    cursor_color: 0, 0.95, 1, 1
    padding: [15, 15]
    font_size: '16sp'
    multiline: False
    size_hint_y: None
    height: dp(70)

ScreenManager:
    transition: FadeTransition()
    SplashScreen:
    DashboardScreen:
    ConfigScreen:
    CookieScreen:
    LocationScreen:

<SplashScreen>:
    name: 'splash'
    canvas.before:
        Color:
            rgba: 0.04, 0.04, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 50
        Label:
            text: 'PROXIMITY V6'
            font_size: '32sp'
            bold: True
            color: 0, 0.95, 1, 1
        Label:
            text: root.status_text
            font_size: '14sp'
            color: 0.6, 0.6, 0.6, 1

<DashboardScreen>:
    name: 'dashboard'
    canvas.before:
        Color:
            rgba: 0.04, 0.04, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: [25, 40, 25, 25]
        spacing: 20
        Label:
            text: 'DASHBOARD V6'
            font_size: '22sp'
            bold: True
            size_hint_y: None
            height: dp(60)
            color: 0, 0.95, 1, 1
        
        GlassCard:
            size_hint_y: 0.4
            Label:
                text: root.monitoring_status
                font_size: '34sp'
                bold: True
            Label:
                text: "Update: " + root.last_update
                font_size: '11sp'
                color: 0.5, 0.5, 0.6, 1

        ScrollView:
            BoxLayout:
                id: people_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 12

        NeonButton:
            text: 'STOP' if root.is_running else 'START'
            bg_color: [1, 0.3, 0.3, 1] if root.is_running else [0, 0.95, 1, 1]
            on_release: app.toggle_monitoring()
        
        Button:
            text: 'IMPOSTAZIONI'
            background_color: 0, 0, 0, 0
            size_hint_y: None
            height: dp(50)
            on_release: root.manager.current = 'config'

<ConfigScreen>:
    name: 'config'
    canvas.before:
        Color:
            rgba: 0.04, 0.04, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 20
        Label:
            text: 'SETTINGS'
            font_size: '22sp'
            bold: True
            size_hint_y: None
            height: dp(70)
        PremiumTextInput:
            id: email_input
            hint_text: 'Email Google'
        PremiumTextInput:
            id: ntfy_input
            hint_text: 'Ntfy Topic'
            
        BoxLayout:
            size_hint_y: None
            height: dp(60)
            spacing: dp(15)
            NeonButton:
                text: 'SUONO ALLARME'
                font_size: '14sp'
                on_release: root.choose_audio()
            Label:
                id: audio_label
                text: 'Predefinito'
                color: 0.6, 0.6, 0.6, 1
            

        NeonButton:
            text: 'GESTIONE COOKIE'
            on_release: root.manager.current = 'cookie'
        NeonButton:
            text: 'GESTIONE LUOGHI'
            on_release: root.manager.current = 'locations'
        NeonButton:
            text: 'SALVA E ESCI'
            on_release: root.save_and_exit(email_input.text, ntfy_input.text)

<CookieScreen>:
    name: 'cookie'
    canvas.before:
        Color:
            rgba: 0.04, 0.04, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 30
        spacing: 20
        Label:
            text: 'COOKIE HUB'
            font_size: '22sp'
            bold: True
        NeonButton:
            text: 'SIGN IN NOW (AUTO)'
            on_release: root.login_online()
        Label:
            id: status_label
            text: 'STATUS: Pronto'
            font_size: '18sp'
            bold: True
            color: 1, 1, 1, 1
            size_hint_y: None
            height: dp(60)
        PremiumTextInput:
            id: cookie_input
            hint_text: 'Paste JSON...'
            multiline: True
            size_hint_y: 1
        NeonButton:
            text: 'IMPORTA'
            on_release: root.import_cookies()
        NeonButton:
            text: 'INDIETRO'
            on_release: root.manager.current = 'config'

<LocationScreen>:
    name: 'locations'
    canvas.before:
        Color:
            rgba: 0.04, 0.04, 0.08, 1
        Rectangle:
            pos: self.pos
            size: self.size
    BoxLayout:
        orientation: 'vertical'
        padding: 20
        spacing: 15
        Label:
            text: 'GESTIONE LUOGHI'
            font_size: '22sp'
            bold: True
            size_hint_y: None
            height: dp(50)
            
        ScrollView:
            BoxLayout:
                id: loc_list
                orientation: 'vertical'
                size_hint_y: None
                height: self.minimum_height
                spacing: 10
                
        BoxLayout:
            orientation: 'vertical'
            size_hint_y: None
            height: dp(340)
            spacing: 10
            
            BoxLayout:
                spacing: 10
                size_hint_y: None
                height: dp(70)
                PremiumTextInput:
                    id: loc_name
                    hint_text: 'Nome (es. Casa)'
                PremiumTextInput:
                    id: loc_rad
                    hint_text: 'Raggio (es. 100)'
                    input_filter: 'int'
                    
            BoxLayout:
                spacing: 10
                size_hint_y: None
                height: dp(70)
                PremiumTextInput:
                    id: loc_lat
                    hint_text: 'Lat (es. 41.9)'
                PremiumTextInput:
                    id: loc_lon
                    hint_text: 'Lon (es. 12.5)'
                    
            NeonButton:
                text: 'AGGIUNGI LUOGO'
                size_hint_y: None
                height: dp(70)
                on_release: root.add_loc()
                
            NeonButton:
                text: 'INDIETRO'
                size_hint_y: None
                height: dp(70)
                on_release: root.save_and_go_back()
"""

class SplashScreen(Screen): status_text = StringProperty("Avvio in corso...")
class DashboardScreen(Screen):
    monitoring_status = StringProperty("INATTIVO")
    last_update = StringProperty("Mai")
    is_running = BooleanProperty(False)

    def update_list(self, people, locations):
        self.ids.people_list.clear_widgets()
        for p in people:
            closest_dist = float('inf')
            closest_loc = "Nessuna"
            for loc in locations:
                app = App.get_running_app()
                dist = app.haversine(p.latitude, p.longitude, loc['lat'], loc['lon'])
                if dist < closest_dist:
                    closest_dist = dist
                    closest_loc = loc['name']
            
            card = BoxLayout(orientation='vertical', size_hint_y=None, height=80, padding=10)
            card.add_widget(Label(text=f"{p.full_name}", bold=True, halign='left', size_hint_x=1))
            
            if closest_loc == "Nessuna":
                card.add_widget(Label(text=f"Nessun luogo configurato", font_size='12sp', color=[0.7,0.7,0.7,1]))
            else:
                card.add_widget(Label(text=f"Vicino a: {closest_loc} ({closest_dist:.0f}m)", font_size='12sp', color=[0.7,0.7,0.7,1]))

            self.ids.people_list.add_widget(card)

class ConfigScreen(Screen):
    def on_enter(self):
        app = App.get_running_app()
        self.ids.email_input.text = app.config_data.get("google_email", "")
        self.ids.ntfy_input.text = app.config_data.get("ntfy_topic", "")
        if app.config_data.get("custom_audio"):
            self.ids.audio_label.text = "Personalizzato"
    
    def choose_audio(self):
        from kivy.utils import platform
        if platform == 'android':
            try:
                from jnius import autoclass
                from android import activity
                
                Intent = autoclass('android.content.Intent')
                intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.setType("audio/*")
                
                self.ids.audio_label.text = "Apertura file..."
                
                def on_activity_result(request_code, result_code, result_intent):
                    if request_code == 111:
                        activity.unbind(on_activity_result=on_activity_result)
                        if result_code == -1 and result_intent: # RESULT_OK
                            try:
                                uri = result_intent.getData()
                                if uri:
                                    PythonActivity = autoclass('org.kivy.android.PythonActivity')
                                    context = PythonActivity.mActivity.getApplicationContext()
                                    resolver = context.getContentResolver()
                                    
                                    pfd = resolver.openFileDescriptor(uri, "r")
                                    if pfd:
                                        fd = pfd.getFd()
                                        dest_path = DATA_DIR / "custom_alarm.mp3"
                                        import shutil
                                        
                                        with open(fd, "rb", closefd=False) as src, open(str(dest_path), "wb") as dst:
                                            shutil.copyfileobj(src, dst)
                                            
                                        pfd.close()
                                        
                                        app = App.get_running_app()
                                        app.config_data["custom_audio"] = True
                                        with open(CONFIG_FILE, "w") as f:
                                            json.dump(app.config_data, f, indent=4)
                                        
                                        from kivy.clock import Clock
                                        Clock.schedule_once(lambda dt: app.reload_audio())
                                        self.ids.audio_label.text = "Personalizzato"
                                    else:
                                        self.ids.audio_label.text = "Nessun file"
                            except Exception as e:
                                self.ids.audio_label.text = "Err copia"
                                log_debug(f"Audio copy err: {str(e)}")
                        else:
                            self.ids.audio_label.text = "Annullato"
                
                activity.bind(on_activity_result=on_activity_result)
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                PythonActivity.mActivity.startActivityForResult(intent, 111)
            except Exception as e:
                self.ids.audio_label.text = "Err intent"
                log_debug(f"Audio intent err: {str(e)}")
        else:
            try:
                from plyer import filechooser
                filechooser.open_file(on_selection=self.on_audio_selected, filters=[("Audio", "*.mp3", "*.wav", "*.ogg")])
            except Exception as e:
                self.ids.audio_label.text = "Err plyer"
    
    def on_audio_selected(self, selection):
        if selection and len(selection) > 0:
            import shutil
            dest = DATA_DIR / "custom_alarm.mp3"
            try:
                shutil.copy2(selection[0], str(dest))
                app = App.get_running_app()
                app.config_data["custom_audio"] = True
                with open(CONFIG_FILE, "w") as f:
                    json.dump(app.config_data, f, indent=4)
                
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: app.reload_audio())
                self.ids.audio_label.text = "Personalizzato"
            except Exception as e:
                self.ids.audio_label.text = "Errore copia"
                log_debug(str(e))

    def save_and_exit(self, email, ntfy):
        app = App.get_running_app()
        app.config_data["google_email"] = email
        app.config_data["ntfy_topic"] = ntfy
        with open(CONFIG_FILE, "w") as f:
            json.dump(app.config_data, f, indent=4)
        self.manager.current = 'dashboard'

class CookieScreen(Screen):
    def login_online(self):
        self.ids.status_label.text = "Inizializzazione Native..."
        if platform == 'android':
            self.open_native_login()
        else:
            self.ids.status_label.text = "Solo Android!"
            import webbrowser
            webbrowser.open("https://accounts.google.com/")
    def open_native_login(self):
        try:
            from jnius import autoclass, PythonJavaClass, java_method
            self.ids.status_label.text = "Inizializzazione Native..."
            WebView = autoclass('android.webkit.WebView')
            CookieManager = autoclass('android.webkit.CookieManager')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            LayoutParams = autoclass('android.view.ViewGroup$LayoutParams')
            LinearLayout = autoclass('android.widget.LinearLayout')
            
            self.wv = None
            self.lay = None
            self.poll_event = None
            
            class WebBoot(PythonJavaClass):
                __javacontext__ = 'app'
                __javainterfaces__ = ['java/lang/Runnable']
                def __init__(self, s): super().__init__(); self.s = s
                
                @java_method('()V')
                def run(self):
                    try:
                        act = PythonActivity.mActivity; wv = WebView(act)
                        # Abilita Cookie globali
                        cm = CookieManager.getInstance()
                        cm.setAcceptCookie(True)
                        try:
                            cm.setAcceptThirdPartyCookies(wv, True)
                        except: pass
                        
                        settings = wv.getSettings()
                        settings.setJavaScriptEnabled(True)
                        settings.setDomStorageEnabled(True)
                        settings.setDatabaseEnabled(True)
                        
                        ua = "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.0.0 Mobile Safari/537.36"
                        settings.setUserAgentString(ua)

                        lay = LinearLayout(act)
                        lay.addView(wv, LayoutParams(-1, -1))
                        
                        self.s.wv = wv
                        self.s.lay = lay
                        
                        WebViewClient = autoclass('android.webkit.WebViewClient')
                        wv.setWebViewClient(WebViewClient())
                        
                        wv.loadUrl("https://accounts.google.com/")
                        
                        act.addContentView(lay, LayoutParams(-1, -1))
                        self.s.ids.status_label.text = "WebView OK!"
                        
                        from kivy.clock import Clock
                        Clock.schedule_once(self.s.start_polling, 1)
                    except Exception as e:
                        self.s.ids.status_label.text = f"Inner Err: {str(e)}"

            act = PythonActivity.mActivity
            booter = WebBoot(self)
            act.runOnUiThread(booter)
            
        except Exception as e:
            self.ids.status_label.text = f"Fatal Jnius: {str(e)}"
            log_debug(traceback.format_exc())

    def start_polling(self, dt):
        from kivy.clock import Clock
        self.poll_event = Clock.schedule_interval(self.check_cookies, 2)

    def check_cookies(self, dt):
        try:
            from jnius import autoclass
            CookieManager = autoclass('android.webkit.CookieManager')
            
            # Proviamo a interrogare sia google.com che accounts.google.com
            cm = CookieManager.getInstance()
            ck = cm.getCookie("https://google.com")
            if not ck: ck = cm.getCookie("https://accounts.google.com")
            
            if ck and "SID=" in ck:
                if self.poll_event:
                    self.poll_event.cancel()
                self.process_cookies(ck)
        except Exception as e:
            log_debug(f"Cookie poll err: {str(e)}")

    def close_webview(self):
        try:
            from jnius import autoclass, PythonJavaClass, java_method
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            class WebCloseBoot(PythonJavaClass):
                __javacontext__ = 'app'
                __javainterfaces__ = ['java/lang/Runnable']
                def __init__(self, s): super().__init__(); self.s = s
                @java_method('()V')
                def run(self):
                    try:
                        if self.s.wv and self.s.wv.getParent():
                            self.s.wv.getParent().removeView(self.s.wv)
                        if self.s.lay and self.s.lay.getParent():
                            self.s.lay.getParent().removeView(self.s.lay)
                    except: pass
            act = PythonActivity.mActivity
            act.runOnUiThread(WebCloseBoot(self))
        except: pass

    def process_cookies(self, s):
        self.close_webview()
        cks = []
        for p in s.split(";"):
            if "=" in p:
                n, v = p.strip().split("=", 1); cks.append({"name": n, "value": v, "domain": ".google.com", "path": "/"})
        with open(COOKIES_FILE, "wb") as f: pickle.dump(cks, f)
        self.ids.status_label.text = "Cookie salvati! Torno indietro..."
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.go_back(), 2)

    def go_back(self):
        self.manager.current = 'config'
    def import_cookies(self): self.manager.current = 'config'

class LocationScreen(Screen):
    def on_enter(self):
        self.refresh_list()
        
    def refresh_list(self):
        self.ids.loc_list.clear_widgets()
        app = App.get_running_app()
        for i, loc in enumerate(app.config_data.get("locations", [])):
            box = BoxLayout(size_hint_y=None, height=50, spacing=10)
            lbl = Label(text=f"{loc['name']} ({loc['radius_m']}m)\\n{loc['lat']}, {loc['lon']}", halign='left', font_size='12sp')
            btn = Button(text="Rimuovi", size_hint_x=0.3, background_color=[1,0.2,0.2,1], font_size='12sp')
            btn.bind(on_release=lambda btn, index=i: self.remove_loc(index))
            box.add_widget(lbl)
            box.add_widget(btn)
            self.ids.loc_list.add_widget(box)
            
    def remove_loc(self, index):
        app = App.get_running_app()
        app.config_data.get("locations", []).pop(index)
        self.refresh_list()
        self.save_config()
        
    def add_loc(self):
        name = self.ids.loc_name.text.strip()
        rad = self.ids.loc_rad.text.strip()
        lat = self.ids.loc_lat.text.strip()
        lon = self.ids.loc_lon.text.strip()
        
        if not (name and rad and lat and lon):
            self.ids.loc_name.hint_text = "COMPILA TUTTO!"
            return
            
        try:
            rad_val = int(rad)
            # Sostituiamo la virgola col punto per parsarli come Float
            lat_val = float(lat.replace(',', '.'))
            lon_val = float(lon.replace(',', '.'))
            
            app = App.get_running_app()
            if "locations" not in app.config_data:
                app.config_data["locations"] = []
                
            app.config_data["locations"].append({
                "name": name,
                "radius_m": rad_val,
                "lat": lat_val,
                "lon": lon_val
            })
            
            # Svuota i campi
            self.ids.loc_name.text = ""
            self.ids.loc_rad.text = ""
            self.ids.loc_lat.text = ""
            self.ids.loc_lon.text = ""
            self.ids.loc_name.hint_text = "Nome (es. Casa)"
            
            self.refresh_list()
            self.save_config()
        except Exception as e:
            self.ids.loc_name.text = ""
            self.ids.loc_name.hint_text = "ERRORE NUMERI!"
            
    def save_config(self):
        app = App.get_running_app()
        with open(CONFIG_FILE, "w") as f:
            json.dump(app.config_data, f, indent=4)
            
    def save_and_go_back(self):
        self.manager.current = 'config'

class ProximityApp(App):
    alarm_sound = None
    monitor_thread = None
    stop_event = threading.Event()
    wake_lock = None

    def on_pause(self):
        return True

    def on_resume(self):
        pass

    def acquire_wake_lock(self):
        if platform == 'android':
            try:
                from jnius import autoclass
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Context = autoclass('android.content.Context')
                
                pm = PythonActivity.mActivity.getSystemService(Context.POWER_SERVICE)
                self.wake_lock = pm.newWakeLock(1, "ProximityApp:BackgroundTracker")
                self.wake_lock.acquire()
                log_debug("Wakelock acquisito")
            except Exception as e:
                log_debug(f"Wakelock err: {str(e)}")

    def release_wake_lock(self):
        if self.wake_lock:
            try:
                self.wake_lock.release()
                log_debug("Wakelock rilasciato")
            except: pass
            self.wake_lock = None

    def build(self):
        log_debug("App Starting")
        try:
            self.load_config()
            self.sm = Builder.load_string(KV)
            Clock.schedule_once(self.load_libs, 1)
            # Pre-caricamento allarme
            self.reload_audio()
            return self.sm
        except Exception:
            err = traceback.format_exc(); log_debug(err)
            return Label(text="FATAL KV ERROR")

    def reload_audio(self):
        try:
            if self.alarm_sound:
                self.alarm_sound.stop()
                self.alarm_sound.unload()
        except: pass
        if self.config_data.get("custom_audio") and (DATA_DIR / "custom_alarm.mp3").exists():
            self.alarm_sound = SoundLoader.load(str(DATA_DIR / "custom_alarm.mp3"))
        else:
            self.alarm_sound = SoundLoader.load(str(ALARM_FILE))
        if self.alarm_sound:
            self.alarm_sound.loop = True

    def load_config(self):
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r") as f: self.config_data = json.load(f)
            else:
                self.config_data = {"google_email": "", "ntfy_topic": "proximity_alert_test", "locations": []}
        except: self.config_data = {}

    def load_libs(self, dt):
        self.sm.get_screen('splash').status_text = "Caricamento librerie..."
        try:
            import requests # noqa
            from locationsharinglib import Service # noqa
            self.sm.get_screen('splash').status_text = "Quasi pronto..."
            Clock.schedule_once(self.go_to_dashboard, 1)
        except Exception:
            log_debug(traceback.format_exc())
            self.sm.get_screen('splash').status_text = "Errore Init!"

    def go_to_dashboard(self, dt):
        self.sm.current = 'dashboard'

    def toggle_monitoring(self):
        dash = self.sm.get_screen('dashboard')
        dash.is_running = not dash.is_running
        if dash.is_running:
            self.stop_event.clear()
            if not hasattr(self, 'tracked_states'):
                self.tracked_states = {}
            self.acquire_wake_lock()
            self.monitor_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
            self.monitor_thread.start()
            dash.monitoring_status = "ATTIVO"
        else:
            self.stop_event.set()
            dash.monitoring_status = "INATTIVO"
            self.stop_alarm()
            self.release_wake_lock()

    def monitoring_loop(self):
        log_debug("Monitor loop started")
        from locationsharinglib import Service
        
        # Patch locationsharinglib to skip cookie file writing if needed, but here we use a file.
        # We need a Netscape cookie file.
        netscape_file = DATA_DIR / "cookies.txt"
        
        while not self.stop_event.is_set():
            try:
                if not COOKIES_FILE.exists():
                    self.update_ui_status("COOKIES MANCANTI")
                    time.sleep(10); continue

                # Convert pkl to Netscape
                with open(COOKIES_FILE, "rb") as f:
                    cookies = pickle.load(f)
                
                lines = ["# Netscape HTTP Cookie File"]
                for c in cookies:
                    domain = c.get('domain', '.google.com')
                    path = c.get('path', '/')
                    expires = int(c.get('expirationDate', c.get('expires', time.time() + 31536000)))
                    name, value = c.get('name'), c.get('value')
                    if name and value:
                        lines.append(f"{domain}\tTRUE\t{path}\tFALSE\t{expires}\t{name}\t{value}")
                
                with open(netscape_file, "w") as f: f.write("\n".join(lines))
                
                service = Service(cookies_file=str(netscape_file))
                people = list(service.get_shared_people())
                
                found_someone_close = False
                for person in people:
                    name = person.full_name or "Sconosciuto"
                    pid = person.id
                    lat, lon = person.latitude, person.longitude
                    
                    for loc in self.config_data.get("locations", []):
                        loc_name = loc['name']
                        t_lat, t_lon = loc['lat'], loc['lon']
                        radius = loc.get('radius_m', 100)
                        
                        dist = self.haversine(lat, lon, t_lat, t_lon)
                        inside = dist <= radius
                        
                        state_key = f"{pid}_{loc_name}"
                        was_inside = self.tracked_states.get(state_key, False)
                        
                        if inside:
                            found_someone_close = True
                            if not was_inside:
                                self.send_ntfy(name, loc_name, dist, "ENTRATO")
                        else:
                            if was_inside:
                                self.send_ntfy(name, loc_name, dist, "USCITO")

                        self.tracked_states[state_key] = inside
                
                if found_someone_close:
                    Clock.schedule_once(lambda dt: self.play_alarm())
                else:
                    Clock.schedule_once(lambda dt: self.stop_alarm())
                
                Clock.schedule_once(lambda dt: self.update_dashboard(people))
                
            except Exception as e:
                log_debug(f"Loop Error: {str(e)}")
            
            time.sleep(10)

    def haversine(self, lat1, lon1, lat2, lon2):
        R = 6371000
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi, dlambda = math.radians(lat2-lat1), math.radians(lon2-lon1)
        a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
        return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1-a))

    def send_ntfy(self, name, loc_name, dist, status="ENTRATO"):
        topic = self.config_data.get("ntfy_topic", "proximity_alert_test")
        try:
            if status == "ENTRATO":
                msg = f"{name} è ENTRATO nel raggio di {loc_name} ({dist:.0f}m)"
                title = f"Allarme: ENTRATO"
            else:
                msg = f"{name} è USCITO dal raggio di {loc_name}"
                title = f"Allarme: USCITO"
            
            requests.post(f"https://ntfy.sh/{topic}", 
                          data=msg.encode("utf-8"),
                          headers={"Title": title, "Priority": "high"})
        except: pass

    def play_alarm(self):
        if self.alarm_sound and self.alarm_sound.state != 'play':
            self.alarm_sound.play()

    def stop_alarm(self):
        if self.alarm_sound:
            self.alarm_sound.stop()

    def update_dashboard(self, people):
        dash = self.sm.get_screen('dashboard')
        dash.last_update = datetime.now().strftime("%H:%M:%S")
        dash.update_list(people, self.config_data.get("locations", []))

    def update_ui_status(self, msg):
        def _upd(dt): self.sm.get_screen('dashboard').monitoring_status = msg
        Clock.schedule_once(_upd)

if __name__ == "__main__":
    try: ProximityApp().run()
    except Exception: log_debug(traceback.format_exc())

'''
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(content)

# --- STEP 2: buildozer.spec (V4.4) ---
spec = r'''
[app]
title = Proximity Alert
package.name = proximityalert
package.domain = org.proximity
source.dir = .
source.include_exts = py,png,jpg,kv,json,mp3,pkl
version = 4.5
requirements = python3,kivy,openssl,requests,urllib3,charset-normalizer,idna,locationsharinglib,cachetools,plyer,beautifulsoup4,pytz,six,pyjnius
orientation = portrait
android.permissions = INTERNET, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION, WAKE_LOCK, FOREGROUND_SERVICE, ACCESS_BACKGROUND_LOCATION
android.api = 31
android.minapi = 21
android.private_storage = True
[buildozer]
log_level = 2
warn_on_root = 1
'''
with open('buildozer.spec', 'w', encoding='utf-8') as f:
    f.write(spec)

# --- STEP 3: COMPILAZIONE ---
!pip install buildozer cython==0.29.33
!sudo apt-get install -y scons libncurses5 aria2 build-essential libltdl-dev libffi-dev libssl-dev python3-dev autoconf automake libtool pkg-config zlib1g-dev adb
!buildozer -v android debug
```
