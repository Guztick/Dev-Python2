# -*- coding: utf-8 -*-
"""
Diálogo de gestión de drivers de adaptadores USB.

Se abre desde la pantalla de conexión. Analiza los adaptadores USB
conectados, identifica su chip, indica si el driver está instalado y
permite instalar el driver correcto (instalador local o descarga oficial).
"""
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog

from gui.theme import Color, Dim, Fuente
from gui.controller import controlador


class TarjetaDriver(MDCard):
    """Tarjeta de un dispositivo USB con su estado de driver."""

    def __init__(self, dispositivo, on_instalar, **kwargs):
        super().__init__(**kwargs)
        self._disp = dispositivo
        self._on_instalar = on_instalar

        self.orientation = "vertical"
        self.md_bg_color = Color.SUPERFICIE
        self.radius = [dp(Dim.RADIO_CHICO)]
        self.size_hint_y = None
        self.adaptive_height = True
        self.padding = dp(Dim.PADDING)
        self.spacing = dp(4)
        self.elevation = 0
        self.line_color = Color.BORDE
        self.line_width = 1

        from core.hardware.drivers import EstadoDriver
        instalado = dispositivo.estado == EstadoDriver.INSTALADO

        # Fila superior: icono de estado + nombre + badge
        fila = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                           height=dp(28), spacing=dp(8))
        color_estado = Color.EXITO if instalado else Color.ADVERTENCIA
        icono_estado = "check-circle" if instalado else "alert-circle"
        fila.add_widget(MDIcon(
            icon=icono_estado, theme_text_color="Custom", text_color=color_estado,
            font_size=dp(20), size_hint_x=None, width=dp(26),
            pos_hint={"center_y": 0.5}))
        fila.add_widget(MDLabel(
            text=dispositivo.nombre, theme_text_color="Custom",
            text_color=Color.TEXTO, font_size=Fuente.CUERPO, bold=True,
            pos_hint={"center_y": 0.5}, shorten=True, shorten_from="right"))
        self.add_widget(fila)

        # Chip identificado
        self.add_widget(MDLabel(
            text=f"Chip: {dispositivo.nombre_chip}", theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.SECUNDARIO,
            size_hint_y=None, height=dp(20)))

        # Estado / puerto
        if instalado:
            texto_estado = f"Driver instalado · Puerto {dispositivo.puerto}"
            color_txt = Color.EXITO
        else:
            texto_estado = "Driver no instalado · sin puerto COM"
            color_txt = Color.ADVERTENCIA
        self.add_widget(MDLabel(
            text=texto_estado, theme_text_color="Custom", text_color=color_txt,
            font_size=Fuente.ETIQUETA, size_hint_y=None, height=dp(18)))

        # Botón de instalar driver (solo si falta y hay chip identificado)
        if not instalado and dispositivo.chip:
            btn = MDRaisedButton(
                text="INSTALAR DRIVER", md_bg_color=Color.PRIMARIO,
                theme_text_color="Custom", text_color=(1, 1, 1, 1),
                font_size=Fuente.ETIQUETA, size_hint=(1, None), height=dp(40),
                elevation=0)
            btn.bind(on_release=lambda *_: self._on_instalar(dispositivo))
            self.add_widget(btn)


