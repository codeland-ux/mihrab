"""
Language Manager - Çoklu Dil Desteği
Mihrab - İslami Yaşam Rehberi
"""

from kivy.event import EventDispatcher
from kivy.properties import StringProperty, DictProperty
from kivy.logger import Logger


class LanguageManager(EventDispatcher):
    current_lang = StringProperty('tr')
    translations = DictProperty({})
    
    def __init__(self):
        super().__init__()
        from data_loader import data_loader
        self.data_loader = data_loader
        
        # ✅ Sadece ihtiyaç duyulan diller
        self.supported_languages = {
            'tr': 'Türkçe 🇹🇷',
            'en': 'English 🇬🇧',
            'ar': 'العربية 🇸🇦'
        }
        
        # ✅ Tüm çeviriler burada (JSON'a gerek yok!)
        self._fallback_translations = {
            'tr': {
                'app_name': 'Mihrab',
                'prayer_times': 'Namaz Vakitleri',
                'quran': 'Kuran-ı Kerim',
                'duas': 'Dualar & Sureler',
                'tasbih': 'Dijital Tesbih',
                'qibla': 'Kıble Bulucu',
                'library': 'İslami Kütüphane',
                'settings': 'Ayarlar',
                'language': 'Dil',
                'theme': 'Tema',
                'dark_mode': 'Karanlık Mod',
                'light_mode': 'Aydınlık Mod',
                'notifications': 'Bildirimler',
                'vibration': 'Titreşim',
                'about': 'Hakkında',
                'city': 'Şehir',
                'district': 'İlçe',
                'remaining_time': 'Kalan Süre',
                'hijri_date': 'Hicri Tarih',
                'daily_ayah': 'Günün Ayeti',
                'daily_hadith': 'Günün Hadisi',
                'daily_dua': 'Günün Duası',
            },
            'en': {
                'app_name': 'Mihrab',
                'prayer_times': 'Prayer Times',
                'quran': 'The Holy Quran',
                'duas': 'Duas & Surahs',
                'tasbih': 'Digital Tasbih',
                'qibla': 'Qibla Finder',
                'library': 'Islamic Library',
                'settings': 'Settings',
                'language': 'Language',
                'theme': 'Theme',
                'dark_mode': 'Dark Mode',
                'light_mode': 'Light Mode',
                'notifications': 'Notifications',
                'vibration': 'Vibration',
                'about': 'About',
                'city': 'City',
                'district': 'District',
                'remaining_time': 'Remaining Time',
                'hijri_date': 'Hijri Date',
                'daily_ayah': 'Daily Verse',
                'daily_hadith': 'Daily Hadith',
                'daily_dua': 'Daily Dua',
            },
            'ar': {
                'app_name': 'محراب',
                'prayer_times': 'أوقات الصلاة',
                'quran': 'القرآن الكريم',
                'duas': 'الأدعية والسور',
                'tasbih': 'تسبيح رقمي',
                'qibla': 'القبلة',
                'library': 'المكتبة الإسلامية',
                'settings': 'الإعدادات',
                'language': 'اللغة',
                'theme': 'المظهر',
                'dark_mode': 'الوضع المظلم',
                'light_mode': 'الوضع الفاتح',
                'notifications': 'الإشعارات',
                'vibration': 'الاهتزاز',
                'about': 'عن التطبيق',
                'city': 'المدينة',
                'district': 'المنطقة',
                'remaining_time': 'الوقت المتبقي',
                'hijri_date': 'التاريخ الهجري',
                'daily_ayah': 'آية اليوم',
                'daily_hadith': 'حديث اليوم',
                'daily_dua': 'دعاء اليوم',
            }
        }
        
        # ✅ Dili yükle (direkt fallback'ten)
        self.set_language('tr')
    
    def set_language(self, lang):
        """Dil değiştir"""
        if lang in self.supported_languages:
            self.current_lang = lang
            
            # ✅ Doğrudan fallback'ten al (JSON'a gerek yok!)
            fallback = self._fallback_translations.get(lang, {})
            if fallback:
                self.translations = fallback
                Logger.info(f"LanguageManager: Dil değiştirildi -> {lang}")
                return True
            
            return False
        
        Logger.warning(f"LanguageManager: Desteklenmeyen dil: {lang}")
        return False
    
    def get_text(self, key, default=None):
        """Çeviriyi al"""
        if key in self.translations:
            return self.translations.get(key, default or key)
        
        fallback = self._fallback_translations.get(self.current_lang, {})
        if key in fallback:
            return fallback.get(key, default or key)
        
        return default or key
    
    def get_supported_languages(self):
        """Desteklenen dilleri döndür"""
        return self.supported_languages
    
    def get_language_name(self, lang_code):
        """Dil adını döndür"""
        return self.supported_languages.get(lang_code, lang_code)
    
    def get_language_flag(self, lang_code):
        """Dil bayrağı emojisini döndür"""
        flags = {
            'tr': '🇹🇷',
            'en': '🇬🇧',
            'ar': '🇸🇦'
        }
        return flags.get(lang_code, '🌐')


# Singleton
language_manager = LanguageManager()