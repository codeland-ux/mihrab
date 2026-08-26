"""
Notifier - Bildirim Yöneticisi
Mihrab - İslami Yaşam Rehberi
"""

from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform
from kivy.core.audio import SoundLoader
import os

try:
    from plyer import notification, vibrator
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False
    Logger.warning("Notifier: Plyer kullanılamıyor")


class Notifier:
    def __init__(self):
        self.notification_enabled = True
        self.vibration_enabled = True
        self.sound_enabled = True
        self.scheduled_events = []
        self.sound = None
        
        # ✅ iOS bildirim izni kontrolü
        if platform == 'ios':
            self._request_ios_permissions()
    
    def _request_ios_permissions(self):
        """✅ iOS bildirim izni iste"""
        try:
            from plyer import notification
            notification.notify(
                title="Mihrab",
                message="Namaz bildirimleri için izin verin",
                app_name='Mihrab'
            )
            Logger.info("Notifier: iOS bildirim izni istendi")
        except Exception as e:
            Logger.warning(f"Notifier: iOS bildirim izni hatası - {e}")
    
    def send_notification(self, title, message, vibration=True, play_sound=False):
        """Bildirim gönder + ses + titreşim"""
        try:
            if self.notification_enabled and PLYER_AVAILABLE:
                if platform == 'android':
                    from plyer import notification
                    notification.notify(
                        title=title,
                        message=message,
                        app_name='Mihrab',
                        app_icon=''
                    )
                elif platform == 'ios':
                    from plyer import notification
                    notification.notify(
                        title=title,
                        message=message,
                        app_name='Mihrab',
                        sound=play_sound,
                    )
                else:
                    from plyer import notification
                    notification.notify(
                        title=title,
                        message=message,
                        app_name='Mihrab',
                        timeout=10
                    )
            
            if play_sound and self.sound_enabled:
                if platform == 'win':
                    self._play_windows_beep(count=2, duration=0.15)
                elif platform == 'ios' or platform == 'mac':
                    self._play_ios_sound()
                else:
                    self._play_fallback_sound()
            
            if vibration and self.vibration_enabled and platform == 'android':
                self.vibrate()
                
        except Exception as e:
            Logger.error(f"Notifier: Bildirim hatası - {e}")
    
    def _play_windows_beep(self, count=2, duration=0.15):
        """Windows bip sesi"""
        try:
            import winsound
            for i in range(count):
                winsound.Beep(1000, int(duration * 1000))
                if i < count - 1:
                    import time
                    time.sleep(0.1)
        except:
            pass
    
    def _play_ios_sound(self):
        """✅ iOS ses çal (Sistem sesi)"""
        try:
            from pyobjus import autoclass
            AudioServices = autoclass('AudioServices')
            AudioServices.playSystemSound(1000)
            Logger.info("Notifier: iOS ses çalıyor")
        except Exception as e:
            Logger.warning(f"Notifier: iOS ses hatası - {e}")
            self._play_fallback_sound()
    
    def _play_fallback_sound(self):
        """Yedek ses"""
        try:
            sound = SoundLoader.load('assets/sounds/beep.wav')
            if sound:
                sound.play()
        except:
            pass
    
    def play_beep(self, count=2, duration=0.2):
        """Bip sesi çal"""
        try:
            if not self.sound_enabled:
                return
            
            if platform == 'win':
                self._play_windows_beep(count, duration)
            elif platform == 'ios' or platform == 'mac':
                self._play_ios_sound()
            else:
                self._play_fallback_sound()
                
        except Exception as e:
            Logger.error(f"Notifier: Bip sesi hatası - {e}")
    
    def vibrate(self, duration=0.5, count=2):
        """SADECE ANDROİD'DE TİTREŞİM!"""
        if platform != 'android':
            return
        
        try:
            if self.vibration_enabled and PLYER_AVAILABLE:
                from plyer import vibrator
                pattern = [0, int(duration * 1000)] * count
                vibrator.vibrate(pattern=pattern)
        except Exception as e:
            Logger.error(f"Notifier: Titreşim hatası - {e}")
    
    def play_notification_sound(self):
        self.play_beep(count=2, duration=0.15)
    
    def play_adhan_sound(self):
        self.play_beep(count=3, duration=0.5)
    
    def toggle_notifications(self, enabled):
        self.notification_enabled = enabled
        if not enabled:
            self.cancel_all()
    
    def toggle_vibration(self, enabled):
        self.vibration_enabled = enabled
    
    def toggle_sound(self, enabled):
        self.sound_enabled = enabled
    
    def cancel_all(self):
        for event in self.scheduled_events:
            try:
                Clock.unschedule(event)
            except:
                pass
        self.scheduled_events.clear()
    


notifier = Notifier()