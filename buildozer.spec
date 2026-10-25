[app]
title = BilimAi
package.name = bilimai
package.domain = org.bilim
source.dir = .
source.include_exts = py,png,jpg,ttf,kv,atlas
source.exclude_dirs = .github,bin,__pycache__,server
source.exclude_patterns = make_assets.py
version = 0.4
requirements = python3,kivy==2.3.0,certifi,openssl,pyjnius,android
orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/data/icon.png
icon.adaptive_foreground.filename = %(source.dir)s/data/icon_fg.png
icon.adaptive_background.filename = %(source.dir)s/data/icon_bg.png
presplash.filename = %(source.dir)s/data/presplash.png
android.presplash_color = #0A1842

android.permissions = INTERNET
android.manifest.intent_filters = intent_filters.xml
android.manifest.launch_mode = singleTask
android.api = 33
android.minapi = 24
android.archs = arm64-v8a
android.accept_sdk_license = True
android.ndk = 25b

# Pin python-for-android to a release that still builds Kivy 2.3.0 (master moved to Python 3.14)
p4a.branch = v2024.01.21
android.release_artifact = aab

[buildozer]
log_level = 2
warn_on_root = 1
