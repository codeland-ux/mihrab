[app]
title = Mihrab
package.name = mihrab
package.domain = com.yourcompany
version = 2.0.0
version.code = 1
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,json,mp3,wav
source.include_patterns = assets/*
requirements = python3,kivy==2.3.1,plyer,requests
orientation = portrait
services = MihrabService:service.py

android.permissions = INTERNET,ACCESS_NETWORK_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,VIBRATE,WAKE_LOCK,RECEIVE_BOOT_COMPLETED,FOREGROUND_SERVICE,POST_NOTIFICATIONS
android.api = 29
android.minapi = 21
android.target_sdk = 31
android.ndk = 25b
android.fullscreen = 0
android.allow_backup = True

presplash.filename = %(source.dir)s/assets/presplash.png
icon.filename = %(source.dir)s/assets/icon.png

[buildozer]
log_level = 2
warn_on_root = 0