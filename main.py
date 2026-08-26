"""
Mihrab - İslami Yaşam Rehberi
Version: 2.0 - SADE VERSİYON
Dua talebi, kullanıcı girişi, admin paneli YOK!
Sadece İslami Yaşam Rehberi!
"""

import random
import os
import json
from datetime import datetime, timedelta

from kivy.logger import Logger

from kivy.config import Config
Config.set('graphics', 'width', '420')
Config.set('graphics', 'height', '760')
Config.set('graphics', 'resizable', True)

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.utils import platform

# KivyMD
from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, MDListItem, MDListItemHeadlineText, MDListItemSupportingText, MDListItemLeadingIcon
from kivymd.uix.navigationbar import MDNavigationBar, MDNavigationItem, MDNavigationItemLabel, MDNavigationItemIcon

# Özel modüller
from data_loader import data_loader
from language_manager import language_manager
from notifier import notifier
from prayer_manager import prayer_manager
from islamic_tools import qibla_finder, hijri_calendar, digital_tasbih

# ============= FONT AYARLARI =============
FONT_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'fonts', 'amiri.ttf')

# Varsayılan font her zaman 'Roboto'
ARABIC_FONT = 'Roboto'

if os.path.exists(FONT_PATH):
    try:
        LabelBase.register(name='Arabic', fn_regular=FONT_PATH)
        ARABIC_FONT = 'Arabic'
    except Exception as e:
        ARABIC_FONT = 'Roboto'
else:
    ARABIC_FONT = 'Roboto'

# ============= RENK SABİTLERİ =============
GOLD = [1, 0.702, 0, 1]
GOLD_DARK = [1, 0.561, 0, 1]
GOLD_LIGHT = [1, 0.843, 0.4, 1]
BG_LIGHT = [0.98, 0.96, 0.92, 1]
BG_DARK = [0.06, 0.06, 0.06, 1]
CARD_LIGHT = [1, 1, 1, 1]
CARD_DARK = [0.18, 0.18, 0.18, 1]
TEXT_LIGHT = [0, 0, 0, 1]
TEXT_DARK = [1, 1, 1, 1]
TEXT_MUTED_LIGHT = [0.3, 0.3, 0.3, 1]
TEXT_MUTED_DARK = [0.7, 0.7, 0.7, 1]
POPUP_BG = [1, 1, 1, 1]
POPUP_TEXT = [0, 0, 0, 1]

# ============= PROGRESS BAR =============
class ProgressBarWidget(Widget):
    value = NumericProperty(0)
    maximum = NumericProperty(100)
    
    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint = (1, None)
        self.height = dp(10)
        self.bind(pos=self._update, size=self._update, value=self._update)
    
    def _update(self, *a):
        self.canvas.clear()
        with self.canvas:
            Color(0.2, 0.2, 0.2, 0.3)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(5)])
            Color(*GOLD)
            w = (self.value / self.maximum * self.width) if self.maximum > 0 else 0
            if w > 0:
                RoundedRectangle(pos=self.pos, size=(w, self.height), radius=[dp(5)])

