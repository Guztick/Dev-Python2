# -*- coding: utf-8 -*-
"""
Aplicación principal de DiagnosticoPro.

Ensambla todas las pantallas, configura el tema y gestiona la
navegación. Punto de entrada de la interfaz gráfica.

Ejecutar:
    python -m gui.app          (desde diagnostico_auto/)
    python gui/app.py
"""
import os
import sys

# Asegurar que el paquete raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kivy.metrics import dp
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard

from gui.theme import Color, Dim, Fuente, TEMA_KIVYMD
from gui.controller import controlador
from gui.components.navbar import BarraNavegacion
from gui.screens.connection_screen import PantallaConexion
from gui.screens.dashboard_screen import PantallaDashboard
from gui.screens.scan_screen import PantallaEscaneo
from gui.screens.dtc_screen import PantallaDTCs
from gui.screens.livedata_screen import PantallaDatosVivo
from gui.screens.adapter_screen import PantallaAdaptador
from gui.screens.manual_screen import PantallaManual


class PantallaPrincipal(MDScreen):
    """
    Contenedor principal tras la conexión.
    Aloja las secciones (dashboard, escaneo, DTCs, datos) y la
    barra de navegación inferior.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "principal"
        self.md_bg_color = Color.FONDO
        self._construir()

    def on_pre_enter(self, *_):
        """Refrescar la info del vehículo al entrar (tras conectar)."""
        self._dashboard._actualizar_info()

    def _construir(self):
        raiz = MDBoxLayout(orientation="vertical")

        # Gestor de secciones internas — sin animación (estilo pestañas)
        from kivymd.uix.screenmanager import MDScreenManager as _SM
        from kivy.uix.screenmanager import NoTransition
        self._secciones = MDScreenManager(transition=NoTransition())

        self._dashboard = PantallaDashboard(ir_a_seccion=self._ir_a_seccion)
        self._escaneo = PantallaEscaneo(on_resultado=self._on_escaneo_resultado)
        self._dtcs = PantallaDTCs()
        self._datos = PantallaDatosVivo()
        self._adaptador = PantallaAdaptador()
        self._manual = PantallaManual()

        # Renombrar para coincidir con la navegación interna
        self._dashboard.name = "inicio"
        self._escaneo.name = "escaneo"
        self._dtcs.name = "dtcs"
        self._datos.name = "datos"
        self._adaptador.name = "adaptador"
        self._manual.name = "manual"

        for s in (self._dashboard, self._escaneo, self._dtcs,
                  self._datos, self._adaptador, self._manual):
            self._secciones.add_widget(s)

        # Barra de navegación inferior
        self._navbar = BarraNavegacion(
            items=[
                ("view-dashboard", "Inicio", "inicio"),
                ("radar", "Escaneo", "escaneo"),
                ("alert-circle", "DTCs", "dtcs"),
                ("gauge", "Datos", "datos"),
                ("book-wrench", "Manual", "manual"),
                ("usb", "Escáner", "adaptador"),
            ],
            on_cambio=self._cambiar_seccion,
        )

        raiz.add_widget(self._secciones)
        raiz.add_widget(self._navbar)
        self.add_widget(raiz)

        self._navbar.set_activo("inicio")

    def _cambiar_seccion(self, nombre):
        self._secciones.current = nombre

    def _ir_a_seccion(self, seccion):
        """Llamado desde las tarjetas de acción del dashboard."""
        mapeo = {
            "escaneo": "escaneo",
            "dtcs": "dtcs",
            "datos": "datos",
            "actuadores": "escaneo",  # Por ahora redirige a escaneo
        }
        destino = mapeo.get(seccion, "inicio")
        self._secciones.current = destino
        self._navbar.set_activo(destino)

    def ir_a_procedimiento_dtc(self, codigo_dtc: str):
        """
        Navega al manual y muestra el procedimiento del código DTC.
        Llamado desde PantallaDTCs al pulsar 'Ver procedimiento'.
        """
        self._secciones.current = "manual"
        self._navbar.set_activo("manual")
        self._manual.ir_a_procedimiento(codigo_dtc)

    def _on_escaneo_resultado(self, num_dtcs, num_modulos):
        """Actualiza el dashboard con el resumen del escaneo."""
        self._dashboard.set_resumen(num_dtcs, num_modulos)


class DiagnosticoProApp(MDApp):
    """Aplicación principal."""

    def build(self):
        self.title = "DiagnósticoPro"

        # Configurar tema KivyMD
        self.theme_cls.theme_style = TEMA_KIVYMD["theme_style"]
        self.theme_cls.primary_palette = TEMA_KIVYMD["primary_palette"]
        self.theme_cls.accent_palette = TEMA_KIVYMD["accent_palette"]
        try:
            self.theme_cls.material_style = TEMA_KIVYMD["material_style"]
        except Exception:
            pass

        # Color de fondo de la ventana
        Window.clearcolor = Color.FONDO

        # En escritorio, simular proporción de teléfono para previsualizar
        if not self._es_android():
            Window.size = (400, 800)

        # Gestor principal de pantallas
        self._sm = MDScreenManager()
        self._sm.add_widget(PantallaConexion())
        self._sm.add_widget(PantallaPrincipal())

        return self._sm

    @staticmethod
    def _es_android() -> bool:
        return "ANDROID_ARGUMENT" in os.environ

    def on_stop(self):
        """Limpieza al cerrar la app."""
        try:
            controlador.desconectar()
        except Exception:
            pass


def main():
    DiagnosticoProApp().run()


if __name__ == "__main__":
    main()
