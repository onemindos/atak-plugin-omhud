[app]
title = OMHud
package.name = omhud
package.domain = org.onemindos
source.dir = .
source.include_exts = py
version = 0.1.0
requirements = kivy==2.3.0,nats-py
p4a.branch = develop
orientation = landscape
fullscreen = 1
android.permissions = INTERNET,CAMERA
android.api = 33
android.minapi = 26
android.ndk = 25b
android.sdk = 33
p4a.allow_backup = true
android.add_src = .

[buildozer]
log_level = 2
warn_on_root = 1
