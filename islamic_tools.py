"""
İslami Araçlar - Hicri Takvim, Kıble, Tesbih
Mihrab - İslami Yaşam Rehberi
"""

from math import cos, sin, tan, atan2, radians, degrees, sqrt, floor
from datetime import datetime, timedelta
from kivy.logger import Logger


class HijriCalendar:
    """Hicri Takvim - DÜZELTİLMİŞ VERSİYON"""
    
    HIJRI_MONTHS = [
        'Muharrem', 'Safer', 'Rebiülevvel', 'Rebiülahir',
        'Cemaziyelevvel', 'Cemaziyelahir', 'Recep', 'Şaban',
        'Ramazan', 'Şevval', 'Zilkade', 'Zilhicce'
    ]
    
    # ✅ Düzeltilmiş gün sayıları
    MONTH_DAYS = [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]  # Standart
    MONTH_DAYS_LEAP = [30, 30, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]  # Artık yıl
    
    SPECIAL_DAYS = {
        1: {10: "Aşure Günü"},
        7: {27: "Miraç Kandili"},
        8: {15: "Berat Kandili"},
        9: {1: "Ramazan Başlangıcı", 27: "Kadir Gecesi"},
        10: {1: "Ramazan Bayramı"},
        12: {10: "Kurban Bayramı"}
    }
    
    def gregorian_to_hijri(self, date=None):
        """
        Miladi tarihi Hicri'ye çevir - DÜZELTİLMİŞ ALGORİTMA
        
        Args:
            date: datetime objesi (None ise bugün)
        
        Returns:
            dict: Hicri tarih bilgileri
        """
        if date is None:
            date = datetime.now()
        
        try:
            # ✅ YENİ ALGORİTMA - Daha doğru
            year = date.year
            month = date.month
            day = date.day
            
            # 1. Gün farkını hesapla (Muharrem 1, 622)
            # Referans: 622-07-16 Miladi = 1 Muharrem 1
            base_date = datetime(622, 7, 16)
            delta = date - base_date
            total_days = delta.days
            
            # 2. Hicri yıl hesapla (354.367 gün / yıl)
            hijri_year = total_days / 354.367 + 1
            
            # 3. Hicri ay ve gün hesapla
            year_int = int(hijri_year)
            remaining_days = int((hijri_year - year_int) * 354.367)
            
            # 4. Ay hesapla
            month_int = 1
            for i, days_in_month in enumerate(self.MONTH_DAYS):
                if remaining_days > days_in_month:
                    remaining_days -= days_in_month
                    month_int += 1
                else:
                    break
            
            # 5. Gün hesapla
            day_int = remaining_days + 1
            
            # ✅ Hata kontrolü ve düzeltme
            if month_int > 12:
                month_int = 12
                day_int = 30
            if month_int < 1:
                month_int = 1
                day_int = 1
            if day_int > 30:
                day_int = 30
            if day_int < 1:
                day_int = 1
            if year_int < 1:
                year_int = 1446
            
            # ✅ Özel gün kontrolü (Aşure, Kandil vb.)
            special_day = self.SPECIAL_DAYS.get(month_int, {}).get(day_int, None)
            
            result = {
                'year': year_int,
                'month': month_int,
                'month_name': self.HIJRI_MONTHS[month_int - 1] if month_int <= 12 else self.HIJRI_MONTHS[11],
                'day': day_int,
                'date_str': f"{day_int} {self.HIJRI_MONTHS[month_int - 1] if month_int <= 12 else self.HIJRI_MONTHS[11]} {year_int}",
                'special_day': special_day
            }
            
            return result
            
        except Exception as e:
            Logger.error(f"Hicri dönüşüm hatası: {e}")
            return self._fallback(date)
    
    def _fallback(self, date):
        """Hata durumunda basit hesaplama (yaklaşık)"""
        try:
            # Yaklaşık dönüşüm: 622 yıl fark + 1/33 oranında düzeltme
            year = date.year - 622
            # 1/33 oranında düzeltme
            year = year - int(year / 33)
            
            # Ay ve gün yaklaşık
            month = int(((date.month * 30.5) % 365) // 30 + 1)
            day = int(((date.month * 30.5) % 365) % 30) + 1
            
            if month > 12:
                month = 12
                day = 30
            if month < 1:
                month = 1
            if day < 1:
                day = 1
            if year < 1:
                year = 1446
            
            return {
                'year': year,
                'month': month,
                'month_name': self.HIJRI_MONTHS[month - 1] if month <= 12 else self.HIJRI_MONTHS[11],
                'day': day,
                'date_str': f"{day} {self.HIJRI_MONTHS[month - 1] if month <= 12 else self.HIJRI_MONTHS[11]} {year}",
                'special_day': None
            }
        except:
            return {
                'year': 1446,
                'month': 1,
                'month_name': 'Muharrem',
                'day': 1,
                'date_str': '1 Muharrem 1446',
                'special_day': None
            }
    
    def is_special_day(self, hijri_date):
        """Özel gün kontrolü"""
        if hijri_date is None:
            return None
        return self.SPECIAL_DAYS.get(hijri_date['month'], {}).get(hijri_date['day'], None)


# ============= KIBLE BULUCU =============
class QiblaFinder:
    KAABA_LAT = 21.4225
    KAABA_LON = 39.8262
    
    def get_qibla_direction(self, lat, lon):
        try:
            lat1, lon1 = radians(lat), radians(lon)
            lat2, lon2 = radians(self.KAABA_LAT), radians(self.KAABA_LON)
            delta = lon2 - lon1
            x = cos(lat1) * tan(lat2) - sin(lat1) * cos(delta)
            y = sin(delta)
            angle = degrees(atan2(y, x))
            return angle if angle >= 0 else angle + 360
        except Exception as e:
            Logger.error(f"Kıble hatası: {e}")
            return None
    
    def get_qibla_info(self, lat, lon):
        angle = self.get_qibla_direction(lat, lon)
        if angle is None:
            return None
        directions = [
            (337.5, "Kuzey"), (22.5, "Kuzey"),
            (22.5, "Kuzeydoğu"), (67.5, "Kuzeydoğu"),
            (67.5, "Doğu"), (112.5, "Doğu"),
            (112.5, "Güneydoğu"), (157.5, "Güneydoğu"),
            (157.5, "Güney"), (202.5, "Güney"),
            (202.5, "Güneybatı"), (247.5, "Güneybatı"),
            (247.5, "Batı"), (292.5, "Batı"),
            (292.5, "Kuzeybatı"), (337.5, "Kuzeybatı")
        ]
        direction = "Kuzey"
        for i in range(0, len(directions), 2):
            if i + 1 < len(directions):
                if directions[i][0] <= angle < directions[i+1][0]:
                    direction = directions[i][1]
                    break
        distance = self._distance(lat, lon)
        return {
            'angle': round(angle, 2),
            'direction': direction,
            'distance_km': round(distance, 2)
        }
    
    def _distance(self, lat1, lon1):
        R = 6371
        lat1, lon1 = radians(lat1), radians(lon1)
        lat2, lon2 = radians(self.KAABA_LAT), radians(self.KAABA_LON)
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))


