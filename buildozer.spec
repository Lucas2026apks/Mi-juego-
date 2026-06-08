[app]
# Nombre de tu juego en la pantalla del celular/tablet
title = Guerrero 63km Chulupi Edition
# Nombre interno del paquete (sin espacios ni caracteres especiales)
package.name = guerrero63km
# Dominio del desarrollador
package.domain = org.chulupigames

# Directorio donde están tus archivos (el punto significa la carpeta actual)
source.dir = .

# Extensiones de archivos que Buildozer debe meter dentro del APK
source.include_exts = py, png, jpg, json

# Versión de tu aplicación
version = 1.0

# ¡Muy importante! Requisitos de librerías para tu juego
requirements = python3, pygame

# Orientación de la pantalla (Horizontal)
orientation = landscape

# Forzar que el juego ocupe toda la pantalla sin barras de notificaciones
fullscreen = 1

# Arquitectura para celulares y tablets Android modernos
android.archs = arm64-v8a

# (Opcional) Si quieres que se guarde en la memoria del dispositivo
android.allow_backup = True
