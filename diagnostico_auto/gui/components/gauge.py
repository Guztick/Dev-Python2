# -*- coding: utf-8 -*-
"""
Gauge circular y medidores para datos en tiempo real.

Widgets dibujados con canvas para un aspecto profesional de
instrumento automotriz. Incluye animación suave de valores.
"""
import math
from kivy.metrics import dp
from kivy.properties import (
    NumericProperty, StringProperty, ListProperty, BooleanProperty
)
from kivy.uix.widget import Widget
from kivy.graphics import Color as GColor, Line, Ellipse
from kivy.animation import Animation
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

from gui.theme import Color, Fuente


class GaugeCircular(Widget):
    """
    Medidor circular tipo tacómetro.

    Dibuja un arco de progreso con un valor central. El color del arco
    cambia según el porcentaje (verde → ámbar → rojo) si está habilitado.
    """
    valor = NumericProperty(0)
    valor_min = NumericProperty(0)
    valor_max = NumericProperty(100)
    titulo = StringProperty("")
    unidad = StringProperty("")
    color_arco = ListProperty(Color.CYAN)
    color_alerta = BooleanProperty(False)   # Cambiar color según nivel
    grosor = NumericProperty(10)

    # Arco de 270° (deja un hueco abajo, como un tacómetro real)
    ANGULO_INICIO = 135
    ANGULO_TOTAL = 270

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._valor_animado = 0
        self.bind(pos=self._redibujar, size=self._redibujar,
                  valor=self._on_valor)

    def _on_valor(self, *_):
        # Animar suavemente hacia el nuevo valor
        anim = Animation(_valor_animado=self.valor, duration=0.4, t="out_cubic")
        anim.bind(on_progress=lambda *a: self._redibujar())
        anim.start(self)

    def _color_por_nivel(self, fraccion: float):
        """Retorna color según la fracción (0-1) si color_alerta está activo."""
        if not self.color_alerta:
            return self.color_arco
        if fraccion < 0.6:
            return Color.EXITO
        elif fraccion < 0.85:
            return Color.ADVERTENCIA
        return Color.PELIGRO

    def _redibujar(self, *_):
        self.canvas.clear()
        if self.width <= 1 or self.height <= 1:
            return

        cx = self.center_x
        cy = self.center_y
        radio = min(self.width, self.height) / 2 - dp(self.grosor)

        rango = max(self.valor_max - self.valor_min, 0.001)
        fraccion = max(0.0, min(1.0, (self._valor_animado - self.valor_min) / rango))
        color = self._color_por_nivel(fraccion)

        with self.canvas:
            # Arco de fondo (track)
            GColor(*Color.BORDE)
            Line(
                circle=(cx, cy, radio, self.ANGULO_INICIO,
                        self.ANGULO_INICIO + self.ANGULO_TOTAL),
                width=dp(self.grosor),
                cap="round",
            )
            # Arco de progreso
            GColor(*color)
            angulo_fin = self.ANGULO_INICIO + self.ANGULO_TOTAL * fraccion
            if fraccion > 0.001:
                Line(
                    circle=(cx, cy, radio, self.ANGULO_INICIO, angulo_fin),
                    width=dp(self.grosor),
                    cap="round",
                )
            # Punto indicador en el extremo del progreso
            ang_rad = math.radians(angulo_fin - 90)
            px = cx + radio * math.sin(ang_rad + math.pi)
            py = cy + radio * math.cos(ang_rad + math.pi)
            # (el punto se omite para mantener limpieza visual)