# ============= TESBİH =============
class DigitalTasbih:
    def __init__(self):
        self.count = 0
        self.daily_total = 0
        self.weekly_total = 0
        self.monthly_total = 0
        self.daily_date = datetime.now().strftime('%Y-%m-%d')
        self.weekly_date = datetime.now().strftime('%Y-%W')
        self.monthly_date = datetime.now().strftime('%Y-%m')
        self.current_zikir = "Sübhanallah (33)"
        self.zikir_options = [
            "Sübhanallah (33)",
            "Elhamdülillah (33)",
            "Allahu Ekber (33)",
            "Sübhanallahi ve bihamdihi (100)",
            "Estağfirullah (100)",
            "Salavat (100)",
            "La ilahe illallah (100)",
            "Serbest (Hedefsiz)"
        ]
    
    def increment(self, count=1):
        """Sayacı artır"""
        if isinstance(count, int):
            self.count += count
        else:
            self.count += 1
        self._update_totals()
        return self.count
    
    def reset(self):
        self.count = 0
    
    def set_zikir(self, zikir):
        self.current_zikir = zikir
        self.reset()
    
    def get_target(self):
        import re
        match = re.search(r'\((\d+)\)', self.current_zikir)
        if match:
            return int(match.group(1))
        return None
    
    def _update_totals(self):
        today = datetime.now().strftime('%Y-%m-%d')
        week = datetime.now().strftime('%Y-%W')
        month = datetime.now().strftime('%Y-%m')
        
        if today != self.daily_date:
            self.daily_total = 0
            self.daily_date = today
        if week != self.weekly_date:
            self.weekly_total = 0
            self.weekly_date = week
        if month != self.monthly_date:
            self.monthly_total = 0
            self.monthly_date = month
        
        self.daily_total += 1
        self.weekly_total += 1
        self.monthly_total += 1
    
    def get_daily_stats(self):
        today = datetime.now().strftime('%Y-%m-%d')
        if today != self.daily_date:
            self.daily_total = 0
            self.daily_date = today
        return {
            'daily_total': self.daily_total,
            'weekly_total': self.weekly_total,
            'monthly_total': self.monthly_total,
            'current_count': self.count,
            'current_zikir': self.current_zikir,
            'target': self.get_target()
        }
    
    def get_progress(self):
        target = self.get_target()
        if target and target > 0:
            return min(100, (self.count / target) * 100)
        return 0


qibla_finder = QiblaFinder()
hijri_calendar = HijriCalendar()
digital_tasbih = DigitalTasbih()