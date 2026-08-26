"""
Arka Plan Hizmeti - Mihrab
"""

import time
import os
import sys
from datetime import datetime, timedelta

# Proje klasörünü ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from plyer import notification
except:
    notification = None

try:
    from prayer_manager import prayer_manager
except:
    prayer_manager = None


def main():
    print("🔔 Mihrab Arka Plan Hizmeti Başlatıldı")
    
    # Basit test bildirimi
    try:
        if notification:
            notification.notify(
                title="🕌 Mihrab",
                message="Arka plan hizmeti çalışıyor!",
                app_name='Mihrab'
            )
    except:
        pass
    
    last_check = None
    sent_notifications = {}
    prayer_list = ['İmsak', 'Güneş', 'Öğle', 'İkindi', 'Akşam', 'Yatsı']
    
    while True:
        try:
            now = datetime.now()
            
            if last_check and (now - last_check).seconds < 30:
                time.sleep(5)
                continue
            
            last_check = now
            
            # Şehir bilgisini oku
            city_file = os.path.join(
                os.path.dirname(__file__), 'assets', 'data', 'last_city.json'
            )
            
            if os.path.exists(city_file) and prayer_manager:
                import json
                with open(city_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    city_name = data.get('city_name', '')
                    
                    if city_name:
                        times = prayer_manager.get_prayer_times(city_name)
                        
                        if times:
                            for name in prayer_list:
                                time_str = times.get(name, '')
                                if ':' in time_str:
                                    h, m = map(int, time_str.split(':'))
                                    prayer_time = datetime.now().replace(
                                        hour=h, minute=m, second=0, microsecond=0
                                    )
                                    
                                    # 15 dakika önce
                                    pre_time = prayer_time - timedelta(minutes=15)
                                    pre_key = f"{name}_pre"
                                    if (now - pre_time).seconds < 60 and pre_key not in sent_notifications:
                                        if notification:
                                            notification.notify(
                                                title=f"🕌 {name} Vakti Yaklaşıyor",
                                                message=f"{name} vaktine 15 dakika kaldı",
                                                app_name='Mihrab'
                                            )
                                        sent_notifications[pre_key] = now
                                    
                                    # Vakit geldi
                                    time_key = f"{name}_time"
                                    if (now - prayer_time).seconds < 60 and time_key not in sent_notifications:
                                        if notification:
                                            notification.notify(
                                                title=f"🕌 {name} Vakti",
                                                message=f"{name} vakti girdi",
                                                app_name='Mihrab'
                                            )
                                        sent_notifications[time_key] = now
                            
                            # Gün geçtiyse temizle
                            for key in list(sent_notifications.keys()):
                                if (now - sent_notifications[key]).days > 1:
                                    del sent_notifications[key]
            
            time.sleep(30)
            
        except Exception as e:
            print(f"Hizmet hatası: {e}")
            time.sleep(60)


if __name__ == '__main__':
    main()