"""
Data Loader - Mihrab
Sadece temel veri yükleme işlemleri
"""

import json
import os
import requests
from datetime import datetime
from kivy.logger import Logger
from functools import lru_cache

class DataLoader:
    def __init__(self):
        self.base_path = os.path.join(os.path.dirname(__file__), 'assets', 'data')
        self._cache = {}
        self.MAX_CACHE_SIZE = 50
        self._ensure_data_files()
        
        # API URL'leri
        self.QURAN_API = "https://api.quran.com/api/v4"
        
        # Cache'ler
        self._sehirler_cache = None
        self._ilceler_cache = {}
        self._surah_cache = {}
        self._chapters_cache = None
    
    def _ensure_data_files(self):
        """Veri klasörlerini oluştur"""
        os.makedirs(self.base_path, exist_ok=True)
        os.makedirs(os.path.join(self.base_path, 'temp'), exist_ok=True)
    
    # ============= KURAN API (Quran.com) =============
    def get_quran(self):
        """Tüm sureleri getir (Türkçe isimlerle)"""
        if self._chapters_cache:
            return self._chapters_cache
        
        # ✅ Türkçe sure isimleri (manuel)
        TURKCE_SURE_ISIMLERI = {
            1: "Fatiha", 2: "Bakara", 3: "Âl-i İmrân", 4: "Nisâ", 5: "Mâide",
            6: "En'âm", 7: "A'râf", 8: "Enfâl", 9: "Tevbe", 10: "Yûnus",
            11: "Hûd", 12: "Yûsuf", 13: "Ra'd", 14: "İbrâhîm", 15: "Hicr",
            16: "Nahl", 17: "İsrâ", 18: "Kehf", 19: "Meryem", 20: "Tâhâ",
            21: "Enbiyâ", 22: "Hac", 23: "Mü'minûn", 24: "Nûr", 25: "Furkân",
            26: "Şuarâ", 27: "Neml", 28: "Kasas", 29: "Ankebût", 30: "Rûm",
            31: "Lokmân", 32: "Secde", 33: "Ahzâb", 34: "Sebe", 35: "Fâtır",
            36: "Yâsîn", 37: "Sâffât", 38: "Sâd", 39: "Zümer", 40: "Mü'min",
            41: "Fussilet", 42: "Şûrâ", 43: "Zuhruf", 44: "Duhân", 45: "Câsiye",
            46: "Ahkâf", 47: "Muhammed", 48: "Fetih", 49: "Hucurât", 50: "Kâf",
            51: "Zâriyât", 52: "Tûr", 53: "Necm", 54: "Kamer", 55: "Rahmân",
            56: "Vâkıa", 57: "Hadîd", 58: "Mücâdele", 59: "Haşr", 60: "Mümtehine",
            61: "Saff", 62: "Cum'a", 63: "Münâfikûn", 64: "Teğâbun", 65: "Talâk",
            66: "Tahrîm", 67: "Mülk", 68: "Kalem", 69: "Hâkka", 70: "Meâric",
            71: "Nûh", 72: "Cin", 73: "Müzzemmil", 74: "Müddessir", 75: "Kıyâmet",
            76: "İnsân", 77: "Mürselât", 78: "Nebe", 79: "Nâziât", 80: "Abese",
            81: "Tekvîr", 82: "İnfitâr", 83: "Mutaffifîn", 84: "İnşikâk", 85: "Burûc",
            86: "Târık", 87: "A'lâ", 88: "Gâşiye", 89: "Fecr", 90: "Beled",
            91: "Şems", 92: "Leyl", 93: "Duhâ", 94: "İnşirâh", 95: "Tîn",
            96: "Alak", 97: "Kadr", 98: "Beyyine", 99: "Zilzâl", 100: "Âdiyât",
            101: "Kâria", 102: "Tekâsür", 103: "Asr", 104: "Hümeze", 105: "Fîl",
            106: "Kureyş", 107: "Mâûn", 108: "Kevser", 109: "Kâfirûn", 110: "Nasr",
            111: "Tebbet", 112: "İhlâs", 113: "Felak", 114: "Nâs"
        }
        
        try:
            url = f"{self.QURAN_API}/chapters?language=tr"
            response = requests.get(url, timeout=10, headers={'Accept': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                chapters = data.get('chapters', [])
                
                formatted = []
                for ch in chapters:
                    sura_id = ch.get('id')
                    # ✅ Manuel Türkçe isim kullan
                    turkce_isim = TURKCE_SURE_ISIMLERI.get(sura_id, ch.get('name_complex', ch.get('name_simple', '')))
                    
                    formatted.append({
                        'id': sura_id,
                        'name': ch.get('name_simple', ''),
                        'arabic_name': ch.get('name_arabic', ''),
                        'translation': turkce_isim,  # ✅ Türkçe isim
                        'english_name': ch.get('name_simple', ''),
                        'revelation_place': ch.get('revelation_place', ''),
                        'revelation_order': ch.get('revelation_order', 0),
                        'verses_count': ch.get('verses_count', 0),
                        'pages': ch.get('pages', [])
                    })
                
                self._chapters_cache = formatted
                Logger.info(f"DataLoader: {len(formatted)} sure yüklendi (Türkçe isimlerle)")
                return formatted
            else:
                Logger.error(f"DataLoader: API hatası - {response.status_code}")
                return self._get_default_quran()
        except Exception as e:
            Logger.error(f"DataLoader: API hatası - {e}")
            return self._get_default_quran()
    
    def get_surah_detail(self, surah_id):
        """Sure detaylarını getir - FALLBACK ile"""
        try:
            if surah_id in self._surah_cache:
                return self._surah_cache[surah_id]
            
            # ALTERNATİF API: Al-Quran Cloud
            url = f"https://api.alquran.cloud/v1/surah/{surah_id}/editions/quran-uthmani,tr.transliteration,tr.diyanet"
            response = requests.get(url, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    editions = data.get('data', [])
                    
                    arapca_verses = []
                    translit_verses = []
                    meal_verses = []
                    
                    for edition in editions:
                        edition_id = edition.get('edition', {}).get('identifier', '')
                        if edition_id == 'quran-uthmani':
                            arapca_verses = edition.get('ayahs', [])
                        elif edition_id == 'tr.transliteration':
                            translit_verses = edition.get('ayahs', [])
                        elif edition_id == 'tr.diyanet':
                            meal_verses = edition.get('ayahs', [])
                    
                    if arapca_verses:
                        surah_info = arapca_verses[0].get('surah', {})
                        surah_name = surah_info.get('name', '')
                        surah_english_name = surah_info.get('englishName', '')
                        revelation_type = surah_info.get('revelationType', '')
                        
                        formatted_verses = []
                        for i, verse in enumerate(arapca_verses):
                            verse_number = verse.get('numberInSurah', 0)
                            arapca = verse.get('text', '')
                            
                            transliteration = ""
                            if i < len(translit_verses):
                                transliteration = translit_verses[i].get('text', '')
                            
                            meal = ""
                            if i < len(meal_verses):
                                meal = meal_verses[i].get('text', '')
                            
                            formatted_verses.append({
                                'id': verse_number,
                                'text': arapca,
                                'transliteration': transliteration,
                                'translation': meal,
                            })
                        
                        result = {
                            'id': surah_id,
                            'name': surah_english_name,
                            'arabic_name': surah_name,
                            'translation': surah_english_name,
                            'type': revelation_type,
                            'total_verses': len(formatted_verses),
                            'verses': formatted_verses,
                            'surah_meaning': surah_english_name,
                        }
                        
                        self._surah_cache[surah_id] = result
                        Logger.info(f"DataLoader: Sure {surah_id} yüklendi ({len(formatted_verses)} ayet)")
                        return result
            
            # API çalışmazsa FALLBACK kullan
            Logger.warning(f"DataLoader: API çalışmadı, fallback kullanılıyor - Sure {surah_id}")
            return self._get_fallback_surah(surah_id)
            
        except Exception as e:
            Logger.error(f"DataLoader: Sure detay hatası - {e}")
            return self._get_fallback_surah(surah_id)
    
    def _get_fallback_surah(self, surah_id):
        """API çalışmazsa yedek sure verisi"""
        sureler = self.load_json('surahs.json')
        if isinstance(sureler, dict):
            sureler = sureler.get('sureler', [])
        
        for sure in sureler:
            if sure.get('id') == surah_id:
                verses = []
                ayet_sayisi = sure.get('ayet_sayisi', 7)
                for i in range(1, ayet_sayisi + 1):
                    verses.append({
                        'id': i,
                        'text': f"[Sure {surah_id} - Ayet {i}]",
                        'transliteration': '',
                        'translation': f"Sure {surah_id} ayet {i}"
                    })
                
                return {
                    'id': surah_id,
                    'name': sure.get('isim', f'Sure {surah_id}'),
                    'arabic_name': sure.get('arapca', ''),
                    'translation': sure.get('isim', f'Sure {surah_id}'),
                    'type': 'Mekki',
                    'total_verses': ayet_sayisi,
                    'verses': verses,
                    'surah_meaning': sure.get('anlam', ''),
                }
        
        return {
            'id': surah_id,
            'name': f'Sure {surah_id}',
            'arabic_name': '',
            'translation': f'Sure {surah_id}',
            'type': 'Mekki',
            'total_verses': 0,
            'verses': [],
            'surah_meaning': '',
        }
    
    # ============= ŞEHİRLER VE İLÇELER =============
    @lru_cache(maxsize=256)
    def get_sehirler(self):
        if self._sehirler_cache:
            return self._sehirler_cache
        
        ilceler = self.load_json('ilceler.json')
        if not ilceler:
            return self._get_default_cities()
        
        sehirler_dict = {}
        for ilce in ilceler:
            sehir_id = ilce.get('sehir_id')
            sehir_adi = ilce.get('sehir_adi')
            if sehir_id and sehir_id not in sehirler_dict:
                sehirler_dict[sehir_id] = {'id': sehir_id, 'ad': sehir_adi}
        
        sehirler = sorted(sehirler_dict.values(), key=lambda x: int(x['id']))
        self._sehirler_cache = sehirler
        return sehirler
    
    @lru_cache(maxsize=1024)
    def get_ilceler_by_sehir(self, sehir_id):
        if sehir_id in self._ilceler_cache:
            return self._ilceler_cache[sehir_id]
        
        ilceler = self.load_json('ilceler.json')
        if not ilceler:
            return []
        
        filtrelenmis = [
            {'id': ilce.get('ilce_id'), 'ad': ilce.get('ilce_adi')}
            for ilce in ilceler
            if ilce.get('sehir_id') == str(sehir_id)
        ]
        filtrelenmis.sort(key=lambda x: x['ad'])
        self._ilceler_cache[sehir_id] = filtrelenmis
        return filtrelenmis
    
    def _get_default_cities(self):
        return [
            {'id': '34', 'ad': 'İstanbul'},
            {'id': '6', 'ad': 'Ankara'},
            {'id': '35', 'ad': 'İzmir'},
        ]

    
    # ============= JSON YÜKLEME =============
    def load_json(self, filename):
        """
        JSON dosyasını yükle - Cache ve hata yönetimi ile
        
        Args:
            filename: JSON dosya adı
        
        Returns:
            dict/list: Yüklenen veri veya boş veri
        """
        try:
            filepath = os.path.join(self.base_path, filename)
            
            # Cache kontrolü
            if filename in self._cache:
                Logger.debug(f"DataLoader: {filename} cache'ten yüklendi")
                return self._cache[filename]
            
            # Dosya kontrolü
            if not os.path.exists(filepath):
                Logger.warning(f"DataLoader: {filename} bulunamadı, varsayılan kullanılıyor")
                default_data = self._get_default_data(filename)
                self._cache[filename] = default_data
                return default_data
            
            # Dosyayı oku
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    Logger.warning(f"DataLoader: {filename} boş, varsayılan kullanılıyor")
                    default_data = self._get_default_data(filename)
                    self._cache[filename] = default_data
                    return default_data
                
                data = json.loads(content)
                
                # Cache'e ekle
                if len(self._cache) >= self.MAX_CACHE_SIZE:
                    old_key = next(iter(self._cache))
                    self._cache.pop(old_key)
                    Logger.debug(f"DataLoader: Cache limiti aşıldı, {old_key} çıkarıldı")
                
                self._cache[filename] = data
                Logger.debug(f"DataLoader: {filename} yüklendi ({len(str(data))} bayt)")
                return data
                
        except json.JSONDecodeError as e:
            Logger.error(f"DataLoader: {filename} JSON hatası - {e}")
            default_data = self._get_default_data(filename)
            self._cache[filename] = default_data
            return default_data
        except Exception as e:
            Logger.error(f"DataLoader: {filename} yüklenirken hata - {e}")
            default_data = self._get_default_data(filename)
            self._cache[filename] = default_data
            return default_data

    def _get_default_data(self, filename):
        """Varsayılan veri döndür"""
        defaults = {
            'ilceler.json': [],
            'dualar.json': {'dualar': []},
            'surahs.json': {'sureler': []},
            'esmaul_husna.json': {'esmaul_husna': []},
            'library.json': {'kategoriler': []},
            'daily_content.json': {'ayetler': [], 'hadisler': []},
            'special_days.json': {},
        }
        
        default = defaults.get(filename, {})
        Logger.warning(f"DataLoader: {filename} için varsayılan veri kullanılıyor")
        
        if filename not in self._cache:
            self._cache[filename] = default
        return default
    
    # ============= VERİ GETİRME METODLARI =============
    def get_dualar(self, kategori=None):
        """Duaları getir (Statik)"""
        data = self.load_json('dualar.json')
        if isinstance(data, dict):
            dualar = data.get('dualar', [])
        else:
            dualar = data
        if kategori:
            dualar = [d for d in dualar if d.get('kategori') == kategori]
        return dualar
    
    def get_sureler(self, kategori=None):
        """Sureleri getir (Statik)"""
        data = self.load_json('surahs.json')
        sureler = data.get('sureler', []) if isinstance(data, dict) else []
        if kategori:
            sureler = [s for s in sureler if s.get('kategori') == kategori]
        return sureler
    
    def get_esmaul_husna(self):
        """Esmaül Hüsna'yı getir (Statik)"""
        data = self.load_json('esmaul_husna.json')
        return data.get('esmaul_husna', []) if isinstance(data, dict) else []
    
    def get_translations(self, lang='tr'):
        """Çevirileri getir (Statik)"""
        data = self.load_json('translations.json')
        if isinstance(data, dict):
            return data.get(lang, data.get('tr', {}))
        return {}
    
    def reload_data(self):
        """Cache'i temizle"""
        self._cache.clear()
        self._sehirler_cache = None
        self._ilceler_cache = {}
        self._surah_cache = {}
        self._chapters_cache = None
        self.get_sehirler.cache_clear()
        self.get_ilceler_by_sehir.cache_clear()
        Logger.info("DataLoader: Cache temizlendi")


# Singleton
data_loader = DataLoader()