class MedidorCircular(MDBoxLayout):
    """
    Gauge completo: el arco circular + valor numérico + título.
    Componente listo para usar en la pantalla de datos en vivo.
    """
    valor = NumericProperty(0)
    valor_min = NumericProperty(0)
    valor_max = NumericProperty(100)
    titulo = StringProperty("")
    unidad = StringProperty("")
    color_arco = ListProperty(Color.CYAN)
    color_alerta = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.size = (dp(140), dp(150))
        self._construir()

    def _construir(self):
        from kivymd.uix.relativelayout import MDRelativeLayout

        cont = MDRelativeLayout(size_hint=(1, None), height=dp(120))

        self._gauge = GaugeCircular(
            valor=self.valor,
            valor_min=self.valor_min,
            valor_max=self.valor_max,
            color_arco=self.color_arco,
            color_alerta=self.color_alerta,
        )

        # Valor central
        self._lbl_valor = MDLabel(
            text=self._formato_valor(),
            theme_text_color="Custom",
            text_color=Color.TEXTO,
            font_style="H5",
            bold=True,
            halign="center",
            pos_hint={"center_x": 0.5, "center_y": 0.55},
        )
        self._lbl_unidad = MDLabel(
            text=self.unidad,
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO,
            halign="center",
            pos_hint={"center_x": 0.5, "center_y": 0.33},
        )

        cont.add_widget(self._gauge)
        cont.add_widget(self._lbl_valor)
        cont.add_widget(self._lbl_unidad)

        self._lbl_titulo = MDLabel(
            text=self.titulo,
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO,
            halign="center",
            size_hint_y=None,
            height=dp(24),
        )

        self.add_widget(cont)
        self.add_widget(self._lbl_titulo)

    def _formato_valor(self) -> str:
        if self.valor == int(self.valor):
            return str(int(self.valor))
        return f"{self.valor:.1f}"

    def actualizar(self, valor: float) -> None:
        """Actualiza el valor mostrado con animación."""
        self.valor = valor
        self._gauge.valor = valor
        self._lbl_valor.text = self._formato_valor()


class MedidorBarra(MDBoxLayout):
    """
    Medidor de barra horizontal compacto — alternativa al gauge circular
    para datos secundarios. Más denso, ideal para listas de parámetros.
    """
    valor = NumericProperty(0)
    valor_min = NumericProperty(0)
    valor_max = NumericProperty(100)
    titulo = StringProperty("")
    unidad = StringProperty("")
    color_barra = ListProperty(Color.CYAN)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(56)
        self.spacing = dp(4)
        self.padding = [dp(4), dp(4)]
        self._construir()

    def _construir(self):
        # Fila superior: título y valor
        fila = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22))
        self._lbl_titulo = MDLabel(
            text=self.titulo,
            theme_text_color="Custom",
            text_color=Color.TEXTO_SUAVE,
            font_size=Fuente.SECUNDARIO,
        )
        self._lbl_valor = MDLabel(
            text=f"{self._fmt()} {self.unidad}",
            theme_text_color="Custom",
            text_color=Color.TEXTO,
            font_size=Fuente.CUERPO,
            bold=True,
            halign="right",
        )
        fila.add_widget(self._lbl_titulo)
        fila.add_widget(self._lbl_valor)

        # Barra de progreso
        self._barra = Widget(size_hint_y=None, height=dp(6))
        self._barra.bind(pos=self._dibujar_barra, size=self._dibujar_barra)

        self.add_widget(fila)
        self.add_widget(self._barra)

    def _fmt(self) -> str:
        if self.valor == int(self.valor):
            return str(int(self.valor))
        return f"{self.valor:.1f}"

    def _dibujar_barra(self, *_):
        self._barra.canvas.clear()
        rango = max(self.valor_max - self.valor_min, 0.001)
        frac = max(0.0, min(1.0, (self.valor - self.valor_min) / rango))
        with self._barra.canvas:
            GColor(*Color.BORDE)
            Line(points=[self._barra.x, self._barra.center_y,
                         self._barra.right, self._barra.center_y],
                 width=dp(3), cap="round")
            if frac > 0.001:
                GColor(*self.color_barra)
                Line(points=[self._barra.x, self._barra.center_y,
                             self._barra.x + self._barra.width * frac,
                             self._barra.center_y],
                     width=dp(3), cap="round")

    def actualizar(self, valor: float) -> None:
        self.valor = valor
        self._lbl_valor.text = f"{self._fmt()} {self.unidad}"
        self._dibujar_barra()