# ============= ANA UYGULAMA =============
class MihrabApp(MDApp):
    _instance = None
    _loaded = False
    current_tab = StringProperty("prayer")
    is_dark = BooleanProperty(False)
    
    def __init__(self, **kw):
        super().__init__(**kw)
        self.version = "2.0.0"
        self.dl = data_loader
        self.lang = language_manager
        self.notif = notifier
        self.prayer = prayer_manager
        self.qibla = qibla_finder
        self.hijri = hijri_calendar
        self.tasbih = digital_tasbih
        
        self.city_id = None
        self.city_name = ""
        self.dist_id = None
        self.dist_name = ""
        self.pdata = {}
        self.user_location = None
        self._city_menu = None
        self._dist_menu = None
        self._zikir_menu = None
        self._lang_menu = None
        
        self.library_data = None
        self.quran_data = []
        self.special_days = None
        self.daily_content = None
        self.notification_scheduled = False
        self.quran_search_results = []
        
        self.theme_cls.primary_palette = "Yellow"
        self.theme_cls.primary_hue = "700"
        self.title = "Mihrab"
        self.is_android = platform == 'android'
        self.is_ios = platform == 'ios'
        self.gps = None
        
        # ✅ User-Agent listesi
        self.user_agents = [
            'Mihrab/2.0 (Islamic App)',
            'Mihrab-IslamicApp/2.0',
            'MihrabApp/2.0 (Android)',
            'Mihrab/2.0 (iOS)',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
        ]
        self._last_ua_index = 0
    
    def _get_random_user_agent(self):
        """Rastgele User-Agent döndür"""
        self._last_ua_index = (self._last_ua_index + 1) % len(self.user_agents)
        return self.user_agents[self._last_ua_index]
    
    def build(self):
        try:
            internet_status = self.prayer.check_internet()
            Logger.info(f"Mihrab: İnternet durumu: {internet_status}")
        except Exception as e:
            Logger.error(f"Mihrab: İnternet kontrolü hatası: {e}")
            internet_status = True
        
        if not internet_status:
            self._show_no_internet_warning()
        
        self._load_all_data()
        
        self.root = MDBoxLayout(orientation='vertical', md_bg_color=self._get_bg_color())
        
        # ============= TOOLBAR =============
        self.toolbar = MDBoxLayout(
            orientation='horizontal',
            size_hint=(1, None),
            height=dp(50),
            md_bg_color=GOLD,
            padding=[dp(10), 0, dp(10), 0]
        )
        
        # Başlık
        self.title_label = Label(
            text="Mihrab",
            halign='left',
            valign='middle',
            font_size=20,
            bold=True,
            color=[1, 1, 1, 1],
            size_hint=(1, 1)
        )
        self.toolbar.add_widget(self.title_label)
        
        # Sağ taraftaki butonlar
        right_box = MDBoxLayout(orientation='horizontal', size_hint=(None, 1), width=dp(48), spacing=dp(8))
        
        # ✅ Sadece ayarlar butonu
        self.settings_btn = MDIconButton(
            icon="cog",
            md_bg_color=GOLD_DARK,
            size_hint=(None, 1),
            width=dp(40),
            radius=[dp(8)]
        )
        self.settings_btn.bind(on_release=self._show_settings_popup)
        right_box.add_widget(self.settings_btn)
        
        self.toolbar.add_widget(right_box)
        self.root.add_widget(self.toolbar)
        
        # ============= ANA İÇERİK =============
        self.main_content = MDBoxLayout(orientation='vertical')
        self.root.add_widget(self.main_content)
        
        # Scroll alanı
        self.scroll = MDScrollView()
        self.box = MDBoxLayout(
            orientation='vertical',
            padding=dp(10),
            spacing=dp(8),
            adaptive_height=True
        )
        self.scroll.add_widget(self.box)
        
        # ============= NAVIGATION =============
        self._build_navigation()
        
        Clock.schedule_once(lambda dt: self.go("prayer"), 0.1)
        self._apply_theme()
        
        Clock.schedule_once(lambda dt: self._check_location(), 0.5)
        
        Clock.schedule_interval(self._tick, 30)
        Clock.schedule_interval(self._update_remaining_time, 60)
        Clock.schedule_interval(self._check_special_days, 3600)
        
        return self.root
    
    def _get_safe_font(self, use_arabic=False):
        """Güvenli font adı döndürür"""
        if use_arabic and ARABIC_FONT != 'Roboto':
            return ARABIC_FONT
        return 'Roboto'
    
    def _check_location(self):
        """Şehir seçili değilse uyarı göster"""
        if not self.city_name:
            self._show_location_alert()
    
    def _show_location_alert(self):
        """Küçük uyarı popup'u"""
        content = MDBoxLayout(
            orientation='vertical',
            spacing=dp(10),
            padding=dp(16),
            size_hint=(1, None),
            height=dp(150),
            md_bg_color=[1, 1, 1, 1]
        )
        
        content.add_widget(Label(
            text="📍 Konum Seçimi Gerekli",
            halign='center',
            valign='middle',
            font_size=16,
            bold=True,
            color=GOLD,
            size_hint=(1, None),
            height=dp(30)
        ))
        
        content.add_widget(Label(
            text="Namaz vakitleri için şehir seçin veya GPS ile konum belirleyin.",
            halign='center',
            valign='middle',
            font_size=13,
            color=[0.3, 0.3, 0.3, 1],
            size_hint=(1, None),
            height=dp(40)
        ))
        
        btn_row = MDBoxLayout(
            spacing=dp(8),
            size_hint=(1, None),
            height=dp(40)
        )
        
        city_btn = MDButton(
            MDButtonText(text="🏙️ Şehir Seç", font_size=13),
            md_bg_color=GOLD,
            style="elevated"
        )
        city_btn.bind(on_release=self._menu_city)
        btn_row.add_widget(city_btn)
        
        gps_btn = MDButton(
            MDButtonText(text="📍 GPS ile Bul", font_size=13),
            md_bg_color=GOLD_LIGHT,
            style="elevated"
        )
        gps_btn.bind(on_release=lambda x: self._start_gps())
        btn_row.add_widget(gps_btn)
        
        content.add_widget(btn_row)
        
        self.location_popup = Popup(
            title="⚠️ Uyarı",
            content=content,
            size_hint=(0.85, 0.35),
            auto_dismiss=False,
            background_color=[1, 1, 1, 1],
            title_color=[0, 0, 0, 1],
            separator_color=[0.8, 0.8, 0.8, 1]
        )
        self.location_popup.open()
    
    def _show_no_internet_warning(self):
        """İnternet yok uyarısı"""
        if not hasattr(self, 'prayer') or not self.prayer:
            return

        box = MDBoxLayout(orientation='vertical', padding=dp(20), spacing=dp(15))
        box.add_widget(Label(
            text="⚠️ İnternet Bağlantısı Yok!\n\nNamaz vakitleri alınamayabilir.\nLütfen internet bağlantınızı kontrol edin.",
            halign='center',
            valign='middle',
            font_size=14,
            color=[0, 0, 0, 1],
            size_hint=(1, 1)
        ))
        btn = MDButton(
            MDButtonText(text="Tamam", font_size=14),
            md_bg_color=GOLD,
            style="elevated",
            size_hint=(1, None),
            height=dp(50)
        )
        box.add_widget(btn)
        popup = Popup(
            title="🌙 Mihrab",
            content=box,
            size_hint=(0.85, 0.35),
            auto_dismiss=False,
            background_color=[1, 1, 1, 1],
            title_color=[0, 0, 0, 1]
        )
        btn.bind(on_release=popup.dismiss)
        popup.open()
    
    def _load_all_data(self):
        """Tüm verileri yükle"""
        if hasattr(self, '_data_loaded') and self._data_loaded:
            Logger.info("Main: Veriler zaten yüklü, atlanıyor")
            return
        
        Logger.info("Main: Veriler yükleniyor...")
        
        # 1. Kuran (API'den)
        try:
            self.quran_data = self.dl.get_quran()
            if self.quran_data:
                Logger.info(f"Main: Kuran verileri yüklendi ({len(self.quran_data)} sure)")
            else:
                Logger.warning("Main: Kuran verisi yüklenemedi, boş liste kullanılıyor")
                self.quran_data = []
        except Exception as e:
            Logger.error(f"Main: Kuran yükleme hatası - {e}")
            self.quran_data = []
        
        # 2. Dini günler
        try:
            days_file = os.path.join(os.path.dirname(__file__), 'assets', 'data', 'special_days.json')
            if os.path.exists(days_file):
                with open(days_file, 'r', encoding='utf-8') as f:
                    self.special_days = json.load(f)
                Logger.info("Main: Dini günler yüklendi")
            else:
                self.special_days = {}
                Logger.warning("Main: special_days.json bulunamadı")
        except Exception as e:
            Logger.error(f"Main: Dini günler yükleme hatası - {e}")
            self.special_days = {}
        
        # 3. Günlük içerik
        try:
            content_file = os.path.join(os.path.dirname(__file__), 'assets', 'data', 'daily_content.json')
            if os.path.exists(content_file):
                with open(content_file, 'r', encoding='utf-8') as f:
                    self.daily_content = json.load(f)
                Logger.info("Main: Günlük içerik yüklendi")
            else:
                self.daily_content = {"ayetler": [], "hadisler": []}
                Logger.warning("Main: daily_content.json bulunamadı")
        except Exception as e:
            Logger.error(f"Main: Günlük içerik yükleme hatası - {e}")
            self.daily_content = {"ayetler": [], "hadisler": []}
        
        # 4. Kütüphane
        try:
            lib_file = os.path.join(os.path.dirname(__file__), 'assets', 'data', 'library.json')
            if os.path.exists(lib_file):
                with open(lib_file, 'r', encoding='utf-8') as f:
                    self.library_data = json.load(f)
                Logger.info("Main: Kütüphane verileri yüklendi")
            else:
                self.library_data = {"kategoriler": []}
                Logger.warning("Main: library.json bulunamadı")
        except Exception as e:
            Logger.error(f"Main: Kütüphane yükleme hatası - {e}")
            self.library_data = {"kategoriler": []}
        
        self._data_loaded = True
        Logger.info("Main: Tüm veriler başarıyla yüklendi")
    
    def _build_navigation(self):
        """Navigation bar oluştur"""
        self.nav = MDNavigationBar(
            md_bg_color=self._get_card_color()
        )
        
        tabs = [
            ("Vakitler", "mosque-outline", "prayer"),
            ("Kuran", "book-open-variant", "quran"),
            ("Dualar", "book-open-page-variant", "dua"),
            ("Tesbih", "counter", "tasbih"),
            ("Kıble", "compass", "qibla"),
            ("Kütüphane", "bookshelf", "library")
        ]
        
        for name, icon, tid in tabs:
            item = MDNavigationItem(
                MDNavigationItemIcon(icon=icon),
                MDNavigationItemLabel(text=name)
            )
            item.bind(on_release=lambda x, t=tid: self.go(t))
            self.nav.add_widget(item)
        
        self.theme_cls.primary_palette = "Yellow"
        self.theme_cls.primary_hue = "700"
        
        self.root.add_widget(self.nav)
    
    def _apply_theme(self):
        """Temayı uygula"""
        self.theme_cls.theme_style = "Dark" if self.is_dark else "Light"
        Window.clearcolor = BG_DARK if self.is_dark else BG_LIGHT
        
        if hasattr(self, 'root') and self.root:
            self.root.md_bg_color = self._get_bg_color()
        
        if hasattr(self, 'nav'):
            self.nav.md_bg_color = self._get_card_color()
    
    def _get_bg_color(self):
        return BG_DARK if self.is_dark else BG_LIGHT
    
    def _get_card_color(self):
        return CARD_DARK if self.is_dark else CARD_LIGHT
    
    def _get_text_color(self):
        return TEXT_DARK if self.is_dark else TEXT_LIGHT
    
    def _get_muted_color(self):
        return TEXT_MUTED_DARK if self.is_dark else TEXT_MUTED_LIGHT
    
    def go(self, tab):
        self.current_tab = tab
        self.main_content.clear_widgets()
        
        titles = {
            "prayer": "🕌 Namaz Vakitleri",
            "quran": "📖 Kuran-ı Kerim",
            "dua": "📖 Dualar & Sureler",
            "tasbih": "📿 Dijital Tesbih",
            "qibla": "🧭 Kıble Bulucu",
            "library": "📚 İslami Kütüphane"
        }
        self.title_label.text = titles.get(tab, "Mihrab")
        
        if tab == "quran":
            self._show_quran_layout()
        else:
            self.main_content.add_widget(self.scroll)
            self.box.clear_widgets()
            getattr(self, f"show_{tab}")()
    
    def _toast(self, msg):
        try:
            MDSnackbar(MDSnackbarText(text=msg), duration=2.5).open()
        except:
            print(f"🔔 {msg}")
    
    
    # ============= KONUM ALMA (GPS) =============
    def _start_gps(self):
        if platform == 'android':
            try:
                from plyer import gps
                # ✅ GPS configure'u doğru yap
                gps.configure(on_location=self._on_gps_location, on_error=self._on_gps_error)
                gps.start()
                self._toast("📍 Konum alınıyor...")
            except Exception as e:
                self._toast("❌ GPS kullanılamıyor")
                Logger.error(f"GPS hatası: {e}")
        else:
            self._toast("❌ GPS sadece Android'de çalışır")

    def _on_gps_location(self, location):
        """
        ✅ GPS konum alındığında çalışır
        - Koordinatları alır
        - Namaz vakitlerini API'dan çeker
        - Şehir adını reverse geocode ile bulur
        - Ekranda şehir adını gösterir
        """
        try:
            lat = location.get('lat', 0)
            lon = location.get('lon', 0)
            
            if lat and lon:
                Logger.info(f"GPS konum alındı: Lat: {lat}, Lon: {lon}")
                
                # ✅ Kullanıcı konumunu kaydet
                self.user_location = {'lat': lat, 'lon': lon}
                
                # ✅ Koordinatları PrayerManager'a gönder
                self.prayer.set_location(lat, lon)
                
                # ✅ Namaz vakitlerini koordinatlardan al
                self._toast("🔄 Vakitler alınıyor...")
                self.pdata = self.prayer.get_prayer_times_by_coordinates(lat, lon, method=13)
                
                if self.pdata:
                    # ✅ Vakitleri göster
                    self._fill_prayer_times()
                    self._toast("✅ Vakitler güncellendi (GPS)")
                    
                    # ✅ Kalan süreyi güncelle
                    self._update_remaining_time()
                    
                    # ✅ Bildirimleri zamanla
                    if not self.notification_scheduled:
                        self._schedule_prayer_notifications()
                        self.notification_scheduled = True
                else:
                    self._toast("❌ Vakit alınamadı, interneti kontrol edin")
                
                # ✅ Konum popup'ını kapat
                if hasattr(self, 'location_popup') and self.location_popup:
                    self.location_popup.dismiss()
                
                # ✅ Reverse geocode ile şehir adını bul (ekranda göster)
                self._reverse_geocode(lat, lon)
                
                # GPS'i durdur
                if self.gps:
                    try:
                        self.gps.stop()
                    except:
                        pass
                    
        except Exception as e:
            Logger.error(f"Konum işleme hatası: {e}")
            self._toast("❌ Konum işlenirken hata oluştu")

    def _reverse_geocode(self, lat, lon):
        """
        ✅ Koordinatlardan şehir adını bul (OpenStreetMap Nominatim API)
        Bu fonksiyon ekranda şehir adını gösterir
        """
        try:
            import requests
            
            # User-Agent
            user_agent = self._get_random_user_agent()
            
            # Nominatim API (ücretsiz, dünya çapında)
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&accept-language=tr&zoom=10"
            
            response = requests.get(
                url, 
                timeout=5, 
                headers={
                    'User-Agent': user_agent,
                    'Accept': 'application/json',
                    'Accept-Language': 'tr-TR,tr;q=0.9,en;q=0.8'
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                address = data.get('address', {})
                
                # ✅ Şehir bilgisini al (öncelik sırasına göre)
                city = (
                    address.get('city') or 
                    address.get('town') or 
                    address.get('county') or 
                    address.get('state_district') or 
                    address.get('state') or
                    address.get('country')
                )
                
                # ✅ İlçe bilgisini al
                district = (
                    address.get('suburb') or 
                    address.get('district') or 
                    address.get('village') or
                    address.get('neighbourhood')
                )
                
                if city:
                    # ✅ Ekranda göster
                    self.city_name = city
                    self.dist_name = district or ""
                    
                    # ✅ Loc label'ı güncelle
                    loc_text = self.city_name[:20]
                    if self.dist_name:
                        loc_text += f" - {self.dist_name[:15]}"
                    
                    if hasattr(self, 'loc_label'):
                        self.loc_label.text = loc_text
                    
                    Logger.info(f"Reverse geocode: {city} - {district if district else ''}")
                    self._toast(f"📍 {city}")
                else:
                    Logger.warning("Reverse geocode: Şehir bulunamadı")
                    self.city_name = "Konum"
                    if hasattr(self, 'loc_label'):
                        self.loc_label.text = "📍 GPS Konum"
                    
            else:
                Logger.warning(f"Reverse geocode başarısız: {response.status_code}")
                self.city_name = "GPS Konum"
                if hasattr(self, 'loc_label'):
                    self.loc_label.text = "📍 GPS Konum"
                    
        except requests.exceptions.Timeout:
            Logger.warning("Reverse geocode timeout")
            self.city_name = "GPS Konum"
            if hasattr(self, 'loc_label'):
                self.loc_label.text = "📍 GPS Konum"
        except requests.exceptions.ConnectionError:
            Logger.warning("Reverse geocode bağlantı hatası")
            self.city_name = "GPS Konum"
            if hasattr(self, 'loc_label'):
                self.loc_label.text = "📍 GPS Konum"
        except Exception as e:
            Logger.error(f"Ters coğrafi kodlama hatası: {e}")
            self.city_name = "GPS Konum"
            if hasattr(self, 'loc_label'):
                self.loc_label.text = "📍 GPS Konum"

    def _on_gps_error(self, error):
        """GPS hatası"""
        self._toast("❌ Konum alınamadı")
        Logger.error(f"GPS hatası: {error}")
        if self.gps:
            try:
                self.gps.stop()
            except:
                pass
            
            
    def _show_daily_dua(self):
        """Günün duasını göster - ORTALANMIŞ, KAYDIRILABİLİR"""
        dualar = self.dl.get_dualar()
        if not dualar:
            return
        
        dua = random.choice(dualar)
        
        from kivy.uix.scrollview import ScrollView
        
        box = MDBoxLayout(
            orientation='vertical',
            spacing=dp(2),
            padding=dp(8),
            size_hint=(1, None),
            height=dp(75)
        )
        
        baslik = Label(
            text="📿 Günün Duası",
            halign='center',
            valign='middle',
            font_size=10,
            bold=True,
            color=GOLD,
            size_hint=(1, None),
            height=dp(16),
            padding=(dp(8), 0),
            font_name='Roboto'
        )
        box.add_widget(baslik)
        
        scroll = ScrollView(
            size_hint=(1, None),
            height=dp(38),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(3),
            bar_color=[0.5, 0.5, 0.5, 0.3]
        )
        
        dua_label = Label(
            text=f"\"{dua.get('okunus', '')}\"",
            halign='center',
            valign='top',
            font_size=10,
            color=self._get_text_color(),
            size_hint=(1, None),
            padding=(dp(8), dp(2)),
            text_size=(Window.width - dp(100), None),
            font_name='Roboto'
        )
        dua_label.bind(texture_size=lambda i, v: setattr(i, 'height', v[1]))
        scroll.add_widget(dua_label)
        box.add_widget(scroll)
        
        kategori = Label(
            text=f"📌 {dua.get('kategori', 'Dua')}",
            halign='center',
            valign='middle',
            font_size=8,
            color=self._get_muted_color(),
            size_hint=(1, None),
            height=dp(14),
            padding=(dp(8), 0),
            font_name='Roboto'
        )
        box.add_widget(kategori)
        
        dua_card = MDCard(
            box,
            size_hint=(1, None),
            height=dp(75),
            md_bg_color=self._get_card_color(),
            elevation=1,
            radius=dp(10)
        )
        dua_card.bind(on_release=lambda x: self._show_dua_detail(dua))
        self.box.add_widget(dua_card)
    
    # ============= PRAYER PAGE =============
    def show_prayer(self):
        """
        Namaz vakitleri sayfasını göster
        - Topbar
        - Kalan Süre (ÜSTTE)
        - Günün Ayeti
        - Günün Hadisi
        - Günün Duası
        - Namaz Vakitleri (KARTLAR)
        - Hicri Tarih (ALTA)  ← EN ALTTA!
        """
        if not self.prayer.check_internet():
            self._toast("⚠️ İnternet bağlantısı yok!")
            self.box.add_widget(Label(
                text="⚠️ İnternet Bağlantısı Yok\nLütfen bağlantınızı kontrol edin",
                halign='center',
                valign='middle',
                font_size=16,
                color=[1, 0.3, 0.3, 1],
                size_hint=(1, None),
                height=dp(80)
            ))
            return
        
        # ============= TOPBAR =============
        topbar = MDBoxLayout(spacing=dp(6), size_hint=(1, None), height=dp(40))
        
        self.city_btn = MDButton(
            MDButtonText(text="🏙️ Şehir", font_size=11),
            md_bg_color=GOLD,
            style="elevated",
            size_hint=(None, 1),
            width=dp(70)
        )
        self.city_btn.bind(on_release=self._menu_city)
        topbar.add_widget(self.city_btn)
        
        refresh_btn = MDButton(
            MDButtonText(text="🔄", font_size=14),
            md_bg_color=GOLD_DARK,
            style="elevated",
            size_hint=(None, 1),
            width=dp(40)
        )
        refresh_btn.bind(on_release=self._refresh_prayer)
        topbar.add_widget(refresh_btn)
        
        gps_btn = MDButton(
            MDButtonText(text="📍", font_size=14),
            md_bg_color=GOLD_LIGHT,
            style="elevated",
            size_hint=(None, 1),
            width=dp(40)
        )
        gps_btn.bind(on_release=lambda x: self._start_gps())
        topbar.add_widget(gps_btn)
        
        loc_text = f"{self.city_name[:15]}" if self.city_name else "Konum"
        if self.dist_name:
            loc_text += f" - {self.dist_name[:15]}"
        self.loc_label = Label(
            text=loc_text,
            halign='right',
            valign='middle',
            font_size=10,
            bold=True,
            color=GOLD_DARK,
            size_hint=(1, 1)
        )
        topbar.add_widget(self.loc_label)
        self.box.add_widget(topbar)
        
        # ============= KALAN SÜRE (ÜSTTE) =============
        if hasattr(self, 'remaining_label') and self.remaining_label:
            try:
                self.box.remove_widget(self.remaining_label)
            except:
                pass
        
        self.remaining_label = Label(
            text="⏳ Hesaplanıyor...",
            halign='center',
            valign='middle',
            font_size=13,
            bold=True,
            color=GOLD,
            size_hint=(1, None),
            height=dp(28),
            font_name='Roboto'
        )
        self.box.add_widget(self.remaining_label)
        
        # ============= GÜNÜN AYETİ =============
        self._show_daily_ayah()
        
        # ============= GÜNÜN HADİSİ =============
        self._show_daily_hadith()
        
        # ============= GÜNÜN DUASI =============
        self._show_daily_dua()
        
        # ============= NAMAZ VAKİTLERİ GRİDİ =============
        self.prayer_grid = GridLayout(cols=2, spacing=dp(8), size_hint=(1, None))
        self.prayer_grid.bind(minimum_height=self.prayer_grid.setter('height'))
        self.box.add_widget(self.prayer_grid)
        
        if self.pdata:
            self._fill_prayer_times()
            if not self.notification_scheduled:
                self._schedule_prayer_notifications()
                self.notification_scheduled = True
        else:
            self._show_empty_prayer_cards()
        
        # ============= HİCRİ TARİH (EN ALTTA) =============
        # ✅ Hicri Tarih artık namaz vakitlerinin ALTINDA!
        hijri_date = self._get_hijri_text()
        hijri_label = Label(
            text=f"📅 {hijri_date}",
            halign='center',
            valign='middle',
            font_size=13,
            bold=True,
            color=GOLD,
            size_hint=(1, None),
            height=dp(28)
        )
        self.box.add_widget(hijri_label)
        
        # ✅ Kalan süreyi güncelle
        self._update_remaining_time()
                
    def _show_daily_ayah(self):
        """Günün ayetini göster - TAM METİN, KAYDIRILABİLİR"""
        if not self.daily_content or not self.daily_content.get('ayetler'):
            return
        
        day_of_year = datetime.now().timetuple().tm_yday
        ayetler = self.daily_content['ayetler']
        ayet = ayetler[day_of_year % len(ayetler)]
        
        # ✅ ScrollView ile kaydırılabilir metin
        from kivy.uix.scrollview import ScrollView
        
        # İçerik kutusu
        box = MDBoxLayout(
            orientation='vertical',
            spacing=dp(2),
            padding=dp(8),
            size_hint=(1, None),
            height=dp(80)  # ✅ Sabit yükseklik
        )
        
        # Başlık
        baslik = Label(
            text="📖 Günün Ayeti",
            halign='left',
            valign='middle',
            font_size=11,
            bold=True,
            color=GOLD,
            size_hint=(1, None),
            height=dp(18),
            padding=(dp(8), 0),
            font_name='Roboto'
        )
        box.add_widget(baslik)
        
        # ✅ ScrollView ile metin (kaydırılabilir)
        scroll = ScrollView(
            size_hint=(1, None),
            height=dp(40),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(3),
            bar_color=[0.5, 0.5, 0.5, 0.3]
        )
        
        ayet_label = Label(
            text=f"\"{ayet.get('metin', '')}\"",
            halign='left',
            valign='top',
            font_size=11,
            color=self._get_text_color(),
            size_hint=(1, None),
            padding=(dp(8), dp(2)),
            text_size=(Window.width - dp(100), None),  # ✅ Genişlik sınırı
            font_name='Roboto'
        )
        ayet_label.bind(texture_size=lambda i, v: setattr(i, 'height', v[1]))
        scroll.add_widget(ayet_label)
        box.add_widget(scroll)
        
        # Kaynak bilgisi
        kaynak = Label(
            text=f"📎 {ayet.get('sure', '')} {ayet.get('ayet', '')}",
            halign='right',
            valign='middle',
            font_size=9,
            color=self._get_muted_color(),
            size_hint=(1, None),
            height=dp(14),
            padding=(dp(8), 0),
            font_name='Roboto'
        )
        box.add_widget(kaynak)
        
        ayet_card = MDCard(
            box,
            size_hint=(1, None),
            height=dp(80),
            md_bg_color=self._get_card_color(),
            elevation=1,
            radius=dp(10)
        )
        self.box.add_widget(ayet_card)
    
    def _show_daily_hadith(self):
        """Günün hadisini göster - ORTALANMIŞ, TAM METİN, KAYDIRILABİLİR"""
        if not self.daily_content or not self.daily_content.get('hadisler'):
            return
        
        day_of_year = datetime.now().timetuple().tm_yday
        hadisler = self.daily_content['hadisler']
        hadis = hadisler[day_of_year % len(hadisler)]
        
        # ✅ ScrollView ile kaydırılabilir metin
        from kivy.uix.scrollview import ScrollView
        
        # İçerik kutusu
        box = MDBoxLayout(
            orientation='vertical',
            spacing=dp(2),
            padding=dp(8),
            size_hint=(1, None),
            height=dp(80)  # ✅ Sabit yükseklik
        )
        
        # Başlık (ORTALI)
        baslik = Label(
            text="📜 Günün Hadisi",
            halign='center',  # ✅ ORTALI!
            valign='middle',
            font_size=11,
            bold=True,
            color=GOLD,
            size_hint=(1, None),
            height=dp(18),
            padding=(dp(8), 0),
            font_name='Roboto'
        )
        box.add_widget(baslik)
        
        # ✅ ScrollView ile metin (kaydırılabilir)
        scroll = ScrollView(
            size_hint=(1, None),
            height=dp(40),
            do_scroll_x=False,
            do_scroll_y=True,
            bar_width=dp(3),
            bar_color=[0.5, 0.5, 0.5, 0.3]
        )
        
        hadis_label = Label(
            text=f"\"{hadis.get('metin', '')}\"",
            halign='center',  # ✅ ORTALI!
            valign='top',
            font_size=11,
            color=self._get_text_color(),
            size_hint=(1, None),
            padding=(dp(8), dp(2)),
            text_size=(Window.width - dp(100), None),  # ✅ Genişlik sınırı
            font_name='Roboto'
        )
        hadis_label.bind(texture_size=lambda i, v: setattr(i, 'height', v[1]))
        scroll.add_widget(hadis_label)
        box.add_widget(scroll)
        
        # Kaynak bilgisi (ORTALI)
        kaynak = Label(
            text=f"📎 {hadis.get('kaynak', '')}",
            halign='center',  # ✅ ORTALI!
            valign='middle',
            font_size=9,
            color=self._get_muted_color(),
            size_hint=(1, None),
            height=dp(14),
            padding=(dp(8), 0),
            font_name='Roboto'
        )
        box.add_widget(kaynak)
        
        hadis_card = MDCard(
            box,
            size_hint=(1, None),
            height=dp(80),
            md_bg_color=self._get_card_color(),
            elevation=1,
            radius=dp(10)
        )
        self.box.add_widget(hadis_card)
    
    def _get_hijri_text(self):
        h = self.hijri.gregorian_to_hijri()
        if h:
            special = self.hijri.is_special_day(h)
            if special:
                return f"{h['date_str']} - 🌟 {special}"
            return h['date_str']
        return "Hicri tarih alınamadı"
    
    def _update_remaining_time(self, *args):
        """Kalan namaz vakitlerini güncelle"""
        if not hasattr(self, 'remaining_label') or self.remaining_label is None:
            return
        
        if not self.pdata:
            self.remaining_label.text = "⏳ Vakit bekleniyor..."
            Clock.schedule_once(self._update_remaining_time, 30)
            return
        
        try:
            rem = self.prayer.get_remaining_time()
            
            if rem:
                name = rem.get('name', '')
                time_str = rem.get('time', '00:00')
                total_minutes = rem.get('total_minutes', 0)
                color_code = self._get_remaining_time_color(total_minutes)
                emoji = self._get_prayer_emoji(name)
                
                self.remaining_label.text = f"{emoji} Sonraki: {name} - {time_str} kaldı"
                self.remaining_label.color = color_code
                
                if total_minutes < 5:
                    interval = 5
                elif total_minutes < 15:
                    interval = 10
                elif total_minutes < 60:
                    interval = 15
                else:
                    interval = 30
                
                if total_minutes < 1:
                    interval = 1
                    
                Clock.schedule_once(self._update_remaining_time, interval)
                
            else:
                next_prayer = self._get_next_day_prayer()
                if next_prayer:
                    name = next_prayer.get('name', '')
                    time_str = next_prayer.get('time', '00:00')
                    emoji = self._get_prayer_emoji(name)
                    self.remaining_label.text = f"{emoji} Yarın: {name} - {time_str}"
                    self.remaining_label.color = [0.5, 0.5, 0.8, 1]
                    Clock.schedule_once(self._update_remaining_time, 60)
                else:
                    self.remaining_label.text = "⏳ Vakit bekleniyor..."
                    Clock.schedule_once(self._update_remaining_time, 30)
                        
        except Exception as e:
            Logger.error(f"Kalan süre güncelleme hatası: {e}")
            self.remaining_label.text = "⏳ Vakit hesaplanamadı"
            Clock.schedule_once(self._update_remaining_time, 60)
    
    def _get_next_day_prayer(self):
        if not self.pdata or not self.city_name:
            return None
        
        imsak = self.pdata.get('İmsak', '')
        if imsak:
            try:
                h, m = map(int, imsak.split(':'))
                m += 2
                if m >= 60:
                    h += 1
                    m -= 60
                new_time = f"{h:02d}:{m:02d}"
                return {'name': 'İmsak (Yarın)', 'time': new_time}
            except:
                pass
        
        return {'name': 'İmsak', 'time': '--:--'}
    
    def _get_remaining_time_color(self, total_minutes):
        if total_minutes < 5:
            return [1, 0.2, 0.2, 1]
        elif total_minutes < 15:
            return [1, 0.6, 0, 1]
        elif total_minutes < 30:
            return [1, 0.8, 0, 1]
        elif total_minutes < 60:
            return [0.4, 0.8, 0.2, 1]
        else:
            return [0.2, 0.7, 0.2, 1]

    def _get_prayer_emoji(self, prayer_name):
        emoji_map = {
            'İmsak': '🌅',
            'Güneş': '☀️',
            'Öğle': '🌞',
            'İkindi': '🌤️',
            'Akşam': '🌙',
            'Yatsı': '🌃'
        }
        return emoji_map.get(prayer_name, '🕌')
    
    def _show_empty_prayer_cards(self):
        self.prayer_grid.clear_widgets()
        icons = ['🌅', '☀️', '🌞', '🌤️', '🌙', '🌃']
        names = ['İmsak', 'Güneş', 'Öğle', 'İkindi', 'Akşam', 'Yatsı']
        muted_color = self._get_muted_color()
        card_color = self._get_card_color()
        
        for i in range(6):
            inner = MDBoxLayout(orientation='vertical', padding=dp(8), spacing=dp(2), adaptive_height=True)
            icon_label = Label(
                text=icons[i],
                halign='center',
                font_size=24,
                color=GOLD,
                size_hint=(1, None),
                height=dp(30)
            )
            inner.add_widget(icon_label)
            name_label = Label(
                text=names[i],
                halign='center',
                font_size=11,
                color=muted_color,
                size_hint=(1, None),
                height=dp(18)
            )
            inner.add_widget(name_label)
            time_label = Label(
                text="--:--",
                halign='center',
                font_size=18,
                bold=True,
                color=muted_color,
                size_hint=(1, None),
                height=dp(24)
            )
            inner.add_widget(time_label)
            inner.bind(minimum_height=inner.setter('height'))
            card = MDCard(inner, size_hint=(1, None), height=dp(85), md_bg_color=card_color, elevation=1, radius=dp(10))
            self.prayer_grid.add_widget(card)
    
    def _fill_prayer_times(self):
        """Namaz vakitlerini göster"""
        if hasattr(self, 'prayer_grid') and len(self.prayer_grid.children) == 6:
            try:
                prayer_names = list(self.pdata.keys())
                prayer_times = list(self.pdata.values())
                
                for i, card in enumerate(self.prayer_grid.children):
                    if i >= len(prayer_names):
                        break
                    
                    for child in card.children:
                        if isinstance(child, MDBoxLayout):
                            for label in child.children:
                                if isinstance(label, Label):
                                    if label.font_size == 18:
                                        if i < len(prayer_times):
                                            label.text = prayer_times[i]
                                    elif label.font_size == 11:
                                        if i < len(prayer_names):
                                            label.text = prayer_names[i]
                return
            except Exception as e:
                Logger.warning(f"Prayer: Metin güncelleme hatası: {e}")
        
        self.prayer_grid.clear_widgets()
        
        icons = {
            'İmsak': '🌅', 
            'Güneş': '☀️', 
            'Öğle': '🌞', 
            'İkindi': '🌤️', 
            'Akşam': '🌙', 
            'Yatsı': '🌃'
        }
        text_color = self._get_text_color()
        muted_color = self._get_muted_color()
        card_color = self._get_card_color()
        
        for name, time in self.pdata.items():
            inner = MDBoxLayout(orientation='vertical', padding=dp(8), spacing=dp(2), adaptive_height=True)
            
            icon_label = Label(
                text=icons.get(name, '🕌'),
                halign='center',
                font_size=24,
                color=GOLD,
                size_hint=(1, None),
                height=dp(30),
                font_name='Roboto'
            )
            inner.add_widget(icon_label)
            
            name_label = Label(
                text=name,
                halign='center',
                font_size=11,
                color=muted_color,
                size_hint=(1, None),
                height=dp(18),
                font_name='Roboto'
            )
            inner.add_widget(name_label)
            
            time_label = Label(
                text=time,
                halign='center',
                font_size=18,
                bold=True,
                color=text_color,
                size_hint=(1, None),
                height=dp(24),
                font_name='Roboto'
            )
            inner.add_widget(time_label)
            
            inner.bind(minimum_height=inner.setter('height'))
            
            card = MDCard(
                inner, 
                size_hint=(1, None), 
                height=dp(85), 
                md_bg_color=card_color, 
                elevation=1, 
                radius=dp(10)
            )
            
            card._name_label = name_label
            card._time_label = time_label
            
            self.prayer_grid.add_widget(card)
        
        Logger.info(f"Prayer: {len(self.pdata)} vakit kartı oluşturuldu")
    
    def _refresh_prayer(self, *args):
        """Namaz vakitlerini yenile"""
        if not self.city_name:
            self._toast("Önce bir şehir seçin")
            return
        
        if not self.prayer.check_internet():
            self._toast("❌ İnternet bağlantısı gerekli!")
            return
        
        location = self.city_name
        
        self._toast(f"🔄 Vakitler güncelleniyor: {location}")
        data = self.prayer.get_prayer_times(location)
        
        if data:
            self.pdata = data
            self._fill_prayer_times()
            self._toast("✅ Vakitler güncellendi")
            self._update_qibla()
            self._schedule_prayer_notifications()
        else:
            self._toast("❌ Vakit alınamadı")
        self._update_remaining_time()
    
    # ============= OTOMATİK NAMAZ BİLDİRİMİ =============
    def _schedule_prayer_notifications(self):
        if not self.pdata:
            return
        
        if hasattr(self, '_scheduled_events'):
            for event in self._scheduled_events:
                try:
                    Clock.unschedule(event)
                except:
                    pass
            self._scheduled_events.clear()
        else:
            self._scheduled_events = []
        
        now = datetime.now()
        prayer_list = ['İmsak', 'Güneş', 'Öğle', 'İkindi', 'Akşam', 'Yatsı']
        
        for name in prayer_list:
            try:
                time_str = self.pdata.get(name, '00:00')
                if ':' not in time_str:
                    continue
                    
                h, m = map(int, time_str.split(':'))
                prayer_time = now.replace(hour=h, minute=m, second=0, microsecond=0)
                
                if prayer_time <= now:
                    continue
                
                pre_time = prayer_time - timedelta(minutes=15)
                if pre_time > now:
                    delay_before = (pre_time - now).total_seconds()
                    if delay_before > 0:
                        event = Clock.schedule_once(
                            lambda dt, n=name: self._send_prayer_notification(n, "ön"),
                            delay_before
                        )
                        self._scheduled_events.append(event)
                        scheduled_count += 1
                
                delay_exact = (prayer_time - now).total_seconds()
                if delay_exact > 0:
                    event1 = Clock.schedule_once(
                        lambda dt, n=name: self._send_prayer_notification(n, "vakit"),
                        delay_exact
                    )
                    self._scheduled_events.append(event1)
                    
                    event2 = Clock.schedule_once(
                        lambda dt, n=name: self._play_adhan(n),
                        delay_exact + 5
                    )
                    self._scheduled_events.append(event2)
                    
            except:
                continue
    
    def _send_prayer_notification(self, name, tip=""):
        """✅ Namaz bildirimi + BİP sesi"""
        try:
            if tip == "ön":
                self.notif.send_notification(
                    title=f"🕌 {name} Vakti Yaklaşıyor",
                    message=f"{name} vaktine 15 dakika kaldı. Hazırlanın!",
                    vibration=True,
                    play_sound=True  # ✅ Bildirim sesi (2 kısa bip)
                )
            else:
                self.notif.send_notification(
                    title=f"🕌 {name} Vakti",
                    message=f"{name} vakti girdi. Allah kabul etsin!",
                    vibration=True,
                    play_sound=True  # ✅ Bildirim sesi (2 kısa bip)
                )
        except Exception as e:
            Logger.error(f"Bildirim gönderme hatası ({name}): {e}")

    def _play_adhan(self, name):
        """✅ Ezan bildirimi + BİP sesi"""
        try:
            # 1. Bildirim gönder
            self.notif.send_notification(
                title=f"🕌 {name} Vakti - Ezan",
                message=f"{name} ezanı okunuyor. Allahu Ekber!",
                vibration=True,
                play_sound=False  # Çünkü ses ayrı çalınacak
            )
            
            # 2. ✅ Bip sesi çal (Ezan için 3 uzun bip)
            self.notif.play_beep(count=3, duration=0.5)
            
        except Exception as e:
            Logger.error(f"Ezan bildirimi hatası ({name}): {e}")
    
    def _cancel_notifications(self):
        if hasattr(self, '_scheduled_events'):
            for event in self._scheduled_events:
                try:
                    Clock.unschedule(event)
                except:
                    pass
            self._scheduled_events.clear()
    
    # ============= KURAN SAYFASI =============
    def _show_quran_layout(self):
        """Kuran sayfası"""
        search_box = MDBoxLayout(orientation='horizontal', size_hint=(1, None), height=dp(44), spacing=dp(8), padding=[dp(10), dp(4), dp(10), dp(4)])
        search_box.md_bg_color = self._get_bg_color()
        
        self.quran_search_input = TextInput(
            hint_text="🔍 Sure veya ayet ara...",
            multiline=False,
            size_hint=(1, None),
            height=dp(36),
            background_color=[1, 1, 1, 1],
            foreground_color=[0, 0, 0, 1],
            font_size=13
        )
        self.quran_search_input.bind(text=self._search_quran)
        search_box.add_widget(self.quran_search_input)
        
        clear_btn = MDButton(
            MDButtonText(text="✖", font_size=12),
            md_bg_color=[0.8, 0.8, 0.8, 1],
            style="elevated",
            size_hint=(None, 1),
            width=dp(40)
        )
        clear_btn.bind(on_release=self._clear_quran_search)
        search_box.add_widget(clear_btn)
        
        self.main_content.add_widget(search_box)
        
        title_label = Label(
            text=f"📖 Kuran-ı Kerim ({len(self.quran_data)} Sure)",
            halign='center',
            valign='middle',
            font_size=16,
            bold=True,
            color=GOLD,
            size_hint=(1, None),
            height=dp(34)
        )
        self.main_content.add_widget(title_label)
        
        self.scroll = MDScrollView()
        self.box = MDBoxLayout(
            orientation='vertical',
            padding=dp(10),
            spacing=dp(8),
            adaptive_height=True
        )
        self.scroll.add_widget(self.box)
        self.main_content.add_widget(self.scroll)
        
        self.quran_list = MDList()
        self.box.add_widget(self.quran_list)
        
        self.quran_search_input.text = ""
        self.quran_search_results = self.quran_data
        self._display_quran_results()
    
    def _search_quran(self, instance, value):
        if not value.strip():
            self.quran_search_results = self.quran_data
        else:
            keyword = value.lower()
            results = []
            for sure in self.quran_data:
                if (keyword in sure.get('translation', '').lower() or 
                    keyword in sure.get('name', '').lower() or
                    keyword in sure.get('transliteration', '').lower()):
                    results.append(sure)
                else:
                    for verse in sure.get('verses', []):
                        if keyword in verse.get('translation', '').lower():
                            results.append(sure)
                            break
            self.quran_search_results = results
        self._display_quran_results()
    
    def _clear_quran_search(self, *args):
        self.quran_search_input.text = ""
        self.quran_search_results = self.quran_data
        self._display_quran_results()
    
    def _display_quran_results(self):
        if not hasattr(self, 'quran_list'):
            return
        self.quran_list.clear_widgets()
        
        if not self.quran_search_results:
            self.quran_list.add_widget(Label(
                text="🔍 Sonuç bulunamadı",
                halign='center',
                valign='middle',
                font_size=14,
                color=self._get_muted_color(),
                size_hint=(1, None),
                height=dp(50),
                font_name='Roboto'
            ))
            return
        
        for sure in self.quran_search_results:
            sure_id = sure.get('id', '?')
            sure_name = sure.get('translation', sure.get('name', 'Sure'))
            arabic_name = sure.get('arabic_name', '')
            total_verses = sure.get('verses_count', sure.get('total_verses', 0))
            
            card_box = MDBoxLayout(
                orientation='horizontal',
                padding=dp(8),
                spacing=dp(4),
                adaptive_height=True
            )
            
            if arabic_name:
                arabic_label = Label(
                    text=arabic_name[::-1],
                    halign='right',
                    font_size=18,
                    color=GOLD,
                    size_hint=(0.25, None),
                    height=dp(44),
                    padding=(dp(4), 0),
                    font_name=ARABIC_FONT
                )
                card_box.add_widget(arabic_label)
            
            info_box = MDBoxLayout(
                orientation='vertical',
                size_hint=(0.75 if arabic_name else 1, None),
                height=dp(44),
                spacing=dp(0),
                padding=(dp(8), 0, 0, 0)
            )
            
            name_label = Label(
                text=f"{sure_id}. {sure_name}",
                halign='left',
                valign='middle',
                font_size=13,
                bold=True,
                color=self._get_text_color(),
                size_hint=(1, 0.5),
                height=dp(22),
                font_name='Roboto'
            )
            info_box.add_widget(name_label)
            
            verse_label = Label(
                text=f"{total_verses} ayet",
                halign='left',
                valign='middle',
                font_size=10,
                color=self._get_muted_color(),
                size_hint=(1, 0.5),
                height=dp(22),
                font_name='Roboto'
            )
            info_box.add_widget(verse_label)
            
            card_box.add_widget(info_box)
            
            sure_card = MDCard(
                card_box,
                size_hint=(1, None),
                height=dp(52),
                md_bg_color=self._get_card_color(),
                elevation=1,
                radius=dp(10)
            )
            sure_card.bind(on_release=lambda x, s=sure: self._show_surah_detail(s))
            self.quran_list.add_widget(sure_card)
    
    def _show_surah_detail(self, sure):
        sure_id = sure.get('id', '?')
        sure_name = sure.get('translation', sure.get('name', 'Sure'))
        
        self._toast(f"📖 {sure_name} yükleniyor...")
        
        def load_detail(dt):
            detail = self.dl.get_surah_detail(sure_id)
            
            if detail:
                total_verses = detail.get('total_verses', 0)
                verses = detail.get('verses', [])
                surah_meaning = detail.get('surah_meaning', '')
                type_info = detail.get('type', '').upper()
                arabic_name = detail.get('arabic_name', '')
                
                content = ""
                
                if arabic_name:
                    reversed_arabic = arabic_name[::-1]
                    content += f"[b][size=24]{reversed_arabic}[/size][/b]\n\n"
                
                content += f"[b][size=18]📖 {sure_id}. {sure_name}[/size][/b]\n"
                if surah_meaning:
                    content += f"[i]📝 {surah_meaning}[/i]\n"
                content += f"📊 {total_verses} ayet | 📌 {type_info}\n\n"
                content += "─" * 30 + "\n\n"
                
                for verse in verses[:20]:
                    verse_id = verse.get('id', '')
                    verse_text = verse.get('text', '')
                    verse_transliteration = verse.get('transliteration', '')
                    verse_translation = verse.get('translation', '')
                    
                    reversed_text = verse_text[::-1]
                    
                    if len(verse_text) > 40 or '\n' in verse_text:
                        reversed_text = f"[b]Son[/b]\n{reversed_text}\n[b]Baş[/b]"
                    
                    content += f"[b][size=20]{verse_id}. {reversed_text}[/size][/b]\n"
                    
                    if verse_transliteration:
                        content += f"🔊 [i]{verse_transliteration}[/i]\n"
                    if verse_translation:
                        content += f"📝 {verse_translation}\n"
                    content += "\n"
                
                if total_verses > 20:
                    content += f"\n... ve {total_verses - 20} ayet daha\n"
                
                self._show_popup_rtl(f"{sure_name} Suresi", content)
            else:
                self._toast("❌ Sure detayları yüklenemedi")
        
        Clock.schedule_once(load_detail, 0.1)

    def _show_fallback_surah(self, sure_id, sure_name):
        content = f"""
    [b][size=18]📖 {sure_id}. {sure_name}[/size][/b]

    ⚠️ API bağlantısı kurulamadı.
    Lütfen internet bağlantınızı kontrol edin.

    📌 Alternatif olarak:
    • Daha sonra tekrar deneyin
    • Ayarlar'dan internet bağlantısını kontrol edin
    """
        self._show_popup_rtl(f"{sure_name} Suresi", content)
    
    def _show_popup_rtl(self, title, content, is_rtl=True):
        box = MDBoxLayout(
            orientation='vertical',
            padding=dp(12),
            spacing=dp(8),
            md_bg_color=[1, 1, 1, 1]
        )
        
        scr = ScrollView()
        
        use_arabic_font = is_rtl and ARABIC_FONT != 'Roboto'
        font_to_use = ARABIC_FONT if use_arabic_font else 'Roboto'
        
        lbl = Label(
            text=content,
            halign='right' if is_rtl else 'left',
            valign='top',
            padding=dp(12),
            text_size=(Window.width - dp(80), None),
            size_hint_y=None,
            font_size=14,
            color=[0, 0, 0, 1],
            font_name=font_to_use,
            markup=True
        )
        lbl.bind(texture_size=lambda i, v: setattr(i, 'height', v[1]))
        scr.add_widget(lbl)
        box.add_widget(scr)
        
        close_btn = MDButton(
            MDButtonText(text="✖ Kapat", font_size=12),
            md_bg_color=GOLD,
            style="elevated",
            size_hint=(1, None),
            height=dp(44)
        )
        box.add_widget(close_btn)
        
        pop = Popup(
            title=title,
            content=box,
            size_hint=(0.92, 0.75),
            auto_dismiss=False,
            background_color=[1, 1, 1, 1],
            title_color=[0, 0, 0, 1]
        )
        close_btn.bind(on_release=pop.dismiss)
        pop.open()
    
    # ============= DUA SAYFASI =============
    def show_dua(self):
        if not self.prayer.check_internet():
            self._toast("⚠️ İnternet bağlantısı yok!")
            return
        
        row = MDBoxLayout(spacing=dp(6), size_hint=(1, None), height=dp(40))
        
        btn1 = MDButton(MDButtonText(text="📖 Dualar", font_size=10), md_bg_color=GOLD, style="elevated")
        btn1.bind(on_release=self._list_dua)
        row.add_widget(btn1)
        
        btn2 = MDButton(MDButtonText(text="📜 Sureler", font_size=10), md_bg_color=GOLD, style="elevated")
        btn2.bind(on_release=self._list_surah)
        row.add_widget(btn2)
        
        btn3 = MDButton(MDButtonText(text="⭐ Esma", font_size=10), md_bg_color=GOLD, style="elevated")
        btn3.bind(on_release=self._list_esma)
        row.add_widget(btn3)
        
        self.box.add_widget(row)
        
        self.dua_list = MDList()
        self.box.add_widget(self.dua_list)
        self._list_dua()
    
    def _list_dua(self, *args):
        if not hasattr(self, 'dua_list'):
            return
        self.dua_list.clear_widgets()
        
        dualar = self.dl.get_dualar()
        if not dualar:
            self.dua_list.add_widget(Label(
                text="📭 Henüz dua bulunmuyor",
                halign='center',
                valign='middle',
                font_size=14,
                color=self._get_muted_color(),
                size_hint=(1, None),
                height=dp(50),
                font_name='Roboto'
            ))
            return
        
        for d in dualar:
            card_box = MDBoxLayout(
                orientation='vertical',
                padding=dp(10),
                spacing=dp(4),
                adaptive_height=True,
                md_bg_color=self._get_card_color()
            )
            
            category_label = Label(
                text=f"📖 {d.get('kategori', 'Dua')}",
                halign='left',
                valign='middle',
                font_size=13,
                bold=True,
                color=GOLD,
                size_hint=(1, None),
                height=dp(26),
                padding=(dp(8), 0),
                font_name='Roboto'
            )
            card_box.add_widget(category_label)
            
            arabic_text = d.get('arapca', '')
            if arabic_text:
                reversed_arabic = arabic_text[::-1]
                arabic_label = Label(
                    text=reversed_arabic,
                    halign='right',
                    valign='middle',
                    font_size=20,
                    color=GOLD,
                    size_hint=(1, None),
                    height=dp(34),
                    padding=(dp(8), 0),
                    font_name=ARABIC_FONT
                )
                card_box.add_widget(arabic_label)
            
            okunus_text = d.get('okunus', '')
            if okunus_text:
                display_text = okunus_text[:55] + ('...' if len(okunus_text) > 55 else '')
                okunus_label = Label(
                    text=display_text,
                    halign='left',
                    valign='middle',
                    font_size=12,
                    color=self._get_text_color(),
                    size_hint=(1, None),
                    height=dp(24),
                    padding=(dp(8), 0),
                    font_name='Roboto'
                )
                card_box.add_widget(okunus_label)
            
            kaynak = d.get('kaynak', '')
            if kaynak:
                kaynak_label = Label(
                    text=f"📎 {kaynak}",
                    halign='right',
                    valign='middle',
                    font_size=9,
                    color=self._get_muted_color(),
                    size_hint=(1, None),
                    height=dp(20),
                    padding=(dp(8), 0),
                    font_name='Roboto'
                )
                card_box.add_widget(kaynak_label)
            
            card_height = dp(60)
            if arabic_text:
                card_height += dp(34)
            if okunus_text:
                card_height += dp(24)
            if kaynak:
                card_height += dp(20)
            
            card = MDCard(
                card_box,
                size_hint=(1, None),
                height=card_height,
                md_bg_color=self._get_card_color(),
                elevation=1,
                radius=dp(10)
            )
            card.bind(on_release=lambda x, dd=d: self._show_dua_detail(dd))
            self.dua_list.add_widget(card)
    
    def _list_surah(self, *args):
        if not hasattr(self, 'dua_list'):
            return
        self.dua_list.clear_widgets()
        for s in self.dl.get_sureler():
            item = MDListItem(
                MDListItemLeadingIcon(icon="book-open-variant"),
                MDListItemHeadlineText(text=s.get('isim', 'Sure')),
                MDListItemSupportingText(text=f"{s.get('ayet_sayisi', '')} ayet")
            )
            
            for child in item.children:
                if isinstance(child, MDListItemHeadlineText):
                    child.font_name = ARABIC_FONT
            item.bind(on_release=lambda x, ss=s: self._show_surah_detail_old(ss))
            self.dua_list.add_widget(item)
    
    def _list_esma(self, *args):
        if not hasattr(self, 'dua_list'):
            return
        self.dua_list.clear_widgets()
        
        esmalar = self.dl.get_esmaul_husna()
        if not esmalar:
            self.dua_list.add_widget(Label(
                text="⭐ Henüz Esma bulunmuyor",
                halign='center',
                valign='middle',
                font_size=14,
                color=self._get_muted_color(),
                size_hint=(1, None),
                height=dp(50),
                font_name='Roboto'
            ))
            return
        
        for e in esmalar:
            card_box = MDBoxLayout(
                orientation='vertical',
                padding=dp(8),
                spacing=dp(4),
                adaptive_height=True,
                md_bg_color=self._get_card_color()
            )
            
            arabic_text = e.get('arapca', '')
            reversed_arabic = arabic_text[::-1] if arabic_text else ''
            
            title_box = MDBoxLayout(
                orientation='horizontal',
                size_hint=(1, None),
                height=dp(32),
                spacing=dp(1),
                padding=(dp(1), 0)
            )
            
            id_label = Label(
                text=f"{e.get('id', '')}.",
                halign='left',
                valign='middle',
                font_size=10,
                bold=True,
                color=GOLD,
                size_hint=(0.03, 1),
                font_name='Roboto'
            )
            title_box.add_widget(id_label)
            
            if reversed_arabic:
                arabic_label = Label(
                    text=reversed_arabic,
                    halign='left',
                    valign='middle',
                    font_size=24,
                    color=GOLD,
                    size_hint=(0.97, 1),
                    font_name=ARABIC_FONT
                )
                title_box.add_widget(arabic_label)
            else:
                spacer = Widget(size_hint=(0.97, 1))
                title_box.add_widget(spacer)
            
            card_box.add_widget(title_box)
            
            okunus_text = e.get('okunus', '')
            if okunus_text:
                okunus_label = Label(
                    text=f"🔊 {okunus_text}",
                    halign='left',
                    valign='middle',
                    font_size=12,
                    color=self._get_text_color(),
                    size_hint=(1, None),
                    height=dp(22),
                    padding=(dp(2), 0),
                    font_name='Roboto'
                )
                card_box.add_widget(okunus_label)
            
            anlam_text = e.get('anlam', '')
            if anlam_text:
                anlam_display = anlam_text[:60] + ('...' if len(anlam_text) > 60 else '')
                anlam_label = Label(
                    text=f"📝 {anlam_display}",
                    halign='left',
                    valign='middle',
                    font_size=11,
                    color=self._get_muted_color(),
                    size_hint=(1, None),
                    height=dp(22),
                    padding=(dp(2), 0),
                    font_name='Roboto'
                )
                card_box.add_widget(anlam_label)
            
            card_height = dp(60)
            if arabic_text:
                card_height += dp(32)
            if okunus_text:
                card_height += dp(22)
            if anlam_text:
                card_height += dp(22)
            
            card = MDCard(
                card_box,
                size_hint=(1, None),
                height=card_height,
                md_bg_color=self._get_card_color(),
                elevation=1,
                radius=dp(10)
            )
            card.bind(on_release=lambda x, ee=e: self._show_esma_detail(ee))
            self.dua_list.add_widget(card)
    
    def _show_dua_detail(self, dua):
        arabic_text = dua.get('arapca', '')
        reversed_arabic = arabic_text[::-1] if arabic_text else ""
        
        if reversed_arabic and len(reversed_arabic) > 40:
            reversed_arabic = f"[b]Son[/b]\n{reversed_arabic}\n[b]Baş[/b]"
        
        content_parts = []
        
        if reversed_arabic:
            content_parts.append(f"[b][size=20]{reversed_arabic}[/size][/b]\n")
        
        okunus = dua.get('okunus', '')
        if okunus:
            content_parts.append(f"📖 **OKUNUŞU:**\n{okunus}\n")
        
        anlam = dua.get('anlam', '')
        if anlam:
            content_parts.append(f"📝 **ANLAMI:**\n{anlam}\n")
        
        kaynak = dua.get('kaynak', '')
        if kaynak:
            content_parts.append(f"📚 **KAYNAK:**\n{kaynak}")
        
        content = "\n\n".join(content_parts)
        
        self._show_popup_rtl(
            dua.get('kategori', 'Dua'),
            content,
            is_rtl=True
        )
    
    def _show_surah_detail_old(self, sure):
        arabic_text = sure.get('arapca', '')
        if arabic_text:
            arabic_text = arabic_text[::-1]
        
        content = f"📝 ANLAMI:\n{sure.get('anlam', '')}\n\n📖 OKUNUŞU:\n{sure.get('okunus', '')}\n\n📊 AYET SAYISI:\n{sure.get('ayet_sayisi', 'Bilgi yok')}"
        if arabic_text:
            content = f"🕋 ARAPÇA:\n{arabic_text}\n\n{content}"
        self._show_popup_rtl(sure.get('isim', 'Sure'), content)
    
    def _show_esma_detail(self, esma):
        arabic_text = esma.get('arapca', '')
        if arabic_text:
            arabic_text = arabic_text[::-1]
        
        title = f"⭐ {arabic_text}" if arabic_text else esma.get('okunus', 'Esma')
        content = f"🔊 OKUNUŞU:\n{esma.get('okunus', '')}\n\n📝 ANLAMI:\n{esma.get('anlam', '')}"
        self._show_popup_rtl(title, content)
    
    def _show_popup(self, title, content, is_rtl=False):
        box = MDBoxLayout(
            orientation='vertical',
            padding=dp(12),
            spacing=dp(8),
            md_bg_color=[1, 1, 1, 1]
        )
        
        scr = ScrollView()
        
        use_arabic_font = is_rtl and ARABIC_FONT != 'Roboto'
        font_to_use = ARABIC_FONT if use_arabic_font else 'Roboto'
        
        lbl = Label(
            text=content,
            halign='right' if is_rtl else 'left',
            valign='top',
            padding=dp(12),
            text_size=(Window.width - dp(80), None),
            size_hint_y=None,
            font_size=14,
            color=[0, 0, 0, 1],
            font_name=font_to_use,
            markup=True
        )
        lbl.bind(texture_size=lambda i, v: setattr(i, 'height', v[1]))
        scr.add_widget(lbl)
        box.add_widget(scr)
        
        close_btn = MDButton(
            MDButtonText(text="✖ Kapat", font_size=12),
            md_bg_color=GOLD,
            style="elevated",
            size_hint=(1, None),
            height=dp(44)
        )
        box.add_widget(close_btn)
        
        pop = Popup(
            title=title,
            content=box,
            size_hint=(0.92, 0.75),
            auto_dismiss=False,
            background_color=[1, 1, 1, 1],
            title_color=[0, 0, 0, 1]
        )
        close_btn.bind(on_release=pop.dismiss)
        pop.open()
    
    # ============= TASBIH PAGE =============
    def show_tasbih(self):
        self.zikir_btn = MDButton(
            MDButtonText(text=self.tasbih.current_zikir, font_size=12),
            md_bg_color=GOLD,
            style="elevated",
            size_hint=(1, None),
            height=dp(44)
        )
        self.zikir_btn.bind(on_release=self._menu_zikir)
        self.box.add_widget(self.zikir_btn)
        
        self.tasbih_counter = Label(
            text="0",
            halign='center',
            valign='middle',
            font_size=52,
            bold=True,
            color=GOLD,
            size_hint=(1, None),
            height=dp(65)
        )
        self.box.add_widget(self.tasbih_counter)
        
        target = self.tasbih.get_target()
        self.target_label = Label(
            text=f"🎯 Hedef: {target}" if target else "🎯 Serbest Mod",
            halign='center',
            valign='middle',
            font_size=12,
            color=self._get_muted_color(),
            size_hint=(1, None),
            height=dp(24)
        )
        self.box.add_widget(self.target_label)
        
        self.progress_bar = ProgressBarWidget()
        self.progress_bar.value = 0
        self.box.add_widget(self.progress_bar)
        
        self.progress_label = Label(
            text="%0",
            halign='center',
            valign='middle',
            font_size=13,
            bold=True,
            color=GOLD,
            size_hint=(1, None),
            height=dp(26)
        )
        self.box.add_widget(self.progress_label)
        
        tap_btn = MDButton(
            MDButtonText(text="📿 TAP", font_size=28, bold=True),
            md_bg_color=GOLD_DARK,
            style="elevated",
            size_hint=(1, None),
            height=dp(75)
        )
        tap_btn.bind(on_release=self._tap_tasbih)
        self.box.add_widget(tap_btn)
        
        quick_row = MDBoxLayout(spacing=dp(8), size_hint=(1, None), height=dp(38))
        for count in [10, 33, 100]:
            btn = MDButton(
                MDButtonText(text=f"+{count}", font_size=12),
                md_bg_color=GOLD_LIGHT,
                style="elevated"
            )
            btn.bind(on_release=lambda x, c=count: self._tap_tasbih(c))
            quick_row.add_widget(btn)
        self.box.add_widget(quick_row)
        
        control_row = MDBoxLayout(spacing=dp(8), size_hint=(1, None), height=dp(38))
        reset_btn = MDButton(
            MDButtonText(text="🔄 Sıfırla", font_size=12),
            md_bg_color=[0.3, 0.3, 0.3, 1],
            style="elevated"
        )
        reset_btn.bind(on_release=self._reset_tasbih)
        control_row.add_widget(reset_btn)
        save_btn = MDButton(
            MDButtonText(text="💾 Kaydet", font_size=12),
            md_bg_color=[0.2, 0.6, 0.2, 1],
            style="elevated"
        )
        save_btn.bind(on_release=self._save_tasbih)
        control_row.add_widget(save_btn)
        self.box.add_widget(control_row)
        
        stats = self.tasbih.get_daily_stats()
        stats_card = MDCard(
            MDBoxLayout(
                Label(text=f"📊 Bugün: {stats['daily_total']}", halign='left', valign='middle', font_size=12, color=self._get_text_color(), size_hint=(1, None), height=dp(22), padding=(dp(10), 0)),
                Label(text=f"📈 Hafta: {stats['weekly_total']}", halign='left', valign='middle', font_size=12, color=self._get_text_color(), size_hint=(1, None), height=dp(22), padding=(dp(10), 0)),
                Label(text=f"📆 Ay: {stats['monthly_total']}", halign='left', valign='middle', font_size=12, color=self._get_text_color(), size_hint=(1, None), height=dp(22), padding=(dp(10), 0)),
                orientation='vertical', spacing=dp(2), padding=dp(8), adaptive_height=True
            ),
            size_hint=(1, None), height=dp(82),
            md_bg_color=self._get_card_color(), elevation=1, radius=dp(10)
        )
        self.box.add_widget(stats_card)
    
    def _tap_tasbih(self, count=1):
        try:
            c = int(count) if count else 1
        except:
            c = 1
        self.tasbih.increment(c)
        stats = self.tasbih.get_daily_stats()
        
        if hasattr(self, 'tasbih_counter'):
            self.tasbih_counter.text = str(stats['current_count'])
        if hasattr(self, 'progress_bar'):
            self.progress_bar.value = self.tasbih.get_progress()
        if hasattr(self, 'progress_label'):
            self.progress_label.text = f"%{int(self.tasbih.get_progress())}"
        
        target = self.tasbih.get_target()
        if target and stats['current_count'] >= target:
            self._toast("🎉 Tebrikler! Hedef tamamlandı!")
            self.notif.send_notification(
                title="🎉 Tesbih Hedefi Tamamlandı!",
                message=f"{self.tasbih.current_zikir} hedefine ulaştınız!",
                vibration=True
            )
    
    def _reset_tasbih(self, *args):
        self.tasbih.reset()
        if hasattr(self, 'tasbih_counter'):
            self.tasbih_counter.text = "0"
        if hasattr(self, 'progress_bar'):
            self.progress_bar.value = 0
        if hasattr(self, 'progress_label'):
            self.progress_label.text = "%0"
        self._toast("🔄 Sayaç sıfırlandı")
    
    def _save_tasbih(self, *args):
        stats = self.tasbih.get_daily_stats()
        self._toast(f"💾 Kaydedildi: {stats['daily_total']} bugün")
    
    def _menu_zikir(self, *args):
        items = [{'text': z, 'on_release': lambda x=z: self._pick_zikir(x)} for z in self.tasbih.zikir_options]
        menu = MDDropdownMenu(caller=self.zikir_btn, items=items, width_mult=4, max_height=dp(350))
        menu.open()
    
    def _pick_zikir(self, zikir):
        self.tasbih.set_zikir(zikir)
        for child in self.zikir_btn.children:
            if isinstance(child, MDButtonText):
                child.text = zikir
                break
        self._reset_tasbih()
        target = self.tasbih.get_target()
        if hasattr(self, 'target_label'):
            self.target_label.text = f"🎯 Hedef: {target}" if target else "🎯 Serbest Mod"
    
    # ============= QIBLA PAGE =============
    def show_qibla(self):
        self.qibla_angle = Label(
            text="--°",
            halign='center',
            valign='middle',
            font_size=52,
            bold=True,
            color=GOLD,
            size_hint=(1, None),
            height=dp(65)
        )
        self.box.add_widget(self.qibla_angle)
        
        self.qibla_direction = Label(
            text="🧭 Yön: --",
            halign='center',
            valign='middle',
            font_size=16,
            bold=True,
            color=self._get_text_color(),
            size_hint=(1, None),
            height=dp(30)
        )
        self.box.add_widget(self.qibla_direction)
        
        self.qibla_distance = Label(
            text="📏 Mesafe: -- km",
            halign='center',
            valign='middle',
            font_size=13,
            color=self._get_muted_color(),
            size_hint=(1, None),
            height=dp(26)
        )
        self.box.add_widget(self.qibla_distance)
        
        compass_card = MDCard(
            MDBoxLayout(
                Label(text="🧭", halign='center', valign='middle', font_size=80, size_hint=(1, None), height=dp(100)),
                orientation='vertical', padding=dp(16), adaptive_height=True
            ),
            size_hint=(1, None), height=dp(120),
            md_bg_color=self._get_card_color(), elevation=2, radius=dp(15)
        )
        self.box.add_widget(compass_card)
        
        if self.dist_name:
            self._update_qibla()
        else:
            self.box.add_widget(Label(
                text="⚠️ Vakitler'den şehir seçin",
                halign='center',
                valign='middle',
                font_size=12,
                color=self._get_muted_color(),
                size_hint=(1, None),
                height=dp(28)
            ))
    
    def _update_qibla(self):
        lat, lon = (self.user_location['lat'], self.user_location['lon']) if self.user_location else (41.0082, 28.9784)
        info = self.qibla.get_qibla_info(lat, lon)
        if info:
            if hasattr(self, 'qibla_angle'):
                self.qibla_angle.text = f"{info['angle']}°"
            if hasattr(self, 'qibla_direction'):
                self.qibla_direction.text = f"🧭 Yön: {info['direction']}"
            if hasattr(self, 'qibla_distance'):
                self.qibla_distance.text = f"📏 Mesafe: {info['distance_km']} km"
    
    # ============= LIBRARY PAGE =============
    def show_library(self):
        if not self.library_data or not self.library_data.get('kategoriler'):
            self.box.add_widget(Label(
                text="📚 Kütüphane verisi bulunamadı.",
                halign='center',
                valign='middle',
                font_size=14,
                color=self._get_muted_color(),
                size_hint=(1, None),
                height=dp(50)
            ))
            return
        
        row = MDBoxLayout(spacing=dp(6), size_hint=(1, None), height=dp(40))
        for kategori in self.library_data['kategoriler']:
            btn = MDButton(
                MDButtonText(text=f"{kategori['icon']} {kategori['ad'][:10]}", font_size=10),
                md_bg_color=GOLD,
                style="elevated"
            )
            btn.bind(on_release=lambda x, k=kategori: self._show_library_category(k))
            row.add_widget(btn)
        self.box.add_widget(row)
        
        self.library_list = MDList()
        self.box.add_widget(self.library_list)
        
        if self.library_data['kategoriler']:
            self._show_library_category(self.library_data['kategoriler'][0])
    
    def _show_library_category(self, kategori):
        if not hasattr(self, 'library_list'):
            return
        self.library_list.clear_widgets()
        
        for item in kategori.get('items', []):
            card = MDCard(
                MDBoxLayout(
                    Label(
                        text=f"📌 {item.get('baslik', '')}",
                        halign='left',
                        valign='middle',
                        font_size=14,
                        bold=True,
                        color=GOLD,
                        size_hint=(1, None),
                        height=dp(26),
                        padding=(dp(10), 0)
                    ),
                    Label(
                        text=item.get('metin', '')[:100] + ("..." if len(item.get('metin', '')) > 100 else ""),
                        halign='left',
                        valign='top',
                        font_size=12,
                        color=self._get_text_color(),
                        size_hint=(1, None),
                        height=dp(40),
                        padding=(dp(10), dp(4)),
                        text_size=(Window.width - dp(60), None)
                    ),
                    Label(
                        text=f"📎 {item.get('kaynak', 'Bilgi yok')}",
                        halign='right',
                        valign='middle',
                        font_size=10,
                        color=self._get_muted_color(),
                        size_hint=(1, None),
                        height=dp(20),
                        padding=(dp(10), 0)
                    ),
                    orientation='vertical',
                    spacing=dp(2),
                    padding=dp(8),
                    adaptive_height=True,
                    md_bg_color=self._get_card_color()
                ),
                size_hint=(1, None),
                height=dp(110),
                md_bg_color=self._get_card_color(),
                elevation=1,
                radius=dp(10)
            )
            card.bind(on_release=lambda x, it=item: self._show_library_detail(it))
            self.library_list.add_widget(card)
    
    def _show_library_detail(self, item):
        content = f"""📌 **{item.get('baslik', '')}**

    {item.get('metin', '')}

    📎 **Kaynak:** {item.get('kaynak', 'Bilgi yok')}"""
        
        arabic_chars = 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي'
        is_rtl = any(c in content for c in arabic_chars)
        
        self._show_popup("📚 Detay", content, is_rtl=is_rtl)
    
    # ============= AYARLAR =============
    def _show_settings_popup(self, *args):
        content = MDBoxLayout(orientation='vertical', spacing=dp(8), padding=dp(12))
        
        lang_btn = MDButton(
            MDButtonText(text=f"🌐 Dil: {self.lang.current_lang.upper()}", font_size=12),
            md_bg_color=GOLD,
            style="elevated",
            size_hint=(1, None),
            height=dp(40)
        )
        lang_btn.bind(on_release=self._menu_lang)
        content.add_widget(lang_btn)
        
        notif_status = "Açık" if self.notif.notification_enabled else "Kapalı"
        notif_btn = MDButton(
            MDButtonText(text=f"🔔 Namaz Bildirimi: {notif_status}", font_size=12),
            md_bg_color=GOLD_DARK,
            style="elevated",
            size_hint=(1, None),
            height=dp(40)
        )
        notif_btn.bind(on_release=self._toggle_notif)
        content.add_widget(notif_btn)
        
        vib_status = "Açık" if self.notif.vibration_enabled else "Kapalı"
        vib_btn = MDButton(
            MDButtonText(text=f"📳 Titreşim: {vib_status}", font_size=12),
            md_bg_color=GOLD_LIGHT,
            style="elevated",
            size_hint=(1, None),
            height=dp(40)
        )
        vib_btn.bind(on_release=self._toggle_vib)
        content.add_widget(vib_btn)
        
        theme_text = "🌙 Karanlık" if self.is_dark else "☀️ Aydınlık"
        theme_btn = MDButton(
            MDButtonText(text=f"🎨 Tema: {theme_text}", font_size=12),
            md_bg_color=GOLD,
            style="elevated",
            size_hint=(1, None),
            height=dp(40)
        )
        theme_btn.bind(on_release=self._toggle_theme)
        content.add_widget(theme_btn)
        
        about_btn = MDButton(
            MDButtonText(text="ℹ️ Hakkında", font_size=12),
            md_bg_color=[0.2, 0.2, 0.2, 1],
            style="elevated",
            size_hint=(1, None),
            height=dp(40)
        )
        about_btn.bind(on_release=self._show_about)
        content.add_widget(about_btn)
        
        close_btn = MDButton(
            MDButtonText(text="✖ Kapat", font_size=12),
            md_bg_color=[0.3, 0.3, 0.3, 1],
            style="elevated",
            size_hint=(1, None),
            height=dp(40)
        )
        content.add_widget(close_btn)
        
        pop = Popup(
            title="⚙️ Ayarlar",
            content=content,
            size_hint=(0.9, 0.7),
            auto_dismiss=False,
            background_color=POPUP_BG,
            title_color=POPUP_TEXT
        )
        close_btn.bind(on_release=pop.dismiss)
        pop.open()

    
    def _menu_lang(self, *args):
        items = [{'text': n, 'on_release': lambda x=c: self._pick_lang(x)} for c, n in self.lang.get_supported_languages().items()]
        menu = MDDropdownMenu(caller=self.settings_btn, items=items, width_mult=3)
        menu.open()
    
    def _pick_lang(self, code):
        self.lang.set_language(code)
        self._toast(f"Dil: {code.upper()}")
    
    def _toggle_notif(self, *args):
        self.notif.toggle_notifications(not self.notif.notification_enabled)
        status = "Açık" if self.notif.notification_enabled else "Kapalı"
        self._toast(f"Namaz Bildirimi: {status}")
    
    def _toggle_vib(self, *args):
        self.notif.toggle_vibration(not self.notif.vibration_enabled)
        status = "Açık" if self.notif.vibration_enabled else "Kapalı"
        self._toast(f"Titreşim: {status}")
    
    def _toggle_theme(self, *args):
        self.is_dark = not self.is_dark
        self._apply_theme()
        current = self.current_tab
        self.box.clear_widgets()
        self.go(current)
        self._toast(f"Tema: {'Karanlık' if self.is_dark else 'Aydınlık'}")
    
    def _show_about(self, *args):
        content = """🕌 **Mihrab - İslami Yaşam Rehberi**

    📌 Sürüm: 2.0 (Sade Versiyon)

    ✨ **Özellikler:**
    • Namaz Vakitleri (Online)
    • Otomatik Namaz Bildirimi
    • Kuran-ı Kerim (Meal)
    • Dijital Tesbih
    • Kıble Bulucu
    • Dualar & Sureler
    • İslami Kütüphane
    • Dini Gün Takvimi
    • Günün Ayeti & Hadisi
    • GPS Konum Bulma
    • Çoklu Dil Desteği
    • Kullanıcı Verisi TOPLANMAZ!

    📝 Açık Kaynak Kod"""
        self._show_popup("ℹ️ Hakkında", content, is_rtl=False)
    
    def _get_font_name(self, use_arabic=False):
        if use_arabic and ARABIC_FONT != 'Roboto':
            return ARABIC_FONT
        return 'Roboto'
    
    # ============= DİNİ GÜN TAKVİMİ =============
    def _check_special_days(self, *args):
        if not self.special_days:
            return
        
        today = datetime.now().strftime('%Y-%m-%d')
        year = datetime.now().year
        
        days = self.special_days.get(str(year), [])
        for day in days:
            if day.get('tarih') == today:
                self._send_special_day_notification(day)
    
    def _send_special_day_notification(self, day):
        name = day.get('isim', 'Özel Gün')
        tur = day.get('tur', '')
        
        emoji_map = {
            'kandil': '🌟',
            'bayram': '🎉',
            'ozel_gece': '🌙',
            'ozel_gun': '⭐',
            'ay_baslangici': '📅'
        }
        emoji = emoji_map.get(tur, '📌')
        
        self.notif.send_notification(
            title=f"{emoji} {name}",
            message=f"Bugün {name}. {day.get('aciklama', '')}",
            vibration=True
        )
        self._toast(f"{emoji} {name} bugün!")
    
    # ============= MENÜLER =============
    def _menu_city(self, *args):
        if not self.prayer.check_internet():
            self._toast("❌ İnternet bağlantısı gerekli!")
            return
        
        sehirler = self.dl.get_sehirler()
        
        if not sehirler:
            self._toast("❌ Şehir verisi yüklenemedi")
            return
        
        items = [{'text': s['ad'], 'on_release': lambda x=s: self._pick_city(x)} for s in sehirler]
        self._city_menu = MDDropdownMenu(
            caller=self.city_btn,
            items=items,
            width_mult=4,
            max_height=dp(400)
        )
        self._city_menu.open()

    def _pick_city(self, city):
        self.city_id = city['id']
        self.city_name = city['ad']
        
        if self._city_menu:
            self._city_menu.dismiss()
        
        if hasattr(self, 'location_popup') and self.location_popup:
            self.location_popup.dismiss()
        
        Clock.schedule_once(lambda dt: self._menu_district(), 0.2)

    def _menu_district(self):
        if not self.city_id:
            self._toast("❌ Önce şehir seçin")
            return
        
        ilceler = self.dl.get_ilceler_by_sehir(self.city_id)
        
        if not ilceler:
            self._toast("❌ İlçe verisi yüklenemedi")
            return
        
        items = [{'text': d['ad'], 'on_release': lambda x=d: self._pick_district(x)} for d in ilceler]
        self._dist_menu = MDDropdownMenu(
            caller=self.city_btn,
            items=items,
            width_mult=4,
            max_height=dp(400)
        )
        self._dist_menu.open()

    def _pick_district(self, district):
        self.dist_id = district['id']
        self.dist_name = district['ad']
        
        if self._dist_menu:
            self._dist_menu.dismiss()
        
        loc_text = f"{self.city_name[:15]} - {self.dist_name[:15]}"
        if hasattr(self, 'loc_label'):
            self.loc_label.text = loc_text
        
        self._toast(f"📍 {self.city_name} - {self.dist_name}")
        
        self._save_last_city()
        
        Clock.schedule_once(lambda dt: self._refresh_prayer(), 0.3)
    
    def _tick(self, dt):
        self._update_remaining_time()
    
    def on_start(self):
        if self.prayer.check_internet():
            self._toast("🌙 Mihrab'a Hoşgeldiniz!")
            self._load_last_city()
            if self.is_android:
                Clock.schedule_once(lambda dt: self._start_gps(), 2)
        else:
            self._toast("⚠️ İnternet bağlantısı yok!")
    
    def _load_last_city(self):
        try:
            cache_file = os.path.join(os.path.dirname(__file__), 'assets', 'data', 'last_city.json')
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('city_id') and data.get('district_id'):
                        self.city_id = data['city_id']
                        self.city_name = data['city_name']
                        self.dist_id = data['district_id']
                        self.dist_name = data['district_name']
                        if hasattr(self, 'loc_label'):
                            self.loc_label.text = f"{self.city_name[:15]} - {self.dist_name[:15]}"
                        Clock.schedule_once(lambda dt: self._refresh_prayer(), 1)
        except Exception as e:
            pass
    
    def _save_last_city(self):
        try:
            if not self.city_id or not self.dist_id:
                return
            cache_file = os.path.join(os.path.dirname(__file__), 'assets', 'data', 'last_city.json')
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'city_id': self.city_id,
                    'city_name': self.city_name,
                    'district_id': self.dist_id,
                    'district_name': self.dist_name,
                    'updated': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def on_stop(self):
        self._save_last_city()
        self.notif.cancel_all()

if __name__ == '__main__':
    MihrabApp().run()