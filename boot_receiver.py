"""
Boot Receiver - Telefon açılışında hizmeti başlat
"""

from android import service

def on_boot():
    try:
        service.start('MihrabService')
        print("Mihrab: Telefon açılışında hizmet başlatıldı")
    except Exception as e:
        print(f"Hizmet başlatma hatası: {e}")