class DialogoDrivers:
    """Controla el diálogo de gestión de drivers."""

    def __init__(self):
        self._dialogo = None
        self._contenido = None
        self._btn_analizar = None

    def abrir(self):
        if self._dialogo is None:
            self._construir()
        self._dialogo.open()
        # Analizar automáticamente al abrir
        Clock.schedule_once(lambda dt: self._analizar(), 0.3)

    def _construir(self):
        contenedor = MDBoxLayout(
            orientation="vertical", spacing=dp(Dim.ESPACIO),
            size_hint_y=None, height=dp(420), padding=[0, dp(4)])

        # Texto de ayuda Bluetooth
        ayuda = MDCard(
            md_bg_color=(Color.CYAN[0], Color.CYAN[1], Color.CYAN[2], 0.10),
            radius=[dp(Dim.RADIO_CHICO)], size_hint_y=None, height=dp(56),
            padding=dp(10), elevation=0, line_color=Color.CYAN, line_width=1)
        fila_ayuda = MDBoxLayout(orientation="horizontal", spacing=dp(8))
        fila_ayuda.add_widget(MDIcon(
            icon="bluetooth", theme_text_color="Custom", text_color=Color.CYAN,
            font_size=dp(18), size_hint_x=None, width=dp(24),
            pos_hint={"center_y": 0.5}))
        fila_ayuda.add_widget(MDLabel(
            text="Los adaptadores Bluetooth no necesitan driver: solo "
                 "empareja en Windows y usa el puerto COM saliente.",
            theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.ETIQUETA))
        ayuda.add_widget(fila_ayuda)
        contenedor.add_widget(ayuda)

        # Lista scrollable de dispositivos
        scroll = MDScrollView(do_scroll_x=False)
        self._contenido = MDBoxLayout(
            orientation="vertical", spacing=dp(Dim.ESPACIO_CHICO),
            size_hint_y=None, adaptive_height=True)
        scroll.add_widget(self._contenido)
        contenedor.add_widget(scroll)

        self._btn_analizar = MDRaisedButton(
            text="ANALIZAR ADAPTADORES", md_bg_color=Color.SUPERFICIE,
            theme_text_color="Custom", text_color=Color.PRIMARIO,
            line_color=Color.PRIMARIO, font_size=Fuente.SECUNDARIO,
            size_hint=(1, None), height=dp(44), elevation=0)
        self._btn_analizar.bind(on_release=lambda *_: self._analizar())
        contenedor.add_widget(self._btn_analizar)

        self._dialogo = MDDialog(
            title="Drivers de adaptadores USB",
            type="custom",
            content_cls=contenedor,
            buttons=[
                MDFlatButton(
                    text="ADMIN. DISPOSITIVOS", theme_text_color="Custom",
                    text_color=Color.TEXTO_SUAVE,
                    on_release=lambda *_: controlador.abrir_administrador_dispositivos()),
                MDFlatButton(
                    text="CERRAR", theme_text_color="Custom",
                    text_color=Color.PRIMARIO,
                    on_release=lambda *_: self._dialogo.dismiss()),
            ],
        )

    def _analizar(self):
        self._btn_analizar.text = "ANALIZANDO..."
        self._btn_analizar.disabled = True
        self._contenido.clear_widgets()
        cargando = MDBoxLayout(orientation="vertical", size_hint_y=None,
                               height=dp(80))
        cargando.add_widget(MDIcon(
            icon="sync", theme_text_color="Custom", text_color=Color.PRIMARIO,
            font_size=dp(36), halign="center", size_hint_y=None, height=dp(44)))
        cargando.add_widget(MDLabel(
            text="Buscando adaptadores...", theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE, font_size=Fuente.SECUNDARIO,
            halign="center"))
        self._contenido.add_widget(cargando)

        controlador.diagnosticar_drivers(
            on_completo=lambda disp: Clock.schedule_once(
                lambda dt: self._mostrar_resultado(disp)))

    def _mostrar_resultado(self, dispositivos):
        self._btn_analizar.text = "ANALIZAR DE NUEVO"
        self._btn_analizar.disabled = False
        self._contenido.clear_widgets()

        if not dispositivos:
            vacio = MDBoxLayout(orientation="vertical", size_hint_y=None,
                                height=dp(120), spacing=dp(8))
            vacio.add_widget(MDIcon(
                icon="usb-port", theme_text_color="Custom",
                text_color=Color.TEXTO_TENUE, font_size=dp(48),
                halign="center", size_hint_y=None, height=dp(56)))
            vacio.add_widget(MDLabel(
                text="No se detectaron adaptadores USB.\n"
                     "Conecta tu ELM327 por USB y vuelve a analizar.",
                theme_text_color="Custom", text_color=Color.TEXTO_TENUE,
                font_size=Fuente.SECUNDARIO, halign="center"))
            self._contenido.add_widget(vacio)
            return

        for disp in dispositivos:
            self._contenido.add_widget(
                TarjetaDriver(disp, on_instalar=self._instalar))

    def _instalar(self, dispositivo):
        controlador.instalar_driver(
            dispositivo,
            on_completo=lambda exito, msg: Clock.schedule_once(
                lambda dt: self._on_instalado(exito, msg)))

    def _on_instalado(self, exito, mensaje):
        from kivymd.uix.snackbar import Snackbar
        try:
            Snackbar(text=mensaje, duration=3).open()
        except Exception:
            # Fallback si la versión de Snackbar difiere
            pass
