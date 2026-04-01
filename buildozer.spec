[app]
title = RotorProtek
package.name = rotorprotek
package.domain = com.rotorprotek
source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,ttf,ico,csv,xlsx
source.exclude_dirs = .git,.github,build,old,__pycache__
source.exclude_patterns = *.pyc,*.pyo,allstarts.csv,allstarts_lemona.csv,tmp_*.csv
version = 0.1.16
icon.filename = logo_app_hd.png
presplash.filename = logo_app_hd.png

requirements = python3,kivy==2.3.0,kivymd==1.2.0,numpy,pyjnius,openpyxl

orientation = portrait,landscape
fullscreen = 0

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.api = 34
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.private_storage = True
android.accept_sdk_license = True
android.enable_androidx = True
android.entrypoint = org.kivy.android.PythonActivity
android.presplash_color = #F2F2F2
android.logcat_filters = python:D,ActivityManager:I,*:S
