"""
Prayer Manager - Namaz Vakitleri Yöneticisi
Mihrab - İslami Yaşam Rehberi
"""

import json
import os
import requests
import re
import time
from datetime import datetime
from kivy.logger import Logger


class PrayerManager:
    def __init__(self):
        self.prayer_times = {}
        self.cached_times = {}
        self.current_location = None
        self.offline_mode = False
        self.last_update = None
        self.is_connected = False
        self._last_request_time = 0
        self._min_request_interval = 2  # saniye
        self.cache_file = os.path.join(
            os.path.dirname(__file__), 'assets', 'data', 'prayer_cache.json'
        )
        self.load_cache()
        self.check_internet()
    
    def check_internet(self):
        try:
            requests.get('https://www.google.com', timeout=3)
            self.is_connected = True
            return True
        except:
            self.is_connected = False
            return False
    
    def get_prayer_times(self, city_name):
        """Al-Adhan API ile şehir adından namaz vakitleri"""
        Logger.info(f"PrayerManager: Vakit isteniyor - {city_name}")
        
        if not self.check_internet():
            Logger.warning("PrayerManager: İnternet bağlantısı yok!")
            return None
        
        # Cache kontrolü
        cache_key = f"prayer_{city_name}_{datetime.now().strftime('%Y-%m-%d')}"
        if cache_key in self.cached_times:
            Logger.info("PrayerManager: Önbellekten döndürülüyor")
            return self.cached_times[cache_key]
        
        # API'den al
        result = self._get_from_aladhan(city_name)
        if result:
            self.cached_times[cache_key] = result
            self.prayer_times = result
            self.last_update = datetime.now()
            self._cache_times(result)
            return result
        
        Logger.error("PrayerManager: Vakit alınamadı!")
        return None
    
    def get_prayer_times_by_coordinates(self, lat, lon, method=13):
        """
        ✅ Al-Adhan API ile KOORDİNATLARDAN namaz vakitleri
        
        Args:
            lat: Enlem (float)
            lon: Boylam (float)
            method: Hesaplama yöntemi (13 = Diyanet)
        
        Returns:
            dict: Namaz vakitleri sözlüğü
        """
        Logger.info(f"PrayerManager: Koordinatlardan vakit isteniyor - {lat}, {lon}")
        
        if not self.check_internet():
            Logger.warning("PrayerManager: İnternet bağlantısı yok!")
            return None
        
        # Cache kontrolü
        cache_key = f"prayer_{lat}_{lon}_{datetime.now().strftime('%Y-%m-%d')}"
        if cache_key in self.cached_times:
            Logger.info("PrayerManager: Önbellekten döndürülüyor (koordinat)")
            return self.cached_times[cache_key]
        
        # API'den al
        result = self._get_from_aladhan_by_coordinates(lat, lon, method)
        if result:
            self.cached_times[cache_key] = result
            self.prayer_times = result
            self.last_update = datetime.now()
            self._cache_times(result)
            return result
        
        Logger.error("PrayerManager: Koordinat vakit alınamadı!")
        return None
    
    def _get_from_aladhan(self, city_name, country='Turkey'):
        """Al-Adhan API'den şehir adı ile namaz vakitlerini al"""
        import urllib.parse
        
        # Rate limiting
        now = time.time()
        if hasattr(self, '_last_request_time') and self._last_request_time:
            elapsed = now - self._last_request_time
            min_interval = 2
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        
        try:
            city_encoded = urllib.parse.quote(city_name)
            country_encoded = urllib.parse.quote(country)
            
            # Farklı API metodlarını dene (fallback)
            methods = [
                f"https://api.aladhan.com/v1/timingsByCity?city={city_encoded}&country={country_encoded}&method=13",
                f"https://api.aladhan.com/v1/timingsByCity?city={city_encoded}&country={country_encoded}&method=2",
                f"https://api.aladhan.com/v1/timingsByCity?city={city_encoded}&country=Turkey&method=13"
            ]
            
            for i, url in enumerate(methods):
                try:
                    Logger.debug(f"PrayerManager: Al-Adhan deneme {i+1}")
                    response = requests.get(url, timeout=10, headers={
                        'User-Agent': 'Mihrab/2.0',
                        'Accept': 'application/json'
                    })
                    
                    if response.status_code == 200:
                        data = response.json()
                        timings = data.get('data', {}).get('timings', {})
                        
                        prayer_map = {
                            'Fajr': 'İmsak',
                            'Sunrise': 'Güneş',
                            'Dhuhr': 'Öğle',
                            'Asr': 'İkindi',
                            'Maghrib': 'Akşam',
                            'Isha': 'Yatsı'
                        }
                        
                        result = {}
                        for eng, tr in prayer_map.items():
                            if eng in timings:
                                raw_time = timings[eng]
                                clean_time = re.sub(r'\(.*?\)', '', raw_time)
                                clean_time = re.sub(r'[^0-9:]', '', clean_time)
                                
                                if ':' in clean_time:
                                    parts = clean_time.split(':')
                                    if len(parts) >= 2:
                                        hour = parts[0].zfill(2)
                                        minute = parts[1][:2].ljust(2, '0')
                                        result[tr] = f"{hour}:{minute}"
                        
                        if len(result) == 6:
                            self._last_request_time = time.time()
                            Logger.info(f"PrayerManager: ✓ Vakitler alındı: {result}")
                            return result
                        elif len(result) >= 4:
                            self._last_request_time = time.time()
                            Logger.warning(f"PrayerManager: Kısmi vakit ({len(result)}/6)")
                            return result
                            
                except requests.exceptions.Timeout:
                    Logger.warning(f"PrayerManager: Timeout (deneme {i+1})")
                    continue
                except requests.exceptions.ConnectionError:
                    Logger.warning(f"PrayerManager: Bağlantı hatası (deneme {i+1})")
                    continue
                except Exception as e:
                    Logger.warning(f"PrayerManager: Hata (deneme {i+1}): {e}")
                    continue
            
            return None
            
        except Exception as e:
            Logger.error(f"PrayerManager: Genel API hatası - {e}")
            return None
    
    def _get_from_aladhan_by_coordinates(self, lat, lon, method=13):
        """
        ✅ Al-Adhan API'den KOORDİNATLAR ile namaz vakitlerini al
        
        Args:
            lat: Enlem (float)
            lon: Boylam (float)
            method: Hesaplama yöntemi (13 = Diyanet)
        
        Returns:
            dict: Namaz vakitleri
        """
        import urllib.parse
        
        # Rate limiting
        now = time.time()
        if hasattr(self, '_last_request_time') and self._last_request_time:
            elapsed = now - self._last_request_time
            min_interval = 2
            if elapsed < min_interval:
                time.sleep(min_interval - elapsed)
        
        try:
            # ✅ Koordinatları formatla
            lat_str = str(lat)[:10]
            lon_str = str(lon)[:10]
            
            # ✅ API URL'leri (farklı yöntemler)
            urls = [
                f"https://api.aladhan.com/v1/timings?latitude={lat_str}&longitude={lon_str}&method={method}",
                f"https://api.aladhan.com/v1/timings?lat={lat_str}&long={lon_str}&method={method}",
                f"https://api.aladhan.com/v1/timings?latitude={lat_str}&longitude={lon_str}&method=2",
            ]
            
            for i, url in enumerate(urls):
                try:
                    Logger.debug(f"PrayerManager: Koordinat API deneme {i+1}")
                    response = requests.get(url, timeout=10, headers={
                        'User-Agent': 'Mihrab/2.0',
                        'Accept': 'application/json'
                    })
                    
                    if response.status_code == 200:
                        data = response.json()
                        timings = data.get('data', {}).get('timings', {})
                        
                        prayer_map = {
                            'Fajr': 'İmsak',
                            'Sunrise': 'Güneş',
                            'Dhuhr': 'Öğle',
                            'Asr': 'İkindi',
                            'Maghrib': 'Akşam',
                            'Isha': 'Yatsı'
                        }
                        
                        result = {}
                        for eng, tr in prayer_map.items():
                            if eng in timings:
                                raw_time = timings[eng]
                                clean_time = re.sub(r'\(.*?\)', '', raw_time)
                                clean_time = re.sub(r'[^0-9:]', '', clean_time)
                                
                                if ':' in clean_time:
                                    parts = clean_time.split(':')
                                    if len(parts) >= 2:
                                        hour = parts[0].zfill(2)
                                        minute = parts[1][:2].ljust(2, '0')
                                        result[tr] = f"{hour}:{minute}"
                        
                        if len(result) == 6:
                            self._last_request_time = time.time()
                            Logger.info(f"PrayerManager: ✓ Koordinat vakitler alındı: {result}")
                            return result
                        elif len(result) >= 4:
                            self._last_request_time = time.time()
                            Logger.warning(f"PrayerManager: Kısmi koordinat vakit ({len(result)}/6)")
                            return result
                            
                except requests.exceptions.Timeout:
                    Logger.warning(f"PrayerManager: Koordinat API timeout (deneme {i+1})")
                    continue
                except requests.exceptions.ConnectionError:
                    Logger.warning(f"PrayerManager: Koordinat API bağlantı hatası (deneme {i+1})")
                    continue
                except Exception as e:
                    Logger.warning(f"PrayerManager: Koordinat API hata (deneme {i+1}): {e}")
                    continue
            
            return None
            
        except Exception as e:
            Logger.error(f"PrayerManager: Koordinat API genel hata - {e}")
            return None
    
    def _cache_times(self, times):
        try:
            cache_data = {
                'date': datetime.now().strftime('%Y-%m-%d'),
                'times': times
            }
            os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            self.cached_times = times
            self.last_update = datetime.now()
            Logger.info("PrayerManager: Vakitler önbelleğe alındı")
        except Exception as e:
            Logger.error(f"PrayerManager: Cache hatası - {e}")
    
    def load_cache(self):
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return
                    cache_data = json.loads(content)
                    if cache_data.get('date') == datetime.now().strftime('%Y-%m-%d'):
                        self.cached_times = cache_data.get('times', {})
                        Logger.info("PrayerManager: Önbellekten yüklendi")
        except Exception as e:
            Logger.error(f"PrayerManager: Cache yükleme hatası - {e}")
    
    def get_remaining_time(self):
        if not self.prayer_times:
            return None
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        prayer_list = ['İmsak', 'Güneş', 'Öğle', 'İkindi', 'Akşam', 'Yatsı']
        
        for prayer in prayer_list:
            try:
                time_str = self.prayer_times.get(prayer, '00:00')
                h, m = map(int, time_str.split(':'))
                prayer_minutes = h * 60 + m
                if prayer_minutes > current_minutes:
                    remaining = prayer_minutes - current_minutes
                    return {
                        'name': prayer,
                        'time': f"{remaining // 60:02d}:{remaining % 60:02d}",
                        'total_minutes': remaining
                    }
            except:
                continue
        return None
    
    def set_location(self, lat, lon):
        self.current_location = {'lat': lat, 'lon': lon}


prayer_manager = PrayerManager()