#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lanzador de DiagnósticoPro para PC.

Uso:
    python run.py            -> abre la aplicación
    python run.py --check    -> verifica dependencias sin abrir la app
"""
import sys
import os

def verificar_dependencias():
    faltantes = []
    opcionales_faltantes = []

    requeridos = [
        ("kivy", "kivy==2.3.1"),
        ("kivymd", "kivymd==1.2.0"),
        ("PIL", "pillow>=10.0"),
        ("serial", "pyserial>=3.5"),
    ]
    for modulo, paquete in requeridos:
        try:
            __import__(modulo)
        except ImportError:
            faltantes.append(paquete)

    if faltantes:
        print("ERROR — Faltan dependencias. Ejecuta:")
        print(f"  pip install {' '.join(faltantes)}")
        print()
        print("O instala todo de una vez:")
        print("  pip install -r requirements-pc.txt")
        return False

    if opcionales_faltantes:
        print("AVISO — Opcionales no instalados (no necesarios para Demo):")
        for p in opcionales_faltantes:
            print(f"  {p}")

    print("OK — Todas las dependencias están disponibles.")
    return True

def main():
    if "--check" in sys.argv:
        verificar_dependencias()
        return

    if not verificar_dependencias():
        sys.exit(1)

    # Añadir diagnostico_auto al path
    base = os.path.dirname(os.path.abspath(__file__))
    app_dir = os.path.join(base, "diagnostico_auto")
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)

    os.chdir(app_dir)
    from gui.app import main as arrancar
    arrancar()

if __name__ == "__main__":
    main()
