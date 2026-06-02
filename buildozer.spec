[app]

# Nombre de la aplicación
title = DiagnosticoPro

# Nombre del paquete (sin espacios)
package.name = diagnosticopro

# Dominio (formato inverso, identificador único de la app)
package.domain = com.diagnostico

# Directorio con el código fuente (donde está main.py)
source.dir = diagnostico_auto

# Extensiones de archivos a incluir en el paquete
source.include_exts = py,png,jpg,jpeg,kv,json,ttf,atlas

# Patrones a excluir
source.exclude_dirs = tests, bin, __pycache__, .buildozer

# Versión de la aplicación
version = 0.1.0

# Dependencias de Python
# pyjnius: acceso a APIs nativas de Android (Bluetooth)
# android: módulo de integración con Android
requirements = python3,kivy==2.3.1,kivymd==1.2.0,pillow,pyjnius,android,plyer

# Orientación de la pantalla (portrait = vertical, ideal para móvil)
orientation = portrait

# Pantalla completa (0 = con barra de estado)
fullscreen = 0

# Ícono de la app (se generará uno por defecto si no existe)
# icon.filename = %(source.dir)s/assets/icono.png

# Color de fondo de la pantalla de carga
android.presplash_color = #0D1117

# ===== Permisos de Android =====
# INTERNET: para adaptadores ELM327 WiFi
# BLUETOOTH*: para conexión con escáner Bluetooth
# ACCESS_*_LOCATION: requerido por Android para escanear dispositivos Bluetooth
android.permissions = INTERNET, ACCESS_NETWORK_STATE, BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, ACCESS_FINE_LOCATION, ACCESS_COARSE_LOCATION

# ===== Características de hardware =====
# Habilitar USB host para adaptadores OBD por USB OTG
android.features = android.hardware.usb.host

# ===== Versiones de API de Android =====
# api: versión objetivo (33 = Android 13)
# minapi: versión mínima soportada (21 = Android 5.0)
android.api = 33
android.minapi = 21

# Arquitecturas a compilar (cubre la mayoría de dispositivos modernos)
android.archs = arm64-v8a, armeabi-v7a

# Aceptar automáticamente las licencias del SDK de Android
android.accept_sdk_license = True

# Permitir copias de seguridad
android.allow_backup = True

[buildozer]

# Nivel de log (2 = detallado, útil para depurar la compilación)
log_level = 2

# Advertir si se ejecuta como root
warn_on_root = 1
