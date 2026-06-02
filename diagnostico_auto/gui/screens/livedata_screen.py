# -*- coding: utf-8 -*-
"""
Pantalla de datos en tiempo real.

Muestra los sensores del vehículo actualizándose en vivo mediante
gauges circulares (parámetros clave) y barras (parámetros secundarios).
"""
from kivy.metrics import dp
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard

from gui.theme import Color, Dim, Fuente
from gui.controller import controlador
from gui.components.gauge import MedidorCircular, MedidorBarra


class PantallaDatosVivo(MDScreen):
    """Datos de sensores en tiempo real."""

    # Parámetros que se muestran como gauge circular (los más importantes)
    GAUGES_PRINCIPALES = [
        ("RPM motor", "rpm", 0, 7000, Color.CYAN, True),
        ("Temp. refrigerante", "°C", 0, 120, Color.PRIMARIO, True),
        ("Carga del motor", "%", 0, 100, Color.EXITO, True),
        ("Posición acelerador", "%", 0, 100, Color.ADVERTENCIA, False),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "datos"
        self.md_bg_color = Color.FONDO
        self._activo = False
        self._evento = None
        self._gauges = {}
        self._barras = {}
        self._construir()

    def _construir(self):
        raiz = MDBoxLayout(orientation="vertical", padding=dp(Dim.PADDING),
                           spacing=dp(Dim.ESPACIO))

        # ===== Encabezado con botón play/pausa =====
        encabezado = MDBoxLayout(orientation="horizontal", size_hint_y=None,
                                 height=dp(48), spacing=dp(Dim.ESPACIO))
        col_titulo = MDBoxLayout(orientation="vertical", pos_hint={"center_y": 0.5})
        col_titulo.add_widget(MDLabel(
            text="Datos en tiempo real", theme_text_color="Custom",
            text_color=Color.TEXTO, font_style="H5", bold=True,
            size_hint_y=None, height=dp(32)))
        self._lbl_estado = MDLabel(
            text="Pausado", theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO, size_hint_y=None, height=dp(18))
        col_titulo.add_widget(self._lbl_estado)

        self._btn_play = MDIconButton(
            icon="play", theme_icon_color="Custom", icon_color=(1, 1, 1, 1),
            md_bg_color=Color.PRIMARIO, pos_hint={"center_y": 0.5},
            icon_size=dp(28))
        self._btn_play.bind(on_release=self._toggle)

        encabezado.add_widget(col_titulo)
        encabezado.add_widget(self._btn_play)
        raiz.add_widget(encabezado)

        # ===== Contenido scrollable =====
        scroll = MDScrollView(do_scroll_x=False)
        contenido = MDBoxLayout(orientation="vertical", spacing=dp(Dim.ESPACIO),
                                size_hint_y=None, adaptive_height=True)

        # Grid de gauges circulares (2 columnas)
        grid_gauges = MDGridLayout(cols=2, spacing=dp(Dim.ESPACIO),
                                   size_hint_y=None, adaptive_height=True,
                                   padding=[0, dp(4)])
        for nombre, unidad, vmin, vmax, color, alerta in self.GAUGES_PRINCIPALES:
            cont_gauge = MDCard(
                md_bg_color=Color.SUPERFICIE, radius=[dp(Dim.RADIO)],
                size_hint_y=None, height=dp(168), elevation=0,
                line_color=Color.BORDE, line_width=1,
                padding=dp(Dim.PADDING_CHICO))
            gauge = MedidorCircular(
                titulo=nombre, unidad=unidad, valor_min=vmin, valor_max=vmax,
                color_arco=color, color_alerta=alerta,
                pos_hint={"center_x": 0.5})
            self._gauges[nombre] = gauge
            cont_gauge.add_widget(gauge)
            grid_gauges.add_widget(cont_gauge)
        contenido.add_widget(grid_gauges)

        # Sección de parámetros secundarios (barras)
        contenido.add_widget(MDLabel(
            text="Otros parámetros", theme_text_color="Custom",
            text_color=Color.TEXTO, font_size=Fuente.SUBTITULO, bold=True,
            size_hint_y=None, height=dp(32)))

        self._tarjeta_barras = MDCard(
            orientation="vertical", md_bg_color=Color.SUPERFICIE,
            radius=[dp(Dim.RADIO)], size_hint_y=None, adaptive_height=True,
            elevation=0, line_color=Color.BORDE, line_width=1,
            padding=dp(Dim.PADDING), spacing=dp(Dim.ESPACIO_CHICO))

        barras_def = [
            ("Velocidad", "km/h", 0, 220, Color.CYAN),
            ("Flujo de aire (MAF)", "g/s", 0, 50, Color.PRIMARIO),
            ("Presión colector", "kPa", 0, 250, Color.INFO),
            ("Avance de encendido", "°", -10, 40, Color.ADVERTENCIA),
            ("Temp. admisión", "°C", 0, 90, Color.EXITO),
            ("Nivel combustible", "%", 0, 100, Color.CYAN),
            ("Voltaje batería", "V", 10, 16, Color.EXITO),
        ]
        for nombre, unidad, vmin, vmax, color in barras_def:
            barra = MedidorBarra(titulo=nombre, unidad=unidad,
                                 valor_min=vmin, valor_max=vmax, color_barra=color)
            self._barras[nombre] = barra
            self._tarjeta_barras.add_widget(barra)
        contenido.add_widget(self._tarjeta_barras)

        scroll.add_widget(contenido)
        raiz.add_widget(scroll)
        self.add_widget(raiz)

    def _toggle(self, *_):
        if self._activo:
            self._detener()
        else:
            self._iniciar()

    def _iniciar(self):
        self._activo = True
        self._btn_play.icon = "pause"
        self._lbl_estado.text = "● En vivo"
        self._lbl_estado.text_color = Color.EXITO
        # Actualizar cada 500ms
        self._evento = Clock.schedule_interval(self._actualizar, 0.5)

    def _detener(self):
        self._activo = False
        self._btn_play.icon = "play"
        self._lbl_estado.text = "Pausado"
        self._lbl_estado.text_color = Color.TEXTO_SUAVE
        if self._evento:
            self._evento.cancel()
            self._evento = None

    def _actualizar(self, *_):
        datos = controlador.leer_datos_vivo()
        for nombre, (valor, _unidad) in datos.items():
            if nombre in self._gauges:
                self._gauges[nombre].actualizar(valor)
            if nombre in self._barras:
                self._barras[nombre].actualizar(valor)

    def on_leave(self, *_):
        """Detener actualizaciones al salir de la pantalla (ahorra recursos)."""
        self._detener()
