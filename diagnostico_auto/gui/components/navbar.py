# -*- coding: utf-8 -*-
"""
Barra de navegación inferior personalizada.

Construida a medida para control total del estilo y coherencia
con el tema de la app. Cada ítem tiene ícono + etiqueta, y resalta
la sección activa.
"""
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel, MDIcon

from gui.theme import Color, Dim, Fuente


class ItemNav(ButtonBehavior, MDBoxLayout):
    """Un ítem de la barra de navegación (ícono + etiqueta)."""

    def __init__(self, icono, etiqueta, nombre, on_seleccion, **kwargs):
        super().__init__(**kwargs)
        self.nombre = nombre
        self._on_seleccion = on_seleccion
        self._activo = False

        self.orientation = "vertical"
        self.spacing = dp(2)
        self.padding = [0, dp(8), 0, dp(6)]

        self._icono = MDIcon(
            icon=icono, theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=dp(26), halign="center", size_hint_y=None, height=dp(30))
        self._etiqueta = MDLabel(
            text=etiqueta, theme_text_color="Custom", text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.ETIQUETA, bold=True, halign="center",
            size_hint_y=None, height=dp(16))

        self.add_widget(self._icono)
        self.add_widget(self._etiqueta)

    def on_release(self):
        self._on_seleccion(self.nombre)

    def set_activo(self, valor: bool):
        self._activo = valor
        color = Color.PRIMARIO if valor else Color.TEXTO_SUAVE
        self._icono.text_color = color
        self._etiqueta.text_color = color


class BarraNavegacion(MDBoxLayout):
    """Barra de navegación inferior con varios ítems."""

    def __init__(self, items, on_cambio, **kwargs):
        """
        items: lista de tuplas (icono, etiqueta, nombre)
        on_cambio: callback(nombre) al seleccionar un ítem
        """
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(Dim.ALTURA_NAV)
        self.md_bg_color = Color.FONDO_ELEVADO
        self._on_cambio = on_cambio
        self._items = {}

        # Línea superior divisoria
        from kivy.graphics import Color as GColor, Line
        with self.canvas.before:
            self._linea_color = GColor(*Color.BORDE)
            self._linea = Line(width=1)
        self.bind(pos=self._actualizar_linea, size=self._actualizar_linea)

        for icono, etiqueta, nombre in items:
            item = ItemNav(icono, etiqueta, nombre, self._seleccionar)
            self._items[nombre] = item
            self.add_widget(item)

    def _actualizar_linea(self, *_):
        self._linea.points = [self.x, self.top, self.right, self.top]

    def _seleccionar(self, nombre):
        self.set_activo(nombre)
        self._on_cambio(nombre)

    def set_activo(self, nombre):
        for nom, item in self._items.items():
            item.set_activo(nom == nombre)
