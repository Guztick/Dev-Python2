# -*- coding: utf-8 -*-
"""
Punto de entrada de DiagnosticoPro.

Este es el archivo que ejecuta la aplicación móvil (APK) y también
sirve para lanzar la interfaz gráfica en escritorio.

    python main.py            → Lanza la interfaz gráfica
    python cli.py --demo      → Modo consola (terminal)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import main

if __name__ == "__main__":
    main()
